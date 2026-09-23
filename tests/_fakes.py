"""Objek palsu bersama untuk uji (bukan uji; tidak dikumpulkan pytest).
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from llm import GeminiProvider
    from retriever import ArticleHit

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status: int = 200) -> None:
        self.text = text
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")


class FakeSession:
    """Session palsu: mengembalikan/melempar item berurutan dari `script`."""

    def __init__(self, script: list[Any]) -> None:
        self.script = list(script)
        self.calls = 0

    def get(self, url: str, timeout: float) -> FakeResponse:
        assert timeout == 45, "timeout eksplisit 45 dtk wajib dipakai (nilai literal, bukan dari konstanta)"
        self.calls += 1
        item = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(item, Exception):
            raise item
        return item


def fake_list_page(first_id: int) -> str:
    """Halaman daftar sintetis dengan 10 tautan artikel (untuk uji paginasi)."""
    links = "".join(
        f'<a href="https://turnbackhoax.id/articles/{first_id + i}-slug-{i}">x</a>'
        for i in range(10)
    )
    return f"<html><body>{links}</body></html>"


def read_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


class ScriptedProvider:
    """Penyedia palsu untuk uji generator: mengembalikan keluaran berurutan."""

    name = "scripted"
    model = ""
    sdk_version = "scripted-test"
    thinking_level = "medium"
    ledger = None  # sama seperti GeminiProvider(proactive=False): anggaran harian nonaktif
    limits = None

    def __init__(self, outputs: list[Any]) -> None:
        self.outputs = list(outputs)
        self.records: list[Any] = []
        self.prompts: list[str] = []

    def generate(self, system_prompt: str, user_prompt: str, json_schema: dict[str, Any] | None = None) -> str:
        self.prompts.append(user_prompt)
        item = self.outputs.pop(0) if len(self.outputs) > 1 else self.outputs[0]
        if isinstance(item, Exception):
            raise item
        return item

    def model_version_info(self) -> dict[str, Any]:
        """Sama seperti `LLMProvider.model_version_info`, tanpa panggilan API sungguhan."""
        return {
            "model_id": self.model,
            "tanggal": "2026-01-01",
            "sdk_version": self.sdk_version,
            "sumber_versi": "sdk_terpasang",
            "catatan": "ScriptedProvider palsu: tidak ada metadata respons API sungguhan.",
        }


def make_hit(aid: str, label: str = "SALAH", refs: list[str] | None = None) -> "ArticleHit":
    from retriever import ArticleHit

    return ArticleHit(
        article_id=aid, title=f"Judul {aid}", url=f"https://turnbackhoax.id/articles/{aid}-x",
        label=label, score=0.6, best_section="narasi",
        references=refs if refs is not None else [f"https://sumber-sahih.example/{aid}"],
        date="01/01/2026", narasi=f"Narasi {aid}", kesimpulan=f"Kesimpulan {aid}",
    )


def llm_json(**kw: Any) -> str:
    import json as _json

    base = {"artikel_terpilih": "", "klaim_sama": False, "alasan": "", "klarifikasi": ""}
    base.update(kw)
    return _json.dumps(base)


class FakeHTTPError(Exception):
    """Meniru GenAiError: status_code, body, headers, message."""

    def __init__(self, status: int, body: str | dict[str, Any] = "", message: str = "galat",
                 headers: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.status_code, self.body, self.message = status, body, message
        self.headers = headers or {}


class FakeInteraction:
    def __init__(self, text: str = "{}", status: str = "completed") -> None:
        from types import SimpleNamespace

        self.output_text, self.status = text, status
        self.usage = SimpleNamespace(total_input_tokens=11, total_output_tokens=7, total_thought_tokens=3)


class FakeInteractions:
    def __init__(self, script: list[Any]) -> None:
        self.script: list[Any] = list(script)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kw: Any) -> Any:
        self.calls.append(kw)
        item = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(item, Exception):
            raise item
        return item


def attach_client(provider: Any, client: Any) -> None:
    """Ganti klien SDK pada penyedia (atribut privat `_client`; hanya uji yang memasangnya)."""
    provider._client = client


def attach_fake_client(provider: Any, interactions: Any) -> None:
    """Pasang klien palsu pada penyedia (menggantikan genai.Client; hanya `.interactions` yang dipakai)."""
    from types import SimpleNamespace

    attach_client(provider, SimpleNamespace(interactions=interactions))


def make_gemini(script: list[Any]) -> "tuple[GeminiProvider, FakeInteractions, str]":
    from llm import GeminiProvider

    key = "AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234"
    p = GeminiProvider(api_key=key, min_interval_s=0, proactive=False)
    fake = FakeInteractions(script)
    attach_fake_client(p, fake)
    return p, fake, key


def quota_body(quota_id: str, retry_delay: str = "30s") -> dict[str, Any]:
    """Bentuk galat 429 Gemini (QuotaFailure + RetryInfo) seperti pada dokumentasi galat Google."""
    return {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
         "violations": [{"quotaMetric": "generate_content_free_tier_requests", "quotaId": quota_id}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay}]}}
