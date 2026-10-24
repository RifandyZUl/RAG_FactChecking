"""Uji offline evaluation.external_eval: aturan kutipan, bentuk yang di-commit, dan keluaran yang tetap tersegel."""

from evaluation.external_eval import (
    exclusion_reason,
    public_case,
    technical_line,
    technical_status,
)


def test_exclusion_rules_k1_and_k2():
    assert exclusion_reason("https://daftar-semu.xyz/?fbclid=abc") == "K1"
    assert exclusion_reason("") == "K1"
    assert exclusion_reason("𝐀𝐬𝐬𝐚𝐥𝐚𝐦𝐮𝐚𝐥𝐚𝐢𝐤𝐮𝐦") == "K1"
    assert exclusion_reason("Unggahan disertai pernyataan dari tokoh semu, berikut isinya:") == "K2"
    assert exclusion_reason("Kata semu satu dua tiga empat lima") is None


def test_public_case_drops_message_text():
    c = {"kode": "P1-1", "kutipan": "teks pesan semu", "sha256_kutipan": "x", "expected_article": "1"}
    assert "kutipan" not in public_case(c) and public_case(c)["sha256_kutipan"] == "x"


def _rec(run, status, verdict, article):
    call = {"ok": True, "rate_limited": False}
    return {"run": run, "status": status, "jumlah_percobaan_butir": 1, "verdict": verdict, "article_id": article,
            "percobaan": [{"error": None, "verdict": verdict, "article_id": article, "calls": [call]}]}


def test_technical_output_never_reveals_decisions():
    recs = [_rec(1, "selesai", "ditemukan", "36123"), _rec(1, "selesai", "belum_ditemukan", None)]
    text = str(technical_status(recs)) + technical_line("liputan6", 1, 1, 91, "selesai", recs[0]["percobaan"])
    assert "ditemukan" not in text and "36123" not in text and "verdict" not in text
    assert technical_status(recs)["run_1"]["panggilan_llm"] == 2
