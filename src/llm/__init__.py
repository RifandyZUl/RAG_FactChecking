"""
Abstraksi penyedia LLM.

Pipeline generasi hanya bergantung pada antarmuka `LLMProvider`, sehingga
penyedia dan model bisa diganti lewat konfigurasi (`LLM_PROVIDER` di `.env`)
tanpa menulis ulang pipeline. Alasannya: tier gratis dapat memperketat batas
tanpa pemberitahuan atau berhenti total, dan tahap evaluasi perlu
membandingkan beberapa model (mis. model juri yang berbeda dari generator).

Modul (dipisah menurut alasan berubah):
  errors, base, secrets     galat, antarmuka + CallRecord, .env + penyamaran kunci
  gemini, gemini_errors     penyedia Gemini dan penafsiran galat HTTP-nya
  limits, throttle, ledger  angka batas kuota, pembatas laju, buku besar + anggaran harian
"""

import os
from typing import Any

from llm.base import CallRecord, LLMProvider
from llm.errors import LLMConfigError, LLMError, LLMQuotaExhaustedError
from llm.gemini import GeminiProvider
from llm.secrets import load_env

__all__ = [
    "CallRecord", "GeminiProvider", "LLMConfigError", "LLMError", "LLMProvider",
    "LLMQuotaExhaustedError", "get_provider",
]


DEFAULT_PROVIDER = "gemini"


PROVIDERS: dict[str, type[LLMProvider]] = {"gemini": GeminiProvider}


def get_provider(name: str | None = None, **kwargs: Any) -> LLMProvider:
    """Buat penyedia dari konfigurasi: argumen `name` atau variabel LLM_PROVIDER."""
    load_env()
    key = (name or os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    if key not in PROVIDERS:
        raise LLMConfigError(f"LLM_PROVIDER '{key}' tidak dikenal; pilihan: {sorted(PROVIDERS)}")
    return PROVIDERS[key](**kwargs)
