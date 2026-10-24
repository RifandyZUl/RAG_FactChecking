"""
Pembuktian embedding lintas lingkungan (Tahap 2): apakah bge-m3 di lingkungan ini menghasilkan vektor yang
sama dengan yang tersimpan di indeks, dan apakah retrieval memberi top-3 yang sama. Tanpa LLM/API.

Dijalankan di venv Windows (pembanding) dan di dalam container Linux, masing-masing pada SALINAN indeks
produksi (bukan indeks produksi itu sendiri):
  1. 200 chunk acak, `random.Random(20261022).sample(sorted(ids), 200)`, di-embed ulang dengan
     `ingest.load_model()` (revisi dipatok, batch 8, normalisasi sama dengan ingest), dibandingkan dengan
     vektor tersimpan: kosinus minimum, rata-rata, persentil-1.
  2. 64 kueri tetap `evaluation.retriever_exactness` (54 butir set uji v1 + 10 kueri set pengembangan):
     retriever HNSW vs pencarian eksak DI lingkungan ini, ditambah top-3 eksak (id + skor) per kueri yang
     disimpan untuk dibandingkan antar-lingkungan (`--compare`).

Ambang DITETAPKAN SEBELUM MENGUKUR (pemilik proyek, 2026-10-24; docs/audit/audit_tahap0.md):
  SAMA     : kosinus minimum >= 0,99999, rata-rata >= 0,999999, dan top-3 identik 64/64 (HNSW = eksak di
             lingkungan ini dan, dengan --compare, sama dengan lingkungan pembanding).
  BERHENTI : kosinus minimum < 0,999, atau ada top-3 yang berbeda.
  di antara: laporkan dan tunggu keputusan pemilik proyek.

Pemakaian (dari root proyek):
  python -m evaluation.embedding_proof --chroma-dir SALINAN --out-json X.json [--compare PEMBANDING.json]
Kode keluar: 0 SAMA | 2 di antara (tunggu keputusan) | 1 BERHENTI.
"""

import argparse
import json
import platform
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np

from hf_env import prepare_hf_env

SEED = 20261022
SAMPLE_SIZE = 200
BATCH_SIZE = 8  # sama dengan ingest.BATCH_SIZE
TOP_K = 3
MIN_COS_SAME, MEAN_COS_SAME = 0.99999, 0.999999
MIN_COS_STOP = 0.999
VERDICT_SAME, VERDICT_BETWEEN, VERDICT_STOP = "SAMA", "DI ANTARA (tunggu keputusan)", "BERHENTI"
EXIT_CODES = {VERDICT_SAME: 0, VERDICT_BETWEEN: 2, VERDICT_STOP: 1}


def sample_ids(ids: list[str], seed: int = SEED, n: int = SAMPLE_SIZE) -> list[str]:
    return random.Random(seed).sample(sorted(ids), n)


def cosine_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Kosinus baris demi baris (float64, tanpa mengandalkan vektor sudah ternormalisasi)."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    return (a * b).sum(axis=1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))


def cosine_stats(cos: np.ndarray) -> dict[str, float]:
    return {"minimum": float(cos.min()), "rata_rata": float(cos.mean()), "persentil_1": float(np.percentile(cos, 1)),
            "maksimum": float(cos.max())}


def compare_top3(own: dict[str, list[list]], other: dict[str, list[list]]) -> dict[str, Any]:
    """Top-3 eksak per kueri antar-lingkungan: kueri dengan id berbeda dan selisih skor terbesar."""
    if set(own) != set(other):
        raise ValueError("himpunan kueri berbeda antar-lingkungan")
    differing = [q for q in own if [a for a, _ in own[q]] != [a for a, _ in other[q]]]
    deltas = [abs(s1 - s2) for q in own if q not in differing
              for (_, s1), (_, s2) in zip(own[q], other[q])]
    return {"kueri": len(own), "top3_berbeda": differing, "maks_selisih_skor": max(deltas) if deltas else None}


def verdict(stats: dict[str, float], hnsw_differs: int, cross_differs: int | None) -> str:
    if stats["minimum"] < MIN_COS_STOP or hnsw_differs or cross_differs:
        return VERDICT_STOP
    if stats["minimum"] >= MIN_COS_SAME and stats["rata_rata"] >= MEAN_COS_SAME:
        return VERDICT_SAME
    return VERDICT_BETWEEN


def environment() -> dict[str, str]:
    import sentence_transformers
    import torch
    import transformers

    return {"python": platform.python_version(), "sistem": platform.platform(), "torch": torch.__version__,
            "transformers": transformers.__version__, "sentence_transformers": sentence_transformers.__version__,
            "numpy": np.__version__}


def main() -> int:
    prepare_hf_env()
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--chroma-dir", type=Path, required=True, help="SALINAN indeks (jangan indeks produksi)")
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--compare", type=Path, default=None, help="hasil lingkungan pembanding (JSON alat ini)")
    args = ap.parse_args()

    from evaluation.retriever_exactness import (
        exact_ranking,
        exact_top_articles,
        load_queries,
    )
    from evaluation.retriever_exactness import run as run_exactness
    from ingest import MODEL_REVISION, get_collection, load_model

    chroma_dir = args.chroma_dir.resolve()
    if not (chroma_dir / "chroma.sqlite3").is_file():
        raise SystemExit(f"{chroma_dir} tidak berisi indeks ChromaDB")
    collection = get_collection(chroma_dir)
    stored = collection.get(include=["embeddings", "documents", "metadatas"])
    ids, docs, metas = stored["ids"], stored["documents"], stored["metadatas"]
    matrix = np.asarray(stored["embeddings"], dtype=np.float32)
    pos = {cid: i for i, cid in enumerate(ids)}
    chosen = sample_ids(ids)

    model = load_model()
    # Terpanjang dulu, seperti ingest (pengisian batch mirip); urutan hasil dikembalikan sesudahnya.
    order = sorted(range(len(chosen)), key=lambda i: metas[pos[chosen[i]]].get("n_tokens", 0), reverse=True)
    encoded = model.encode([docs[pos[chosen[i]]] for i in order], batch_size=BATCH_SIZE, normalize_embeddings=True,
                           show_progress_bar=False)
    fresh = np.empty_like(encoded)
    fresh[order] = encoded
    cos = cosine_rows(fresh, matrix[[pos[c] for c in chosen]])
    stats = cosine_stats(cos)

    queries = load_queries()
    names = [n for n, _ in queries]
    qvecs = np.asarray(model.encode([q for _, q in queries], normalize_embeddings=True, batch_size=BATCH_SIZE),
                       dtype=np.float32)
    del model
    exactness = run_exactness(collection, names, qvecs)
    top3 = {}
    for name, vec in zip(names, qvecs):
        o, sims = exact_ranking(vec, matrix)
        top3[name] = [[a, s] for a, s in exact_top_articles(o, sims, metas, TOP_K)]
    hnsw_differs = exactness["ringkasan"]["top3_artikel_berbeda"]

    report: dict[str, Any] = {
        "lingkungan": environment(), "revisi_model": MODEL_REVISION, "indeks": str(chroma_dir),
        "jumlah_chunk": len(ids), "benih": SEED, "sampel": SAMPLE_SIZE,
        "ambang": {"SAMA": f"min >= {MIN_COS_SAME}, rata-rata >= {MEAN_COS_SAME}, top-3 identik 64/64",
                   "BERHENTI": f"min < {MIN_COS_STOP} atau ada top-3 berbeda"},
        "kosinus_200_chunk": stats,
        "chunk_kosinus_terendah": [[chosen[i], float(cos[i])] for i in np.argsort(cos)[:5]],
        "retriever_exactness": {"top3_hnsw_vs_eksak_berbeda": hnsw_differs,
                                "chunk_terlewat": exactness["ringkasan"]["chunk_terlewat"],
                                "parameter_hnsw": exactness["parameter_hnsw"]},
        "top3_eksak_per_kueri": top3,
        "id_sampel": chosen,
    }
    cross = None
    if args.compare:
        other = json.loads(args.compare.read_text(encoding="utf-8"))
        if other["id_sampel"] != chosen:
            raise SystemExit("sampel id berbeda dari pembanding: salinan indeks tidak sama")
        cross = compare_top3(top3, other["top3_eksak_per_kueri"])
        report["banding_dengan"] = {"berkas": str(args.compare), "lingkungan": other["lingkungan"], **cross}
    result = verdict(stats, len(hnsw_differs), len(cross["top3_berbeda"]) if cross else None)
    report["putusan"] = result
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    env = report["lingkungan"]
    print(f"lingkungan: Python {env['python']} | {env['sistem']} | torch {env['torch']}")
    print(f"kosinus 200 chunk: min {stats['minimum']:.9f} | rata-rata {stats['rata_rata']:.9f} | "
          f"p1 {stats['persentil_1']:.9f}")
    print(f"top-3 HNSW vs eksak berbeda: {len(hnsw_differs)}/{len(names)} {hnsw_differs}")
    if cross:
        print(f"top-3 eksak vs pembanding berbeda: {len(cross['top3_berbeda'])}/{cross['kueri']} "
              f"{cross['top3_berbeda']} | maks |selisih skor| {cross['maks_selisih_skor']}")
    print(f"PUTUSAN: {result}")
    return EXIT_CODES[result]


if __name__ == "__main__":
    sys.exit(main())
