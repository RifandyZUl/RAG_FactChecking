"""Uji set pengembangan dengan dua label terpisah (evaluation.devset) dan turunannya di retrieval_eval."""

from evaluation.devset import DEV_QUERIES, VERDICT_BELUM, VERDICT_DITEMUKAN, DevQuery
from evaluation.retrieval_eval import NEGATIVE_QUERIES, QUERIES


def _by_claim(fragment: str) -> DevQuery:
    (q,) = [d for d in DEV_QUERIES if fragment in d.claim]
    return q


def test_query3_has_two_different_labels() -> None:
    """Kueri 3: seharusnya TERJANGKAU retrieval (36729) tetapi keputusan akhirnya belum_ditemukan (lebih umum)."""
    q3 = _by_claim("malaysia marah")
    assert q3.expected_retrieval_article == "36729"
    assert q3.expected_verdict == VERDICT_BELUM
    assert q3.expected_article_id is None, "tidak ada artikel yang seharusnya DIPILIH generator"
    assert q3.kekhususan == "umum" and q3.tipe == "negatif_sulit"
    assert "SETELAH melihat keluaran model" in q3.catatan


def test_query2_is_marked_borderline_and_not_decided_generally() -> None:
    q2 = _by_claim("bantuan buat orang tua")
    assert q2.kekhususan == "batas" and q2.batas
    assert q2.expected_verdict == VERDICT_DITEMUKAN and q2.expected_retrieval_article == "36737"
    assert "per butir" in q2.catatan
    assert sum(d.batas for d in DEV_QUERIES) == 1


def test_dev_set_shape_and_derived_retrieval_lists() -> None:
    assert len(DEV_QUERIES) == 10 and len({d.claim for d in DEV_QUERIES}) == 10
    # Recall@3 memakai expected_retrieval_article: kueri 3 IKUT (dulu positif, tetap terjangkau)
    assert [c for c, _ in QUERIES] == [d.claim for d in DEV_QUERIES if d.expected_retrieval_article]
    assert dict(QUERIES)["malaysia marah ke indonesia soal asap"] == "36729"
    assert len(QUERIES) == 5
    # negatif murni (tanpa artikel yang perlu terjangkau) = 5, dengan kata kunci absen
    assert len(NEGATIVE_QUERIES) == 5 and all(kw for _, _, kw in NEGATIVE_QUERIES)
    # keputusan akhir: 4 ditemukan (termasuk butir batas), 6 belum_ditemukan
    assert sum(d.expected_verdict == VERDICT_DITEMUKAN for d in DEV_QUERIES) == 4
    for d in DEV_QUERIES:
        assert (d.expected_article_id is not None) == (d.expected_verdict == VERDICT_DITEMUKAN)
