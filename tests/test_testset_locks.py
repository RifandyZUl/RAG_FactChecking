"""Kunci set uji v1: pedoman anotasi dan prompt sistem tidak boleh berubah diam-diam setelah pra-registrasi."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from generator import RESPONSE_SCHEMA, SYSTEM_PROMPT

TESTSET = Path(__file__).resolve().parent.parent / "testset"
ROOT = TESTSET.parent


def _norm_sha(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def test_annotation_guide_matches_lock() -> None:
    lock = json.loads((TESTSET / "GUIDE_LOCK.json").read_text(encoding="utf-8"))
    guide = (TESTSET / lock["berkas"].split("/")[-1]).read_text(encoding="utf-8")
    assert _norm_sha(guide) == lock["sha256_ternormalisasi"], (
        "ANNOTATION_GUIDE.md berubah setelah dikunci: pedoman hanya boleh berubah lewat versi baru (set uji baru)"
    )
    assert f"Versi {lock['versi']}" in guide


def test_meta_preregistration_is_consistent_with_locks() -> None:
    meta = json.loads((TESTSET / "v1.meta.json").read_text(encoding="utf-8"))
    lock = json.loads((TESTSET / "GUIDE_LOCK.json").read_text(encoding="utf-8"))
    assert meta["pedoman_anotasi"]["sha256_ternormalisasi"] == lock["sha256_ternormalisasi"]
    prompt_sha = _norm_sha(SYSTEM_PROMPT + "\n--skema--\n" + json.dumps(RESPONSE_SCHEMA, sort_keys=True, ensure_ascii=False))
    assert meta["prompt_sistem"]["sha256_ternormalisasi"] == prompt_sha, (
        "prompt sistem/skema berubah setelah pra-registrasi set uji v1: perubahan berarti set uji baru"
    )


def test_meta_preregisters_metric_thresholds_and_limitations() -> None:
    """Ambang dan metrik utama ditulis SEBELUM data dibuat (tidak boleh disesuaikan setelah hasil keluar)."""
    meta = json.loads((TESTSET / "v1.meta.json").read_text(encoding="utf-8"))
    assert meta["butir"] is not None and len(meta["sha256_butir"]) == 64, (
        "testset/v1.jsonl sudah disusun (2026-09-23, disetujui pemilik proyek) -- butir dan "
        "sha256_butir seharusnya sudah terisi, bukan lagi null seperti sebelum data dibuat."
    )
    ev = meta["evaluasi"]
    assert ev["jumlah_run"] == 3 and "modus" in ev["metrik_utama"] and "tidak dipakai" in ev["seed"]
    assert "Wilson" in ev["interval_kepercayaan"]
    assert meta["ambang"]["H1"]["terdukung"] == "<= 1 dari 20" and meta["ambang"]["H1"]["gugur"] == ">= 3 dari 20"
    assert meta["ambang"]["H3"]["gugur"].startswith(">= 5 kesalahan dari 50")
    assert any("satu anotator" in k.lower() for k in meta["keterbatasan"])
    # dua label terpisah dan dua jenis kesalahan yang dipisah, ditulis sebelum data
    fmt = meta["format_butir"]
    assert "expected_retrieval_article" in fmt["kolom"] and "expected_verdict" in fmt["kolom"]
    assert "batas" in fmt["kolom"] and "kekhususan" in fmt["kolom"]
    err = ev["jenis_kesalahan"]
    assert set(err["dipisah"]) == {"kecocokan_palsu", "penolakan_palsu", "artikel_salah"}
    assert "Wilson" in err["interval"] and "batas dan non-batas" in err["himpunan"]
    assert any("kecocokan palsu" in x and "penolakan palsu" in x for x in ev["laporan_wajib"])
    # keputusan sumber dan confound (ditulis sebelum data)
    src = meta["sumber_butir"]
    assert set(src["nilai"]) == {"buatan_model", "manusia", "teks_nyata"}
    assert "MENGETAHUI TOPIK SASARAN" in src["manusia"] and "independensinya tidak penuh" in src["manusia"]
    assert "DILEPAS" in src["lintas_situs_otomatis"] and "TIDAK dipakai" in src["lintas_situs_otomatis"]
    cs = meta["komposisi_sumber_rancangan"]
    neg = cs["negatif_sulit"]
    assert neg["pola_sama_entitas_beda"]["total"] + neg["entitas_sama_klaim_beda"]["total"] + neg["angka_waktu_beda"]["total"] == 20
    assert "tumpang tindih" in ev["confound_sumber"]["masalah"] and "WAJIB" in ev["confound_sumber"]["aturan_pelaporan"]
    assert any("tabel silang" in x for x in ev["laporan_wajib"])
    assert "TIDAK ditampilkan" in meta["penyaring_otomatis"]["kelas_usulan"]
    assert "kesepakatan" in meta["penyaring_otomatis"]["evaluasi"]
    assert any("mengetahui topik sasaran" in k for k in meta["keterbatasan"])
    c = meta["komposisi_rancangan"]
    assert c["positif"] + c["negatif_sulit"] + c["negatif_mudah"] == c["total"] == 50
    assert sum(c["alokasi_positif_label"].values()) == 20 == sum(c["alokasi_positif_sel"].values())


def test_v1_jsonl_matches_recorded_hash_and_composition() -> None:
    """testset/v1.jsonl (bila sudah disusun) harus persis cocok dengan sha256_butir di v1.meta.json --
    perubahan diam-diam pada berkas butir setelah dicatat di sini harus terdeteksi."""
    meta = json.loads((TESTSET / "v1.meta.json").read_text(encoding="utf-8"))
    if meta["butir"] is None:
        return  # belum disusun -- lihat test_meta_preregisters_metric_thresholds_and_limitations
    lines = (TESTSET / "v1.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(x) for x in lines if x.strip()]
    reserialized = "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows)
    assert hashlib.sha256(reserialized.encode("utf-8")).hexdigest() == meta["sha256_butir"]
    c = meta["komposisi_rancangan"]
    n_batas = sum(1 for r in rows if r["batas"])
    n_utama = len(rows) - n_batas
    assert n_utama == c["total"] == 50
    assert sum(1 for r in rows if r["tipe"] == "positif") == c["positif"]
    assert sum(1 for r in rows if r["tipe"] == "negatif_sulit") == c["negatif_sulit"]
    assert sum(1 for r in rows if r["tipe"] == "negatif_mudah") == c["negatif_mudah"]


def test_generator_fingerprint_matches_frozen_lock() -> None:
    """
    Sidik jari generator v1 (prompt+skema, seluruh generator.py, model, thinking_level bawaan)
    dikunci di v1.meta.json.sidik_jari_generator_v1 saat pembekuan. Hasil evaluasi TIDAK SAH
    disebut "untuk v1" bila salah satu berubah sejak pembekuan -- uji ini menolak (gagal) bila
    itu terjadi, dijalankan otomatis sebagai bagian test suite biasa (bukan hanya sebelum
    evaluasi). Skrip evaluasi (belum ditulis) wajib menjalankan pemeriksaan setara sebelum
    menandai hasil sebagai valid untuk v1.
    """
    meta = json.loads((TESTSET / "v1.meta.json").read_text(encoding="utf-8"))
    if "sidik_jari_generator_v1" not in meta:
        pytest.skip("belum dibekukan")
    lock = meta["sidik_jari_generator_v1"]

    prompt_sha = _norm_sha(SYSTEM_PROMPT + "\n--skema--\n" + json.dumps(RESPONSE_SCHEMA, sort_keys=True, ensure_ascii=False))
    assert lock["sha256_prompt_sistem_dan_skema"] == prompt_sha, (
        "prompt sistem/skema berubah sejak pembekuan testset-v1: hasil evaluasi tidak sah untuk v1"
    )

    generator_src = (ROOT / "src" / "generator.py").read_text(encoding="utf-8")
    assert lock["sha256_generator_py"] == _norm_sha(generator_src), (
        "src/generator.py berubah sejak pembekuan testset-v1 (di luar SYSTEM_PROMPT/RESPONSE_SCHEMA "
        "yang sudah dicek terpisah): hasil evaluasi tidak sah untuk v1"
    )

    from llm.gemini import DEFAULT_GEMINI_MODEL

    assert lock["model"] == DEFAULT_GEMINI_MODEL, "model bawaan generator berubah sejak pembekuan testset-v1"
    assert lock["thinking_level"] == "medium", (
        "thinking_level terkunci di v1.meta.json bukan 'medium' -- periksa apakah ini sengaja "
        "(bawaan GeminiProvider saat ini juga 'medium', lihat src/llm/gemini.py)"
    )


def test_v1_jsonl_unchanged_since_tag() -> None:
    """testset/v1.jsonl tidak boleh berubah setelah tag testset-v1 diberikan -- dibandingkan
    byte-demi-byte dengan isi persis pada tag itu, bukan hanya hash yang tercatat di v1.meta.json
    (yang bisa saja ikut diubah bersamaan)."""
    tag_check = subprocess.run(["git", "tag", "-l", "testset-v1"], cwd=ROOT, capture_output=True, text=True)
    if "testset-v1" not in tag_check.stdout.split():
        pytest.skip("tag testset-v1 belum dibuat")
    tagged = subprocess.run(["git", "show", "testset-v1:testset/v1.jsonl"], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
    current = (TESTSET / "v1.jsonl").read_text(encoding="utf-8")
    assert current == tagged, "testset/v1.jsonl berbeda dari isi yang dibekukan pada tag testset-v1"
