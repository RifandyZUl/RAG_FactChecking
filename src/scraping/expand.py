"""
Perluasan basis data (tahap 3): kumpulkan artikel LEBIH TUA dari artikel tertua yang sudah dimiliki,
per kelompok, tanpa menyentuh data/articles.json maupun archive/v1.

Halaman daftar TurnBackHoax diurutkan dari yang terbaru; posisinya bergeser setiap ada artikel
baru, dan id artikel TIDAK menurun monoton. Karena itu titik mulai dicari lewat URL jangkar (artikel
tertua yang dimiliki, dalam urutan daftar), bukan lewat id atau nomor halaman tetap.

Tiap kelompok ditulis ke data/expansion/batch_NN.json (artikel, urutan daftar) dan
batch_NN_report.json (berhasil, gagal beserta alasan, seksi kosong, rentang tanggal). Status
lanjutan disimpan di data/expansion/state.json. HTML mentah di-cache di data/raw_html/ lewat
scrape_article, sehingga parsing dapat diulang tanpa memanggil server. Penggabungan ke
data/articles.json dilakukan TERPISAH setelah seluruh kelompok lolos pemeriksaan kualitas.

Ketentuan jaringan mengikuti scraping.client: timeout 45 dtk, retry terbatas, jeda 1,5 dtk.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m scraping.expand --batch-size 250
"""

import argparse
import contextlib
import io
import json
import re
import sys
import time
from datetime import date
from typing import Any

from paths import ARTICLES_PATH, DATA_DIR
from scraping.client import DELAY, make_session
from scraping.discovery import LIST_URL, find_article_urls, get_soup
from scraping.pipeline import scrape_article

EXPANSION_DIR = DATA_DIR / "expansion"
STATE_PATH = EXPANSION_DIR / "state.json"
MAX_FAILURE_RATE = 0.05  # ambang sewenang-wenang dari pemilik proyek (bukan berbasis data)
SECTIONS = ("narasi", "penjelasan", "kesimpulan")
_FAIL_LINE = re.compile(r"\[gagal\] \S+ -> (.+)")


def article_id_of(url: str) -> str | None:
    m = re.search(r"/articles/(\d+)-", url)
    return m.group(1) if m else None


def urls_after_anchor(page_urls: list[str], anchor_url: str | None) -> tuple[list[str], bool]:
    """
    URL pada satu halaman yang terletak SETELAH jangkar (lebih tua). (daftar, jangkar_ditemukan).
    Tanpa jangkar (None), seluruh URL halaman dikembalikan.
    """
    if anchor_url is None:
        return list(page_urls), True
    if anchor_url in page_urls:
        return page_urls[page_urls.index(anchor_url) + 1:], True
    return [], False


def batch_stats(articles: list[dict], failures: list[dict], attempted: int) -> dict[str, Any]:
    """Ringkasan kelompok: berhasil, gagal (alasan), seksi kosong, rentang tanggal, tingkat gagal."""
    empty = [a["article_id"] for a in articles if any(not a.get(k) for k in SECTIONS)]
    empty_by_section = {k: sum(1 for a in articles if not a.get(k)) for k in SECTIONS}
    dates = []
    for a in articles:
        try:
            day, month, year = (int(x) for x in a["date"].split("/"))
            dates.append(date(year, month, day))  # tanggal kalender, tanpa zona waktu
        except (KeyError, ValueError):
            pass
    reasons: dict[str, int] = {}
    for f in failures:
        reasons[f["alasan"]] = reasons.get(f["alasan"], 0) + 1
    return {
        "dicoba": attempted,
        "berhasil": len(articles),
        "gagal": len(failures),
        "tingkat_gagal": round(len(failures) / attempted, 4) if attempted else 0.0,
        "alasan_gagal": reasons,
        "artikel_seksi_kosong": len(empty),
        "seksi_kosong_per_seksi": empty_by_section,
        "id_seksi_kosong": empty,
        "tanggal_tanpa_format_sah": len(articles) - len(dates),
        "rentang_tanggal": [min(dates).isoformat(), max(dates).isoformat()] if dates else None,
        "label": _count(a.get("label") for a in articles),
    }


def _count(values: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def fetch_list_page(page: int, session: Any) -> list[str] | None:
    soup = get_soup(f"{LIST_URL}?page={page}", session)
    if soup is None:
        return None
    seen: list[str] = []
    for u in find_article_urls(soup):
        if u not in seen:
            seen.append(u)
    return seen


def collect_urls(session: Any, anchor_url: str, start_page: int, n: int, known_ids: set[str],
                 max_scan_pages: int = 80) -> tuple[list[str], int]:
    """
    Kumpulkan n URL lebih tua dari jangkar, dimulai dari `start_page` (jangkar dicari maju).
    Mengembalikan (url, halaman_terakhir_dibaca).
    """
    urls: list[str] = []
    found_anchor = False
    page = start_page
    for page in range(start_page, start_page + max_scan_pages):
        page_urls = fetch_list_page(page, session)
        time.sleep(DELAY)
        if page_urls is None:
            raise RuntimeError(f"halaman daftar {page} gagal diambil")
        if not found_anchor:
            candidates, found_anchor = urls_after_anchor(page_urls, anchor_url)
            print(f"[daftar] halaman {page}: jangkar {'DITEMUKAN' if found_anchor else 'belum ada'}")
        else:
            candidates = page_urls
        for u in candidates:
            aid = article_id_of(u)
            if aid and aid not in known_ids and u not in urls:
                urls.append(u)
        if len(urls) >= n:
            break
    if not found_anchor:
        raise RuntimeError(f"jangkar {anchor_url} tidak ditemukan pada halaman {start_page}-{page}")
    return urls[:n], page


def scrape_with_reason(url: str, session: Any) -> tuple[dict | None, bool, str]:
    """scrape_article + alasan gagal (diambil dari keluaran fetch_html; modul klien tidak diubah)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        art, from_network = scrape_article(url, session)
    log = buf.getvalue()
    if log:
        print(log, end="")
    if art is not None:
        return art, from_network, ""
    m = _FAIL_LINE.search(log)
    return None, from_network, (m.group(1).strip() if m else "HTML sah tetapi parse_article mengembalikan None")


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    base = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    return {"batch": 0, "anchor_url": base[-1]["url"], "start_page": 1,
            "known_ids": [a["article_id"] for a in base], "catatan": "jangkar awal = artikel terakhir data/articles.json"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--batch-size", type=int, default=250)
    ap.add_argument("--start-page", type=int, default=None, help="halaman awal pencarian jangkar (bawaan: dari status)")
    args = ap.parse_args()

    state = load_state()
    known = set(state["known_ids"])
    batch_no = state["batch"] + 1
    start_page = args.start_page or state["start_page"]
    session = make_session()

    print(f"=== Kelompok {batch_no}: {args.batch_size} artikel setelah {state['anchor_url']} ===")
    urls, last_page = collect_urls(session, state["anchor_url"], start_page, args.batch_size, known)
    print(f"{len(urls)} URL terkumpul (halaman daftar s.d. {last_page})")

    articles, failures = [], []
    for i, url in enumerate(urls, 1):
        art, from_network, reason = scrape_with_reason(url, session)
        if art is None:
            failures.append({"url": url, "article_id": article_id_of(url), "alasan": reason})
        else:
            articles.append(art)
        print(f"[{i}/{len(urls)}] {article_id_of(url)} {'ok' if art else 'GAGAL: ' + reason}")
        if from_network:
            time.sleep(DELAY)

    stats = batch_stats(articles, failures, len(urls))
    EXPANSION_DIR.mkdir(parents=True, exist_ok=True)
    (EXPANSION_DIR / f"batch_{batch_no:02d}.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"kelompok": batch_no, "jangkar_awal": state["anchor_url"], "halaman_daftar_terakhir": last_page,
              "statistik": stats, "gagal": failures}
    (EXPANSION_DIR / f"batch_{batch_no:02d}_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    state.update({"batch": batch_no, "anchor_url": urls[-1] if urls else state["anchor_url"],
                  "start_page": last_page, "known_ids": sorted(known | {article_id_of(u) for u in urls})})
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    if stats["tingkat_gagal"] > MAX_FAILURE_RATE:
        print(f"BERHENTI: tingkat gagal {stats['tingkat_gagal']:.1%} > {MAX_FAILURE_RATE:.0%}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
