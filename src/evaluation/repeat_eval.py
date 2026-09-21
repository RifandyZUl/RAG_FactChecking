"""
Ulangan diagnostik (LIVE): jalankan kueri set pengembangan beberapa kali dengan setelan generator
YANG SAMA untuk mengukur ketidakkonsistenan keputusan antar-run.

Murni diagnostik: tidak mengubah prompt, setelan, atau logika generator, dan hasilnya tidak boleh
dipakai untuk menyetel apa pun (10 kueri ini sudah terlalu sering dipakai). Hasil per panggilan ditulis
ke data/generation_repeat_<model>.jsonl (satu baris per kueri per run), dapat dilanjutkan.

Pemakaian (dari root proyek): PYTHONPATH=src python -m evaluation.repeat_eval [--model ID] [--runs 5]
"""

import argparse
import json
import logging
import re
import sys

from evaluation.devset import DEV_QUERIES, VERDICT_DITEMUKAN
from evaluation.results_store import append_record
from generator import MAX_FORMAT_RETRIES, AnswerGenerator
from ingest import get_collection, load_model
from llm import LLMConfigError, get_provider
from llm.ledger import plan_budget
from paths import DATA_DIR
from retriever import retrieve

LOG_PATH = DATA_DIR / "llm_calls.log"
MAX_CONSECUTIVE_API_FAILURES = 2


def repeat_path(model: str):
    return DATA_DIR / f"generation_repeat_{re.sub(r'[^A-Za-z0-9._-]', '_', model)}.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--model")
    ap.add_argument("--runs", type=int, default=5)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"),
                                  logging.StreamHandler(sys.stderr)])
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        provider = get_provider(**({"model": args.model} if args.model else {}))
    except LLMConfigError as e:
        print(f"Konfigurasi LLM belum siap: {e}")
        return 2

    cases = [(d.claim, d.expected_article_id, "positif" if d.expected_verdict == VERDICT_DITEMUKAN else "negatif")
             for d in DEV_QUERIES]
    out = repeat_path(provider.model)
    done: set[tuple[int, int]] = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r["verdict"] != "gagal":
                    done.add((r["run"], r["idx"]))
    todo = [(run, i) for run in range(1, args.runs + 1) for i in range(len(cases)) if (run, i) not in done]

    print(f"Model: {provider.model} | thinking: {provider.thinking_level} | runs: {args.runs} | "
          f"sudah ada: {len(done)} | akan dijalankan: {len(todo)}")
    if provider.ledger is not None and provider.limits is not None:
        plan = plan_budget(provider.ledger, provider.limits, len(todo), 1 + MAX_FORMAT_RETRIES)
        print(f"RPM {provider.limits.rpm} | {plan.describe()}")
        if todo and not plan.ok:
            print(f"TIDAK DIMULAI: {plan.needed} dibutuhkan, {plan.remaining} tersisa.")
            return 4
    if not todo:
        return 0

    model = load_model()
    collection = get_collection()
    gen = AnswerGenerator(provider, lambda claim, k: retrieve(claim, model, collection, top_k=k))

    consecutive = 0
    for run, i in todo:
        claim, expected, kind = cases[i]
        dq = DEV_QUERIES[i]
        ans = gen.answer(claim)
        if ans.quota_exhausted:
            print(f"BERHENTI (kuota): {ans.error}")
            return 3
        rec = {"run": run, "idx": i, "claim": claim, "kind": kind, "expected": expected,
               "expected_retrieval_article": dq.expected_retrieval_article,
               "expected_verdict": dq.expected_verdict, "kekhususan": dq.kekhususan, "batas": dq.batas,
               "verdict": ans.verdict, "article_id": ans.article_id, "alasan": ans.alasan,
               "klarifikasi": ans.klarifikasi, "raw": ans.raw_outputs, "error": ans.error,
               "parse_failures": ans.parse_failures,
               "candidates": [c["article_id"] for c in ans.candidates],
               "latency": sum(c.latency_s for c in ans.calls),
               "tokens": [[c.input_tokens, c.output_tokens, c.thought_tokens] for c in ans.calls],
               "model": provider.model, "thinking": provider.thinking_level}
        append_record(out, rec)
        print(f"run {run} kueri {i + 1:>2} ({kind}): {ans.verdict} {ans.article_id or ''}", flush=True)
        api_failed = ans.verdict == "gagal" and bool(ans.error) and ans.parse_failures == 0
        consecutive = consecutive + 1 if api_failed else 0
        if consecutive >= MAX_CONSECUTIVE_API_FAILURES:
            print(f"BERHENTI: {consecutive} kueri beruntun gagal di API ({ans.error[:200]})")
            return 3
    print(f"Selesai. Hasil: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
