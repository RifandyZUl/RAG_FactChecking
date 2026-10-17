"""Uji offline candidates.blind_session: kolam, pengecualian, dan pemilihan berbenih yang dapat diulang."""

from candidates.blind_session import AUDIT, INCONSISTENT, PICK, pools, select


def test_pools_exclude_discussed_inconsistent_and_audit_items():
    p = pools()
    assert len(INCONSISTENT) == 15
    assert len(p[1]) == 50 - 5 - 15 - 4, "P1-20 dan P1-29 sudah termasuk 15 butir tidak konsisten"
    assert len(p[2]) == 48
    assert not set(range(1, 6)) & set(p[1]) and not set(INCONSISTENT) & set(p[1])
    assert all(n not in p[int(r[1])] for r, n in AUDIT)


def test_selection_is_reproducible_and_inside_pools():
    a, b = select(), select()
    assert a == b
    p = pools()
    for r in (1, 2):
        got = a["uji_ulang"][f"putaran_{r}"]
        assert len(got) == len(set(got)) == PICK[r] and set(got) <= set(p[r])
    assert select(seed=1) != a, "benih menentukan pilihan"
