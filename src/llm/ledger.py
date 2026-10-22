"""
Buku besar kuota harian lokal dan perencanaan anggaran.

Dokumentasi Google menyatakan RPD direset tengah malam waktu Pasifik dan batas
berlaku per proyek (bukan per kunci). Dokumentasi TIDAK menyatakan apakah
permintaan yang ditolak 429 ikut terhitung; karena itu buku besar lokal menghitung
setiap permintaan yang dikirim, termasuk yang ditolak (perkiraan konservatif).

Penulisan dilindungi dua kunci: `threading.Lock` per berkas (utas di satu proses, mis. sesi demo
Streamlit) dan kunci berkas OS (proses berbeda, mis. demo dan skrip evaluasi). Kunci berkas memakai
`msvcrt.locking` (Windows) atau `fcntl.flock` (Linux); OS melepasnya sendiri bila proses pemegangnya
mati, jadi tidak ada kunci tertinggal. Kunci berkas TIDAK andal menembus folder bersama antara Windows
dan container Docker (bind mount WSL2): jangan menjalankan demo di container dan evaluasi di host
bersamaan.
"""

import json
import os
import sys
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
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


LOCK_TIMEOUT_S = 30.0  # menunggu proses lain selesai menulis; satu penulisan hanya beberapa milidetik
_LOCK_POLL_S = 0.02
_thread_locks: dict[Path, threading.Lock] = {}
_thread_locks_guard = threading.Lock()


def _thread_lock(path: Path) -> threading.Lock:
    """Satu `threading.Lock` per berkas buku besar, dibagi semua instans di proses ini."""
    key = path.resolve()
    with _thread_locks_guard:
        return _thread_locks.setdefault(key, threading.Lock())


def _try_os_lock(fd: int) -> bool:
    """Kunci eksklusif tanpa menunggu atas byte pertama berkas kunci; False bila dipegang proses lain."""
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True
    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    return True


def _os_unlock(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)


@contextmanager
def file_lock(path: Path, timeout_s: float = LOCK_TIMEOUT_S) -> Iterator[None]:
    """
    Kunci eksklusif antar-utas dan antar-proses atas `path` (berkas `<path>.lock` di sebelahnya).

    Melempar TimeoutError bila tidak didapat dalam `timeout_s`. Berkas `.lock` dibiarkan ada: yang
    mengunci adalah kunci OS pada berkas itu, bukan keberadaannya, sehingga proses yang mati tidak
    meninggalkan kunci.
    """
    lock_path = path.with_name(path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_s
    if not _thread_lock(path).acquire(timeout=timeout_s):
        raise TimeoutError(f"kunci utas {lock_path} tidak didapat dalam {timeout_s} dtk")
    try:
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            while not _try_os_lock(fd):
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"{lock_path} dipegang proses lain lebih dari {timeout_s} dtk")
                time.sleep(_LOCK_POLL_S)
            try:
                yield
            finally:
                _os_unlock(fd)
        finally:
            os.close(fd)
    finally:
        _thread_lock(path).release()


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

    @property
    def events_path(self) -> Path:
        """Catatan asal tiap penambahan (JSONL, hanya ditambah) di sebelah berkas buku besar."""
        return self.path.with_name(self.path.stem + "_events.jsonl")

    def add(self, n: int = 1, attempt: int | None = None) -> int:
        """
        Catat n permintaan terkirim (langsung ke disk); kembalikan total hari ini.

        Setiap penambahan juga ditulis ke `events_path` beserta waktu UTC, proses asal
        (argumen baris perintah, atau `RAG_LEDGER_ORIGIN` bila di-set), pid, dan nomor
        percobaan di dalam penyedia, agar selisih buku besar dengan berkas hasil dapat
        ditelusuri. Hitungan di berkas buku besar tidak berubah bentuknya.
        """
        with file_lock(self.path):  # baca-ubah-tulis: tanpa kunci, dua penulis bisa saling menimpa
            data = self._load()
            days = data.setdefault(self.model, {})
            key = self.day_key()
            days[key] = int(days.get(key, 0)) + n
            for old in sorted(days)[:-3]:  # simpan 3 hari terakhir saja
                del days[old]
            self._save(data)
            self._log_event(key, n, days[key], attempt)
        return days[key]

    def _log_event(self, day: str, n: int, total: int, attempt: int | None) -> None:
        origin = os.environ.get("RAG_LEDGER_ORIGIN") or " ".join(
            [Path(sys.argv[0]).name if sys.argv and sys.argv[0] else "?", *sys.argv[1:]])
        event = {"waktu_utc": self._now().astimezone(timezone.utc).isoformat(timespec="seconds"),
                 "model": self.model, "hari_pasifik": day, "n": n, "total_hari_ini": total,
                 "percobaan": attempt, "asal": origin, "pid": os.getpid()}
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def seed(self, used: int) -> None:
        """
        Set hitungan hari ini. Hanya untuk nilai yang dapat ditelusuri (mis. log panggilan
        sendiri); BUKAN dari angka puncak dashboard AI Studio.
        """
        with file_lock(self.path):
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
