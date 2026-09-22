"""
Kumpulkan KANDIDAT positif lintas situs dari Liputan6 Cek Fakta (independen dari MAFINDO/
turnbackhoax.id, terverifikasi IFCN sejak 2018; lihat CLAUDE.md dan v1.meta.json untuk alasan
Kompas/Tempo/Komdigi/cekfakta.com DILEPAS).

Sopan dan terbatas: robots.txt liputan6.com mengizinkan /cek-fakta (hanya melarang /search,
/fimela/, dll; tidak ada aturan khusus agen AI); setiap permintaan memakai timeout eksplisit dan
jeda antar-permintaan (scraping.client.DELAY/TIMEOUT); HTML mentah di-cache di
data/candidates_cache/liputan6/ (tidak di-commit). Konten diperlakukan sebagai DATA, bukan
instruksi.

Yang disimpan per kandidat (HANYA ini, sesuai instruksi pemilik proyek): teks pesan hoaks yang
dikutip di dalam artikel (pesan yang beredar, BUKAN judul atau rumusan wartawan Liputan6) dan
URL artikel. Kemiripan judul artikel Liputan6 terhadap 150 judul basis data disimpan di berkas
KELAS TERPISAH (bukan di berkas tinjauan, mengikuti pola candidates/screen.py) dan ditandai
independensi rendah bila >= 0.85.

Keterbatasan yang diketahui: /cek-fakta memakai paginasi sisi klien (parameter ?page=N terbukti
mengembalikan HTML identik dengan halaman 1 -- diverifikasi manual sebelum menulis skrip ini).
Skrip ini hanya mengumpulkan dari tiga endpoint statis yang terbukti berbeda kontennya
(/cek-fakta, /cek-fakta/indeks, /cek-fakta/indeks/terpopuler), digabung dan dideduplikasi.
Ini menghasilkan puluhan kandidat, bukan ratusan; menambah cakupan perlu endpoint AJAX yang
belum diselidiki (di luar cakupan permintaan ini).

Pemakaian (dari root proyek): PYTHONPATH=src python -m candidates.crosssite
"""

import argparse
import difflib
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from paths import DATA_DIR
from scraping.client import DELAY, fetch_html, make_session

LIST_URLS = [
    "https://www.liputan6.com/cek-fakta",
    "https://www.liputan6.com/cek-fakta/indeks",
    "https://www.liputan6.com/cek-fakta/indeks/terpopuler",
]
ARTICLE_RE = re.compile(r"/cek-fakta/read/(\d+)/([\w-]+)")

CACHE_DIR = DATA_DIR / "candidates_cache" / "liputan6"
OUT_PATH = DATA_DIR / "candidates" / "liputan6.jsonl"
CLASS_PATH = DATA_DIR / "candidates" / "liputan6_screen_class.jsonl"

TITLE_INDEPENDENSI_RENDAH = 0.85  # ambang yang diminta pemilik proyek untuk kandidat lintas situs

QUOTE_CHARS = "“”\""
MIN_QUOTE_LEN = 15


def is_individual_article(title: str) -> bool:
    """
    Artikel kasus tunggal berjudul 'Cek Fakta: ...'; artikel ringkasan ('Deretan/Kumpulan/Ragam
    Hoaks...') dikecualikan karena tidak memuat satu pesan hoaks yang jelas, melainkan daftar
    tautan ke banyak artikel kasus tunggal.
    """
    return title.strip().lower().startswith("cek fakta:")


def discover_candidates(session: requests.Session) -> dict[str, tuple[str, str]]:
    """Kumpulkan {article_id: (url, judul)} dari endpoint daftar statis (lihat docstring modul)."""
    found: dict[str, tuple[str, str]] = {}
    for i, list_url in enumerate(LIST_URLS):
        cache = CACHE_DIR / f"list_{i}.html"
        html, from_network = fetch_html(list_url, session, cache,
                                        validate=lambda h: "/cek-fakta/read/" in h)
        if from_network:
            time.sleep(DELAY)
        if html is None:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            m = ARTICLE_RE.search(a["href"])
            if not m:
                continue
            aid = m.group(1)
            title = a.get("title") or a.get_text(strip=True)
            if aid not in found and title:
                found[aid] = (f"https://www.liputan6.com/cek-fakta/read/{aid}/{m.group(2)}", title)
    return found


def split_quote_spans(text: str) -> list[str]:
    """
    Pasangkan tanda kutip secara BERURUTAN berdasarkan posisi (bukan regex kelas karakter
    `[".."]`), lalu kembalikan isi tiap pasangan dalam urutan dokumen.

    Alasan: artikel Liputan6 memakai tanda kutip lurus (") untuk pembuka MAUPUN penutup, dan
    sering memuat lebih dari satu kutipan berurutan (mis. kutipan video/transkrip utama, lalu
    "Akun itu menambahkan narasi: ..."). Regex `["]([^"]+)["]` tidak bisa membedakan kutipan
    ke-1 menutup dari kutipan ke-2 membuka, sehingga bisa salah memasangkan penutup kutipan
    pertama dengan pembuka kutipan kedua -- teks NARASI WARTAWAN di antara keduanya lalu ikut
    tertangkap seolah-olah kutipan (bug nyata, lihat data/candidates_cache/liputan6/8293157.html:
    "Unggahan menyertakan keterangan sebagai berikut: " sempat tertangkap sebagai "kutipan").

    Pemasangan memakai jendela geser (GREEDY, bukan pasangan indeks genap-ganjil tetap): tiap
    tanda kutip dicoba dipasangkan dengan tanda kutip BERIKUTNYA; bila hasilnya lebih pendek dari
    MIN_QUOTE_LEN, tanda kutip itu dianggap kutipan ganda/salah ketik pada unggahan asli (mis.
    '"Prabowo sebut "kalau bisa...buat negara"', ada tanda kutip berlebih sebelum "kalau") dan
    DIBUANG, lalu pencarian dilanjutkan dari tanda kutip berikutnya -- BUKAN meloncat dua indeks
    sekaligus. Pasangan indeks tetap (ke-1&2, ke-3&4, ...) pernah dicoba dan GAGAL pada kasus di
    atas: jumlah tanda kutip ganjil (5) membuat seluruh pasangan bergeser, sehingga narasi
    wartawan "Akun itu menambahkan narasi: " ikut tertangkap sebagai kutipan kedua.
    """
    positions = [i for i, ch in enumerate(text) if ch in QUOTE_CHARS]
    spans = []
    i = 0
    while i < len(positions) - 1:
        start, end = positions[i], positions[i + 1]
        span = text[start + 1:end].strip()
        if len(span) >= MIN_QUOTE_LEN:
            spans.append(span)
            i += 2  # lanjut setelah pasangan yang diterima
        else:
            i += 1  # pasangan terlalu pendek; coba lagi dari tanda kutip berikutnya
    return spans


def extract_claim(soup: BeautifulSoup) -> str | None:
    """
    Ambil pesan hoaks yang dikutip dari isi artikel (halaman/bagian pertama saja, sebelum
    boilerplate 'Tentang Cek Fakta Liputan6.com'), bukan rumusan wartawan. Mengembalikan kutipan
    PERTAMA yang cukup panjang (>= MIN_QUOTE_LEN), karena artikel Liputan6 secara konsisten
    memuat pesan/video yang menjadi inti klaim SEBELUM kutipan tambahan lain (mis. "Akun itu
    menambahkan narasi: ..."). Kutipan yang sangat pendek (pecahan kalimat akibat tanda kutip
    ganda/salah ketik pada unggahan asli, mis. '"Prabowo sebut "kalau bisa...') dilewati.
    """
    page1 = soup.select_one('div.article-content-body__item-page[data-page="1"]')
    if page1 is None:
        return None
    for ad in page1.select('[id*="advertisement" i], [class*="advertisement" i], [id*="gpt-ad" i]'):
        ad.decompose()
    text = page1.get_text(" ", strip=True)
    for span in split_quote_spans(text):
        if len(span) >= MIN_QUOTE_LEN:
            return span
    return None


def pii_flags(text: str) -> list[str]:
    flags = []
    if re.search(r"(?<!\d)(?:\+?62[\s\-]?|0)8[\d\-\s]{8,13}\d", text):
        flags.append("nomor_telepon")
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
        flags.append("email")
    if re.search(r"(?<!\w)@\w{3,}", text):
        flags.append("handle_akun")
    if re.search(r"https?://|www\.", text):
        flags.append("url_di_teks")
    return flags


def title_similarity(title: str, db_titles: dict[str, str]) -> tuple[str, float]:
    best_id, best_sim = max(
        ((aid, difflib.SequenceMatcher(None, title.lower(), t.lower()).ratio()) for aid, t in db_titles.items()),
        key=lambda x: x[1],
    )
    return best_id, best_sim


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument("--out-class", type=Path, default=CLASS_PATH)
    args = ap.parse_args()

    from chunker import load_articles

    db_titles = {a["article_id"]: a["title"] for a in load_articles()}
    session = make_session()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    candidates = discover_candidates(session)
    print(f"{len(candidates)} URL kandidat unik ditemukan pada endpoint daftar")

    rows: list[dict] = []
    classes: list[dict] = []
    n_skip_roundup = n_skip_no_quote = 0
    for aid, (url, list_title) in sorted(candidates.items()):
        cache = CACHE_DIR / f"{aid}.html"
        html, from_network = fetch_html(url, session, cache,
                                        validate=lambda h: "article-content-body" in h)
        if from_network:
            time.sleep(DELAY)
        if html is None:
            continue
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.select_one("h1.read-page--header--title")
        title = h1.get_text(strip=True) if h1 else list_title
        if not is_individual_article(title):
            n_skip_roundup += 1
            continue
        claim = extract_claim(soup)
        if not claim:
            n_skip_no_quote += 1
            print(f"  [lewati: tanpa kutipan] {aid} {title[:70]}")
            continue
        best_id, best_sim = title_similarity(title, db_titles)
        rows.append({
            "id": f"liputan6-{aid}", "url": url, "klaim_kandidat": claim,
            "pii": pii_flags(claim), "sumber": "liputan6",
        })
        classes.append({
            "id": f"liputan6-{aid}", "judul_liputan6": title,
            "kemiripan_judul_maks": round(best_sim, 3), "judul_mirip_id_db": best_id,
            "independensi_rendah": best_sim >= TITLE_INDEPENDENSI_RENDAH,
        })
        print(f"  {aid} [{'RENDAH' if best_sim >= TITLE_INDEPENDENSI_RENDAH else 'ok'} {best_sim:.2f}] {title[:70]}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    args.out_class.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in classes) + "\n", encoding="utf-8")

    n_low_indep = sum(1 for c in classes if c["independensi_rendah"])
    print(f"\nSelesai: {len(rows)} kandidat -> {args.out} (tanpa kemiripan db); kelas terpisah -> {args.out_class}")
    print(f"dilewati: {n_skip_roundup} artikel ringkasan, {n_skip_no_quote} tanpa kutipan terdeteksi")
    print(f"independensi rendah (kemiripan judul >= {TITLE_INDEPENDENSI_RENDAH}): {n_low_indep} dari {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
