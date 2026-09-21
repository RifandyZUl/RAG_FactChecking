"""Uji parsing HTML NYATA TurnBackHoax (scraping.parser) memakai fixture di tests/fixtures/.

Fixture berasal dari cache hasil scraping (data/raw_html/) dan disalin ke tests/fixtures/ agar
ikut ter-commit (data/raw_html/ di-gitignore dan bisa berubah saat scraping ulang dengan
force_refresh). HTML tiruan sebelumnya dibuang karena dibuat dari asumsi struktur yang keliru
dan tidak menangkap dua cacat pada artikel nyata: kontainer salah dan tautan hoaks bocor ke
daftar referensi.
"""

from _fakes import FIXTURE_DIR, read_fixture
from scraping.discovery import is_valid_list_html
from scraping.links import blocked_reason
from scraping.parser import is_valid_article_html, parse_article


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


def test_html_validators() -> None:
    error_html = read_fixture("error_page.html")
    assert "Terjadi kesalahan saat mengambil data" in error_html
    assert not is_valid_article_html(error_html), "halaman galat lolos sbg artikel"
    assert not is_valid_list_html(error_html), "halaman galat lolos sbg daftar"
    assert is_valid_article_html(read_fixture("36738.html"))
    assert is_valid_list_html(read_fixture("list_page.html"))
