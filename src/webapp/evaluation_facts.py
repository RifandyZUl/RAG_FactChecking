"""
Angka evaluasi yang tampil di halaman "Tentang": DIHITUNG dari berkas hasil yang di-commit, tidak diketik.

Sumber tunggal:
- `testset/eksternal_hasil_per_butir.json`: 91 butir set eksternal Liputan6 (label final + keputusan
  modus 3 run), dipublikasikan sesuai `docs/rancangan_evaluasi_eksternal.md` bagian 8.
- `testset/eksternal_butir.json`: ukuran indeks yang dibekukan saat evaluasi.

Kategori memakai aturan yang ditetapkan SEBELUM segel dibuka (README "Hasil Evaluasi"; rancangan 6.1/6.2
dan 7.7): positif "memadai" bila batas bawah Wilson 95% >= 60%; kecocokan palsu "gugur" bila batas bawah
> 10%, "lulus" bila batas atas <= 20%. `tests/test_evaluation_facts.py` memastikan angkanya sama dengan README.
"""

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from evaluation.metrics import wilson_interval
from paths import PROJECT_ROOT

RESULTS_PATH = PROJECT_ROOT / "testset" / "eksternal_hasil_per_butir.json"
FROZEN_PATH = PROJECT_ROOT / "testset" / "eksternal_butir.json"
NOT_IN_ARCHIVE = "TIDAK ADA"  # label final butir negatif: klaimnya tidak ada di basis data

POSITIVE_ADEQUATE_LOWER = 0.60
FALSE_MATCH_FAIL_LOWER = 0.10
FALSE_MATCH_PASS_UPPER = 0.20


@dataclass(frozen=True)
class Proportion:
    k: int
    n: int

    @property
    def rate(self) -> float:
        return self.k / self.n

    @property
    def wilson(self) -> tuple[float, float]:
        return wilson_interval(self.k, self.n)


@dataclass(frozen=True)
class ExternalEvaluation:
    total_items: int
    found_correctly: Proportion  # butir positif: artikel yang benar ditemukan
    false_matches: Proportion  # butir negatif: keliru dicocokkan dengan artikel lain
    index_articles: int  # ukuran indeks saat evaluasi

    @property
    def positive_category(self) -> str:
        return "memadai" if self.found_correctly.wilson[0] >= POSITIVE_ADEQUATE_LOWER else "belum memadai"

    @property
    def false_match_category(self) -> str:
        low, high = self.false_matches.wilson
        if low > FALSE_MATCH_FAIL_LOWER:
            return "belum lulus"
        return "lulus" if high <= FALSE_MATCH_PASS_UPPER else "tidak konklusif"


def compute_external(results: list[dict], index_articles: int) -> ExternalEvaluation:
    """Hitung metrik utama dari baris per butir (fungsi murni, mudah diuji)."""
    positives = [r for r in results if r["label_final"] != NOT_IN_ARCHIVE]
    negatives = [r for r in results if r["label_final"] == NOT_IN_ARCHIVE]
    correct = sum(1 for r in positives
                  if r["keputusan_modus"] == "ditemukan" and r["article_id_modus"] == r["label_final"])
    false_match = sum(1 for r in negatives if r["keputusan_modus"] == "ditemukan")
    return ExternalEvaluation(len(results), Proportion(correct, len(positives)),
                              Proportion(false_match, len(negatives)), index_articles)


@cache
def external_evaluation(results_path: Path = RESULTS_PATH, frozen_path: Path = FROZEN_PATH) -> ExternalEvaluation:
    rows = json.loads(results_path.read_text(encoding="utf-8"))["butir"]
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))["indeks_beku"]
    return compute_external(rows, int(frozen["jumlah_artikel"]))
