"""Uji fungsi murni penyaring kandidat (candidates.screen): penanda data pribadi, usulan klaim, dan kelas usulan."""

from candidates.screen import claim_candidate, pii_flags, propose_class


def test_pii_flags_detects_phone_email_handle_url_and_account_name() -> None:
    assert pii_flags("hubungi 0812-3456-7890 sekarang") == ["nomor_telepon"]
    assert "nomor_telepon" in pii_flags("WA +62 812 3456 7890")
    assert "email" in pii_flags("kirim ke budi.s@mail.co.id")
    assert "handle_akun" in pii_flags("ikuti @akun_palsu")
    assert "url_di_teks" in pii_flags("klik https://contoh.example/x")
    assert "nama_akun" in pii_flags("Akun Facebook “Budi Santoso” mengunggah")
    assert pii_flags("Beredar pesan bahwa harga cabai naik di pasar") == []
    assert pii_flags("tahun 2015 sebanyak 1.234.567 orang") == []


def test_pii_flags_catches_forms_that_used_to_slip_through() -> None:
    """Celah yang ditemukan pada pemeriksaan 2026-09-26: en-dash, wa.me, dan URL tanpa skema."""
    assert "nomor_telepon" in pii_flags("Hotline 0800–0000–0000")  # pemisah en-dash
    assert "nomor_telepon" in pii_flags("chat wa.me/628000000000")
    assert "url_di_teks" in pii_flags("daftar di bantuan-contoh.web.id/form")
    assert "url_di_teks" in pii_flags("klik bit.ly/contoh-fiktif")
    assert pii_flags("harga naik 2,5 persen, kata pejabat.") == []
    assert pii_flags("Bupati A.B. Contoh menegaskan hal itu") == []


def test_claim_candidate_prefers_first_long_quote_else_first_sentence() -> None:
    n = ("Akun X “abc” mengunggah narasi: “Pemerintah akan menghapus subsidi listrik mulai bulan depan "
         "untuk semua rumah tangga”. Hingga kini 1.000 suka.")
    assert claim_candidate(n) == "Pemerintah akan menghapus subsidi listrik mulai bulan depan untuk semua rumah tangga"
    assert claim_candidate("Beredar foto banjir besar. Foto itu diklaim baru.") == "Beredar foto banjir besar."


def test_propose_class_thresholds() -> None:
    assert propose_class(0.9, 0.3) == "kemungkinan_sama"
    assert propose_class(0.2, 0.85) == "kemungkinan_sama"
    assert propose_class(0.2, 0.65) == "tetangga"
    assert propose_class(0.2, 0.40) == "jauh"
