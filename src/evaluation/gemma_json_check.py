"""
Uji format JSON Gemma 4 (LIVE: memakai permintaan dari kuota Gemma) untuk H4.

H4: Gemma 4 dapat berfungsi sebagai model juri RAGAS. RAGAS bergantung pada
keluaran JSON, sedangkan halaman Gemma-di-Gemini-API tidak menyebut keluaran
terstruktur. Uji ini mengirim 3 prompt (bentuk mirip langkah RAGAS + prompt
generator kita) masing-masing dalam dua mode dan memeriksa keluarannya:

  skema : `response_format` dengan skema JSON (mode terstruktur server)
  teks  : tanpa skema, hanya instruksi "balas JSON saja" (cara RAGAS)

Yang dilaporkan per keluaran: JSON valid apa adanya, berpagar ```json, valid
setelah ekstraksi longgar, dan bentuk (kunci + tipe) sesuai. Kegagalan pemanggilan
(galat integrasi/kuota) dipisahkan dari kegagalan format.

Bukan evaluasi juri RAGAS itu sendiri: RAGAS belum terpasang, dan prompt di sini
adalah perkiraan bentuk langkahnya. Sampel: 3 prompt x 2 mode, indikasi saja.
Pemakaian (dari root proyek): PYTHONPATH=src python -m evaluation.gemma_json_check [--model gemma-4-31b-it]
"""

import argparse
import json
import logging
import re
import sys

from chunker import load_articles
from generator import RESPONSE_SCHEMA, SYSTEM_PROMPT, build_user_prompt, parse_llm_output
from llm import LLMConfigError, LLMError, LLMQuotaExhaustedError, get_provider
from evaluation.results_store import append_record
from llm.ledger import plan_budget
from paths import PROJECT_ROOT
from retriever import ArticleHit

OUT_PATH = PROJECT_ROOT / "data" / "gemma_json_test.jsonl"
LOG_PATH = PROJECT_ROOT / "data" / "llm_calls.log"
CLAIM = "katanya ojol nggak boleh isi pertalite lagi ya?"
CANDIDATES = ("36730", "36737", "36731")  # 36730 = artikel yang benar untuk CLAIM

JUDGE_SYSTEM = "Kamu adalah penilai yang teliti. Balas HANYA dengan JSON valid, tanpa teks lain."

STATEMENTS_SCHEMA = {
    "type": "object",
    "properties": {"statements": {"type": "array", "items": {"type": "string"}}},
    "required": ["statements"],
}
VERDICTS_SCHEMA = {
    "type": "object",
    "properties": {"verdicts": {"type": "array", "items": {
        "type": "object",
        "properties": {"statement": {"type": "string"}, "reason": {"type": "string"},
                       "verdict": {"type": "integer"}},
        "required": ["statement", "reason", "verdict"]}}},
    "required": ["verdicts"],
}


def check_statements(d: dict) -> bool:
    s = d.get("statements")
    return isinstance(s, list) and len(s) >= 1 and all(isinstance(x, str) for x in s)


def check_verdicts(d: dict) -> bool:
    v = d.get("verdicts")
    return (isinstance(v, list) and len(v) >= 1 and all(
        isinstance(x, dict) and isinstance(x.get("statement"), str)
        and isinstance(x.get("reason"), str) and x.get("verdict") in (0, 1)
        and not isinstance(x.get("verdict"), bool) for x in v))


def check_generator(d: dict) -> bool:
    return parse_llm_output(json.dumps(d)) is not None


def build_prompts(articles: dict[str, dict]) -> list[dict]:
    a = articles["36730"]
    context = f"{a['title']}\nNarasi: {a['narasi']}\nKesimpulan: {a['kesimpulan']}"
    answer = f"Klaim itu tidak benar. {a['kesimpulan']}"
    statements = ["Pengemudi ojek online dilarang membeli Pertalite.",
                  "Klaim larangan itu adalah hoaks.",
                  "Pemerintah mengumumkan larangan itu pada hari ini."]

    hits = [ArticleHit(article_id=i, title=articles[i]["title"], url=articles[i]["url"],
                       label=articles[i]["label"], score=0.6, best_section="narasi",
                       references=articles[i].get("references", []), date=articles[i].get("date", ""),
                       narasi=articles[i]["narasi"], kesimpulan=articles[i]["kesimpulan"])
            for i in CANDIDATES]
    return [
        {"name": "P1 ekstraksi pernyataan (langkah faithfulness RAGAS)", "system": JUDGE_SYSTEM,
         "user": (f"Pertanyaan: {CLAIM}\nJawaban: {answer}\n\nUraikan jawaban menjadi pernyataan "
                  'atomik yang berdiri sendiri. Balas JSON: {"statements": ["...", "..."]}'),
         "schema": STATEMENTS_SCHEMA, "check": check_statements},
        {"name": "P2 verdict per pernyataan terhadap konteks (NLI faithfulness)", "system": JUDGE_SYSTEM,
         "user": (f"Konteks:\n{context}\n\nPernyataan:\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(statements))
                  + '\n\nUntuk tiap pernyataan, nilai apakah dapat disimpulkan dari konteks '
                    "(verdict 1) atau tidak (verdict 0). Balas JSON: "
                    '{"verdicts": [{"statement": "...", "reason": "...", "verdict": 0}]}'),
         "schema": VERDICTS_SCHEMA, "check": check_verdicts},
        {"name": "P3 prompt generator kita (skema klaim_sama)", "system": SYSTEM_PROMPT,
         "user": build_user_prompt(CLAIM, hits), "schema": RESPONSE_SCHEMA, "check": check_generator},
    ]


def lenient_json(text: str) -> tuple[dict | None, bool, bool]:
    """(hasil ekstraksi longgar, valid apa adanya, berpagar kode)."""
    raw = text.strip()
    try:
        d = json.loads(raw)
        return (d if isinstance(d, dict) else None), isinstance(d, dict), False
    except ValueError:
        pass
    fenced = bool(re.match(r"^```", raw))
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
    braces = re.search(r"\{.*\}", s, re.DOTALL)
    for cand in (s, braces.group(0) if braces else None):
        if not cand:
            continue
        try:
            d = json.loads(cand)
        except ValueError:
            continue
        if isinstance(d, dict):
            return d, False, fenced
    return None, False, fenced


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--model", default="gemma-4-31b-it")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"),
                                  logging.StreamHandler(sys.stderr)])
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        provider = get_provider(model=args.model, thinking_level="minimal")
    except LLMConfigError as e:
        print(f"Konfigurasi LLM belum siap: {e}")
        return 2

    articles = {a["article_id"]: a for a in load_articles()}
    prompts = build_prompts(articles)
    n_calls = len(prompts) * 2
    if provider.ledger is not None and provider.limits is not None:
        plan = plan_budget(provider.ledger, provider.limits, n_calls, 1)
        print(f"{provider.model} | RPM {provider.limits.rpm} | TPM {provider.limits.tpm} | {plan.describe()}")
        if not plan.ok:
            print(f"TIDAK DIMULAI: {n_calls} panggilan dibutuhkan, {plan.remaining} tersisa.")
            return 4
    print(f"Model: {provider.model} | thinking: {provider.thinking_level}\n")

    rows: list[dict] = []
    for pr in prompts:
        for mode in ("skema", "teks"):
            n_before = len(provider.records)
            row = {"prompt": pr["name"], "mode": mode, "model": provider.model,
                   "call_ok": False, "error": "", "raw": ""}
            try:
                row["raw"] = provider.generate(pr["system"], pr["user"],
                                               json_schema=pr["schema"] if mode == "skema" else None)
                row["call_ok"] = True
            except LLMQuotaExhaustedError as e:
                print(f"BERHENTI: {e}")
                return 3
            except LLMError as e:
                row["error"] = str(e)
            recs = provider.records[n_before:]
            row["mode_dipakai"] = recs[-1].structured_mode if recs else "-"
            row["tokens"] = [recs[-1].input_tokens, recs[-1].output_tokens, recs[-1].thought_tokens] if recs else None
            row["latency"] = round(recs[-1].latency_s, 1) if recs else None
            if row["call_ok"]:
                d, strict, fenced = lenient_json(row["raw"])
                row.update(strict_json=strict, fenced=fenced, lenient_json=d is not None,
                           shape_ok=bool(d is not None and pr["check"](d)))
            append_record(OUT_PATH, row)
            rows.append(row)
            print("=" * 78)
            print(f"{pr['name']} | mode diminta: {mode} | mode dipakai: {row['mode_dipakai']}")
            if not row["call_ok"]:
                print("GALAT PEMANGGILAN (integrasi/kuota, bukan format):", row["error"])
                continue
            print(f"JSON apa adanya: {row['strict_json']} | berpagar: {row['fenced']} | "
                  f"valid setelah ekstraksi: {row['lenient_json']} | bentuk sesuai: {row['shape_ok']} | "
                  f"token masuk/keluar/pikir: {row['tokens']} | {row['latency']}s")
            print("--- keluaran mentah ---")
            print(row["raw"])

    ok = [r for r in rows if r["call_ok"]]
    print("\n" + "=" * 78 + "\nRINGKASAN (3 prompt x 2 mode)")
    print(f"Panggilan berhasil: {len(ok)}/{len(rows)}; galat pemanggilan: {len(rows) - len(ok)}")
    for mode in ("skema", "teks"):
        sub = [r for r in ok if r["mode"] == mode]
        print(f"  mode {mode:<5}: JSON apa adanya {sum(r['strict_json'] for r in sub)}/{len(sub)}, "
              f"valid setelah ekstraksi {sum(r['lenient_json'] for r in sub)}/{len(sub)}, "
              f"bentuk sesuai {sum(r['shape_ok'] for r in sub)}/{len(sub)}, "
              f"mode skema diturunkan ke teks oleh penyedia: "
              f"{sum(r['mode_dipakai'] != 'schema' for r in sub) if mode == 'skema' else '-'}")
    print(f"Hasil lengkap: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
