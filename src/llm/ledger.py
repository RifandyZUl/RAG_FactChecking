"""
Buku besar kuota harian lokal dan perencanaan anggaran.

Dokumentasi Google menyatakan RPD direset tengah malam waktu Pasifik dan batas
berlaku per proyek (bukan per kunci). Dokumentasi TIDAK menyatakan apakah
permintaan yang ditolak 429 ikut terhitung; karena itu buku besar lokal menghitung
setiap permintaan yang dikirim, termasuk yang ditolak (perkiraan konservatif).
"""

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from llm.limits import ModelLimits
from paths import LEDGER_PATH


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
