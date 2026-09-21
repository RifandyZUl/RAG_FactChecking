"""Uji logika generator: pengaman di kode (bukan di prompt) dan sanitasi URL.
"""

from _fakes import ScriptedProvider, llm_json, make_hit


def test_generator_logic() -> None:
    from generator import AnswerGenerator, allowed_urls, find_urls, render
    from llm import LLMError

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


def test_find_urls_strict_and_loose() -> None:
    from generator import find_urls, strip_urls

    brand = "belum ditemukan dalam basis data cek fakta TurnBackHoax.id sebagai klaim"
    assert find_urls(brand) == [], "nama merek tanpa skema bukan URL"
    assert find_urls(brand, loose=True) == ["TurnBackHoax.id"]
    txt = "lihat https://a.example/x, www.b.example dan kompas.com/berita."
    assert find_urls(txt) == ["https://a.example/x", "www.b.example"]
    assert len(find_urls(txt, loose=True)) == 3
    assert "kompas.com" not in strip_urls(txt), "strip tetap membuang domain telanjang"
