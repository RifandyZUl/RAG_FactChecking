"""Uji kesegaran indeks (evaluation.index_check) dan pembangunan ulang dari nol (ingest.reset_collection)."""

from evaluation.index_check import compare_index


def _chunk(cid: str, text: str, **meta) -> dict:
    md = {"article_id": cid.split("_")[0], "url": "u", "title": "T", "label": "SALAH", "category": "Politik",
          "date": "01/01/2026", "section": cid.split("_")[1], "references": "[]", "n_tokens": 5, "truncated": False}
    md.update(meta)
    return {"id": cid, "text": text, "metadata": md}


def _stored(chunks: list[dict]):
    return [c["id"] for c in chunks], [c["text"] for c in chunks], [dict(c["metadata"]) for c in chunks]


def test_compare_index_fresh_has_no_problems() -> None:
    chunks = [_chunk("1_narasi", "a"), _chunk("1_kesimpulan", "k")]
    assert compare_index(chunks, *_stored(chunks)) == []


def test_compare_index_detects_stale_text_even_when_ids_match() -> None:
    """Kasus indeks basi: id sama, teks lama (terduplikasi) -> tidak ada galat di retriever, tetapi harus terdeteksi."""
    new = [_chunk("1_narasi", "a"), _chunk("1_kesimpulan", "k")]
    old = [_chunk("1_narasi", "a a"), _chunk("1_kesimpulan", "k")]
    problems = compare_index(new, *_stored(old))
    assert len(problems) == 1 and "1_narasi" in problems[0] and "teks beda" in problems[0]
    assert "indeks 3 kar vs articles.json 1 kar" in problems[0]


def test_compare_index_detects_missing_extra_and_metadata_drift() -> None:
    new = [_chunk("1_narasi", "a"), _chunk("2_narasi", "b", n_tokens=7)]
    old = [_chunk("1_narasi", "a"), _chunk("3_narasi", "z")]
    problems = compare_index(new, *_stored(old))
    text = " | ".join(problems)
    assert "belum ada di indeks" in text and "2_narasi" in text
    assert "usang" in text and "3_narasi" in text
    drift = compare_index([_chunk("1_narasi", "a", n_tokens=9)], *_stored([_chunk("1_narasi", "a")]))
    assert len(drift) == 1 and "n_tokens" in drift[0]


def test_compare_index_detects_stale_references_when_text_is_identical() -> None:
    """
    Kasus yang TIDAK tertangkap ingest inkremental (ia hanya membandingkan teks): kebijakan
    penyaringan rujukan diperketat, teks chunk sama, tetapi rujukan tersimpan di indeks masih lama.
    """
    stale = '["https://www.contoh.go.id/rilis", "https://tinyurl.com/contoh1"]'
    fresh = '["https://www.contoh.go.id/rilis"]'
    sections = ("narasi", "penjelasan", "kesimpulan")
    new = [_chunk(f"1_{s}", s, references=fresh) for s in sections]
    old = [_chunk(f"1_{s}", s, references=stale) for s in sections]
    problems = compare_index(new, *_stored(old))
    assert len(problems) == 3, "setiap chunk artikel itu dilaporkan"
    assert all("metadata 'references' beda" in p for p in problems)
    assert compare_index(new, *_stored(new)) == []


def test_reset_collection_removes_stale_content(tmp_path) -> None:
    """--rebuild: koleksi lama beserta seluruh isinya (termasuk id usang) hilang; koleksi baru kosong."""
    from ingest import get_collection, reset_collection

    path = tmp_path / "chroma"
    coll = get_collection(path)
    coll.upsert(ids=["1_narasi", "9_narasi"], embeddings=[[1.0, 0.0], [0.0, 1.0]], documents=["lama", "usang"],
                metadatas=[{"section": "narasi"}, {"section": "narasi"}])
    assert coll.count() == 2

    fresh = reset_collection(path)
    assert fresh.count() == 0, "koleksi lama harus terhapus, bukan dilewati"
    assert get_collection(path).count() == 0


# -- sidik jari isi (arsip indeks Versi 1) ------------------------------------

def _fp_inputs() -> tuple[list[str], list[str], list[dict], list[list[float]]]:
    ids = ["2_narasi", "1_narasi", "1_kesimpulan"]
    docs = ["b", "a", "k"]
    metas = [{"article_id": "2", "section": "narasi"}, {"article_id": "1", "section": "narasi"},
             {"article_id": "1", "section": "kesimpulan"}]
    embs = [[0.0, 1.0], [1.0, 0.0], [0.6, 0.8]]
    return ids, docs, metas, embs


def test_fingerprint_counts_and_order_independence() -> None:
    from evaluation.index_check import content_fingerprint

    ids, docs, metas, embs = _fp_inputs()
    fp = content_fingerprint(ids, docs, metas, embs)
    assert (fp["jumlah_chunk"], fp["jumlah_artikel"]) == (3, 2)
    rev = content_fingerprint(ids[::-1], docs[::-1], metas[::-1], embs[::-1])
    assert fp == rev, "urutan penyimpanan tidak boleh memengaruhi sidik jari"


def test_fingerprint_detects_text_metadata_and_embedding_changes() -> None:
    from evaluation.index_check import content_fingerprint

    ids, docs, metas, embs = _fp_inputs()
    base = content_fingerprint(ids, docs, metas, embs)
    changed_text = content_fingerprint(ids, ["b", "a!", "k"], metas, embs)
    assert changed_text["sha256_teks_metadata"] != base["sha256_teks_metadata"]
    assert changed_text["sha256_embedding_float32"] == base["sha256_embedding_float32"]
    metas2 = [dict(m) for m in metas]
    metas2[0]["section"] = "penjelasan"
    assert content_fingerprint(ids, docs, metas2, embs)["sha256_teks_metadata"] != base["sha256_teks_metadata"]
    embs2 = [list(e) for e in embs]
    embs2[1][0] = 0.9999999
    changed_emb = content_fingerprint(ids, docs, metas, embs2)
    assert changed_emb["sha256_embedding_float32"] != base["sha256_embedding_float32"]
    assert changed_emb["sha256_teks_metadata"] == base["sha256_teks_metadata"]


def test_compare_fingerprints_and_articles_hash() -> None:
    from evaluation.index_check import (
        FINGERPRINT_KEYS,
        articles_content_hash,
        compare_fingerprints,
    )

    fp = {k: "x" for k in FINGERPRINT_KEYS}
    assert compare_fingerprints(fp, dict(fp)) == []
    other = dict(fp, sha256_embedding_float32="y")
    problems = compare_fingerprints(other, fp)
    assert len(problems) == 1 and "dibangun ulang" in problems[0]
    a = [{"article_id": "1", "title": "T"}]
    assert articles_content_hash(a) == articles_content_hash([{"title": "T", "article_id": "1"}])
    assert articles_content_hash(a) != articles_content_hash([{"article_id": "1", "title": "U"}])


def test_v1_archive_fingerprint_recorded_in_meta() -> None:
    """Sidik jari arsip Versi 1 wajib tercatat lengkap di v1.meta.json."""
    import json
    from pathlib import Path

    from evaluation.index_check import FINGERPRINT_KEYS, V1_ARCHIVE_META_KEY

    meta = json.loads((Path(__file__).resolve().parent.parent / "testset" / "v1.meta.json").read_text(encoding="utf-8"))
    fp = meta[V1_ARCHIVE_META_KEY]["sidik_jari_isi"]
    assert set(FINGERPRINT_KEYS) <= set(fp)
    assert (fp["jumlah_artikel"], fp["jumlah_chunk"]) == (150, 450)


def test_update_metadata_rewrites_only_metadata_of_chunks_with_identical_text(tmp_path) -> None:
    """Pembaruan terarah: metadata basi diganti; embedding dan teks utuh; chunk berteks beda/tidak ada tak disentuh."""
    import numpy as np

    from ingest import get_collection, update_metadata

    stale, fresh = '["https://www.contoh.go.id/rilis", "https://tinyurl.com/contoh1"]', '["https://www.contoh.go.id/rilis"]'
    old = [_chunk("1_narasi", "n", references=stale), _chunk("1_kesimpulan", "k", references=stale),
           _chunk("2_narasi", "teks lama", references=stale), _chunk("3_narasi", "c")]
    vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.6, 0.8, 0.0]]
    coll = get_collection(tmp_path / "chroma")
    coll.upsert(ids=[c["id"] for c in old], embeddings=vectors, documents=[c["text"] for c in old],
                metadatas=[c["metadata"] for c in old])

    new = [_chunk("1_narasi", "n", references=fresh), _chunk("1_kesimpulan", "k", references=fresh),
           _chunk("2_narasi", "teks baru", references=fresh), _chunk("3_narasi", "c"), _chunk("4_narasi", "belum ada")]
    assert len(compare_index(new[:2], *_stored(old[:2]))) == 2, "sebelum: index_check melihat metadata basi"
    summary = update_metadata(new, coll)
    assert summary["metadata_diperbarui"] == 2 and summary["artikel_terdampak"] == ["1"]
    assert summary["kunci_berubah"] == {"references": 2}
    assert (summary["teks_berbeda_dilewati"], summary["belum_ada_di_indeks"]) == (1, 1)

    got = coll.get(ids=[c["id"] for c in old], include=["documents", "metadatas", "embeddings"])
    by_id = {i: (d, m, e) for i, d, m, e in zip(got["ids"], got["documents"], got["metadatas"], got["embeddings"])}
    for c, vec in zip(old, vectors):
        doc, _, emb = by_id[c["id"]]
        assert doc == c["text"] and np.allclose(emb, vec), f"{c['id']}: teks/embedding berubah"
    assert by_id["1_narasi"][1]["references"] == fresh and by_id["1_kesimpulan"][1]["references"] == fresh
    assert by_id["2_narasi"][1]["references"] == stale, "teks berbeda: bukan urusan pembaruan metadata"
    assert coll.count() == 4, "tidak ada chunk yang ditambahkan"
    assert compare_index(new[:2] + new[3:4], *_stored([{"id": i, "text": by_id[i][0], "metadata": by_id[i][1]}
                                                       for i in ("1_narasi", "1_kesimpulan", "3_narasi")])) == []
    assert update_metadata(new, coll)["metadata_diperbarui"] == 0, "idempoten"
