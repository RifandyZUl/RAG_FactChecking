"""
Evaluasi eksternal (LIVE: memanggil LLM; butuh kunci di .env) -- docs/rancangan_evaluasi_eksternal.md.

Dua set pada indeks produksi 1.532 artikel yang DIBEKUKAN:
  liputan6  91 butir celah Liputan6 (99 dikurangi 8 butir aturan kutipan K1/K2), kueri = kutipan pesan apa adanya
  v1        54 butir testset-v1 sebagai uji kemunduran (prosedur dan benih run sama dengan evaluation.testset_eval)

Satu run per pemanggilan (`--run N`), dapat dilanjutkan per (run, butir). Hasil mentah per butir TERSEGEL: ditulis
ke data/external_eval_<set>_<model>.jsonl (lokal, tidak di-commit) dan TIDAK pernah dicetak -- layar dan --status
hanya memuat status teknis (jumlah panggilan, galat, 429), tanpa keputusan, artikel, atau metrik apa pun, sampai
sesi buta selesai (bagian 8). Metrik dihitung skrip analisis terpisah setelah segel dibuka.

Sebelum panggilan pertama setiap run: daftar butir sama dengan yang dibekukan, sidik jari isi indeks sama,
ef_search 2000, hash generator/retriever/chunker sama, dan model/thinking sama dengan kunci Versi 1. Satu saja
berbeda -> tidak dimulai (kode keluar 5).

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m evaluation.external_eval --freeze                  # sekali; menolak menimpa
  PYTHONPATH=src python -m evaluation.external_eval --set liputan6 --run 1 [--check-budget]
  PYTHONPATH=src python -m evaluation.external_eval --set v1 --run 1
  PYTHONPATH=src python -m evaluation.external_eval --status                  # status teknis saja
"""

import argparse
import hashlib
import json
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from hf_env import prepare_hf_env
from paths import DATA_DIR, PROJECT_ROOT

FROZEN_PATH = PROJECT_ROOT / "testset" / "eksternal_butir.json"
L6_SEEDS = {1: 2026101701, 2: 2026101702, 3: 2026101703}
MIN_WORDS = 5  # aturan K1 (bagian 2.2)
FAR_DAYS = 30
EXPECTED_EF_SEARCH = 2000
LOCKED_FILES = ("src/generator.py", "src/retriever.py", "src/chunker.py")
CALLS_PER_ITEM_PLAN = 2  # 1 + ulang format; item-level retry hanya saat galat, buku besar tetap penghenti keras
LOG_PATH = DATA_DIR / "llm_calls.log"


def norm_sha(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def exclusion_reason(message: str) -> str | None:
    """K1: kurang dari MIN_WORDS kata setelah tautan dibuang; K2: kalimat pengantar redaksi (diakhiri titik dua)."""
    from labeling.sessions.trace_audit import words

    if len(words(message)) < MIN_WORDS:
        return "K1"
    if message.rstrip().endswith(":"):
        return "K2"
    return None


def build_liputan6_cases() -> list[dict[str, Any]]:
    """99 butir dengan label AWAL pemilik proyek, alasan dikeluarkan (bila ada), dan strata selisih terbit."""
    from labeling.gap.gap_blocks import day_gap
    from labeling.gap.gap_review import OUT_DIR
    from labeling.sessions.trace_audit import load_items

    r1 = json.loads((OUT_DIR / "hasil_konfirmasi.json").read_text(encoding="utf-8"))
    r2 = json.loads((OUT_DIR / "hasil_konfirmasi_49.json").read_text(encoding="utf-8"))
    gap = {(1, p["butir"]): day_gap(p["l6_tanggal"], p["tbh_tanggal"]) for p in r1["pasangan"]}
    gap |= {(2, p["butir"]): p["selisih_hari"] for p in r2["pasangan"]}
    doubt = {d["butir"] for d in r2["keputusan"] if d.get("ragu")}
    cases = []
    for it in load_items():
        k = (it["putaran"], it["butir"])
        positive = it["jenis"] == "sama"
        days = gap.get(k) if positive else None
        cases.append({"kode": f"P{k[0]}-{k[1]}", "putaran": k[0], "butir": k[1], "l6_id": it["l6_id"],
                      "kutipan": it["kutipan"], "sha256_kutipan": norm_sha(it["kutipan"]),
                      "expected_verdict": "ditemukan" if positive else "belum_ditemukan",
                      "expected_article": it["keputusan"] if positive else None,
                      "ragu": k[0] == 2 and k[1] in doubt,
                      "selisih_hari": days, "strata_selisih": None if days is None else ("<=30" if abs(days) <= FAR_DAYS else ">30"),
                      "dikeluarkan": exclusion_reason(it["kutipan"])})
    return cases


def public_case(c: dict[str, Any]) -> dict[str, Any]:
    """Bentuk yang boleh di-commit: tanpa teks kutipan (hanya hash-nya)."""
    return {k: v for k, v in c.items() if k != "kutipan"}


def index_fingerprint() -> tuple[dict[str, Any], int | None]:
    from chunker import load_articles
    from evaluation.index_check import articles_content_hash, content_fingerprint
    from ingest import collection_ef_search, get_collection

    coll = get_collection()
    got = coll.get(include=["documents", "metadatas", "embeddings"])
    fp = content_fingerprint(got["ids"], got["documents"], got["metadatas"], got["embeddings"])
    fp["sha256_articles_json_isi"] = articles_content_hash(load_articles())
    return fp, collection_ef_search(coll)


def file_hashes() -> dict[str, str]:
    return {f: norm_sha((PROJECT_ROOT / f).read_text(encoding="utf-8")) for f in LOCKED_FILES}


def freeze() -> int:
    if FROZEN_PATH.exists():
        raise SystemExit(f"{FROZEN_PATH.name} sudah ada: tidak ditimpa")
    cases = build_liputan6_cases()
    fp, ef = index_fingerprint()
    used = [c for c in cases if not c["dikeluarkan"]]
    out = {
        "dibekukan": "2026-10-17", "rancangan": "docs/rancangan_evaluasi_eksternal.md",
        "ringkas": {"butir": len(cases), "dipakai": len(used),
                    "positif": sum(c["expected_verdict"] == "ditemukan" for c in used),
                    "negatif": sum(c["expected_verdict"] == "belum_ditemukan" for c in used),
                    "dikeluarkan": dict(Counter(c["dikeluarkan"] for c in cases if c["dikeluarkan"]))},
        "label": "label AWAL pemilik proyek; label final butir audit ditetapkan setelah sesi buta (bagian 7)",
        "indeks_beku": {**fp, "ef_search": ef}, "hash_berkas_terkunci": file_hashes(), "benih_run_liputan6": L6_SEEDS,
        "butir": [public_case(c) for c in cases],
    }
    FROZEN_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "butir"}, ensure_ascii=False, indent=2))
    return 0


def preflight(frozen: dict[str, Any], provider: Any, check_cases: bool) -> list[str]:
    """Masalah yang menghalangi evaluasi (kosong = boleh mulai)."""
    from evaluation.index_check import compare_fingerprints

    problems = []
    meta = json.loads((PROJECT_ROOT / "testset" / "v1.meta.json").read_text(encoding="utf-8"))["sidik_jari_generator_v1"]
    if file_hashes()["src/generator.py"] != meta["sha256_generator_py"]:
        problems.append("src/generator.py berbeda dari kunci Versi 1")
    for f, h in file_hashes().items():
        if h != frozen["hash_berkas_terkunci"][f]:
            problems.append(f"{f} berbeda dari yang dibekukan")
    if provider.model != meta["model"] or getattr(provider, "thinking_level", None) != meta["thinking_level"]:
        problems.append(f"model/thinking {provider.model}/{getattr(provider, 'thinking_level', None)} != kunci {meta['model']}/{meta['thinking_level']}")
    if check_cases and [public_case(c) for c in build_liputan6_cases()] != frozen["butir"]:
        problems.append("daftar butir/label/kutipan berbeda dari yang dibekukan")
    fp, ef = index_fingerprint()
    problems += compare_fingerprints(fp, frozen["indeks_beku"])
    if fp.get("sha256_articles_json_isi") != frozen["indeks_beku"]["sha256_articles_json_isi"]:
        problems.append("isi articles.json berbeda dari yang dibekukan")
    if ef != EXPECTED_EF_SEARCH:
        problems.append(f"ef_search {ef}, seharusnya {EXPECTED_EF_SEARCH}")
    return problems


def out_path(set_name: str, model: str) -> Path:
    tag = "liputan6" if set_name == "liputan6" else "v1_idx1532"
    return DATA_DIR / f"external_eval_{tag}_{re.sub(r'[^A-Za-z0-9._-]', '_', model)}.jsonl"


def load_records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()] if path.exists() else []


def technical_line(set_name: str, run: int, pos: int, n: int, status: str, percobaan: list[dict]) -> str:
    """Baris layar per butir: hanya status teknis, tanpa keputusan atau artikel (hasil tersegel)."""
    calls = [c for p in percobaan for c in p["calls"]]
    errors = sum(bool(p["error"]) for p in percobaan)
    return (f"[{set_name} run {run} pos {pos}/{n}] status={status} percobaan={len(percobaan)} panggilan={len(calls)} "
            f"galat={errors} 429={sum(bool(c['rate_limited']) for c in calls)}")


def technical_status(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Ringkasan teknis TANPA keputusan, artikel, atau metrik."""
    out: dict[str, Any] = {}
    for run in sorted({r["run"] for r in records}):
        rs = [r for r in records if r["run"] == run]
        calls = [c for r in rs for p in r["percobaan"] for c in p["calls"]]
        out[f"run_{run}"] = {"butir_tercatat": len(rs), "status": dict(Counter(r["status"] for r in rs)),
                             "panggilan_llm": len(calls), "panggilan_gagal": sum(not c["ok"] for c in calls),
                             "panggilan_429": sum(bool(c["rate_limited"]) for c in calls),
                             "butir_dengan_ulang": sum(r["jumlah_percobaan_butir"] > 1 for r in rs),
                             "galat_contoh": sorted({str(p["error"])[:120] for r in rs for p in r["percobaan"] if p["error"]})[:5]}
    return out


def run_eval(set_name: str, run: int, check_budget: bool) -> int:
    from evaluation.testset_eval import (
        MAX_CONSECUTIVE_UNANSWERED,
        RUN_SEEDS,
        answer_with_item_retries,
        load_cases,
        retrieval_trace,
        shuffled_order,
    )
    from llm import LLMConfigError, get_provider
    from llm.ledger import plan_budget

    frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    if set_name == "liputan6":
        cases = [c for c in build_liputan6_cases() if not c["dikeluarkan"]]
        claims = [c["kutipan"] for c in cases]
        seed = L6_SEEDS[run]
    else:
        cases = load_cases()
        claims = [c["klaim"] for c in cases]
        seed = RUN_SEEDS[run]
    try:
        provider = get_provider()
    except LLMConfigError as e:
        print(f"Konfigurasi LLM belum siap: {e}")
        return 2
    out = out_path(set_name, provider.model)
    done = {(r["run"], r["idx"]) for r in load_records(out)}
    order = shuffled_order(len(cases), seed)
    todo = [i for i in order if (run, i) not in done]
    print(f"set {set_name} | run {run} (benih {seed}) | butir {len(cases)} | sudah {len(cases) - len(todo)} | akan dijalankan {len(todo)}")
    if provider.ledger is not None and provider.limits is not None:
        plan = plan_budget(provider.ledger, provider.limits, len(todo), CALLS_PER_ITEM_PLAN)
        print(plan.describe())
        if todo and not plan.ok:
            print("TIDAK DIMULAI: kuota harian tidak cukup.")
            return 4
    if check_budget or not todo:
        return 0

    problems = preflight(frozen, provider, check_cases=set_name == "liputan6")
    if problems:
        print("TIDAK DIMULAI (pemeriksaan awal gagal):")
        for p in problems:
            print("  -", p)
        return 5
    print("pemeriksaan awal lolos: daftar butir, sidik jari indeks, ef_search, hash berkas, model/thinking")

    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8")])
    from evaluation.results_store import append_record
    from generator import AnswerGenerator
    from ingest import get_collection, load_model
    from retriever import retrieve

    embedder, collection = load_model(), get_collection()
    gen = AnswerGenerator(provider, lambda claim, k: retrieve(claim, embedder, collection, top_k=k))
    unanswered = 0
    for pos, idx in enumerate(todo, len(cases) - len(todo) + 1):
        c, claim = cases[idx], claims[idx]
        hits = retrieve(claim, embedder, collection, top_k=3)
        ans, percobaan, status = answer_with_item_retries(gen, claim)
        if status == "kuota_habis":
            print(f"BERHENTI (kuota habis) pada pos {pos}; jalankan ulang setelah reset untuk melanjutkan.")
            return 3
        expected = c["expected_article"] if set_name == "liputan6" else c["expected_retrieval_article"]
        record = {"set": set_name, "run": run, "seed_run": seed, "idx": idx,
                  "id": c["kode"] if set_name == "liputan6" else c["id"],
                  "status": status, "jumlah_percobaan_butir": len(percobaan), "percobaan": percobaan,
                  "verdict": ans.verdict, "article_id": ans.article_id, "status_label": ans.status_label,
                  "klarifikasi": ans.klarifikasi, "alasan": ans.alasan,
                  "model": provider.model, "thinking": getattr(provider, "thinking_level", None),
                  **retrieval_trace(hits, expected)}
        append_record(out, record)
        print(technical_line(set_name, run, pos, len(cases), status, percobaan), flush=True)
        unanswered = unanswered + 1 if status == "tak_terjawab" else 0
        if unanswered >= MAX_CONSECUTIVE_UNANSWERED:
            print("BERHENTI: butir beruntun tak terjawab (kemungkinan masalah server/kuota).")
            return 3
    print(f"Selesai: set {set_name} run {run}. Hasil tersegel di {out.name}.")
    return 0


def status() -> int:
    from llm import get_provider

    model = get_provider().model
    print(json.dumps({s: technical_status(load_records(out_path(s, model))) for s in ("liputan6", "v1")}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    prepare_hf_env()  # sebelum transformers dimuat (hf_env.py)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--freeze", action="store_true", help="bekukan daftar butir, sidik jari indeks, dan hash berkas")
    g.add_argument("--set", choices=("liputan6", "v1"))
    g.add_argument("--status", action="store_true", help="status teknis hasil (tanpa metrik)")
    ap.add_argument("--run", type=int, choices=(1, 2, 3))
    ap.add_argument("--check-budget", action="store_true")
    args = ap.parse_args()
    if args.freeze:
        return freeze()
    if args.status:
        return status()
    if args.run is None:
        ap.error("--set memerlukan --run")
    return run_eval(args.set, args.run, args.check_budget)


if __name__ == "__main__":
    sys.exit(main())
