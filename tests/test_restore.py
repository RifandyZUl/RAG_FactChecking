"""Uji pemulihan articles.json dari daftar artikel (scraping.restore) dan isi archive/v1/article_ids.json."""

import hashlib
import json
from pathlib import Path

import pytest

from scraping.restore import load_article_list, restore

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = [{"article_id": "2", "url": "https://turnbackhoax.id/articles/2-b"},
           {"article_id": "1", "url": "https://turnbackhoax.id/articles/1-a"}]


def _fake_scrape(results: dict[str, dict | None], network: set[str] = frozenset()):
    calls: list[str] = []

    def scrape(url: str) -> tuple[dict | None, bool]:
        calls.append(url)
        return results.get(url), url in network

    return scrape, calls


def test_restore_keeps_list_order() -> None:
    scrape, calls = _fake_scrape({e["url"]: {"article_id": e["article_id"]} for e in ENTRIES})
    articles, problems = restore(ENTRIES, scrape, delay_s=0)
    assert problems == []
    assert [a["article_id"] for a in articles] == ["2", "1"], "urutan wajib sama dengan daftar (sidik jari)"
    assert calls == [e["url"] for e in ENTRIES]


def test_restore_reports_missing_and_mismatched_articles() -> None:
    scrape, _ = _fake_scrape({ENTRIES[0]["url"]: None, ENTRIES[1]["url"]: {"article_id": "999"}})
    articles, problems = restore(ENTRIES, scrape, delay_s=0)
    assert articles == []
    assert any(p.startswith("2:") and "gagal" in p for p in problems)
    assert any(p.startswith("1:") and "berbeda" in p for p in problems)


def test_load_article_list_accepts_object_or_list_and_validates(tmp_path: Path) -> None:
    obj, lst, bad = tmp_path / "o.json", tmp_path / "l.json", tmp_path / "b.json"
    obj.write_text(json.dumps({"artikel": ENTRIES}), encoding="utf-8")
    lst.write_text(json.dumps(ENTRIES), encoding="utf-8")
    bad.write_text(json.dumps([{"article_id": "1"}]), encoding="utf-8")
    assert load_article_list(obj) == load_article_list(lst) == ENTRIES
    with pytest.raises(ValueError):
        load_article_list(bad)


def test_committed_article_list_is_metadata_only_and_matches_archive_fingerprint() -> None:
    """archive/v1/article_ids.json: tanpa isi seksi/tautan, dan daftar id-nya = sidik jari arsip."""
    data = json.loads((ROOT / "archive" / "v1" / "article_ids.json").read_text(encoding="utf-8"))
    allowed = {"article_id", "url", "title", "label", "category", "date"}
    assert data["jumlah"] == len(data["artikel"]) == 150
    assert all(set(a) == allowed for a in data["artikel"]), "hanya metadata; isi seksi dilarang"
    ids = sorted(a["article_id"] for a in data["artikel"])
    meta = json.loads((ROOT / "testset" / "v1.meta.json").read_text(encoding="utf-8"))
    recorded = meta["arsip_indeks_v1_2026-09-25"]["sidik_jari_isi"]["sha256_daftar_artikel"]
    assert hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest() == recorded == data["sha256_daftar_artikel"]
    assert all(a["url"].startswith("https://turnbackhoax.id/articles/") for a in data["artikel"])
