"""
Lapisan layanan pemeriksaan: validasi masukan, batas laju, serialisasi, lalu pipeline Versi 1 apa adanya.

Tanpa Streamlit. Tampilan (`ui/`) hanya memanggil `check_message` dan memetakan hasilnya ke teks lewat
`presentation.py`; tidak ada logika retrieval atau keputusan di sini: semuanya lewat
`retriever.retrieve` dan `generator.AnswerGenerator` (keduanya TERKUNCI), persis seperti yang dievaluasi.

Mengapa pemeriksaan DISERIALKAN per proses: penyedia LLM dibagi semua sesi, dan generator mengambil
catatan panggilannya sebagai `provider.records[n_before:]`. Dua pemeriksaan serentak akan saling
mencampur `calls`, dan `presentation.classify_failure` membaca `calls`, sehingga jenis galat satu
pengguna bisa berasal dari pengguna lain. Generator terkunci, jadi perbaikannya di sini: satu kunci
di sekitar pemeriksaan (biayanya kecil; penyedia sudah menjaga jeda antar-panggilan).
"""

import logging
import threading
import time
import unicodedata
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import settings
from generator import Answer, AnswerGenerator
from retriever import ArticleHit, retrieve

logger = logging.getLogger("service")


class CheckError(Enum):
    """Alasan pemeriksaan tidak dijalankan atau tidak selesai, di luar galat LLM (lihat presentation)."""

    EMPTY = "kosong"
    TOO_LONG = "terlalu_panjang"
    SESSION_INTERVAL = "jeda_sesi"
    SESSION_HOURLY = "batas_sesi_per_jam"
    GLOBAL_HOURLY = "batas_global_per_jam"
    DAILY_STOP = "batas_harian"
    BUSY = "antrean_penuh"
    NO_INDEX = "basis_data_tidak_ada"
    CONFIG = "konfigurasi"
    UNEXPECTED = "lainnya"


# -- Validasi -------------------------------------------------------------------------------------

_KEEP_CONTROL = {"\n", "\t"}


def clean_message(text: str) -> str:
    """
    Normalkan masukan: baris baru CRLF/CR -> LF, buang karakter kontrol (kategori Unicode Cc) kecuali
    baris baru dan tab, lalu buang spasi di awal/akhir. Isi lain tidak diubah.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "".join(ch for ch in text if ch in _KEEP_CONTROL or unicodedata.category(ch) != "Cc").strip()


def validate_message(text: str, limit: int = settings.MAX_INPUT_CHARS) -> CheckError | None:
    """`CheckError.EMPTY`/`TOO_LONG` untuk teks yang SUDAH dibersihkan; None bila layak diperiksa."""
    if not text:
        return CheckError.EMPTY
    if len(text) > limit:
        return CheckError.TOO_LONG
    return None


def is_long_message(text: str, token_count: int | None) -> bool:
    """Apakah pesan cukup panjang untuk diberi peringatan (token embedding; cadangan: karakter)."""
    if token_count is not None:
        return token_count > settings.LONG_CLAIM_WARN_TOKENS
    return len(text) > settings.LONG_CLAIM_WARN_CHARS


# -- Batas laju -----------------------------------------------------------------------------------


@dataclass
class SessionUsage:
    """Waktu mulai pemeriksaan satu sesi (disimpan di `st.session_state`). Bisa hilang saat halaman dimuat ulang."""

    started: list[float] = field(default_factory=list)


class HourlyWindow:
    """Jendela geser satu jam untuk batas global per proses (aman-utas)."""

    def __init__(self, limit: int, clock: Callable[[], float] = time.monotonic) -> None:
        self.limit, self._clock = limit, clock
        self._events: deque[float] = deque()
        self._lock = threading.Lock()

    def try_take(self) -> float | None:
        """Ambil satu slot; None bila berhasil, atau detik sampai slot tersedia."""
        with self._lock:
            now = self._clock()
            while self._events and self._events[0] <= now - 3600:
                self._events.popleft()
            if len(self._events) >= self.limit:
                return self._events[0] + 3600 - now
            self._events.append(now)
            return None


_global_window = HourlyWindow(settings.GLOBAL_MAX_PER_HOUR)
_check_lock = threading.Lock()


def session_wait_s(usage: SessionUsage, now: float) -> tuple[CheckError, float] | None:
    """Batas per sesi: jeda minimum dan maksimum per jam. None bila boleh."""
    recent = [t for t in usage.started if t > now - 3600]
    usage.started[:] = recent
    if recent and now - recent[-1] < settings.SESSION_MIN_INTERVAL_S:
        return CheckError.SESSION_INTERVAL, settings.SESSION_MIN_INTERVAL_S - (now - recent[-1])
    if len(recent) >= settings.SESSION_MAX_PER_HOUR:
        return CheckError.SESSION_HOURLY, recent[0] + 3600 - now
    return None


def daily_requests_used(provider: Any) -> int | None:
    """Permintaan hari ini menurut buku besar penyedia (dibagi dengan evaluasi); None bila tak ada buku besar."""
    ledger = getattr(provider, "ledger", None)
    return None if ledger is None else ledger.used_today()


# -- Pemeriksaan ----------------------------------------------------------------------------------


@dataclass
class CheckOutcome:
    """Hasil satu pemeriksaan untuk lapisan tampilan. `answer` None berarti pipeline tidak dijalankan/selesai."""

    message: str
    answer: Answer | None = None
    hits: list[ArticleHit] = field(default_factory=list)
    penjelasan: str = ""  # seksi Penjelasan artikel terpilih (dari indeks), hanya bila ditemukan
    error: CheckError | None = None
    retry_after_s: int | None = None
    query_tokens: int | None = None
    timings: dict[str, float] = field(default_factory=dict)  # detik: antre, siapkan, embedding, pencarian, llm, total
    model: str = ""
    error_detail: str = ""  # untuk panel penguji saja; sudah disamarkan


class _TimedModel:
    """Pembungkus model embedding yang mencatat lama `encode` (retriever terkunci tidak disentuh)."""

    def __init__(self, model: Any, timings: dict[str, float]) -> None:
        self._model, self._timings = model, timings

    def encode(self, *args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return self._model.encode(*args, **kwargs)
        finally:
            self._timings["embedding"] = self._timings.get("embedding", 0.0) + time.perf_counter() - t0


class _TimedCollection:
    """Pembungkus koleksi yang mencatat lama `query` + `get` sebagai waktu pencarian."""

    def __init__(self, collection: Any, timings: dict[str, float]) -> None:
        self._collection, self._timings = collection, timings

    def _timed(self, name: str, *args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return getattr(self._collection, name)(*args, **kwargs)
        finally:
            self._timings["pencarian"] = self._timings.get("pencarian", 0.0) + time.perf_counter() - t0

    def query(self, *args: Any, **kwargs: Any) -> Any:
        return self._timed("query", *args, **kwargs)

    def get(self, *args: Any, **kwargs: Any) -> Any:
        return self._timed("get", *args, **kwargs)

    def count(self) -> int:
        return self._collection.count()


@dataclass
class Resources:
    """Sumber daya yang dibutuhkan pemeriksaan; disuntikkan agar layanan bisa diuji dengan objek palsu."""

    get_collection: Callable[[], Any]
    get_model: Callable[[], Any]
    get_provider: Callable[[], Any]
    count_tokens: Callable[[str], int | None]


def _fetch_penjelasan(collection: Any, article_id: str) -> str:
    stored = collection.get(ids=[f"{article_id}_penjelasan"], include=["documents"])
    docs = stored.get("documents") or []
    return docs[0] if docs else ""


def check_message(
    raw_text: str,
    usage: SessionUsage,
    res: Resources,
    on_wait: Callable[[], None] = lambda: None,
    clock: Callable[[], float] = time.monotonic,
) -> CheckOutcome:
    """
    Periksa satu pesan dari awal sampai akhir. Tidak pernah melempar galat ke tampilan: setiap kegagalan
    menjadi `CheckOutcome.error` (galat LLM tetap di `answer`, diklasifikasi `presentation`).

    `on_wait` dipanggil sekali bila pemeriksaan lain sedang berjalan (tampilan menulis "menunggu giliran").
    """
    from llm import LLMConfigError
    from llm.secrets import redact
    from resources import IndexUnavailableError

    text = clean_message(raw_text)
    out = CheckOutcome(message=text)
    out.error = validate_message(text)
    if out.error is not None:
        return out

    now = clock()
    limited = session_wait_s(usage, now)
    if limited is not None:
        out.error, wait = limited
        out.retry_after_s = max(1, round(wait))
        return out

    try:
        provider = res.get_provider()
    except LLMConfigError as e:
        out.error, out.error_detail = CheckError.CONFIG, redact(str(e))
        logger.error("konfigurasi LLM: %s", out.error_detail)
        return out
    out.model = getattr(provider, "model", "")
    used = daily_requests_used(provider)
    if used is not None and used >= settings.DAILY_STOP_REQUESTS:
        out.error = CheckError.DAILY_STOP
        return out

    wait = _global_window.try_take()
    if wait is not None:
        out.error, out.retry_after_s = CheckError.GLOBAL_HOURLY, max(1, round(wait))
        return out
    usage.started.append(now)

    t_queue = time.perf_counter()
    if not _check_lock.acquire(blocking=False):
        on_wait()
        if not _check_lock.acquire(timeout=settings.QUEUE_TIMEOUT_S):
            out.error = CheckError.BUSY
            return out
    try:
        out.timings["antre"] = time.perf_counter() - t_queue
        _run_pipeline(out, provider, res)
        out.timings["total"] = time.perf_counter() - t_queue
    except IndexUnavailableError as e:
        out.error, out.error_detail = CheckError.NO_INDEX, str(e)
        logger.error("indeks tidak tersedia: %s", e)
    except Exception as e:
        out.error, out.error_detail = CheckError.UNEXPECTED, redact(f"{type(e).__name__}: {e}")
        logger.exception("pemeriksaan gagal di luar lapisan LLM")
    finally:
        _check_lock.release()
    return out


def _run_pipeline(out: CheckOutcome, provider: Any, res: Resources) -> None:
    """Jalankan retrieval + generator (di bawah kunci). Mengisi `out`; galat dibiarkan naik ke pemanggil."""
    t0 = time.perf_counter()
    collection = res.get_collection()
    model = res.get_model()
    out.timings["siapkan"] = time.perf_counter() - t0  # ~0 setelah pemanasan selesai
    out.query_tokens = res.count_tokens(out.message)

    timed_model, timed_collection = _TimedModel(model, out.timings), _TimedCollection(collection, out.timings)

    def retrieve_and_keep(query: str, k: int) -> list[ArticleHit]:
        out.hits = retrieve(query, timed_model, timed_collection, top_k=k)
        return out.hits

    try:
        out.answer = AnswerGenerator(provider, retrieve_and_keep).answer(out.message)
    finally:
        # Catatan panggilan sudah disalin ke `answer.calls`; dipangkas agar tidak tumbuh seumur proses.
        provider.records.clear()
    out.timings["llm"] = sum(c.latency_s for c in out.answer.calls)  # termasuk jeda dan percobaan ulang penyedia
    if out.answer.error:
        logger.warning("pemeriksaan gagal: %s", out.answer.error)  # sudah disamarkan penyedia
    if out.answer.verdict == "ditemukan" and out.answer.article_id:
        out.penjelasan = _fetch_penjelasan(collection, out.answer.article_id)
