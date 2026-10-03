"""Uji alat pembanding retriever (HNSW) lawan pencarian eksak (evaluation.retriever_exactness); tanpa model."""

import numpy as np

from evaluation.retriever_exactness import (
    compare_query,
    exact_top_articles,
    run,
    search_params,
    summarize,
)

# 6 chunk, 4 artikel; vektor satuan 2D dengan sudut berbeda terhadap kueri (1, 0)
ANGLES = {"1_narasi": 5, "2_narasi": 10, "1_kesimpulan": 20, "3_narasi": 30, "4_narasi": 40, "3_kesimpulan": 60}
IDS = list(ANGLES)
METAS = [{"article_id": i.split("_")[0], "section": i.split("_")[1], "title": "T", "url": "u", "label": "SALAH",
          "references": "[]"} for i in IDS]
MATRIX = np.asarray([[np.cos(np.radians(a)), np.sin(np.radians(a))] for a in ANGLES.values()], dtype=np.float32)
QUERY = np.asarray([1.0, 0.0], dtype=np.float32)


def _returned(ids: list[str]) -> tuple[list[str], list[dict], list[float]]:
    idx = [IDS.index(i) for i in ids]
    return ids, [METAS[j] for j in idx], [1.0 - float(MATRIX[j] @ QUERY) for j in idx]


def test_identical_results_report_no_difference() -> None:
    r = compare_query(QUERY, IDS, METAS, MATRIX, *_returned(IDS), n_results=6)
    assert r["top3_sama"] and r["chunk_terlewat"] == [] and r["keluar"] == [] and r["masuk"] == []
    assert [a for a, _ in r["eksak_top"][:3]] == ["1", "2", "3"]


def test_missed_chunk_that_changes_top3_is_reported_with_ranks() -> None:
    """Bentuk kasus v1-048: chunk terbaik artikel peringkat 2 tidak dikembalikan retriever."""
    returned = [i for i in IDS if i != "2_narasi"]
    r = compare_query(QUERY, IDS, METAS, MATRIX, *_returned(returned), n_results=6)
    assert not r["top3_sama"]
    assert r["chunk_terlewat"] == [{"chunk": "2_narasi", "peringkat_eksak": 2, "skor": 0.9848}]
    assert r["keluar"] == [{"artikel": "2", "peringkat_eksak": 2, "peringkat_retriever": None}]
    assert r["masuk"] == [{"artikel": "4", "peringkat_retriever": 3, "peringkat_eksak": 4}]
    assert [a for a, _ in r["retriever_top"][:3]] == ["1", "3", "4"]


def test_missed_chunk_outside_top_articles_is_counted_but_top3_stays_equal() -> None:
    """Chunk kedua sebuah artikel terlewat: tercatat, tetapi tiga besar artikel tidak berubah."""
    returned = [i for i in IDS if i != "1_kesimpulan"]
    r = compare_query(QUERY, IDS, METAS, MATRIX, *_returned(returned), n_results=6)
    assert r["top3_sama"] and [m["chunk"] for m in r["chunk_terlewat"]] == ["1_kesimpulan"]


def test_exact_top_articles_uses_best_chunk_per_article() -> None:
    order = np.argsort(-(MATRIX @ QUERY))
    assert exact_top_articles(order, MATRIX @ QUERY, METAS, 2) == [("1", 0.9962), ("2", 0.9848)]


def test_summarize_counts_queries_and_chunks() -> None:
    same = compare_query(QUERY, IDS, METAS, MATRIX, *_returned(IDS), n_results=6)
    diff = compare_query(QUERY, IDS, METAS, MATRIX, *_returned([i for i in IDS if i != "2_narasi"]), n_results=6)
    s = summarize(["a", "b", "c"], [same, diff, same], n_results=6)
    assert s["kueri_dengan_chunk_terlewat"] == ["b"] and s["top3_artikel_berbeda"] == ["b"]
    assert (s["chunk_terlewat"], s["chunk_diperiksa"], s["kueri"]) == (1, 18, 3)


def test_run_on_real_small_collection_matches_exact_search(tmp_path) -> None:
    """Koleksi ChromaDB sungguhan yang kecil: HNSW = eksak, parameter terbaca, latensi terukur."""
    from ingest import PRODUCTION_EF_SEARCH, get_collection

    rng = np.random.default_rng(7)
    vecs = rng.normal(size=(60, 8)).astype(np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    ids = [f"{i // 3}_{('narasi', 'penjelasan', 'kesimpulan')[i % 3]}" for i in range(60)]
    metas = [{"article_id": i.split("_")[0], "section": i.split("_")[1], "title": "T", "url": "u", "label": "SALAH",
              "references": "[]"} for i in ids]
    coll = get_collection(tmp_path / "chroma")
    coll.upsert(ids=ids, embeddings=vecs.tolist(), documents=["x"] * 60, metadatas=metas)
    report = run(coll, ["q1", "q2", "q3"], vecs[[0, 17, 42]] , repeats=1)
    assert report["jumlah_chunk"] == 60 and report["ringkasan"]["top3_artikel_berbeda"] == []
    assert report["ringkasan"]["chunk_terlewat"] == 0 and report["rincian_berbeda"] == {}
    assert search_params(coll)["ef_search"] == report["parameter_hnsw"]["ef_search"] == PRODUCTION_EF_SEARCH
    assert report["latensi_kueri_ms"]["median"] >= 0
