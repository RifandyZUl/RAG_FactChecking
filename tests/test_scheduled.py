"""Uji pembungkus pembaruan berkala (scraping.scheduled): tanpa jaringan, tanpa notifikasi sungguhan."""

import json
from pathlib import Path

import pytest

from scraping import expand, scheduled

BASE = "https://turnbackhoax.id/articles/"


def _art(aid: str, label: str = "SALAH", **over: object) -> dict:
    art = {"article_id": aid, "url": f"{BASE}{aid}-judul", "title": "Judul", "title_raw": f"[{label}] Judul",
           "label": label, "category": "Politik", "date": "03/10/2026", "narasi": "n", "penjelasan": "p",
           "kesimpulan": "k", "references_raw": [], "references": [], "references_filtered": [], "claim_sources": []}
    art.update(over)
    return art


class Env:
    """Lingkungan jalan tiruan: direktori sementara, expand.run_forward/run_retry terskrip, notifikasi dicatat."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        self.exp = tmp_path / "expansion"
        self.exp.mkdir()
        self.marker = tmp_path / "PERHATIAN_PEMBARUAN.txt"
        self.toasts: list[tuple[str, str]] = []
        self.forward_calls = 0
        self.retry_calls = 0
        self.forward_result: object = 0  # int, exception, atau list artikel (ditulis sebagai hasil hari itu)
        self.retry_result = 0
        self.failures: list[dict] = []
        articles = tmp_path / "articles.json"
        articles.write_text(json.dumps([_art("100")]), encoding="utf-8")
        monkeypatch.setattr(expand, "EXPANSION_DIR", self.exp)
        monkeypatch.setattr(expand, "STATE_PATH", self.exp / "state.json")
        monkeypatch.setattr(expand, "FAILED_PATH", self.exp / "failed_ids.json")
        monkeypatch.setattr(expand, "ARTICLES_PATH", articles)
        monkeypatch.setattr(scheduled, "ARTICLES_PATH", articles)
        monkeypatch.setattr(scheduled, "MARKER_PATH", self.marker)
        monkeypatch.setattr(expand, "load_state", dict)
        monkeypatch.setattr(expand, "run_forward", self._forward)
        monkeypatch.setattr(expand, "run_retry", self._retry)
        monkeypatch.setattr(scheduled, "notify_windows", lambda t, b: self.toasts.append((t, b)) or True)

    def _forward(self, state: dict, max_pages: int) -> int:
        self.forward_calls += 1
        if isinstance(self.forward_result, Exception):
            raise self.forward_result
        if isinstance(self.forward_result, list):
            today = scheduled.now_utc().astimezone(scheduled.ZoneInfo("Asia/Jakarta")).date().isoformat()
            (self.exp / f"forward_{today}.json").write_text(json.dumps(self.forward_result), encoding="utf-8")
            return 0
        return int(self.forward_result)  # type: ignore[arg-type]

    def _retry(self, include_permanent: bool) -> int:
        self.retry_calls += 1
        return self.retry_result

    def add_failure(self, aid: str, reason: str, times: int = 1) -> None:
        self.failures += [{"url": f"{BASE}{aid}-judul", "article_id": aid, "alasan": reason, "retry": 0, "jalan": "x",
                           "waktu_utc": "2026-10-03T00:00:00+00:00"}] * times
        (self.exp / "failed_ids.json").write_text(json.dumps(self.failures), encoding="utf-8")

    def status(self) -> dict:
        return json.loads((self.exp / scheduled.STATUS_NAME).read_text(encoding="utf-8"))


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Env:
    return Env(monkeypatch, tmp_path)


def test_clean_run_queues_articles_writes_status_and_no_marker(env: Env) -> None:
    env.forward_result = [_art("201"), _art("202", "PENIPUAN")]
    assert scheduled.run_once() == 0
    s = env.status()
    assert (s["kode_keluar"], s["arti"], s["antrean_belum_digabung"]) == (0, "bersih", 2)
    assert s["kualitas"]["artikel"] == 2 and not s["kualitas"]["tahan_penggabungan"] and s["artikel_baru"] == 2
    assert not env.marker.exists() and env.toasts == [] and s["notifikasi"] == "tidak perlu"
    assert not (env.exp / scheduled.LOCK_NAME).exists(), "kunci dilepas"
    assert Path(s["log"]).exists() and "mode maju" in Path(s["log"]).read_text(encoding="utf-8")
    assert len((env.exp / scheduled.HISTORY_NAME).read_text(encoding="utf-8").splitlines()) == 1


def test_network_down_writes_marker_and_notifies_then_clean_run_removes_marker(env: Env) -> None:
    env.forward_result = expand.EXIT_NETWORK_DOWN  # pemutus sirkuit expand
    assert scheduled.run_once() == expand.EXIT_NETWORK_DOWN
    text = env.marker.read_text(encoding="utf-8")
    assert "Kode keluar  : 4" in text and "jaringan putus" in text and "pembaruan_status.json" in text
    assert len(env.toasts) == 1 and "Kode 4" in env.toasts[0][1] and env.status()["notifikasi"] == "terkirim"

    env.forward_result = [_art("201")]
    assert scheduled.run_once() == 0
    assert not env.marker.exists(), "penanda dihapus pada jalan bersih berikutnya"
    assert len(env.toasts) == 1


def test_list_page_failure_counts_as_network_down(env: Env) -> None:
    """Jaringan mati sejak awal: permintaan pertama (halaman daftar) yang gagal, bukan artikel."""
    env.forward_result = RuntimeError("halaman daftar 1 gagal diambil")
    assert scheduled.run_once() == expand.EXIT_NETWORK_DOWN
    assert "RuntimeError: halaman daftar 1 gagal diambil" in env.marker.read_text(encoding="utf-8")
    assert len(env.toasts) == 1


@pytest.mark.parametrize(("exc", "code"), [
    (RuntimeError("tidak bertemu artikel yang sudah dimiliki dalam 30 halaman"), scheduled.EXIT_BOUNDARY_LOST),
    (KeyError("anchor_url"), scheduled.EXIT_UNEXPECTED),
    (RuntimeError("lain"), scheduled.EXIT_UNEXPECTED),
])
def test_other_exceptions_are_reported_not_swallowed(env: Env, exc: Exception, code: int) -> None:
    env.forward_result = exc
    assert scheduled.run_once() == code
    assert type(exc).__name__ in env.status()["galat"] and env.marker.exists() and len(env.toasts) == 1
    assert not (env.exp / scheduled.LOCK_NAME).exists(), "kunci dilepas walau ada galat"


def test_held_and_review_codes_are_passed_through(env: Env) -> None:
    for code in (expand.EXIT_HELD_RETRY, expand.EXIT_HELD_SYSTEMATIC, expand.EXIT_NEEDS_REVIEW):
        env.forward_result = code
        assert scheduled.run_once() == code
        assert f"Kode keluar  : {code}" in env.marker.read_text(encoding="utf-8")


def test_new_or_unreadable_label_holds_merging_and_notifies(env: Env) -> None:
    env.forward_result = [_art("201"), _art("202", "MENYESATKAN"), _art("203", "TIDAK DIKETAHUI"), _art("204", "KOMEDI")]
    assert scheduled.run_once() == expand.EXIT_NEEDS_REVIEW
    q = env.status()["kualitas"]
    assert q["tahan_penggabungan"] and q["label_belum_ditinjau"] == ["MENYESATKAN", "TIDAK DIKETAHUI"]
    assert q["id_label_belum_ditinjau"] == ["202", "203"]
    assert "Penggabungan DITAHAN" in env.marker.read_text(encoding="utf-8") and len(env.toasts) == 1


def test_quality_report_flags() -> None:
    arts = [_art("1", narasi=""), _art("2", references_filtered=[{"url": "http://x]", "reasons": ["URL tidak sah"]}]),
            _art("3"), _art("3"), _art("100")]
    q = scheduled.quality_report(arts, owned_before={"100"})
    assert q["seksi_kosong"] == ["1"] and q["url_tidak_sah"] == ["2"]
    assert q["duplikat"] == 1 and q["tumpang_tindih_dengan_yang_dimiliki"] == ["100"] and q["tahan_penggabungan"]
    clean = scheduled.quality_report([_art("1", narasi=""), _art("2", "SATIR")], owned_before=set())
    assert not clean["tahan_penggabungan"], "seksi kosong hanya dilaporkan; SATIR sudah ditinjau"


def test_open_retryable_failures_are_retried_before_forward(env: Env) -> None:
    env.add_failure("150", "galat tak terduga: ValueError: x (a.py:1 f)")
    env.forward_result = [_art("201")]
    assert scheduled.run_once() == 0 and env.retry_calls == 1 and env.forward_calls == 1

    env.retry_result = expand.EXIT_NETWORK_DOWN  # jaringan putus saat coba ulang: mode maju tidak dijalankan
    (next(env.exp.glob("forward_*.json"))).unlink()
    assert scheduled.run_once() == expand.EXIT_NETWORK_DOWN and env.forward_calls == 1


def test_permanent_failure_keeps_notifying_until_reviewed(env: Env) -> None:
    env.add_failure("150", "404 Client Error: Not Found for url: x")
    env.forward_result = [_art("201")]
    assert scheduled.run_once() == expand.EXIT_NEEDS_REVIEW
    assert env.retry_calls == 0, "kegagalan permanen tidak dicoba ulang otomatis"
    assert "['150']" in env.marker.read_text(encoding="utf-8")


def test_missed_schedule_can_run_twice_a_day_without_refetching(env: Env) -> None:
    """Jalan susulan (laptop baru menyala) lalu jalan terjadwal di hari yang sama: yang kedua tidak mengambil lagi."""
    env.forward_result = [_art("201")]
    assert scheduled.run_once() == 0 and scheduled.run_once() == 0
    assert env.forward_calls == 1 and env.status()["mode_maju"].startswith("dilewati")
    assert env.status()["antrean_belum_digabung"] == 1


def test_lock_prevents_overlapping_runs_and_stale_lock_is_taken_over(env: Env) -> None:
    lock = env.exp / scheduled.LOCK_NAME
    lock.write_text("{}", encoding="utf-8")
    assert scheduled.run_once() == scheduled.EXIT_LOCKED
    assert env.forward_calls == 0 and lock.exists() and not env.marker.exists(), "jalan yang dilewati tidak mengubah apa pun"
    assert scheduled.acquire_lock(lock, now=lock.stat().st_mtime + scheduled.LOCK_STALE_SECONDS + 1), "kunci basi diambil alih"


def test_stops_trying_after_three_systematic_holds_until_reset(env: Env) -> None:
    env.forward_result = expand.EXIT_HELD_SYSTEMATIC
    for _ in range(scheduled.MAX_CONSECUTIVE_SYSTEMATIC):
        assert scheduled.run_once() == expand.EXIT_HELD_SYSTEMATIC
    assert env.forward_calls == 3
    assert scheduled.run_once() == expand.EXIT_HELD_SYSTEMATIC and env.forward_calls == 3, "jalan ke-4 tidak mencoba lagi"
    assert env.status()["berhenti_mencoba"] is True and "BERHENTI MENCOBA" in env.marker.read_text(encoding="utf-8")

    scheduled.reset()
    env.forward_result = [_art("201")]
    assert scheduled.run_once() == 0 and env.forward_calls == 4 and not env.marker.exists()


def test_network_failures_never_trigger_stop_trying(env: Env) -> None:
    env.forward_result = expand.EXIT_NETWORK_DOWN
    for _ in range(6):
        assert scheduled.run_once() == expand.EXIT_NETWORK_DOWN
    assert env.forward_calls == 6, "internet mati berhari-hari: tetap dicoba setiap jalan"


def test_no_notify_still_writes_marker(env: Env) -> None:
    env.forward_result = expand.EXIT_NETWORK_DOWN
    assert scheduled.run_once(notify=False) == expand.EXIT_NETWORK_DOWN
    assert env.marker.exists() and env.toasts == [] and "dimatikan" in env.status()["notifikasi"]


def test_notify_failure_is_recorded_not_raised(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scheduled, "notify_windows", lambda t, b: False)
    env.forward_result = expand.EXIT_NETWORK_DOWN
    assert scheduled.run_once() == expand.EXIT_NETWORK_DOWN
    assert env.status()["notifikasi"] == "GAGAL dikirim" and env.marker.exists()


def test_unreviewed_label_in_queue_keeps_marker_on_later_runs_until_merged(env: Env) -> None:
    """
    Cacat yang ditemukan pada percobaan manual 2026-10-03: jalan kedua (tidak mengambil apa pun) dianggap
    bersih dan menghapus penanda, padahal artikel berlabel baru masih di antrean.
    """
    env.forward_result = [_art("201"), _art("202", "MENYESATKAN")]
    assert scheduled.run_once() == expand.EXIT_NEEDS_REVIEW and env.marker.exists()
    assert scheduled.run_once() == expand.EXIT_NEEDS_REVIEW, "jalan susulan di hari yang sama: masih perlu ditinjau"
    assert env.marker.exists() and env.status()["kualitas"]["id_label_belum_ditinjau"] == ["202"]
    assert env.forward_calls == 1

    # setelah pemilik proyek menggabungkan antrean ke articles.json, jalan berikutnya bersih
    merged = json.loads(expand.ARTICLES_PATH.read_text(encoding="utf-8")) + [_art("201"), _art("202", "MENYESATKAN")]
    expand.ARTICLES_PATH.write_text(json.dumps(merged), encoding="utf-8")
    assert scheduled.run_once() == 0 and not env.marker.exists()
    assert env.status()["antrean_belum_digabung"] == 0


def test_pending_articles_lists_unmerged_articles_from_all_result_files(env: Env) -> None:
    (env.exp / "batch_07.json").write_text(json.dumps([_art("100"), _art("90")]), encoding="utf-8")
    (env.exp / "forward_2026-10-01.json").write_text(json.dumps([_art("201")]), encoding="utf-8")
    (env.exp / "retry_2026-10-02.json").write_text(json.dumps([_art("150"), _art("201")]), encoding="utf-8")
    (env.exp / "forward_2026-10-01_report.json").write_text(json.dumps({"gagal": []}), encoding="utf-8")
    assert sorted(a["article_id"] for a in scheduled.pending_articles()) == ["150", "201", "90"], "100 sudah digabung"


def test_reviewed_labels_match_what_the_demo_knows_how_to_display() -> None:
    from presentation import STATUS_ALIASES, STATUS_STYLES

    assert scheduled.REVIEWED_LABELS == set(STATUS_STYLES) | set(STATUS_ALIASES)


def test_reviewed_new_label_no_longer_holds_merging(env: Env) -> None:
    """BELUM TERBUKTI sudah diputuskan tampilannya (2026-10-03): artikel berlabel itu tidak menahan penggabungan."""
    env.forward_result = [_art("201"), _art("202", "BELUM TERBUKTI")]
    assert scheduled.run_once() == 0 and not env.marker.exists()
    assert env.status()["kualitas"]["label_belum_ditinjau"] == []
