"""Pembuktian embedding Tahap 2: ambang putusan (ditetapkan sebelum mengukur) dan perbandingan top-3."""

import numpy as np
import pytest

from evaluation import embedding_proof as ep


def _stats(minimum: float, mean: float) -> dict[str, float]:
    return {"minimum": minimum, "rata_rata": mean, "persentil_1": minimum, "maksimum": 1.0}


@pytest.mark.parametrize(("minimum", "mean", "hnsw", "cross", "expected"), [
    (0.999995, 0.9999995, 0, None, ep.VERDICT_SAME),
    (0.99999, 0.999999, 0, 0, ep.VERDICT_SAME),           # tepat di ambang = SAMA
    (0.999989, 0.9999995, 0, 0, ep.VERDICT_BETWEEN),      # minimum di bawah ambang SAMA
    (0.999995, 0.9999989, 0, 0, ep.VERDICT_BETWEEN),      # rata-rata di bawah ambang SAMA
    (0.999, 0.9999, 0, 0, ep.VERDICT_BETWEEN),            # tepat 0,999 belum BERHENTI
    (0.99899, 0.9999, 0, 0, ep.VERDICT_STOP),
    (0.999999, 0.9999999, 1, 0, ep.VERDICT_STOP),         # HNSW != eksak di lingkungan ini
    (0.999999, 0.9999999, 0, 1, ep.VERDICT_STOP),         # top-3 beda dengan lingkungan pembanding
])
def test_verdict_thresholds(minimum: float, mean: float, hnsw: int, cross: int | None, expected: str) -> None:
    assert ep.verdict(_stats(minimum, mean), hnsw, cross) == expected


def test_sample_is_deterministic_and_independent_of_input_order() -> None:
    ids = [f"{i}_narasi" for i in range(1000)]
    first = ep.sample_ids(ids)
    assert len(first) == ep.SAMPLE_SIZE == len(set(first))
    assert ep.sample_ids(list(reversed(ids))) == first


def test_cosine_rows_does_not_assume_normalised_vectors() -> None:
    a = np.array([[3.0, 4.0], [1.0, 0.0]])
    b = np.array([[6.0, 8.0], [0.0, 1.0]])
    assert np.allclose(ep.cosine_rows(a, b), [1.0, 0.0])


def test_compare_top3_reports_differing_queries_and_score_delta() -> None:
    own = {"q1": [["a", 0.9], ["b", 0.8], ["c", 0.7]], "q2": [["d", 0.6], ["e", 0.5], ["f", 0.4]]}
    same = {"q1": [["a", 0.9001], ["b", 0.8], ["c", 0.7]], "q2": [["d", 0.6], ["f", 0.5], ["e", 0.4]]}
    out = ep.compare_top3(own, same)
    assert out["top3_berbeda"] == ["q2"]
    assert out["maks_selisih_skor"] == pytest.approx(0.0001)
    with pytest.raises(ValueError):
        ep.compare_top3(own, {"q1": own["q1"]})
