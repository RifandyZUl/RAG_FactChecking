"""
Analisis metrik set uji v1 dari hasil evaluasi mentah -- TIDAK memanggil API, TIDAK mengubah
testset/v1.jsonl, prompt, atau logika generator apa pun. Metrik dapat dihitung ulang kapan saja
tanpa biaya karena hanya membaca berkas lokal:

  - data/testset_v1_eval_<model>.jsonl : hasil mentah 3 run x 54 butir (evaluation.testset_eval)
  - testset/v1.jsonl                   : butir + label pra-registrasi
  - testset/v1.meta.json               : daftar pasangan minimal (dipakai VERBATIM, tidak
                                          diturunkan ulang) dan ambang H1/H3 pra-registrasi
  - data/articles.json                 : HANYA untuk memeriksa URL di luar metadata (Aturan
                                          Wajib #3) -- baca lokal (chunker.load_articles()),
                                          BUKAN panggilan API

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m evaluation.testset_analysis [--eval-file PATH] [--out PATH]
"""

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from chunker import load_articles
from evaluation.metrics import ERROR_TYPES, classify_error, wilson_interval
from generator import find_urls
from paths import DATA_DIR, PROJECT_ROOT

V1_PATH = PROJECT_ROOT / "testset" / "v1.jsonl"
META_PATH = PROJECT_ROOT / "testset" / "v1.meta.json"
DEFAULT_EVAL_PATH = DATA_DIR / "testset_v1_eval_gemini-3.5-flash-lite.jsonl"

NO_MODE = "tanpa_modus"  # verdict sentinel: ketiga run berbeda, tidak ada 2 yang sepakat


# ---------------------------------------------------------------------------------------------
# Muat data
# ---------------------------------------------------------------------------------------------

def load_v1_items(path: Path = V1_PATH) -> dict[str, dict[str, Any]]:
    return {r["id"]: r for r in (json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip())}


def load_eval_records(path: Path) -> dict[str, list[dict[str, Any]]]:
    """id butir -> daftar rekam per run (diurutkan berdasarkan nomor run)."""
    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            by_id[r["id"]].append(r)
    for recs in by_id.values():
        recs.sort(key=lambda r: r["run"])
    return dict(by_id)


def load_meta(path: Path = META_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------
# Keputusan modus dan kesepakatan antar-run
# ---------------------------------------------------------------------------------------------

def compute_mode(records: list[dict[str, Any]]) -> tuple[str, str | None, bool]:
    """
    (verdict, article_id, ada_modus) dari 3 run: keputusan (verdict, article_id) yang muncul
    pada >= 2 dari 3 run. Bila ketiganya berbeda, verdict=NO_MODE, article_id=None,
    ada_modus=False -- dilaporkan sebagai kasus tersendiri, TIDAK dihitung sebagai jawaban salah
    atau benar (dikeluarkan dari penyebut akurasi/kesalahan, sama seperti status "gagal" pada
    evaluation.metrics, karena tidak ada keputusan tunggal yang bisa dinilai).
    """
    decisions = [(r["verdict"], r["article_id"]) for r in records]
    (verdict, article_id), n = Counter(decisions).most_common(1)[0]
    if n >= 2:
        return verdict, article_id, True
    return NO_MODE, None, False


def agreement_kind(records: list[dict[str, Any]]) -> str:
    """'bulat' (3/3 sama) | 'mayoritas' (2/3 sama) | 'tanpa_modus' (semua beda)."""
    decisions = [(r["verdict"], r["article_id"]) for r in records]
    counts = Counter(decisions)
    top_n = counts.most_common(1)[0][1]
    if top_n == 3:
        return "bulat"
    if top_n == 2:
        return "mayoritas"
    return NO_MODE


# ---------------------------------------------------------------------------------------------
# A.3-A.4: akurasi + jenis kesalahan (memakai evaluation.metrics, dievaluasi pada butir modus)
# ---------------------------------------------------------------------------------------------

def mode_records_for(item_ids: list[str], v1_items: dict, eval_by_id: dict) -> list[dict[str, Any]]:
    """Satu 'rekam modus' per butir: expected_* dari v1.jsonl, verdict/article_id dari modus."""
    out = []
    for id_ in item_ids:
        item = v1_items[id_]
        verdict, article_id, ada_modus = compute_mode(eval_by_id[id_])
        out.append({
            "id": id_, "batas": item["batas"],
            "expected_verdict": item["expected_verdict"],
            "expected_retrieval_article": item["expected_retrieval_article"],
            "verdict": verdict, "article_id": article_id, "ada_modus": ada_modus,
        })
    return out


def accuracy_with_wilson(mode_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Akurasi keseluruhan (Wilson 95%) atas butir YANG PUNYA MODUS; tanpa-modus dilaporkan terpisah."""
    with_mode = [r for r in mode_records if r["ada_modus"]]
    no_mode = [r for r in mode_records if not r["ada_modus"]]
    correct = sum(1 for r in with_mode if classify_error(
        r["expected_verdict"], r["expected_retrieval_article"], r["verdict"], r["article_id"]) is None)
    n = len(with_mode)
    lo, hi = wilson_interval(correct, n)
    return {
        "n_total_butir": len(mode_records), "n_dengan_modus": n, "n_tanpa_modus": len(no_mode),
        "benar": correct, "wilson95": [round(lo, 4), round(hi, 4)],
        "id_tanpa_modus": [r["id"] for r in no_mode],
    }


def error_breakdown(mode_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Tiga jenis kesalahan (kecocokan_palsu/penolakan_palsu/artikel_salah), Wilson 95%,
    dihitung atas butir yang punya modus SAJA (per jenis expected_verdict)."""
    with_mode = [r for r in mode_records if r["ada_modus"]]
    n_belum = sum(1 for r in with_mode if r["expected_verdict"] == "belum_ditemukan")
    n_ditemukan = sum(1 for r in with_mode if r["expected_verdict"] == "ditemukan")
    counts = dict.fromkeys(ERROR_TYPES, 0)
    detail: dict[str, list[str]] = {t: [] for t in ERROR_TYPES}
    for r in with_mode:
        err = classify_error(r["expected_verdict"], r["expected_retrieval_article"], r["verdict"], r["article_id"])
        if err in ERROR_TYPES:
            counts[err] += 1
            detail[err].append(r["id"])
    denom = {"kecocokan_palsu": n_belum, "penolakan_palsu": n_ditemukan, "artikel_salah": n_ditemukan}
    return {
        t: {"k": counts[t], "n": denom[t], "wilson95": [round(x, 4) for x in wilson_interval(counts[t], denom[t])],
            "id_butir": detail[t]}
        for t in ERROR_TYPES
    }


# ---------------------------------------------------------------------------------------------
# A.5: Recall@3
# ---------------------------------------------------------------------------------------------

def recall_at_3(item_ids: list[str], eval_by_id: dict) -> dict[str, Any]:
    """Recall@3 memakai recall_at_3 yang disimpan runner. Retrieval deterministik -> ketiga run
    SEHARUSNYA identik per butir; inkonsistensi dilaporkan sebagai temuan data, bukan disembunyikan."""
    hits, total, inconsistent = 0, 0, []
    for id_ in item_ids:
        recs = eval_by_id[id_]
        values = {r["recall_at_3"] for r in recs}
        if len(values) > 1:
            inconsistent.append({"id": id_, "nilai_per_run": [r["recall_at_3"] for r in recs]})
        v = recs[0]["recall_at_3"]
        if v is None:
            continue
        total += 1
        hits += int(v)
    lo, hi = wilson_interval(hits, total)
    return {"k": hits, "n": total, "wilson95": [round(lo, 4), round(hi, 4)], "run_tidak_konsisten": inconsistent}


# ---------------------------------------------------------------------------------------------
# A.6: akurasi per sumber / tipe / subtipe
# ---------------------------------------------------------------------------------------------

def accuracy_by_group(mode_records: list[dict[str, Any]], v1_items: dict, group_field: str) -> dict[str, Any]:
    groups: dict[Any, list[dict]] = defaultdict(list)
    for r in mode_records:
        groups[v1_items[r["id"]][group_field]].append(r)
    return {str(g): accuracy_with_wilson(rows) for g, rows in groups.items()}


# ---------------------------------------------------------------------------------------------
# A.7: pasangan minimal (VERBATIM dari v1.meta.json, tidak diturunkan ulang)
# ---------------------------------------------------------------------------------------------

def is_correct(mode_records_by_id: dict[str, dict], id_: str) -> bool | None:
    r = mode_records_by_id[id_]
    if not r["ada_modus"]:
        return None
    return classify_error(r["expected_verdict"], r["expected_retrieval_article"], r["verdict"], r["article_id"]) is None


def minimal_pair_analysis(meta: dict, v1_items: dict, mode_records_by_id: dict[str, dict]) -> dict[str, Any]:
    daftar = meta["hasil_penyusunan_testset_v1_2026-09-23"]["pasangan_minimal_2026-09-23"]["hasil"]["daftar_pasangan"]
    positif_by_article = {v["expected_retrieval_article"]: k for k, v in v1_items.items()
                          if v["tipe"] == "positif"}
    per_subtipe: dict[str, dict[str, Any]] = defaultdict(lambda: {"pasangan": [], "kedua_benar": 0, "n": 0})
    for pair in daftar:
        pos_id = positif_by_article[pair["artikel"]]
        neg_id = pair["negatif_sulit"]
        pos_ok, neg_ok = is_correct(mode_records_by_id, pos_id), is_correct(mode_records_by_id, neg_id)
        both_ok = bool(pos_ok) and bool(neg_ok) if pos_ok is not None and neg_ok is not None else None
        sub = per_subtipe[pair["subtipe"]]
        sub["n"] += 1
        sub["pasangan"].append({"artikel": pair["artikel"], "positif": pos_id, "negatif_sulit": neg_id,
                                "positif_benar": pos_ok, "negatif_sulit_benar": neg_ok, "kedua_benar": both_ok})
        if both_ok:
            sub["kedua_benar"] += 1
    return dict(per_subtipe)


# ---------------------------------------------------------------------------------------------
# A.8: H1 / H3
# ---------------------------------------------------------------------------------------------

def h1_status(mode_records: list[dict[str, Any]], meta: dict) -> dict[str, Any]:
    neg_sulit = [r for r in mode_records if r["id"] and v1_tipe(r) == "negatif_sulit"]
    return _h1_from_negsulit(neg_sulit, meta)


def _h1_from_negsulit(neg_sulit: list[dict[str, Any]], meta: dict) -> dict[str, Any]:
    kecocokan_palsu = sum(1 for r in neg_sulit if r["ada_modus"] and r["verdict"] == "ditemukan")
    ambang = meta["ambang"]["H1"]
    if kecocokan_palsu <= 1:
        status = f"TERDUKUNG ({kecocokan_palsu}/{len(neg_sulit)} <= 1, ambang: {ambang['terdukung']})"
    elif kecocokan_palsu == 2:
        status = f"TIDAK KONKLUSIF ({kecocokan_palsu}/{len(neg_sulit)}, ambang: {ambang['tidak_konklusif']})"
    else:
        status = f"GUGUR ({kecocokan_palsu}/{len(neg_sulit)} >= 3, ambang: {ambang['gugur']})"
    return {"kecocokan_palsu": kecocokan_palsu, "n_negatif_sulit": len(neg_sulit), "status": status}


def h3_status(mode_records_non_batas: list[dict[str, Any]], n_format_violations: int, meta: dict) -> dict[str, Any]:
    n_salah = sum(1 for r in mode_records_non_batas if r["ada_modus"] and classify_error(
        r["expected_verdict"], r["expected_retrieval_article"], r["verdict"], r["article_id"]) is not None)
    n_salah += sum(1 for r in mode_records_non_batas if not r["ada_modus"])  # tanpa modus = kesalahan untuk H3
    ambang = meta["ambang"]["H3"]
    gugur = n_salah >= 5 or n_format_violations >= 2
    status = (f"GUGUR (kesalahan {n_salah}/{len(mode_records_non_batas)}, pelanggaran format "
              f"{n_format_violations}; ambang: {ambang['gugur']})" if gugur else
              f"TERDUKUNG pada sampel ini (kesalahan {n_salah}/{len(mode_records_non_batas)}, "
              f"pelanggaran format {n_format_violations})")
    return {"n_kesalahan": n_salah, "n_butir": len(mode_records_non_batas),
            "n_pelanggaran_format": n_format_violations, "status": status}


def v1_tipe(mode_record: dict[str, Any]) -> str:
    return mode_record.get("_tipe", "")


# ---------------------------------------------------------------------------------------------
# B: diagnostik
# ---------------------------------------------------------------------------------------------

def disagreements(v1_items: dict, eval_by_id: dict) -> list[dict[str, Any]]:
    out = []
    for id_, recs in eval_by_id.items():
        kind = agreement_kind(recs)
        if kind != "bulat":
            out.append({
                "id": id_, "klaim": v1_items[id_]["klaim"], "kesepakatan": kind,
                "per_run": [{"run": r["run"], "verdict": r["verdict"], "article_id": r["article_id"],
                            "alasan": r["alasan"]} for r in recs],
            })
    return out


def format_violations(eval_by_id: dict) -> dict[str, Any]:
    total = 0
    per_butir: dict[str, int] = {}
    for id_, recs in eval_by_id.items():
        n = sum(p["parse_failures"] for r in recs for p in r["percobaan"])
        if n:
            per_butir[id_] = n
            total += n
    return {"total": total, "per_butir": per_butir}


def urls_outside_metadata(eval_by_id: dict, articles_by_id: dict) -> dict[str, Any]:
    """Aturan Wajib #3: URL pada keluaran mentah LLM yang tidak berasal dari metadata kandidat
    (url artikel + references) yang ditunjukkan pada butir itu. Dicek pada raw_outputs (keluaran
    mentah), bukan klarifikasi/alasan tersimpan (yang sudah melalui strip_urls di generator.py)."""
    total = 0
    per_butir: dict[str, list[str]] = {}
    for id_, recs in eval_by_id.items():
        found: list[str] = []
        for r in recs:
            allowed: set[str] = set()
            for c in r["retrieval_top3"]:
                a = articles_by_id.get(c["article_id"])
                if a:
                    allowed.add(a["url"])
                    allowed.update(a["references"])
            for p in r["percobaan"]:
                for raw in p["raw_outputs"]:
                    found.extend(u for u in find_urls(raw, loose=True) if u not in allowed)
        if found:
            per_butir[id_] = found
            total += len(found)
    return {"total": total, "per_butir": per_butir}


def latency_and_tokens_per_run(eval_by_id: dict) -> dict[int, dict[str, float]]:
    per_run: dict[int, list[dict[str, float]]] = defaultdict(list)
    for recs in eval_by_id.values():
        for r in recs:
            calls = [c for p in r["percobaan"] for c in p["calls"]]
            lat = sum(c["latency_s"] for c in calls)
            tok_in = sum(c["input_tokens"] or 0 for c in calls)
            tok_out = sum(c["output_tokens"] or 0 for c in calls)
            per_run[r["run"]].append({"latency": lat, "tok_in": tok_in, "tok_out": tok_out})
    return {
        run: {
            "latensi_rata2_s": round(statistics.mean(x["latency"] for x in rows), 2),
            "token_masuk_rata2": round(statistics.mean(x["tok_in"] for x in rows), 1),
            "token_keluar_rata2": round(statistics.mean(x["tok_out"] for x in rows), 1),
            "n_butir": len(rows),
        }
        for run, rows in per_run.items()
    }


# ---------------------------------------------------------------------------------------------
# C: caveat wajib (teks tetap, dicetak di keluaran laporan -- bukan hanya di v1.meta.json)
# ---------------------------------------------------------------------------------------------

CAVEATS = """\
CAVEAT WAJIB (baca sebelum menafsirkan angka di atas):

1. KETERGANTUNGAN ARTIKEL JANGKAR: 11 artikel dipakai lebih dari satu butir (24/54 butir, 44%
   dari seluruh set uji). Butir yang berbagi artikel jangkar TIDAK saling independen -- satu
   kegagalan retrieval pada artikel itu dapat menjatuhkan beberapa butir sekaligus. Interval
   Wilson 95% di atas mengasumsikan butir saling bebas (i.i.d.) dan akan TERLALU PERCAYA DIRI
   (interval lebih sempit dari yang sebenarnya) bila asumsi itu dilanggar.

2. PASANGAN MINIMAL SUBTIPE "ANGKA ATAU WAKTU BEDA" ADALAH HASIL KONSTRUKSI, BUKAN PENGAMATAN:
   seluruh 6 pasangan minimal subtipe ini sengaja diarahkan ke artikel yang sudah punya butir
   positif (keputusan desain saat generasi Gemma), bukan kebetulan yang muncul dari populasi
   independen. Kesimpulan H1 dari analisis pasangan minimal keseluruhan (bukan per subtipe)
   bertumpu terutama pada subtipe ini.

3. CONFOUND SUMBER: subtipe "angka atau waktu beda" 100% buatan_model (Gemma); "negatif mudah"
   0% buatan_model (seluruh 15 kandidat Gemma ditolak pemilik proyek, digantikan teks_nyata).
   Pada kedua sel ini, efek SUMBER dan efek TIPE/SUBTIPE BUTIR tidak dapat dipisahkan -- akurasi
   tinggi/rendah pada sel itu bisa jadi mencerminkan kualitas sumber, bukan kesulitan subtipe.

4. UKURAN SAMPEL: 50 butir non-batas (dari mana pun metriknya dihitung) HANYA MENDETEKSI
   KEGAGALAN YANG JELAS. Batas bawah Wilson 95% bila SEMUA benar hanya ~0,84 (n=20) dan ~0,89
   (n=30) -- angka di atas TIDAK MENDUKUNG klaim akurasi di atas 95%, betapa pun tingginya
   proporsi benar yang teramati.
"""


# ---------------------------------------------------------------------------------------------
# Orkestrasi
# ---------------------------------------------------------------------------------------------

def run_analysis(eval_path: Path, v1_path: Path = V1_PATH, meta_path: Path = META_PATH,
                 articles: list[dict] | None = None) -> dict[str, Any]:
    v1_items = load_v1_items(v1_path)
    eval_by_id = load_eval_records(eval_path)
    meta = load_meta(meta_path)
    if articles is None:
        articles = load_articles()
    articles_by_id = {a["article_id"]: a for a in articles}

    all_ids = list(v1_items)
    non_batas_ids = [i for i in all_ids if not v1_items[i]["batas"]]
    batas_ids = [i for i in all_ids if v1_items[i]["batas"]]

    mode_non_batas = mode_records_for(non_batas_ids, v1_items, eval_by_id)
    mode_batas = mode_records_for(batas_ids, v1_items, eval_by_id)
    mode_all = mode_non_batas + mode_batas
    for r in mode_all:
        r["_tipe"] = v1_items[r["id"]]["tipe"]
    mode_by_id = {r["id"]: r for r in mode_all}

    kesepakatan_per_kekhususan: dict[str, Counter] = defaultdict(Counter)
    for id_ in all_ids:
        kesepakatan_per_kekhususan[v1_items[id_]["kekhususan"]][agreement_kind(eval_by_id[id_])] += 1

    fmt = format_violations(eval_by_id)
    urls = urls_outside_metadata(eval_by_id, articles_by_id)

    positif_negsulit_ids = [i for i in non_batas_ids if v1_items[i]["tipe"] in ("positif", "negatif_sulit")]
    result = {
        "n_butir_v1jsonl": len(all_ids), "n_non_batas": len(non_batas_ids), "n_batas": len(batas_ids),
        "A_akurasi_non_batas": accuracy_with_wilson(mode_non_batas),
        "A_akurasi_batas": accuracy_with_wilson(mode_batas),
        "A_kesepakatan_per_kekhususan": {k: dict(v) for k, v in kesepakatan_per_kekhususan.items()},
        "A_jenis_kesalahan_non_batas": error_breakdown(mode_non_batas),
        "A_jenis_kesalahan_batas": error_breakdown(mode_batas),
        "A_recall_at_3_non_batas": recall_at_3([i for i in non_batas_ids
                                                if v1_items[i]["expected_retrieval_article"]], eval_by_id),
        "A_recall_at_3_batas": recall_at_3(batas_ids, eval_by_id),
        "A_akurasi_per_sumber": accuracy_by_group(mode_non_batas, v1_items, "sumber"),
        "A_akurasi_per_tipe": accuracy_by_group(mode_all, v1_items, "tipe"),
        "A_akurasi_per_subtipe": accuracy_by_group(
            [r for r in mode_non_batas if v1_items[r["id"]]["subtipe"]], v1_items, "subtipe"),
        "A_pasangan_minimal_per_subtipe": minimal_pair_analysis(meta, v1_items, mode_by_id),
        "A_H1": h1_status(mode_non_batas, meta),
        "A_H3": h3_status(mode_non_batas, fmt["total"], meta),
        "B_disagreements": disagreements(v1_items, eval_by_id),
        "B_format_violations": fmt,
        "B_urls_outside_metadata": urls,
        "B_latency_tokens_per_run": latency_and_tokens_per_run(eval_by_id),
    }
    return result


def format_report(result: dict[str, Any]) -> str:
    lines = [CAVEATS, "=" * 78, "RINGKASAN METRIK SET UJI V1", "=" * 78]

    a = result["A_akurasi_non_batas"]
    lo, hi = a["wilson95"]
    lines.append(f"\nA.3 Akurasi NON-BATAS (metrik utama): {a['benar']}/{a['n_dengan_modus']} "
                f"Wilson95 [{lo:.3f}; {hi:.3f}] | tanpa modus: {a['n_tanpa_modus']} {a['id_tanpa_modus']}")
    b = result["A_akurasi_batas"]
    lo, hi = b["wilson95"]
    lines.append(f"A.3 Akurasi BATAS (terpisah, bukan metrik utama): {b['benar']}/{b['n_dengan_modus']} "
                f"Wilson95 [{lo:.3f}; {hi:.3f}] | tanpa modus: {b['n_tanpa_modus']} {b['id_tanpa_modus']}")

    lines.append("\nA.2 Kesepakatan antar-run per kekhususan:")
    for kekhususan, counts in result["A_kesepakatan_per_kekhususan"].items():
        lines.append(f"  {kekhususan}: {dict(counts)}")

    lines.append("\nA.4 Jenis kesalahan NON-BATAS:")
    for t, e in result["A_jenis_kesalahan_non_batas"].items():
        lo, hi = e["wilson95"]
        lines.append(f"  {t}: {e['k']}/{e['n']} Wilson95 [{lo:.3f}; {hi:.3f}] {e['id_butir']}")
    lines.append("A.4 Jenis kesalahan BATAS:")
    for t, e in result["A_jenis_kesalahan_batas"].items():
        lo, hi = e["wilson95"]
        lines.append(f"  {t}: {e['k']}/{e['n']} Wilson95 [{lo:.3f}; {hi:.3f}] {e['id_butir']}")

    r3 = result["A_recall_at_3_non_batas"]
    lo, hi = r3["wilson95"]
    lines.append(f"\nA.5 Recall@3 NON-BATAS: {r3['k']}/{r3['n']} Wilson95 [{lo:.3f}; {hi:.3f}]"
                f"{' | INKONSISTEN antar-run: ' + str(r3['run_tidak_konsisten']) if r3['run_tidak_konsisten'] else ''}")
    r3b = result["A_recall_at_3_batas"]
    lo, hi = r3b["wilson95"]
    lines.append(f"A.5 Recall@3 BATAS: {r3b['k']}/{r3b['n']} Wilson95 [{lo:.3f}; {hi:.3f}]")

    lines.append("\nA.6 Akurasi per sumber:")
    for sumber, acc in result["A_akurasi_per_sumber"].items():
        lo, hi = acc["wilson95"]
        lines.append(f"  {sumber}: {acc['benar']}/{acc['n_dengan_modus']} Wilson95 [{lo:.3f}; {hi:.3f}]")
    lines.append("A.6 Akurasi per tipe:")
    for tipe, acc in result["A_akurasi_per_tipe"].items():
        lo, hi = acc["wilson95"]
        lines.append(f"  {tipe}: {acc['benar']}/{acc['n_dengan_modus']} Wilson95 [{lo:.3f}; {hi:.3f}]")
    lines.append("A.6 Akurasi per subtipe:")
    for sub, acc in result["A_akurasi_per_subtipe"].items():
        lo, hi = acc["wilson95"]
        lines.append(f"  {sub}: {acc['benar']}/{acc['n_dengan_modus']} Wilson95 [{lo:.3f}; {hi:.3f}]")

    lines.append("\nA.7 Pasangan minimal per subtipe (kedua butir benar / total pasangan):")
    for sub, info in result["A_pasangan_minimal_per_subtipe"].items():
        lines.append(f"  {sub}: {info['kedua_benar']}/{info['n']}")
        for p in info["pasangan"]:
            lines.append(f"    artikel {p['artikel']}: positif={p['positif']}({p['positif_benar']}) "
                        f"negatif_sulit={p['negatif_sulit']}({p['negatif_sulit_benar']}) "
                        f"kedua_benar={p['kedua_benar']}")

    lines.append(f"\nA.8 Status H1: {result['A_H1']['status']}")
    lines.append(f"A.8 Status H3: {result['A_H3']['status']}")

    lines.append(f"\nB.1 Butir tidak bulat antar-run ({len(result['B_disagreements'])}):")
    for d in result["B_disagreements"]:
        lines.append(f"  {d['id']} ({d['kesepakatan']}): {d['klaim'][:60]!r}")
        for pr in d["per_run"]:
            lines.append(f"    run {pr['run']}: {pr['verdict']} {pr['article_id'] or ''} -- {pr['alasan'][:100]!r}")

    lines.append(f"\nB.3 Pelanggaran format: total={result['B_format_violations']['total']} "
                f"per_butir={result['B_format_violations']['per_butir']}")
    lines.append(f"B.3 URL di luar metadata: total={result['B_urls_outside_metadata']['total']} "
                f"per_butir={result['B_urls_outside_metadata']['per_butir']}")

    lines.append("\nB.4 Latensi & token rata-rata per run:")
    for run, s in sorted(result["B_latency_tokens_per_run"].items()):
        lines.append(f"  run {run}: latensi={s['latensi_rata2_s']}s token_masuk={s['token_masuk_rata2']} "
                    f"token_keluar={s['token_keluar_rata2']} (n={s['n_butir']})")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--eval-file", type=Path, default=DEFAULT_EVAL_PATH)
    ap.add_argument("--out", type=Path, default=None, help="simpan laporan JSON lengkap ke berkas ini")
    args = ap.parse_args()

    result = run_analysis(args.eval_file)
    print(format_report(result))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nLaporan JSON lengkap: {args.out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
