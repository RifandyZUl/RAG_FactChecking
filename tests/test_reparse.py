"""Uji parse ulang offline (scraping.reparse)."""

import json
import shutil

import pytest

from _fakes import FIXTURE_DIR
from scraping.parser import parse_article
from scraping.pipeline import write_articles
from scraping.reparse import reparse
from test_parser import ARTICLE_URLS


def _setup(tmp_path):
    raw = tmp_path / "raw_html"
    raw.mkdir()
    for aid in ARTICLE_URLS:
        shutil.copyfile(FIXTURE_DIR / f"{aid}.html", raw / f"{aid}.html")
    existing = tmp_path / "articles.json"
    existing.write_text(json.dumps([{"article_id": aid, "url": url} for aid, url in ARTICLE_URLS.items()]),
                        encoding="utf-8")
    return raw, existing


def test_reparse_matches_direct_parse_in_same_order(tmp_path) -> None:
    raw, existing = _setup(tmp_path)
    result = reparse(existing, raw)
    expected = [parse_article((FIXTURE_DIR / f"{aid}.html").read_text(encoding="utf-8"), url)
                for aid, url in ARTICLE_URLS.items()]
    assert result == expected and [a["article_id"] for a in result] == list(ARTICLE_URLS)

    # penulis yang sama dengan pipeline: byte hasil reparse == byte penulisan langsung
    out_a, out_b = tmp_path / "a.json", tmp_path / "b.json"
    write_articles(result, out_a)
    write_articles(expected, out_b)
    assert out_a.read_bytes() == out_b.read_bytes()


def test_reparse_fails_hard_on_missing_or_invalid_cache(tmp_path) -> None:
    raw, existing = _setup(tmp_path)
    (raw / "36738.html").unlink()
    (raw / "36737.html").write_text("<html>Terjadi kesalahan saat mengambil data</html>", encoding="utf-8")
    with pytest.raises(RuntimeError) as e:
        reparse(existing, raw)
    assert "36738" in str(e.value) and "36737" in str(e.value) and "dibatalkan" in str(e.value)
