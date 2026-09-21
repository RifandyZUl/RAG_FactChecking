"""
Abstraksi penyedia LLM.

Pipeline generasi hanya bergantung pada antarmuka `LLMProvider`, sehingga
penyedia dan model bisa diganti lewat konfigurasi (`LLM_PROVIDER` di `.env`)
tanpa menulis ulang pipeline. Alasannya: tier gratis dapat memperketat batas
tanpa pemberitahuan atau berhenti total, dan tahap evaluasi perlu
membandingkan beberapa model (mis. model juri yang berbeda dari generator).

Kunci API dibaca dari `.env`/lingkungan dan TIDAK PERNAH dicetak: semua teks
galat dan log melewati `redact()`.
"""

import json
import logging
import os
import random
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rate_limit import DailyLedger, ModelLimits, RateLimiter, estimate_tokens, limits_for

PROJECT_ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger("llm")

DEFAULT_PROVIDER = "gemini"
# Flash stabil terbaru pada halaman model Google (diperbarui 2026-09-17);
# lihat CLAUDE.md untuk sumber dan batas kuota. Dapat diganti lewat LLM_MODEL.
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"

MAX_ATTEMPTS = 4  # percobaan total per panggilan (1 awal + maksimal 3 retry)
BACKOFF_BASE_S = 2.0
BACKOFF_MAX_S = 60.0
# Bila server meminta menunggu lebih lama dari ini, anggap kuota habis dan
# berhenti dengan galat jelas, bukan tidur berjam-jam.
MAX_HINTED_WAIT_S = 120.0
REQUEST_TIMEOUT_S = 90.0


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
        json_schema: dict | None = None,
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


def _error_payload(err: Any) -> Any:
    """Isi JSON galat HTTP. Pada SDK terpasang `body` berupa dict; str diterima juga."""
    body = getattr(err, "body", None)
    if isinstance(body, str) and body:
        try:
            return json.loads(body)
        except ValueError:
            return None
    return body


def _error_headers(err: Any) -> Any:
    """Header respons: `err.headers` bila ada, kalau tidak `err.response.headers`."""
    headers = getattr(err, "headers", None)
    if headers is None:
        headers = getattr(getattr(err, "response", None), "headers", None)
    return headers


def _hinted_delay_s(err: Any) -> float | None:
    """Ambil saran waktu tunggu dari galat 429: Retry-After atau RetryInfo.retryDelay."""
    headers = _error_headers(err)
    if headers is not None:
        ra = headers.get("retry-after")
        if ra and re.fullmatch(r"\d+(\.\d+)?", ra.strip()):
            return float(ra)
    stack = [_error_payload(err)]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            rd = cur.get("retryDelay")
            if isinstance(rd, str):
                m = re.fullmatch(r"(\d+(?:\.\d+)?)s", rd.strip())
                if m:
                    return float(m.group(1))
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def classify_429(err: Any) -> str:
    """
    Jenis batas pada galat 429: "harian", "per_menit", atau "tidak_diketahui".

    Dibaca dari `quotaId` pada rincian QuotaFailure (mis. ...PerDayPerProjectPer
    Model-FreeTier). Bila ada batas harian di antara pelanggaran, hasilnya "harian"
    karena itu yang mengikat. Format ini dikenal dari galat Gemini API umumnya;
    belum diamati langsung pada akun ini (lihat CLAUDE.md).
    """
    ids: list[str] = []
    stack = [_error_payload(err)]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for key in ("quotaId", "quotaMetric"):
                if isinstance(cur.get(key), str):
                    ids.append(cur[key])
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    joined = " ".join(ids).lower()
    if "perday" in joined or "per_day" in joined:
        return "harian"
    if "perminute" in joined or "per_minute" in joined:
        return "per_menit"
    return "tidak_diketahui"


def disable_sdk_retry(client: Any) -> bool:
    """
    Matikan retry internal SDK, agar retry hanya terjadi di `generate` dan tercatat.

    SDK terpasang (Interactions, google-genai 2.24) secara bawaan mengulang 429/5xx
    sampai 3 kali sambil menunggu `Retry-After` tanpa batas atas, tanpa log: satu
    "percobaan" kita bisa menghabiskan menit dan mengirim 4 permintaan (diukur dengan
    transport palsu, bukan server). Opsi publik `retry_options.attempts` tidak bisa
    menurunkannya di bawah 1 retry, jadi konfigurasi internal diganti. Mengembalikan
    False (dengan peringatan) bila SDK berubah bentuk.
    """
    try:
        from google.genai._gaos import utils as gaos_utils

        client.interactions.sdk_configuration.retry_config = gaos_utils.RetryConfig(
            "none", None, False
        )
        return True
    except (ImportError, AttributeError) as e:
        logger.warning("Retry internal SDK TIDAK bisa dimatikan (%s): jeda dan jumlah "
                       "permintaan sebenarnya dapat melebihi yang tercatat.", type(e).__name__)
        return False


# Nilai thinking_level yang didukung, dari https://ai.google.dev/gemini-api/docs/thinking
# (diambil 2026-09-21). Model di luar tabel tidak divalidasi. Gemma 4: hanya
# "high" (aktif) atau "minimal" (nonaktif) menurut dokumentasi Gemma di Gemini API.
_ALL_LEVELS = {"minimal", "low", "medium", "high"}


def supported_thinking_levels(model: str) -> set[str] | None:
    if model.startswith("gemma-4"):
        return {"minimal", "high"}
    if "flash-lite" in model:
        return _ALL_LEVELS
    if model == "gemini-3.8-flash":
        return {"low", "medium", "high"}
    return None


_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_TRANSIENT_NAMES = ("Timeout", "Connect", "Network", "RemoteProtocol", "ReadError")


class GeminiProvider(LLMProvider):
    """
    Gemini lewat Interactions API pada SDK `google-genai`
    (`client.interactions.create`, sesuai dokumentasi resmi Google AI Studio).
    """

    name = "gemini"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        thinking_level: str | None = None,
        max_output_tokens: int = 8192,
        min_interval_s: float | None = None,
        proactive: bool = True,
        limits: ModelLimits | None = None,
        ledger: DailyLedger | None = None,
    ) -> None:
        super().__init__()
        load_env()
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            raise LLMConfigError(
                "GEMINI_API_KEY belum diisi. Buat berkas .env di root proyek "
                "(lihat .env.example) atau set variabel lingkungan."
            )
        self.model = model or os.environ.get("LLM_MODEL") or DEFAULT_GEMINI_MODEL
        self.thinking_level = thinking_level or os.environ.get("LLM_THINKING_LEVEL", "medium")
        allowed = supported_thinking_levels(self.model)
        if allowed is not None and self.thinking_level not in allowed:
            raise LLMConfigError(
                f"thinking_level '{self.thinking_level}' tidak didukung {self.model}; "
                f"pilihan: {sorted(allowed)} (atur LLM_THINKING_LEVEL)."
            )
        self.max_output_tokens = max_output_tokens
        # Throttling proaktif: RPM/TPM per model + anggaran harian (buku besar lokal).
        self.limits = (limits or limits_for(self.model)) if proactive else None
        self.limiter = RateLimiter(self.limits) if self.limits else None
        self.ledger = (ledger or DailyLedger(self.model)) if self.limits else None
        if proactive and self.limits is None:
            logger.warning("Batas kuota model %s tidak dikenal: throttling proaktif dan "
                           "anggaran harian NONAKTIF (isi LLM_RPM/LLM_TPM/LLM_RPD).", self.model)
        self.min_interval_s = (
            min_interval_s if min_interval_s is not None
            else float(os.environ.get("LLM_MIN_INTERVAL_S", "4"))
        )
        self._last_call_end = 0.0

        from google import genai  # impor malas: tidak wajib untuk uji offline

        self._client = genai.Client(api_key=self._api_key)
        self.sdk_retry_disabled = disable_sdk_retry(self._client)

    # -- utilitas ---------------------------------------------------------
    def _safe(self, text: str) -> str:
        return redact(text, (self._api_key,))

    def _pace(self) -> None:
        """Jeda minimum antar-panggilan agar tidak mendorong batas RPM."""
        wait = self.min_interval_s - (time.monotonic() - self._last_call_end)
        if wait > 0:
            time.sleep(wait)

    def _before_call(self, est_tokens: int, t_start: float, attempt: int, mode: str) -> None:
        """Tahan permintaan sampai aman (RPM/TPM) dan catat ke anggaran harian."""
        self._pace()
        if self.limiter is None or self.ledger is None or self.limits is None:
            return
        used = self.ledger.used_today()
        if used >= self.limits.rpd:
            self._log(CallRecord(self.name, self.model, time.monotonic() - t_start, False,
                                 attempt - 1, structured_mode=mode, error="anggaran-lokal-habis"))
            reset = self.ledger.next_reset().astimezone().strftime("%Y-%m-%d %H:%M %Z")
            raise LLMQuotaExhaustedError(
                f"Anggaran harian {self.model} habis menurut buku besar lokal "
                f"({used}/{self.limits.rpd} permintaan); tidak ada permintaan dikirim. "
                f"Reset: {reset}."
            )
        try:
            waited = self.limiter.acquire(est_tokens)
        except ValueError as e:
            raise LLMError(str(e)) from None
        if waited >= 1.0:
            logger.info("throttling proaktif: menunggu %.1f dtk (RPM %d, TPM %d)",
                        waited, self.limits.rpm, self.limits.tpm)
        self.ledger.add(1)  # dihitung sebelum dikirim: hasil akhir permintaan tak dijamin terlihat

    def _create(self, system_prompt: str, user_prompt: str, json_schema: dict | None) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": user_prompt,
            "system_instruction": system_prompt,
            "store": False,  # jangan menyimpan interaksi di sisi Google
            "generation_config": {
                "thinking_level": self.thinking_level,
                "max_output_tokens": self.max_output_tokens,
            },
            "timeout": REQUEST_TIMEOUT_S,
        }
        if json_schema is not None:
            kwargs["response_format"] = {
                "type": "text",
                "mime_type": "application/json",
                "schema": json_schema,
            }
        return self._client.interactions.create(**kwargs)

    # -- antarmuka --------------------------------------------------------
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict | None = None,
    ) -> str:
        t_start = time.monotonic()
        rate_limited = 0
        mode = "schema" if json_schema is not None else "teks"
        last_error = ""
        est_tokens = estimate_tokens(system_prompt, user_prompt)

        for attempt in range(1, MAX_ATTEMPTS + 1):
            self._before_call(est_tokens, t_start, attempt, mode)
            t_attempt = time.monotonic()
            try:
                interaction = self._create(
                    system_prompt, user_prompt, json_schema if mode == "schema" else None
                )
            except Exception as e:  # noqa: BLE001 - diklasifikasi di bawah, tidak ditelan
                self._last_call_end = time.monotonic()
                status = getattr(e, "status_code", None)
                last_error = f"{type(e).__name__} status={status}"

                # 400 saat memakai skema server: turunkan ke mode teks sekali saja
                if status == 400 and mode == "schema":
                    logger.warning("400 dengan skema server; mencoba ulang tanpa skema: %s",
                                   self._safe(str(getattr(e, "message", e))[:200]))
                    mode = "teks"
                    continue

                transient = status in _RETRYABLE_STATUS or (
                    status is None and any(t in type(e).__name__ for t in _TRANSIENT_NAMES)
                )
                if not transient:
                    self._log(CallRecord(self.name, self.model, time.monotonic() - t_start,
                                         False, attempt, structured_mode=mode,
                                         error=last_error, rate_limited=rate_limited))
                    raise LLMError(
                        f"Panggilan {self.name}/{self.model} ditolak ({last_error}): "
                        + self._safe(str(getattr(e, "message", e))[:300])
                    ) from None

                kind = ""
                if status == 429:
                    rate_limited += 1
                    kind = classify_429(e)
                    last_error += f" jenis={kind}"
                hinted = _hinted_delay_s(e)
                # Kuota harian: retry tidak akan berhasil, berhenti seketika.
                # Saran tunggu > MAX_HINTED_WAIT_S diperlakukan sama (tidak tidur berjam-jam).
                if kind == "harian" or (hinted is not None and hinted > MAX_HINTED_WAIT_S):
                    self._log(CallRecord(self.name, self.model, time.monotonic() - t_start,
                                         False, attempt, structured_mode=mode,
                                         error=last_error + " kuota-habis", rate_limited=rate_limited))
                    reason = ("kuota harian habis" if kind == "harian" else
                              f"server meminta menunggu {hinted:.0f} dtk")
                    raise LLMQuotaExhaustedError(
                        f"Kuota {self.name}/{self.model} habis ({reason}); tidak di-retry.",
                        retry_after_s=hinted,
                    ) from None
                if attempt == MAX_ATTEMPTS:
                    self._log(CallRecord(self.name, self.model, time.monotonic() - t_start,
                                         False, attempt, structured_mode=mode,
                                         error=last_error, rate_limited=rate_limited))
                    raise LLMError(
                        f"Panggilan {self.name}/{self.model} gagal setelah {attempt} "
                        f"percobaan ({last_error})."
                    ) from None
                backoff = min(BACKOFF_MAX_S, BACKOFF_BASE_S * 2 ** (attempt - 1))
                wait = (hinted if hinted is not None else backoff) + random.uniform(0, 1)
                logger.warning(
                    "[retry %d/%d] %s; panggilan berlangsung %.1f dtk; jeda sebelum retry "
                    "%.1f dtk (saran server: %s)",
                    attempt, MAX_ATTEMPTS - 1, last_error,
                    self._last_call_end - t_attempt, wait,
                    f"{hinted:.0f} dtk" if hinted is not None else "tidak ada")
                time.sleep(wait)
                continue

            self._last_call_end = time.monotonic()
            status_val = getattr(interaction, "status", None)
            text = getattr(interaction, "output_text", None)
            usage = getattr(interaction, "usage", None)
            rec = CallRecord(
                self.name, self.model, time.monotonic() - t_start, True, attempt,
                input_tokens=getattr(usage, "total_input_tokens", None),
                output_tokens=getattr(usage, "total_output_tokens", None),
                thought_tokens=getattr(usage, "total_thought_tokens", None),
                structured_mode=mode, rate_limited=rate_limited,
            )
            if self.limiter is not None:
                self.limiter.settle(rec.input_tokens)  # token nyata menggantikan perkiraan
            if status_val != "completed" or not text:
                rec.ok = False
                rec.error = f"status={status_val} teks_kosong={not text}"
                self._log(rec)
                raise LLMError(
                    f"Respons {self.name}/{self.model} tidak lengkap ({rec.error})."
                )
            self._log(rec)
            return self._safe(text)

        raise LLMError("tak tercapai")  # pragma: no cover


PROVIDERS: dict[str, type[LLMProvider]] = {"gemini": GeminiProvider}


def get_provider(name: str | None = None, **kwargs: Any) -> LLMProvider:
    """Buat penyedia dari konfigurasi: argumen `name` atau variabel LLM_PROVIDER."""
    load_env()
    key = (name or os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    if key not in PROVIDERS:
        raise LLMConfigError(f"LLM_PROVIDER '{key}' tidak dikenal; pilihan: {sorted(PROVIDERS)}")
    return PROVIDERS[key](**kwargs)
