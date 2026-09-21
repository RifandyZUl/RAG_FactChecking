"""
Metrik evaluasi generator: interval Wilson dan jenis kesalahan yang dipisah.

Akurasi total menyembunyikan pergeseran jenis kesalahan (prompt yang lebih ketat cenderung menggeser kesalahan
dari kecocokan palsu ke penolakan palsu), sehingga laporan selalu memisahkan:

- kecocokan_palsu : expected_verdict = belum_ditemukan, dijawab ditemukan (klaim yang tak ada dianggap ada)
- penolakan_palsu : expected_verdict = ditemukan, dijawab belum ditemukan (klaim yang ada dilewatkan)
- artikel_salah   : expected_verdict = ditemukan (artikel A), dijawab ditemukan artikel B (bukan A)

masing-masing dengan interval Wilson 95%, untuk semua butir, butir non-batas, dan butir batas.
"""

import math
from collections.abc import Iterable, Mapping
from typing import Any

from evaluation.devset import ANSWER_TO_EXPECTED, VERDICT_BELUM, VERDICT_DITEMUKAN

ERROR_TYPES = ("kecocokan_palsu", "penolakan_palsu", "artikel_salah")


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Interval kepercayaan Wilson (95% bila z=1,96) untuk proporsi k dari n; (0, 1) bila n = 0."""
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - margin) / denom), min(1.0, (centre + margin) / denom)


def classify_error(expected_verdict: str, expected_article: str | None, verdict: str,
                   article_id: str | None) -> str | None:
    """
    Jenis kesalahan sebuah jawaban, atau None bila benar. `verdict` adalah nilai generator
    ("ditemukan" | "tidak_ditemukan" | "gagal"); "gagal" dikembalikan sebagai "gagal" (bukan kesalahan
    keputusan, tidak dihitung).
    """
    if verdict not in ANSWER_TO_EXPECTED:
        return "gagal"
    got = ANSWER_TO_EXPECTED[verdict]
    if expected_verdict == VERDICT_BELUM:
        return "kecocokan_palsu" if got == VERDICT_DITEMUKAN else None
    if got == VERDICT_BELUM:
        return "penolakan_palsu"
    return None if article_id == expected_article else "artikel_salah"


def error_report(records: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """
    Rekap kesalahan per himpunan ("semua", "non_batas", "batas"). Setiap catatan memuat `expected_verdict`,
    `expected_retrieval_article`, `verdict`, `article_id`, dan `batas`. Butir berstatus "gagal" dilaporkan
    terpisah dan tidak masuk penyebut.
    """
    subsets: dict[str, list[Mapping[str, Any]]] = {"semua": [], "non_batas": [], "batas": []}
    for r in records:
        subsets["semua"].append(r)
        subsets["batas" if r.get("batas") else "non_batas"].append(r)

    out: dict[str, dict[str, Any]] = {}
    for name, rows in subsets.items():
        n_belum = n_ditemukan = gagal = 0
        counts = dict.fromkeys(ERROR_TYPES, 0)
        for r in rows:
            err = classify_error(r["expected_verdict"], r["expected_retrieval_article"], r["verdict"], r["article_id"])
            if err == "gagal":
                gagal += 1
                continue
            if r["expected_verdict"] == VERDICT_BELUM:
                n_belum += 1
            else:
                n_ditemukan += 1
            if err:
                counts[err] += 1
        denominators = {"kecocokan_palsu": n_belum, "penolakan_palsu": n_ditemukan, "artikel_salah": n_ditemukan}
        out[name] = {
            "n_butir": len(rows), "n_gagal": gagal,
            "n_expected_belum_ditemukan": n_belum, "n_expected_ditemukan": n_ditemukan,
            "kesalahan": {t: {"k": counts[t], "n": denominators[t], "wilson95": wilson_interval(counts[t], denominators[t])}
                          for t in ERROR_TYPES},
            "benar": (n_belum + n_ditemukan) - sum(counts.values()),
        }
    return out


def format_error_report(report: Mapping[str, Mapping[str, Any]]) -> str:
    lines = []
    labels = {"kecocokan_palsu": "kecocokan palsu (negatif dijawab ditemukan)",
              "penolakan_palsu": "penolakan palsu (positif dijawab belum ditemukan)",
              "artikel_salah": "artikel salah (positif dijawab artikel lain)"}
    for name in ("non_batas", "batas", "semua"):
        r = report[name]
        lines.append(f"[{name}] butir={r['n_butir']} gagal={r['n_gagal']} benar={r['benar']}")
        for t in ERROR_TYPES:
            e = r["kesalahan"][t]
            lo, hi = e["wilson95"]
            lines.append(f"    {labels[t]:<52} {e['k']}/{e['n']}  Wilson95 [{lo:.3f}; {hi:.3f}]")
    return "\n".join(lines)
