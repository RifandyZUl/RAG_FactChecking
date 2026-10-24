"""
Sumber daya berat demo (indeks, model embedding, tokenizer, penyedia LLM): dimuat SEKALI per proses.

Tanpa Streamlit, sehingga bisa diuji dan dipakai utas pemanasan. `app.py` membungkus pengambilnya
dengan `st.cache_resource`; keduanya bermuara pada `_Once` yang sama, jadi pemanasan dan sesi pengguna
tidak pernah memuat model dua kali (dibuktikan `tests/test_resources.py` dan baris log
"memuat <nama>" yang hanya muncul sekali).

Pemanasan (`start_warmup`) TIDAK memanggil LLM: ia hanya membuat objek penyedia (tanpa permintaan
jaringan ke Gemini).

Indeks hanya DIBACA: koleksi dibuka tanpa `get_or_create`. (ChromaDB sendiri menulis ulang berkas
indeks setiap kali koleksi dibuka, juga saat evaluasi; isinya tetap sama. Lihat CLAUDE.md.)
"""

import logging
import sqlite3
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Generic, TypeVar

from ingest import (
    CHROMA_DIR,
    COLLECTION_NAME,
    MODEL_NAME,
    MODEL_REVISION,
    collection_ef_search,
    expected_ef_search,
)
from ingest import load_model as _load_embedding_model
from llm import LLMProvider, get_provider
from webapp import (
    settings,  # noqa: F401  (variabel lingkungan HF sebelum transformers diimpor)
)

logger = logging.getLogger("resources")

T = TypeVar("T")


class IndexUnavailableError(Exception):
    """Indeks vektor tidak ada atau kosong; demo tidak membuatnya sendiri."""


class _Once(Generic[T]):
    """Pemuat malas aman-utas: `get()` memanggil `factory` sekali; galat tidak disimpan (dicoba lagi)."""

    def __init__(self, name: str, factory: Callable[[], T]) -> None:
        self.name, self._factory = name, factory
        self._lock = threading.Lock()
        self._value: T | None = None
        self._loaded = False
        self.load_count = 0  # berapa kali factory benar-benar dijalankan (uji & log)
        self.load_seconds: float | None = None

    @property
    def loaded(self) -> bool:
        return self._loaded

    def get(self) -> T:
        if self._loaded:
            return self._value  # type: ignore[return-value]
        with self._lock:  # pemanggil kedua menunggu pemuatan yang sedang berjalan
            if not self._loaded:
                logger.info("memuat %s", self.name)
                t0 = time.perf_counter()
                self.load_count += 1
                self._value = self._factory()
                self.load_seconds = time.perf_counter() - t0
                self._loaded = True
                logger.info("%s siap dalam %.1f dtk", self.name, self.load_seconds)
        return self._value  # type: ignore[return-value]

    def reset(self) -> None:
        """Hanya untuk uji."""
        with self._lock:
            self._value, self._loaded, self.load_count, self.load_seconds = None, False, 0, None


def open_collection(chroma_dir: Path = CHROMA_DIR) -> Any:
    """
    Buka koleksi ChromaDB yang SUDAH ada (tanpa membuat koleksi). `IndexUnavailableError` bila berkas,
    koleksi, atau isinya tidak ada. `ef_search` yang tidak sesuai dicatat sebagai peringatan (pencarian
    bisa meleset; `evaluation.index_check` gagal pada keadaan itu).
    """
    import chromadb
    import chromadb.errors
    from chromadb.config import Settings

    if not (chroma_dir / "chroma.sqlite3").is_file():
        raise IndexUnavailableError(f"berkas basis data tidak ditemukan di {chroma_dir}")
    client = chromadb.PersistentClient(path=str(chroma_dir), settings=Settings(anonymized_telemetry=False))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except chromadb.errors.NotFoundError as e:
        raise IndexUnavailableError(f"koleksi '{COLLECTION_NAME}' tidak ada") from e
    if collection.count() == 0:
        raise IndexUnavailableError(f"koleksi '{COLLECTION_NAME}' kosong")
    found, expected = collection_ef_search(collection), expected_ef_search(chroma_dir)
    if found != expected:
        logger.warning("ef_search indeks %s, seharusnya %s: hasil pencarian bisa meleset", found, expected)
    return collection


def _load_tokenizer() -> Any:
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)


collection = _Once("indeks", open_collection)
embedding_model = _Once("model embedding", _load_embedding_model)
tokenizer = _Once("tokenizer", _load_tokenizer)
provider: _Once[LLMProvider] = _Once("penyedia LLM", get_provider)


def count_tokens(text: str) -> int | None:
    """Panjang teks dalam token model embedding; None bila tokenizer belum siap atau gagal dimuat."""
    if not tokenizer.loaded:
        return None
    return len(tokenizer.get()(text)["input_ids"])


# -- Pemanasan ------------------------------------------------------------------------------------


class WarmupState(Enum):
    NOT_STARTED = "belum"
    RUNNING = "berjalan"
    READY = "siap"
    FAILED = "gagal"


_warmup_lock = threading.Lock()
_warmup_thread: threading.Thread | None = None
_warmup_state = WarmupState.NOT_STARTED
WARMUP_ORDER = (tokenizer, collection, embedding_model, provider)  # tokenizer dulu: dipakai saat mengetik


def _warmup(loaders: tuple[_Once[Any], ...]) -> None:
    global _warmup_state
    failed = False
    for loader in loaders:
        try:
            loader.get()
        except Exception:
            failed = True
            logger.exception("pemanasan: %s gagal dimuat", loader.name)
    _warmup_state = WarmupState.FAILED if failed else WarmupState.READY


def start_warmup(loaders: tuple[_Once[Any], ...] = WARMUP_ORDER) -> bool:
    """Mulai pemanasan di satu utas latar bila belum pernah dimulai. True bila panggilan ini memulainya."""
    global _warmup_thread, _warmup_state
    with _warmup_lock:
        if _warmup_thread is not None:
            return False
        _warmup_state = WarmupState.RUNNING
        _warmup_thread = threading.Thread(target=_warmup, args=(loaders,), name="pemanasan", daemon=True)
        _warmup_thread.start()
        return True


def warmup_state() -> WarmupState:
    return _warmup_state


# -- Statistik indeks -----------------------------------------------------------------------------


@dataclass(frozen=True)
class IndexStats:
    article_count: int | None
    latest_date: date | None  # tanggal terbit artikel terbaru di indeks


def parse_metadata_date(value: str) -> date | None:
    """Tanggal metadata artikel berformat dd/mm/yyyy (mis. "14/08/2026"); None bila tidak terbaca."""
    parts = value.strip().split("/")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    try:
        return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except ValueError:
        return None


def index_stats(chroma_dir: Path = CHROMA_DIR) -> IndexStats:
    """
    Jumlah artikel dan tanggal artikel terbaru, dibaca dari sqlite ChromaDB dalam mode BACA-SAJA
    (koleksi tidak dibuka). Tanggal diurai, bukan dibandingkan sebagai teks ("14/08" > "01/10").
    Nilai None bila tidak terbaca (indeks belum ada atau skema internal ChromaDB berubah).
    """
    db = chroma_dir / "chroma.sqlite3"
    if not db.is_file():
        return IndexStats(None, None)
    try:
        con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
        try:
            count = con.execute(
                "select count(distinct string_value) from embedding_metadata where key = 'article_id'"
            ).fetchone()
            dates = con.execute("select distinct string_value from embedding_metadata where key = 'date'").fetchall()
        finally:
            con.close()
    except sqlite3.Error as e:
        logger.warning("statistik indeks tidak terbaca: %s", e)
        return IndexStats(None, None)
    parsed = [d for d in (parse_metadata_date(row[0] or "") for row in dates) if d is not None]
    return IndexStats(int(count[0]) if count and count[0] else None, max(parsed) if parsed else None)
