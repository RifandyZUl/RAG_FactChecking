"""
Uji offline candidates/gemma_generate.py -- TIDAK ADA panggilan API (memakai ScriptedProvider
palsu dari tests/_fakes.py). Menguji fungsi murni (pemeriksa salin Narasi, kemiripan judul,
audit kebocoran, penguraian JSON) dan alur generate_for_job() dengan provider palsu.
"""

import pytest

from _fakes import ScriptedProvider
from candidates.gemma_generate import (
    RAW_WITHHELD,
    assert_no_pii,
    assert_pii_checked,
    assert_reviewed_before_testset,
    build_prompt_negatif_angka_waktu,
    build_prompt_negatif_entitas_sama,
    build_prompt_negatif_mudah,
    build_prompt_positif,
    copies_ngram,
    generate_for_job,
    leak_flag,
    parse_klaim_list,
    passed_checks,
    reviewable_rows,
    run_checks,
    title_similarity,
    write_review_csv,
)

DB_TITLES = {"36001": "Ojol Dilarang Beli Pertalite", "36002": "Vaksin HPV Bikin Impoten"}
GUIDE_TEXT = "Uji dua arah: bila klaim pengguna benar, klaim inti artikel pasti benar."


def test_copies_ngram_detects_four_word_overlap() -> None:
    narasi = "Akun Facebook mengunggah klaim bantuan sosial seratus ribu rupiah untuk warga miskin"
    candidate_copied = "katanya ada klaim bantuan sosial seratus ribu rupiah buat siapa aja"
    candidate_paraphrased = "katanya ada duit bansos gratis buat rakyat kurang mampu"
    assert copies_ngram(candidate_copied, narasi, 4) is True
    assert copies_ngram(candidate_paraphrased, narasi, 4) is False


def test_copies_ngram_short_text_never_flagged() -> None:
    assert copies_ngram("halo", "halo dunia yang indah sekali hari ini", 4) is False


def test_title_similarity_finds_closest_title() -> None:
    aid, sim = title_similarity("ojek online dilarang beli pertalite katanya", DB_TITLES)
    assert aid == "36001"
    assert sim > 0.3


def test_leak_flag_true_on_guide_overlap() -> None:
    candidate = "Ini contoh klaim yang menyalin uji dua arah bila klaim pengguna benar klaim inti artikel pasti benar begitu saja"
    assert leak_flag(candidate, GUIDE_TEXT) is True


def test_leak_flag_false_on_clean_text() -> None:
    assert leak_flag("klaim yang sama sekali tidak berkaitan dengan pedoman", GUIDE_TEXT) is False


def test_parse_klaim_list_plain_json() -> None:
    assert parse_klaim_list('{"klaim": ["a", "b", "c"]}') == ["a", "b", "c"]


def test_parse_klaim_list_fenced_json() -> None:
    raw = '```json\n{"klaim": ["satu", "dua"]}\n```'
    assert parse_klaim_list(raw) == ["satu", "dua"]


def test_parse_klaim_list_invalid_returns_none() -> None:
    assert parse_klaim_list("bukan json sama sekali") is None
    assert parse_klaim_list('{"lain": ["a"]}') is None
    assert parse_klaim_list('{"klaim": ["a", 1]}') is None
    assert parse_klaim_list('{"klaim": []}') is None


def test_run_checks_positif_flags_copied_narasi() -> None:
    narasi = "Akun Facebook mengunggah klaim bantuan sosial seratus ribu rupiah untuk warga miskin"
    copied = "katanya ada klaim bantuan sosial seratus ribu rupiah buat siapa aja"
    checks = run_checks("positif", copied, narasi, DB_TITLES, GUIDE_TEXT)
    assert checks["copies_narasi_ngram"] is True
    assert passed_checks("positif", checks) is False


def test_run_checks_positif_passes_clean_paraphrase() -> None:
    narasi = "Akun Facebook mengunggah klaim bantuan sosial seratus ribu rupiah untuk warga miskin"
    paraphrase = "katanya ada duit bansos gratis buat rakyat kurang mampu"
    checks = run_checks("positif", paraphrase, narasi, DB_TITLES, GUIDE_TEXT)
    assert checks["copies_narasi_ngram"] is False
    assert passed_checks("positif", checks) is True


def test_run_checks_flags_phone_number_pii() -> None:
    """
    Kejadian nyata 2026-09-23: kandidat positif berisi nomor WA berpola nomor Indonesia lolos
    tak tertandai ke tinjauan tahap 3 karena gemma_generate.py tidak pernah menjalankan
    pii_flags() (sudah ada di candidates/screen.py). Diperbaiki: run_checks kini memanggilnya
    untuk SEMUA slot (bukan hanya negatif).
    """
    text = "Ada bantuan dana hibah 500 juta, daftar lewat WA 0800-0000-0000"
    checks = run_checks("positif", text, "Narasi apa saja", DB_TITLES, GUIDE_TEXT)
    assert "nomor_telepon" in checks["pii_flags"]
    assert passed_checks("positif", checks) is False


def test_run_checks_negatif_flags_high_title_similarity() -> None:
    checks = run_checks("negatif_mudah", "Ojol Dilarang Beli Pertalite", None, DB_TITLES, GUIDE_TEXT)
    assert checks["title_sim_flag"] is True
    assert passed_checks("negatif_mudah", checks) is False


def test_run_checks_negatif_excludes_own_target_article_from_title_similarity() -> None:
    """
    Kandidat angka_waktu_beda/entitas_sama SEHARUSNYA mirip judul artikel targetnya sendiri
    (itu maksud subtipenya); tanpa target_article, ini salah ditandai gagal (bug nyata
    2026-09-22, lihat run_checks docstring).
    """
    checks_without_exclusion = run_checks(
        "negatif_angka_waktu", "Ojol Dilarang Beli Pertalite", None, DB_TITLES, GUIDE_TEXT,
    )
    assert checks_without_exclusion["title_sim_flag"] is True  # cocok dgn 36001, tanpa pengecualian

    checks_with_exclusion = run_checks(
        "negatif_angka_waktu", "Ojol Dilarang Beli Pertalite", None, DB_TITLES, GUIDE_TEXT,
        target_article="36001",
    )
    assert checks_with_exclusion["title_sim_id"] != "36001"
    assert checks_with_exclusion["title_sim_flag"] is False  # 36002 (HPV) jauh lebih rendah


def test_run_checks_negatif_passes_dissimilar_claim() -> None:
    checks = run_checks("negatif_angka_waktu", "kucing tetangga hilang sejak kemarin sore",
                         None, DB_TITLES, GUIDE_TEXT)
    assert checks["title_sim_flag"] is False
    assert passed_checks("negatif_angka_waktu", checks) is True


def test_run_checks_any_slot_fails_on_leak() -> None:
    leaked = "uji dua arah bila klaim pengguna benar klaim inti artikel pasti benar begitu saja"
    checks = run_checks("negatif_mudah", leaked, None, DB_TITLES, GUIDE_TEXT)
    assert checks["leak_flag"] is True
    assert passed_checks("negatif_mudah", checks) is False


def test_build_prompts_mention_constraints() -> None:
    system, user = build_prompt_positif("Narasi contoh")
    assert "empat kata" in system
    assert "Narasi contoh" in user

    system2, _ = build_prompt_negatif_angka_waktu("KIA contoh", "Narasi contoh")
    assert "angka" in system2 and "waktu" in system2

    system3, _ = build_prompt_negatif_mudah(["Politik", "Kesehatan"])
    assert "Politik" in system3 and "Kesehatan" in system3

    system4, user4 = build_prompt_negatif_entitas_sama("KIA contoh", "Narasi contoh")
    assert "entitas" in system4 and "KIA contoh" in user4


ARTICLES = {
    "36001": {"article_id": "36001", "title": "Ojol Dilarang Beli Pertalite", "category": "Politik",
              "narasi": "Akun Facebook mengunggah klaim ojek online dilarang membeli Pertalite bersubsidi mulai bulan depan"},
}


def test_generate_for_job_positif_no_real_api_call() -> None:
    provider = ScriptedProvider(['{"klaim": ["katanya ojol gaboleh beli pertalite lagi", '
                                  '"ojol dilarang isi pertalite katanya", "bener ga sih ojol gaboleh pertalite"]}'])
    provider.model = "gemma-4-test"
    rows = generate_for_job(provider, "positif", "36001", ARTICLES, DB_TITLES, GUIDE_TEXT)
    assert len(rows) == 3
    assert all(r["sumber"] == "buatan_model" for r in rows)
    assert all(r["model"] == "gemma-4-test" for r in rows)
    assert all(r["status"] == "kandidat, belum ditinjau" for r in rows)
    assert provider.prompts == [provider.prompts[0]]  # satu panggilan saja dikirim


def test_generate_for_job_handles_format_failure() -> None:
    provider = ScriptedProvider(["ini bukan json"])
    provider.model = "gemma-4-test"
    rows = generate_for_job(provider, "negatif_mudah", None, ARTICLES, DB_TITLES, GUIDE_TEXT)
    assert len(rows) == 1
    assert rows[0]["lolos_pemeriksaan_otomatis"] is False
    assert rows[0]["status"] == "gagal format, dibuang"


def test_generate_for_job_marks_leaked_candidate_as_failed() -> None:
    leaked_claim = "uji dua arah bila klaim pengguna benar klaim inti artikel pasti benar begitu saja"
    provider = ScriptedProvider([f'{{"klaim": ["{leaked_claim}"]}}'])
    provider.model = "gemma-4-test"
    rows = generate_for_job(provider, "negatif_mudah", None, ARTICLES, DB_TITLES, GUIDE_TEXT)
    assert rows[0]["lolos_pemeriksaan_otomatis"] is False
    assert rows[0]["pemeriksaan"]["leak_flag"] is True


def test_generate_for_job_includes_model_version_metadata() -> None:
    provider = ScriptedProvider(['{"klaim": ["klaim bersih tanpa masalah apa pun di sini"]}'])
    provider.model = "gemma-4-test"
    rows = generate_for_job(provider, "negatif_mudah", None, ARTICLES, DB_TITLES, GUIDE_TEXT)
    assert rows[0]["versi"]["model_id"] == "gemma-4-test"
    assert "tanggal" in rows[0]["versi"]
    assert rows[0]["versi"]["sumber_versi"] in ("metadata_respons_api", "sdk_terpasang")


def test_generate_for_job_negatif_entitas_sama_no_real_api_call() -> None:
    provider = ScriptedProvider(['{"klaim": ["ojol katanya sekarang dilarang naik motor listrik", '
                                  '"ojol dilarang parkir di minimarket katanya", "bener ga ojol dilarang ngetem"]}'])
    provider.model = "gemma-4-test"
    rows = generate_for_job(provider, "negatif_entitas_sama", "36001", ARTICLES, DB_TITLES, GUIDE_TEXT)
    assert len(rows) == 3
    assert all(r["sumber"] == "buatan_model" for r in rows)
    assert all("title_sim_flag" in r["pemeriksaan"] for r in rows)
    assert provider.prompts == [provider.prompts[0]]  # satu panggilan saja dikirim


def test_generate_for_job_format_failure_still_has_version_metadata() -> None:
    provider = ScriptedProvider(["ini bukan json"])
    provider.model = "gemma-4-test"
    rows = generate_for_job(provider, "negatif_mudah", None, ARTICLES, DB_TITLES, GUIDE_TEXT)
    assert rows[0]["versi"]["model_id"] == "gemma-4-test"


# -- syarat: kandidat gagal pemeriksaan otomatis tidak pernah masuk berkas tinjauan atau set uji --

FAILED_LEAK_ROW = {
    "slot": "negatif_mudah", "target_article": None,
    "klaim": "uji dua arah bila klaim pengguna benar klaim inti artikel pasti benar begitu saja",
    "model": "gemma-4-test", "lolos_pemeriksaan_otomatis": False,
    "pemeriksaan": {"leak_flag": True},
}
FAILED_COPY_ROW = {
    "slot": "positif", "target_article": "36001",
    "klaim": "katanya ada klaim bantuan sosial seratus ribu rupiah buat siapa aja",
    "model": "gemma-4-test", "lolos_pemeriksaan_otomatis": False,
    "pemeriksaan": {"leak_flag": False, "copies_narasi_ngram": True},
}
PASSED_ROW = {
    "slot": "negatif_mudah", "target_article": None,
    "klaim": "kucing tetangga hilang sejak kemarin sore",
    "model": "gemma-4-test", "lolos_pemeriksaan_otomatis": True,
    "pemeriksaan": {"leak_flag": False, "title_sim_flag": False},
}


def test_reviewable_rows_excludes_leaked_and_copied() -> None:
    result = reviewable_rows([FAILED_LEAK_ROW, FAILED_COPY_ROW, PASSED_ROW])
    assert result == [PASSED_ROW]


def test_write_review_csv_never_contains_failed_candidates(tmp_path) -> None:
    out = tmp_path / "tinjauan_gemma.csv"
    n = write_review_csv([FAILED_LEAK_ROW, FAILED_COPY_ROW, PASSED_ROW], out)
    assert n == 1
    content = out.read_text(encoding="utf-8-sig")
    assert FAILED_LEAK_ROW["klaim"] not in content
    assert FAILED_COPY_ROW["klaim"] not in content
    assert PASSED_ROW["klaim"] in content


def test_write_review_csv_empty_when_nothing_passed(tmp_path) -> None:
    out = tmp_path / "tinjauan_gemma.csv"
    n = write_review_csv([FAILED_LEAK_ROW, FAILED_COPY_ROW], out)
    assert n == 0
    content = out.read_text(encoding="utf-8-sig")
    assert FAILED_LEAK_ROW["klaim"] not in content
    assert FAILED_COPY_ROW["klaim"] not in content


def test_assert_reviewed_before_testset_rejects_failed_candidate() -> None:
    with pytest.raises(ValueError):
        assert_reviewed_before_testset(FAILED_LEAK_ROW)
    with pytest.raises(ValueError):
        assert_reviewed_before_testset(FAILED_COPY_ROW)


def test_assert_reviewed_before_testset_allows_passed_candidate() -> None:
    assert assert_reviewed_before_testset(PASSED_ROW) is None  # tidak melempar galat


# -- assert_no_pii: pengaman umum untuk butir set uji dari SEMUA sumber, bukan hanya Gemma --

def test_assert_no_pii_rejects_phone_number() -> None:
    with pytest.raises(ValueError):
        assert_no_pii("daftar lewat WA 0800-0000-0000 ya", "v1-999")


def test_assert_no_pii_rejects_email() -> None:
    with pytest.raises(ValueError):
        assert_no_pii("hubungi admin@contoh.id untuk info lebih lanjut", "v1-999")


def test_assert_no_pii_allows_clean_text() -> None:
    assert assert_no_pii("klaim biasa tanpa data pribadi apa pun", "v1-999") is None


# -- pemeriksaan PII sebagai bagian TETAP alur (2026-09-26) -------------------

def test_format_failure_withholds_raw_output_containing_pii() -> None:
    """Keluaran mentah yang gagal diurai tetap diperiksa PII; bila ada penanda, teksnya tidak disimpan."""
    provider = ScriptedProvider(["bukan json, daftar lewat WA 0800-0000-0000 atau bantuan-contoh.web.id/daftar"])
    provider.model = "gemma-4-test"
    rows = generate_for_job(provider, "negatif_mudah", None, ARTICLES, DB_TITLES, GUIDE_TEXT)
    assert rows[0]["raw"] == RAW_WITHHELD
    assert {"nomor_telepon", "url_di_teks"} <= set(rows[0]["pemeriksaan"]["pii_flags"])
    assert "0800" not in str(rows[0])


def test_format_failure_keeps_clean_raw_output_for_audit() -> None:
    provider = ScriptedProvider(["ini bukan json"])
    provider.model = "gemma-4-test"
    rows = generate_for_job(provider, "negatif_mudah", None, ARTICLES, DB_TITLES, GUIDE_TEXT)
    assert rows[0]["raw"] == "ini bukan json"
    assert rows[0]["pemeriksaan"] == {"pii_flags": []}


def test_every_generated_row_carries_pii_check() -> None:
    provider = ScriptedProvider(['{"klaim": ["klaim bersih satu", "daftar di bit.ly/contoh-fiktif"]}'])
    provider.model = "gemma-4-test"
    rows = generate_for_job(provider, "negatif_mudah", None, ARTICLES, DB_TITLES, GUIDE_TEXT)
    assert_pii_checked(rows)  # tidak melempar
    flagged = [r for r in rows if r["pemeriksaan"]["pii_flags"]]
    assert len(flagged) == 1 and flagged[0]["lolos_pemeriksaan_otomatis"] is False


def test_assert_pii_checked_blocks_rows_without_pii_check() -> None:
    with pytest.raises(ValueError, match="pemeriksaan PII"):
        assert_pii_checked([{"klaim": "x", "pemeriksaan": {"leak_flag": False}}])
