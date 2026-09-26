"""
Uji claim_candidate() (candidates/screen.py) memakai HTML nyata arsip TurnBackHoax
Fixture sudah DISAMARKAN (tests/anonymize_fixtures.py): struktur HTML asli dipertahankan, tetapi
teks isi diganti kata semu sepanjang kata asli dan tautan sumber hoaks diganti jalur fiktif pada
domain yang sama. Literal teks pada asersi di bawah adalah padanan TERSAMAR (posisi karakternya
sama dengan teks asli), sehingga setiap pemeriksaan menguji hal yang sama seperti sebelumnya.
(tests/fixtures/), lewat jalur parsing yang sama dengan pengumpul (scraping.parser.parse_article).

Fixture archive_32490.html, archive_35310.html, archive_35850.html adalah tiga kandidat yang
klaim_kandidat-nya sempat salah (menangkap kalimat pembuka "Akun X ... mengunggah narasi ..."
alih-alih pesan yang beredar) karena Narasi artikel ini TIDAK memakai tanda kutip di sekitar
pesannya (lihat CLAUDE.md/laporan v1.meta.json 2026-09-22).
"""

from _fakes import read_fixture
from candidates.screen import claim_candidate
from scraping.parser import parse_article

ARTICLE_URLS = {
    "32490": "https://turnbackhoax.id/articles/32490-penipuan-bantuan-dana-untuk-masyarakat-non-muslim-2026",
    "35310": "https://turnbackhoax.id/articles/35310-parodi-jubir-esdm-minta-masyarakat-pakai-solar-saat-harga-pertamax-naik",
    "35850": "https://turnbackhoax.id/articles/35850-penipuan-tautan-pendaftaran-lowongan-kerja-j-t-cargo",
}


def _narasi(article_id: str) -> str:
    html = read_fixture(f"archive_{article_id}.html")
    art = parse_article(html, ARTICLE_URLS[article_id])
    assert art is not None, f"{article_id}: parse_article mengembalikan None"
    return art["narasi"]


def test_claim_candidate_32490_ambil_pesan_bantuan_bukan_kalimat_pembuka() -> None:
    claim = claim_candidate(_narasi("32490"))
    assert claim.startswith("Hirawac Nala tahop gecotohefa dow naheri")
    assert "lolitonabi" not in claim  # kata "mengunggah" pada kalimat pembuka


def test_claim_candidate_35310_ambil_kutipan_jubir_bukan_kalimat_pembuka() -> None:
    claim = claim_candidate(_narasi("35310"))
    assert claim.startswith("Jutewojo Legu Mu 16.250 gag Monut")
    assert "Tajowol hajapero pipute" not in claim  # kalimat pembuka


def test_claim_candidate_35850_ambil_isi_lowongan_bukan_kalimat_pembuka() -> None:
    claim = claim_candidate(_narasi("35850"))
    assert claim.startswith("FAJIWORA HADIN B&W KUREP")
    assert "copajesepe bawin" not in claim  # kalimat pembuka


def test_claim_candidate_preserves_quoted_narasi_without_narasi_cue_word_inside() -> None:
    """Regresi: kutipan panjang yang memuat kata 'narasi' di tengahnya sendiri tidak boleh terpotong."""
    narasi = (
        'Beredar unggahan foto [arsip] pada Jumat dari akun Facebook "X" berisi narasi:\n'
        '"Sebuah pernyataan viral. Dalam narasi yang beredar luas, tokoh itu disebut berkata tegas."\n'
        "Pernyataan itu memicu reaksi."
    )
    claim = claim_candidate(narasi)
    assert claim == "Sebuah pernyataan viral. Dalam narasi yang beredar luas, tokoh itu disebut berkata tegas."
