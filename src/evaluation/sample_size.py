"""
Perhitungan ukuran sampel untuk rancangan set uji Versi 2 (docs/rancangan_v2.md bagian 6.3).

Tanpa data, tanpa model, tanpa jaringan: hanya rumus. Menghasilkan angka yang dikutip di dokumen
rancangan agar dapat ditelusuri dan dihitung ulang:

  (a) interval Wilson 95% dan jumlah butir per kondisi agar interval dua proporsi tidak tumpang tindih;
  (b) McNemar eksak dua sisi untuk perbandingan berpasangan (dua versi pada butir yang sama), dan
      jumlah butir agar peluang mengamati cukup perbaikan mencapai 80%;
  (c) batas atas Wilson bila tidak ada kejadian (0 dari n), dan batas bawah bila semua benar.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m evaluation.sample_size [--out-json testset/v2_ukuran_sampel.json]
"""

import argparse
import json
import sys
from math import comb, sqrt
from pathlib import Path

Z95 = 1.959964
ALPHA = 0.05
POWER = 0.80
MIN_NET_IMPROVEMENTS = 6  # perbaikan searah terkecil yang memberi McNemar p < 0,05 tanpa kemunduran


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Interval Wilson untuk proporsi k/n."""
    if n <= 0:
        raise ValueError("n harus positif")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def n_for_non_overlap(p_low: float, p_high: float, limit: int = 20000) -> int | None:
    """
    Butir per kondisi terkecil agar interval Wilson 95% dua proporsi TERAMATI (p_low, p_high) tidak
    tumpang tindih. Kriteria konservatif (lebih ketat daripada uji selisih dua proporsi).
    """
    if not 0 <= p_low < p_high <= 1:
        raise ValueError("butuh 0 <= p_low < p_high <= 1")
    for n in range(5, limit):
        if wilson(round(p_high * n), n)[0] > wilson(round(p_low * n), n)[1]:
            return n
    return None


def mcnemar_exact_p(improved: int, worsened: int) -> float:
    """McNemar eksak dua sisi atas pasangan tak-serasi (butir yang berubah benar->salah atau sebaliknya)."""
    n = improved + worsened
    if n == 0:
        return 1.0
    k = min(improved, worsened)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def prob_at_least(k: int, n: int, rate: float) -> float:
    """P(X >= k) untuk X ~ Binomial(n, rate)."""
    return sum(comb(n, i) * rate ** i * (1 - rate) ** (n - i) for i in range(k, n + 1))


def n_for_paired_improvement(rate: float, min_improved: int = MIN_NET_IMPROVEMENTS, power: float = POWER,
                             limit: int = 5000) -> int | None:
    """
    Butir terkecil agar peluang mengamati >= `min_improved` perbaikan mencapai `power`, bila tiap butir
    membaik dengan peluang `rate` dan TIDAK ada kemunduran. Asumsi tanpa kemunduran membuat angka ini
    batas bawah: kemunduran apa pun menuntut lebih banyak butir.
    """
    for n in range(min_improved, limit):
        if prob_at_least(min_improved, n, rate) >= power:
            return n
    return None


def build_report() -> dict:
    """Seluruh angka yang dikutip di docs/rancangan_v2.md bagian 6.3."""
    report: dict = {
        "catatan": "Dihitung dari rumus saja (Wilson 95%, McNemar eksak dua sisi, binomial). Tidak ada data yang dibaca.",
        "wilson_acuan": {
            "48/50": [round(x, 3) for x in wilson(48, 50)],
            "batas_bawah_bila_semua_benar": {str(n): round(wilson(n, n)[0], 3) for n in (10, 15, 20, 25, 30, 40, 50, 60, 100, 150, 200)},
            "batas_atas_bila_nol_kejadian": {str(n): round(wilson(0, n)[1], 3) for n in (10, 15, 20, 25, 30, 40, 50, 60, 100, 150, 200)},
        },
        "interval_tidak_tumpang_tindih_butir_per_kondisi": {
            f"{lo:.2f} vs {hi:.2f}": n_for_non_overlap(lo, hi)
            for lo, hi in [(0.96, 0.99), (0.90, 0.96), (0.86, 0.95), (0.80, 0.95), (0.50, 0.80), (0.30, 0.80),
                           (0.10, 0.80), (0.10, 0.50), (0.00, 0.50)]
        },
        "mcnemar_eksak_p": {f"{b} membaik, {c} memburuk": round(mcnemar_exact_p(b, c), 4)
                            for b, c in [(4, 0), (5, 0), (6, 0), (7, 0), (8, 0), (6, 1), (8, 1), (9, 1), (8, 2), (11, 2)]},
        "berpasangan_butir_agar_peluang_80persen_mengamati_6_perbaikan": {
            f"{r:.2f}": n_for_paired_improvement(r) for r in (0.04, 0.06, 0.08, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90)
        },
    }
    # Butir pesan panjang: laju perbaikan sejati = (bagian butir yang benar-benar terkena pemotongan)
    # x (bagian yang dipulihkan Versi 2). Keduanya BELUM diketahui untuk pesan nyata.
    report["pesan_panjang_butir_positif_yang_dibutuhkan"] = {
        "penjelasan": "baris = bagian butir yang terkena pemotongan pada pesan nyata; kolom = bagian yang dipulihkan Versi 2; "
                      "isi = butir positif pesan panjang agar peluang 80% mengamati >= 6 perbaikan tanpa kemunduran",
        "tabel": {f"terkena {a:.0%}": {f"dipulihkan {b:.0%}": n_for_paired_improvement(a * b) for b in (0.5, 0.7, 0.9)}
                  for a in (0.2, 0.4, 0.6, 0.8, 1.0)},
    }
    return report


def format_report(r: dict) -> str:
    lines = ["UKURAN SAMPEL -- rancangan set uji Versi 2 (rumus saja; tidak ada data yang dibaca)", ""]
    lines.append(f"Wilson95 48/50 = {r['wilson_acuan']['48/50']}")
    lines.append("n : batas bawah bila semua benar | batas atas bila 0 kejadian")
    for n, lo in r["wilson_acuan"]["batas_bawah_bila_semua_benar"].items():
        lines.append(f"  {n:>4} : {lo:.3f} | {r['wilson_acuan']['batas_atas_bila_nol_kejadian'][n]:.3f}")
    lines += ["", "Butir per kondisi agar interval Wilson 95% dua proporsi tidak tumpang tindih:"]
    lines += [f"  {k}: {v}" for k, v in r["interval_tidak_tumpang_tindih_butir_per_kondisi"].items()]
    lines += ["", "McNemar eksak dua sisi:"]
    lines += [f"  {k}: p = {v}" for k, v in r["mcnemar_eksak_p"].items()]
    lines += ["", "Perbandingan berpasangan: butir agar peluang 80% mengamati >= 6 perbaikan (tanpa kemunduran):"]
    lines += [f"  laju perbaikan sejati {k}: {v}" for k, v in r["berpasangan_butir_agar_peluang_80persen_mengamati_6_perbaikan"].items()]
    lines += ["", "Butir positif pesan panjang yang dibutuhkan (terkena x dipulihkan):"]
    for row, cols in r["pesan_panjang_butir_positif_yang_dibutuhkan"]["tabel"].items():
        lines.append(f"  {row}: " + " | ".join(f"{c} -> {n}" for c, n in cols.items()))
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--out-report", type=Path, default=None)
    args = ap.parse_args()
    report = build_report()
    text = format_report(report)
    print(text, end="")
    if args.out_json:
        args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.out_report:
        args.out_report.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
