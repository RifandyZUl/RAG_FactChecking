"""Uji metrik evaluasi: interval Wilson dan pemisahan jenis kesalahan (evaluation.metrics)."""

from evaluation.metrics import classify_error, error_report, wilson_interval


def test_wilson_interval_known_values() -> None:
    lo, hi = wilson_interval(20, 20)
    assert abs(lo - 0.8389) < 1e-3 and abs(hi - 1.0) < 1e-9
    lo, hi = wilson_interval(0, 20)
    assert lo == 0.0 and abs(hi - 0.1611) < 1e-3
    lo, hi = wilson_interval(19, 20)
    assert abs(lo - 0.7639) < 1e-3 and abs(hi - 0.9911) < 1e-3
    assert wilson_interval(0, 0) == (0.0, 1.0)
    lo, hi = wilson_interval(15, 30)
    assert lo < 0.5 < hi and abs((lo + hi) / 2 - 0.5) < 0.01


def test_classify_error_three_types_and_failure() -> None:
    assert classify_error("belum_ditemukan", "36729", "ditemukan", "36729") == "kecocokan_palsu"
    assert classify_error("belum_ditemukan", None, "tidak_ditemukan", None) is None
    assert classify_error("ditemukan", "36737", "tidak_ditemukan", None) == "penolakan_palsu"
    assert classify_error("ditemukan", "36737", "ditemukan", "36042") == "artikel_salah"
    assert classify_error("ditemukan", "36737", "ditemukan", "36737") is None
    assert classify_error("ditemukan", "36737", "gagal", None) == "gagal"


def _rec(ev: str, art: str | None, verdict: str, aid: str | None, batas: bool = False) -> dict[str, object]:
    return {"expected_verdict": ev, "expected_retrieval_article": art, "verdict": verdict, "article_id": aid,
            "batas": batas}


def test_error_report_separates_types_and_borderline() -> None:
    records = [
        _rec("ditemukan", "1", "ditemukan", "1"),                    # benar
        _rec("ditemukan", "2", "tidak_ditemukan", None),             # penolakan palsu
        _rec("ditemukan", "3", "ditemukan", "9"),                    # artikel salah
        _rec("belum_ditemukan", None, "tidak_ditemukan", None),      # benar
        _rec("belum_ditemukan", None, "ditemukan", "5"),             # kecocokan palsu
        _rec("belum_ditemukan", "6", "tidak_ditemukan", None),       # benar (kueri 3: terjangkau, tetap belum)
        _rec("ditemukan", "7", "tidak_ditemukan", None, batas=True),  # penolakan palsu, butir BATAS
        _rec("ditemukan", "8", "gagal", None),                       # gagal: tidak masuk penyebut
    ]
    rep = error_report(records)
    nb, b, allr = rep["non_batas"], rep["batas"], rep["semua"]
    assert nb["kesalahan"]["kecocokan_palsu"]["k"] == 1 and nb["kesalahan"]["kecocokan_palsu"]["n"] == 3
    assert nb["kesalahan"]["penolakan_palsu"]["k"] == 1 and nb["kesalahan"]["penolakan_palsu"]["n"] == 3
    assert nb["kesalahan"]["artikel_salah"]["k"] == 1
    assert nb["n_gagal"] == 1 and nb["n_butir"] == 7 and nb["benar"] == 3
    # butir batas dilaporkan terpisah, tidak masuk hitungan non-batas
    b_pen = b["kesalahan"]["penolakan_palsu"]
    assert b["n_butir"] == 1 and b_pen["k"] == 1 and b_pen["n"] == 1
    assert allr["kesalahan"]["penolakan_palsu"]["k"] == 2 and allr["kesalahan"]["penolakan_palsu"]["n"] == 4
    lo, hi = nb["kesalahan"]["kecocokan_palsu"]["wilson95"]
    assert 0 < lo < 1 / 3 < hi < 1
    # pergeseran jenis kesalahan terlihat walau akurasi total sama
    type1 = error_report([_rec("belum_ditemukan", None, "ditemukan", "5"), _rec("ditemukan", "1", "ditemukan", "1")])
    type2 = error_report([_rec("belum_ditemukan", None, "tidak_ditemukan", None),
                          _rec("ditemukan", "1", "tidak_ditemukan", None)])
    assert type1["semua"]["benar"] == type2["semua"]["benar"] == 1
    assert type1["semua"]["kesalahan"]["kecocokan_palsu"]["k"] == 1 == type2["semua"]["kesalahan"]["penolakan_palsu"]["k"]
    assert type1["semua"]["kesalahan"]["penolakan_palsu"]["k"] == 0
