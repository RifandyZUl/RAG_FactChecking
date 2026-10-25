"""Uji penghitung artikel tanpa rujukan (evaluation.reference_gaps): hanya angka yang keluar."""

from evaluation.reference_gaps import count_missing_references


def test_counts_only_empty_references() -> None:
    articles = [
        {"article_id": "1", "title": "Judul rahasia", "references": ["https://contoh.go.id/a"]},
        {"article_id": "2", "title": "Judul lain", "references": []},
        {"article_id": "3", "title": "Tanpa kunci"},
    ]
    assert count_missing_references(articles) == {"jumlah_artikel": 3, "artikel_tanpa_rujukan": 2}


def test_output_has_no_article_text() -> None:
    out = count_missing_references([{"article_id": "99", "title": "Judul rahasia", "references": []}])
    assert set(out) == {"jumlah_artikel", "artikel_tanpa_rujukan"}
    assert "rahasia" not in repr(out) and "99" not in repr(out)
