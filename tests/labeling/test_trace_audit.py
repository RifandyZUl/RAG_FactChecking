"""Uji offline labeling.sessions.trace_audit: normalisasi, penyaringan domain, ambang rangkaian kata, status per butir."""

from labeling.sessions.trace_audit import NGRAM, audit, hoax_hosts, traces, words

PHRASE = "kata satu dua tiga empat lima enam tujuh delapan"  # 9 kata semu


def test_words_normalize_fancy_unicode_and_drop_urls():
    assert words("𝐀𝐲𝐨 Cek-NAMA https://contoh-semu.xyz/a?b=1 www.semu.id") == ["ayo", "cek", "nama"]


def test_hoax_hosts_skip_blocked_trusted_and_own_sites():
    urls = ["https://www.daftar-semu.xyz/x", "https://bit.ly/abc", "https://facebook.com/p", "https://bansos.kemensos.go.id",
            "https://www.liputan6.com/cek-fakta/1", "https://turnbackhoax.id/articles/1", "http://kemenag.go.id]"]
    assert hoax_hosts(urls) == {"daftar-semu.xyz"}


def test_traces_need_ngram_of_at_least_eight_words():
    seven = " ".join(PHRASE.split()[:NGRAM - 1])
    assert not traces(f"awal {seven} akhir", {"narasi": f"lain {seven} lain"})["ada"]
    assert traces(f"awal {PHRASE} akhir", {"narasi": f"BEREDAR: {PHRASE.upper()}!"})["rangkaian_kata"] == 2
    t = traces("klik https://daftar-semu.xyz/form sekarang", {"narasi": "tanpa tautan", "claim_sources": ["http://www.daftar-semu.xyz"]})
    assert t["domain"] == ["daftar-semu.xyz"] and t["ada"]


def test_audit_status_and_precision_never_touch_labels():
    items = [{"putaran": 2, "butir": 1, "kutipan": PHRASE, "jenis": "sama", "keputusan": "10", "kandidat": ["10", "11"]},
             {"putaran": 2, "butir": 2, "kutipan": PHRASE, "jenis": "tidak_ada", "keputusan": "TIDAK ADA", "kandidat": ["11"]},
             {"putaran": 1, "butir": 3, "kutipan": "pendek", "jenis": "tidak_ada", "keputusan": "TIDAK ADA", "kandidat": ["10"]}]
    arts = {"10": {"narasi": PHRASE}, "11": {"narasi": "lain sama sekali"}}
    rep = audit(items, arts)
    assert [r["status"] for r in rep["rinci"]] == ["jejak_hanya_pada_pilihan", "tanpa_jejak", "tanpa_jejak"]
    assert rep["presisi_pada_butir_cocok"] == {"pasangan_berjejak": 1, "pasangan_berjejak_adalah_pilihan": 1}
    arts["11"]["narasi"] = PHRASE
    rep = audit(items, arts)
    assert rep["tidak_ada_berjejak_untuk_ditinjau_buta"] == ["P2-2"]
    assert rep["rinci"][0]["status"] == "jejak_pada_pilihan_dan_lainnya"
    assert [i["jenis"] for i in items] == ["sama", "tidak_ada", "tidak_ada"], "label tidak diubah"
