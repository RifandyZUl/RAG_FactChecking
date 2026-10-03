"""
Bandingkan pencarian retriever (HNSW ChromaDB, perkiraan) dengan pencarian EKSAK (brute-force kosinus
atas seluruh vektor tersimpan) pada set kueri tetap: 54 butir set uji v1 + 10 kueri set pengembangan.
Hanya retrieval; tanpa LLM/API dan tanpa jaringan.

Mengapa ada: HNSW adalah pencarian perkiraan. Pada indeks 1.532 artikel dengan `ef_search` bawaan (100)
retriever produksi tidak lagi selalu sama dengan pencarian eksak (v1-048: artikel peringkat 2 tidak
terambil), dan selisihnya membesar bersama ukuran indeks (testset/v1_temuan_untuk_v2.md bagian 10).
`evaluation.index_check` tidak menangkap ini: ia memeriksa ISI indeks, bukan mutu pencariannya. Jalankan
alat ini setiap kali indeks bertambah.

Yang dilaporkan: parameter pencarian yang berlaku, kueri yang chunk teratasnya tidak dikembalikan
retriever, kueri yang top-3 ARTIKEL-nya berbeda (beserta artikel yang masuk/keluar dan peringkatnya),
dan latensi kueri. Kode keluar 1 bila ada top-3 artikel yang berbeda, 0 bila tidak.

`ef_search` hanya berlaku bagi proses yang membuka indeks SETELAH nilainya diubah (segmen HNSW di-cache
per proses), jadi ukur dalam proses baru. Arsip JANGAN dibuka langsung: salin byte-nya lebih dulu dan
beri jalur salinannya lewat --chroma-dir.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m evaluation.retriever_exactness [--chroma-dir DIR] [--out-json X.json]
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from retriever import CHUNK_FETCH, aggregate_by_article

TOP_ARTICLES = 3


def exact_ranking(query_vec: np.ndarray, matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(urutan indeks chunk dari skor tertinggi, skor kosinus) untuk satu kueri; vektor sudah ternormalisasi."""
    sims = matrix @ query_vec
    return np.argsort(-sims, kind="stable"), sims


def exact_top_articles(order: np.ndarray, sims: np.ndarray, metadatas: list[dict], k: int) -> list[tuple[str, float]]:
    """k artikel teratas menurut skor chunk terbaiknya (agregasi maksimum, sama dengan retriever)."""
    best: dict[str, float] = {}
    for j in order:
        aid = metadatas[j]["article_id"]
        if aid not in best:
            best[aid] = round(float(sims[j]), 4)
            if len(best) == k:
                break
    return list(best.items())


def compare_query(query_vec: np.ndarray, ids: list[str], metadatas: list[dict], matrix: np.ndarray,
                  returned_ids: list[str], returned_metas: list[dict], returned_distances: list[float],
                  n_results: int = CHUNK_FETCH) -> dict[str, Any]:
    """Bandingkan satu hasil retriever (chunk yang dikembalikan) dengan pencarian eksak."""
    order, sims = exact_ranking(query_vec, matrix)
    got = set(returned_ids)
    missed = [{"chunk": ids[j], "peringkat_eksak": rank, "skor": round(float(sims[j]), 4)}
              for rank, j in enumerate(order[:n_results], 1) if ids[j] not in got]
    exact = exact_top_articles(order, sims, metadatas, TOP_ARTICLES + 2)
    hits = aggregate_by_article(returned_metas, returned_distances)[:TOP_ARTICLES + 2]
    approx = [(h.article_id, round(h.score, 4)) for h in hits]
    exact3, approx3 = [a for a, _ in exact[:TOP_ARTICLES]], [a for a, _ in approx[:TOP_ARTICLES]]
    rank_in_approx = {a: r for r, (a, _) in enumerate(approx, 1)}
    rank_in_exact = {a: r for r, (a, _) in enumerate(exact, 1)}
    return {
        "chunk_terlewat": missed,
        "top3_sama": exact3 == approx3,
        "eksak_top": exact,
        "retriever_top": approx,
        # artikel yang seharusnya di tiga besar tetapi tidak ada di tiga besar retriever, dan sebaliknya
        "keluar": [{"artikel": a, "peringkat_eksak": rank_in_exact[a], "peringkat_retriever": rank_in_approx.get(a)}
                   for a in exact3 if a not in approx3],
        "masuk": [{"artikel": a, "peringkat_retriever": rank_in_approx[a], "peringkat_eksak": rank_in_exact.get(a)}
                  for a in approx3 if a not in exact3],
    }


def summarize(names: list[str], results: list[dict[str, Any]], n_results: int = CHUNK_FETCH) -> dict[str, Any]:
    missed_total = sum(len(r["chunk_terlewat"]) for r in results)
    return {
        "kueri": len(results),
        "n_results": n_results,
        "kueri_dengan_chunk_terlewat": [n for n, r in zip(names, results) if r["chunk_terlewat"]],
        "chunk_terlewat": missed_total,
        "chunk_diperiksa": len(results) * n_results,
        "top3_artikel_berbeda": [n for n, r in zip(names, results) if not r["top3_sama"]],
    }


def search_params(collection: Any) -> dict[str, Any]:
    """Parameter HNSW yang tersimpan pada koleksi (ef_search, ef_construction, max_neighbors, ...)."""
    cfg = getattr(collection, "configuration_json", None) or {}
    return dict(cfg.get("hnsw") or {})


def load_queries() -> list[tuple[str, str]]:
    """(nama, teks) kueri tetap: butir set uji v1 lalu kueri set pengembangan."""
    from evaluation.devset import DEV_QUERIES
    from paths import PROJECT_ROOT

    lines = (PROJECT_ROOT / "testset" / "v1.jsonl").read_text(encoding="utf-8").splitlines()
    items = [json.loads(ln) for ln in lines if ln.strip()]
    return [(it["id"], it["klaim"]) for it in items] + [(f"dev-{i:02d}", q.claim) for i, q in enumerate(DEV_QUERIES, 1)]


def run(collection: Any, names: list[str], vectors: np.ndarray, repeats: int = 3,
        n_results: int = CHUNK_FETCH) -> dict[str, Any]:
    """Jalankan perbandingan dan ukur latensi kueri (median per kueri atas `repeats` ulangan)."""
    stored = collection.get(include=["embeddings", "metadatas"])
    ids, metadatas = stored["ids"], stored["metadatas"]
    matrix = np.asarray(stored["embeddings"], dtype=np.float32)
    n = min(n_results, len(ids))
    results, latencies = [], []
    for vec in vectors:
        timings = []
        res: dict[str, Any] = {}
        for _ in range(repeats):
            t0 = time.perf_counter()
            res = collection.query(query_embeddings=[vec.tolist()], n_results=n, include=["metadatas", "distances"])
            timings.append((time.perf_counter() - t0) * 1000)
        latencies.append(statistics.median(timings))
        results.append(compare_query(vec, ids, metadatas, matrix, res["ids"][0], res["metadatas"][0],
                                     res["distances"][0], n))
    latencies.sort()
    return {
        "jumlah_chunk": len(ids),
        "parameter_hnsw": search_params(collection),
        "ringkasan": summarize(names, results, n),
        "latensi_kueri_ms": {"median": round(statistics.median(latencies), 2),
                             "p95": round(latencies[min(len(latencies) - 1, int(0.95 * len(latencies)))], 2),
                             "maks": round(latencies[-1], 2), "ulangan": repeats,
                             "catatan": "hanya collection.query (tanpa embedding kueri dan tanpa LLM)"},
        "rincian_berbeda": {name: r for name, r in zip(names, results) if not r["top3_sama"]},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--chroma-dir", type=Path, default=None, help="folder ChromaDB (bawaan: indeks aktif)")
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--vectors-cache", type=Path, default=None,
                    help="berkas .npy embedding kueri; dibuat bila belum ada (agar model tidak dimuat ulang)")
    args = ap.parse_args()

    from ingest import CHROMA_DIR, get_collection, load_model

    queries = load_queries()
    names = [n for n, _ in queries]
    if args.vectors_cache and args.vectors_cache.exists():
        vectors = np.load(args.vectors_cache)
        if len(vectors) != len(queries):
            raise SystemExit(f"{args.vectors_cache}: {len(vectors)} vektor, tetapi ada {len(queries)} kueri")
    else:
        model = load_model()
        vectors = np.asarray(model.encode([q for _, q in queries], normalize_embeddings=True, batch_size=8),
                             dtype=np.float32)
        del model
        if args.vectors_cache:
            np.save(args.vectors_cache, vectors)

    chroma_dir = args.chroma_dir.resolve() if args.chroma_dir else CHROMA_DIR
    if not (chroma_dir / "chroma.sqlite3").is_file():
        raise SystemExit(f"{chroma_dir} tidak berisi indeks ChromaDB")
    report = run(get_collection(chroma_dir), names, vectors)
    report["indeks"] = str(chroma_dir)
    s, lat = report["ringkasan"], report["latensi_kueri_ms"]
    print(f"indeks: {chroma_dir} | {report['jumlah_chunk']} chunk | parameter HNSW: {report['parameter_hnsw']}")
    print(f"kueri dengan chunk terlewat: {len(s['kueri_dengan_chunk_terlewat'])}/{s['kueri']} | "
          f"chunk terlewat: {s['chunk_terlewat']}/{s['chunk_diperiksa']} | "
          f"top-{TOP_ARTICLES} artikel berbeda: {len(s['top3_artikel_berbeda'])} {s['top3_artikel_berbeda']}")
    print(f"latensi kueri (ms): median {lat['median']} | p95 {lat['p95']} | maks {lat['maks']}")
    for name, r in report["rincian_berbeda"].items():
        print(f"  {name}: eksak {r['eksak_top'][:TOP_ARTICLES]} | retriever {r['retriever_top'][:TOP_ARTICLES]}")
        print(f"     keluar: {r['keluar']} | masuk: {r['masuk']}")
    if args.out_json:
        args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if s["top3_artikel_berbeda"]:
        print("RETRIEVER TIDAK SAMA DENGAN PENCARIAN EKSAK pada kueri di atas")
        return 1
    print(f"RETRIEVER = PENCARIAN EKSAK pada top-{TOP_ARTICLES} artikel untuk semua kueri")
    return 0


if __name__ == "__main__":
    sys.exit(main())
