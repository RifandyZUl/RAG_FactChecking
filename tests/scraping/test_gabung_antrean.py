"""scripts/gabung_antrean.py: antrean ditambahkan di akhir, artikel lama utuh, cadangan di folder yang diberikan."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("gabung_antrean", ROOT / "scripts" / "gabung_antrean.py")
gabung = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gabung)  # type: ignore[union-attr]


def _articles(*ids: str) -> list[dict]:
    return [{"article_id": i, "label": "SALAH", "title": f"judul {i}"} for i in ids]


def _setup(tmp_path: Path, ids: tuple[str, ...] = ("1", "2"), with_index_backup: bool = True) -> tuple[Path, Path]:
    """articles.json dan folder cadangan seperti setelah langkah cadangan indeks di README (hanya chroma/)."""
    path = tmp_path / "articles.json"
    path.write_text(json.dumps(_articles(*ids), ensure_ascii=False, indent=2), encoding="utf-8")
    folder = tmp_path / "backups" / "pre_antrean_2026-10-25"
    if with_index_backup:
        (folder / "chroma").mkdir(parents=True)
        (folder / "chroma" / "chroma.sqlite3").write_bytes(b"cadangan")
    return path, folder


def test_merge_into_folder_that_only_holds_the_index_backup(tmp_path: Path) -> None:
    path, folder = _setup(tmp_path)
    out = gabung.merge(path, _articles("3"), folder)
    assert [a["article_id"] for a in json.loads(path.read_text(encoding="utf-8"))] == ["1", "2", "3"]
    assert out == {"lama": 2, "antrean": 1, "sekarang": 3, "cadangan": str(folder / "articles.json")}
    assert [a["article_id"] for a in json.loads((folder / "articles.json").read_text(encoding="utf-8"))] == ["1", "2"]
    assert (folder / "chroma" / "chroma.sqlite3").read_bytes() == b"cadangan"  # cadangan indeks tidak disentuh


def test_merge_refuses_when_articles_backup_already_exists(tmp_path: Path) -> None:
    path, folder = _setup(tmp_path)
    (folder / "articles.json").write_text("[]", encoding="utf-8")
    with pytest.raises(FileExistsError):
        gabung.merge(path, _articles("3"), folder)
    assert json.loads(path.read_text(encoding="utf-8")) == _articles("1", "2")
    assert (folder / "articles.json").read_text(encoding="utf-8") == "[]"


def test_merge_refuses_without_index_backup(tmp_path: Path) -> None:
    """Folder lain (mis. tengah malam terlewati) tanpa chroma/: ditolak, tidak ada yang ditulis."""
    path, folder = _setup(tmp_path, with_index_backup=False)
    with pytest.raises(FileNotFoundError, match="cadangan indeks"):
        gabung.merge(path, _articles("3"), folder)
    assert json.loads(path.read_text(encoding="utf-8")) == _articles("1", "2")
    assert not folder.exists()


def test_merge_refuses_duplicate_ids(tmp_path: Path) -> None:
    path, folder = _setup(tmp_path, ids=("1",))
    with pytest.raises(ValueError, match="id ganda"):
        gabung.merge(path, _articles("1"), folder)
    assert json.loads(path.read_text(encoding="utf-8")) == _articles("1")


def test_write_requires_explicit_backup_folder() -> None:
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "gabung_antrean.py"), "--tulis"],
                         capture_output=True, text=True, cwd=ROOT, check=False)
    assert out.returncode == 2 and "--folder-cadangan" in out.stderr
