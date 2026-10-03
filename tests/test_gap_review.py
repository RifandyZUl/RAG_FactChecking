"""Uji penyiapan berkas konfirmasi celah "belum ditemukan" (candidates.gap_review): fungsi murni, tanpa model."""

from candidates.gap_review import (
    COLUMNS,
    banner_label,
    build_rows,
    clean_title,
    draw_sample,
    in_range_tail,
    is_non_hoax_verdict,
    lexical_top,
)


def test_clean_title_strips_prefix_and_leading_verdict() -> None:
    assert clean_title("Cek Fakta: Tidak Benar Link Pendaftaran Contoh 2026") == ("Link Pendaftaran Contoh 2026", "tidak benar")
    assert clean_title("Cek Fakta: Hoaks, Video Contoh") == ("Video Contoh", "hoaks")
    assert clean_title("Cek Fakta: Klarifikasi Lembaga soal Contoh") == ("Lembaga soal Contoh", "klarifikasi")
    assert clean_title("Cek Fakta: Video Contoh Ini Terjadi pada 2015") == ("Video Contoh Ini Terjadi pada 2015", "")


def test_banner_label_reads_the_three_liputan6_banners() -> None:
    assert banner_label("Kesimpulan ... Perbesar Banner Cek Fakta: Salah (Sumber)") == "salah"
    assert banner_label("Kesimpulan Perbesar banner Hoax (Sumber) Postingan ...") == "hoax"
    assert banner_label("Kesimpulan Perbesar Banner Cek Fakta - Klarifikasi. (Sumber)") == "klarifikasi"
    assert banner_label("Kesimpulan ... merupakan video lama pada 2015.") == ""


def test_only_clear_non_hoax_verdicts_are_excluded() -> None:
    assert is_non_hoax_verdict("Cek Fakta: Klarifikasi Lembaga soal Contoh", "Kesimpulan Postingan telah diklarifikasi.")
    assert is_non_hoax_verdict("Cek Fakta: Contoh", "Kesimpulan Postingan telah diklarifikasi. Perbesar Banner cek Fakta: klarifikasi (Sumber)")
    assert not is_non_hoax_verdict("Cek Fakta: Tidak Benar Contoh", "Kesimpulan klaim tidak benar. Perbesar banner Hoax (Sumber)")
    # penanda bertentangan (banner klarifikasi, judul dan Kesimpulan "tidak benar"): diputuskan manusia, bukan otomatis
    assert not is_non_hoax_verdict("Cek Fakta: Tidak Benar Contoh",
                                   "Kesimpulan Perbesar Banner Cek Fakta - Klarifikasi. (Sumber) Postingan contoh adalah tidak benar.")
    # tanpa kata vonis dan tanpa banner: tidak dikeluarkan otomatis
    assert not is_non_hoax_verdict("Cek Fakta: Video Contoh Ini Terjadi pada 2015", "Kesimpulan merupakan video lama pada 2015.")
    # banner "Cek Fakta: Salah" tidak boleh membuat kata "salah" di banner dihitung sebagai pernyataan Kesimpulan
    assert is_non_hoax_verdict("Cek Fakta: Contoh", "Kesimpulan Sudah dijelaskan lembaganya. Perbesar Banner Cek Fakta: Klarifikasi (Sumber)")


def test_draw_sample_is_seeded_and_order_independent() -> None:
    ids = [str(i) for i in range(99)]
    a = draw_sample(ids)
    assert a == draw_sample(list(reversed(ids))) and len(a) == 50 and len(set(a)) == 50
    assert draw_sample(ids, seed=1) != a
    assert sorted(draw_sample(["1", "2"], n=50)) == ["1", "2"]


def test_lexical_top_matches_on_title_keywords() -> None:
    titles = {"1": "Tautan Pendaftaran Bantuan Alat Pertanian 2026", "2": "Kebijakan Razia Kendaraan dari Rumah ke Rumah",
              "3": "Bantuan Bibit Sawit Gratis"}
    top = lexical_top("Link Pendaftaran Bantuan Alat Pertanian 2026", titles, k=2)
    assert top[0][0] == "1" and top[0][1] == 1.0, "kata umum (link/tautan/pendaftaran/bantuan) tidak dihitung"
    assert len(top) == 2


def test_range_tail_flags_last_two_weeks_only() -> None:
    assert in_range_tail("2026-09-27") and in_range_tail("2026-09-14")
    assert not in_range_tail("2026-09-13") and not in_range_tail("2025-10-02")


def test_rows_hide_scores_and_order_candidates_by_date() -> None:
    cand = [{"id": "10", "tanggal": "05/01/2026", "label": "SALAH", "asal": "indeks", "judul": "A", "kesimpulan": "KA"},
            {"id": "30", "tanggal": "01/10/2026", "label": "PENIPUAN", "asal": "antrean (belum di-ingest)", "judul": "C", "kesimpulan": "KC"},
            {"id": "20", "tanggal": "20/03/2026", "label": "SALAH", "asal": "indeks", "judul": "B", "kesimpulan": "KB"}]
    rows = build_rows([{"id": "x", "judul": "Cek Fakta: Tidak Benar Contoh", "tanggal": "2026-09-20", "pesan": "pesan",
                        "ujung_rentang": True, "kandidat": cand}])
    assert [r["TBH_id"] for r in rows] == ["30", "20", "10"], "terbaru dulu, bukan menurut skor"
    assert list(rows[0]) == COLUMNS and COLUMNS[-1] == "TBH_kesimpulan", "Kesimpulan di kolom paling kanan"
    assert not any("skor" in c.lower() or "mirip" in c.lower() for c in COLUMNS)
    assert rows[0]["L6_judul"] and rows[0]["ujung_rentang"] == "YA" and rows[0]["KEPUTUSAN"] == ""
    assert rows[1]["L6_judul"] == "" and rows[1]["L6_kutipan_pesan"] == "", "data butir hanya di baris pertama"
    assert all(r["KEPUTUSAN"] == "" and r["catatan"] == "" for r in rows), "keputusan tidak pernah diisi kode"
