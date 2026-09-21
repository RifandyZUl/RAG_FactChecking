"""
Pengumpulan URL artikel dari halaman daftar (paginasi ?page=N).
"""

import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scraping.client import DELAY, fetch_html

BASE_URL = "https://turnbackhoax.id"
LIST_URL = f"{BASE_URL}/articles"


ARTICLE_PATH = re.compile(r"^/articles/\d+-")


def find_article_urls(soup: BeautifulSoup) -> list[str]:
    """Ambil URL artikel (pola /articles/{id}-{slug}) dari halaman daftar."""
    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        path = a["href"].replace(BASE_URL, "")
        if ARTICLE_PATH.match(path):
            urls.append(urljoin(BASE_URL, path))
    return urls


def is_valid_list_html(html: str) -> bool:
    """Halaman daftar sah bila memuat minimal satu tautan artikel."""
    return bool(find_article_urls(BeautifulSoup(html, "html.parser")))


def get_soup(url: str, session: requests.Session) -> BeautifulSoup | None:
    """Ambil halaman daftar (tanpa cache, divalidasi) sebagai BeautifulSoup."""
    html, _ = fetch_html(url, session, validate=is_valid_list_html)
    return BeautifulSoup(html, "html.parser") if html is not None else None


def discover_article_urls(
    session: requests.Session, max_articles: int = 150, max_pages: int = 40
) -> list[str]:
    """
    Kumpulkan URL artikel dari halaman daftar.

    Pola URL artikel: /articles/{id}-{slug}. Halaman tanpa tautan artikel
    dianggap galat server (di-retry oleh fetch_html), BUKAN akhir paginasi.
    Bila halaman tetap gagal setelah retry, pengumpulan berhenti dengan
    pesan eksplisit dan hasil parsial dikembalikan.
    """
    urls: list[str] = []
    seen: set[str] = set()

    for page in range(1, max_pages + 1):
        page_url = f"{LIST_URL}?page={page}"
        print(f"[daftar] halaman {page}")
        soup = get_soup(page_url, session)
        if soup is None:
            print(f"  [berhenti] halaman {page} gagal diambil; "
                  f"hasil parsial: {len(urls)} URL")
            break

        found_on_page = 0
        for full in find_article_urls(soup):
            if full not in seen:
                seen.add(full)
                urls.append(full)
                found_on_page += 1

        print(f"  ditemukan {found_on_page} artikel baru (total {len(urls)})")

        if found_on_page == 0:
            # Halaman sah tetapi semua artikelnya sudah pernah terlihat
            print("  tidak ada artikel baru -> berhenti")
            break
        if len(urls) >= max_articles:
            break

        time.sleep(DELAY)

    return urls[:max_articles]
