"""Uji offline labeling.gap.gap_result: validasi berkas terisi, batas sensitivitas, perbandingan dengan kunci."""

from labeling.gap.gap_result import compare_with_key, sensitivity, timing, validate
from labeling.gap.gap_review import COLUMNS


def _rows(decisions: dict[int, str]) -> list[dict[str, str]]:
    """Dua kandidat (id 100+n dan 200+n) per butir; keputusan di baris pertama."""
    rows = []
    for n, decision in decisions.items():
        for i, tbh in enumerate((100 + n, 200 + n), 1):
            row = dict.fromkeys(COLUMNS, "")
            row.update({"butir": str(n), "kandidat": str(i), "TBH_id": str(tbh), "TBH_label": "SALAH"})
            if i == 1:
                row.update({"L6_judul": f"judul {n}", "L6_tanggal": "2026-01-01", "KEPUTUSAN": decision})
            rows.append(row)
    return rows


def _decisions(kinds: dict[int, str]) -> list[dict]:
    return [{"butir": str(n), "jenis": k, "keputusan": str(100 + n) if k == "sama" else "", "ujung_rentang": False} for n, k in kinds.items()]


def test_validate_accepts_filled_file_with_identical_fixed_columns():
    template = _rows({1: "", 2: "", 3: ""})
    filled = _rows({1: "101", 2: "TIDAK ADA", 3: "BUKAN PUTUSAN HOAKS"})
    assert validate(filled, template, expected_items=3) == []


def test_validate_reports_instead_of_guessing():
    template = _rows({1: "", 2: "", 3: ""})
    assert any("jumlah butir" in p for p in validate(_rows({1: "101", 2: "TIDAK ADA"}), template[:4], expected_items=3))
    for bad in ("", "999", "mungkin"):  # kosong, id di luar kandidat, tulisan lain
        assert any("butir 2" in p for p in validate(_rows({1: "101", 2: bad, 3: "TIDAK ADA"}), template, expected_items=3))
    changed = _rows({1: "101", 2: "TIDAK ADA", 3: "TIDAK ADA"})
    changed[3]["TBH_judul"] = "diubah"
    assert any("berbeda dari berkas asli" in p for p in validate(changed, template, expected_items=3))
    assert any("seharusnya kosong" in p for p in validate(changed, _rows({1: "101", 2: "", 3: ""}), expected_items=3))


def test_sensitivity_flips_only_items_whose_main_label_matches_the_list():
    kinds = {n: "sama" for n in range(1, 5)} | {n: "tidak_ada" for n in range(5, 11)} | {11: "bukan_putusan_hoaks"}
    s = sensitivity(_decisions(kinds), accepted=(1, 2, 5), rejected=(6, 11))
    assert (s["utama"]["tidak_ada"], s["utama"]["butir_sah"]) == (6, 10)  # bukan putusan hoaks keluar dari penyebut
    assert (s["batas_atas"]["tidak_ada"], s["batas_atas"]["butir_dibalik"]) == (8, [1, 2])
    assert (s["batas_bawah"]["tidak_ada"], s["batas_bawah"]["butir_dibalik"]) == (5, [6])
    assert s["tidak_sesuai_daftar"] == [5, 11]


def test_sensitivity_category_comparison():
    kinds = {n: "tidak_ada" for n in range(1, 30)} | {n: "sama" for n in range(30, 51)}  # 29/50: ambigu
    stable = sensitivity(_decisions(kinds), accepted=(30,), rejected=(1,))
    assert stable["utama"]["status"] == "ambigu" and stable["kategori_sama_di_kedua_batas"]
    moved = sensitivity(_decisions(kinds), accepted=tuple(range(30, 38)), rejected=())
    assert moved["batas_atas"]["status"] == "jelas_di_atas_50" and not moved["kategori_sama_di_kedua_batas"]


def test_timing_relative_to_liputan6():
    assert [timing("2026-03-10", d) for d in ("09/03/2026", "10/03/2026", "11/03/2026")] == ["sebelum", "hari_sama", "sesudah"]


def test_compare_with_key_ranks_human_choice_per_search():
    decisions = [{"butir": 1, "jenis": "sama", "keputusan": "101"}, {"butir": 2, "jenis": "sama", "keputusan": "202"},
                 {"butir": 3, "jenis": "tidak_ada", "keputusan": "TIDAK ADA"}]
    scores = {"a": {"embedding_top": [["101", 0.7], ["201", 0.6]], "kata_kunci_top": [["201", 0.5, 0.4], ["101", 0.3, 0.2]]},
              "b": {"embedding_top": [["102", 0.65]], "kata_kunci_top": [["202", 0.6, 0.5]]},
              "c": {"embedding_top": [["103", 0.8]], "kata_kunci_top": [["203", 0.1, 0.1]]}}
    out = compare_with_key(decisions, {"1": "a", "2": "b", "3": "c"}, scores)
    assert (out["pilihan_adalah_teratas_embedding"], out["pilihan_ada_di_5_teratas_embedding"]) == (1, 1)
    assert (out["pilihan_adalah_teratas_kata_kunci"], out["pilihan_ada_di_3_teratas_kata_kunci"]) == (1, 2)
    assert out["pilihan_teratas_di_keduanya"] == 0 and out["pilihan_bukan_teratas_di_keduanya"] == []
    assert [x["butir"] for x in out["tidak_ada_dengan_skor_embedding_di_atas_median_pilihan"]] == [3]
