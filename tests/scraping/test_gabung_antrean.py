"""scripts/gabung_antrean.py: antrean ditambahkan di akhir, artikel lama utuh, cadangan tidak ditimpa."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("gabung_antrean", ROOT / "scripts" / "gabung_antrean.py")
gabung = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gabung)  # type: ignore[union-attr]


def _articles(*ids: str) -> list[dict]:
    return [{"article_id": i, "label": "SALAH", "title": f"judul {i}"} for i in ids]


def test_merge_appends_queue_and_keeps_old_articles(tmp_path: Path) -> None:
    path = tmp_path / "articles.json"
    path.write_text(json.dumps(_articles("1", "2"), ensure_ascii=False, indent=2), encoding="utf-8")
    out = gabung.merge(path, _articles("3"), tmp_path / "cadangan")
    merged = json.loads(path.read_text(encoding="utf-8"))
    assert [a["article_id"] for a in merged] == ["1", "2", "3"]
    assert out == {"lama": 2, "antrean": 1, "sekarang": 3, "cadangan": str(tmp_path / "cadangan" / "articles.json")}
    assert [a["article_id"] for a in json.loads((tmp_path / "cadangan" / "articles.json").read_text(encoding="utf-8"))] == ["1", "2"]


def test_merge_refuses_existing_backup_and_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "articles.json"
    path.write_text(json.dumps(_articles("1")), encoding="utf-8")
    (tmp_path / "cadangan").mkdir()
    (tmp_path / "cadangan" / "articles.json").write_text("[]", encoding="utf-8")
    with pytest.raises(FileExistsError):
        gabung.merge(path, _articles("2"), tmp_path / "cadangan")
    with pytest.raises(ValueError, match="id ganda"):
        gabung.merge(path, _articles("1"), tmp_path / "cadangan_lain")
    assert json.loads(path.read_text(encoding="utf-8")) == _articles("1")
