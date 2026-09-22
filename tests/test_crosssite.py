"""
Uji ekstraksi kutipan candidates/crosssite.py memakai HTML NYATA Liputan6 (tests/fixtures/) dan
uji unit split_quote_spans dengan string buatan yang meniru pola tanda kutip bermasalah.

Fixture liputan6_8292010.html dan liputan6_8293157.html berasal dari cache pengumpulan kandidat
(data/candidates_cache/liputan6/) -- dua kasus nyata yang sempat gagal diekstrak (lihat CLAUDE.md/
laporan v1.meta.json 2026-09-22): 8292010 menangkap komentar bantahan warganet alih-alih pernyataan
hoaks aslinya, dan 8293157 gagal total (hanya menangkap kalimat pembuka kutipan).
"""

from bs4 import BeautifulSoup

from _fakes import read_fixture
from candidates.crosssite import extract_claim, split_quote_spans


def test_split_quote_spans_skips_degenerate_pair_from_duplicated_quote_mark() -> None:
    """
    Tanda kutip ganda pada unggahan asli (mis. salah ketik) tidak boleh membuat SELURUH
    pasangan berikutnya bergeser. Pola ini persis kasus 8292010: '"Prabowo sebut "kalau
    bisa...buat negara" Akun itu menambahkan narasi: "Gak bisa pak...terjadi"'.
    """
    text = (
        '"Prabowo sebut "kalau bisa seluruh warung tutup saja biar mereka belanja di kopdes" '
        'Akun itu menambahkan narasi: "Gak bisa pak, warung rakyat tidak boleh tutup begitu saja"'
    )
    spans = split_quote_spans(text)
    assert spans[0] == "kalau bisa seluruh warung tutup saja biar mereka belanja di kopdes"
    assert "Akun itu menambahkan narasi" not in spans[0]


def test_split_quote_spans_pairs_multi_paragraph_quote() -> None:
    """Kutipan yang direntangkan lewat spasi pengganti newline antarparagraf tetap satu span."""
    text = 'Berikut isi transkrip video klaim: "Presenter: halo semua. Ustaz: saya klarifikasi." lanjut cerita'
    spans = split_quote_spans(text)
    assert spans == ["Presenter: halo semua. Ustaz: saya klarifikasi."]


def _extract_from_fixture(name: str) -> str | None:
    soup = BeautifulSoup(read_fixture(name), "html.parser")
    return extract_claim(soup)


def test_extract_claim_8292010_ambil_pernyataan_hoaks_bukan_bantahan() -> None:
    """
    Regresi: sebelum diperbaiki, fungsi ini mengembalikan komentar bantahan warganet
    ("Gak bisa pak...") karena tanda kutip ganda di awal kalimat menggeser semua pasangan.
    """
    claim = _extract_from_fixture("liputan6_8292010.html")
    assert claim is not None
    assert claim.startswith("kalau bisa seluruh warung")
    assert "buat negara" in claim
    assert "Gak bisa pak" not in claim
    assert "menambahkan narasi" not in claim


def test_extract_claim_8293157_ambil_transkrip_bukan_kalimat_pembuka() -> None:
    """
    Regresi: sebelum diperbaiki, fungsi ini mengembalikan 'Unggahan menyertakan keterangan
    sebagai berikut:' -- teks wartawan di antara dua kutipan, bukan kutipan itu sendiri.
    """
    claim = _extract_from_fixture("liputan6_8293157.html")
    assert claim is not None
    assert claim != "Unggahan menyertakan keterangan sebagai berikut:"
    assert claim.startswith("Presenter:")
    assert "Abdul Somad" in claim
