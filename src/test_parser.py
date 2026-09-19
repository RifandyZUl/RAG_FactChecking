"""
Uji logika parsing scraper dengan HTML NYATA TurnBackHoax.

Fixture berasal dari cache hasil scraping (data/raw_html/) dan disalin ke
src/fixtures/ agar ikut ter-commit (data/raw_html/ di-gitignore dan bisa
berubah saat scraping ulang dengan force_refresh). HTML tiruan sebelumnya
dibuang karena dibuat dari asumsi struktur yang keliru dan tidak menangkap
dua cacat pada artikel nyata: kontainer salah dan tautan hoaks bocor ke
daftar referensi.
"""

import tempfile
from pathlib import Path

import requests

import scraper
from scraper import (
    blocked_reason,
    discover_article_urls,
    fetch_html,
    is_valid_article_html,
    is_valid_list_html,
    normalize_url,
    parse_article,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

# id artikel -> URL asli (id dipakai sebagai nama berkas fixture)
ARTICLE_URLS = {
    "36738": "https://turnbackhoax.id/articles/36738-salah-ada-kebijakan-razia-kendaraan-dari-rumah-ke-rumah",
    "36737": "https://turnbackhoax.id/articles/36737-penipuan-tautan-pendaftaran-program-bantuan-lansia",
    "36731": "https://turnbackhoax.id/articles/36731-penipuan-tautan-pendaftaran-cek-kesehatan-gratis",
    "36730": "https://turnbackhoax.id/articles/36730-salah-ojol-dilarang-beli-pertalite",
    "36729": "https://turnbackhoax.id/articles/36729-salah-malaysia-laporkan-indonesia-ke-pbb-soal-karhutla",
}


def load(article_id: str) -> dict:
    """Parse fixture HTML nyata lewat jalur kode yang sama dengan scraper."""
    html = (FIXTURE_DIR / f"{article_id}.html").read_text(encoding="utf-8")
    art = parse_article(html, ARTICLE_URLS[article_id])
    assert art is not None, f"{article_id}: parse_article mengembalikan None"
    return art


def test_normalize_and_domain() -> None:
    assert normalize_url("  https://a.com/x?p=1#frag  ") == "https://a.com/x?p=1"
    assert normalize_url("https://a.com/x") == "https://a.com/x"

    # Arsip dan hosting gambar: selalu disaring, apa pun path-nya
    for u in [
        "https://archive.li/n2Rxw", "https://archive.ph/6Yd1j",
        "https://web.archive.org/web/2020/x", "http://archive.today/TwOTs",
        "https://archive.is/abc", "https://archive.vn/abc", "https://archive.md/HzI4C",
        "https://webarchive.io/archive/chaa/x", "https://ghostarchive.org/archive/F59Ye",
        "https://ibb.co.com/cKj7vmkf", "https://ibb.co/cKj7vmkf",
    ]:
        assert blocked_reason(u), f"seharusnya disaring: {u}"

    # Media sosial: disaring, baik postingan maupun beranda akun
    for u in [
        "https://vt.tiktok.com/ZSq9c6ky7/",
        "https://www.tiktok.com/@sindonews/video/7516875885891374343",
        "https://x.com/a/status/1", "https://twitter.com/a/status/1",
        "https://www.instagram.com/p/DdApnwrzvas/",
        "https://www.instagram.com/reel/DCQov8YyCgw/",
        "https://www.instagram.com/kemensosri/p/DXjyJ9gkZf_/",
        "https://web.facebook.com/photo/?fbid=1&set=a.2",
        "https://www.facebook.com/photo.php?fbid=1&set=pb.1",
        "https://www.facebook.com/share/1EDkBDGFdE",
        "https://web.facebook.com/khanza.khulfi/posts/pfbid02cKx",
        "https://www.youtube.com/watch?v=T7UMijc_ddI",
        "https://www.youtube.com/shorts/a3B204GdwtI", "https://youtu.be/abc",
        "https://www.threads.com/@bacotwakanda.id/post/DcgGDHyEkiA",
        # beranda akun: sengaja ikut disaring (penilaian akun resmi vs
        # penyebar hoaks ditunda ke Versi 2, lihat CLAUDE.md)
        "https://www.instagram.com/kemensetneg.ri/",
        "https://www.instagram.com/bank_brksyariah?igshid=YzAw",
        "https://x.com/brksyariahid",
        "https://web.facebook.com/bankriaukeprisyariah.id?mibextid=LQQJ4d&_rdc=1&_rdr",
        "https://www.tiktok.com/@binmas_penjaringan",
        "https://www.youtube.com/@kemenkes",
        "https://www.threads.com/@lowongankerja209",
    ]:
        assert blocked_reason(u), f"seharusnya disaring: {u}"

    # Tidak boleh salah cocok pada domain yang hanya berakhiran mirip
    assert blocked_reason("https://www.netflix.com/id") is None
    assert blocked_reason("https://www.cnnindonesia.com/a") is None
    assert blocked_reason("https://box.com/status/1") is None


def test_article_36738() -> None:
    """Kasus kebocoran: seksi Referensi asli memuat TikTok dan archive.li."""
    a = load("36738")
    assert a["label"] == "SALAH"
    assert a["narasi"] and a["penjelasan"], "seksi Narasi/Penjelasan kosong"
    assert a["kesimpulan"].startswith("Faktanya"), "isi Kesimpulan salah"

    tiktok = "https://vt.tiktok.com/ZSq9c6ky7/"
    archive = "https://archive.li/n2Rxw"

    # Wajib: tautan hoaks TIDAK boleh muncul di references (Aturan Wajib #1)
    assert tiktok not in a["references"], "TikTok bocor ke references"
    assert archive not in a["references"], "archive.li bocor ke references"
    assert not any("tiktok" in r or "archive.li" in r for r in a["references"])

    # Tetap tersimpan apa adanya di references_raw dan tercatat di filtered
    assert tiktok in a["references_raw"] and archive in a["references_raw"]
    filtered = {f["url"]: f["reasons"] for f in a["references_filtered"]}
    assert tiktok in filtered and archive in filtered
    assert any("claim_sources" in r for r in filtered[tiktok])
    assert any("tiktok.com" in r for r in filtered[tiktok])
    assert any("archive.li" in r for r in filtered[archive])
    assert len(filtered[tiktok]) == 2, "TikTok harus tercatat memenuhi kedua kriteria"

    # Rujukan sahih tetap ada, fragmen '#page2' sudah dibuang
    assert any("cnbcindonesia.com" in r for r in a["references"])
    assert any(r.startswith("https://www.kompas.com/cekfakta/") for r in a["references"])
    assert not any("#" in r for r in a["references"])

    # claim_sources tetap memuat sumber hoaks
    assert tiktok in a["claim_sources"]


def test_article_36729() -> None:
    a = load("36729")
    assert a["kesimpulan"].startswith("Faktanya, Malaysia tidak melaporkan")
    assert any("x.com" in c for c in a["claim_sources"]), "sumber klaim tidak terambil"
    assert not any("x.com" in r for r in a["references"])
    assert any("cnnindonesia.com" in r for r in a["references"])
    assert any("kompasiana.com" in r for r in a["references"])
    assert not any("goog_rewarded" in r for r in a["references_raw"]), \
        "fragmen #goog_rewarded tidak dibuang"


def test_article_36737() -> None:
    a = load("36737")
    assert not any("facebook.com" in r or "webarchive.io" in r for r in a["references"])
    assert any("kabar24.bisnis.com" in r for r in a["references"])


def test_all_fixtures_invariants() -> None:
    """Invarian yang harus berlaku pada setiap artikel nyata."""
    for article_id in ARTICLE_URLS:
        a = load(article_id)
        for key in ("narasi", "penjelasan", "kesimpulan"):
            assert a[key], f"{article_id}: seksi {key} kosong"

        claim = set(a["claim_sources"])
        for r in a["references"]:
            assert r not in claim, f"{article_id}: {r} ada di claim_sources"
            assert blocked_reason(r) is None, f"{article_id}: {r} seharusnya disaring"

        # Tidak ada tautan yang hilang: raw = references + filtered
        assert set(a["references_raw"]) == \
            set(a["references"]) | {f["url"] for f in a["references_filtered"]}, \
            f"{article_id}: references_raw tidak sama dengan references + filtered"

        for url in a["references_raw"] + a["claim_sources"]:
            assert "#" not in url and url == url.strip(), f"{article_id}: URL belum dinormalkan"


class FakeResponse:
    def __init__(self, text: str, status: int = 200) -> None:
        self.text = text
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")


class FakeSession:
    """Session palsu: mengembalikan/melempar item berurutan dari `script`."""

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.calls = 0

    def get(self, url: str, timeout: float) -> FakeResponse:
        assert timeout == scraper.TIMEOUT, "timeout eksplisit 45 dtk wajib dipakai"
        self.calls += 1
        item = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(item, Exception):
            raise item
        return item


def fake_list_page(first_id: int) -> str:
    """Halaman daftar sintetis dengan 10 tautan artikel (untuk uji paginasi)."""
    links = "".join(
        f'<a href="https://turnbackhoax.id/articles/{first_id + i}-slug-{i}">x</a>'
        for i in range(10)
    )
    return f"<html><body>{links}</body></html>"


def read_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_html_validators() -> None:
    error_html = read_fixture("error_page.html")
    assert "Terjadi kesalahan saat mengambil data" in error_html
    assert not is_valid_article_html(error_html), "halaman galat lolos sbg artikel"
    assert not is_valid_list_html(error_html), "halaman galat lolos sbg daftar"
    assert is_valid_article_html(read_fixture("36738.html"))
    assert is_valid_list_html(read_fixture("list_page.html"))


def test_fetch_retries_error_page_and_skips_cache() -> None:
    """Halaman galat 200 di-retry, dan tidak pernah ditulis ke cache."""
    error_html = read_fixture("error_page.html")
    good_html = read_fixture("36738.html")
    scraper.time.sleep = lambda s: None  # jangan benar-benar menunggu backoff

    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "1.html"

        # galat dua kali lalu sukses -> 3 panggilan, cache berisi HTML sah
        sess = FakeSession([FakeResponse(error_html), FakeResponse(error_html),
                            FakeResponse(good_html)])
        html, net = fetch_html("u", sess, cache, validate=is_valid_article_html)
        assert html == good_html and net and sess.calls == 3
        assert cache.read_text(encoding="utf-8") == good_html

        # galat terus -> menyerah setelah 1 + MAX_RETRIES percobaan, cache TIDAK dibuat
        cache2 = Path(tmp) / "2.html"
        sess = FakeSession([FakeResponse(error_html)])
        html, _ = fetch_html("u", sess, cache2, validate=is_valid_article_html)
        assert html is None and sess.calls == scraper.MAX_RETRIES + 1
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


def test_fetch_retry_policy() -> None:
    """Retry hanya untuk timeout/koneksi; 404 tidak di-retry."""
    scraper.time.sleep = lambda s: None
    sess = FakeSession([requests.ReadTimeout("t"), requests.ConnectionError("c"),
                        FakeResponse("<html>ok</html>")])
    html, _ = fetch_html("u", sess)
    assert html == "<html>ok</html>" and sess.calls == 3

    sess = FakeSession([requests.ConnectionError("c")])
    html, _ = fetch_html("u", sess)
    assert html is None and sess.calls == scraper.MAX_RETRIES + 1

    sess = FakeSession([FakeResponse("nope", status=404)])
    html, _ = fetch_html("u", sess)
    assert html is None and sess.calls == 1, "404 tidak boleh di-retry"


def test_discover_not_fooled_by_error_page() -> None:
    """Halaman daftar galat di tengah paginasi di-retry, bukan dianggap akhir."""
    scraper.time.sleep = lambda s: None
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
    # eksplisit (fetch_html sudah mencoba 1 + MAX_RETRIES kali)
    sess = FakeSession([FakeResponse(error_html)])
    assert discover_article_urls(sess, max_articles=20) == []
    assert sess.calls == scraper.MAX_RETRIES + 1

    # Halaman daftar asli menghasilkan 10 URL
    sess = FakeSession([FakeResponse(read_fixture("list_page.html"))])
    assert len(discover_article_urls(sess, max_articles=10)) == 10


def test_aggregate_by_article() -> None:
    """Agregasi per artikel: skor tertinggi per artikel, tanpa duplikat artikel."""
    from chunker import encode_references
    from retriever import aggregate_by_article

    def meta(aid: str, section: str, refs: list[str]) -> dict:
        return {"article_id": aid, "title": f"T{aid}", "url": f"u{aid}", "label": "SALAH",
                "section": section, "references": encode_references(refs)}

    # jarak kosinus -> skor = 1 - jarak
    metas = [
        meta("A", "penjelasan", ["r1"]), meta("B", "narasi", []),
        meta("A", "narasi", ["r1"]), meta("A", "kesimpulan", ["r1"]),
        meta("B", "kesimpulan", []),
    ]
    dists = [0.30, 0.35, 0.50, 0.60, 0.20]
    hits = aggregate_by_article(metas, dists)
    assert [h.article_id for h in hits] == ["B", "A"], "urutan harus menurut skor tertinggi"
    b, a = hits
    assert abs(b.score - 0.80) < 1e-9 and b.best_section == "kesimpulan"
    assert abs(a.score - 0.70) < 1e-9 and a.best_section == "penjelasan"
    assert set(a.section_scores) == {"penjelasan", "narasi", "kesimpulan"}
    assert a.references == ["r1"], "references harus didekode dari metadata"
    assert len({h.article_id for h in hits}) == len(hits)


def run() -> None:
    tests = [
        test_aggregate_by_article,
        test_normalize_and_domain,
        test_html_validators,
        test_fetch_retries_error_page_and_skips_cache,
        test_fetch_retry_policy,
        test_discover_not_fooled_by_error_page,
        test_article_36738,
        test_article_36729,
        test_article_36737,
        test_all_fixtures_invariants,
    ]
    for t in tests:
        t()
        print(f"OK  {t.__name__}")
    print("\nSemua pemeriksaan lolos.")


if __name__ == "__main__":
    run()
