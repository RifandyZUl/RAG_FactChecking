"""Hierarki galat panggilan LLM (pesan sudah disamarkan oleh penyedia)."""


class LLMError(Exception):
    """Panggilan LLM gagal setelah penanganan galat; pesan sudah disamarkan."""

    def __init__(self, message: str, retry_after_s: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s


class LLMConfigError(LLMError):
    """Konfigurasi hilang atau tidak valid (mis. kunci API belum diisi)."""


class LLMQuotaExhaustedError(LLMError):
    """
    Kuota habis dan retry tidak akan menolong (mis. kuota harian). Pemanggil
    sebaiknya menghentikan seluruh proses, bukan sekadar menandai satu kueri gagal.
    """
