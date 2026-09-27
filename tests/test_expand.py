"""Uji offline scraping.expand (tanpa jaringan): penentuan jangkar, pengumpulan URL, statistik, alasan gagal."""

import pytest

from scraping import expand
from scraping.expand import (
    article_id_of,
    batch_stats,
    collect_urls,
    scrape_with_reason,
    urls_after_anchor,
)

BASE = "https://turnbackhoax.id/articles/"


def u(aid: int) -> str:
    return f"{BASE}{aid}-judul-{aid}"


def _art(aid: str, date: str = "05/08/2026", **sections: str) -> dict:
    base = {"article_id": aid, "date": date, "label": "SALAH",
            "narasi": "n", "penjelasan": "p", "kesimpulan": "k"}
    base.update(sections)
    return base


def test_article_id_of() -> None:
    assert article_id_of(u(35990)) == "35990"
    assert article_id_of("https://turnbackhoax.id/about") is None


def test_urls_after_anchor() -> None:
    page = [u(3), u(2), u(1)]
    assert urls_after_anchor(page, u(2)) == ([u(1)], True)
    assert urls_after_anchor(page, u(1)) == ([], True)  # jangkar di akhir halaman
    assert urls_after_anchor(page, u(9)) == ([], False)
    assert urls_after_anchor(page, None) == (page, True)


def _fake_pages(monkeypatch: pytest.MonkeyPatch, pages: dict[int, list[str] | None]) -> list[int]:
    fetched: list[int] = []

    def fake_fetch(page: int, session: object) -> list[str] | None:
        fetched.append(page)
        return pages.get(page, [])

    monkeypatch.setattr(expand, "fetch_list_page", fake_fetch)
    monkeypatch.setattr(expand.time, "sleep", lambda s: None)
    return fetched


def test_collect_urls_scans_forward_to_anchor_and_skips_known(monkeypatch: pytest.MonkeyPatch) -> None:
    # halaman bergeser: jangkar (30) kini di halaman 16, bukan 15; id tidak monoton
    fetched = _fake_pages(monkeypatch, {15: [u(40), u(38)], 16: [u(33), u(30), u(29), u(31)],
                                        17: [u(27), u(26), u(25)]})
    urls, last = collect_urls(None, u(30), 15, n=4, known_ids={"26"})
    assert urls == [u(29), u(31), u(27), u(25)], "urutan daftar, lewati yang sudah dimiliki"
    assert last == 17 and fetched == [15, 16, 17]


def test_collect_urls_fails_when_anchor_missing_or_page_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_pages(monkeypatch, {1: [u(5)], 2: [u(4)]})
    with pytest.raises(RuntimeError, match="jangkar"):
        collect_urls(None, u(99), 1, n=5, known_ids=set(), max_scan_pages=2)
    _fake_pages(monkeypatch, {1: None})
    with pytest.raises(RuntimeError, match="gagal diambil"):
        collect_urls(None, u(99), 1, n=5, known_ids=set())


def test_batch_stats() -> None:
    arts = [_art("1", "01/07/2026"), _art("2", "15/12/2025", penjelasan=""), _art("3", "tanggal-rusak", kesimpulan="")]
    fails = [{"url": u(4), "article_id": "4", "alasan": "404 Client Error"},
             {"url": u(5), "article_id": "5", "alasan": "404 Client Error"}]
    s = batch_stats(arts, fails, attempted=5)
    assert (s["berhasil"], s["gagal"], s["tingkat_gagal"]) == (3, 2, 0.4)
    assert s["alasan_gagal"] == {"404 Client Error": 2}
    assert s["artikel_seksi_kosong"] == 2 and s["id_seksi_kosong"] == ["2", "3"]
    assert s["seksi_kosong_per_seksi"] == {"narasi": 0, "penjelasan": 1, "kesimpulan": 1}
    assert s["rentang_tanggal"] == ["2025-12-15", "2026-07-01"]
    assert s["tanggal_tanpa_format_sah"] == 1


def test_batch_stats_empty_batch() -> None:
    s = batch_stats([], [], attempted=0)
    assert s["tingkat_gagal"] == 0.0 and s["rentang_tanggal"] is None


def test_scrape_with_reason_extracts_reason_from_client_log(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing(url: str, session: object) -> tuple[None, bool]:
        print(f"  [gagal] {url} -> 404 Client Error: Not Found")
        return None, True

    monkeypatch.setattr(expand, "scrape_article", failing)
    art, net, reason = scrape_with_reason(u(1), None)
    assert art is None and net is True and reason == "404 Client Error: Not Found"

    monkeypatch.setattr(expand, "scrape_article", lambda url, s: (None, False))
    assert scrape_with_reason(u(1), None)[2].startswith("HTML sah tetapi parse_article")

    monkeypatch.setattr(expand, "scrape_article", lambda url, s: ({"article_id": "1"}, False))
    assert scrape_with_reason(u(1), None) == ({"article_id": "1"}, False, "")


def test_failure_threshold_is_the_owner_choice() -> None:
    assert expand.MAX_FAILURE_RATE == 0.05
