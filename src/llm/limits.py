"""
Angka batas kuota tier gratis per model (RPM, TPM, RPD). Berubah bila Google mengubah tier.

Batas per model dibaca dari `DEFAULT_LIMITS` dan dapat ditimpa lewat `.env`
(`LLM_RPM`, `LLM_TPM`, `LLM_RPD`). Angka bawaan diambil dari AI Studio dan dapat
berubah tanpa pemberitahuan (lihat CLAUDE.md), jadi periksa ulang secara berkala.
"""

import os
from dataclasses import dataclass


CHARS_PER_TOKEN = 3.0  # perkiraan konservatif teks Indonesia; dikoreksi dengan token nyata


LIMITS_DATE = "2026-09-21"  # tanggal angka di bawah diambil dari AI Studio


@dataclass(frozen=True)
class ModelLimits:
    """Batas tier gratis satu model: permintaan/menit, token masuk/menit, permintaan/hari."""

    rpm: int
    tpm: int
    rpd: int


_FLASH_LITE = ModelLimits(rpm=15, tpm=250_000, rpd=500)


_GEMMA = ModelLimits(rpm=30, tpm=16_000, rpd=14_400)


# Diambil dari AI Studio (kolom batas) pada LIMITS_DATE. ID model diverifikasi dari
# dokumentasi resmi; AI Studio menampilkan nama pendek ("gemma-4-26b"), yang di sini
# dipetakan ke ID API (pemetaan itu asumsi: AI Studio tidak menampilkan ID persis).
DEFAULT_LIMITS: dict[str, ModelLimits] = {
    "gemini-3.8-flash": ModelLimits(rpm=5, tpm=250_000, rpd=20),
    "gemini-3.5-flash-lite": _FLASH_LITE,
    "gemini-3.1-flash-lite": _FLASH_LITE,
    "gemma-4-26b-a4b-it": _GEMMA,
    "gemma-4-31b-it": _GEMMA,
}


def limits_for(model: str) -> ModelLimits | None:
    """Batas untuk `model`; nilai `LLM_RPM`/`LLM_TPM`/`LLM_RPD` di lingkungan menimpa bawaan."""
    base = DEFAULT_LIMITS.get(model)
    env = {k: os.environ.get(f"LLM_{k.upper()}") for k in ("rpm", "tpm", "rpd")}
    if base is None and not all(env.values()):
        return None
    vals = {k: int(env[k]) if env[k] else getattr(base, k) for k in ("rpm", "tpm", "rpd")}
    return ModelLimits(**vals)


def estimate_tokens(*texts: str) -> int:
    """Perkiraan kasar token masuk (belum dikirim); TPM Gemini menghitung token masuk."""
    return int(sum(len(t) for t in texts) / CHARS_PER_TOKEN) + 1
