"""Uji perhitungan ukuran sampel (evaluation.sample_size): rumus terhadap nilai yang sudah diketahui."""

import json
from pathlib import Path

import pytest

from evaluation.sample_size import (
    build_report,
    mcnemar_exact_p,
    n_for_non_overlap,
    n_for_paired_improvement,
    prob_at_least,
    wilson,
)

ROOT = Path(__file__).resolve().parent.parent


def test_wilson_matches_values_recorded_for_v1() -> None:
    """Angka di testset/v1_analysis_report.txt: 48/50 -> [0,865; 0,989]; semua benar n=20 -> 0,84, n=30 -> 0,89."""
    lo, hi = wilson(48, 50)
    assert (round(lo, 3), round(hi, 3)) == (0.865, 0.989)
    assert round(wilson(20, 20)[0], 2) == 0.84 and round(wilson(30, 30)[0], 2) == 0.89
    assert wilson(0, 20)[0] == pytest.approx(0.0, abs=1e-12) and round(wilson(0, 20)[1], 3) == 0.161
    with pytest.raises(ValueError, match="positif"):
        wilson(0, 0)


def test_mcnemar_exact_known_values() -> None:
    assert mcnemar_exact_p(0, 0) == 1.0
    assert mcnemar_exact_p(6, 0) == pytest.approx(2 / 64)  # 0,03125: terkecil yang < 0,05 tanpa kemunduran
    assert mcnemar_exact_p(5, 0) == pytest.approx(2 / 32) and mcnemar_exact_p(5, 0) > 0.05
    assert mcnemar_exact_p(0, 6) == mcnemar_exact_p(6, 0), "dua sisi: simetris"
    assert mcnemar_exact_p(8, 1) == pytest.approx(2 * (1 + 9) / 512)
    assert mcnemar_exact_p(3, 3) == 1.0


def test_binomial_tail_and_paired_sample_size() -> None:
    assert prob_at_least(0, 10, 0.3) == pytest.approx(1.0)
    assert prob_at_least(10, 10, 0.5) == pytest.approx(0.5 ** 10)
    n = n_for_paired_improvement(0.10)
    assert n is not None and prob_at_least(6, n, 0.10) >= 0.8 > prob_at_least(6, n - 1, 0.10)
    assert n_for_paired_improvement(1.0) == 6, "bila semua butir membaik, enam butir cukup"
    assert n_for_paired_improvement(0.04) > n_for_paired_improvement(0.10) > n_for_paired_improvement(0.50)


def test_non_overlap_is_monotone_and_validated() -> None:
    near, far = n_for_non_overlap(0.96, 0.99), n_for_non_overlap(0.10, 0.80)
    assert near is not None and far is not None and near > 100 > far
    n = n_for_non_overlap(0.80, 0.95)
    assert n is not None and wilson(round(0.95 * n), n)[0] > wilson(round(0.80 * n), n)[1]
    with pytest.raises(ValueError):
        n_for_non_overlap(0.9, 0.9)


def test_stored_result_file_matches_the_formulas() -> None:
    """Berkas hasil yang dikutip docs/rancangan_v2.md harus sama dengan hasil hitung ulang."""
    stored = json.loads((ROOT / "testset" / "v2_ukuran_sampel.json").read_text(encoding="utf-8"))
    assert stored == json.loads(json.dumps(build_report(), ensure_ascii=False))
