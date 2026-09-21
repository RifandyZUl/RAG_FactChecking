"""
Uji logika parsing scraper dengan HTML NYATA TurnBackHoax.

Fixture berasal dari cache hasil scraping (data/raw_html/) dan disalin ke
src/fixtures/ agar ikut ter-commit (data/raw_html/ di-gitignore dan bisa
berubah saat scraping ulang dengan force_refresh). HTML tiruan sebelumnya
dibuang karena dibuat dari asumsi struktur yang keliru dan tidak menangkap
dua cacat pada artikel nyata: kontainer salah dan tautan hoaks bocor ke
daftar referensi.
"""

import tempfile
from pathlib import Path

import requests

import scraping.client as scraping_client
from scraping.client import fetch_html
from scraping.discovery import discover_article_urls, is_valid_list_html
from scraping.links import blocked_reason, normalize_url
from scraping.parser import is_valid_article_html, parse_article

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

# id artikel -> URL asli (id dipakai sebagai nama berkas fixture)
ARTICLE_URLS = {
    "36738": "https://turnbackhoax.id/articles/36738-salah-ada-kebijakan-razia-kendaraan-dari-rumah-ke-rumah",
    "36737": "https://turnbackhoax.id/articles/36737-penipuan-tautan-pendaftaran-program-bantuan-lansia",
    "36731": "https://turnbackhoax.id/articles/36731-penipuan-tautan-pendaftaran-cek-kesehatan-gratis",
    "36730": "https://turnbackhoax.id/articles/36730-salah-ojol-dilarang-beli-pertalite",
    "36729": "https://turnbackhoax.id/articles/36729-salah-malaysia-laporkan-indonesia-ke-pbb-soal-karhutla",
}


def load(article_id: str) -> dict:
    """Parse fixture HTML nyata lewat jalur kode yang sama dengan scraper."""
    html = (FIXTURE_DIR / f"{article_id}.html").read_text(encoding="utf-8")
    art = parse_article(html, ARTICLE_URLS[article_id])
    assert art is not None, f"{article_id}: parse_article mengembalikan None"
    return art


def test_normalize_and_domain() -> None:
    assert normalize_url("  https://a.com/x?p=1#frag  ") == "https://a.com/x?p=1"
    assert normalize_url("https://a.com/x") == "https://a.com/x"

    # Arsip dan hosting gambar: selalu disaring, apa pun path-nya
    for u in [
        "https://archive.li/n2Rxw", "https://archive.ph/6Yd1j",
        "https://web.archive.org/web/2020/x", "http://archive.today/TwOTs",
        "https://archive.is/abc", "https://archive.vn/abc", "https://archive.md/HzI4C",
        "https://webarchive.io/archive/chaa/x", "https://ghostarchive.org/archive/F59Ye",
        "https://ibb.co.com/cKj7vmkf", "https://ibb.co/cKj7vmkf",
    ]:
        assert blocked_reason(u), f"seharusnya disaring: {u}"

    # Media sosial: disaring, baik postingan maupun beranda akun
    for u in [
        "https://vt.tiktok.com/ZSq9c6ky7/",
        "https://www.tiktok.com/@sindonews/video/7516875885891374343",
        "https://x.com/a/status/1", "https://twitter.com/a/status/1",
        "https://www.instagram.com/p/DdApnwrzvas/",
        "https://www.instagram.com/reel/DCQov8YyCgw/",
        "https://www.instagram.com/kemensosri/p/DXjyJ9gkZf_/",
        "https://web.facebook.com/photo/?fbid=1&set=a.2",
        "https://www.facebook.com/photo.php?fbid=1&set=pb.1",
        "https://www.facebook.com/share/1EDkBDGFdE",
        "https://web.facebook.com/khanza.khulfi/posts/pfbid02cKx",
        "https://www.youtube.com/watch?v=T7UMijc_ddI",
        "https://www.youtube.com/shorts/a3B204GdwtI", "https://youtu.be/abc",
        "https://www.threads.com/@bacotwakanda.id/post/DcgGDHyEkiA",
        # beranda akun: sengaja ikut disaring (penilaian akun resmi vs
        # penyebar hoaks ditunda ke Versi 2, lihat CLAUDE.md)
        "https://www.instagram.com/kemensetneg.ri/",
        "https://www.instagram.com/bank_brksyariah?igshid=YzAw",
        "https://x.com/brksyariahid",
        "https://web.facebook.com/bankriaukeprisyariah.id?mibextid=LQQJ4d&_rdc=1&_rdr",
        "https://www.tiktok.com/@binmas_penjaringan",
        "https://www.youtube.com/@kemenkes",
        "https://www.threads.com/@lowongankerja209",
    ]:
        assert blocked_reason(u), f"seharusnya disaring: {u}"

    # Tidak boleh salah cocok pada domain yang hanya berakhiran mirip
    assert blocked_reason("https://www.netflix.com/id") is None
    assert blocked_reason("https://www.cnnindonesia.com/a") is None
    assert blocked_reason("https://box.com/status/1") is None


def test_article_36738() -> None:
    """Kasus kebocoran: seksi Referensi asli memuat TikTok dan archive.li."""
    a = load("36738")
    assert a["label"] == "SALAH"
    assert a["narasi"] and a["penjelasan"], "seksi Narasi/Penjelasan kosong"
    assert a["kesimpulan"].startswith("Faktanya"), "isi Kesimpulan salah"

    tiktok = "https://vt.tiktok.com/ZSq9c6ky7/"
    archive = "https://archive.li/n2Rxw"

    # Wajib: tautan hoaks TIDAK boleh muncul di references (Aturan Wajib #1)
    assert tiktok not in a["references"], "TikTok bocor ke references"
    assert archive not in a["references"], "archive.li bocor ke references"
    assert not any("tiktok" in r or "archive.li" in r for r in a["references"])

    # Tetap tersimpan apa adanya di references_raw dan tercatat di filtered
    assert tiktok in a["references_raw"] and archive in a["references_raw"]
    filtered = {f["url"]: f["reasons"] for f in a["references_filtered"]}
    assert tiktok in filtered and archive in filtered
    assert any("claim_sources" in r for r in filtered[tiktok])
    assert any("tiktok.com" in r for r in filtered[tiktok])
    assert any("archive.li" in r for r in filtered[archive])
    assert len(filtered[tiktok]) == 2, "TikTok harus tercatat memenuhi kedua kriteria"

    # Rujukan sahih tetap ada, fragmen '#page2' sudah dibuang
    assert any("cnbcindonesia.com" in r for r in a["references"])
    assert any(r.startswith("https://www.kompas.com/cekfakta/") for r in a["references"])
    assert not any("#" in r for r in a["references"])

    # claim_sources tetap memuat sumber hoaks
    assert tiktok in a["claim_sources"]


def test_article_36729() -> None:
    a = load("36729")
    assert a["kesimpulan"].startswith("Faktanya, Malaysia tidak melaporkan")
    assert any("x.com" in c for c in a["claim_sources"]), "sumber klaim tidak terambil"
    assert not any("x.com" in r for r in a["references"])
    assert any("cnnindonesia.com" in r for r in a["references"])
    assert any("kompasiana.com" in r for r in a["references"])
    assert not any("goog_rewarded" in r for r in a["references_raw"]), \
        "fragmen #goog_rewarded tidak dibuang"


def test_article_36737() -> None:
    a = load("36737")
    assert not any("facebook.com" in r or "webarchive.io" in r for r in a["references"])
    assert any("kabar24.bisnis.com" in r for r in a["references"])


def test_all_fixtures_invariants() -> None:
    """Invarian yang harus berlaku pada setiap artikel nyata."""
    for article_id in ARTICLE_URLS:
        a = load(article_id)
        for key in ("narasi", "penjelasan", "kesimpulan"):
            assert a[key], f"{article_id}: seksi {key} kosong"

        claim = set(a["claim_sources"])
        for r in a["references"]:
            assert r not in claim, f"{article_id}: {r} ada di claim_sources"
            assert blocked_reason(r) is None, f"{article_id}: {r} seharusnya disaring"

        # Tidak ada tautan yang hilang: raw = references + filtered
        assert set(a["references_raw"]) == \
            set(a["references"]) | {f["url"] for f in a["references_filtered"]}, \
            f"{article_id}: references_raw tidak sama dengan references + filtered"

        for url in a["references_raw"] + a["claim_sources"]:
            assert "#" not in url and url == url.strip(), f"{article_id}: URL belum dinormalkan"


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


def test_html_validators() -> None:
    error_html = read_fixture("error_page.html")
    assert "Terjadi kesalahan saat mengambil data" in error_html
    assert not is_valid_article_html(error_html), "halaman galat lolos sbg artikel"
    assert not is_valid_list_html(error_html), "halaman galat lolos sbg daftar"
    assert is_valid_article_html(read_fixture("36738.html"))
    assert is_valid_list_html(read_fixture("list_page.html"))


def test_fetch_retries_error_page_and_skips_cache() -> None:
    """Halaman galat 200 di-retry, dan tidak pernah ditulis ke cache."""
    error_html = read_fixture("error_page.html")
    good_html = read_fixture("36738.html")
    scraping_client.time.sleep = lambda s: None  # jangan benar-benar menunggu backoff

    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "1.html"

        # galat dua kali lalu sukses -> 3 panggilan, cache berisi HTML sah
        sess = FakeSession([FakeResponse(error_html), FakeResponse(error_html),
                            FakeResponse(good_html)])
        html, net = fetch_html("u", sess, cache, validate=is_valid_article_html)
        assert html == good_html and net and sess.calls == 3
        assert cache.read_text(encoding="utf-8") == good_html

        # galat terus -> menyerah setelah 1 + MAX_RETRIES percobaan, cache TIDAK dibuat
        cache2 = Path(tmp) / "2.html"
        sess = FakeSession([FakeResponse(error_html)])
        html, _ = fetch_html("u", sess, cache2, validate=is_valid_article_html)
        assert html is None and sess.calls == scraping_client.MAX_RETRIES + 1
        assert not cache2.exists(), "halaman galat ter-cache"

        # cache lama yang rusak diabaikan dan diambil ulang
        cache3 = Path(tmp) / "3.html"
        cache3.write_text(error_html, encoding="utf-8")
        sess = FakeSession([FakeResponse(good_html)])
        html, net = fetch_html("u", sess, cache3, validate=is_valid_article_html)
        assert html == good_html and net and sess.calls == 1
        assert cache3.read_text(encoding="utf-8") == good_html

        # cache sah dipakai tanpa jaringan
        sess = FakeSession([FakeResponse(error_html)])
        html, net = fetch_html("u", sess, cache3, validate=is_valid_article_html)
        assert html == good_html and not net and sess.calls == 0


def test_fetch_retry_policy() -> None:
    """Retry hanya untuk timeout/koneksi; 404 tidak di-retry."""
    scraping_client.time.sleep = lambda s: None
    sess = FakeSession([requests.ReadTimeout("t"), requests.ConnectionError("c"),
                        FakeResponse("<html>ok</html>")])
    html, _ = fetch_html("u", sess)
    assert html == "<html>ok</html>" and sess.calls == 3

    sess = FakeSession([requests.ConnectionError("c")])
    html, _ = fetch_html("u", sess)
    assert html is None and sess.calls == scraping_client.MAX_RETRIES + 1

    sess = FakeSession([FakeResponse("nope", status=404)])
    html, _ = fetch_html("u", sess)
    assert html is None and sess.calls == 1, "404 tidak boleh di-retry"


def test_discover_not_fooled_by_error_page() -> None:
    """Halaman daftar galat di tengah paginasi di-retry, bukan dianggap akhir."""
    scraping_client.time.sleep = lambda s: None
    error_html = read_fixture("error_page.html")
    sess = FakeSession([
        FakeResponse(fake_list_page(1000)),   # halaman 1
        FakeResponse(error_html),             # halaman 2: galat, percobaan 1
        FakeResponse(error_html),             # percobaan 2
        FakeResponse(fake_list_page(2000)),   # halaman 2 akhirnya sah
    ])
    urls = discover_article_urls(sess, max_articles=20)
    assert len(urls) == 20, f"paginasi berhenti terlalu dini: {len(urls)} URL"
    assert sess.calls == 4

    # Galat sejak halaman 1 dan tak kunjung sah -> hasil kosong dengan pesan
    # eksplisit (fetch_html sudah mencoba 1 + MAX_RETRIES kali)
    sess = FakeSession([FakeResponse(error_html)])
    assert discover_article_urls(sess, max_articles=20) == []
    assert sess.calls == scraping_client.MAX_RETRIES + 1

    # Halaman daftar asli menghasilkan 10 URL
    sess = FakeSession([FakeResponse(read_fixture("list_page.html"))])
    assert len(discover_article_urls(sess, max_articles=10)) == 10


def test_aggregate_by_article() -> None:
    """Agregasi per artikel: skor tertinggi per artikel, tanpa duplikat artikel."""
    from chunker import encode_references
    from retriever import aggregate_by_article

    def meta(aid: str, section: str, refs: list[str]) -> dict:
        return {"article_id": aid, "title": f"T{aid}", "url": f"u{aid}", "label": "SALAH",
                "section": section, "references": encode_references(refs)}

    # jarak kosinus -> skor = 1 - jarak
    metas = [
        meta("A", "penjelasan", ["r1"]), meta("B", "narasi", []),
        meta("A", "narasi", ["r1"]), meta("A", "kesimpulan", ["r1"]),
        meta("B", "kesimpulan", []),
    ]
    dists = [0.30, 0.35, 0.50, 0.60, 0.20]
    hits = aggregate_by_article(metas, dists)
    assert [h.article_id for h in hits] == ["B", "A"], "urutan harus menurut skor tertinggi"
    b, a = hits
    assert abs(b.score - 0.80) < 1e-9 and b.best_section == "kesimpulan"
    assert abs(a.score - 0.70) < 1e-9 and a.best_section == "penjelasan"
    assert set(a.section_scores) == {"penjelasan", "narasi", "kesimpulan"}
    assert a.references == ["r1"], "references harus didekode dari metadata"
    assert len({h.article_id for h in hits}) == len(hits)


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


def test_generator_logic() -> None:
    from generator import AnswerGenerator, allowed_urls, find_urls, render
    from llm_provider import LLMError

    hits = [make_hit("100", "SALAH"), make_hit("200", "PARODI"), make_hit("300", "PENIPUAN", refs=[])]
    retrieve = lambda claim, k: hits[:k]  # noqa: E731

    # 1. Cocok: status dan rujukan dari METADATA; URL buatan LLM dibuang dan dihitung
    out = llm_json(artikel_terpilih="200", klaim_sama=True, alasan="mirip lihat http://palsu.example/a",
                   klarifikasi="Ini parodi. Lihat www.karangan.com dan kompas.com/berita.")
    ans = AnswerGenerator(ScriptedProvider([out]), retrieve).answer("klaim")
    assert ans.verdict == "ditemukan" and ans.article_id == "200"
    assert ans.status_label == "PARODI", "status harus dari label metadata"
    assert ans.references == ["https://sumber-sahih.example/200"]
    assert len(ans.llm_urls_found) >= 2, "URL pada keluaran mentah LLM harus terhitung"
    text = render(ans)
    outside = [u for u in find_urls(text) if u not in allowed_urls(ans)]
    assert not outside, f"URL di luar metadata pada keluaran akhir: {outside}"
    assert "palsu.example" not in text and "karangan.com" not in text and "kompas.com" not in text

    # 2. Label dari metadata walau LLM menyebut label lain di teksnya
    out = llm_json(artikel_terpilih="100", klaim_sama=True, klarifikasi="Ini PENIPUAN.")
    ans = AnswerGenerator(ScriptedProvider([out]), retrieve).answer("klaim")
    assert ans.status_label == "SALAH"

    # 3. id di luar kandidat ditolak -> tidak cocok
    out = llm_json(artikel_terpilih="999", klaim_sama=True, klarifikasi="x")
    ans = AnswerGenerator(ScriptedProvider([out]), retrieve).answer("klaim")
    assert ans.verdict == "tidak_ditemukan" and ans.invalid_id and ans.article_id is None
    assert "BELUM DITEMUKAN" in render(ans)

    # 4. klaim_sama=false -> tidak ditemukan, walau LLM tetap mengisi id
    out = llm_json(artikel_terpilih="100", klaim_sama=False, alasan="hanya mirip topik")
    ans = AnswerGenerator(ScriptedProvider([out]), retrieve).answer("klaim")
    assert ans.verdict == "tidak_ditemukan" and not ans.invalid_id
    assert "hanya mirip topik" in render(ans)

    # 5. Artikel tanpa references: jawaban tetap ada, tanpa bagian rujukan
    out = llm_json(artikel_terpilih="300", klaim_sama=True, klarifikasi="Penipuan.")
    ans = AnswerGenerator(ScriptedProvider([out]), retrieve).answer("klaim")
    assert ans.verdict == "ditemukan" and ans.references == []
    assert "RUJUKAN" not in render(ans)

    # 6. Gagal parse: sekali lalu sukses -> 1 kegagalan; terus gagal -> "gagal"
    good = llm_json(artikel_terpilih="100", klaim_sama=True, klarifikasi="ok")
    ans = AnswerGenerator(ScriptedProvider(["bukan json", good]), retrieve).answer("klaim")
    assert ans.verdict == "ditemukan" and ans.parse_failures == 1
    ans = AnswerGenerator(ScriptedProvider(["bukan json"]), retrieve).answer("klaim")
    assert ans.verdict == "gagal" and ans.parse_failures == 2
    assert "TIDAK DAPAT DIPROSES" in render(ans)
    # tipe salah (klaim_sama string) juga pelanggaran format
    bad = '{"artikel_terpilih": "100", "klaim_sama": "true", "alasan": "", "klarifikasi": ""}'
    ans = AnswerGenerator(ScriptedProvider([bad]), retrieve).answer("klaim")
    assert ans.verdict == "gagal" and ans.parse_failures == 2

    # 7. Pagar kode ```json diterima
    fenced = "```json\n" + good + "\n```"
    ans = AnswerGenerator(ScriptedProvider([fenced]), retrieve).answer("klaim")
    assert ans.verdict == "ditemukan" and ans.parse_failures == 0

    # 8. LLMError tidak menjatuhkan proses
    ans = AnswerGenerator(ScriptedProvider([LLMError("kuota habis")]), retrieve).answer("klaim")
    assert ans.verdict == "gagal" and "kuota habis" in ans.error

    # 9. Konteks: Narasi dan Kesimpulan dikirim; Penjelasan tidak ada di ArticleHit
    prov = ScriptedProvider([out])
    AnswerGenerator(prov, retrieve).answer("klaim pengguna X")
    p = prov.prompts[0]
    assert "Narasi 100" in p and "Kesimpulan 100" in p and "klaim pengguna X" in p
    assert "Penjelasan" not in p


class _FakeHTTPError(Exception):
    """Meniru GenAiError: status_code, body, headers, message."""

    def __init__(self, status: int, body: str = "", message: str = "galat", headers=None) -> None:
        super().__init__(message)
        self.status_code, self.body, self.message = status, body, message
        self.headers = headers or {}


class _FakeInteraction:
    def __init__(self, text="{}", status="completed") -> None:
        from types import SimpleNamespace

        self.output_text, self.status = text, status
        self.usage = SimpleNamespace(total_input_tokens=11, total_output_tokens=7, total_thought_tokens=3)


class _FakeInteractions:
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

    from llm_provider import GeminiProvider

    key = "AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234"
    p = GeminiProvider(api_key=key, min_interval_s=0, proactive=False)
    fake = _FakeInteractions(script)
    p._client = SimpleNamespace(interactions=fake)
    return p, fake, key


def test_gemini_provider_error_handling() -> None:
    import llm_provider as lp
    from llm_provider import LLMConfigError, LLMError, redact

    slept: list[float] = []
    lp.time.sleep = lambda s: slept.append(s)  # jangan benar-benar menunggu

    # 429 dengan retryDelay -> menunggu sesuai saran, lalu sukses; token dicatat
    body = '{"error": {"details": [{"retryDelay": "3s"}]}}'
    p, fake, _ = make_gemini([_FakeHTTPError(429, body), _FakeInteraction('{"a": 1}')])
    out = p.generate("sys", "usr", json_schema={"type": "object"})
    rec = p.records[-1]
    assert out == '{"a": 1}' and rec.ok and rec.attempts == 2 and rec.rate_limited == 1
    assert (rec.input_tokens, rec.output_tokens, rec.thought_tokens) == (11, 7, 3)
    assert 3.0 <= slept[-1] <= 4.1, "harus menunggu sesuai retryDelay 3s (+jitter)"
    assert fake.calls[0]["store"] is False and fake.calls[0]["timeout"] == lp.REQUEST_TIMEOUT_S
    assert fake.calls[0]["response_format"]["mime_type"] == "application/json"
    assert fake.calls[0]["system_instruction"] == "sys" and fake.calls[0]["input"] == "usr"

    # 429 terus -> menyerah setelah MAX_ATTEMPTS dengan LLMError (proses tidak mati diam-diam)
    p, fake, _ = make_gemini([_FakeHTTPError(429)])
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError:
        pass
    assert len(fake.calls) == lp.MAX_ATTEMPTS and p.records[-1].rate_limited == lp.MAX_ATTEMPTS

    # Saran tunggu sangat lama (kuota harian) -> berhenti tanpa tidur berjam-jam
    p, fake, _ = make_gemini([_FakeHTTPError(429, '{"retryDelay": "3600s"}')])
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError as e:
        assert e.retry_after_s == 3600 and len(fake.calls) == 1

    # 400 dengan skema server -> turun ke mode teks sekali
    p, fake, _ = make_gemini([_FakeHTTPError(400), _FakeInteraction("ok")])
    assert p.generate("s", "u", json_schema={"type": "object"}) == "ok"
    assert "response_format" in fake.calls[0] and "response_format" not in fake.calls[1]
    assert p.records[-1].structured_mode == "teks"

    # 401: tidak di-retry, kunci tidak bocor ke pesan galat
    p, fake, key = make_gemini([_FakeHTTPError(401, message=f"API key {'AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234'} tidak valid")])
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError as e:
        assert key not in str(e) and "KUNCI-DISAMARKAN" in str(e)
    assert len(fake.calls) == 1

    # Status tidak completed -> LLMError
    p, fake, _ = make_gemini([_FakeInteraction("potongan", status="incomplete")])
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError:
        assert p.records[-1].ok is False

    # redact dan konfigurasi
    assert "AIzaSy" not in redact("x AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ012345 y")
    # .env asli (kini berisi kunci) tidak boleh ikut terbaca oleh uji ini
    old = lp.os.environ.pop("GEMINI_API_KEY", None)
    real_load_env, lp.load_env = lp.load_env, lambda path=None: None
    try:
        lp.GeminiProvider(api_key="")
        raise AssertionError("seharusnya LLMConfigError")
    except LLMConfigError:
        pass
    finally:
        lp.load_env = real_load_env
        if old is not None:
            lp.os.environ["GEMINI_API_KEY"] = old
    try:
        lp.get_provider("tidak-ada")
        raise AssertionError("seharusnya LLMConfigError")
    except LLMConfigError:
        pass


def _quota_body(quota_id: str, retry_delay: str = "30s") -> dict:
    """Bentuk galat 429 Gemini (QuotaFailure + RetryInfo) seperti pada dokumentasi galat Google."""
    return {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
         "violations": [{"quotaMetric": "generate_content_free_tier_requests", "quotaId": quota_id}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay}]}}


def test_provider_with_real_sdk_errors() -> None:
    """
    Galat SDK ASLI (transport palsu, tanpa jaringan): membuktikan (1) retry internal SDK
    mati sehingga satu percobaan = satu permintaan, (2) 429 harian tidak di-retry,
    (3) 429 per menit di-retry maksimal 3 kali, (4) saran server terbaca dari galat nyata
    (body berupa dict, header di err.response), bukan dari fake berbentuk lain.
    """
    import httpx
    from google import genai
    from google.genai import types

    import llm_provider as lp
    from llm_provider import LLMError, LLMQuotaExhaustedError

    lp.time.sleep = lambda s: None  # jangan menunggu sungguhan

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
    p, calls = provider_for(429, _quota_body("GenerateRequestsPerDayPerProjectPerModel-FreeTier"),
                            {"retry-after": "5"})
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMQuotaExhaustedError")
    except LLMQuotaExhaustedError as e:
        assert "harian" in str(e)
    assert len(calls) == 1, f"kuota harian tidak boleh di-retry (permintaan: {len(calls)})"

    # per menit: 1 awal + 3 retry = MAX_ATTEMPTS permintaan, bukan dikali retry SDK
    p, calls = provider_for(429, _quota_body("GenerateRequestsPerMinutePerProjectPerModel-FreeTier"),
                            {"retry-after": "5"})
    try:
        p.generate("s", "u")
        raise AssertionError("seharusnya LLMError")
    except LLMError as e:
        assert not isinstance(e, LLMQuotaExhaustedError)
    assert len(calls) == lp.MAX_ATTEMPTS == 4, f"permintaan: {len(calls)}"
    assert p.records[-1].rate_limited == 4 and "per_menit" in p.records[-1].error

    # saran server terbaca dari galat nyata; > batas -> kuota habis tanpa retry
    p, calls = provider_for(429, _quota_body("GenerateRequestsPerMinutePerProjectPerModel-FreeTier"),
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


def test_find_urls_strict_and_loose() -> None:
    from generator import find_urls, strip_urls

    brand = "belum ditemukan dalam basis data cek fakta TurnBackHoax.id sebagai klaim"
    assert find_urls(brand) == [], "nama merek tanpa skema bukan URL"
    assert find_urls(brand, loose=True) == ["TurnBackHoax.id"]
    txt = "lihat https://a.example/x, www.b.example dan kompas.com/berita."
    assert find_urls(txt) == ["https://a.example/x", "www.b.example"]
    assert len(find_urls(txt, loose=True)) == 3
    assert "kompas.com" not in strip_urls(txt), "strip tetap membuang domain telanjang"


def test_eval_resume_and_incremental() -> None:
    import json
    import tempfile
    from pathlib import Path

    from test_generation import append_record, load_done

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "x.jsonl"
        assert load_done(path) == {}
        append_record(path, {"claim": "a", "verdict": "ditemukan"})
        append_record(path, {"claim": "b", "verdict": "gagal"})
        append_record(path, {"claim": "c", "verdict": "tidak_ditemukan"})
        done = load_done(path)
        assert set(done) == {"a", "c"}, "yang gagal harus diulang, bukan dilewati"
        append_record(path, {"claim": "b", "verdict": "ditemukan"})  # hasil ulang menimpa
        assert set(load_done(path)) == {"a", "b", "c"}
        assert len(path.read_text(encoding="utf-8").splitlines()) == 4
        assert all(json.loads(x) for x in path.read_text(encoding="utf-8").splitlines())


def test_rate_limiter_sliding_window() -> None:
    from rate_limit import MARGIN_S, ModelLimits, RateLimiter

    now = [0.0]
    sleeps: list[float] = []

    def sleep(x: float) -> None:
        sleeps.append(x)
        now[0] += x

    # RPM 5: dalam JENDELA 60 dtk mana pun tak boleh ada > 5 permintaan
    rl = RateLimiter(ModelLimits(rpm=5, tpm=250_000, rpd=20), clock=lambda: now[0], sleep=sleep)
    stamps = []
    for _ in range(13):
        rl.acquire(100)
        stamps.append(now[0])
    for t in stamps:
        in_window = [x for x in stamps if t - 60 < x <= t]
        assert len(in_window) <= 5, f"jendela 60 dtk berisi {len(in_window)} permintaan"
    assert sleeps and abs(sleeps[0] - (60 + MARGIN_S)) < 1e-6, "permintaan ke-6 menunggu ~60 dtk"

    # TPM: dua prompt 600 token tak muat dalam 1000 token/menit -> yang kedua menunggu
    now[0], sleeps[:] = 0.0, []
    rl = RateLimiter(ModelLimits(rpm=100, tpm=1000, rpd=100), clock=lambda: now[0], sleep=sleep)
    rl.acquire(600)
    assert rl.acquire(600) > 0 and sleeps
    # settle: perkiraan besar diganti angka nyata kecil -> permintaan berikut tidak menunggu
    now[0], sleeps[:] = 0.0, []
    rl = RateLimiter(ModelLimits(rpm=100, tpm=1000, rpd=100), clock=lambda: now[0], sleep=sleep)
    rl.acquire(900)
    rl.settle(100)
    assert rl.acquire(900) == 0 and not sleeps
    # prompt yang mustahil muat di TPM ditolak, bukan menunggu selamanya
    try:
        rl.acquire(5000)
        raise AssertionError("seharusnya ValueError")
    except ValueError:
        pass


def test_daily_ledger_and_budget() -> None:
    import tempfile
    from datetime import datetime, timezone

    from rate_limit import DailyLedger, ModelLimits, plan_budget

    def at(*a):
        return lambda: datetime(*a, tzinfo=timezone.utc)

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "ledger.json"
        # Musim panas (PDT, UTC-7): tengah malam Pasifik = 07:00 UTC
        before = DailyLedger("m", path, at(2026, 9, 21, 6, 59))
        after = DailyLedger("m", path, at(2026, 9, 21, 7, 1))
        assert before.day_key() == "2026-09-20" and after.day_key() == "2026-09-21"
        assert before.next_reset() == datetime(2026, 9, 21, 7, 0, tzinfo=timezone.utc)
        # Musim dingin (PST, UTC-8): tengah malam Pasifik = 08:00 UTC
        assert DailyLedger("m", path, at(2026, 11, 2, 7, 59)).day_key() == "2026-11-01"
        assert DailyLedger("m", path, at(2026, 11, 2, 8, 1)).day_key() == "2026-11-02"
        assert DailyLedger("m", path, at(2026, 11, 2, 7, 59)).next_reset() == \
            datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc)

        assert before.used_today() == 0
        before.add()
        before.add(3)
        assert before.used_today() == 4 and after.used_today() == 0, "hari baru mulai dari nol"
        assert DailyLedger("lain", path, at(2026, 9, 21, 6, 59)).used_today() == 0, "per model"
        before.seed(21)
        assert before.used_today() == 21

        lim = ModelLimits(rpm=5, tpm=250_000, rpd=20)
        plan = plan_budget(before, lim, n_queries=10, calls_per_query_worst=2)
        assert plan.remaining == 0 and not plan.ok, "21/20 terpakai: jangan mulai"
        plan = plan_budget(after, lim, n_queries=10, calls_per_query_worst=2)
        assert plan.ok and plan.remaining == 20 and plan.worst_case == 20
        after.seed(15)
        plan = plan_budget(after, lim, n_queries=10, calls_per_query_worst=2)
        assert not plan.ok and plan.remaining == 5
        after.seed(0)
        assert not plan_budget(after, lim, 21, 2).ok


def test_provider_proactive_budget() -> None:
    import tempfile
    from types import SimpleNamespace

    import llm_provider as lp
    from llm_provider import GeminiProvider, LLMConfigError, LLMQuotaExhaustedError
    from rate_limit import DailyLedger, ModelLimits

    key = "AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY1234"
    lp.time.sleep = lambda s: None
    with tempfile.TemporaryDirectory() as d:
        ledger = DailyLedger("gemini-3.8-flash", Path(d) / "l.json")
        p = GeminiProvider(api_key=key, model="gemini-3.8-flash", min_interval_s=0,
                           limits=ModelLimits(rpm=1000, tpm=10**7, rpd=3), ledger=ledger)
        # 429 per menit lalu sukses: KEDUA permintaan terhitung di anggaran harian
        body = _quota_body("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "1s")
        fake = _FakeInteractions([_FakeHTTPError(429, body), _FakeInteraction("a"),
                                  _FakeInteraction("b"), _FakeInteraction("c")])
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


def test_compare_models_h3() -> None:
    from test_generation import compare_models

    cases = [(f"p{i}", f"9{i}", "positif") for i in range(5)] + \
            [(f"n{i}", None, "negatif") for i in range(5)]

    def mk(v, a=None):
        return {"verdict": v, "article_id": a}

    base = {f"p{i}": mk("ditemukan", f"9{i}") for i in range(5)}
    base.update({f"n{i}": mk("tidak_ditemukan") for i in range(5)})

    assert compare_models(base, dict(base), cases)[1].startswith("TERDUKUNG")
    one_pos = dict(base, p0=mk("tidak_ditemukan"))
    assert compare_models(base, one_pos, cases)[1].startswith("TERDUKUNG"), "1 beda positif lolos"
    two_pos = dict(one_pos, p1=mk("tidak_ditemukan"))
    assert compare_models(base, two_pos, cases)[1].startswith("TIDAK TERDUKUNG")
    one_neg = dict(base, n2=mk("ditemukan", "36214"))
    assert compare_models(base, one_neg, cases)[1].startswith("TIDAK TERDUKUNG"), "negatif harus sama"
    wrong_id = dict(base, p3=mk("ditemukan", "lain"))
    assert compare_models(base, wrong_id, cases)[1].startswith("TERDUKUNG"), "beda id = 1 beda positif"
    partial = {k: v for k, v in base.items() if k != "n4"}
    assert compare_models(base, partial, cases)[1].startswith("BELUM KONKLUSIF")


def run() -> None:
    tests = [
        test_generator_logic,
        test_gemini_provider_error_handling,
        test_provider_with_real_sdk_errors,
        test_find_urls_strict_and_loose,
        test_eval_resume_and_incremental,
        test_rate_limiter_sliding_window,
        test_daily_ledger_and_budget,
        test_provider_proactive_budget,
        test_compare_models_h3,
        test_aggregate_by_article,
        test_normalize_and_domain,
        test_html_validators,
        test_fetch_retries_error_page_and_skips_cache,
        test_fetch_retry_policy,
        test_discover_not_fooled_by_error_page,
        test_article_36738,
        test_article_36729,
        test_article_36737,
        test_all_fixtures_invariants,
    ]
    for t in tests:
        t()
        print(f"OK  {t.__name__}")
    print("\nSemua pemeriksaan lolos.")


if __name__ == "__main__":
    run()
