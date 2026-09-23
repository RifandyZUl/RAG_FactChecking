"""
Uji offline evaluation.testset_analysis -- data tiruan seluruhnya (tidak membaca berkas nyata
proyek, tidak memanggil API). Menguji keputusan modus, kesepakatan antar-run, akurasi+Wilson,
jenis kesalahan, Recall@3, pasangan minimal, ambang H1/H3, dan diagnostik (disagreement, format,
URL di luar metadata, latensi/token).
"""
import json

import pytest

from evaluation import testset_analysis as ta

V1_ITEMS = {
    "v1-001": {"id": "v1-001", "klaim": "klaim satu", "tipe": "positif", "subtipe": None,
               "expected_retrieval_article": "100", "expected_verdict": "ditemukan",
               "expected_label": "SALAH", "kekhususan": "spesifik", "batas": False, "sumber": "manusia"},
    "v1-002": {"id": "v1-002", "klaim": "klaim dua", "tipe": "negatif_sulit",
               "subtipe": "pola_sama_entitas_beda", "expected_retrieval_article": "200",
               "expected_verdict": "belum_ditemukan", "expected_label": None, "kekhususan": "spesifik",
               "batas": False, "sumber": "teks_nyata"},
    "v1-003": {"id": "v1-003", "klaim": "klaim tiga", "tipe": "positif", "subtipe": None,
               "expected_retrieval_article": "300", "expected_verdict": "ditemukan",
               "expected_label": "PENIPUAN", "kekhususan": "spesifik", "batas": False, "sumber": "buatan_model"},
    "v1-004": {"id": "v1-004", "klaim": "klaim empat", "tipe": "negatif_sulit",
               "subtipe": "angka_waktu_beda", "expected_retrieval_article": "300",
               "expected_verdict": "belum_ditemukan", "expected_label": None, "kekhususan": "spesifik",
               "batas": False, "sumber": "buatan_model"},
    "v1-005": {"id": "v1-005", "klaim": "klaim lima", "tipe": "negatif_mudah", "subtipe": None,
               "expected_retrieval_article": None, "expected_verdict": "belum_ditemukan",
               "expected_label": None, "kekhususan": "jauh", "batas": False, "sumber": "teks_nyata"},
    "v1-006": {"id": "v1-006", "klaim": "klaim enam", "tipe": "batas", "subtipe": None,
               "expected_retrieval_article": "400", "expected_verdict": "belum_ditemukan",
               "expected_label": "SALAH", "kekhususan": "batas", "batas": True, "sumber": "liputan6"},
}

META = {
    "ambang": {
        "H1": {"terdukung": "<= 1 dari 20", "tidak_konklusif": "2 dari 20", "gugur": ">= 3 dari 20"},
        "H3": {"gugur": ">= 5 kesalahan dari 50 pada keputusan modus, atau pelanggaran format >= 2"},
    },
    "hasil_penyusunan_testset_v1_2026-09-23": {
        "pasangan_minimal_2026-09-23": {
            "hasil": {"daftar_pasangan": [
                {"artikel": "300", "negatif_sulit": "v1-004", "subtipe": "angka_waktu_beda"},
            ]},
        },
    },
}

ARTICLES = [
    {"article_id": "100", "url": "https://turnbackhoax.id/articles/100-x", "references": ["https://sumber-sahih.example/100"]},
    {"article_id": "200", "url": "https://turnbackhoax.id/articles/200-x", "references": []},
    {"article_id": "300", "url": "https://turnbackhoax.id/articles/300-x", "references": ["https://sumber-sahih.example/300"]},
    {"article_id": "400", "url": "https://turnbackhoax.id/articles/400-x", "references": []},
]


def call(latency=5.0, tok_in=1000, tok_out=50, rate_limited=0, error=""):
    return {"ok": True, "attempts": 1, "latency_s": latency, "input_tokens": tok_in,
            "output_tokens": tok_out, "thought_tokens": 10, "structured_mode": "schema",
            "rate_limited": rate_limited, "error": error, "model_version": "v1"}


def attempt(verdict, article_id, alasan="alasan", raw="{}", parse_failures=0, calls=None):
    return {"percobaan_ke": 1, "verdict": verdict, "article_id": article_id, "status_label": None,
            "error": "", "invalid_id": False, "parse_failures": parse_failures,
            "raw_outputs": [raw], "calls": calls or [call()]}


def rec(id_, run, verdict, article_id, top3, recall, alasan="alasan", raw="{}", parse_failures=0):
    return {
        "run": run, "id": id_, "verdict": verdict, "article_id": article_id, "alasan": alasan,
        "retrieval_top3": [{"article_id": a, "score": 0.6} for a in top3],
        "recall_at_3": recall,
        "percobaan": [attempt(verdict, article_id, alasan, raw, parse_failures)],
    }


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def build_eval_rows():
    rows = []
    # v1-001: bulat, benar ketiga run
    for run in (1, 2, 3):
        rows.append(rec("v1-001", run, "ditemukan", "100", ["100", "150"], True,
                        raw='{"artikel_terpilih":"100"}' if run != 1 else "url http://evil.example/x"))
    # v1-002: mayoritas benar (2x tidak_ditemukan, 1x kecocokan_palsu)
    rows.append(rec("v1-002", 1, "tidak_ditemukan", None, ["900"], False))
    rows.append(rec("v1-002", 2, "tidak_ditemukan", None, ["900"], False))
    rows.append(rec("v1-002", 3, "ditemukan", "900", ["900"], False))
    # v1-003: tanpa modus (ketiga run beda)
    rows.append(rec("v1-003", 1, "ditemukan", "300", ["300", "310"], True))
    rows.append(rec("v1-003", 2, "ditemukan", "999", ["300", "310"], True))
    rows.append(rec("v1-003", 3, "tidak_ditemukan", None, ["300", "310"], True))
    # v1-004: bulat benar (pasangan minimal dengan v1-003)
    for run in (1, 2, 3):
        rows.append(rec("v1-004", run, "tidak_ditemukan", None, ["300", "310"], True))
    # v1-005 (negatif_mudah): bulat benar, tanpa expected_retrieval_article
    for run in (1, 2, 3):
        rows.append(rec("v1-005", run, "tidak_ditemukan", None, ["999"], None))
    # v1-006 (batas): mayoritas benar, dengan 1 parse_failure dan format sekali
    rows.append(rec("v1-006", 1, "tidak_ditemukan", None, ["400"], True, parse_failures=1))
    rows.append(rec("v1-006", 2, "tidak_ditemukan", None, ["400"], True))
    rows.append(rec("v1-006", 3, "ditemukan", "400", ["400"], True))
    return rows


@pytest.fixture
def fixture_dir(tmp_path):
    v1_path = tmp_path / "v1.jsonl"
    write_jsonl(v1_path, list(V1_ITEMS.values()))
    meta_path = tmp_path / "v1.meta.json"
    meta_path.write_text(json.dumps(META, ensure_ascii=False), encoding="utf-8")
    eval_path = tmp_path / "eval.jsonl"
    write_jsonl(eval_path, build_eval_rows())
    return v1_path, meta_path, eval_path


# ---- unit: keputusan modus & kesepakatan ---------------------------------------------------

def test_compute_mode_unanimous():
    recs = [{"verdict": "ditemukan", "article_id": "100"}] * 3
    assert ta.compute_mode(recs) == ("ditemukan", "100", True)


def test_compute_mode_majority():
    recs = [{"verdict": "tidak_ditemukan", "article_id": None},
            {"verdict": "tidak_ditemukan", "article_id": None},
            {"verdict": "ditemukan", "article_id": "900"}]
    assert ta.compute_mode(recs) == ("tidak_ditemukan", None, True)


def test_compute_mode_no_majority():
    recs = [{"verdict": "ditemukan", "article_id": "1"},
            {"verdict": "ditemukan", "article_id": "2"},
            {"verdict": "tidak_ditemukan", "article_id": None}]
    verdict, article_id, ada_modus = ta.compute_mode(recs)
    assert verdict == ta.NO_MODE and article_id is None and ada_modus is False


def test_agreement_kind_bulat_mayoritas_tanpa_modus():
    bulat = [{"verdict": "a", "article_id": "1"}] * 3
    mayoritas = [{"verdict": "a", "article_id": "1"}, {"verdict": "a", "article_id": "1"},
                {"verdict": "b", "article_id": "2"}]
    tanpa = [{"verdict": "a", "article_id": "1"}, {"verdict": "b", "article_id": "2"},
             {"verdict": "c", "article_id": "3"}]
    assert ta.agreement_kind(bulat) == "bulat"
    assert ta.agreement_kind(mayoritas) == "mayoritas"
    assert ta.agreement_kind(tanpa) == ta.NO_MODE


# ---- integrasi: run_analysis penuh dengan fixture tiruan ------------------------------------

def test_run_analysis_accuracy_and_no_mode_excluded(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)

    acc = result["A_akurasi_non_batas"]
    # non-batas: v1-001(benar), v1-002(benar), v1-003(tanpa modus), v1-004(benar), v1-005(benar)
    assert acc["n_total_butir"] == 5
    assert acc["n_tanpa_modus"] == 1 and acc["id_tanpa_modus"] == ["v1-003"]
    assert acc["n_dengan_modus"] == 4
    assert acc["benar"] == 4  # keempat yang punya modus semuanya benar

    acc_batas = result["A_akurasi_batas"]
    assert acc_batas["n_total_butir"] == 1 and acc_batas["benar"] == 1


def test_run_analysis_error_breakdown_counts_kecocokan_palsu(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)
    err = result["A_jenis_kesalahan_non_batas"]
    # v1-002 modusnya tidak_ditemukan (mayoritas benar) -> TIDAK ada kecocokan_palsu di level modus
    assert err["kecocokan_palsu"]["k"] == 0
    assert err["penolakan_palsu"]["k"] == 0
    assert err["artikel_salah"]["k"] == 0


def test_run_analysis_recall_at_3(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)
    r3 = result["A_recall_at_3_non_batas"]
    # butir dengan expected_retrieval_article di antara non-batas: v1-001,v1-002,v1-003,v1-004 (bukan v1-005)
    assert r3["n"] == 4
    assert r3["k"] == 3  # v1-002 recall False, tiga lainnya True
    assert r3["run_tidak_konsisten"] == []


def test_run_analysis_minimal_pair_uses_meta_verbatim(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)
    pairs = result["A_pasangan_minimal_per_subtipe"]["angka_waktu_beda"]
    assert pairs["n"] == 1
    p = pairs["pasangan"][0]
    assert p["positif"] == "v1-003" and p["negatif_sulit"] == "v1-004"
    assert p["positif_benar"] is None  # v1-003 tanpa modus
    assert p["negatif_sulit_benar"] is True
    assert p["kedua_benar"] is None  # tidak bisa dihitung tanpa modus positif
    assert pairs["kedua_benar"] == 0


def test_run_analysis_h1_h3_status(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)
    h1 = result["A_H1"]
    assert h1["n_negatif_sulit"] == 2  # v1-002, v1-004
    assert h1["kecocokan_palsu"] == 0
    assert "TERDUKUNG" in h1["status"]
    h3 = result["A_H3"]
    assert "TERDUKUNG" in h3["status"] or "GUGUR" in h3["status"]


def test_run_analysis_disagreements_lists_non_unanimous(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)
    ids = {d["id"] for d in result["B_disagreements"]}
    assert ids == {"v1-002", "v1-003", "v1-006"}
    v1_003 = next(d for d in result["B_disagreements"] if d["id"] == "v1-003")
    assert v1_003["kesepakatan"] == ta.NO_MODE
    assert len(v1_003["per_run"]) == 3
    assert v1_003["per_run"][0]["alasan"] == "alasan"


def test_run_analysis_format_violations(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)
    fmt = result["B_format_violations"]
    assert fmt["total"] == 1
    assert fmt["per_butir"] == {"v1-006": 1}


def test_run_analysis_urls_outside_metadata_detected(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)
    urls = result["B_urls_outside_metadata"]
    assert urls["total"] >= 1
    assert "v1-001" in urls["per_butir"]
    assert any("evil.example" in u for u in urls["per_butir"]["v1-001"])


def test_run_analysis_latency_tokens_per_run(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)
    lt = result["B_latency_tokens_per_run"]
    assert set(lt) == {1, 2, 3}
    for run_stats in lt.values():
        assert run_stats["n_butir"] == 6
        assert run_stats["latensi_rata2_s"] > 0


def test_format_report_runs_without_error(fixture_dir):
    v1_path, meta_path, eval_path = fixture_dir
    result = ta.run_analysis(eval_path, v1_path, meta_path, articles=ARTICLES)
    text = ta.format_report(result)
    assert "CAVEAT WAJIB" in text
    assert "KETERGANTUNGAN ARTIKEL JANGKAR" in text
    assert "v1-003" in text  # muncul di diagnostik disagreement
