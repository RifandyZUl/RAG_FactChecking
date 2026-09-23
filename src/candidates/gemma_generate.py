"""
Hasilkan kandidat butir set uji v1 dari Gemma (sumber buatan_model): positif, negatif sulit
subtipe "angka atau waktu beda", negatif sulit subtipe "entitas sama klaim beda", dan negatif
mudah.

LIVE saat dijalankan langsung sebagai skrip (memanggil API Gemma, mengonsumsi kuota harian).
Logika inti -- pembangun prompt, pemeriksa larangan salin >= 4 kata dari Narasi, pemeriksa
kemiripan judul (sama seperti candidates/screen.py dan crosssite.py), audit kebocoran teks
terhadap ANNOTATION_GUIDE.md + SYSTEM_PROMPT, dan penguraian keluaran JSON -- adalah fungsi
murni, diuji TANPA panggilan API di tests/test_gemma_generate.py (memakai ScriptedProvider palsu
dari tests/_fakes.py).

Hasil disimpan sebagai KANDIDAT untuk ditinjau manusia (data/candidates/gemma_candidates.jsonl),
BUKAN langsung masuk set uji: setiap baris memuat metadata (nama model, versi -- dari metadata
respons API bila tersedia, jika tidak versi SDK terpasang + catatan, lihat
`LLMProvider.model_version_info` -- tanggal, dan nama prompt pembuat) dan hasil pemeriksaan
otomatis (`lolos_pemeriksaan_otomatis`). Kandidat yang gagal pemeriksaan (kebocoran teks, salin
>= 4 kata dari Narasi, kebetulan sangat mirip judul artikel lain, atau memuat penanda data
pribadi -- `pii_flags()`, sama seperti candidates/screen.py, ditambahkan 2026-09-23 setelah
kandidat berisi nomor telepon berpola nomor Indonesia lolos tak tertandai ke tinjauan tahap 3)
TETAP ditulis ke gemma_candidates.jsonl (bukan dihapus diam-diam) tapi ditandai gagal, untuk
jejak audit -- KEDUANYA ditegakkan lewat kode, bukan hanya konvensi: `reviewable_rows`/
`write_review_csv` memastikan kandidat gagal tidak pernah keluar ke berkas tinjauan manusia, dan
`assert_reviewed_before_testset` menolak kandidat gagal sebagai butir set uji (lihat
tests/test_gemma_generate.py untuk uji yang menegakkan keduanya).

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m candidates.gemma_generate --check-budget
  PYTHONPATH=src python -m candidates.gemma_generate --slot positif --target 36120 36111
  PYTHONPATH=src python -m candidates.gemma_generate --slot negatif_angka_waktu --target 36xxx
  PYTHONPATH=src python -m candidates.gemma_generate --slot negatif_entitas_sama --target 36xxx
  PYTHONPATH=src python -m candidates.gemma_generate --slot negatif_mudah --n-negatif-mudah 5
"""

import argparse
import csv
import difflib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from candidates.screen import pii_flags

from chunker import load_articles
from generator import SYSTEM_PROMPT
from llm import LLMConfigError, LLMError, LLMQuotaExhaustedError, get_provider
from llm.ledger import plan_budget
from paths import DATA_DIR, PROJECT_ROOT

N_PER_SLOT = 3
GUIDE_PATH = PROJECT_ROOT / "testset" / "ANNOTATION_GUIDE.md"
OUT_PATH = DATA_DIR / "candidates" / "gemma_candidates.jsonl"

MIN_COPY_NGRAM = 4  # larangan salin >= 4 kata berurutan dari Narasi (slot positif)
MIN_LEAK_NGRAM = 6  # audit kebocoran: >= 6 kata berurutan sama dengan pedoman/prompt dianggap bocor
TITLE_SIMILARITY_FLAG = 0.85  # sama seperti ambang kandidat lintas situs (crosssite.py)

SLOTS = ("positif", "negatif_angka_waktu", "negatif_entitas_sama", "negatif_mudah")

REVIEW_CSV_COLUMNS = [
    "id", "klaim", "url_sumber", "catatan_sumber", "keputusan (setuju/tolak/edit)",
    "label_saya (sama/tidak_sama/batas)", "alasan_saya", "artikel_basis_data_pasangan",
]


def _words(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.lower())


def _ngrams(words: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def copies_ngram(candidate: str, source: str, n: int) -> bool:
    """True bila `candidate` memuat >= n kata berurutan yang identik dengan `source`."""
    cand_words, src_words = _words(candidate), _words(source)
    if len(cand_words) < n or len(src_words) < n:
        return False
    return bool(_ngrams(cand_words, n) & _ngrams(src_words, n))


def title_similarity(text: str, db_titles: dict[str, str]) -> tuple[str, float]:
    """Kemiripan `text` terhadap tiap judul basis data; kembalikan (article_id, skor) tertinggi."""
    return max(
        ((aid, difflib.SequenceMatcher(None, text.lower(), t.lower()).ratio()) for aid, t in db_titles.items()),
        key=lambda x: x[1],
    )


def leak_audit_text() -> str:
    """Teks gabungan pedoman anotasi terkunci + prompt sistem generator, untuk audit kebocoran."""
    guide = GUIDE_PATH.read_text(encoding="utf-8") if GUIDE_PATH.exists() else ""
    return guide + "\n" + SYSTEM_PROMPT


def leak_flag(candidate: str, reference_text: str) -> bool:
    """True bila kandidat memuat >= MIN_LEAK_NGRAM kata berurutan yang sama dengan pedoman/prompt."""
    return copies_ngram(candidate, reference_text, MIN_LEAK_NGRAM)


def build_prompt_positif(narasi: str) -> tuple[str, str]:
    system = (
        "Kamu menulis klaim berbahasa Indonesia sehari-hari untuk set uji sistem pemeriksa fakta, "
        "HANYA berdasarkan potongan Narasi hoaks yang diberikan. JANGAN menyalin empat kata atau "
        "lebih berurutan dari Narasi; parafrasekan dengan kata-katamu sendiri, gaya bahasa bebas "
        "(santai / pesan berantai / salah ketik), tetap mempertahankan unsur inti (subjek, "
        "tindakan, objek atau kondisi pembeda). Balas HANYA JSON tanpa teks lain: "
        f'{{"klaim": ["...", "...", "..."]}} berisi tepat {N_PER_SLOT} variasi klaim.'
    )
    user = f"Narasi:\n{narasi}"
    return system, user


def build_prompt_negatif_angka_waktu(kia: str, narasi: str) -> tuple[str, str]:
    system = (
        "Kamu menulis klaim berbahasa Indonesia sehari-hari untuk set uji NEGATIF sistem pemeriksa "
        "fakta. Ambil klaim inti (KIA) berikut, lalu UBAH salah satu angka atau keterangan waktu di "
        "dalamnya (mis. jumlah, persentase, tanggal, durasi, usia) sehingga menjadi PROPOSISI YANG "
        "SECARA FAKTUAL BERBEDA -- bukan sinonim, bukan salah ketik, tetapi klaim lain yang tidak "
        "akan dijawab sama oleh Kesimpulan artikel aslinya. Subjek, tindakan, dan objek pembeda "
        "lain tetap sama. Balas HANYA JSON tanpa teks lain: "
        f'{{"klaim": ["...", "...", "..."]}} berisi tepat {N_PER_SLOT} variasi klaim.'
    )
    user = f"Klaim inti (KIA): {kia}\nKonteks Narasi:\n{narasi}"
    return system, user


def build_prompt_negatif_entitas_sama(kia: str, narasi: str) -> tuple[str, str]:
    system = (
        "Kamu menulis klaim berbahasa Indonesia sehari-hari untuk set uji NEGATIF sistem pemeriksa "
        "fakta, subtipe 'entitas sama, klaim beda'. Ambil klaim inti (KIA) berikut, PERTAHANKAN "
        "entitas/aktor utamanya (nama orang, lembaga, atau tempat yang sama), tetapi UBAH tindakan "
        "atau proposisi spesifiknya sehingga menjadi klaim yang SECARA FAKTUAL BERBEDA -- bukan "
        "sinonim, dan BUKAN sekadar mengubah angka atau keterangan waktu (itu subtipe lain), "
        "melainkan tindakan/peristiwa lain tentang entitas yang sama, yang tidak akan dijawab sama "
        "oleh Kesimpulan artikel aslinya. Balas HANYA JSON tanpa teks lain: "
        f'{{"klaim": ["...", "...", "..."]}} berisi tepat {N_PER_SLOT} variasi klaim.'
    )
    user = f"Klaim inti (KIA): {kia}\nKonteks Narasi:\n{narasi}"
    return system, user


def build_prompt_negatif_mudah(avoid_categories: list[str]) -> tuple[str, str]:
    avoid = "; ".join(avoid_categories) if avoid_categories else "(tidak ada)"
    system = (
        "Kamu menulis klaim hoaks berbahasa Indonesia sehari-hari yang topiknya JAUH dan TIDAK "
        "berkaitan dengan kategori berikut (untuk set uji NEGATIF sistem pemeriksa fakta -- klaim "
        "yang seharusnya dijawab 'tidak ditemukan di basis data'). Kategori yang harus DIHINDARI: "
        f"{avoid}. Buat klaim dengan topik yang berbeda-beda satu sama lain. Balas HANYA JSON "
        f'tanpa teks lain: {{"klaim": ["...", "...", "..."]}} berisi tepat {N_PER_SLOT} klaim.'
    )
    user = "Buat klaim hoaks dengan topik yang jauh dari kategori yang disebutkan."
    return system, user


def parse_klaim_list(raw: str) -> list[str] | None:
    """Urai keluaran JSON `{"klaim": [...]}`, toleran terhadap pagar kode ```json."""
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)
    try:
        d = json.loads(s)
    except ValueError:
        m = re.search(r"\{.*\}", s, re.DOTALL)
        if not m:
            return None
        try:
            d = json.loads(m.group(0))
        except ValueError:
            return None
    if not isinstance(d, dict):
        return None
    klaim = d.get("klaim")
    if not isinstance(klaim, list) or not klaim or not all(isinstance(x, str) and x.strip() for x in klaim):
        return None
    return [x.strip() for x in klaim]


def run_checks(
    slot: str, text: str, narasi: str | None, db_titles: dict[str, str], reference_text: str,
    target_article: str | None = None,
) -> dict[str, Any]:
    """
    Pemeriksaan otomatis per kandidat. positif: larangan salin Narasi. negatif_*: kemiripan
    terhadap 150 judul basis data (agar tidak kebetulan cocok dengan ARTIKEL LAIN). Semua slot:
    audit kebocoran terhadap pedoman/prompt.

    `target_article`, bila diisi, DIKELUARKAN dari perbandingan judul: untuk subtipe berbasis KIA
    artikel target (negatif_angka_waktu, negatif_entitas_sama), kandidat SEHARUSNYA mirip judul
    artikel targetnya sendiri (itu maksud subtipenya -- KIA yang sama, satu unsur diubah); tanpa
    pengecualian ini pemeriksaan salah menandai kandidat yang justru benar sebagai gagal.
    """
    checks: dict[str, Any] = {"leak_flag": leak_flag(text, reference_text), "pii_flags": pii_flags(text)}
    if slot == "positif":
        checks["copies_narasi_ngram"] = narasi is not None and copies_ngram(text, narasi, MIN_COPY_NGRAM)
    else:
        compare_titles = db_titles
        if target_article is not None and target_article in db_titles:
            compare_titles = {aid: t for aid, t in db_titles.items() if aid != target_article}
        best_id, best_sim = title_similarity(text, compare_titles)
        checks["title_sim_max"] = round(best_sim, 3)
        checks["title_sim_id"] = best_id
        checks["title_sim_flag"] = best_sim >= TITLE_SIMILARITY_FLAG
    return checks


def passed_checks(slot: str, checks: dict[str, Any]) -> bool:
    if checks.get("leak_flag") or checks.get("pii_flags"):
        return False
    if slot == "positif":
        return not checks.get("copies_narasi_ngram", False)
    return not checks.get("title_sim_flag", False)


def reviewable_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Kandidat yang boleh keluar ke berkas tinjauan manusia: HANYA yang lolos pemeriksaan
    otomatis (audit kebocoran, salin Narasi, kemiripan judul -- lihat `passed_checks`).
    Kandidat gagal tetap tersimpan di `gemma_candidates.jsonl` untuk jejak audit (lihat
    docstring modul), tapi tidak pernah keluar dari fungsi ini -- satu-satunya jalur yang
    boleh dipakai untuk menyusun berkas tinjauan (lihat `write_review_csv`).
    """
    return [r for r in rows if r.get("lolos_pemeriksaan_otomatis") is True]


def write_review_csv(rows: list[dict[str, Any]], path: Path) -> int:
    """
    Tulis kandidat yang lolos pemeriksaan otomatis (lihat `reviewable_rows`) sebagai berkas
    tinjauan CSV, format kolom sama dengan `tinjauan_tahap1.csv`/`tinjauan_tahap2.csv`.
    Kandidat gagal (bocor, salin Narasi, atau kebetulan mirip judul lain) TIDAK PERNAH ditulis
    ke sini. Mengembalikan jumlah baris yang ditulis.
    """
    reviewable = reviewable_rows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_CSV_COLUMNS)
        writer.writeheader()
        for i, r in enumerate(reviewable, 1):
            writer.writerow({
                "id": f"gemma-{r['slot']}-{r.get('target_article') or 'batch'}-{i}",
                "klaim": r["klaim"],
                "url_sumber": "",
                "catatan_sumber": f"buatan_model ({r['model']})",
                "keputusan (setuju/tolak/edit)": "",
                "label_saya (sama/tidak_sama/batas)": "",
                "alasan_saya": "",
                "artikel_basis_data_pasangan": r.get("target_article") or "",
            })
    return len(reviewable)


def assert_reviewed_before_testset(candidate: dict[str, Any]) -> None:
    """
    Pengaman terakhir sebelum sebuah kandidat Gemma dipakai sebagai butir set uji: kandidat
    yang gagal pemeriksaan otomatis TIDAK BOLEH masuk, apa pun isi kolom tinjauan manusia
    untuk ID itu. Seharusnya kandidat gagal memang tidak pernah muncul di berkas tinjauan
    (lihat `reviewable_rows`/`write_review_csv`), tapi diperiksa lagi di sini karena penyusun
    set uji nanti membaca ID dari CSV yang bisa saja diedit atau disalin manual.
    """
    if not candidate.get("lolos_pemeriksaan_otomatis"):
        raise ValueError(
            "kandidat gagal pemeriksaan otomatis (leak_flag/copies_narasi_ngram/title_sim_flag) "
            f"tidak boleh masuk set uji: slot={candidate.get('slot')!r} "
            f"target={candidate.get('target_article')!r} klaim={candidate.get('klaim')!r}"
        )


def assert_no_pii(klaim: str, item_id: str = "") -> None:
    """
    Pengaman umum (BUKAN khusus kandidat Gemma) sebelum teks apa pun -- dari sumber mana pun
    (manusia, teks_nyata, liputan6, buatan_model) -- masuk sebagai butir set uji final. Dipakai
    saat menyusun testset/v1.jsonl dari SELURUH sumber, bukan hanya alur candidates.gemma_generate.

    Diperkenalkan 2026-09-23 setelah kandidat gemma-positif-36191-8 (nomor WA berpola nomor
    Indonesia asli) sempat lolos ke tinjauan tahap 3 tak tertandai -- lihat pii_flags di
    candidates/screen.py dan run_checks di modul ini. KETERBATASAN: pii_flags() tidak menangkap
    handle platform tanpa '@' (mis. "TikTok dana.hibh") -- kasus semacam itu masih bergantung
    pada tinjauan manusia, bukan pemeriksaan otomatis ini.
    """
    flags = pii_flags(klaim)
    if flags:
        raise ValueError(f"butir mengandung penanda data pribadi {flags} tidak boleh masuk set uji: "
                          f"id={item_id!r} klaim={klaim!r}")


def generate_for_job(
    provider: Any,
    slot: str,
    target_article: str | None,
    articles: dict[str, dict],
    db_titles: dict[str, str],
    reference_text: str,
) -> list[dict[str, Any]]:
    """
    Jalankan satu permintaan (satu artikel target atau satu batch negatif_mudah), kembalikan
    daftar dict kandidat (termasuk yang gagal pemeriksaan, ditandai `lolos_pemeriksaan_otomatis`).
    Menerima `provider` apa pun yang punya metode `.generate` (LLMProvider ASLI atau PALSU untuk
    uji) -- inilah yang membuat fungsi ini bisa diuji offline.
    """
    narasi = None
    if slot == "positif":
        narasi = articles[target_article]["narasi"]
        system, user = build_prompt_positif(narasi)
    elif slot == "negatif_angka_waktu":
        kia = articles[target_article]["title"]
        system, user = build_prompt_negatif_angka_waktu(kia, articles[target_article]["narasi"])
    elif slot == "negatif_entitas_sama":
        kia = articles[target_article]["title"]
        system, user = build_prompt_negatif_entitas_sama(kia, articles[target_article]["narasi"])
    elif slot == "negatif_mudah":
        avoid = sorted({a["category"] for a in articles.values()})
        system, user = build_prompt_negatif_mudah(avoid)
    else:
        raise ValueError(f"slot tidak dikenal: {slot}")

    raw = provider.generate(system, user)
    versi = provider.model_version_info()
    klaim_list = parse_klaim_list(raw)
    if klaim_list is None:
        return [{
            "slot": slot, "target_article": target_article, "klaim": None,
            "model": provider.model, "versi": versi,
            "dibuat_pada": datetime.now(timezone.utc).isoformat(),
            "prompt_pembuat": f"{slot}_v1", "sumber": "buatan_model",
            "galat": "gagal urai JSON", "raw": raw[:500],
            "pemeriksaan": {}, "lolos_pemeriksaan_otomatis": False,
            "status": "gagal format, dibuang",
        }]

    out = []
    for text in klaim_list[:N_PER_SLOT]:
        checks = run_checks(slot, text, narasi, db_titles, reference_text, target_article)
        out.append({
            "slot": slot, "target_article": target_article, "klaim": text,
            "model": provider.model, "versi": versi,
            "dibuat_pada": datetime.now(timezone.utc).isoformat(),
            "prompt_pembuat": f"{slot}_v1", "sumber": "buatan_model",
            "pemeriksaan": checks, "lolos_pemeriksaan_otomatis": passed_checks(slot, checks),
            "status": "kandidat, belum ditinjau",
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--model", default="gemma-4-31b-it")
    ap.add_argument("--check-budget", action="store_true",
                    help="hanya laporkan anggaran kuota harian; tidak ada panggilan LLM")
    ap.add_argument("--slot", choices=SLOTS)
    ap.add_argument("--target", nargs="+", default=[],
                    help="article_id target (untuk slot positif / negatif_angka_waktu)")
    ap.add_argument("--n-negatif-mudah", type=int, default=0,
                    help="jumlah permintaan negatif_mudah (tiap permintaan = hingga "
                         f"{N_PER_SLOT} kandidat)")
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    jobs: list[tuple[str, str | None]] = []
    if args.slot in ("positif", "negatif_angka_waktu", "negatif_entitas_sama"):
        jobs = [(args.slot, aid) for aid in args.target]
    elif args.slot == "negatif_mudah":
        jobs = [("negatif_mudah", None) for _ in range(args.n_negatif_mudah)]

    try:
        provider = get_provider(model=args.model, thinking_level="minimal")
    except LLMConfigError as e:
        print(f"Konfigurasi LLM belum siap: {e}")
        return 2

    if provider.ledger is not None and provider.limits is not None:
        plan = plan_budget(provider.ledger, provider.limits, len(jobs), 1)
        print(f"{provider.model} | RPM {provider.limits.rpm} | TPM {provider.limits.tpm} | {plan.describe()}")
        if jobs and not plan.ok:
            print(f"TIDAK DIMULAI: {len(jobs)} permintaan dibutuhkan, {plan.remaining} tersisa.")
            return 4
    else:
        print("Batas kuota model ini tidak dikenal: anggaran harian tidak dihitung.")
    if args.check_budget:
        return 0
    if not jobs:
        print("Tidak ada pekerjaan (tentukan --slot dengan --target atau --n-negatif-mudah).")
        return 0

    articles = {a["article_id"]: a for a in load_articles()}
    db_titles = {aid: a["title"] for aid, a in articles.items()}
    reference_text = leak_audit_text()

    all_out: list[dict[str, Any]] = []
    for slot, aid in jobs:
        try:
            rows = generate_for_job(provider, slot, aid, articles, db_titles, reference_text)
        except LLMQuotaExhaustedError as e:
            print(f"BERHENTI: {e}")
            break
        except LLMError as e:
            print(f"[gagal panggilan] {slot} {aid}: {e}")
            continue
        all_out.extend(rows)
        for r in rows:
            mark = "lolos" if r["lolos_pemeriksaan_otomatis"] else "GAGAL"
            print(f"  [{mark}] {slot} {aid or ''}: {r.get('klaim') or r.get('galat')}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a", encoding="utf-8") as f:
        for c in all_out:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    n_pass = sum(r["lolos_pemeriksaan_otomatis"] for r in all_out)
    print(f"\n{len(all_out)} kandidat -> {args.out} "
          f"({n_pass} lolos pemeriksaan otomatis, {len(all_out) - n_pass} ditandai gagal)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
