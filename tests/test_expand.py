"""Uji offline scraping.expand (tanpa jaringan): penentuan jangkar, pengumpulan URL, statistik, alasan gagal."""

import json
from pathlib import Path

import pytest

from scraping import expand
from scraping.expand import (
    article_id_of,
    batch_stats,
    collect_new_urls,
    collect_urls,
    record_failure,
    scrape_all,
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


def test_collect_new_urls_stops_at_first_known(monkeypatch: pytest.MonkeyPatch) -> None:
    # id tidak monoton; titik henti = artikel dimiliki PERTAMA dalam urutan daftar
    fetched = _fake_pages(monkeypatch, {1: [u(60), u(58), u(61)], 2: [u(57), u(50), u(56), u(49)],
                                        3: [u(48)]})
    urls, stop = collect_new_urls(None, known_ids={"50", "49", "48"})
    assert urls == [u(60), u(58), u(61), u(57)]
    assert stop["article_id"] == "50" and stop["halaman"] == 2
    assert stop["tak_dikenal_setelah_titik_henti"] == [u(56)], "dilaporkan, tidak diambil"
    assert fetched == [1, 2], "tidak menelusuri halaman setelah titik henti"


def test_collect_new_urls_nothing_new_and_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_pages(monkeypatch, {1: [u(50), u(49)]})
    assert collect_new_urls(None, known_ids={"50"})[0] == []
    _fake_pages(monkeypatch, {1: [u(60)], 2: [u(59)]})
    with pytest.raises(RuntimeError, match="tidak bertemu"):
        collect_new_urls(None, known_ids={"1"}, max_pages=2)
    _fake_pages(monkeypatch, {1: None})
    with pytest.raises(RuntimeError, match="gagal diambil"):
        collect_new_urls(None, known_ids={"1"})


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


def test_scrape_with_reason_extracts_reason_and_retries_from_client_log(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing(url: str, session: object) -> tuple[None, bool]:
        print("  [retry 1/3] ReadTimeout; menunggu 2 dtk")
        print("  [retry 2/3] ReadTimeout; menunggu 4 dtk")
        print(f"  [gagal] {url} -> 404 Client Error: Not Found")
        return None, True

    monkeypatch.setattr(expand, "scrape_article", failing)
    assert scrape_with_reason(u(1), None) == (None, True, "404 Client Error: Not Found", 2)

    monkeypatch.setattr(expand, "scrape_article", lambda url, s: (None, False))
    assert scrape_with_reason(u(1), None)[2].startswith("HTML sah tetapi parse_article")

    def ok_after_retry(url: str, session: object) -> tuple[dict, bool]:
        print("  [retry 1/3] ConnectionError; menunggu 2 dtk")
        return {"article_id": "1"}, True

    monkeypatch.setattr(expand, "scrape_article", ok_after_retry)
    assert scrape_with_reason(u(1), None) == ({"article_id": "1"}, True, "", 1), "retry pada artikel berhasil ikut terhitung"


def test_record_failure_appends_across_runs_never_overwrites(tmp_path: Path) -> None:
    path = tmp_path / "failed_ids.json"
    record_failure({"url": u(1), "article_id": "1", "alasan": "a", "retry": 3}, run="batch_03", path=path)
    record_failure({"url": u(2), "article_id": "2", "alasan": "b", "retry": 0}, run="forward_2026-09-28", path=path)
    record_failure({"url": u(1), "article_id": "1", "alasan": "a", "retry": 3}, run="batch_04", path=path)
    entries = json.loads(path.read_text(encoding="utf-8"))
    assert [(e["article_id"], e["jalan"]) for e in entries] == [
        ("1", "batch_03"), ("2", "forward_2026-09-28"), ("1", "batch_04")], "entri lama dipertahankan, urutan dijaga"
    assert all(e["waktu_utc"] and e["alasan"] for e in entries)


def test_scrape_all_records_each_failure_and_counts_retries(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ledger = tmp_path / "failed_ids.json"
    monkeypatch.setattr(expand, "FAILED_PATH", ledger)
    monkeypatch.setattr(expand, "RETRIES", {"artikel": 0, "halaman_daftar": 0})
    monkeypatch.setattr(expand.time, "sleep", lambda s: None)
    outcomes = {u(1): (_art("1"), True, "", 1), u(2): (None, True, "ReadTimeout setelah 4 percobaan", 3),
                u(3): (None, False, "HTML sah tetapi parse_article mengembalikan None", 0)}
    monkeypatch.setattr(expand, "scrape_with_reason", lambda url, s: outcomes[url])
    arts, fails = scrape_all([u(1), u(2), u(3)], None, run="batch_09")
    assert [a["article_id"] for a in arts] == ["1"]
    assert [(f["article_id"], f["retry"]) for f in fails] == [("2", 3), ("3", 0)]
    assert expand.RETRIES["artikel"] == 4
    logged = json.loads(ledger.read_text(encoding="utf-8"))
    assert [(e["article_id"], e["jalan"]) for e in logged] == [("2", "batch_09"), ("3", "batch_09")]
    assert batch_stats(arts, fails, 3)["id_gagal"] == ["2", "3"]


def test_fetch_list_page_counts_list_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(expand, "RETRIES", {"artikel": 0, "halaman_daftar": 0})

    def flaky_soup(url: str, session: object) -> None:
        print("  [retry 1/3] halaman galat (HTML tidak lolos validasi); menunggu 2 dtk")
        print(f"  [gagal] {url} -> ReadTimeout setelah 4 percobaan")

    monkeypatch.setattr(expand, "get_soup", flaky_soup)
    assert expand.fetch_list_page(5, None) is None
    assert expand.RETRIES == {"artikel": 0, "halaman_daftar": 1}


def test_failure_threshold_is_the_owner_choice() -> None:
    assert expand.MAX_FAILURE_RATE == 0.05
