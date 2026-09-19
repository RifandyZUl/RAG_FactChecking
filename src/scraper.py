"""
Scraper artikel TurnBackHoax.id

Mengambil artikel cek fakta dan memecahnya berdasarkan seksi (Narasi,
Penjelasan, Kesimpulan) sesuai struktur baku artikel TurnBackHoax.

Catatan: halaman daftar artikel kemungkinan dimuat lewat JavaScript
(tombol "Load More"). Jika discover_article_urls() mengembalikan daftar
kosong, lihat catatan di bagian bawah file ini.
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://turnbackhoax.id"
LIST_URL = f"{BASE_URL}/articles"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
DELAY = 1.5  # jeda antar-request, hindari membebani server


def get_soup(url: str) -> BeautifulSoup | None:
    """Ambil halaman dan kembalikan objek BeautifulSoup."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"  [gagal] {url} -> {e}")
        return None


def discover_article_urls(max_articles: int = 150, max_pages: int = 40) -> list[str]:
    """
    Kumpulkan URL artikel dari halaman daftar.

    Pola URL artikel: /articles/{id}-{slug}
    """
    urls: list[str] = []
    seen: set[str] = set()
    pattern = re.compile(r"^/articles/\d+-")

    for page in range(1, max_pages + 1):
        page_url = f"{LIST_URL}?page={page}"
        print(f"[daftar] halaman {page}")
        soup = get_soup(page_url)
        if soup is None:
            break

        found_on_page = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]
            path = href.replace(BASE_URL, "")
            if pattern.match(path):
                full = urljoin(BASE_URL, path)
                if full not in seen:
                    seen.add(full)
                    urls.append(full)
                    found_on_page += 1

        print(f"  ditemukan {found_on_page} artikel baru (total {len(urls)})")

        if found_on_page == 0:
            print("  tidak ada artikel baru -> berhenti")
            break
        if len(urls) >= max_articles:
            break

        time.sleep(DELAY)

    return urls[:max_articles]


def parse_title(title: str) -> tuple[str, str]:
    """
    Pisahkan label kebenaran dari judul.

    "[SALAH] Malaysia Laporkan ..." -> ("SALAH", "Malaysia Laporkan ...")
    """
    m = re.match(r"^\s*\[([^\]]+)\]\s*(.+)$", title)
    if m:
        return m.group(1).strip().upper(), m.group(2).strip()
    return "TIDAK DIKETAHUI", title.strip()


# Kata kunci penanda seksi, dicocokkan pada teks yang di-bold
SECTION_KEYS = {
    "narasi": "narasi",
    "penjelasan": "penjelasan",
    "kesimpulan": "kesimpulan",
    "hasil periksa fakta": "hasil_periksa_fakta",
    "referensi": "referensi",
}


def extract_sections(container) -> dict[str, str]:
    """
    Pecah isi artikel menjadi seksi berdasarkan penanda <strong>/<b>.

    Struktur artikel TurnBackHoax: **Narasi** ... **Penjelasan** ...
    **Kesimpulan** ... **Hasil Periksa Fakta** ... **Referensi**
    """
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for el in container.find_all(["p", "ul", "ol", "div", "h2", "h3", "strong", "b"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue

        key = SECTION_KEYS.get(text.lower().rstrip(":").strip())
        if key and len(text) < 40:
            current = key
            sections.setdefault(current, [])
            continue

        if current:
            sections[current].append(text)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


def extract_references(container) -> list[str]:
    """
    Ambil tautan rujukan valid, yaitu HANYA yang berada di dalam seksi
    "Referensi".

    Penting: tautan di seksi "Narasi" adalah sumber hoaks itu sendiri
    (postingan media sosial asli) dan TIDAK boleh disajikan ke pengguna
    sebagai rujukan yang sahih.
    """
    refs: list[str] = []
    in_refs = False

    for el in container.find_all(["p", "ul", "ol", "div", "strong", "b", "a"]):
        text = el.get_text(" ", strip=True)

        # Deteksi penanda awal seksi Referensi
        if text and len(text) < 40 and text.lower().rstrip(":").strip() == "referensi":
            in_refs = True
            continue

        if not in_refs:
            continue

        if el.name == "a" and el.get("href", "").startswith("http"):
            href = el["href"]
            if "turnbackhoax.id" not in href and href not in refs:
                refs.append(href)

    return refs


def extract_claim_sources(container) -> list[str]:
    """
    Ambil tautan sumber klaim hoaks (dari seksi Narasi).

    Disimpan terpisah untuk keperluan analisis/dokumentasi, JANGAN
    ditampilkan ke pengguna sebagai rujukan yang sahih.
    """
    sources: list[str] = []
    in_narasi = False

    for el in container.find_all(["p", "ul", "ol", "div", "strong", "b", "a"]):
        text = el.get_text(" ", strip=True)
        key = SECTION_KEYS.get(text.lower().rstrip(":").strip()) if text else None

        if key and len(text) < 40:
            in_narasi = key == "narasi"
            continue

        if not in_narasi:
            continue

        if el.name == "a" and el.get("href", "").startswith("http"):
            href = el["href"]
            if "turnbackhoax.id" not in href and href not in sources:
                sources.append(href)

    return sources


def scrape_article(url: str) -> dict | None:
    """Ambil dan parse satu artikel menjadi dict terstruktur."""
    soup = get_soup(url)
    if soup is None:
        return None

    h1 = soup.find("h1")
    if h1 is None:
        print(f"  [lewati] tidak ada <h1>: {url}")
        return None

    raw_title = h1.get_text(" ", strip=True)
    label, clean_title = parse_title(raw_title)

    # Kontainer isi artikel: ambil elemen induk dari <h1> sebagai perkiraan.
    # VERIFIKASI: sesuaikan selector ini setelah memeriksa HTML asli.
    container = h1.find_parent(["article", "main", "div"]) or soup

    sections = extract_sections(container)
    references = extract_references(container)
    claim_sources = extract_claim_sources(container)

    m_id = re.search(r"/articles/(\d+)-", url)
    article_id = m_id.group(1) if m_id else None

    # Kategori dan tanggal: dicari dari tautan kategori dan pola tanggal
    category = None
    cat_link = container.find("a", href=re.compile(r"category="))
    if cat_link:
        category = cat_link.get_text(strip=True)

    date = None
    m_date = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", container.get_text(" ", strip=True))
    if m_date:
        date = m_date.group(1)

    return {
        "article_id": article_id,
        "url": url,
        "title": clean_title,
        "title_raw": raw_title,
        "label": label,
        "category": category,
        "date": date,
        "narasi": sections.get("narasi", ""),
        "penjelasan": sections.get("penjelasan", ""),
        "kesimpulan": sections.get("kesimpulan", ""),
        "references": references,
        "claim_sources": claim_sources,
    }


def main(max_articles: int = 150, out_path: str = "data/articles.json") -> None:
    print("=== Tahap 1: mengumpulkan URL artikel ===")
    urls = discover_article_urls(max_articles=max_articles)

    if not urls:
        print(
            "\nTidak ada URL artikel yang ditemukan.\n"
            "Kemungkinan daftar artikel dimuat lewat JavaScript.\n"
            "Alternatif: gunakan Playwright/Selenium untuk merender halaman daftar,\n"
            "atau periksa tab Network di browser untuk menemukan endpoint JSON\n"
            "yang dipakai tombol 'Load More'."
        )
        return

    print(f"\n=== Tahap 2: mengambil {len(urls)} artikel ===")
    articles = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        art = scrape_article(url)
        if art:
            articles.append(art)
        time.sleep(DELAY)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nSelesai. {len(articles)} artikel tersimpan di {out}")

    # Ringkasan cepat untuk validasi kualitas parsing
    kosong = sum(1 for a in articles if not a["kesimpulan"])
    print(f"Artikel tanpa seksi 'Kesimpulan' terparse: {kosong}")
    if kosong > len(articles) * 0.2:
        print(
            "PERINGATAN: banyak artikel gagal terparse seksinya. "
            "Periksa kembali selector di extract_sections()."
        )


if __name__ == "__main__":
    main(max_articles=150)