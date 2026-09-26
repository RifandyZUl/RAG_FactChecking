"""
Pulihkan articles.json dari daftar artikel (mis. archive/v1/article_ids.json) -- untuk membangun
ulang arsip indeks bila salinan articles.json-nya hilang.

Tiap artikel diambil lewat `scrape_article` yang sama dengan pipeline: dari cache HTML mentah
(data/raw_html/) bila ada, selain itu dari situs sumber (timeout 45 dtk, retry, jeda antar-
permintaan; lihat scraping.client). Urutan keluaran = urutan daftar, karena sidik jari isi
articles.json (`sha256_articles_json_isi`, lihat evaluation.index_check) bergantung pada urutan.

Gagal keras (kode keluar 1, berkas TIDAK ditulis) bila ada artikel yang tidak dapat dipulihkan
(dihapus penerbit, galat jaringan, atau HTML tidak valid) -- arsip parsial tidak setara dengan
arsip asli.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m scraping.restore archive/v1/article_ids.json --out archive/v1/articles.json
"""

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from scraping.client import DELAY, make_session
from scraping.pipeline import scrape_article, write_articles


def load_article_list(path: Path) -> list[dict[str, Any]]:
    """Baca daftar artikel: objek dengan kunci "artikel", atau langsung list; wajib ada article_id + url."""
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data["artikel"] if isinstance(data, dict) else data
    for e in entries:
        if not e.get("article_id") or not e.get("url"):
            raise ValueError(f"entri tanpa article_id/url: {e}")
    return entries


def restore(
    entries: list[dict[str, Any]],
    scrape: Callable[[str], tuple[dict | None, bool]],
    delay_s: float = DELAY,
) -> tuple[list[dict], list[str]]:
    """
    Ambil ulang artikel sesuai urutan daftar. Mengembalikan (artikel, masalah).

    `scrape(url) -> (artikel|None, dari_jaringan)` disuntikkan agar dapat diuji tanpa jaringan.
    """
    articles: list[dict] = []
    problems: list[str] = []
    for i, e in enumerate(entries, 1):
        art, from_network = scrape(e["url"])
        if art is None:
            problems.append(f"{e['article_id']}: gagal diambil atau di-parse ({e['url']})")
        elif art["article_id"] != e["article_id"]:
            problems.append(f"{e['article_id']}: id hasil parse berbeda ({art['article_id']})")
        else:
            articles.append(art)
        print(f"[{i}/{len(entries)}] {e['article_id']} {'jaringan' if from_network else 'cache'}"
              f"{'' if art else ' GAGAL'}")
        if from_network and delay_s > 0:
            time.sleep(delay_s)
    return articles, problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("ids", type=Path, help="daftar artikel (mis. archive/v1/article_ids.json)")
    ap.add_argument("--out", type=Path, required=True, help="berkas articles.json keluaran")
    ap.add_argument("--force-refresh", action="store_true", help="abaikan cache, ambil dari jaringan")
    args = ap.parse_args()

    entries = load_article_list(args.ids)
    session = make_session()
    articles, problems = restore(entries, lambda url: scrape_article(url, session, args.force_refresh))
    if problems:
        print(f"DIBATALKAN: {len(problems)} dari {len(entries)} artikel tidak dapat dipulihkan; "
              f"{args.out} tidak ditulis.")
        for p in problems[:20]:
            print("  -", p)
        return 1
    write_articles(articles, args.out)
    print(f"{len(articles)} artikel ditulis ke {args.out}. Verifikasi dengan "
          "evaluation.index_check --expect-v1-archive setelah indeks dibangun ulang.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
