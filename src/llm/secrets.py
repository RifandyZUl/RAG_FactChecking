"""
Rahasia dan konfigurasi lingkungan: muat `.env` dan samarkan kunci API pada teks.

Kunci API TIDAK PERNAH dicetak: semua teks galat dan log melewati `redact()`.
"""

import os
import re
from pathlib import Path

from paths import PROJECT_ROOT


def load_env(path: Path | None = None) -> None:
    """
    Muat pasangan KEY=VALUE dari `.env` ke os.environ.

    Variabel yang sudah ada di lingkungan tidak ditimpa. Nilai tidak pernah
    dicetak atau dicatat.
    """
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


_SECRET_PATTERN = re.compile(r"AIza[0-9A-Za-z_\-]{20,}")


def redact(text: str, secrets: tuple[str, ...] = ()) -> str:
    """Samarkan kunci API (nilai yang diketahui dan pola kunci Google) pada teks."""
    for s in secrets:
        if s and len(s) >= 8:
            text = text.replace(s, "[KUNCI-DISAMARKAN]")
    return _SECRET_PATTERN.sub("[KUNCI-DISAMARKAN]", text)
