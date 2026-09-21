"""Uji klien HTTP (scraping.client): retry, validasi halaman galat, dan cache.
"""

import tempfile
from pathlib import Path

import requests

import scraping.client as scraping_client
from _fakes import FakeResponse, FakeSession, read_fixture
from scraping.client import fetch_html
from scraping.parser import is_valid_article_html


def test_fetch_retries_error_page_and_skips_cache(monkeypatch) -> None:
    """Halaman galat 200 di-retry, dan tidak pernah ditulis ke cache."""
    error_html = read_fixture("error_page.html")
    good_html = read_fixture("36738.html")
    monkeypatch.setattr(scraping_client.time, "sleep", lambda s: None)  # jangan benar-benar menunggu backoff

    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "1.html"

        # galat dua kali lalu sukses -> 3 panggilan, cache berisi HTML sah
        sess = FakeSession([FakeResponse(error_html), FakeResponse(error_html),
                            FakeResponse(good_html)])
        html, net = fetch_html("u", sess, cache, validate=is_valid_article_html)
        assert html == good_html and net and sess.calls == 3
        assert cache.read_text(encoding="utf-8") == good_html

        # galat terus -> menyerah setelah 1 + 3 retry = 4 percobaan, cache TIDAK dibuat
        cache2 = Path(tmp) / "2.html"
        sess = FakeSession([FakeResponse(error_html)])
        html, _ = fetch_html("u", sess, cache2, validate=is_valid_article_html)
        assert html is None and sess.calls == 4
        assert not cache2.exists(), "halaman galat ter-cache"

        # cache lama yang rusak diabaikan dan diambil ulang
        cache3 = Path(tmp) / "3.html"
        cache3.write_text(error_html, encoding="utf-8")
        sess = FakeSession([FakeResponse(good_html)])
        html, net = fetch_html("u", sess, cache3, validate=is_valid_article_html)
        assert html == good_html and net and sess.calls == 1
        assert cache3.read_text(encoding="utf-8") == good_html

        # cache sah dipakai tanpa jaringan
        sess = FakeSession([FakeResponse(error_html)])
        html, net = fetch_html("u", sess, cache3, validate=is_valid_article_html)
        assert html == good_html and not net and sess.calls == 0


def test_fetch_retry_policy(monkeypatch) -> None:
    """Retry hanya untuk timeout/koneksi; 404 tidak di-retry."""
    monkeypatch.setattr(scraping_client.time, "sleep", lambda s: None)
    sess = FakeSession([requests.ReadTimeout("t"), requests.ConnectionError("c"),
                        FakeResponse("<html>ok</html>")])
    html, _ = fetch_html("u", sess)
    assert html == "<html>ok</html>" and sess.calls == 3

    sess = FakeSession([requests.ConnectionError("c")])
    html, _ = fetch_html("u", sess)
    assert html is None and sess.calls == 4, "1 percobaan awal + 3 retry"

    sess = FakeSession([FakeResponse("nope", status=404)])
    html, _ = fetch_html("u", sess)
    assert html is None and sess.calls == 1, "404 tidak boleh di-retry"
