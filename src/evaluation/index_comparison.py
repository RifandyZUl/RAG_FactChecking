"""
Bandingkan kandidat retrieval set uji v1 pada dua indeks (mis. arsip Versi 1 vs produksi) -- hanya
retrieval, tanpa panggilan LLM/API. PENGAMATAN, bukan penilaian mutu: pada indeks yang lebih besar,
label negatif set uji v1 tidak otomatis berlaku (lihat v1.meta.json, keterikatan_basis_data_150).

Per butir: top-3 artikel (agregasi maksimum, skor kosinus eksak) di tiap indeks, peringkat artikel
sasaran, dan apakah artikel asal butir (url_asal TurnBackHoax) kini ada di indeks pembanding. Ringkasan:
sebaran skor top-1 per tipe butir, dan butir negatif yang punya kandidat top-3 di atas ambang.

Arsip JANGAN dibuka langsung (ChromaDB menulis ulang berkas saat dibuka): salin byte `archive/v1/`
lebih dulu dan beri jalur salinannya.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m evaluation.index_comparison --baseline SALINAN_ARSIP --out-json X.json
"""

import argparse
import json
import re
import statistics
from pathlib import Path
from typing import Any

from evaluation.retrieval_ablation import (
    ChunkMatrix,
    article_rank,
    load_items,
    rank_articles,
)
from paths import DATA_DIR, PROJECT_ROOT

# Positif terendah set PENGEMBANGAN pada indeks 150 artikel (CLAUDE.md, "Skor kemiripan berdaya pisah rendah").
DEFAULT_THRESHOLD = 0.5739
NEGATIVE_TYPES = ("negatif_sulit", "negatif_mudah")
_TBH_ID = re.compile(r"turnbackhoax\.id/articles/(\d+)-")


def distribution(values: list[float]) -> dict[str, float]:
    return {"n": len(values), "min": round(min(values), 4), "median": round(statistics.median(values), 4),
            "rerata": round(statistics.mean(values), 4), "maks": round(max(values), 4)}


def compare(items: list[dict[str, Any]], vectors: Any, matrices: dict[str, ChunkMatrix],
            article_ids: dict[str, set[str]], threshold: float) -> dict[str, Any]:
    """Susun perbandingan per butir dan ringkasannya untuk dua indeks bernama 'dasar' dan 'pembanding'."""
    rows = []
    for it, v in zip(items, vectors):
        m = _TBH_ID.search(it.get("url_asal") or "")
        row: dict[str, Any] = {"id": it["id"], "tipe": it["tipe"], "sasaran": it["expected_retrieval_article"],
                               "artikel_asal_tbh": m.group(1) if m else None}
        for name, matrix in matrices.items():
            ranking = rank_articles(matrix.scores(v))
            top3 = [(a, round(s, 4)) for a, s in ranking[:3]]
            row[name] = {
                "top3": top3,
                "skor_top1": round(ranking[0][1], 4),
                "peringkat_sasaran": article_rank(ranking, it["expected_retrieval_article"])
                if it["expected_retrieval_article"] else None,
                "artikel_asal_ada": (row["artikel_asal_tbh"] in article_ids[name]) if m else None,
                "top3_di_atas_ambang": [[a, s, a in article_ids["dasar"]] for a, s in top3 if s > threshold],
            }
        rows.append(row)

    summary: dict[str, Any] = {}
    for tipe in sorted({r["tipe"] for r in rows}):
        group = [r for r in rows if r["tipe"] == tipe]
        base = [r["dasar"]["skor_top1"] for r in group]
        other = [r["pembanding"]["skor_top1"] for r in group]
        diff = [o - b for b, o in zip(base, other)]
        summary[tipe] = {
            "skor_top1_dasar": distribution(base),
            "skor_top1_pembanding": distribution(other),
            "selisih": distribution(diff),
            "naik": sum(d > 1e-9 for d in diff),
            "turun": sum(d < -1e-9 for d in diff),
            "artikel_top1_berganti": [r["id"] for r in group if r["dasar"]["top3"][0][0] != r["pembanding"]["top3"][0][0]],
        }
    negatives = [r for r in rows if r["tipe"] in NEGATIVE_TYPES]
    return {
        "ambang": threshold,
        "negatif_dengan_kandidat_di_atas_ambang": {
            name: [r["id"] for r in negatives if r[name]["top3_di_atas_ambang"]] for name in matrices},
        "negatif_artikel_asal_kini_ada_di_pembanding": [
            r["id"] for r in negatives if r["pembanding"]["artikel_asal_ada"]],
        "sebaran_per_tipe": summary,
        "butir": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", type=Path, required=True, help="direktori indeks dasar (salinan arsip v1)")
    ap.add_argument("--compare", type=Path, default=DATA_DIR, help="direktori indeks pembanding (bawaan data/)")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--out-json", type=Path, required=True)
    args = ap.parse_args()

    if args.baseline.resolve().is_relative_to((PROJECT_ROOT / "archive").resolve()):
        raise SystemExit("jangan buka arsip langsung; salin byte archive/v1/ lalu beri jalur salinannya")
    from ingest import MODEL_NAME, get_collection, load_model

    items = load_items()
    model = load_model()
    vectors = model.encode([i["klaim"] for i in items], normalize_embeddings=True, batch_size=8)
    dirs = {"dasar": args.baseline, "pembanding": args.compare}
    matrices = {n: ChunkMatrix(get_collection(d / "chroma")) for n, d in dirs.items()}
    article_ids = {n: {a["article_id"] for a in json.loads((d / "articles.json").read_text(encoding="utf-8"))}
                   for n, d in dirs.items()}
    res = compare(items, vectors, matrices, article_ids, args.threshold)
    res["meta"] = {"model_embedding": MODEL_NAME, "jumlah_chunk": {n: len(m.meta) for n, m in matrices.items()},
                   "jumlah_artikel": {n: len(a) for n, a in article_ids.items()},
                   "catatan": "Pengamatan retrieval saja; tanpa LLM. Top-3 di atas ambang: [artikel, skor, ada_di_dasar]."}
    args.out_json.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "butir"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
