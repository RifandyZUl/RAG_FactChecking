"""
Scraper artikel TurnBackHoax.id

Mengambil artikel cek fakta dan memecahnya berdasarkan seksi (Narasi,
Penjelasan, Kesimpulan) sesuai struktur baku artikel TurnBackHoax.

Catatan: halaman daftar artikel sudah terverifikasi server-side rendered
dengan paginasi ?page=N. Kendala utamanya adalah latensi server yang
tinggi, sehingga semua permintaan memakai timeout, retry, dan cache HTML.
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
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}
DELAY = 1.5  # jeda antar-request, hindari membebani server
TIMEOUT = 45  # detik; server turnbackhoax.id lambat mengirim respons pertama
MAX_RETRIES = 3  # retry setelah percobaan pertama (total maksimal 4 percobaan)
BACKOFF_BASE = 2.0  # jeda retry: 2 dtk, 4 dtk, 8 dtk (exponential backoff)

# Dijangkar ke root proyek agar tidak bergantung pada direktori kerja
RAW_HTML_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_html"


def make_session() -> requests.Session:
    """Buat Session yang dipakai ulang (koneksi keep-alive) dengan header browser."""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def fetch_html(
    url: str,
    session: requests.Session,
    cache_path: Path | None = None,
    force_refresh: bool = False,
) -> tuple[str | None, bool]:
    """
    Ambil HTML mentah sebuah halaman, memakai cache bila tersedia.

    Mengembalikan (html, dari_jaringan). Nilai kedua False bila HTML dibaca
    dari cache, sehingga pemanggil boleh melewati jeda antar-request.

    Retry dengan exponential backoff HANYA untuk read timeout dan connection
    error. Galat HTTP (termasuk 404) tidak di-retry.
    """
    if cache_path is not None and not force_refresh and cache_path.exists():
        return cache_path.read_text(encoding="utf-8"), False

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
        except (requests.ReadTimeout, requests.ConnectionError) as e:
            # ConnectTimeout adalah turunan ConnectionError, jadi ikut tertangkap
            if attempt == MAX_RETRIES:
                print(f"  [gagal] {url} -> {type(e).__name__} setelah "
                      f"{MAX_RETRIES + 1} percobaan")
                return None, True
            wait = BACKOFF_BASE * (2 ** attempt)
            print(f"  [retry {attempt + 1}/{MAX_RETRIES}] {type(e).__name__}; "
                  f"menunggu {wait:.0f} dtk")
            time.sleep(wait)
        except requests.RequestException as e:
            # Termasuk HTTPError (404, 5xx): tidak di-retry
            print(f"  [gagal] {url} -> {e}")
            return None, True
        else:
            if cache_path is not None:
                # Tulis ke berkas sementara lalu ganti, agar cache tidak
                # berisi HTML terpotong bila proses terhenti di tengah jalan
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = cache_path.with_suffix(".tmp")
                tmp.write_text(resp.text, encoding="utf-8")
                tmp.replace(cache_path)
            return resp.text, True

    return None, True  # tak tercapai; menenangkan pemeriksa tipe


def get_soup(url: str, session: requests.Session) -> BeautifulSoup | None:
    """Ambil halaman daftar (tanpa cache) dan kembalikan objek BeautifulSoup."""
    html, _ = fetch_html(url, session)
    return BeautifulSoup(html, "html.parser") if html is not None else None


def discover_article_urls(
    session: requests.Session, max_articles: int = 150, max_pages: int = 40
) -> list[str]:
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
        soup = get_soup(page_url, session)
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

    html, from_network = fetch_html(url, session, cache_path, force_refresh)
    if html is None:
        return None, from_network
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    if h1 is None:
        print(f"  [lewati] tidak ada <h1>: {url}")
        return None, from_network

    raw_title = h1.get_text(" ", strip=True)
    label, clean_title = parse_title(raw_title)

    # Kontainer isi artikel: ambil elemen induk dari <h1> sebagai perkiraan.
    # VERIFIKASI: sesuaikan selector ini setelah memeriksa HTML asli.
    container = h1.find_parent(["article", "main", "div"]) or soup

    sections = extract_sections(container)
    references = extract_references(container)
    claim_sources = extract_claim_sources(container)

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
    }, from_network


def main(
    max_articles: int = 150,
    out_path: str = "data/articles.json",
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