"""
Evaluasi lapisan generasi (LIVE: memanggil LLM sungguhan; butuh kunci di .env).

Menjalankan 5 kueri positif dan 5 kueri negatif dari test_retrieval.py, mencetak
keluaran lengkap, lalu melaporkan kriteria penerimaan dan status hipotesis:

  H1  LLM yang membaca Narasi dapat membedakan klaim identik dari klaim yang
      sekadar bertetangga topik.
  H3  Model kelas Flash cukup untuk tugas ini.

Sampel kecil (5 positif, 5 negatif): hasilnya indikasi, bukan evaluasi statistik.
Prasyarat: python src/ingest.py sudah dijalankan dan .env berisi GEMINI_API_KEY.
"""

import json
import logging
import os
import re
import statistics
import sys
from pathlib import Path

from chunker import PROJECT_ROOT, load_articles
from generator import Answer, AnswerGenerator, allowed_urls, find_urls, render
from ingest import get_collection, load_model
from llm_provider import LLMConfigError, get_provider
from retriever import retrieve
from test_retrieval import NEGATIVE_QUERIES, QUERIES

OUT_PATH = PROJECT_ROOT / "data" / "generation_eval.jsonl"
LOG_PATH = PROJECT_ROOT / "data" / "llm_calls.log"
HOAX_TARGET = "36214"  # artikel vaksin HPV bikin impoten (tetangga dekat kasus H1)
VAKSIN_FLU_MARK = "vaksin flu"


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


def append_record(path: Path, record: dict) -> None:
    """Tambahkan satu hasil ke jsonl dan paksa ke disk (tahan terhadap proses yang dihentikan)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def load_done(path: Path) -> dict[str, dict]:
    """
    Hasil yang sudah ada per klaim (baris terakhir menang). Kueri berstatus "gagal"
    tidak dianggap selesai, jadi diulang saat dilanjutkan.
    """
    done: dict[str, dict] = {}
    if not path.exists():
        return done
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError as e:
            raise SystemExit(f"{path} baris {n} rusak ({e}); perbaiki atau pakai --force.")
        if rec.get("verdict") == "gagal":
            done.pop(rec["claim"], None)
        else:
            done[rec["claim"]] = rec
    return done


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"),
                  logging.StreamHandler(sys.stderr)],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        provider = get_provider()
    except LLMConfigError as e:
        print(f"Konfigurasi LLM belum siap: {e}")
        return 2

    force = "--force" in sys.argv[1:]
    cases = [(q, exp, "positif") for q, exp in QUERIES] + \
            [(q, None, "negatif") for q, _, _ in NEGATIVE_QUERIES]
    done = {} if force else load_done(OUT_PATH)
    if force and OUT_PATH.exists():
        OUT_PATH.unlink()
    todo = [c for c in cases if c[0] not in done]
    print(f"Penyedia: {provider.name} | model: {provider.model} | "
          f"thinking: {getattr(provider, 'thinking_level', '-')} | "
          f"retry internal SDK dimatikan: {getattr(provider, 'sdk_retry_disabled', '-')}")
    print(f"Kueri: {len(cases)} (5 positif + 5 negatif); sudah ada di jsonl: "
          f"{len(done)}; dijalankan sekarang: {len(todo)}"
          f"{' (--force)' if force else ''}\n")
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
    for claim, expected, kind in todo:
        i = cases.index((claim, expected, kind)) + 1
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
            "claim": claim, "kind": kind, "expected": expected, "verdict": ans.verdict,
            "article_id": ans.article_id, "status_label": ans.status_label,
            "expected_label": articles[expected]["label"] if expected else None,
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
        append_record(OUT_PATH, record)  # langsung ke disk: hasil tak hilang bila proses mati
        results.append(record)

    if aborted:
        print(f"\nEvaluasi dihentikan: {aborted}\nHasil sejauh ini tersimpan di {OUT_PATH}; "
              "jalankan ulang untuk melanjutkan (kueri yang sudah punya hasil dilewati).")
        return 3
    # urutan sesuai daftar kueri
    order = {c[0]: n for n, c in enumerate(cases)}
    results.sort(key=lambda r: order[r["claim"]])

    pos = [r for r in results if r["kind"] == "positif"]
    neg = [r for r in results if r["kind"] == "negatif"]
    pos_ok = [r for r in pos if r["verdict"] == "ditemukan" and r["article_id"] == r["expected"]
              and r["status_label"] == r["expected_label"]]
    neg_ok = [r for r in neg if r["verdict"] == "tidak_ditemukan"]
    failed = [r for r in results if r["verdict"] == "gagal"]
    lat = [r["latency"] for r in results if r["latency"] > 0]

    print("\n" + "=" * 78 + "\nRINGKASAN KRITERIA PENERIMAAN")
    print(f"1. Positif dengan status sesuai label artikel benar : {len(pos_ok)}/5")
    print(f"2. Negatif dijawab 'tidak ditemukan/berbeda'         : {len(neg_ok)}/5")
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

    vaksin = next(r for r in neg if VAKSIN_FLU_MARK in r["claim"].lower())
    print("\nH1 (kasus 'vaksin flu bikin mandul'): "
          f"verdict={vaksin['verdict']} id={vaksin['article_id']}")
    if vaksin["verdict"] == "gagal":
        h1 = "BELUM KONKLUSIF (pemanggilan gagal)"
    elif vaksin["verdict"] == "ditemukan" and vaksin["article_id"] == HOAX_TARGET:
        h1 = "GUGUR (memaksakan kecocokan dengan artikel vaksin HPV 36214)"
    else:
        h1 = "TERDUKUNG pada kasus ini (klaim dinyatakan berbeda / tidak ditemukan)"
    print("Status H1:", h1, "-- satu kasus sulit; jangan digeneralisasi.")

    wrong = [r for r in results if (r["kind"] == "positif" and r not in pos_ok)
             or (r["kind"] == "negatif" and r not in neg_ok)]
    fmt_bad = sum(r["parse_failures"] for r in results)
    if failed:
        h3 = f"BELUM KONKLUSIF ({len(failed)} kueri gagal diproses: galat/format)"
    elif fmt_bad >= 2 or len(wrong) >= 2:
        h3 = f"GUGUR (format bermasalah {fmt_bad}x; keliru {len(wrong)}/10)"
    else:
        h3 = f"TERDUKUNG pada sampel ini (keliru {len(wrong)}/10; pelanggaran format {fmt_bad})"
    print("Status H3:", h3)
    print(f"\nHasil lengkap: {OUT_PATH}\nLog panggilan: {LOG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
