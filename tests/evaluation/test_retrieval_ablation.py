"""Uji offline fungsi murni eksperimen ablasi retrieval (tanpa model, tanpa indeks, tanpa API)."""

import random

import pytest

from evaluation.retrieval_ablation import (
    FILLER_SENTENCES,
    ChunkScore,
    aggregate_max,
    aggregate_mean,
    aggregate_mean_top2,
    article_rank,
    best_section_of,
    claim_visibility,
    filler_text,
    group_items,
    hit_at_k,
    load_items,
    mcnemar_exact_p,
    pad_claim,
    paired_comparison,
    parse_recorded_top3,
    rank_articles,
    recall_summary,
    targeted_items,
)
from retriever import aggregate_by_article

CHUNKS = [
    ChunkScore("A", "narasi", 0.50), ChunkScore("A", "penjelasan", 0.80), ChunkScore("A", "kesimpulan", 0.40),
    ChunkScore("B", "narasi", 0.70), ChunkScore("B", "penjelasan", 0.69), ChunkScore("B", "kesimpulan", 0.68),
    ChunkScore("C", "narasi", 0.30), ChunkScore("C", "penjelasan", 0.20), ChunkScore("C", "kesimpulan", 0.75),
]


def test_aggregators() -> None:
    assert aggregate_max([0.5, 0.8, 0.4]) == 0.8
    assert aggregate_mean([0.5, 0.8, 0.4]) == pytest.approx(0.5667, abs=1e-4)
    assert aggregate_mean_top2([0.5, 0.8, 0.4]) == pytest.approx(0.65)
    assert aggregate_mean_top2([0.3]) == 0.3


def test_rank_articles_strategies_differ() -> None:
    assert [a for a, _ in rank_articles(CHUNKS)] == ["A", "C", "B"]
    assert [a for a, _ in rank_articles(CHUNKS, aggregate_mean)] == ["B", "A", "C"]
    assert [a for a, _ in rank_articles(CHUNKS, aggregate_mean_top2)] == ["B", "A", "C"]


def test_rank_articles_section_filter() -> None:
    assert [a for a, _ in rank_articles(CHUNKS, sections=frozenset({"narasi"}))] == ["B", "A", "C"]
    assert [a for a, _ in rank_articles(CHUNKS, sections=frozenset({"kesimpulan"}))] == ["C", "B", "A"]


def test_max_ranking_matches_production_aggregation() -> None:
    """Agregasi maks eksperimen harus sama dengan retriever.aggregate_by_article produksi."""
    metas = [{"article_id": c.article_id, "title": "", "url": "", "label": "", "section": c.section,
              "references": "[]"} for c in CHUNKS]
    prod = aggregate_by_article(metas, [1 - c.score for c in CHUNKS])
    ours = rank_articles(CHUNKS)
    assert [h.article_id for h in prod] == [a for a, _ in ours]
    assert [round(h.score, 6) for h in prod] == [round(s, 6) for _, s in ours]


def test_ties_are_deterministic() -> None:
    tied = [ChunkScore("Z", "narasi", 0.5), ChunkScore("Y", "narasi", 0.5)]
    assert [a for a, _ in rank_articles(tied)] == ["Y", "Z"]


def test_rank_and_hit() -> None:
    ranking = rank_articles(CHUNKS)
    assert article_rank(ranking, "B") == 3
    assert article_rank(ranking, "X") is None
    assert hit_at_k(3, 3) and not hit_at_k(4, 3) and not hit_at_k(None, 20)


def test_recall_summary() -> None:
    s = recall_summary([1, 2, 4, None], 3)
    assert (s["benar"], s["n"], s["proporsi"]) == (2, 4, 0.5)
    assert s["wilson95"][0] < 0.5 < s["wilson95"][1]


@pytest.mark.parametrize(("gained", "lost", "expected"), [
    (0, 0, 1.0), (1, 0, 1.0), (2, 0, 0.5), (3, 0, 0.25), (6, 0, 0.03125), (3, 3, 1.0), (5, 1, 0.21875),
])
def test_mcnemar_exact(gained: int, lost: int, expected: float) -> None:
    assert mcnemar_exact_p(gained, lost) == pytest.approx(expected)


def test_paired_comparison_requires_significance_and_min_diff() -> None:
    base = [False] * 6 + [True] * 34
    assert paired_comparison(base, [True] * 40)["kesimpulan"] == "selisih bermakna"  # +6, p=0,031
    two = paired_comparison([False, False, True], [True, True, True])
    assert two["selisih_bersih"] == 2 and two["kesimpulan"] == "tidak dapat dibedakan dari kebetulan"
    assert paired_comparison([True, False], [True, False])["kesimpulan"] == "identik"


def test_filler_is_exact_length_and_deterministic() -> None:
    for n in (0, 10, 777, 4000):
        text = filler_text(n, random.Random(1))
        assert len(text) == n
    assert filler_text(500, random.Random(7)) == filler_text(500, random.Random(7))
    assert any(s[:20] in filler_text(2000, random.Random(3)) for s in FILLER_SENTENCES)


@pytest.mark.parametrize("target", [1500, 3000, 5000])
@pytest.mark.parametrize("placement", ["kedua_sisi", "belakang"])
def test_pad_claim_keeps_claim_intact(target: int, placement: str) -> None:
    claim = "katanya vaksin HPV bikin anak laki-laki impoten, hati2 ya"
    text, offset = pad_claim(claim, target, random.Random(0), placement)
    assert len(text) == target
    assert text[offset:offset + len(claim)] == claim
    if placement == "belakang":
        assert offset == 0
    else:
        assert target * 0.4 < offset < target * 0.6


def test_pad_claim_rejects_unknown_placement_and_keeps_long_claims() -> None:
    with pytest.raises(ValueError):
        pad_claim("x", 100, random.Random(0), "tengah")
    assert pad_claim("a" * 50, 20, random.Random(0)) == ("a" * 50, 0)


@pytest.mark.parametrize(("before", "claim", "expected"), [
    (0, 40, "utuh"), (400, 111, "utuh"), (400, 112, "sebagian"), (511, 5, "terpotong_seluruhnya"),
    (600, 30, "terpotong_seluruhnya"),
])
def test_claim_visibility(before: int, claim: int, expected: str) -> None:
    assert claim_visibility(before, claim, 512) == expected


def test_best_section_of() -> None:
    assert best_section_of(CHUNKS, "A") == "penjelasan"
    assert best_section_of(CHUNKS, "C") == "kesimpulan"
    assert best_section_of(CHUNKS, "X") is None


def test_parse_recorded_top3_accepts_repr_and_list() -> None:
    rec = [{"article_id": "36573", "score": 0.78}, {"article_id": 36520, "score": 0.6}]
    assert parse_recorded_top3(rec) == ["36573", "36520"]
    assert parse_recorded_top3(repr(rec)) == ["36573", "36520"]


def test_groups_on_frozen_testset() -> None:
    """Komposisi kelompok pada set uji beku (membaca v1.jsonl, tidak mengubahnya)."""
    items = load_items()
    groups = group_items(items)
    assert len(items) == 54
    assert len(groups["non_batas"]) == 50 and len(groups["batas"]) == 4
    targeted = group_items(targeted_items(items))
    assert len(targeted["non_batas"]) == 40 and len(targeted["batas"]) == 4
    assert "tipe:negatif_mudah" not in targeted
    assert {i["id"] for i in items} >= {"v1-022", "v1-024", "v1-027", "v1-033"}
