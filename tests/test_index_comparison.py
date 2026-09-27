"""Uji offline evaluation.index_comparison (tanpa model/indeks): perbandingan dua indeks per butir."""

from evaluation.index_comparison import compare
from evaluation.retrieval_ablation import ChunkScore


class FakeMatrix:
    """Pengganti ChunkMatrix: skor chunk tetap per butir (vektor = id butir)."""

    def __init__(self, table: dict[str, list[tuple[str, float]]]) -> None:
        self.table = table

    def scores(self, query_vector: str) -> list[ChunkScore]:
        return [ChunkScore(aid, "narasi", s) for aid, s in self.table[query_vector]]


def _item(iid: str, tipe: str, target: str | None, url: str | None = None) -> dict:
    return {"id": iid, "tipe": tipe, "expected_retrieval_article": target, "url_asal": url}


def test_compare_reports_new_candidates_source_article_and_score_shift() -> None:
    items = [_item("p1", "positif", "10"),
             _item("n1", "negatif_mudah", None, "https://turnbackhoax.id/articles/99-contoh")]
    base = FakeMatrix({"p1": [("10", 0.80), ("11", 0.50)], "n1": [("11", 0.52)]})
    # indeks pembanding = superset: artikel baru 20 menyalip sasaran p1, artikel asal n1 (99) kini ada
    other = FakeMatrix({"p1": [("10", 0.80), ("11", 0.50), ("20", 0.85)], "n1": [("11", 0.52), ("99", 0.83)]})
    res = compare(items, ["p1", "n1"], {"dasar": base, "pembanding": other},
                  {"dasar": {"10", "11"}, "pembanding": {"10", "11", "20", "99"}}, threshold=0.5739)

    p1, n1 = res["butir"]
    assert (p1["dasar"]["peringkat_sasaran"], p1["pembanding"]["peringkat_sasaran"]) == (1, 2)
    assert n1["artikel_asal_tbh"] == "99" and n1["pembanding"]["artikel_asal_ada"] is True
    assert n1["dasar"]["artikel_asal_ada"] is False
    assert n1["pembanding"]["top3_di_atas_ambang"] == [["99", 0.83, False]], "False = artikel baru"
    assert res["negatif_dengan_kandidat_di_atas_ambang"] == {"dasar": [], "pembanding": ["n1"]}
    assert res["negatif_artikel_asal_kini_ada_di_pembanding"] == ["n1"]
    s = res["sebaran_per_tipe"]["positif"]
    assert s["naik"] == 1 and s["turun"] == 0 and s["artikel_top1_berganti"] == ["p1"]
