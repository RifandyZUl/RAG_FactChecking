"""Kunci set uji v1: pedoman anotasi dan prompt sistem tidak boleh berubah diam-diam setelah pra-registrasi."""

import hashlib
import json
from pathlib import Path

from generator import RESPONSE_SCHEMA, SYSTEM_PROMPT

TESTSET = Path(__file__).resolve().parent.parent / "testset"


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
    assert meta["butir"] is None and meta["status"].startswith("PRA-REGISTRASI")
    ev = meta["evaluasi"]
    assert ev["jumlah_run"] == 3 and "modus" in ev["metrik_utama"] and "tidak dipakai" in ev["seed"]
    assert "Wilson" in ev["interval_kepercayaan"]
    assert meta["ambang"]["H1"]["terdukung"] == "<= 1 dari 20" and meta["ambang"]["H1"]["gugur"] == ">= 3 dari 20"
    assert meta["ambang"]["H3"]["gugur"].startswith(">= 5 kesalahan dari 50")
    assert any("satu anotator" in k.lower() for k in meta["keterbatasan"])
    c = meta["komposisi_rancangan"]
    assert c["positif"] + c["negatif_sulit"] + c["negatif_mudah"] == c["total"] == 50
    assert sum(c["alokasi_positif_label"].values()) == 20 == sum(c["alokasi_positif_sel"].values())
