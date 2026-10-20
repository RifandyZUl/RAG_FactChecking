"""Uji offline evaluation.external_analysis: kappa, ambang yang dikunci, label final, penilaian butir, kunci segel."""

import ast
import json
from pathlib import Path

import pytest

from evaluation import external_analysis as ea


def test_cohen_kappa_known_values():
    assert ea.cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    # po = 0,8; pe = 0,5*0,6 + 0,5*0,4 = 0,5 -> 0,6
    a = ["y"] * 5 + ["n"] * 5
    b = ["y"] * 5 + ["n"] * 4 + ["y"]
    assert ea.cohen_kappa(a, b) == pytest.approx((0.9 - 0.5) / 0.5)
    assert ea.cohen_kappa(["y", "y"], ["y", "y"]) is None, "kesepakatan peluang 1 -> tak terdefinisi"


def test_bootstrap_is_seeded_and_reports_undefined_resamples():
    a, b = ["y", "n", "y", "n", "y"], ["y", "n", "n", "n", "y"]
    r1, r2 = ea.bootstrap_kappa(a, b, n_boot=500), ea.bootstrap_kappa(a, b, n_boot=500)
    assert r1 == r2 and r1["benih"] == ea.BOOT_SEED
    assert r1["ulangan_tak_terdefinisi_dibuang"] > 0


@pytest.mark.parametrize("k,band", [(0.80, "pakai_apa_adanya"), (0.7999, "dua_arah"), (0.60, "dua_arah"),
                                    (0.5999, "bukan_gerbang"), (None, "tak_terdefinisi")])
def test_kappa_bands_follow_7_4(k, band):
    assert ea.kappa_band(k) == band


@pytest.mark.parametrize("k,n,cat", [(32, 42, "memadai"), (31, 42, "tidak_konklusif"), (19, 42, "tidak_konklusif"),
                                     (18, 42, "buruk")])
def test_positive_category_matches_counts_in_design(k, n, cat):
    assert ea.positive_category(k, n) == cat


@pytest.mark.parametrize("k,n,cat", [(4, 49, "lulus"), (5, 49, "tidak_konklusif"), (9, 49, "tidak_konklusif"), (10, 49, "gugur")])
def test_false_match_category_matches_counts_in_design(k, n, cat):
    assert ea.false_match_category(k, n) == cat


def test_worst_category():
    assert ea.worst("kecocokan_palsu", ["lulus", "tidak_konklusif"]) == "tidak_konklusif"
    assert ea.worst("positif", ["memadai", "buruk", "tidak_konklusif"]) == "buruk"


def _case(kode, art=None, ragu=False, days=None):
    r, n = kode[1], kode.split("-")[1]
    return {"kode": kode, "putaran": int(r), "butir": int(n), "l6_id": f"L{kode}", "dikeluarkan": None,
            "expected_verdict": "ditemukan" if art else "belum_ditemukan", "expected_article": art, "ragu": ragu,
            "selisih_hari": days, "strata_selisih": None if days is None else ("<=30" if abs(days) <= 30 else ">30")}


def test_final_labels_change_only_audit_items_that_changed(monkeypatch, tmp_path):
    for name in ("FROZEN_PATH", "SESSION_RESULT_PATH"):
        p = tmp_path / name
        p.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(ea, name, p)
    cases = {k: c for k, c in ((c["kode"], c) for c in [_case("P1-10"), _case("P1-30"), _case("P2-5", "111", days=40), _case("P2-6")])}
    session = [{"kode": "P1-10", "jenis_butir": "audit", "keputusan": "999", "ragu": True},
               {"kode": "P1-30", "jenis_butir": "audit", "keputusan": ea.NONE, "ragu": False},
               {"kode": "P2-5", "jenis_butir": "uji_ulang", "keputusan": ea.NONE, "ragu": False},  # uji ulang tidak mengubah
               {"kode": "P2-6", "jenis_butir": "uji_ulang", "keputusan": "222", "ragu": False}]
    out = ea.final_labels(cases, session, {"P1-10": -3})
    by = {it["kode"]: it for it in out["butir"]}
    assert out["berubah"] == ["P1-10"]
    assert by["P1-10"]["label_final"] == {"expected_verdict": "ditemukan", "expected_article": "999", "ragu": True}
    assert by["P1-10"]["label_awal"]["expected_verdict"] == "belum_ditemukan"
    assert by["P1-10"]["strata_selisih"]["label_final"] == "<=30"
    assert by["P2-5"]["label_final"]["expected_article"] == "111" and by["P2-6"]["label_final"]["expected_article"] is None
    with pytest.raises(SystemExit):
        ea.final_labels(cases, session, {})


def test_outcome_and_any_in_list_target():
    m = lambda v, a=None: {"verdict": v, "article_id": a}
    pos = {"positif": True, "sasaran": {"1"}}
    neg = {"positif": False, "sasaran": set()}
    anyl = {"positif": True, "sasaran": ea.ANY_IN_LIST}
    assert ea.outcome(pos, m("ditemukan", "1"), []) == "benar"
    assert ea.outcome(pos, m("ditemukan", "2"), ["2"]) == "artikel_salah"
    assert ea.outcome(pos, m("tidak_ditemukan"), []) == "penolakan_palsu"
    assert ea.outcome(neg, m("ditemukan", "5"), []) == "kecocokan_palsu"
    assert ea.outcome(neg, m("tidak_ditemukan"), []) == "benar"
    assert ea.outcome(anyl, m("ditemukan", "7"), ["7", "8"]) == "benar"
    assert ea.outcome(anyl, m("ditemukan", "9"), ["7", "8"]) == "artikel_salah"
    assert ea.outcome(pos, m(ea.UNANSWERED), []) == ea.UNANSWERED


def test_item_mode_splits_and_no_mode():
    r = lambda v, a: {"verdict": v, "article_id": a}
    assert ea.item_mode([r("ditemukan", "1")] * 2 + [r("tidak_ditemukan", None)])["kesepakatan"] == "mayoritas"
    nm = ea.item_mode([r("ditemukan", "1"), r("ditemukan", "2"), r("tidak_ditemukan", None)])
    assert nm["verdict"] == ea.UNANSWERED and nm["kesepakatan"] == "tanpa_modus"


def test_flip_and_summarize():
    labels = {"A": {"positif": True, "sasaran": {"1"}, "ragu": False, "putaran": 1, "strata_selisih": "<=30"},
              "B": {"positif": False, "sasaran": set(), "ragu": True, "putaran": 2, "strata_selisih": None}}
    modes = {"A": {"verdict": "ditemukan", "article_id": "1"}, "B": {"verdict": "ditemukan", "article_id": "3"}}
    s = ea.summarize(labels, modes, {"A": ["1"], "B": ["3"]})
    assert (s["positif"]["k"], s["positif"]["n"], s["kecocokan_palsu"]["k"], s["kecocokan_palsu"]["n"]) == (1, 1, 1, 1)
    flipped = ea.flip(labels, {"B": ea.ANY_IN_LIST, "A": None})
    s2 = ea.summarize(flipped, modes, {"A": ["1"], "B": ["3"]})
    assert (s2["positif"]["k"], s2["positif"]["n"], s2["kecocokan_palsu"]["k"]) == (1, 1, 1)
    assert labels["A"]["positif"], "label asli tidak berubah"


def test_discovery_stratum():
    keys = {"L": {"embedding_top": [["1", 0.7], ["2", 0.6]], "kata_kunci_top": [["3", 0.5, 0.4], ["1", 0.1, 0.1]]}}
    assert ea.discovery_stratum("L", "1", keys) == "a_teratas_embedding"
    assert ea.discovery_stratum("L", "2", keys) == "b_5_teratas_embedding"
    assert ea.discovery_stratum("L", "3", keys) == "c_hanya_kata_kunci"
    assert ea.discovery_stratum("L", "4", keys) == "di_luar_daftar_pencarian"


def test_metrics_refuse_until_final_labels_hash_is_recorded(monkeypatch, tmp_path):
    p = tmp_path / "label_final.json"
    p.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(ea, "FINAL_LABELS_PATH", p)
    monkeypatch.setattr(ea, "FINAL_LABELS_SHA256", "")
    with pytest.raises(SystemExit, match="segel tidak dibuka"):
        ea.locked_final_labels()
    monkeypatch.setattr(ea, "FINAL_LABELS_SHA256", "0" * 64)
    with pytest.raises(SystemExit, match="segel tidak dibuka"):
        ea.locked_final_labels()


def test_reliability_and_final_labels_do_not_touch_system_results():
    tree = ast.parse(Path(ea.__file__).read_text(encoding="utf-8"))
    funcs = {n.name: ast.unparse(n) for n in tree.body if isinstance(n, ast.FunctionDef)}
    for name in ("reliability", "final_labels", "cmd_reliability", "cmd_final_labels", "load_session", "agreement"):
        assert not any(s in funcs[name] for s in ("LIPUTAN6_EVAL", "external_eval_", "load_eval_records", "V1_1532")), name


def test_recorded_final_labels_hash_is_in_design_document():
    doc = (Path(ea.__file__).parents[2] / "docs" / "rancangan_evaluasi_eksternal.md").read_text(encoding="utf-8")
    assert ea.FINAL_LABELS_SHA256 == "" or ea.FINAL_LABELS_SHA256 in doc


def test_reliability_on_small_session():
    cases = {c["kode"]: c for c in [_case("P2-1", "1"), _case("P2-2"), _case("P1-6", "5"), _case("P1-10")]}
    session = [{"kode": "P2-1", "putaran": 2, "jenis_butir": "uji_ulang", "keputusan": "1", "ragu": False},
               {"kode": "P2-2", "putaran": 2, "jenis_butir": "uji_ulang", "keputusan": "7", "ragu": True},
               {"kode": "P1-6", "putaran": 1, "jenis_butir": "uji_ulang", "keputusan": "6", "ragu": False},
               {"kode": "P1-10", "putaran": 1, "jenis_butir": "audit", "keputusan": "8", "ragu": False}]
    audit = {"rinci": [{"putaran": 1, "butir": 10, "kandidat_berjejak": ["8"], "sinyal": {"8": {"ada": True}}}]}
    out = ea.reliability(cases, session, audit)
    assert out["gabungan_30"]["n"] == 3 and out["gabungan_30"]["arah_perubahan"] == {"sama": 1, "TIDAK_ADA_ke_cocok": 1, "id_lain": 1}
    assert out["audit_7"]["TIDAK_ADA_ke_cocok"] == 1 and out["audit_7"]["cocok_dan_sama_dengan_jejak"] == 1
    assert json.dumps(out)  # dapat ditulis
