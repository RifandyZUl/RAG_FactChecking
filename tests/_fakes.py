"""Objek palsu bersama untuk uji (bukan uji; tidak dikumpulkan pytest).
"""

from pathlib import Path

import requests

import scraping.client as scraping_client


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

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.calls = 0

    def get(self, url: str, timeout: float) -> FakeResponse:
        assert timeout == scraping_client.TIMEOUT, "timeout eksplisit 45 dtk wajib dipakai"
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

    def __init__(self, outputs: list) -> None:
        self.outputs = list(outputs)
        self.records: list = []
        self.prompts: list[str] = []

    def generate(self, system_prompt: str, user_prompt: str, json_schema=None) -> str:
        self.prompts.append(user_prompt)
        item = self.outputs.pop(0) if len(self.outputs) > 1 else self.outputs[0]
        if isinstance(item, Exception):
            raise item
        return item


def make_hit(aid: str, label: str = "SALAH", refs: list[str] | None = None):
    from retriever import ArticleHit

    return ArticleHit(
        article_id=aid, title=f"Judul {aid}", url=f"https://turnbackhoax.id/articles/{aid}-x",
        label=label, score=0.6, best_section="narasi",
        references=refs if refs is not None else [f"https://sumber-sahih.example/{aid}"],
        date="01/01/2026", narasi=f"Narasi {aid}", kesimpulan=f"Kesimpulan {aid}",
    )


def llm_json(**kw) -> str:
    import json as _json

    base = {"artikel_terpilih": "", "klaim_sama": False, "alasan": "", "klarifikasi": ""}
    base.update(kw)
    return _json.dumps(base)


class FakeHTTPError(Exception):
    """Meniru GenAiError: status_code, body, headers, message."""

    def __init__(self, status: int, body: str = "", message: str = "galat", headers=None) -> None:
        super().__init__(message)
        self.status_code, self.body, self.message = status, body, message
        self.headers = headers or {}


class FakeInteraction:
    def __init__(self, text="{}", status="completed") -> None:
        from types import SimpleNamespace

        self.output_text, self.status = text, status
        self.usage = SimpleNamespace(total_input_tokens=11, total_output_tokens=7, total_thought_tokens=3)


class FakeInteractions:
    def __init__(self, script: list) -> None:
        self.script, self.calls = list(script), []

    def create(self, **kw):
        self.calls.append(kw)
        item = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(item, Exception):
            raise item
        return item


def make_gemini(script: list):
    from types import SimpleNamespace

    from llm import GeminiProvider

    key = "AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234"
    p = GeminiProvider(api_key=key, min_interval_s=0, proactive=False)
    fake = FakeInteractions(script)
    p._client = SimpleNamespace(interactions=fake)
    return p, fake, key


def quota_body(quota_id: str, retry_delay: str = "30s") -> dict:
    """Bentuk galat 429 Gemini (QuotaFailure + RetryInfo) seperti pada dokumentasi galat Google."""
    return {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
         "violations": [{"quotaMetric": "generate_content_free_tier_requests", "quotaId": quota_id}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay}]}}
