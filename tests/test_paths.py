"""Uji pemilihan indeks (RAG_INDEX_DIR) dan penjaga tulis ke arsip."""

from pathlib import Path

import pytest

import paths
from ingest import refuse_archive_write


def _make_index(root: Path) -> Path:
    (root / "chroma").mkdir(parents=True)
    (root / "chroma" / "chroma.sqlite3").write_bytes(b"")
    (root / "articles.json").write_text("[]", encoding="utf-8")
    return root


def test_default_is_main_data_dir() -> None:
    assert paths.resolve_index_dir(None) == paths.DATA_DIR
    assert paths.resolve_index_dir("  ") == paths.DATA_DIR


def test_absolute_index_dir_is_used(tmp_path: Path) -> None:
    idx = _make_index(tmp_path / "idx")
    assert paths.resolve_index_dir(str(idx)) == idx.resolve()


def test_missing_index_dir_raises_instead_of_creating_empty_index(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="tidak berisi indeks lengkap"):
        paths.resolve_index_dir(str(tmp_path / "salah-ketik"))
    assert not (tmp_path / "salah-ketik").exists()


def test_incomplete_index_dir_raises(tmp_path: Path) -> None:
    idx = tmp_path / "idx"
    (idx / "chroma").mkdir(parents=True)
    (idx / "articles.json").write_text("[]", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="chroma.sqlite3"):
        paths.resolve_index_dir(str(idx))


def test_scraping_write_path_never_follows_index_dir() -> None:
    assert paths.ARTICLES_PATH == paths.DATA_DIR / "articles.json"
    assert paths.RAW_HTML_DIR == paths.DATA_DIR / "raw_html"


def test_archive_detection_and_write_guard() -> None:
    inside = paths.V1_ARCHIVE_DIR / "chroma"
    assert paths.is_archive_path(inside)
    assert not paths.is_archive_path(paths.DATA_DIR / "chroma")
    with pytest.raises(PermissionError, match="archive"):
        refuse_archive_write(inside, allow_archive=False)
    refuse_archive_write(inside, allow_archive=True)
    refuse_archive_write(paths.DATA_DIR / "chroma", allow_archive=False)


def test_reset_collection_refuses_archive_path() -> None:
    from ingest import reset_collection

    with pytest.raises(PermissionError):
        reset_collection(paths.V1_ARCHIVE_DIR / "chroma")
