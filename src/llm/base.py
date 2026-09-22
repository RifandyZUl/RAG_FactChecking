"""
Antarmuka penyedia LLM dan catatan panggilan.

Pipeline hanya bergantung pada `LLMProvider.generate`; penyedia dipilih lewat konfigurasi.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
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
    model_version: str | None = None  # versi/checkpoint dari metadata respons API, bila API mengungkapnya


class LLMProvider(ABC):
    """Antarmuka penyedia LLM: satu metode `generate`."""

    name: str = "abstrak"
    model: str = ""
    sdk_version: str = ""  # diisi subclass (mis. versi paket SDK terpasang); "" bila tidak dilacak

    def __init__(self) -> None:
        self.records: list[CallRecord] = []

    def model_version_info(self) -> dict[str, Any]:
        """
        Metadata versi model untuk jejak audit (mis. metadata kandidat set uji).

        Diutamakan versi checkpoint dari metadata respons API panggilan sukses terakhir
        (`CallRecord.model_version`), bila penyedia mengisinya. Provider Gemini lewat
        Interactions API (google-genai 2.24) TIDAK mengisinya -- lihat
        `.venv/Lib/site-packages/google/genai/_gaos/types/interactions/model.py`: field
        `model` pada respons hanya berisi ID model (literal union), tanpa versi checkpoint.
        Bila tidak tersedia, dicatat versi SDK terpasang + ID model + tanggal sebagai
        pengganti, dengan catatan eksplisit bahwa ini BUKAN versi checkpoint model.
        """
        last_ok = next((r for r in reversed(self.records) if r.ok), None)
        api_version = last_ok.model_version if last_ok else None
        info: dict[str, Any] = {
            "model_id": self.model,
            "tanggal": datetime.now(timezone.utc).date().isoformat(),
        }
        if api_version:
            info["model_version"] = api_version
            info["sumber_versi"] = "metadata_respons_api"
        else:
            info["sdk_version"] = self.sdk_version or "tidak diketahui"
            info["sumber_versi"] = "sdk_terpasang"
            info["catatan"] = (
                "API tidak mengungkap versi checkpoint model pada respons; versi SDK "
                "dicatat sebagai pengganti, BUKAN versi checkpoint model itu sendiri."
            )
        return info

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
