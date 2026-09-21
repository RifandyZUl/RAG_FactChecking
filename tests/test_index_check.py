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
