"""
Penyimpanan hasil evaluasi: satu baris JSON per kueri, dapat dilanjutkan.
"""

import json
import os
import re
from pathlib import Path

from paths import PROJECT_ROOT


def append_record(path: Path, record: dict) -> None:
    """Tambahkan satu hasil ke jsonl dan paksa ke disk (tahan terhadap proses yang dihentikan)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def load_done(path: Path) -> dict[str, dict]:
    """
    Hasil yang sudah ada per klaim (baris terakhir menang). Kueri berstatus "gagal"
    tidak dianggap selesai, jadi diulang saat dilanjutkan.
    """
    done: dict[str, dict] = {}
    if not path.exists():
        return done
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError as e:
            raise SystemExit(f"{path} baris {n} rusak ({e}); perbaiki atau pakai --force.")
        if rec.get("verdict") == "gagal":
            done.pop(rec["claim"], None)
        else:
            done[rec["claim"]] = rec
    return done


def out_path_for(model: str) -> Path:
    """Berkas hasil per model, agar perbandingan antarmodel tidak saling menimpa."""
    return PROJECT_ROOT / "data" / f"generation_eval_{re.sub(r'[^A-Za-z0-9._-]', '_', model)}.jsonl"
