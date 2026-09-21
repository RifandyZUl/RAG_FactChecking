"""Uji penyedia Gemini (llm.gemini): retry, klasifikasi 429, throttling proaktif, anggaran.
"""

from pathlib import Path

from _fakes import FakeHTTPError, FakeInteraction, FakeInteractions, make_gemini, quota_body


def test_gemini_provider_error_handling(monkeypatch) -> None:
    import llm
    import llm.gemini as lp
    from llm import LLMConfigError, LLMError
    from llm.secrets import redact

    slept: list[float] = []
    monkeypatch.setattr(lp.time, "sleep", lambda s: slept.append(s))  # jangan benar-benar menunggu

    # 429 dengan retryDelay -> menunggu sesuai saran, lalu sukses; token dicatat
    body = '{"error": {"details": [{"retryDelay": "3s"}]}}'
    p, fake, _ = make_gemini([FakeHTTPError(429, body), FakeInteraction('{"a": 1}')])
    out = p.generate("sys", "usr", json_schema={"type": "object"})
    rec = p.records[-1]
    assert out == '{"a": 1}' and rec.ok and rec.attempts == 2 and rec.rate_limited == 1
    assert (rec.input_tokens, rec.output_tokens, rec.thought_tokens) == (11, 7, 3)
    assert 3.0 <= slept[-1] <= 4.1, "harus menunggu sesuai retryDelay 3s (+jitter)"
    assert fake.calls[0]["store"] is False and fake.calls[0]["timeout"] == lp.REQUEST_TIMEOUT_S
    assert fake.calls[0]["response_format"]["mime_type"] == "application/json"
    assert fake.calls[0]["system_instruction"] == "sys" and fake.calls[0]["input"] == "usr"

    # 429 terus -> menyerah setelah MAX_ATTEMPTS dengan LLMError (proses tidak mati diam-diam)
    p, fake, _ = make_gemini([FakeHTTPError(429)])
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError:
        pass
    assert len(fake.calls) == lp.MAX_ATTEMPTS and p.records[-1].rate_limited == lp.MAX_ATTEMPTS

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
    p, fake, key = make_gemini([FakeHTTPError(401, message=f"API key {'AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234'} tidak valid")])
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
    monkeypatch.setattr(lp, "load_env", lambda path=None: None)
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


def test_provider_with_real_sdk_errors(monkeypatch) -> None:
    """
    Galat SDK ASLI (transport palsu, tanpa jaringan): membuktikan (1) retry internal SDK
    mati sehingga satu percobaan = satu permintaan, (2) 429 harian tidak di-retry,
    (3) 429 per menit di-retry maksimal 3 kali, (4) saran server terbaca dari galat nyata
    (body berupa dict, header di err.response), bukan dari fake berbentuk lain.
    """
    import httpx
    from google import genai
    from google.genai import types

    import llm.gemini as lp
    from llm import LLMError, LLMQuotaExhaustedError

    monkeypatch.setattr(lp.time, "sleep", lambda s: None)  # jangan menunggu sungguhan

    def provider_for(status: int, body: dict, headers: dict) -> tuple[lp.GeminiProvider, list]:
        calls: list = []

        def handler(req: httpx.Request) -> httpx.Response:
            calls.append(req)
            return httpx.Response(status, headers=headers, json=body)

        p = lp.GeminiProvider(api_key="AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234", min_interval_s=0,
                             proactive=False)
        hx = httpx.Client(transport=httpx.MockTransport(handler))
        p._client = genai.Client(api_key="AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234",
                                 http_options=types.HttpOptions(httpx_client=hx))
        assert lp.disable_sdk_retry(p._client), "retry internal SDK harus bisa dimatikan"
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

    # per menit: 1 awal + 3 retry = MAX_ATTEMPTS permintaan, bukan dikali retry SDK
    p, calls = provider_for(429, quota_body("GenerateRequestsPerMinutePerProjectPerModel-FreeTier"),
                            {"retry-after": "5"})
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError as e:
        assert not isinstance(e, LLMQuotaExhaustedError)
    assert len(calls) == lp.MAX_ATTEMPTS == 4, f"permintaan: {len(calls)}"
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
    assert len(calls) == lp.MAX_ATTEMPTS and "tidak_diketahui" in p.records[-1].error


def test_provider_proactive_budget(monkeypatch) -> None:
    import tempfile
    from types import SimpleNamespace

    import llm.gemini as lp
    from llm import GeminiProvider, LLMConfigError, LLMQuotaExhaustedError
    from llm.ledger import DailyLedger
    from llm.limits import ModelLimits

    key = "AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234"
    monkeypatch.setattr(lp.time, "sleep", lambda s: None)
    with tempfile.TemporaryDirectory() as d:
        ledger = DailyLedger("gemini-3.8-flash", Path(d) / "l.json")
        p = GeminiProvider(api_key=key, model="gemini-3.8-flash", min_interval_s=0,
                           limits=ModelLimits(rpm=1000, tpm=10**7, rpd=3), ledger=ledger)
        # 429 per menit lalu sukses: KEDUA permintaan terhitung di anggaran harian
        body = quota_body("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "1s")
        fake = FakeInteractions([FakeHTTPError(429, body), FakeInteraction("a"),
                                  FakeInteraction("b"), FakeInteraction("c")])
        p._client = SimpleNamespace(interactions=fake)
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
