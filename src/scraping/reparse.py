"""
Parse ulang artikel dari cache HTML mentah (data/raw_html/), TANPA jaringan.

Dipakai setelah logika parsing berubah: daftar URL dan urutan diambil dari articles.json yang
ada, HTML dari cache, hasil ditulis dengan penulis yang sama seperti `scraping.pipeline`
(sehingga byte-nya sebanding). Gagal keras bila ada cache yang hilang atau tidak sah; tidak
pernah menulis hasil parsial.

Pemakaian (dari root proyek): PYTHONPATH=src python -m scraping.reparse [--out JALUR]
Setelah articles.json berubah, indeks vektor WAJIB dibangun ulang (lihat CLAUDE.md).
"""

import argparse
import json
from pathlib import Path

from paths import ARTICLES_PATH, RAW_HTML_DIR
from scraping.parser import is_valid_article_html, parse_article
from scraping.pipeline import write_articles


def reparse(
    articles_path: Path = ARTICLES_PATH,
    raw_html_dir: Path = RAW_HTML_DIR,
) -> list[dict]:
    """Kembalikan artikel hasil parse ulang (urutan sama dengan `articles_path`)."""
    existing = json.loads(articles_path.read_text(encoding="utf-8"))
    problems: list[str] = []
    result: list[dict] = []
    for a in existing:
        cache = raw_html_dir / f"{a['article_id']}.html"
        if not cache.exists():
            problems.append(f"{a['article_id']}: cache tidak ada ({cache})")
            continue
        html = cache.read_text(encoding="utf-8")
        if not is_valid_article_html(html):
            problems.append(f"{a['article_id']}: cache tidak lolos validasi HTML")
            continue
        art = parse_article(html, a["url"])
        if art is None:
            problems.append(f"{a['article_id']}: parse_article mengembalikan None")
            continue
        result.append(art)
    if problems:
        raise RuntimeError("Parse ulang dibatalkan, tidak ada yang ditulis:\n  " + "\n  ".join(problems))
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--out", type=Path, default=ARTICLES_PATH, help="berkas keluaran (bawaan: articles.json)")
    args = ap.parse_args()
    articles = reparse()
    write_articles(articles, args.out)
    print(f"{len(articles)} artikel di-parse ulang dari cache dan ditulis ke {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
