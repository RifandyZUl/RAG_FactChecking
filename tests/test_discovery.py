"""Uji pengumpulan URL artikel (scraping.discovery).
"""

import scraping.client as scraping_client
from _fakes import FakeResponse, FakeSession, fake_list_page, read_fixture
from scraping.discovery import discover_article_urls


def test_discover_not_fooled_by_error_page(monkeypatch) -> None:
    """Halaman daftar galat di tengah paginasi di-retry, bukan dianggap akhir."""
    monkeypatch.setattr(scraping_client.time, "sleep", lambda s: None)
    error_html = read_fixture("error_page.html")
    sess = FakeSession([
        FakeResponse(fake_list_page(1000)),   # halaman 1
        FakeResponse(error_html),             # halaman 2: galat, percobaan 1
        FakeResponse(error_html),             # percobaan 2
        FakeResponse(fake_list_page(2000)),   # halaman 2 akhirnya sah
    ])
    urls = discover_article_urls(sess, max_articles=20)
    assert len(urls) == 20, f"paginasi berhenti terlalu dini: {len(urls)} URL"
    assert sess.calls == 4

    # Galat sejak halaman 1 dan tak kunjung sah -> hasil kosong dengan pesan
    # eksplisit (fetch_html sudah mencoba 1 + 3 retry = 4 kali)
    sess = FakeSession([FakeResponse(error_html)])
    assert discover_article_urls(sess, max_articles=20) == []
    assert sess.calls == 4

    # Halaman daftar asli menghasilkan 10 URL
    sess = FakeSession([FakeResponse(read_fixture("list_page.html"))])
    assert len(discover_article_urls(sess, max_articles=10)) == 10


def test_find_article_urls_does_not_crash_on_odd_hrefs() -> None:
    """Titik pengurai URL lain (urljoin): href aneh di halaman daftar tidak boleh melempar galat."""
    from bs4 import BeautifulSoup

    from scraping.discovery import find_article_urls

    html = ('<a href="/articles/1-judul]aneh[x#f">a</a><a href="http://contoh.go.id]">b</a>'
            '<a href="https://turnbackhoax.id/articles/2-judul">c</a><a href="//[rusak/articles/3-x">d</a>')
    assert find_article_urls(BeautifulSoup(html, "html.parser")) == [
        "https://turnbackhoax.id/articles/1-judul]aneh[x#f", "https://turnbackhoax.id/articles/2-judul"]
