"""
Evaluasi lapisan generasi (LIVE: memanggil LLM sungguhan; butuh kunci di .env).

Menjalankan 5 kueri positif dan 5 kueri negatif dari evaluation/retrieval_eval.py, mencetak
keluaran lengkap, lalu melaporkan kriteria penerimaan dan status hipotesis:

  H1  LLM yang membaca Narasi dapat membedakan klaim identik dari klaim yang
      sekadar bertetangga topik.
  H3  Model kelas Flash cukup untuk tugas ini.

Sampel kecil (5 positif, 5 negatif): hasilnya indikasi, bukan evaluasi statistik.
Prasyarat: python src/ingest.py sudah dijalankan dan .env berisi GEMINI_API_KEY.
Pemakaian (dari root proyek): PYTHONPATH=src python -m evaluation.generation_eval [--model ID]
"""

import argparse
import logging
import re
import statistics
import sys

from chunker import load_articles
from evaluation.comparison import compare_models
from evaluation.devset import DEV_QUERIES, VERDICT_BELUM, VERDICT_DITEMUKAN
from evaluation.metrics import error_report, format_error_report
from evaluation.results_store import append_record, load_done, out_path_for
from generator import (
    MAX_FORMAT_RETRIES,
    Answer,
    AnswerGenerator,
    allowed_urls,
    find_urls,
    render,
)
from ingest import get_collection, load_model
from llm import LLMConfigError, get_provider
from llm.ledger import plan_budget
from paths import PROJECT_ROOT
from retriever import retrieve

LOG_PATH = PROJECT_ROOT / "data" / "llm_calls.log"


HOAX_TARGET = "36214"  # artikel vaksin HPV bikin impoten (tetangga dekat kasus H1)


VAKSIN_FLU_MARK = "vaksin flu"


MAX_CONSECUTIVE_API_FAILURES = 2  # setelah ini evaluasi berhenti agar anggaran tidak terbakar


def unsupported_tokens(ans: Answer, context: str) -> list[str]:
    """
    Token yang muncul di teks LLM (klarifikasi/alasan) tetapi tidak ada di konteks
    atau klaim: angka dan kata berhuruf kapital. Penanda untuk PEMERIKSAAN MANUAL,
    bukan penilaian otomatis atas kebenaran pernyataan.
    """
    text = f"{ans.klarifikasi} {ans.alasan}"
    haystack = (context + " " + ans.claim).lower()
    cands = re.findall(r"\d[\d.,]*|\b[A-Z][a-zA-Z]{3,}\b", text)
    return sorted({t for t in cands if t.lower().rstrip(".,") not in haystack})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--model", help="ID model (bawaan: LLM_MODEL / bawaan penyedia)")
    ap.add_argument("--force", action="store_true", help="abaikan hasil lama dan mulai ulang")
    ap.add_argument("--check-budget", action="store_true",
                    help="hanya laporkan anggaran kuota harian; tidak ada panggilan LLM")
    ap.add_argument("--compare", nargs=2, metavar=("MODEL_DASAR", "MODEL_KANDIDAT"),
                    help="bandingkan dua berkas hasil (tanpa panggilan LLM) dan nilai H3")
    args = ap.parse_args()

    # Dua label terpisah per kueri (lihat evaluation.devset): artikel yang seharusnya terjangkau retrieval
    # vs keputusan akhir yang seharusnya. `kind` di sini mengikuti expected_verdict.
    queries = {d.claim: d for d in DEV_QUERIES}
    cases = [(d.claim, d.expected_retrieval_article,
              "positif" if d.expected_verdict == VERDICT_DITEMUKAN else "negatif") for d in DEV_QUERIES]
    if args.compare:
        base, cand = (load_done(out_path_for(m)) for m in args.compare)
        table, status = compare_models(base, cand, cases)
        print(f"Dasar: {args.compare[0]} | kandidat: {args.compare[1]}\n{table}\n"
              f"Kesetaraan keputusan antarmodel (informasi; BUKAN kriteria H3, yang dinilai "
              f"terhadap ground truth): {status}")
        return 0

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"),
                  logging.StreamHandler(sys.stderr)],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        provider = get_provider(**({"model": args.model} if args.model else {}))
    except LLMConfigError as e:
        print(f"Konfigurasi LLM belum siap: {e}")
        return 2

    force = args.force
    out_path = out_path_for(provider.model)
    done = {} if force else load_done(out_path)
    todo = [c for c in cases if c[0] not in done]
    print(f"Penyedia: {provider.name} | model: {provider.model} | "
          f"thinking: {getattr(provider, 'thinking_level', '-')} | "
          f"retry internal SDK dimatikan: {getattr(provider, 'sdk_retry_disabled', '-')}")
    print(f"Kueri: {len(cases)} ({sum(c[2] == 'positif' for c in cases)} positif + "
          f"{sum(c[2] == 'negatif' for c in cases)} negatif menurut expected_verdict); "
          f"sudah ada di {out_path.name}: "
          f"{len(done)}; akan dijalankan: {len(todo)}"
          f"{' (--force)' if force else ''}")

    # Anggaran kuota harian: hitung SEBELUM memulai; bila tidak cukup, laporkan saja.
    if provider.ledger is not None and provider.limits is not None:
        plan = plan_budget(provider.ledger, provider.limits, len(todo), 1 + MAX_FORMAT_RETRIES)
        print(f"RPM {provider.limits.rpm} | TPM {provider.limits.tpm} | {plan.describe()}\n")
        if todo and not plan.ok:
            print(f"TIDAK DIMULAI: kuota harian tidak cukup ({plan.needed} dibutuhkan, "
                  f"{plan.remaining} tersisa). Jalankan lagi setelah reset.")
            return 4
    else:
        print("Batas kuota model ini tidak dikenal: anggaran harian tidak dihitung.\n")
    if args.check_budget:
        return 0
    if force and out_path.exists():
        out_path.unlink()
    if not todo:
        print("Semua kueri sudah punya hasil; tidak ada panggilan LLM. "
              "Pakai --force untuk mengulang.")

    results: list[dict] = list(done.values())
    if todo:
        articles = {a["article_id"]: a for a in load_articles()}
        collection = get_collection()
        embedder = load_model()
        gen = AnswerGenerator(
            provider, lambda claim, k: retrieve(claim, embedder, collection, top_k=k)
        )

    aborted = ""
    consecutive_api_failures = 0
    for claim, expected, kind in todo:
        i = cases.index((claim, expected, kind)) + 1
        dq = queries[claim]
        ans = gen.answer(claim)
        if ans.quota_exhausted:
            # Bukan hasil evaluasi: tidak ditulis ke jsonl, supaya diulang saat lanjut.
            aborted = ans.error
            print(f"[{i}/10] BERHENTI: {ans.error}")
            break
        hits_ctx = " ".join(
            f"{a['title']} {a['narasi']} {a['kesimpulan']}"
            for a in (articles[c["article_id"]] for c in ans.candidates)
        )
        rendered = render(ans)
        outside = [u for u in find_urls(rendered) if u not in allowed_urls(ans)]
        unsup = unsupported_tokens(ans, hits_ctx)
        latency = sum(c.latency_s for c in ans.calls)

        print("=" * 78)
        print(f"[{i}/10] ({kind}) {claim}")
        print("Kandidat:", "; ".join(
            f"{c['article_id']} {c['label']} skor={c['score']} '{c['title'][:40]}'"
            for c in ans.candidates))
        for j, raw in enumerate(ans.raw_outputs, 1):
            print(f"--- keluaran mentah LLM #{j} ---\n{raw}")
        print("--- jawaban akhir ---")
        print(rendered)
        print("--- diagnostik ---")
        print(f"verdict={ans.verdict} id={ans.article_id} label={ans.status_label} "
              f"invalid_id={ans.invalid_id} parse_gagal={ans.parse_failures} "
              f"url_dari_llm={ans.llm_urls_found} url_di_luar_metadata={outside}")
        print(f"latensi={latency:.1f}s panggilan={len(ans.calls)} "
              f"429={sum(c.rate_limited for c in ans.calls)} "
              f"token_masuk={[c.input_tokens for c in ans.calls]} "
              f"token_keluar={[c.output_tokens for c in ans.calls]} "
              f"token_pikir={[c.thought_tokens for c in ans.calls]}")
        print(f"token tak ada di konteks (periksa manual): {unsup}")
        if ans.error:
            print("GALAT:", ans.error)

        record = {
            "claim": claim, "kind": kind, "tipe": dq.tipe,
            "expected": dq.expected_article_id,  # artikel yang seharusnya DIPILIH (None bila belum_ditemukan)
            "expected_retrieval_article": dq.expected_retrieval_article,
            "expected_verdict": dq.expected_verdict, "kekhususan": dq.kekhususan, "batas": dq.batas,
            "verdict": ans.verdict,
            "article_id": ans.article_id, "status_label": ans.status_label,
            "expected_label": articles[dq.expected_article_id]["label"] if dq.expected_article_id else None,
            "invalid_id": ans.invalid_id, "parse_failures": ans.parse_failures,
            "llm_urls": ans.llm_urls_found, "urls_outside": outside, "unsupported": unsup,
            "latency": latency, "rate_limited": sum(c.rate_limited for c in ans.calls),
            "error": ans.error, "rendered": rendered, "raw": ans.raw_outputs,
            "candidates": ans.candidates,
            "model": provider.model, "thinking": getattr(provider, "thinking_level", None),
            "thought_tokens": [c.thought_tokens for c in ans.calls],
            "input_tokens": [c.input_tokens for c in ans.calls],
            "output_tokens": [c.output_tokens for c in ans.calls],
        }
        append_record(out_path, record)  # langsung ke disk: hasil tak hilang bila proses mati
        results.append(record)

        # Pemutus: galat pemanggilan beruntun (bukan pelanggaran format) hampir pasti
        # masalah di sisi server/kuota; melanjutkan hanya membakar anggaran harian.
        api_failed = ans.verdict == "gagal" and bool(ans.error) and ans.parse_failures == 0
        consecutive_api_failures = consecutive_api_failures + 1 if api_failed else 0
        if consecutive_api_failures >= MAX_CONSECUTIVE_API_FAILURES:
            aborted = (f"{consecutive_api_failures} kueri beruntun gagal di pemanggilan API "
                       f"(terakhir: {ans.error[:200]})")
            break

    if aborted:
        print(f"\nEvaluasi dihentikan: {aborted}\nHasil sejauh ini tersimpan di {out_path}; "
              "jalankan ulang untuk melanjutkan (kueri yang sudah punya hasil dilewati).")
        return 3
    # urutan sesuai daftar kueri
    order = {c[0]: n for n, c in enumerate(cases)}
    results.sort(key=lambda r: order[r["claim"]])

    def is_correct(r: dict) -> bool:
        if r["expected_verdict"] == VERDICT_BELUM:
            return r["verdict"] == "tidak_ditemukan"
        return (r["verdict"] == "ditemukan" and r["article_id"] == r["expected"]
                and r["status_label"] == r["expected_label"])

    failed = [r for r in results if r["verdict"] == "gagal"]
    lat = [r["latency"] for r in results if r["latency"] > 0]
    core = [r for r in results if not r["batas"]]  # butir batas dilaporkan terpisah, tidak masuk hitungan utama
    core_pos = [r for r in core if r["expected_verdict"] == VERDICT_DITEMUKAN]
    core_neg = [r for r in core if r["expected_verdict"] == VERDICT_BELUM]
    borderline = [r for r in results if r["batas"]]

    print("\n" + "=" * 78 + "\nRINGKASAN KRITERIA PENERIMAAN (set pengembangan; BUKAN bukti mutu)")
    print(f"1. Positif (expected ditemukan), non-batas, artikel dan status benar : "
          f"{sum(map(is_correct, core_pos))}/{len(core_pos)}")
    print(f"2. Negatif (expected belum_ditemukan), non-batas, dijawab belum       : "
          f"{sum(map(is_correct, core_neg))}/{len(core_neg)}")
    for r in borderline:
        print(f"   butir BATAS (tidak dihitung di atas): {r['claim']!r} -> {r['verdict']} {r['article_id'] or ''}")
    print(f"3. URL di keluaran akhir di luar metadata            : "
          f"{sum(len(r['urls_outside']) for r in results)} (URL pada keluaran mentah LLM: "
          f"{sum(len(r['llm_urls']) for r in results)})")
    print(f"4. Token tak ada di konteks (kandidat pemeriksaan manual): "
          f"{[(i + 1, r['unsupported']) for i, r in enumerate(results) if r['unsupported']]}")
    print(f"5. Kegagalan parse format (total / kueri gagal akhir) : "
          f"{sum(r['parse_failures'] for r in results)} / {len(failed)}")
    print(f"6. Latensi rata-rata per kueri: "
          f"{statistics.mean(lat) if lat else 0:.1f}s | galat 429: "
          f"{sum(r['rate_limited'] for r in results)}")
    print("\nJenis kesalahan (dipisah; akurasi total menyembunyikan pergeseran antar-jenis):")
    print(format_error_report(error_report(results)))

    vaksin = next(r for r in results if r["expected_verdict"] == VERDICT_BELUM
                  and VAKSIN_FLU_MARK in r["claim"].lower())
    print("\nH1 (kasus 'vaksin flu bikin mandul'): "
          f"verdict={vaksin['verdict']} id={vaksin['article_id']}")
    if vaksin["verdict"] == "gagal":
        h1 = "BELUM KONKLUSIF (pemanggilan gagal)"
    elif vaksin["verdict"] == "ditemukan" and vaksin["article_id"] == HOAX_TARGET:
        h1 = "GUGUR (memaksakan kecocokan dengan artikel vaksin HPV 36214)"
    else:
        h1 = "TERDUKUNG pada kasus ini (klaim dinyatakan berbeda / tidak ditemukan)"
    print("Status H1:", h1, "-- satu kasus sulit; jangan digeneralisasi.")

    wrong = [r for r in core if r["verdict"] != "gagal" and not is_correct(r)]
    fmt_bad = sum(r["parse_failures"] for r in results)
    if failed:
        h3 = f"BELUM KONKLUSIF ({len(failed)} kueri gagal diproses: galat/format)"
    elif fmt_bad >= 2 or len(wrong) >= 2:
        h3 = f"GUGUR (format bermasalah {fmt_bad}x; keliru {len(wrong)}/{len(core)} non-batas)"
    else:
        h3 = f"TERDUKUNG pada sampel ini (keliru {len(wrong)}/{len(core)} non-batas; pelanggaran format {fmt_bad})"
    print("Status H3 (mekanis, set pengembangan, bukan bukti mutu):", h3)
    print(f"\nHasil lengkap: {out_path}\nLog panggilan: {LOG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
