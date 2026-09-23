"""
Evaluasi set uji v1 (LIVE: memanggil LLM sungguhan; butuh kunci di .env).

Menjalankan SELURUH 54 butir testset/v1.jsonl x 3 run (pra-registrasi), urutan diacak per run
dengan benih berbeda (RUN_SEEDS, tercatat juga di testset/v1.meta.json setelah run selesai),
memakai generator yang DIKUNCI di v1.meta.json.sidik_jari_generator_v1.

TIDAK MENGHITUNG METRIK APA PUN: hanya menyimpan hasil mentah per (run, butir) --
verdict, jejak retrieval (top-3 + seksi chunk pemenang + recall@3), keluaran LLM mentah,
token, latensi, dan jumlah percobaan -- ke data/testset_v1_eval_<model>.jsonl, satu baris per
(run, butir), dapat dilanjutkan. Skrip analisis terpisah (belum ditulis) menghitung metrik dari
berkas ini tanpa memanggil API lagi -- supaya cara menghitung bisa berubah tanpa menyentuh data
mentah atau memanggil API ulang.

Butir yang gagal karena galat pemanggilan (429/503/timeout) ATAU format LLM diulang di tingkat
BUTIR (bukan hanya percobaan ulang format internal AnswerGenerator) hingga MAX_ITEM_RETRIES kali;
bila tetap gagal, ditandai status="tak_terjawab" (bukan "jawaban salah") dan TETAP ditulis untuk
jejak audit. Kuota harian habis menghentikan SELURUH proses (bukan menandai satu butir),
sama seperti evaluation.generation_eval/repeat_eval.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m evaluation.testset_eval --check-budget
  PYTHONPATH=src python -m evaluation.testset_eval [--model ID] [--force]
"""

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

from chunker import load_articles
from evaluation.results_store import append_record
from generator import MAX_FORMAT_RETRIES, AnswerGenerator
from ingest import get_collection, load_model
from llm import LLMConfigError, get_provider
from llm.ledger import plan_budget
from paths import DATA_DIR, PROJECT_ROOT
from retriever import ArticleHit, retrieve

LOG_PATH = DATA_DIR / "llm_calls.log"
V1_PATH = PROJECT_ROOT / "testset" / "v1.jsonl"

N_RUNS = 3
# Benih acak per run (satu per run, tercatat di v1.meta.json setelah selesai). Tanggal+nomor run,
# sama pola dengan seed lain di proyek ini (mis. 20260924 untuk sampel arsip).
RUN_SEEDS = {1: 2026092301, 2: 2026092302, 3: 2026092303}
MAX_ITEM_RETRIES = 2  # percobaan TAMBAHAN per butir bila gagal (maks 3 percobaan total)
ITEM_RETRY_PAUSE_S = 5.0  # jeda sebelum mencoba ulang butir yang gagal (bukan retry format internal)
TOP_K = 3
MAX_CONSECUTIVE_UNANSWERED = 2  # setelah ini berhenti (instruksi pemilik proyek 2026-09-23):
# jangan diteruskan sampai kuota habis bila ada galat yang membuat 2 butir berturut-turut gagal


def out_path(model: str) -> Path:
    return DATA_DIR / f"testset_v1_eval_{re.sub(r'[^A-Za-z0-9._-]', '_', model)}.jsonl"


def load_cases() -> list[dict[str, Any]]:
    return [json.loads(x) for x in V1_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]


def shuffled_order(n: int, seed: int) -> list[int]:
    """Urutan indeks 0..n-1 diacak dengan `seed` -- reproducible, dicatat di v1.meta.json."""
    import random

    idx = list(range(n))
    random.Random(seed).shuffle(idx)
    return idx


def load_done(path: Path) -> set[tuple[int, int]]:
    """(run, idx) yang SUDAH punya hasil status='selesai'. 'tak_terjawab' juga dianggap selesai
    (sudah dicoba MAX_ITEM_RETRIES+1 kali) -- tidak diulang otomatis, beda dari verdict='gagal'
    transien di skrip evaluasi lain yang tidak melakukan retry tingkat butir."""
    done: set[tuple[int, int]] = set()
    if not path.exists():
        return done
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError as e:
            raise SystemExit(f"{path} baris {n} rusak ({e}); perbaiki atau pakai --force.")
        done.add((rec["run"], rec["idx"]))
    return done


def serialize_call(c: Any) -> dict[str, Any]:
    return {
        "ok": c.ok, "attempts": c.attempts, "latency_s": round(c.latency_s, 3),
        "input_tokens": c.input_tokens, "output_tokens": c.output_tokens,
        "thought_tokens": c.thought_tokens, "structured_mode": c.structured_mode,
        "rate_limited": c.rate_limited, "error": c.error, "model_version": c.model_version,
    }


def retrieval_trace(hits: list[ArticleHit], expected_retrieval_article: str | None) -> dict[str, Any]:
    top3 = [{"article_id": h.article_id, "score": round(h.score, 4)} for h in hits[:TOP_K]]
    return {
        "retrieval_top3": top3,
        "retrieval_best_section_top1": hits[0].best_section if hits else None,
        "recall_at_3": (expected_retrieval_article in {h.article_id for h in hits[:TOP_K]})
                       if expected_retrieval_article else None,
    }


def answer_with_item_retries(gen: AnswerGenerator, claim: str) -> tuple[Any, list[dict], str]:
    """
    Panggil gen.answer() sampai berhasil (verdict != 'gagal') atau MAX_ITEM_RETRIES+1 percobaan
    habis. Mengembalikan (ans_terakhir, daftar_percobaan, status) dengan status "selesai" |
    "tak_terjawab" | "kuota_habis". Kuota habis TIDAK diulang (bukan masalah butir ini).
    """
    percobaan = []
    ans = None
    for attempt in range(1, MAX_ITEM_RETRIES + 2):
        ans = gen.answer(claim)
        percobaan.append({
            "percobaan_ke": attempt, "verdict": ans.verdict, "article_id": ans.article_id,
            "status_label": ans.status_label, "error": ans.error,
            "invalid_id": ans.invalid_id, "parse_failures": ans.parse_failures,
            "raw_outputs": list(ans.raw_outputs), "calls": [serialize_call(c) for c in ans.calls],
        })
        if ans.quota_exhausted:
            return ans, percobaan, "kuota_habis"
        if ans.verdict != "gagal":
            return ans, percobaan, "selesai"
        if attempt < MAX_ITEM_RETRIES + 1:
            time.sleep(ITEM_RETRY_PAUSE_S)
    return ans, percobaan, "tak_terjawab"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--model", help="ID model (bawaan: LLM_MODEL / bawaan penyedia)")
    ap.add_argument("--force", action="store_true", help="abaikan hasil lama dan mulai ulang")
    ap.add_argument("--check-budget", action="store_true",
                    help="hanya laporkan anggaran kuota harian; tidak ada panggilan LLM")
    ap.add_argument("--run", type=int, choices=sorted(RUN_SEEDS), default=None,
                    help="batasi ke satu nomor run saja (bawaan: jalankan run 1-3 berurutan "
                         "dalam satu proses); dipakai untuk melapor per run sebagai proses terpisah")
    args = ap.parse_args()

    cases = load_cases()
    n = len(cases)
    run_numbers = [args.run] if args.run is not None else sorted(RUN_SEEDS)

    try:
        provider = get_provider(**({"model": args.model} if args.model else {}))
    except LLMConfigError as e:
        print(f"Konfigurasi LLM belum siap: {e}")
        return 2

    out = out_path(provider.model)
    done = set() if args.force else load_done(out)
    all_pairs = [(run, idx) for run in run_numbers for idx in shuffled_order(n, RUN_SEEDS[run])]
    todo = [(run, idx) for run, idx in all_pairs if (run, idx) not in done]

    print(f"Penyedia: {provider.name} | model: {provider.model} | "
          f"thinking: {getattr(provider, 'thinking_level', '-')}")
    print(f"Butir: {n} | run diminta: {run_numbers} (dari {N_RUNS} run rancangan) | "
          f"pasangan (run,butir) dalam cakupan ini: {len(all_pairs)} | sudah ada: {len(done)} | "
          f"akan dijalankan: {len(todo)}{' (--force)' if args.force else ''}")

    if provider.ledger is not None and provider.limits is not None:
        worst_per_item = (1 + MAX_ITEM_RETRIES) * (1 + MAX_FORMAT_RETRIES)
        plan = plan_budget(provider.ledger, provider.limits, len(todo), worst_per_item)
        print(f"RPM {provider.limits.rpm} | TPM {provider.limits.tpm} | {plan.describe()}")
        if todo and not plan.ok:
            print(f"TIDAK DIMULAI: kuota harian tidak cukup ({plan.needed} dibutuhkan, "
                  f"{plan.remaining} tersisa). Jalankan lagi setelah reset.")
            return 4
    else:
        print("Batas kuota model ini tidak dikenal: anggaran harian tidak dihitung.")
    if args.check_budget:
        return 0
    if args.force and out.exists():
        out.unlink()
    if not todo:
        print("Semua (run, butir) sudah punya hasil; tidak ada panggilan LLM. Pakai --force untuk mengulang.")
        return 0

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"),
                                  logging.StreamHandler(sys.stderr)])
    logging.getLogger("httpx").setLevel(logging.WARNING)

    load_articles()  # verifikasi ketersediaan sebelum memulai; hasil tidak dipakai langsung di sini
    embedder, collection = load_model(), get_collection()
    gen = AnswerGenerator(provider, lambda claim, k: retrieve(claim, embedder, collection, top_k=k))

    consecutive_unanswered = 0
    for run, idx in todo:
        row = cases[idx]
        claim = row["klaim"]
        posisi = all_pairs.index((run, idx))

        hits_for_trace = retrieve(claim, embedder, collection, top_k=TOP_K)
        ans, percobaan, status = answer_with_item_retries(gen, claim)

        if status == "kuota_habis":
            print(f"[run {run} idx {idx}] BERHENTI (kuota): {ans.error}")
            print(f"Hasil sejauh ini tersimpan di {out}; jalankan ulang untuk melanjutkan.")
            return 3

        record: dict[str, Any] = {
            "run": run, "seed_run": RUN_SEEDS[run], "posisi_dalam_urutan_gabungan": posisi,
            "idx": idx, "id": row["id"], "klaim": claim, "tipe": row["tipe"], "subtipe": row["subtipe"],
            "expected_retrieval_article": row["expected_retrieval_article"],
            "expected_verdict": row["expected_verdict"], "expected_label": row["expected_label"],
            "kekhususan": row["kekhususan"], "batas": row["batas"],
            "status": status, "jumlah_percobaan_butir": len(percobaan), "percobaan": percobaan,
            "verdict": ans.verdict, "article_id": ans.article_id, "status_label": ans.status_label,
            "klarifikasi": ans.klarifikasi, "alasan": ans.alasan,
            "model": provider.model, "thinking": getattr(provider, "thinking_level", None),
            **retrieval_trace(hits_for_trace, row["expected_retrieval_article"]),
        }
        append_record(out, record)

        print(f"[run {run}/{N_RUNS} pos {posisi + 1}/{len(all_pairs)}] {row['id']} "
              f"({row['tipe']}/{row['subtipe']}): status={status} verdict={ans.verdict} "
              f"id={ans.article_id or ''} percobaan={len(percobaan)}", flush=True)

        consecutive_unanswered = consecutive_unanswered + 1 if status == "tak_terjawab" else 0
        if consecutive_unanswered >= MAX_CONSECUTIVE_UNANSWERED:
            print(f"BERHENTI: {consecutive_unanswered} butir beruntun tak terjawab -- "
                  "kemungkinan masalah sistemik (server/kuota), bukan butir tertentu.")
            print(f"Hasil sejauh ini tersimpan di {out}; jalankan ulang untuk melanjutkan.")
            return 3

    print(f"\nSelesai. {len(todo)} (run, butir) dijalankan. Hasil: {out}")
    print("Metrik BELUM dihitung -- jalankan skrip analisis terpisah (belum ditulis) terhadap berkas ini.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
