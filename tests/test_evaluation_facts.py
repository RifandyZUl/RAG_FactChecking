"""Angka di halaman "Tentang" dihitung dari berkas hasil yang di-commit dan harus sama dengan README."""

from pathlib import Path

from evaluation_facts import Proportion, compute_external, external_evaluation

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


def _pct(p: Proportion) -> str:
    return f"{p.rate * 100:.1f}".replace(".", ",") + "%"


def _interval(p: Proportion) -> str:
    low, high = p.wilson
    return "[" + "; ".join(f"{x * 100:.1f}".replace(".", ",") + "%" for x in (low, high)) + "]"


def test_external_numbers_match_readme() -> None:
    ev = external_evaluation()
    found, false = ev.found_correctly, ev.false_matches
    assert (found.k, found.n, false.k, false.n, ev.total_items) == (36, 46, 10, 45, 91)
    assert f"{found.k}/{found.n} = {_pct(found)}" in README and _interval(found) in README
    assert f"{false.k}/{false.n} = {_pct(false)}" in README and _interval(false) in README
    assert f"set eksternal {ev.total_items} klaim" in README
    assert f"{ev.index_articles:,}".replace(",", ".") + " artikel" in README


def test_categories_follow_the_preregistered_rules() -> None:
    ev = external_evaluation()
    assert ev.positive_category == "memadai" and "**memadai**" in README
    assert ev.false_match_category == "belum lulus" and "**gugur**" in README


def test_compute_external_counts_only_the_correct_article_as_found() -> None:
    rows = [
        {"label_final": "1", "keputusan_modus": "ditemukan", "article_id_modus": "1"},
        {"label_final": "2", "keputusan_modus": "ditemukan", "article_id_modus": "9"},  # artikel salah
        {"label_final": "TIDAK ADA", "keputusan_modus": "ditemukan", "article_id_modus": "3"},
        {"label_final": "TIDAK ADA", "keputusan_modus": "tidak_ditemukan", "article_id_modus": None},
    ]
    ev = compute_external(rows, 10)
    assert (ev.found_correctly.k, ev.found_correctly.n, ev.false_matches.k, ev.false_matches.n) == (1, 2, 1, 2)
