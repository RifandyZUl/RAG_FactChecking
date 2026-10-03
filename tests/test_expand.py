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


# -- pemutus sirkuit ---------------------------------------------------------

NET = "ConnectionError setelah 4 percobaan"
TIMEOUT = "ReadTimeout setelah 4 percobaan"
NOT_FOUND = "404 Client Error: Not Found for url: x"
ERROR_PAGE = "halaman galat (HTML tidak lolos validasi) setelah 4 percobaan"
PARSE_NONE = "HTML sah tetapi parse_article mengembalikan None"


@pytest.mark.parametrize(("reason", "expected"), [
    (NET, True), (TIMEOUT, True), ("ConnectTimeout setelah 4 percobaan", True),
    ("SSLError setelah 4 percobaan", True),
    (NOT_FOUND, False), (ERROR_PAGE, False), (PARSE_NONE, False),
    ("503 Server Error: Service Unavailable for url: x", False), ("", False),
])
def test_is_network_failure_only_counts_network_errors(reason: str, expected: bool) -> None:
    assert expand.is_network_failure(reason) is expected


def _scripted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, outcomes: list[tuple[str, bool]]) -> list[str]:
    """
    Skenario scrape_all: outcomes[i] = (alasan, dari_jaringan); alasan "" berarti berhasil.
    Mengembalikan daftar URL yang benar-benar dicoba (diisi selama jalan).
    """
    monkeypatch.setattr(expand, "FAILED_PATH", tmp_path / "failed_ids.json")
    monkeypatch.setattr(expand, "RETRIES", {"artikel": 0, "halaman_daftar": 0})
    monkeypatch.setattr(expand.time, "sleep", lambda s: None)
    by_url = {u(i): o for i, o in enumerate(outcomes, 1)}
    tried: list[str] = []

    def fake(url: str, session: object) -> tuple[dict | None, bool, str, int]:
        tried.append(url)
        reason, from_network = by_url[url]
        art = None if reason else _art(article_id_of(url) or "")
        return art, from_network, reason, 3 if expand.is_network_failure(reason) else 0

    monkeypatch.setattr(expand, "scrape_with_reason", fake)
    return tried


def _urls(n: int) -> list[str]:
    return [u(i) for i in range(1, n + 1)]


def test_circuit_breaker_stops_on_total_network_outage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # bentuk kejadian kelompok 5: 38 ok, 1 gagal, 2 ok, lalu jaringan putus total sampai akhir
    outcomes = [("", True)] * 38 + [(TIMEOUT, True)] + [("", True)] * 2 + [(NET, True)] * 209
    tried = _scripted(monkeypatch, tmp_path, outcomes)
    with pytest.raises(expand.NetworkDownError) as exc:
        scrape_all(_urls(250), None, run="batch_05")
    limit = expand.MAX_CONSECUTIVE_NETWORK_FAILURES
    assert len(tried) == 41 + limit, "berhenti setelah ambang, bukan mencoba 209 artikel"
    err = exc.value
    assert (err.attempted, err.total, err.consecutive) == (41 + limit, 250, limit)
    assert len(err.articles) == 40 and len(err.failures) == 1 + limit
    ledger = json.loads((tmp_path / "failed_ids.json").read_text(encoding="utf-8"))
    assert len(ledger) == 1 + limit, "yang tercatat gagal hanya yang benar-benar dicoba"


def test_circuit_breaker_ignores_broken_articles_on_healthy_network(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 12 artikel rusak BERUNTUN (404, halaman galat, gagal parse) saat jaringan normal: tidak memutus
    broken = [(NOT_FOUND, True), (ERROR_PAGE, True), (PARSE_NONE, True), (PARSE_NONE, False)] * 3
    tried = _scripted(monkeypatch, tmp_path, [("", True)] * 3 + broken + [("", True)] * 3)
    arts, fails = scrape_all(_urls(18), None, run="batch_09")
    assert len(tried) == 18 and len(arts) == 6 and len(fails) == 12


def test_circuit_breaker_resets_when_server_is_reachable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # gangguan putus-nyambung: 4 gagal jaringan, lalu bukti server terjangkau (berhasil ATAU 404), berulang
    outcomes = [(NET, True)] * 4 + [("", True)] + [(TIMEOUT, True)] * 4 + [(NOT_FOUND, True)] + [(NET, True)] * 4
    tried = _scripted(monkeypatch, tmp_path, outcomes)
    arts, fails = scrape_all(_urls(14), None, run="batch_09", max_network_failures=5)
    assert len(tried) == 14 and len(arts) == 1 and len(fails) == 13


def test_circuit_breaker_cache_hits_do_not_reset_the_count(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # artikel dari cache bukan bukti jaringan hidup (jalan ulang: sebagian artikel sudah ter-cache)
    outcomes = [(NET, True)] * 3 + [("", False)] * 2 + [(NET, True)] * 2 + [("", True)] * 5
    tried = _scripted(monkeypatch, tmp_path, outcomes)
    with pytest.raises(expand.NetworkDownError):
        scrape_all(_urls(12), None, run="batch_09", max_network_failures=5)
    assert len(tried) == 7


def test_circuit_breaker_threshold_is_configurable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    tried = _scripted(monkeypatch, tmp_path, [(NET, True)] * 10)
    with pytest.raises(expand.NetworkDownError):
        scrape_all(_urls(10), None, run="batch_09", max_network_failures=2)
    assert len(tried) == 2


def _fake_run_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, state: dict) -> tuple[Path, Path]:
    exp = tmp_path / "expansion"
    exp.mkdir()
    state_path = exp / "state.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    monkeypatch.setattr(expand, "EXPANSION_DIR", exp)
    monkeypatch.setattr(expand, "STATE_PATH", state_path)
    monkeypatch.setattr(expand, "ARTICLES_PATH", tmp_path / "articles.json")  # tidak ada: basis kosong
    monkeypatch.setattr(expand, "make_session", lambda: None)
    monkeypatch.setattr(expand, "collect_urls", lambda *a, **k: (_urls(20), 120))
    monkeypatch.setattr(expand.sys, "argv", ["expand", "--batch-size", "20"])
    return exp, state_path


def test_main_leaves_state_and_batch_untouched_when_breaker_trips(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    state = {"batch": 4, "anchor_url": u(100), "start_page": 118, "known_ids": ["100", "101"]}
    exp, state_path = _fake_run_dir(monkeypatch, tmp_path, state)
    _scripted(monkeypatch, tmp_path, [("", True)] * 2 + [(NET, True)] * 18)
    monkeypatch.setattr(expand, "FAILED_PATH", exp / "failed_ids.json")

    assert expand.main() == expand.EXIT_NETWORK_DOWN == 4
    assert json.loads(state_path.read_text(encoding="utf-8")) == state, "state.json tidak maju"
    assert not (exp / "batch_05.json").exists() and not (exp / "batch_05_report.json").exists()
    reports = list(exp.glob("batch_05_terputus_*_report.json"))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    limit = expand.MAX_CONSECUTIVE_NETWORK_FAILURES
    assert report["terputus"] is True and report["belum_dicoba"] == 18 - limit
    assert (report["statistik"]["berhasil"], report["statistik"]["gagal"]) == (2, limit)
    assert "TERPUTUS" in capsys.readouterr().out


def test_main_completes_normally_with_broken_articles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # kontrol: tanpa kegagalan, jalur lama tidak berubah (berkas ditulis, state maju, kode 0)
    state = {"batch": 4, "anchor_url": u(100), "start_page": 118, "known_ids": ["100"]}
    exp, state_path = _fake_run_dir(monkeypatch, tmp_path, state)
    _scripted(monkeypatch, tmp_path, [("", True)] * 20)
    monkeypatch.setattr(expand, "FAILED_PATH", exp / "failed_ids.json")

    assert expand.main() == 0
    assert len(json.loads((exp / "batch_05.json").read_text(encoding="utf-8"))) == 20
    new_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert new_state["batch"] == 5 and new_state["anchor_url"] == u(20)
    assert not list(exp.glob("*_terputus_*")) and not list(exp.glob("*_tertahan_*"))


def test_forward_breaker_writes_no_articles_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    exp, _ = _fake_run_dir(monkeypatch, tmp_path, {})
    monkeypatch.setattr(expand, "forward_known_ids", lambda state: {"100"})
    monkeypatch.setattr(expand, "collect_new_urls",
                        lambda s, known, max_pages: (_urls(10), {"url": u(100), "article_id": "100", "halaman": 2}))
    _scripted(monkeypatch, tmp_path, [("", True)] * 3 + [(NET, True)] * 7)
    monkeypatch.setattr(expand, "FAILED_PATH", exp / "failed_ids.json")

    assert expand.run_forward({}, max_pages=5) == expand.EXIT_NETWORK_DOWN
    forward_files = sorted(p.name for p in exp.glob("forward_*"))
    assert len(forward_files) == 1 and "_terputus_" in forward_files[0], "hanya laporan kejadian"


# -- status turunan buku gagal ------------------------------------------------

def _entry(aid: int, run: str, reason: str = NET) -> dict:
    return {"url": u(aid), "article_id": str(aid), "alasan": reason, "retry": 3, "jalan": run,
            "waktu_utc": f"2026-09-28T12:00:{aid:02d}+00:00"}


def test_failure_status_derives_open_and_resolved_without_touching_ledger() -> None:
    entries = [_entry(1, "batch_05"), _entry(2, "batch_05"), _entry(3, "batch_05", NOT_FOUND),
               _entry(2, "batch_05b", TIMEOUT)]
    before = json.dumps(entries)
    status = expand.failure_status(entries, owned={"1", "9"})
    assert (status["entri"], status["id_unik"], status["teratasi"], status["terbuka"]) == (4, 3, 1, 2)
    assert status["id_terbuka"] == ["2", "3"]
    two = status["rincian_terbuka"][0]
    assert (two["kali_gagal"], two["alasan_terakhir"], two["jalan_terakhir"]) == (2, TIMEOUT, "batch_05b")
    assert json.dumps(entries) == before, "buku gagal tidak diubah"
    assert expand.failure_status([], set())["terbuka"] == 0


def test_owned_ids_reads_articles_and_result_files_but_not_reports(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    exp, _ = _fake_run_dir(monkeypatch, tmp_path, {})
    (tmp_path / "articles.json").write_text(json.dumps([_art("1")]), encoding="utf-8")
    (exp / "batch_04.json").write_text(json.dumps([_art("2")]), encoding="utf-8")
    (exp / "forward_2026-09-27.json").write_text(json.dumps([_art("3")]), encoding="utf-8")
    # laporan (termasuk laporan kejadian) berbentuk dict, bukan daftar artikel: tidak boleh dibaca
    for name in ("batch_04_report.json", "batch_05_terputus_20261002T000000Z_report.json",
                 "forward_2026-09-27_report.json"):
        (exp / name).write_text(json.dumps({"gagal": [{"article_id": "99"}]}), encoding="utf-8")
    assert expand.owned_ids() == {"1", "2", "3"}


def test_rerun_resolves_earlier_failures_in_report_and_status(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # jalan ulang kelompok: artikel 1-19 yang dulu gagal kini berhasil; artikel 20 tetap gagal (404 = permanen)
    state = {"batch": 4, "anchor_url": u(100), "start_page": 118, "known_ids": ["100"]}
    exp, _ = _fake_run_dir(monkeypatch, tmp_path, state)
    ledger = exp / "failed_ids.json"
    old = [_entry(i, "batch_05") for i in range(1, 21)]
    ledger.write_text(json.dumps(old), encoding="utf-8")
    _scripted(monkeypatch, tmp_path, [("", True)] * 19 + [(NOT_FOUND, True)])
    monkeypatch.setattr(expand, "FAILED_PATH", ledger)

    assert expand.main() == expand.EXIT_NEEDS_REVIEW == 6, "ditulis; satu kegagalan permanen perlu ditinjau"
    report = json.loads((exp / "batch_05_report.json").read_text(encoding="utf-8"))
    assert report["gagal_terbuka"] == ["20"] and report["gagal_permanen"] == ["20"]
    entries = json.loads(ledger.read_text(encoding="utf-8"))
    assert entries[:20] == old and len(entries) == 21, "entri lama utuh; hanya kegagalan baru ditambahkan"

    capsys.readouterr()
    monkeypatch.setattr(expand.sys, "argv", ["expand", "--failed-status"])
    assert expand.main() == 0
    status = json.loads(capsys.readouterr().out)
    assert (status["id_unik"], status["teratasi"], status["terbuka"]) == (20, 19, 1)
    assert status["rincian_terbuka"][0]["kali_gagal"] == 2
    assert status["id_perlu_tinjauan"] == ["20"] and status["id_bisa_dicoba_ulang"] == []


# -- galat tak terduga saat parse: kegagalan artikel itu, jenisnya terpisah dari jaringan -----

@pytest.mark.parametrize(("reason", "kind"), [
    (NET, "jaringan"), (TIMEOUT, "jaringan"),
    ("galat tak terduga: ValueError: Invalid IPv6 URL (links.py:71 blocked_reason)", "galat_kode"),
    (ERROR_PAGE, "halaman_galat"), (PARSE_NONE, "parse_kosong"), (NOT_FOUND, "http_atau_lain"),
])
def test_failure_kind_separates_code_errors_from_network(reason: str, kind: str) -> None:
    assert expand.failure_kind(reason) == kind


def test_scrape_with_reason_turns_unexpected_exception_into_article_failure(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(expand, "RAW_HTML_DIR", tmp_path)

    def boom(url: str, session: object) -> tuple[dict, bool]:
        print("  [retry 1/3] ReadTimeout; menunggu 2 dtk")
        raise ValueError("Invalid IPv6 URL")

    monkeypatch.setattr(expand, "scrape_article", boom)
    art, from_network, reason, retries = scrape_with_reason(u(7), None)
    assert art is None and retries == 1
    assert from_network is True, "tidak ada cache sebelum pengambilan: dianggap dari jaringan"
    assert reason.startswith("galat tak terduga: ValueError: Invalid IPv6 URL (test_expand.py:")
    assert reason.endswith(" boom)") and not expand.is_network_failure(reason)
    out = capsys.readouterr().out
    assert "Traceback" in out and "[retry 1/3]" in out, "jejak lengkap dan log klien tetap tercetak"

    (tmp_path / "7.html").write_text("<html></html>", encoding="utf-8")
    assert scrape_with_reason(u(7), None)[1] is False, "cache sudah ada: bukan dari jaringan"

    def interrupted(url: str, session: object) -> tuple[dict, bool]:
        raise KeyboardInterrupt

    monkeypatch.setattr(expand, "scrape_article", interrupted)
    with pytest.raises(KeyboardInterrupt):
        scrape_with_reason(u(7), None)


CODE_ERR = "galat tak terduga: ValueError: Invalid IPv6 URL (links.py:71 blocked_reason)"


def test_one_unparseable_article_does_not_abort_the_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # bentuk kejadian kelompok 6: 80 ok, artikel ke-81 melempar galat parse, sisanya ok
    tried = _scripted(monkeypatch, tmp_path, [("", True)] * 80 + [(CODE_ERR, False)] + [("", True)] * 29)
    arts, fails = scrape_all(_urls(110), None, run="batch_06")
    assert len(tried) == 110 and len(arts) == 109
    assert fails == [{"url": u(81), "article_id": "81", "alasan": CODE_ERR, "retry": 0,
                      "jenis": "galat_kode", "exception": "ValueError"}]
    ledger = json.loads((tmp_path / "failed_ids.json").read_text(encoding="utf-8"))
    assert (ledger[0]["jenis"], ledger[0]["exception"]) == ("galat_kode", "ValueError")
    stats = batch_stats(arts, fails, 110)
    assert stats["gagal_per_jenis"] == {"galat_kode": 1} and stats["exception_galat_kode"] == {"ValueError": 1}


def test_systematic_parse_bug_is_visible_and_not_mistaken_for_network(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # semua artikel gagal di-parse (bug kode) + 2 gagal jaringan terpisah: pemutus sirkuit TIDAK terpicu,
    # jalan DITAHAN dengan kode 3 (batas tidak maju), dan laporan memisahkan kedua jenis
    state = {"batch": 5, "anchor_url": u(100), "start_page": 144, "known_ids": ["100"]}
    exp, state_path = _fake_run_dir(monkeypatch, tmp_path, state)
    _scripted(monkeypatch, tmp_path, [(CODE_ERR, True)] * 9 + [(NET, True)] * 2 + [(CODE_ERR, True)] * 9)
    monkeypatch.setattr(expand, "FAILED_PATH", exp / "failed_ids.json")

    assert expand.main() == expand.EXIT_HELD_SYSTEMATIC == 3
    assert json.loads(state_path.read_text(encoding="utf-8")) == state, "batas tidak maju"
    assert not (exp / "batch_06.json").exists() and not (exp / "batch_06_report.json").exists()
    held = list(exp.glob("batch_06_tertahan_*_report.json"))
    assert len(held) == 1
    report = json.loads(held[0].read_text(encoding="utf-8"))
    assert report["keputusan"] == "tahan_sistematis"
    assert report["statistik"]["gagal_per_jenis"] == {"galat_kode": 18, "jaringan": 2}
    assert report["statistik"]["exception_galat_kode"] == {"ValueError": 18}
    out = capsys.readouterr().out
    assert out.count("GAGAL [galat_kode]") == 18 and out.count("GAGAL [jaringan]") == 2
    assert "DITAHAN (kegagalan sistematis)" in out
    monkeypatch.setattr(expand.sys, "argv", ["expand", "--failed-status"])
    assert expand.main() == 0
    assert json.loads(capsys.readouterr().out)["terbuka_per_jenis"] == {"galat_kode": 18, "jaringan": 2}


def test_batch_stats_classifies_old_ledger_entries_without_kind() -> None:
    fails = [{"url": u(1), "article_id": "1", "alasan": NET}, {"url": u(2), "article_id": "2", "alasan": NOT_FOUND}]
    stats = batch_stats([], fails, 2)
    assert stats["gagal_per_jenis"] == {"jaringan": 1, "http_atau_lain": 1} and stats["exception_galat_kode"] == {}


# -- jalan dengan kegagalan tidak memajukan batas "sudah dimiliki" -------------

@pytest.mark.parametrize(("reason", "attempts", "permanent"), [
    (NOT_FOUND, 1, True), ("410 Client Error: Gone for url: x", 1, True),
    (CODE_ERR, 1, False), (CODE_ERR, 2, False), (CODE_ERR, 3, True),
    (NET, 0, False), (ERROR_PAGE, 1, False), (PARSE_NONE, 3, True),
    ("503 Server Error: Service Unavailable for url: x", 1, False),
])
def test_is_permanent_failure(reason: str, attempts: int, permanent: bool) -> None:
    assert expand.is_permanent_failure(reason, attempts) is permanent


def _fail(aid: int, reason: str) -> dict:
    return {"url": u(aid), "article_id": str(aid), "alasan": reason, "retry": 0}


def test_hold_decision_rules() -> None:
    hold = expand.hold_decision
    assert hold([], 20, {}) == ("tulis", [], [])
    # satu artikel gagal dan masih bisa dicoba lagi: tahan
    assert hold([_fail(1, CODE_ERR)], 20, {"1": 1}) == ("tahan_coba_lagi", ["1"], [])
    assert hold([_fail(1, NET)], 5, {}) == ("tahan_coba_lagi", ["1"], []), "jaringan: tidak pernah permanen"
    # sama, tetapi sudah MAX_ATTEMPTS kali gagal antar-jalan, atau 404: permanen -> tulis (perlu tinjauan)
    assert hold([_fail(1, CODE_ERR)], 20, {"1": 3}) == ("tulis", [], ["1"])
    assert hold([_fail(1, NOT_FOUND)], 5, {"1": 1}) == ("tulis", [], ["1"])
    # sistematis (>= 2 gagal dan > 5%): tahan sampai manusia turun tangan, walau semuanya permanen
    assert hold([_fail(1, NOT_FOUND), _fail(2, NOT_FOUND)], 20, {"1": 1, "2": 1})[0] == "tahan_sistematis"
    assert hold([_fail(i, CODE_ERR) for i in range(1, 6)], 5, {str(i): 9 for i in range(1, 6)})[0] == "tahan_sistematis"
    # dua gagal tetapi <= 5%: bukan sistematis
    assert hold([_fail(1, NOT_FOUND), _fail(2, CODE_ERR)], 250, {"1": 1, "2": 1}) == ("tahan_coba_lagi", ["2"], ["1"])
    assert hold([_fail(1, NOT_FOUND), _fail(2, NOT_FOUND)], 250, {})[0] == "tulis"
    # keputusan manusia
    assert hold([_fail(i, CODE_ERR) for i in range(1, 6)], 5, {}, accept=True)[0] == "tulis"


def test_run_with_retryable_failure_is_held_until_it_succeeds_or_becomes_permanent(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Bentuk celah lama: satu artikel gagal di-parse; dulu state maju dan artikel itu tak pernah dicoba lagi."""
    state = {"batch": 5, "anchor_url": u(100), "start_page": 144, "known_ids": ["100"]}
    exp, state_path = _fake_run_dir(monkeypatch, tmp_path, state)
    ledger = exp / "failed_ids.json"
    outcomes = [("", True)] * 7 + [(CODE_ERR, False)] + [("", True)] * 12

    for attempt in (1, 2):
        _scripted(monkeypatch, tmp_path, outcomes)
        monkeypatch.setattr(expand, "FAILED_PATH", ledger)
        assert expand.main() == expand.EXIT_HELD_RETRY == 5
        assert json.loads(state_path.read_text(encoding="utf-8")) == state, "batas tidak maju"
        assert not (exp / "batch_06.json").exists()
        assert len(list(exp.glob("batch_06_tertahan_*_report.json"))) >= 1
        assert len(json.loads(ledger.read_text(encoding="utf-8"))) == attempt
    assert "akan dicoba lagi" in capsys.readouterr().out

    # percobaan ke-3 tetap gagal -> permanen: ditulis, batas maju, artikel 8 ditandai perlu tinjauan
    _scripted(monkeypatch, tmp_path, outcomes)
    monkeypatch.setattr(expand, "FAILED_PATH", ledger)
    assert expand.main() == expand.EXIT_NEEDS_REVIEW
    assert [a["article_id"] for a in json.loads((exp / "batch_06.json").read_text(encoding="utf-8"))].count("8") == 0
    report = json.loads((exp / "batch_06_report.json").read_text(encoding="utf-8"))
    assert report["gagal_permanen"] == ["8"] and report["gagal_terbuka"] == ["8"]
    assert json.loads(state_path.read_text(encoding="utf-8"))["batch"] == 6
    status = expand.failure_status(expand.load_failures(ledger), expand.owned_ids())
    assert status["id_perlu_tinjauan"] == ["8"] and status["id_bisa_dicoba_ulang"] == []


def test_held_run_succeeds_on_rerun_and_then_advances(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    state = {"batch": 5, "anchor_url": u(100), "start_page": 144, "known_ids": ["100"]}
    exp, state_path = _fake_run_dir(monkeypatch, tmp_path, state)
    ledger = exp / "failed_ids.json"
    _scripted(monkeypatch, tmp_path, [("", True)] * 19 + [(NET, True)])
    monkeypatch.setattr(expand, "FAILED_PATH", ledger)
    assert expand.main() == expand.EXIT_HELD_RETRY

    _scripted(monkeypatch, tmp_path, [("", False)] * 19 + [("", True)])  # 19 dari cache, yang gagal kini berhasil
    monkeypatch.setattr(expand, "FAILED_PATH", ledger)
    assert expand.main() == 0
    assert len(json.loads((exp / "batch_06.json").read_text(encoding="utf-8"))) == 20
    assert json.loads(state_path.read_text(encoding="utf-8"))["batch"] == 6
    assert expand.failure_status(expand.load_failures(ledger), expand.owned_ids())["terbuka"] == 0


def test_accept_failures_writes_despite_systematic_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    state = {"batch": 4, "anchor_url": u(100), "start_page": 118, "known_ids": ["100"]}
    exp, state_path = _fake_run_dir(monkeypatch, tmp_path, state)
    monkeypatch.setattr(expand.sys, "argv", ["expand", "--batch-size", "20", "--accept-failures"])
    _scripted(monkeypatch, tmp_path, [("", True)] * 12 + [(NOT_FOUND, True)] * 8)
    monkeypatch.setattr(expand, "FAILED_PATH", exp / "failed_ids.json")
    assert expand.main() == expand.EXIT_NEEDS_REVIEW
    assert len(json.loads((exp / "batch_05.json").read_text(encoding="utf-8"))) == 12
    assert json.loads(state_path.read_text(encoding="utf-8"))["batch"] == 5


def _forward_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    exp, _ = _fake_run_dir(monkeypatch, tmp_path, {})
    monkeypatch.setattr(expand, "forward_known_ids", lambda state: {"100"})
    monkeypatch.setattr(expand, "collect_new_urls",
                        lambda s, known, max_pages: (_urls(5), {"url": u(100), "article_id": "100", "halaman": 1}))
    return exp


def test_forward_run_with_failure_writes_nothing_so_the_boundary_does_not_move(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Mode maju: bila artikel terbaru ditulis sebagai 'dimiliki', artikel gagal di bawahnya terlewat selamanya."""
    exp = _forward_dir(monkeypatch, tmp_path)
    _scripted(monkeypatch, tmp_path, [("", True), ("", True), (CODE_ERR, True), ("", True), ("", True)])
    monkeypatch.setattr(expand, "FAILED_PATH", exp / "failed_ids.json")
    assert expand.run_forward({}, max_pages=5) == expand.EXIT_HELD_RETRY
    names = sorted(f.name for f in exp.glob("forward_*"))
    assert len(names) == 1 and "_tertahan_" in names[0], "tidak ada forward_<tanggal>.json"

    _scripted(monkeypatch, tmp_path, [("", False)] * 5)  # jalan berikutnya: semuanya berhasil
    monkeypatch.setattr(expand, "FAILED_PATH", exp / "failed_ids.json")
    assert expand.run_forward({}, max_pages=5) == 0
    written = [f for f in exp.glob("forward_*.json") if not f.name.endswith("_report.json")]
    assert len(written) == 1 and len(json.loads(written[0].read_text(encoding="utf-8"))) == 5


# -- langkah coba-ulang dari failed_ids.json ----------------------------------

def _retry_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, entries: list[dict]) -> Path:
    exp, _ = _fake_run_dir(monkeypatch, tmp_path, {})
    ledger = exp / "failed_ids.json"
    ledger.write_text(json.dumps(entries), encoding="utf-8")
    monkeypatch.setattr(expand, "FAILED_PATH", ledger)
    return exp


def _retry_outcomes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, exp: Path, by_id: dict[int, tuple[str, bool]]) -> list[str]:
    tried = _scripted(monkeypatch, tmp_path, [by_id.get(i, ("", True)) for i in range(1, max(by_id) + 1)])
    monkeypatch.setattr(expand, "FAILED_PATH", exp / "failed_ids.json")
    return tried


def test_retry_failed_fetches_open_failures_by_url_and_resolves_them(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    entries = [_entry(1, "batch_05"), _entry(2, "batch_05", CODE_ERR), _entry(3, "batch_05", NOT_FOUND),
               _entry(4, "forward_2026-10-01")]
    exp = _retry_dir(monkeypatch, tmp_path, entries)
    (exp / "batch_05.json").write_text(json.dumps([_art("4")]), encoding="utf-8")  # 4 sudah dimiliki: bukan sasaran
    tried = _retry_outcomes(monkeypatch, tmp_path, exp, {1: ("", True), 2: ("", False)})

    monkeypatch.setattr(expand.sys, "argv", ["expand", "--retry-failed"])
    assert expand.main() == expand.EXIT_NEEDS_REVIEW, "3 (404) tetap terbuka dan perlu ditinjau"
    assert tried == [u(1), u(2)], "hanya yang terbuka dan layak dicoba; URL dari buku gagal"
    out = [f for f in exp.glob("retry_*.json") if not f.name.endswith("_report.json")]
    assert len(out) == 1 and [a["article_id"] for a in json.loads(out[0].read_text(encoding="utf-8"))] == ["1", "2"]
    assert expand.owned_ids() >= {"1", "2", "4"}, "hasil coba-ulang terhitung dimiliki"
    status = expand.failure_status(expand.load_failures(exp / "failed_ids.json"), expand.owned_ids())
    assert (status["teratasi"], status["id_terbuka"], status["id_perlu_tinjauan"]) == (3, ["3"], ["3"])
    assert json.loads((exp / "failed_ids.json").read_text(encoding="utf-8")) == entries, "buku gagal tidak ditimpa"
    report = json.loads(next(exp.glob("retry_*_report.json")).read_text(encoding="utf-8"))
    assert report["berhasil"] == ["1", "2"] and report["perlu_tinjauan"] == ["3"]


def test_retry_failed_include_permanent_and_still_failing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    entries = [_entry(1, "batch_05", CODE_ERR)] * 3 + [_entry(2, "batch_05", NET)]
    exp = _retry_dir(monkeypatch, tmp_path, entries)
    tried = _retry_outcomes(monkeypatch, tmp_path, exp, {2: (NET, True)})
    monkeypatch.setattr(expand.sys, "argv", ["expand", "--retry-failed"])
    assert expand.main() == expand.EXIT_HELD_RETRY and tried == [u(2)], "1 permanen: tidak diambil tanpa izin"
    assert len(json.loads((exp / "failed_ids.json").read_text(encoding="utf-8"))) == 5, "kegagalan baru dicatat"

    tried = _retry_outcomes(monkeypatch, tmp_path, exp, {1: ("", False), 2: ("", True)})
    monkeypatch.setattr(expand.sys, "argv", ["expand", "--retry-failed", "--include-permanent"])
    assert expand.main() == 0 and tried == [u(2), u(1)]
    assert expand.failure_status(expand.load_failures(exp / "failed_ids.json"), expand.owned_ids())["terbuka"] == 0


def test_retry_failed_keeps_partial_results_when_network_drops(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    exp = _retry_dir(monkeypatch, tmp_path, [_entry(i, "batch_05") for i in range(1, 9)])
    _retry_outcomes(monkeypatch, tmp_path, exp, {1: ("", True), 2: ("", True), **{i: (NET, True) for i in range(3, 9)}})
    monkeypatch.setattr(expand.sys, "argv", ["expand", "--retry-failed"])
    assert expand.main() == expand.EXIT_NETWORK_DOWN
    out = [f for f in exp.glob("retry_*.json") if not f.name.endswith("_report.json")]
    assert [a["article_id"] for a in json.loads(out[0].read_text(encoding="utf-8"))] == ["1", "2"], "hasil sebagian disimpan"


def test_retry_failed_with_nothing_open_does_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    exp = _retry_dir(monkeypatch, tmp_path, [_entry(1, "batch_05")])
    (exp / "batch_05.json").write_text(json.dumps([_art("1")]), encoding="utf-8")
    tried = _retry_outcomes(monkeypatch, tmp_path, exp, {1: ("", True)})
    monkeypatch.setattr(expand.sys, "argv", ["expand", "--retry-failed"])
    assert expand.main() == 0 and tried == [] and not list(exp.glob("retry_*"))


# -- kegagalan jaringan tidak dihitung ke batas percobaan antar-jalan ---------

def test_attempts_by_id_counts_only_non_network_failures() -> None:
    entries = [_entry(1, "a", NET), _entry(1, "b", TIMEOUT), _entry(1, "c", NET), _entry(1, "d", CODE_ERR),
               _entry(2, "a", CODE_ERR), _entry(2, "b", PARSE_NONE), _entry(2, "c", ERROR_PAGE),
               {**_entry(3, "a", "apa saja"), "jenis": "jaringan"}, _entry(4, "a", NOT_FOUND)]
    assert expand.attempts_by_id(entries) == {"1": 1, "2": 3, "4": 1}


def test_internet_down_for_days_does_not_mark_healthy_articles_permanent(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """
    Internet mati tiga hari: tiap hari lima artikel pertama gagal (jaringan) sebelum pemutus sirkuit
    aktif. Dulu hitungan itu membuat kelimanya 'permanen' pada hari keempat.
    """
    state = {"batch": 5, "anchor_url": u(100), "start_page": 144, "known_ids": ["100"]}
    exp, state_path = _fake_run_dir(monkeypatch, tmp_path, state)
    ledger = exp / "failed_ids.json"
    limit = expand.MAX_CONSECUTIVE_NETWORK_FAILURES
    for day in (1, 2, 3):
        _scripted(monkeypatch, tmp_path, [(NET, True)] * 20)
        monkeypatch.setattr(expand, "FAILED_PATH", ledger)
        assert expand.main() == expand.EXIT_NETWORK_DOWN
        assert len(json.loads(ledger.read_text(encoding="utf-8"))) == day * limit
    status = expand.failure_status(expand.load_failures(ledger), expand.owned_ids())
    assert status["id_perlu_tinjauan"] == [], "tidak ada yang ditandai permanen"
    assert status["id_bisa_dicoba_ulang"] == [str(i) for i in range(1, limit + 1)]
    assert all(r["kali_gagal"] == 3 and r["kali_gagal_non_jaringan"] == 0 for r in status["rincian_terbuka"])
    assert json.loads(state_path.read_text(encoding="utf-8")) == state

    # hari ke-4: internet kembali, tetapi artikel 1 gagal di-parse SEKALI -> ditahan (masih bisa dicoba
    # lagi), bukan langsung permanen karena tiga kegagalan jaringan sebelumnya
    _scripted(monkeypatch, tmp_path, [(CODE_ERR, True)] + [("", True)] * 19)
    monkeypatch.setattr(expand, "FAILED_PATH", ledger)
    assert expand.main() == expand.EXIT_HELD_RETRY
    held = sorted(exp.glob("batch_06_tertahan_*_report.json"))[-1]
    report = json.loads(held.read_text(encoding="utf-8"))
    assert report["gagal_bisa_dicoba_lagi"] == ["1"] and report["gagal_permanen"] == []

    # hari ke-5: semuanya berhasil -> ditulis, batas maju, tidak ada yang terbuka
    _scripted(monkeypatch, tmp_path, [("", True)] * 20)
    monkeypatch.setattr(expand, "FAILED_PATH", ledger)
    assert expand.main() == 0
    assert len(json.loads((exp / "batch_06.json").read_text(encoding="utf-8"))) == 20
    assert expand.failure_status(expand.load_failures(ledger), expand.owned_ids())["terbuka"] == 0


def test_isolated_network_failure_on_many_days_never_becomes_permanent(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Satu artikel gagal karena jaringan (di bawah pemutus sirkuit) lima hari berturut-turut: tetap ditahan."""
    state = {"batch": 5, "anchor_url": u(100), "start_page": 144, "known_ids": ["100"]}
    exp, state_path = _fake_run_dir(monkeypatch, tmp_path, state)
    ledger = exp / "failed_ids.json"
    for _ in range(5):
        _scripted(monkeypatch, tmp_path, [("", True)] * 9 + [(TIMEOUT, True)] + [("", True)] * 10)
        monkeypatch.setattr(expand, "FAILED_PATH", ledger)
        assert expand.main() == expand.EXIT_HELD_RETRY
    assert json.loads(state_path.read_text(encoding="utf-8")) == state and not (exp / "batch_06.json").exists()
    status = expand.failure_status(expand.load_failures(ledger), expand.owned_ids())
    assert status["id_bisa_dicoba_ulang"] == ["10"] and status["id_perlu_tinjauan"] == []


def test_non_network_failures_still_become_permanent_even_with_network_failures_in_between(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    entries = [_entry(1, "a", CODE_ERR), _entry(1, "b", NET), _entry(1, "c", CODE_ERR), _entry(1, "d", NET)]
    assert expand.hold_decision([_fail(1, CODE_ERR)], 20, expand.attempts_by_id(entries + [_entry(1, "e", CODE_ERR)])) == (
        "tulis", [], ["1"])
    assert expand.hold_decision([_fail(1, CODE_ERR)], 20, expand.attempts_by_id(entries))[0] == "tahan_coba_lagi"
