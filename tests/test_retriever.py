"""Uji agregasi retrieval per article_id (retriever).
"""


def test_aggregate_by_article() -> None:
    """Agregasi per artikel: skor tertinggi per artikel, tanpa duplikat artikel."""
    from chunker import encode_references
    from retriever import aggregate_by_article

    def meta(aid: str, section: str, refs: list[str]) -> dict:
        return {"article_id": aid, "title": f"T{aid}", "url": f"u{aid}", "label": "SALAH",
                "section": section, "references": encode_references(refs)}

    # jarak kosinus -> skor = 1 - jarak
    metas = [
        meta("A", "penjelasan", ["r1"]), meta("B", "narasi", []),
        meta("A", "narasi", ["r1"]), meta("A", "kesimpulan", ["r1"]),
        meta("B", "kesimpulan", []),
    ]
    dists = [0.30, 0.35, 0.50, 0.60, 0.20]
    hits = aggregate_by_article(metas, dists)
    assert [h.article_id for h in hits] == ["B", "A"], "urutan harus menurut skor tertinggi"
    b, a = hits
    assert abs(b.score - 0.80) < 1e-9 and b.best_section == "kesimpulan"
    assert abs(a.score - 0.70) < 1e-9 and a.best_section == "penjelasan"
    assert set(a.section_scores) == {"penjelasan", "narasi", "kesimpulan"}
    assert a.references == ["r1"], "references harus didekode dari metadata"
    assert len({h.article_id for h in hits}) == len(hits)
