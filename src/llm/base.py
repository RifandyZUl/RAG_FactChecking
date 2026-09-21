"""
Antarmuka penyedia LLM dan catatan panggilan.

Pipeline hanya bergantung pada `LLMProvider.generate`; penyedia dipilih lewat konfigurasi.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("llm")


@dataclass
class CallRecord:
    """Catatan satu panggilan (satu percobaan berhasil atau panggilan gagal)."""

    provider: str
    model: str
    latency_s: float  # total termasuk retry dan jeda backoff
    ok: bool
    attempts: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    thought_tokens: int | None = None
    structured_mode: str = "teks"  # "schema" bila skema JSON diteruskan ke server
    error: str = ""  # hanya jenis dan status galat, sudah disamarkan
    rate_limited: int = 0  # jumlah galat 429 yang dialami


class LLMProvider(ABC):
    """Antarmuka penyedia LLM: satu metode `generate`."""

    name: str = "abstrak"
    model: str = ""

    def __init__(self) -> None:
        self.records: list[CallRecord] = []

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any] | None = None,
    ) -> str:
        """
        Kirim prompt dan kembalikan teks keluaran model.

        `json_schema` (opsional) meminta keluaran JSON sesuai skema bila
        penyedia mendukungnya. Pemanggil tetap wajib memvalidasi keluaran.
        Melempar `LLMError` (pesan sudah disamarkan) bila gagal.
        """

    def _log(self, rec: CallRecord) -> None:
        self.records.append(rec)
        logger.info(
            "llm provider=%s model=%s ok=%s attempts=%d latensi=%.2fs token_in=%s "
            "token_out=%s token_pikir=%s mode=%s 429=%d%s",
            rec.provider, rec.model, rec.ok, rec.attempts, rec.latency_s,
            rec.input_tokens, rec.output_tokens, rec.thought_tokens,
            rec.structured_mode, rec.rate_limited,
            f" galat={rec.error}" if rec.error else "",
        )
