"""
Orkestrasi scraping: kumpulkan URL, ambil dan parse tiap artikel, tulis articles.json.
"""

import json
import re
import time
from pathlib import Path

import requests

from paths import ARTICLES_PATH, RAW_HTML_DIR
from scraping.client import DELAY, fetch_html, make_session
from scraping.discovery import discover_article_urls
from scraping.parser import is_valid_article_html, parse_article


def scrape_article(
    url: str, session: requests.Session, force_refresh: bool = False
) -> tuple[dict | None, bool]:
    """
    Ambil dan parse satu artikel menjadi dict terstruktur.

    HTML mentah di-cache di data/raw_html/{article_id}.html; force_refresh=True
    melewati cache. Mengembalikan (artikel, dari_jaringan).
    """
    m_id = re.search(r"/articles/(\d+)-", url)
    article_id = m_id.group(1) if m_id else None
    cache_path = RAW_HTML_DIR / f"{article_id}.html" if article_id else None

    html, from_network = fetch_html(
        url, session, cache_path, force_refresh, validate=is_valid_article_html
    )
    if html is None:
        return None, from_network
    return parse_article(html, url), from_network


def write_articles(articles: list[dict], out: Path) -> None:
    """Tulis daftar artikel ke JSON (mode teks: di Windows berakhir baris CRLF; jangan diubah)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")


def main(
    max_articles: int = 150,
    out_path: str | Path | None = None,
    force_refresh: bool = False,
) -> None:
    session = make_session()

    print("=== Tahap 1: mengumpulkan URL artikel ===")
    urls = discover_article_urls(session, max_articles=max_articles)

    if not urls:
        print(
            "\nTidak ada URL artikel yang ditemukan.\n"
            "Halaman daftar sudah terverifikasi server-side rendered, jadi "
            "periksa log di atas:\n"
            "kemungkinan timeout/connection error atau perubahan pola tautan "
            "/articles/{id}-{slug}."
        )
        return

    print(f"\n=== Tahap 2: mengambil {len(urls)} artikel ===")
    articles = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        art, from_network = scrape_article(url, session, force_refresh)
        if art:
            articles.append(art)
        if from_network:  # jeda hanya perlu bila server benar-benar dipanggil
            time.sleep(DELAY)

    # Bawaan dijangkar ke root proyek (paths.ARTICLES_PATH), bukan direktori kerja.
    out = Path(out_path) if out_path is not None else ARTICLES_PATH
    write_articles(articles, out)

    print(f"\nSelesai. {len(articles)} artikel tersimpan di {out}")

    # Ringkasan cepat untuk validasi kualitas parsing
    kosong = sum(1 for a in articles if not a["kesimpulan"])
    print(f"Artikel tanpa seksi 'Kesimpulan' terparse: {kosong}")
    if kosong > len(articles) * 0.2:
        print(
            "PERINGATAN: banyak artikel gagal terparse seksinya. "
            "Periksa kembali selector di extract_sections()."
        )
