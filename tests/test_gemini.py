"""Uji penyedia Gemini (llm.gemini): retry, klasifikasi 429, throttling proaktif, anggaran.
"""

from pathlib import Path
from typing import Any

import httpx
import pytest
from _fakes import (
    FakeHTTPError,
    FakeInteraction,
    FakeInteractions,
    attach_client,
    attach_fake_client,
    make_gemini,
    quota_body,
)


def no_sleep(_seconds: float) -> None:
    """Pengganti time.sleep: jangan benar-benar menunggu."""


def no_env(_path: Any = None) -> None:
    """Pengganti load_env: .env asli tidak boleh ikut terbaca."""


def test_gemini_provider_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    import llm
    import llm.gemini as lp
    from llm import LLMConfigError, LLMError
    from llm.secrets import redact

    slept: list[float] = []

    def record_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(lp.time, "sleep", record_sleep)  # jangan benar-benar menunggu

    # 429 dengan retryDelay -> menunggu sesuai saran, lalu sukses; token dicatat
    body = '{"error": {"details": [{"retryDelay": "3s"}]}}'
    p, fake, _ = make_gemini([FakeHTTPError(429, body), FakeInteraction('{"a": 1}')])
    out = p.generate("sys", "usr", json_schema={"type": "object"})
    rec = p.records[-1]
    assert out == '{"a": 1}' and rec.ok and rec.attempts == 2 and rec.rate_limited == 1
    assert (rec.input_tokens, rec.output_tokens, rec.thought_tokens) == (11, 7, 3)
    assert 3.0 <= slept[-1] <= 4.1, "harus menunggu sesuai retryDelay 3s (+jitter)"
    assert fake.calls[0]["store"] is False and fake.calls[0]["timeout"] == 90.0
    assert fake.calls[0]["response_format"]["mime_type"] == "application/json"
    assert fake.calls[0]["system_instruction"] == "sys" and fake.calls[0]["input"] == "usr"

    # 429 terus -> menyerah setelah 4 percobaan (1 awal + 3 retry) dengan LLMError (proses tidak mati diam-diam)
    p, fake, _ = make_gemini([FakeHTTPError(429)])
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError:
        pass
    assert len(fake.calls) == 4 and p.records[-1].rate_limited == 4

    # Saran tunggu sangat lama (kuota harian) -> berhenti tanpa tidur berjam-jam
    p, fake, _ = make_gemini([FakeHTTPError(429, '{"retryDelay": "3600s"}')])
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError as e:
        assert e.retry_after_s == 3600 and len(fake.calls) == 1

    # 400 dengan skema server -> turun ke mode teks sekali
    p, fake, _ = make_gemini([FakeHTTPError(400), FakeInteraction("ok")])
    assert p.generate("s", "u", json_schema={"type": "object"}) == "ok"
    assert "response_format" in fake.calls[0] and "response_format" not in fake.calls[1]
    assert p.records[-1].structured_mode == "teks"

    # 401: tidak di-retry, kunci tidak bocor ke pesan galat
    fake_key = "AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234"
    p, fake, key = make_gemini([FakeHTTPError(401, message=f"API key {fake_key} tidak valid")])
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError as e:
        assert key not in str(e) and "KUNCI-DISAMARKAN" in str(e)
    assert len(fake.calls) == 1

    # Status tidak completed -> LLMError
    p, fake, _ = make_gemini([FakeInteraction("potongan", status="incomplete")])
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError:
        assert p.records[-1].ok is False

    # redact dan konfigurasi
    assert "AIzaSy" not in redact("x AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ012345 y")
    # .env asli (kini berisi kunci) tidak boleh ikut terbaca oleh uji ini
    old = lp.os.environ.pop("GEMINI_API_KEY", None)
    monkeypatch.setattr(lp, "load_env", no_env)
    try:
        lp.GeminiProvider(api_key="")
        raise AssertionError("seharusnya LLMConfigError")
    except LLMConfigError:
        pass
    finally:
        if old is not None:
            lp.os.environ["GEMINI_API_KEY"] = old
    try:
        llm.get_provider("tidak-ada")
        raise AssertionError("seharusnya LLMConfigError")
    except LLMConfigError:
        pass


def test_provider_with_real_sdk_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Galat SDK ASLI (transport palsu, tanpa jaringan): membuktikan (1) retry internal SDK
    mati sehingga satu percobaan = satu permintaan, (2) 429 harian tidak di-retry,
    (3) 429 per menit di-retry maksimal 3 kali, (4) saran server terbaca dari galat nyata
    (body berupa dict, header di err.response), bukan dari fake berbentuk lain.
    """
    from google import genai
    from google.genai import types

    import llm.gemini as lp
    from llm import LLMError, LLMQuotaExhaustedError

    monkeypatch.setattr(lp.time, "sleep", no_sleep)  # jangan menunggu sungguhan

    def provider_for(
        status: int, body: dict[str, Any], headers: dict[str, str]
    ) -> tuple[lp.GeminiProvider, list[httpx.Request]]:
        calls: list[httpx.Request] = []

        def handler(req: httpx.Request) -> httpx.Response:
            calls.append(req)
            return httpx.Response(status, headers=headers, json=body)

        p = lp.GeminiProvider(api_key="AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234", min_interval_s=0,
                             proactive=False)
        hx = httpx.Client(transport=httpx.MockTransport(handler))
        client = genai.Client(api_key="AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234",
                              http_options=types.HttpOptions(httpx_client=hx))
        attach_client(p, client)
        assert lp.disable_sdk_retry(client), "retry internal SDK harus bisa dimatikan"
        return p, calls

    # harian: satu permintaan saja, jenis kuota habis
    p, calls = provider_for(429, quota_body("GenerateRequestsPerDayPerProjectPerModel-FreeTier"),
                            {"retry-after": "5"})
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMQuotaExhaustedError")
    except LLMQuotaExhaustedError as e:
        assert "harian" in str(e)
    assert len(calls) == 1, f"kuota harian tidak boleh di-retry (permintaan: {len(calls)})"

    # per menit: 1 awal + 3 retry = 4 permintaan, bukan dikali retry SDK
    p, calls = provider_for(429, quota_body("GenerateRequestsPerMinutePerProjectPerModel-FreeTier"),
                            {"retry-after": "5"})
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError as e:
        assert not isinstance(e, LLMQuotaExhaustedError)
    assert len(calls) == 4, f"permintaan: {len(calls)}"
    assert p.records[-1].rate_limited == 4 and "per_menit" in p.records[-1].error

    # saran server terbaca dari galat nyata; > batas -> kuota habis tanpa retry
    p, calls = provider_for(429, quota_body("GenerateRequestsPerMinutePerProjectPerModel-FreeTier"),
                            {"retry-after": "3600"})
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMQuotaExhaustedError")
    except LLMQuotaExhaustedError as e:
        assert e.retry_after_s == 3600
    assert len(calls) == 1

    # 429 tanpa rincian: diperlakukan sementara, tetap dibatasi 3 retry
    p, calls = provider_for(
        429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "coba lagi nanti"}}, {}
    )
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError as e:
        # isi galat yang tak terklasifikasi harus tampil di pesan, bukan disembunyikan
        assert "RESOURCE_EXHAUSTED" in str(e) and "coba lagi nanti" in str(e), str(e)
        assert "tidak ada quotaId" in str(e)
    assert len(calls) == 4 and "tidak_diketahui" in p.records[-1].error


def test_provider_proactive_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    import tempfile

    import llm.gemini as lp
    from llm import GeminiProvider, LLMConfigError, LLMQuotaExhaustedError
    from llm.ledger import DailyLedger
    from llm.limits import ModelLimits

    key = "AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234"
    monkeypatch.setattr(lp.time, "sleep", no_sleep)
    with tempfile.TemporaryDirectory() as d:
        ledger = DailyLedger("gemini-3.8-flash", Path(d) / "l.json")
        p = GeminiProvider(api_key=key, model="gemini-3.8-flash", min_interval_s=0,
                           limits=ModelLimits(rpm=1000, tpm=10**7, rpd=3), ledger=ledger)
        # 429 per menit lalu sukses: KEDUA permintaan terhitung di anggaran harian
        body = quota_body("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "1s")
        fake = FakeInteractions([FakeHTTPError(429, body), FakeInteraction("a"),
                                  FakeInteraction("b"), FakeInteraction("c")])
        attach_fake_client(p, fake)
        assert p.generate("s", "u") == "a"
        assert ledger.used_today() == 2 and len(fake.calls) == 2
        assert p.generate("s", "u") == "b"
        assert ledger.used_today() == 3
        # anggaran habis: tidak ada permintaan dikirim sama sekali
        try:
            p.generate("s", "u")
            raise AssertionError("seharusnya LLMQuotaExhaustedError")
        except LLMQuotaExhaustedError as e:
            assert "3/3" in str(e)
        assert len(fake.calls) == 3, "permintaan tidak boleh dikirim saat anggaran habis"

    # thinking_level tidak didukung model -> galat konfigurasi, bukan 400 dari server
    for model, level, ok in [
        ("gemini-3.8-flash", "minimal", False), ("gemini-3.8-flash", "medium", True),
        ("gemini-3.5-flash-lite", "minimal", True), ("gemma-4-31b-it", "medium", False),
        ("gemma-4-26b-a4b-it", "minimal", True),
    ]:
        try:
            GeminiProvider(api_key=key, model=model, thinking_level=level, proactive=False)
            assert ok, f"{model}/{level} seharusnya ditolak"
        except LLMConfigError:
            assert not ok, f"{model}/{level} seharusnya diterima"


def test_model_version_info_falls_back_to_sdk_version_when_api_omits_it() -> None:
    """
    Respons Interactions API asli (dan FakeInteraction, yang meniru bentuknya) tidak punya
    field versi checkpoint -- lihat model_version_info() di src/llm/base.py. Fallback harus
    memakai versi SDK terpasang dan menyertakan catatan eksplisit.
    """
    p, _fake, _key = make_gemini([FakeInteraction("ok")])
    assert p.generate("s", "u") == "ok"
    info = p.model_version_info()
    assert info["model_id"] == p.model
    assert info["sumber_versi"] == "sdk_terpasang"
    assert info["sdk_version"] and info["sdk_version"] != "tidak diketahui"
    assert "checkpoint" in info["catatan"]
    assert "model_version" not in info


def test_model_version_info_uses_api_metadata_when_present() -> None:
    """Bila suatu saat API mengisi versi checkpoint pada respons, itu yang harus dipakai."""
    interaction = FakeInteraction("ok")
    interaction.model_version = "models/gemma-4-31b-it-001"
    p, _fake, _key = make_gemini([interaction])
    assert p.generate("s", "u") == "ok"
    info = p.model_version_info()
    assert info["model_version"] == "models/gemma-4-31b-it-001"
    assert info["sumber_versi"] == "metadata_respons_api"
    assert "sdk_version" not in info


def test_model_version_info_before_any_call_falls_back() -> None:
    """Sebelum ada panggilan sukses, tidak ada CallRecord untuk dibaca -> fallback SDK juga."""
    p, _fake, _key = make_gemini([FakeInteraction("ok")])
    info = p.model_version_info()
    assert info["sumber_versi"] == "sdk_terpasang"
