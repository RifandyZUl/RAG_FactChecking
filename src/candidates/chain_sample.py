"""
Sampel ACAK pesan berantai asli untuk pengukuran "apakah masalah pesan panjang terjadi pada pesan
nyata" (docs/rancangan_v2.md bagian 10). Hanya mengambil dan mengukur; TIDAK memakai LLM dan tidak
menilai apa pun.

Dua sumber (keputusan pemilik proyek 2026-10-03):
- Liputan6 Cek Fakta, artikel kasus tunggal ("Cek Fakta: ...") terbit dalam rentang tanggal basis data.
  Pencacahan lewat halaman indeks per tanggal (/cek-fakta/indeks/YYYY/MM/DD): tanggal dipilih acak
  berbenih, lalu artikel dipilih acak berbenih dari gabungan tanggal terpilih.
- Arsip TurnBackHoax SEBELUM September 2025 (di luar basis data): halaman daftar dipilih acak berbenih,
  lalu artikel dipilih acak berbenih per halaman.

Yang diukur per pesan: teks pesan yang dikutip artikel (kutipan terpanjang) dan panjangnya dalam token
bge-m3 (tokenizer yang sama dengan retrieval, termasuk token khusus), dibandingkan dengan batas 512.

Sopan dan terbatas: robots.txt kedua situs diperiksa lebih dulu (keduanya mengizinkan jalur ini);
timeout dan jeda mengikuti scraping.client; HTML di-cache di data/candidates_cache/ (tidak di-commit).
Keluaran di data/candidates/pesan_berantai/ (tidak di-commit: berisi teks hoaks apa adanya, bisa memuat
nomor dan tautan penipu). Konten pihak ketiga diperlakukan sebagai DATA, bukan instruksi.

Pemakaian (dari root proyek): PYTHONPATH=src python -m candidates.chain_sample
"""

import argparse
import json
import random
import re
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from candidates.crosssite import ARTICLE_RE, is_individual_article, split_quote_spans
from candidates.screen import pii_flags
from paths import ARTICLES_PATH, DATA_DIR
from scraping.client import DELAY, fetch_html, make_session
from scraping.discovery import LIST_URL, find_article_urls, is_valid_list_html
from scraping.parser import is_valid_article_html, parse_article

SEED = 20261003  # dicatat sebelum pengambilan; jangan diubah setelah hasil dilihat
TOKEN_LIMIT = 512
SAMPLE_SIZE = 100

L6_INDEX = "https://www.liputan6.com/cek-fakta/indeks/{:%Y/%m/%d}"
L6_DATE_FROM, L6_DATE_TO = date(2025, 9, 30), date(2026, 9, 27)  # rentang tanggal basis data 1.532 artikel
L6_N_DATES = 60
L6_CACHE = DATA_DIR / "candidates_cache" / "liputan6"

TBH_CUTOFF = date(2025, 9, 1)  # "sebelum September 2025"
TBH_PAGE_FROM, TBH_PAGE_TO = 175, 1558  # halaman daftar yang seluruhnya lebih tua dari basis data (per 2026-10-03)
TBH_N_PAGES = 30
TBH_PER_PAGE = 4
TBH_CACHE = DATA_DIR / "candidates_cache"

OUT_DIR = DATA_DIR / "candidates" / "pesan_berantai"


def date_range(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def sample_dates(seed: int = SEED, n: int = L6_N_DATES) -> list[date]:
    """n tanggal acak (berbenih) dari rentang basis data; urutan kronologis."""
    return sorted(random.Random(seed).sample(date_range(L6_DATE_FROM, L6_DATE_TO), n))


def sample_pages(seed: int = SEED, n: int = TBH_N_PAGES) -> list[int]:
    """n halaman daftar acak (berbenih) dari arsip di luar basis data."""
    return sorted(random.Random(seed + 1).sample(range(TBH_PAGE_FROM, TBH_PAGE_TO + 1), n))


def longest_quote(text: str) -> tuple[str, int]:
    """(kutipan terpanjang, jumlah kutipan) pada teks; ("", 0) bila tidak ada kutipan."""
    spans = split_quote_spans(text)
    return (max(spans, key=len), len(spans)) if spans else ("", 0)


def length_class(tokens: int, limit: int = TOKEN_LIMIT) -> str:
    return "di_atas_batas" if tokens > limit else "di_bawah_batas"


def l6_index_articles(html: str) -> dict[str, tuple[str, str]]:
    """{id: (url, judul)} artikel kasus tunggal pada satu halaman indeks tanggal."""
    found: dict[str, tuple[str, str]] = {}
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        m = ARTICLE_RE.search(a["href"])
        title = (a.get("title") or a.get_text(" ", strip=True) or "").strip()
        if m and title and is_individual_article(title) and m.group(1) not in found:
            found[m.group(1)] = (f"https://www.liputan6.com/cek-fakta/read/{m.group(1)}/{m.group(2)}", title)
    return found


def l6_published(soup: BeautifulSoup) -> date | None:
    meta = soup.find("meta", attrs={"property": "article:published_time"}) or soup.find("time", attrs={"datetime": True})
    raw = (meta.get("content") or meta.get("datetime") or "") if meta else ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def l6_message(soup: BeautifulSoup) -> dict[str, Any]:
    """Kutipan pesan pada halaman pertama artikel, dan pada seluruh halaman (untuk melihat yang terlewat)."""
    pages = soup.select("div.article-content-body__item-page")
    texts = []
    for page in pages:
        for ad in page.select('[id*="advertisement" i], [class*="advertisement" i], [id*="gpt-ad" i]'):
            ad.decompose()
        texts.append(page.get_text(" ", strip=True))
    first_page = texts[0] if texts else ""
    quote, n_quotes = longest_quote(first_page)
    quote_all, _ = longest_quote(" ".join(texts))
    return {"pesan": quote, "jumlah_kutipan": n_quotes, "jumlah_halaman": len(pages),
            "kutipan_terpanjang_semua_halaman_lebih_panjang": len(quote_all) > len(quote)}


def collect_liputan6(session: Any, count: Any, seed: int = SEED) -> tuple[list[dict], dict[str, Any]]:
    pool: dict[str, tuple[str, str, str]] = {}
    failed_dates = []
    dates = sample_dates(seed)
    for d in dates:
        html, from_network = fetch_html(L6_INDEX.format(d), session, L6_CACHE / f"indeks_{d.isoformat()}.html",
                                        validate=lambda h: "cek-fakta" in h)
        if from_network:
            time.sleep(DELAY)
        if html is None:
            failed_dates.append(d.isoformat())
            continue
        for aid, (url, title) in l6_index_articles(html).items():
            pool.setdefault(aid, (url, title, d.isoformat()))
    order = sorted(pool)
    random.Random(seed + 2).shuffle(order)
    rows: list[dict] = []
    skipped = {"gagal_ambil": 0, "di_luar_rentang_tanggal": 0, "tanpa_kutipan": 0}
    tried = 0
    for aid in order:
        if len(rows) >= SAMPLE_SIZE:
            break
        tried += 1
        url, title, _ = pool[aid]
        html, from_network = fetch_html(url, session, L6_CACHE / f"{aid}.html",
                                        validate=lambda h: "article-content-body" in h)
        if from_network:
            time.sleep(DELAY)
        if html is None:
            skipped["gagal_ambil"] += 1
            continue
        soup = BeautifulSoup(html, "html.parser")
        published = l6_published(soup)
        if published is None or not (L6_DATE_FROM <= published <= L6_DATE_TO):
            skipped["di_luar_rentang_tanggal"] += 1  # tautan samping/terpopuler dari tanggal lain
            continue
        msg = l6_message(soup)
        if not msg["pesan"]:
            skipped["tanpa_kutipan"] += 1
        tokens = count(msg["pesan"]) if msg["pesan"] else 0
        rows.append({"sumber": "liputan6", "id": aid, "url": url, "judul": title, "tanggal": published.isoformat(),
                     **msg, "karakter": len(msg["pesan"]), "token": tokens, "kelas": length_class(tokens),
                     "pii": pii_flags(msg["pesan"])})
    info = {"tanggal_dipilih": len(dates), "tanggal_gagal": failed_dates, "artikel_kasus_tunggal_di_gabungan": len(pool),
            "dicoba": tried, "dilewati": skipped, "benih": seed}
    return rows, info


def collect_archive(session: Any, count: Any, owned: set[str], seed: int = SEED) -> tuple[list[dict], dict[str, Any]]:
    from candidates.screen import claim_candidate

    rng = random.Random(seed + 3)
    pages = sample_pages(seed)
    rows: list[dict] = []
    skipped = {"halaman_gagal": [], "gagal_ambil_atau_parse": 0, "tidak_lebih_tua_dari_batas": 0, "sudah_di_basis_data": 0,
               "tanpa_narasi": 0}
    tried = 0
    for page in pages:
        if len(rows) >= SAMPLE_SIZE:
            break
        html, from_network = fetch_html(f"{LIST_URL}?page={page}", session, TBH_CACHE / f"list_{page}.html",
                                        validate=is_valid_list_html)
        if from_network:
            time.sleep(DELAY)
        if html is None:
            skipped["halaman_gagal"].append(page)
            continue
        urls = list(dict.fromkeys(find_article_urls(BeautifulSoup(html, "html.parser"))))
        for url in rng.sample(urls, min(TBH_PER_PAGE, len(urls))):
            if len(rows) >= SAMPLE_SIZE:
                break
            tried += 1
            m = re.search(r"/articles/(\d+)-", url)
            aid = m.group(1) if m else ""
            if aid in owned:
                skipped["sudah_di_basis_data"] += 1
                continue
            art_html, from_network = fetch_html(url, session, TBH_CACHE / "archive" / f"{aid}.html",
                                                validate=is_valid_article_html)
            if from_network:
                time.sleep(DELAY)
            art = parse_article(art_html, url) if art_html else None
            if art is None:
                skipped["gagal_ambil_atau_parse"] += 1
                continue
            dm = re.match(r"(\d{2})/(\d{2})/(\d{4})", art.get("date") or "")
            published = date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1))) if dm else None
            if published is None or published >= TBH_CUTOFF:
                skipped["tidak_lebih_tua_dari_batas"] += 1
                continue
            narasi = art.get("narasi") or ""
            if not narasi:
                skipped["tanpa_narasi"] += 1
            quote, n_quotes = longest_quote(narasi)
            first = claim_candidate(narasi) if narasi else ""
            message = max(quote, first, key=len)  # kutipan terpanjang, atau teks tanpa kutip setelah kata "narasi"
            tokens = count(message) if message else 0
            rows.append({"sumber": "arsip_turnbackhoax", "id": aid, "url": url, "judul": art["title"], "label": art["label"],
                         "tanggal": published.isoformat(), "halaman_daftar": page, "pesan": message,
                         "jumlah_kutipan": n_quotes, "token_narasi_penuh": count(narasi) if narasi else 0,
                         "karakter": len(message), "token": tokens, "kelas": length_class(tokens), "pii": pii_flags(message)})
    info = {"halaman_dipilih": pages, "dicoba": tried, "dilewati": skipped, "benih": seed}
    return rows, info


def summarize(rows: list[dict]) -> dict[str, Any]:
    with_msg = [r for r in rows if r["pesan"]]
    tokens = sorted(r["token"] for r in with_msg)

    def pct(q: float) -> int:
        return tokens[min(len(tokens) - 1, int(q * len(tokens)))] if tokens else 0

    return {
        "sampel": len(rows),
        "punya_kutipan_pesan": len(with_msg),
        "di_atas_512_token": sum(r["token"] > TOKEN_LIMIT for r in with_msg),
        "di_atas_256_token": sum(r["token"] > TOKEN_LIMIT // 2 for r in with_msg),
        "token_median": pct(0.5), "token_p90": pct(0.9), "token_maks": tokens[-1] if tokens else 0,
        "karakter_maks": max((r["karakter"] for r in with_msg), default=0),
        "memuat_penanda_data_pribadi": sum(bool(r["pii"]) for r in with_msg),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--sources", default="liputan6,arsip", help="sumber yang diambil, dipisah koma")
    args = ap.parse_args()

    from chunker import make_token_counter

    count = make_token_counter()
    session = make_session()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {"benih": SEED, "batas_token": TOKEN_LIMIT}
    if "liputan6" in args.sources:
        rows, info = collect_liputan6(session, count)
        (OUT_DIR / "sampel_liputan6.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        summary["liputan6"] = {"pengambilan": info, **summarize(rows)}
    if "arsip" in args.sources:
        owned = {a["article_id"] for a in json.loads(Path(ARTICLES_PATH).read_text(encoding="utf-8"))}
        rows, info = collect_archive(session, count, owned)
        (OUT_DIR / "sampel_arsip.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        summary["arsip_turnbackhoax"] = {"pengambilan": info, **summarize(rows)}
    (OUT_DIR / "ringkasan.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
