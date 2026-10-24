"""
Sesi buta gabungan evaluasi eksternal (docs/rancangan_evaluasi_eksternal.md bagian 7): pemilihan butir uji ulang.

Pemilihan dikunci dan di-commit SEBELUM panggilan LLM pertama evaluasi, dan hanya bergantung pada benih dan
daftar pengecualian -- tidak pada hasil evaluasi, label, atau isi butir. Berkas sesi buta sendiri (30 butir uji
ulang dicampur 7 butir audit, tanpa penanda) dibuat terpisah, 20 Oktober 2026 (semula paling cepat 27 Oktober;
penyimpangan 2026-10-19, docs/rancangan_evaluasi_eksternal.md 7.2).

Pemakaian (dari root proyek):
  python -m labeling.sessions.blind_session --select    # menolak menimpa pilihan yang sudah ada
"""

import argparse
import json
import random
from typing import Any

from labeling.gap.gap_result import DOUBTFUL_ACCEPTED, DOUBTFUL_REJECTED
from paths import PROJECT_ROOT

SEED = 20261027
ROUND_SIZES = {1: 50, 2: 49}
PICK = {2: 20, 1: 10}  # putaran 2: konsistensi (aturan sama); putaran 1: efek pergantian aturan (dilabel ulang A/B)
DISCUSSED_WITH_AI = tuple(range(1, 6))  # butir 1-5 putaran 1 (rancangan_v2.md 11.5)
INCONSISTENT = tuple(sorted(DOUBTFUL_ACCEPTED + DOUBTFUL_REJECTED))  # 15 butir putaran 1 (11.5)
AUDIT = (("P1", 10), ("P1", 20), ("P1", 29), ("P1", 30), ("P1", 38), ("P1", 45), ("P2", 2))  # 7.1, dipilih tidak acak
SELECTION_PATH = PROJECT_ROOT / "testset" / "eksternal_sesi_buta_pilihan.json"


def pools() -> dict[int, list[int]]:
    """Butir yang boleh terpilih acak per putaran, urut nomor (urutan tetap agar benih bermakna)."""
    audit = {(int(p[1]), n) for p, n in AUDIT}
    excluded = {1: set(DISCUSSED_WITH_AI) | set(INCONSISTENT)}
    return {r: [n for n in range(1, size + 1) if n not in excluded.get(r, set()) and (r, n) not in audit]
            for r, size in ROUND_SIZES.items()}


def select(seed: int = SEED) -> dict[str, Any]:
    """Satu generator acak berbenih: putaran 2 diambil lebih dulu, lalu putaran 1 (urutan ini bagian dari aturan)."""
    rng, pool = random.Random(seed), pools()
    chosen = {r: sorted(rng.sample(pool[r], PICK[r])) for r in (2, 1)}
    return {
        "benih": seed,
        "metode": "random.Random(benih).sample(kolam putaran 2, 20), lalu .sample(kolam putaran 1, 10); kolam urut nomor",
        "dikecualikan": {"putaran_1_butir_1_5_dibahas_bersama_AI": list(DISCUSSED_WITH_AI),
                         "putaran_1_15_butir_tidak_konsisten": list(INCONSISTENT),
                         "butir_audit_jejak_identik": [f"{p}-{n}" for p, n in AUDIT]},
        "kolam": {f"putaran_{r}": len(pool[r]) for r in (1, 2)},
        "uji_ulang": {f"putaran_{r}": chosen[r] for r in (2, 1)},
        "audit_dicampur_tanpa_penanda": [f"{p}-{n}" for p, n in AUDIT],
        "catatan": "Pemilihan tidak bergantung pada hasil evaluasi; berkas sesi buta dibuat paling cepat 2026-10-27.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--select", action="store_true", required=True, help="pilih butir uji ulang dan simpan")
    ap.parse_args()
    if SELECTION_PATH.exists():
        raise SystemExit(f"{SELECTION_PATH.name} sudah ada: pilihan tidak ditimpa")
    out = select()
    SELECTION_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
