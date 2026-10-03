"""
Lapisan pengambilan data yang BISA DIGANTI (2026-10-03).

`scraping.expand` (perluasan, mode maju, coba ulang) tidak lagi memanggil kode scraping HTML secara
langsung, melainkan sebuah "sumber artikel" dengan tiga kemampuan: membuat sesi, memberi daftar URL
artikel pada satu halaman daftar, dan mengambil satu artikel sebagai dict terstruktur. Sumber dipilih
lewat variabel lingkungan ARTICLE_SOURCE (bawaan "html").

Alasannya: Mafindo punya API publik ("Yudistira"); permintaan API key sudah diajukan dan belum dijawab.
Bila key diberikan, sumber baru cukup ditambahkan di sini tanpa mengubah logika kelompok, pemutus
sirkuit, aturan menahan, maupun buku gagal. Integrasi API itu SENGAJA BELUM dibangun.

Kontrak yang wajib dipenuhi sumber apa pun:
- `fetch_article` mengembalikan dict dengan kunci ARTICLE_KEYS, dengan seksi Narasi, Penjelasan, dan
  Kesimpulan TERPISAH (Aturan Wajib #2) serta `references` yang sudah tersaring dan `claim_sources`
  terpisah (Aturan Wajib #1). Sumber yang tidak dapat memisahkan seksi tidak boleh dipakai sebelum
  dievaluasi (lihat CLAUDE.md, "Jalur data resmi").
- Kegagalan yang layak dicoba lagi dilaporkan dengan mencetak baris "[gagal] <url> -> <alasan>" dan
  "[retry i/n] ..." seperti `scraping.client` (dibaca `expand` untuk alasan dan hitungan retry), atau
  dengan melempar exception (dicatat sebagai galat_kode).
- Setiap permintaan jaringan bertimeout dan menghormati jeda antar-permintaan.
"""

import os
from typing import Any, Protocol

from scraping.client import make_session
from scraping.discovery import LIST_URL, find_article_urls, get_soup
from scraping.pipeline import scrape_article

SOURCE_ENV = "ARTICLE_SOURCE"
DEFAULT_SOURCE = "html"

# Kunci dict artikel (sama dengan keluaran scraping.parser.parse_article).
ARTICLE_KEYS = frozenset({
    "article_id", "url", "title", "title_raw", "label", "category", "date", "narasi", "penjelasan",
    "kesimpulan", "references_raw", "references", "references_filtered", "claim_sources",
})


class ArticleSource(Protocol):
    """Sumber artikel cek fakta. Implementasi: HtmlSource (scraping HTML TurnBackHoax)."""

    name: str

    def make_session(self) -> Any:
        """Sesi/klien yang dipakai ulang untuk seluruh jalan."""

    def list_page_urls(self, page: int, session: Any) -> list[str] | None:
        """URL artikel pada halaman daftar ke-`page` (1 = terbaru), urutan daftar; None bila gagal diambil."""

    def fetch_article(self, url: str, session: Any) -> tuple[dict | None, bool]:
        """(artikel terstruktur atau None, dari_jaringan). `dari_jaringan` False bila dibaca dari cache."""


class HtmlSource:
    """Scraping HTML turnbackhoax.id (sumber data Versi 1): halaman daftar ?page=N + halaman artikel."""

    name = "html"

    def make_session(self) -> Any:
        return make_session()

    def list_page_urls(self, page: int, session: Any) -> list[str] | None:
        soup = get_soup(f"{LIST_URL}?page={page}", session)
        return None if soup is None else find_article_urls(soup)

    def fetch_article(self, url: str, session: Any) -> tuple[dict | None, bool]:
        return scrape_article(url, session)


SOURCES: dict[str, type] = {"html": HtmlSource}
# Sumber yang direncanakan tetapi belum dibangun: namanya dikenali agar pesannya jelas.
PLANNED_SOURCES = {"yudistira": "API publik Mafindo (Yudistira): menunggu API key; integrasinya belum dibangun"}


def get_source(name: str | None = None) -> ArticleSource:
    """Sumber artikel menurut `name` atau variabel lingkungan ARTICLE_SOURCE (bawaan "html")."""
    key = (name or os.environ.get(SOURCE_ENV) or DEFAULT_SOURCE).strip().lower()
    if key in SOURCES:
        return SOURCES[key]()
    if key in PLANNED_SOURCES:
        raise NotImplementedError(f"sumber artikel '{key}' belum tersedia: {PLANNED_SOURCES[key]}")
    raise ValueError(f"sumber artikel '{key}' tidak dikenal; pilihan: {sorted(SOURCES)}")


def check_article_schema(article: dict) -> None:
    """Tolak artikel dari sumber mana pun yang kuncinya tidak sesuai kontrak (melempar ValueError)."""
    missing, extra = ARTICLE_KEYS - article.keys(), article.keys() - ARTICLE_KEYS
    if missing or extra:
        raise ValueError(f"artikel tidak sesuai skema: kunci hilang {sorted(missing)}, kunci asing {sorted(extra)}")
