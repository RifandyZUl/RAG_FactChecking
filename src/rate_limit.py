"""
Pembatas laju sisi klien dan anggaran kuota harian untuk penyedia LLM.

Tujuan: batas per menit (RPM, TPM) tidak pernah tersentuh, sehingga retry 429
hanya jaring pengaman, bukan mekanisme utama; dan kuota harian (RPD) diperlakukan
sebagai anggaran yang dihitung SEBELUM evaluasi dimulai.

Batas per model dibaca dari `DEFAULT_LIMITS` dan dapat ditimpa lewat `.env`
(`LLM_RPM`, `LLM_TPM`, `LLM_RPD`). Angka bawaan diambil dari AI Studio dan dapat
berubah tanpa pemberitahuan (lihat CLAUDE.md), jadi periksa ulang secara berkala.

Dokumentasi Google menyatakan RPD direset tengah malam waktu Pasifik dan batas
berlaku per proyek (bukan per kunci). Dokumentasi TIDAK menyatakan apakah
permintaan yang ditolak 429 ikut terhitung; karena itu buku besar lokal menghitung
setiap permintaan yang dikirim, termasuk yang ditolak (perkiraan konservatif).
"""

import json
import logging
import os
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = PROJECT_ROOT / "data" / "quota_ledger.json"
logger = logging.getLogger("llm")

WINDOW_S = 60.0
MARGIN_S = 0.5  # tambahan di atas jendela 60 dtk agar tidak berada tepat di batas
CHARS_PER_TOKEN = 3.0  # perkiraan konservatif teks Indonesia; dikoreksi dengan token nyata
LIMITS_DATE = "2026-09-21"  # tanggal angka di bawah diambil dari AI Studio


@dataclass(frozen=True)
class ModelLimits:
    """Batas tier gratis satu model: permintaan/menit, token masuk/menit, permintaan/hari."""

    rpm: int
    tpm: int
    rpd: int


_FLASH_LITE = ModelLimits(rpm=15, tpm=250_000, rpd=500)
_GEMMA = ModelLimits(rpm=30, tpm=16_000, rpd=14_400)

# Diambil dari AI Studio (kolom batas) pada LIMITS_DATE. ID model diverifikasi dari
# dokumentasi resmi; AI Studio menampilkan nama pendek ("gemma-4-26b"), yang di sini
# dipetakan ke ID API (pemetaan itu asumsi: AI Studio tidak menampilkan ID persis).
DEFAULT_LIMITS: dict[str, ModelLimits] = {
    "gemini-3.8-flash": ModelLimits(rpm=5, tpm=250_000, rpd=20),
    "gemini-3.5-flash-lite": _FLASH_LITE,
    "gemini-3.1-flash-lite": _FLASH_LITE,
    "gemma-4-26b-a4b-it": _GEMMA,
    "gemma-4-31b-it": _GEMMA,
}


def limits_for(model: str) -> ModelLimits | None:
    """Batas untuk `model`; nilai `LLM_RPM`/`LLM_TPM`/`LLM_RPD` di lingkungan menimpa bawaan."""
    base = DEFAULT_LIMITS.get(model)
    env = {k: os.environ.get(f"LLM_{k.upper()}") for k in ("rpm", "tpm", "rpd")}
    if base is None and not all(env.values()):
        return None
    vals = {k: int(env[k]) if env[k] else getattr(base, k) for k in ("rpm", "tpm", "rpd")}
    return ModelLimits(**vals)


def estimate_tokens(*texts: str) -> int:
    """Perkiraan kasar token masuk (belum dikirim); TPM Gemini menghitung token masuk."""
    return int(sum(len(t) for t in texts) / CHARS_PER_TOKEN) + 1


class RateLimiter:
    """
    Jendela geser 60 dtk untuk RPM dan TPM. `acquire` menunggu secukupnya agar
    permintaan berikutnya tidak melampaui batas pada jendela mana pun (yang juga
    menjamin tidak melampaui batas pada menit kalender mana pun). Setiap percobaan,
    termasuk retry, harus melewati `acquire`.
    """

    def __init__(
        self,
        limits: ModelLimits,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.limits = limits
        self._clock, self._sleep = clock, sleep
        self._events: deque[list] = deque()  # [waktu, token]

    def _prune(self, now: float) -> None:
        while self._events and self._events[0][0] <= now - WINDOW_S:
            self._events.popleft()

    def _wait_needed(self, now: float, est_tokens: int) -> float:
        lim = self.limits
        wait = 0.0
        if len(self._events) >= lim.rpm:
            wait = max(wait, self._events[0][0] + WINDOW_S - now)
        used = sum(e[1] for e in self._events)
        if used + est_tokens > lim.tpm:
            need, freed = used + est_tokens - lim.tpm, 0
            for t, k in self._events:
                freed += k
                if freed >= need:
                    wait = max(wait, t + WINDOW_S - now)
                    break
        return wait

    def acquire(self, est_tokens: int) -> float:
        """Blok sampai boleh mengirim; catat permintaan. Mengembalikan detik menunggu."""
        if est_tokens > self.limits.tpm:
            raise ValueError(
                f"Satu prompt (~{est_tokens} token) melebihi TPM model ({self.limits.tpm}); "
                "tidak akan pernah bisa dikirim."
            )
        waited = 0.0
        for _ in range(1000):  # pagar: jangan berputar selamanya bila jam macet
            now = self._clock()
            self._prune(now)
            wait = self._wait_needed(now, est_tokens)
            if wait <= 0:
                self._events.append([now, est_tokens])
                return waited
            self._sleep(wait + MARGIN_S)
            waited += wait + MARGIN_S
        raise RuntimeError("RateLimiter tidak kunjung memberi izin (jam tidak maju?)")

    def settle(self, actual_tokens: int | None) -> None:
        """Ganti perkiraan token permintaan terakhir dengan angka nyata dari server."""
        if actual_tokens is not None and self._events:
            self._events[-1][1] = actual_tokens


def pacific_tz():
    """Zona America/Los_Angeles (butuh paket `tzdata` di Windows)."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        return ZoneInfo("America/Los_Angeles")
    except ZoneInfoNotFoundError as e:
        raise RuntimeError(
            "Data zona waktu tidak ada: pasang `tzdata` (pip install -r requirements.txt)."
        ) from e


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DailyLedger:
    """
    Buku besar lokal: jumlah permintaan yang DIKIRIM per model per hari Pasifik.

    Hanya mengetahui permintaan dari kode ini; tidak tahu pemakaian di luar itu
    (mis. proses lain atau sebelum berkas ini ada). JANGAN mengisinya dari dashboard
    AI Studio: kolom penggunaannya adalah puncak 28 hari, bukan pemakaian hari
    berjalan. Bukti kuota hari ini adalah probe tunggal (src/probe_quota.py).
    """

    def __init__(
        self,
        model: str,
        path: Path = LEDGER_PATH,
        now_fn: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.model, self.path, self._now = model, path, now_fn

    def day_key(self, now: datetime | None = None) -> str:
        return (now or self._now()).astimezone(pacific_tz()).date().isoformat()

    def next_reset(self, now: datetime | None = None) -> datetime:
        """Tengah malam Pasifik berikutnya (UTC)."""
        tz = pacific_tz()
        local = (now or self._now()).astimezone(tz)
        nxt = datetime.combine(local.date() + timedelta(days=1), datetime.min.time(), tzinfo=tz)
        return nxt.astimezone(timezone.utc)

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except ValueError as e:
            raise RuntimeError(f"{self.path} rusak ({e}); perbaiki atau hapus berkas ini.") from e
        return data if isinstance(data, dict) else {}

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)

    def used_today(self) -> int:
        return int(self._load().get(self.model, {}).get(self.day_key(), 0))

    def add(self, n: int = 1) -> int:
        """Catat n permintaan terkirim (langsung ke disk); kembalikan total hari ini."""
        data = self._load()
        days = data.setdefault(self.model, {})
        key = self.day_key()
        days[key] = int(days.get(key, 0)) + n
        for old in sorted(days)[:-3]:  # simpan 3 hari terakhir saja
            del days[old]
        self._save(data)
        return days[key]

    def seed(self, used: int) -> None:
        """
        Set hitungan hari ini. Hanya untuk nilai yang dapat ditelusuri (mis. log panggilan
        sendiri); BUKAN dari angka puncak dashboard AI Studio.
        """
        data = self._load()
        data.setdefault(self.model, {})[self.day_key()] = int(used)
        self._save(data)


@dataclass(frozen=True)
class BudgetPlan:
    """Perbandingan kebutuhan panggilan dengan sisa kuota harian."""

    limit: int
    used: int
    needed: int  # minimum: satu panggilan per kueri
    worst_case: int  # bila tiap kueri butuh percobaan ulang format
    reset_at: datetime

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    @property
    def ok(self) -> bool:
        return self.needed <= self.remaining

    def describe(self) -> str:
        s = (f"anggaran harian: batas {self.limit}, terpakai {self.used} (menurut buku besar "
             f"lokal), sisa {self.remaining}; dibutuhkan minimal {self.needed}, terburuk "
             f"{self.worst_case} (semua kueri gagal format sekali). Reset: "
             f"{self.reset_at.astimezone().strftime('%Y-%m-%d %H:%M %Z')} (waktu lokal).")
        if self.worst_case > self.remaining >= self.needed:
            s += (" Skenario terburuk melebihi sisa: proses akan berhenti otomatis saat "
                  "anggaran habis dan dapat dilanjutkan setelah reset.")
        return s


def plan_budget(
    ledger: DailyLedger, limits: ModelLimits, n_queries: int, calls_per_query_worst: int
) -> BudgetPlan:
    return BudgetPlan(
        limit=limits.rpd, used=ledger.used_today(), needed=n_queries,
        worst_case=n_queries * calls_per_query_worst, reset_at=ledger.next_reset(),
    )
