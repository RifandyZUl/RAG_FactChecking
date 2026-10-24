"""Tautan relatif di dokumen Markdown yang di-track git tidak boleh patah (berkas tujuan harus ada)."""

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def _tracked_markdown() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / f for f in out.split()]


def _broken_links() -> list[str]:
    broken = []
    for doc in _tracked_markdown():
        for target in LINK.findall(doc.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue  # tautan web/surel atau jangkar di halaman yang sama
            path = unquote(target.split("#", 1)[0])
            if not (doc.parent / path).exists():
                broken.append(f"{doc.relative_to(ROOT).as_posix()} -> {target}")
    return broken


def test_tracked_markdown_files_exist() -> None:
    assert len(_tracked_markdown()) >= 10


def test_no_broken_relative_links_in_documents() -> None:
    assert _broken_links() == []
