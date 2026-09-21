"""
Pilih 20 artikel TARGET untuk butir positif set uji v1 (sampel acak berstrata, benih tetap).

Aturan (pra-registrasi di testset/v1.meta.json): enam artikel dikecualikan (target 5 kueri positif pengembangan
dan artikel inti H1); alokasi per sel (kategori x label) mengikuti sebaran 150 artikel dengan PARODI
di-oversample (kedua artikel PARODI dipilih); minimal 2 target dari artikel dengan `references` kosong;
artikel "wajib" (mis. yang sudah punya cakupan pada situs cek fakta lain) dimasukkan lebih dulu ke selnya,
sisanya diacak dengan benih. Hasil: testset/targets_v1.json (hanya id; TIDAK memuat judul).

Pemakaian (dari root proyek): PYTHONPATH=src python -m candidates.targets
"""

import json
import random
from typing import Any

from paths import PROJECT_ROOT

SEED = 20260921
EXCLUDED = ("36730", "36737", "36729", "36738", "36731", "36214")
FORCED = ("36213", "36655", "36157", "36606")  # dimasukkan lebih dulu ke selnya (keputusan pemilik proyek)
CELLS: dict[tuple[str, str], int] = {
    ("Politik", "SALAH"): 6, ("Politik", "PARODI"): 2, ("Bantuan", "PENIPUAN"): 3, ("Lowongan", "PENIPUAN"): 3,
    ("Kesehatan", "SALAH"): 2, ("Bencana", "SALAH"): 2, ("Hadiah", "PENIPUAN"): 1, ("Bisnis", "PENIPUAN"): 1,
}
MIN_EMPTY_REFERENCES = 2


def select_targets(articles: list[dict[str, Any]], seed: int = SEED) -> dict[str, Any]:
    rng = random.Random(seed)
    pool = [a for a in articles if a["article_id"] not in EXCLUDED]
    by_id = {a["article_id"]: a for a in pool}
    chosen: dict[tuple[str, str], list[str]] = {}
    for cell, n in CELLS.items():
        members = sorted(a["article_id"] for a in pool if (a["category"], a["label"]) == cell)
        forced = [i for i in FORCED if i in members]
        rest = [i for i in members if i not in forced]
        rng.shuffle(rest)
        chosen[cell] = (forced + rest)[:n] if len(members) >= n else members
        assert len(chosen[cell]) == n, f"sel {cell} hanya punya {len(members)} artikel"

    def n_empty() -> int:
        return sum(1 for ids in chosen.values() for i in ids if not by_id[i]["references"])

    # jamin minimal 2 target tanpa references: tukar anggota non-wajib dengan artikel references-kosong di sel yang sama
    for cell in sorted(chosen):
        if n_empty() >= MIN_EMPTY_REFERENCES:
            break
        empties = sorted(a["article_id"] for a in pool if (a["category"], a["label"]) == cell and not a["references"]
                         and a["article_id"] not in chosen[cell])
        swappable = [i for i in chosen[cell] if i not in FORCED and by_id[i]["references"]]
        if empties and swappable:
            chosen[cell][chosen[cell].index(swappable[-1])] = empties[0]
    assert n_empty() >= MIN_EMPTY_REFERENCES, "tidak cukup target tanpa references"
    return {
        "seed": seed, "dikecualikan": list(EXCLUDED), "wajib": list(FORCED),
        "sel": {f"{cat}-{label}": ids for (cat, label), ids in chosen.items()},
        "target": [i for ids in chosen.values() for i in ids],
        "jumlah_tanpa_references": n_empty(),
    }


def main() -> int:
    from chunker import load_articles

    result = select_targets(load_articles())
    out = PROJECT_ROOT / "testset" / "targets_v1.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(result['target'])} target -> {out} | tanpa references: {result['jumlah_tanpa_references']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
