"""Uji perbandingan keputusan antarmodel (evaluation.comparison).
"""


def test_compare_models_h3() -> None:
    from evaluation.comparison import compare_models

    cases = [(f"p{i}", f"9{i}", "positif") for i in range(5)] + \
            [(f"n{i}", None, "negatif") for i in range(5)]

    def mk(v, a=None):
        return {"verdict": v, "article_id": a}

    base = {f"p{i}": mk("ditemukan", f"9{i}") for i in range(5)}
    base.update({f"n{i}": mk("tidak_ditemukan") for i in range(5)})

    assert compare_models(base, dict(base), cases)[1].startswith("TERDUKUNG")
    one_pos = dict(base, p0=mk("tidak_ditemukan"))
    assert compare_models(base, one_pos, cases)[1].startswith("TERDUKUNG"), "1 beda positif lolos"
    two_pos = dict(one_pos, p1=mk("tidak_ditemukan"))
    assert compare_models(base, two_pos, cases)[1].startswith("TIDAK TERDUKUNG")
    one_neg = dict(base, n2=mk("ditemukan", "36214"))
    assert compare_models(base, one_neg, cases)[1].startswith("TIDAK TERDUKUNG"), "negatif harus sama"
    wrong_id = dict(base, p3=mk("ditemukan", "lain"))
    assert compare_models(base, wrong_id, cases)[1].startswith("TERDUKUNG"), "beda id = 1 beda positif"
    partial = {k: v for k, v in base.items() if k != "n4"}
    assert compare_models(base, partial, cases)[1].startswith("BELUM KONKLUSIF")
