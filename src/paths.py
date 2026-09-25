"""
Jalur proyek terpusat, dijangkar ke root proyek agar tidak bergantung pada direktori kerja.

Pemilihan indeks: variabel lingkungan RAG_INDEX_DIR mengarahkan jalur BACA indeks (ChromaDB +
articles.json) ke direktori lain, mis. arsip Versi 1 (`archive/v1`). Bawaan: `data/` (indeks
utama). Jalur TULIS scraping (`ARTICLES_PATH`, `RAW_HTML_DIR`) sengaja TIDAK ikut berpindah, dan
`ingest` menolak menulis ke dalam `archive/` kecuali diizinkan eksplisit, agar arsip tidak
tertimpa tanpa sengaja.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_HTML_DIR = DATA_DIR / "raw_html"
ARTICLES_PATH = DATA_DIR / "articles.json"  # jalur TULIS scraping/reparse (selalu indeks utama)
LEDGER_PATH = DATA_DIR / "quota_ledger.json"

ARCHIVE_DIR = PROJECT_ROOT / "archive"
V1_ARCHIVE_DIR = ARCHIVE_DIR / "v1"
INDEX_DIR_ENV = "RAG_INDEX_DIR"


def resolve_index_dir(value: str | None) -> Path:
    """
    Direktori indeks dari nilai RAG_INDEX_DIR; `data/` bila kosong.

    Jalur relatif dijangkar ke root proyek. Bila diatur tetapi tidak berisi indeks
    (`chroma/chroma.sqlite3` dan `articles.json`), dilempar FileNotFoundError -- salah ketik
    tidak boleh diam-diam membuat indeks kosong baru.
    """
    if value is None or not value.strip():
        return DATA_DIR
    path = Path(value.strip())
    path = path if path.is_absolute() else (PROJECT_ROOT / path)
    path = path.resolve()
    missing = [p for p in (path / "chroma" / "chroma.sqlite3", path / "articles.json") if not p.is_file()]
    if missing:
        raise FileNotFoundError(
            f"{INDEX_DIR_ENV}={value!r} tidak berisi indeks lengkap; tidak ditemukan: "
            + ", ".join(str(m) for m in missing)
        )
    return path


def is_archive_path(path: Path) -> bool:
    """Apakah `path` berada di dalam direktori arsip (`archive/`)."""
    return path.resolve().is_relative_to(ARCHIVE_DIR.resolve())


INDEX_DIR = resolve_index_dir(os.environ.get(INDEX_DIR_ENV))
INDEX_ARTICLES_PATH = INDEX_DIR / "articles.json"  # jalur BACA articles.json indeks aktif
INDEX_CHROMA_DIR = INDEX_DIR / "chroma"  # jalur BACA ChromaDB indeks aktif
