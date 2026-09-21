"""Uji penyimpanan dan pelanjutan hasil evaluasi (evaluation.results_store).
"""

from pathlib import Path


def test_eval_resume_and_incremental() -> None:
    import json
    import tempfile
    from pathlib import Path

    from evaluation.results_store import append_record, load_done

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "x.jsonl"
        assert load_done(path) == {}
        append_record(path, {"claim": "a", "verdict": "ditemukan"})
        append_record(path, {"claim": "b", "verdict": "gagal"})
        append_record(path, {"claim": "c", "verdict": "tidak_ditemukan"})
        done = load_done(path)
        assert set(done) == {"a", "c"}, "yang gagal harus diulang, bukan dilewati"
        append_record(path, {"claim": "b", "verdict": "ditemukan"})  # hasil ulang menimpa
        assert set(load_done(path)) == {"a", "b", "c"}
        assert len(path.read_text(encoding="utf-8").splitlines()) == 4
        assert all(json.loads(x) for x in path.read_text(encoding="utf-8").splitlines())
