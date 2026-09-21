"""
Parsing HTML satu artikel TurnBackHoax menjadi dict terstruktur (tanpa jaringan).

Logika `extract_sections`, `extract_references`, dan `extract_claim_sources` sudah
tervalidasi terhadap HTML nyata (lihat tests/).
"""

import re

from bs4 import BeautifulSoup

from scraping.links import filter_references, unique_urls


def is_valid_article_html(html: str) -> bool:
    """
    Halaman artikel sah bila punya <h1> dan minimal satu seksi artikel.

    Server sesekali membalas 200 OK dengan halaman galat ("Terjadi kesalahan
    saat mengambil data") yang tidak punya keduanya.
    """
    soup = BeautifulSoup(html, "html.parser")
    return soup.find("h1") is not None and soup.select_one(
        "section.article-origin, section.article-explanation, "
        "section.article-references"
    ) is not None


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


def parse_article(html: str, url: str) -> dict | None:
    """
    Parse HTML mentah satu artikel menjadi dict terstruktur (tanpa jaringan).

    Dipisah dari scrape_article() agar bisa diuji dengan HTML nyata dari cache.
    """
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    if h1 is None:
        print(f"  [lewati] tidak ada <h1>: {url}")
        return None

    raw_title = h1.get_text(" ", strip=True)
    label, clean_title = parse_title(raw_title)

    m_id = re.search(r"/articles/(\d+)-", url)
    article_id = m_id.group(1) if m_id else None

    # Blok judul: induk terdekat <h1>. Hanya memuat header (judul, kategori,
    # tanggal), BUKAN seksi isi artikel.
    header = h1.find_parent(["article", "main", "div"]) or soup

    # Kontainer isi: ancestor terdekat <h1> yang memuat seksi artikel
    # (<section class="article-origin|article-explanation|article-references">).
    # Terverifikasi pada HTML asli TurnBackHoax; induk langsung <h1> tidak cukup.
    container = header
    while container is not None and container.select_one(
        "section.article-origin, section.article-explanation, "
        "section.article-references"
    ) is None:
        container = container.parent
    if container is None:
        print(f"  [peringatan] seksi artikel tidak ditemukan: {url}")
        container = header

    sections = extract_sections(container)
    references_raw = unique_urls(extract_references(container))
    claim_sources = unique_urls(extract_claim_sources(container))
    references, references_filtered = filter_references(references_raw, claim_sources)

    # Kategori dan tanggal dicari di blok judul, bukan di seluruh artikel,
    # agar tidak tertukar dengan tautan/tanggal di isi artikel.
    category = None
    cat_link = header.find("a", href=re.compile(r"category="))
    if cat_link:
        category = cat_link.get_text(strip=True)

    date = None
    m_date = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", header.get_text(" ", strip=True))
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
        "references_raw": references_raw,
        "references": references,
        "references_filtered": references_filtered,
        "claim_sources": claim_sources,
    }
