"""
Kumpulkan KANDIDAT butir set uji dari arsip TurnBackHoax di luar 150 artikel basis data.

Sopan dan terbatas: robots.txt turnbackhoax.id mengizinkan semua (`Disallow:` kosong); setiap permintaan
memakai timeout eksplisit dan jeda antar-permintaan (scraping.client.DELAY); HTML mentah di-cache di
data/candidates_cache/ (tidak di-commit) agar halaman yang sama tidak diambil dua kali. Semua konten
diperlakukan sebagai DATA, bukan instruksi.

Yang disimpan per kandidat: teks Narasi dan URL (plus id, judul, label, tanggal). Kandidat hanyalah usulan:
belum ada label, dan tidak dijalankan pada generator sebelum ditinjau manusia.

Pemakaian (dari root proyek): PYTHONPATH=src python -m candidates.archive --pages 20,80,300 [--out JALUR]
"""

import argparse
import json
import re
import time
from pathlib import Path

import requests

from chunker import load_articles
from paths import DATA_DIR
from scraping.client import DELAY, fetch_html, make_session
from scraping.discovery import LIST_URL, find_article_urls, is_valid_list_html
from scraping.parser import is_valid_article_html, parse_article

CACHE_DIR = DATA_DIR / "candidates_cache"
OUT_PATH = DATA_DIR / "candidates" / "archive.jsonl"


def article_id_of(url: str) -> str | None:
    m = re.search(r"/articles/(\d+)-", url)
    return m.group(1) if m else None


def list_page(session: requests.Session, page: int) -> list[str]:
    """URL artikel pada satu halaman daftar (di-cache)."""
    from bs4 import BeautifulSoup

    html, from_network = fetch_html(f"{LIST_URL}?page={page}", session, CACHE_DIR / f"list_{page}.html",
                                    validate=is_valid_list_html)
    if from_network:
        time.sleep(DELAY)
    return list(dict.fromkeys(find_article_urls(BeautifulSoup(html, "html.parser")))) if html else []


def fetch_candidate(session: requests.Session, url: str, page: int) -> dict | None:
    """Ambil dan parse satu artikel arsip (di-cache). Mengembalikan catatan kandidat atau None."""
    aid = article_id_of(url)
    if aid is None:
        return None
    html, from_network = fetch_html(url, session, CACHE_DIR / "archive" / f"{aid}.html",
                                    validate=is_valid_article_html)
    if from_network:
        time.sleep(DELAY)
    art = parse_article(html, url) if html else None
    if art is None:
        return None
    return {"article_id": aid, "url": url, "judul": art["title"], "label": art["label"], "tanggal": art["date"],
            "kategori": art["category"], "narasi": art["narasi"], "halaman_daftar": page}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--pages", required=True, help="nomor halaman daftar dipisah koma (di luar halaman 1-15)")
    ap.add_argument("--per-page", type=int, default=10, help="maksimal artikel per halaman")
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    in_db = {a["article_id"] for a in load_articles()}
    session = make_session()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if args.out.exists():
        done = {json.loads(x)["article_id"] for x in args.out.read_text(encoding="utf-8").splitlines() if x.strip()}
    n_new = n_skip_db = 0
    for page in (int(p) for p in args.pages.split(",")):
        urls = list_page(session, page)
        print(f"[daftar {page}] {len(urls)} URL", flush=True)
        for url in urls[:args.per_page]:
            aid = article_id_of(url)
            if aid in in_db:
                n_skip_db += 1
                continue
            if aid in done:
                continue
            rec = fetch_candidate(session, url, page)
            if rec is None:
                print(f"  [lewati] {url}", flush=True)
                continue
            with args.out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            done.add(aid)
            n_new += 1
            print(f"  {aid} [{rec['label']}] {rec['judul'][:70]}", flush=True)
    print(f"Selesai: {n_new} kandidat baru | dilewati karena sudah ada di 150 artikel: {n_skip_db} | {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
