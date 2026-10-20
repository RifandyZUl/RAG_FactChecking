"""
Analisis evaluasi eksternal (docs/rancangan_evaluasi_eksternal.md bagian 6-7), dalam urutan yang dikunci:

  --keandalan     kappa uji ulang 30 butir (7.3-7.4) dan hasil 7 butir audit (7.1); TANPA membuka hasil sistem
  --label-final   label final 99 butir (7.5) -> label_final.json (menolak menimpa); TANPA membuka hasil sistem
  --metrik        BUKA SEGEL: metrik 6.1-6.3, kepatuhan, sensitivitas; hanya bila label_final.json = hash tercatat
  --retrieval-pembanding   Recall@3 kueri judul vs kueri kutipan tanpa LLM (memuat bge-m3; bagian 4 butir 3)

Label final dan keandalan tidak pernah dihitung dari jawaban sistem; --metrik menolak berjalan sebelum hash label
final tercatat di kode (commit yang sama dengan catatan di rancangan 7.5) -- dengan begitu label terkunci sebelum
segel dibuka. Hasil per butir berisi teks pesan tidak pernah dicetak.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m evaluation.external_analysis --keandalan
  PYTHONPATH=src python -m evaluation.external_analysis --label-final
  PYTHONPATH=src python -m evaluation.external_analysis --metrik
"""

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from paths import DATA_DIR, PROJECT_ROOT

FROZEN_PATH = PROJECT_ROOT / "testset" / "eksternal_butir.json"
SESSION_DIR = DATA_DIR / "candidates" / "sesi_buta_eksternal"
SESSION_RESULT_PATH = SESSION_DIR / "hasil_sesi_buta.json"
AUDIT_PATH = DATA_DIR / "candidates" / "celah_liputan6" / "audit_jejak_identik.json"
RELIABILITY_PATH = SESSION_DIR / "keandalan_label.json"
FINAL_LABELS_PATH = SESSION_DIR / "label_final.json"
NONE = "TIDAK ADA"
BOOT_N, BOOT_SEED = 10_000, 20261027  # 7.3
KAPPA_BANDS = ((0.80, "pakai_apa_adanya"), (0.60, "dua_arah"), (float("-inf"), "bukan_gerbang"))  # 7.4


# ---------------------------------------------------------------------------------------------
# Kappa (7.3)
# ---------------------------------------------------------------------------------------------

def cohen_kappa(a: list[str], b: list[str]) -> float | None:
    """Kappa Cohen untuk kategori nominal; None bila tidak terdefinisi (kesepakatan peluang = 1)."""
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe >= 1 else (po - pe) / (1 - pe)


def bootstrap_kappa(a: list[str], b: list[str], n_boot: int = BOOT_N, seed: int = BOOT_SEED) -> dict[str, Any]:
    """Interval 95% bootstrap persentil (ulang-sampel butir berpasangan); ulangan tak terdefinisi dihitung dan dibuang."""
    rng, n, vals, undefined = random.Random(seed), len(a), [], 0
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        k = cohen_kappa([a[i] for i in idx], [b[i] for i in idx])
        if k is None:
            undefined += 1
        else:
            vals.append(k)
    vals.sort()
    ci = [round(vals[int(0.025 * (len(vals) - 1))], 4), round(vals[int(0.975 * (len(vals) - 1))], 4)] if vals else None
    return {"ci95_bootstrap_persentil": ci, "ulangan": n_boot, "benih": seed, "ulangan_tak_terdefinisi_dibuang": undefined}


def kappa_band(k: float | None) -> str:
    if k is None:
        return "tak_terdefinisi"
    return next(name for lo, name in KAPPA_BANDS if k >= lo)


def label_of(case: dict[str, Any]) -> str:
    return case["expected_article"] if case["expected_verdict"] == "ditemukan" else NONE


def direction(old: str, new: str) -> str:
    if old == new:
        return "sama"
    if new == NONE:
        return "cocok_ke_TIDAK_ADA"
    if old == NONE:
        return "TIDAK_ADA_ke_cocok"
    return "id_lain"


def agreement(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    old, new = [p[0] for p in pairs], [p[1] for p in pairs]
    bin_old, bin_new = ["cocok" if x != NONE else NONE for x in old], ["cocok" if x != NONE else NONE for x in new]
    kb, ki = cohen_kappa(bin_old, bin_new), cohen_kappa(old, new)
    return {"n": len(pairs),
            "biner": {"kappa": None if kb is None else round(kb, 4), "sepakat": sum(x == y for x, y in zip(bin_old, bin_new)),
                      **bootstrap_kappa(bin_old, bin_new)},
            "id_persis": {"kappa": None if ki is None else round(ki, 4), "sepakat": sum(x == y for x, y in zip(old, new)),
                          **bootstrap_kappa(old, new)},
            "arah_perubahan": dict(Counter(direction(x, y) for x, y in pairs))}


def load_frozen() -> dict[str, dict[str, Any]]:
    return {c["kode"]: c for c in json.loads(FROZEN_PATH.read_text(encoding="utf-8"))["butir"]}


def load_session() -> list[dict[str, Any]]:
    res = json.loads(SESSION_RESULT_PATH.read_text(encoding="utf-8"))
    if res["perlu_ditanyakan"] or len(res["keputusan"]) != 37:
        raise SystemExit("hasil sesi buta belum lengkap: jalankan candidates.blind_workbook --read lebih dulu")
    return res["keputusan"]


def reliability(cases: dict[str, dict[str, Any]], session: list[dict[str, Any]], audit: dict[str, Any]) -> dict[str, Any]:
    """Kappa 30 butir uji ulang (gabungan, P2, P1) dan hasil 7 butir audit. Label utama tidak diubah di sini."""
    retest = [d for d in session if d["jenis_butir"] == "uji_ulang"]
    rows = [{"kode": d["kode"], "putaran": d["putaran"], "lama": label_of(cases[d["kode"]]), "sesi": d["keputusan"],
             "ragu_lama": cases[d["kode"]]["ragu"], "ragu_sesi": d["ragu"]} for d in retest]
    for r in rows:
        r["arah"] = direction(r["lama"], r["sesi"])

    def group(rs: list[dict[str, Any]]) -> dict[str, Any]:
        return agreement([(r["lama"], r["sesi"]) for r in rs])

    out: dict[str, Any] = {
        "gabungan_30": group(rows), "putaran_2_20": group([r for r in rows if r["putaran"] == 2]),
        "putaran_1_10": group([r for r in rows if r["putaran"] == 1]),
        "butir_berubah": [{k: r[k] for k in ("kode", "lama", "sesi", "arah")} for r in rows if r["arah"] != "sama"],
        "ragu_sesi_uji_ulang": sorted(r["kode"] for r in rows if r["ragu_sesi"]),
    }
    k30, k2 = out["gabungan_30"]["biner"]["kappa"], out["putaran_2_20"]["biner"]["kappa"]
    out["ambang_7_4"] = {"dasar_terkunci": "estimasi titik kappa biner 30 butir (7.4)", "kappa": k30, "kategori": kappa_band(k30),
                         "pembanding_kappa_biner_putaran_2": k2, "kategori_bila_dari_putaran_2": kappa_band(k2)}

    trail = {(f"P{x['putaran']}-{x['butir']}"): x for x in audit["rinci"]}
    aud = []
    for d in (x for x in session if x["jenis_butir"] == "audit"):
        t = trail[d["kode"]]
        aud.append({"kode": d["kode"], "lama": label_of(cases[d["kode"]]), "sesi": d["keputusan"], "ragu_sesi": d["ragu"],
                    "berubah": d["keputusan"] != label_of(cases[d["kode"]]), "kandidat_berjejak": t["kandidat_berjejak"],
                    "sinyal": t["sinyal"],
                    "sesi_sama_dengan_kandidat_berjejak": d["keputusan"] in t["kandidat_berjejak"] if d["keputusan"] != NONE else None})
    out["audit_7"] = {"rinci": sorted(aud, key=lambda x: x["kode"]),
                      "TIDAK_ADA_ke_cocok": sum(a["berubah"] and a["sesi"] != NONE for a in aud),
                      "cocok_dan_sama_dengan_jejak": sum(bool(a["sesi_sama_dengan_kandidat_berjejak"]) for a in aud)}
    return out


# ---------------------------------------------------------------------------------------------
# Label final (7.5)
# ---------------------------------------------------------------------------------------------

def stratum(days: int | None) -> str | None:
    from evaluation.external_eval import FAR_DAYS
    return None if days is None else ("<=30" if abs(days) <= FAR_DAYS else ">30")


def final_labels(cases: dict[str, dict[str, Any]], session: list[dict[str, Any]],
                 gaps: dict[str, int] | None = None) -> dict[str, Any]:
    """
    Label final = label awal, kecuali butir AUDIT yang keputusannya berubah di sesi buta (dipakai label sesi, termasuk
    tanda ragu sesi). Label awal disimpan berdampingan untuk sensitivitas. Uji ulang tidak mengubah apa pun.
    `gaps`: selisih terbit (hari) untuk butir audit yang menjadi cocok, dihitung dari tanggal Liputan6 dan artikel.
    """
    changed = {d["kode"]: d for d in session if d["jenis_butir"] == "audit" and d["keputusan"] != label_of(cases[d["kode"]])}
    gaps = gaps or {}
    items = []
    for kode, c in sorted(cases.items(), key=lambda kv: (kv[1]["putaran"], kv[1]["butir"])):
        final = {"expected_verdict": c["expected_verdict"], "expected_article": c["expected_article"], "ragu": c["ragu"]}
        days = {"label_awal": c["selisih_hari"], "label_final": c["selisih_hari"]}
        if kode in changed:
            d = changed[kode]
            final = {"expected_verdict": "belum_ditemukan" if d["keputusan"] == NONE else "ditemukan",
                     "expected_article": None if d["keputusan"] == NONE else d["keputusan"], "ragu": d["ragu"]}
            days["label_final"] = gaps.get(kode) if d["keputusan"] != NONE else None
            if d["keputusan"] != NONE and days["label_final"] is None:
                raise SystemExit(f"{kode}: selisih terbit untuk label final tidak tersedia")
        items.append({"kode": kode, "putaran": c["putaran"], "butir": c["butir"], "l6_id": c["l6_id"], "dikeluarkan": c["dikeluarkan"],
                      "label_awal": {k: c[k] for k in ("expected_verdict", "expected_article", "ragu")},
                      "label_final": final, "sumber_label_final": "sesi_buta_audit" if kode in changed else "label_awal",
                      "selisih_hari": days, "strata_selisih": {k: stratum(v) for k, v in days.items()}})
    return {"aturan": "7.5: label awal, kecuali butir audit yang berubah di sesi buta", "berubah": sorted(changed),
            "sha256_eksternal_butir": hashlib.sha256(FROZEN_PATH.read_bytes()).hexdigest(),
            "sha256_hasil_sesi_buta": hashlib.sha256(SESSION_RESULT_PATH.read_bytes()).hexdigest(), "butir": items}


# ---------------------------------------------------------------------------------------------
# Metrik (bagian 6) -- hanya dijalankan setelah label final terkunci
# ---------------------------------------------------------------------------------------------

ANY_IN_LIST = "kandidat_mana_pun_di_daftar"  # sasaran butir yang dibalik ke "cocok" tanpa id (3: butir ragu; 11.5)
V1_EXCLUDED = ("v1-021", "v1-022", "v1-029", "v1-043", "v1-049", "v1-050")  # 6.3: label tidak berlaku pada 1.532
NET_REGRESSION_LIMIT = 3  # 6.3
POS_BAR, FM_RATE, FM_UPPER = 0.60, 0.10, 0.20  # 6.1, 6.2
UNANSWERED = "tak_terjawab"


def wilson(k: int, n: int) -> dict[str, Any]:
    from evaluation.metrics import wilson_interval
    lo, hi = wilson_interval(k, n)
    return {"k": k, "n": n, "proporsi": round(k / n, 4) if n else None, "wilson95": [round(lo, 4), round(hi, 4)]}


def positive_category(k: int, n: int) -> str:
    """6.1: memadai bila batas bawah Wilson >= 60%; buruk bila batas atas < 60%; selain itu tidak konklusif."""
    w = wilson(k, n)["wilson95"]
    return "memadai" if w[0] >= POS_BAR else "buruk" if w[1] < POS_BAR else "tidak_konklusif"


def false_match_category(k: int, n: int) -> str:
    """6.2: lulus (= tidak terbukti buruk) bila <= 10% DAN batas atas <= 20%; gugur bila batas bawah > 10%."""
    w = wilson(k, n)
    if w["proporsi"] is not None and w["proporsi"] <= FM_RATE and w["wilson95"][1] <= FM_UPPER:
        return "lulus"
    return "gugur" if w["wilson95"][0] > FM_RATE else "tidak_konklusif"


WORST = {"positif": ["buruk", "tidak_konklusif", "memadai"], "kecocokan_palsu": ["gugur", "tidak_konklusif", "lulus"]}


def worst(kind: str, cats: list[str]) -> str:
    return min(cats, key=WORST[kind].index)


def item_mode(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Modus 3 run (testset_analysis.compute_mode) + bentuk kesepakatan; 'gagal' dan tanpa modus = tak terjawab."""
    from evaluation.testset_analysis import agreement_kind, compute_mode
    verdict, article, has_mode = compute_mode(records)
    return {"verdict": verdict if has_mode and verdict != "gagal" else UNANSWERED, "article_id": article if has_mode else None,
            "kesepakatan": agreement_kind(records), "run": [(r["verdict"], r["article_id"]) for r in records]}


def outcome(label: dict[str, Any], mode: dict[str, Any], cands: list[str]) -> str:
    """benar | penolakan_palsu | artikel_salah | kecocokan_palsu | tak_terjawab, untuk satu butir dan satu label."""
    v, art = mode["verdict"], mode["article_id"]
    if v == UNANSWERED:
        return UNANSWERED
    if not label["positif"]:
        return "kecocokan_palsu" if v == "ditemukan" else "benar"
    if v != "ditemukan":
        return "penolakan_palsu"
    ok = art in cands if label["sasaran"] == ANY_IN_LIST else art in label["sasaran"]
    return "benar" if ok else "artikel_salah"


def label_view(final: dict[str, Any], which: str = "label_final") -> dict[str, dict[str, Any]]:
    """Label per kode untuk butir analisis (bukan dikeluarkan K1/K2): positif, sasaran (himpunan id), strata selisih."""
    out = {}
    for it in final["butir"]:
        if it["dikeluarkan"]:
            continue
        lab = it[which]
        pos = lab["expected_verdict"] == "ditemukan"
        out[it["kode"]] = {"positif": pos, "sasaran": {lab["expected_article"]} if pos else set(), "ragu": lab["ragu"],
                           "putaran": it["putaran"], "strata_selisih": it["strata_selisih"].get(which) if pos else None}
    return out


def summarize(labels: dict[str, dict[str, Any]], modes: dict[str, dict], cands: dict[str, list[str]]) -> dict[str, Any]:
    """Metrik utama untuk satu set label: ketepatan positif dan kecocokan palsu negatif, dengan kategori ambang."""
    res = {k: outcome(lab, modes[k], cands[k]) for k, lab in labels.items()}
    pos = [k for k, lab in labels.items() if lab["positif"] and res[k] != UNANSWERED]
    neg = [k for k, lab in labels.items() if not lab["positif"] and res[k] != UNANSWERED]
    k_pos, k_fm = sum(res[k] == "benar" for k in pos), sum(res[k] == "kecocokan_palsu" for k in neg)
    return {"positif": {**wilson(k_pos, len(pos)), "kategori": positive_category(k_pos, len(pos)),
                        "per_hasil": dict(Counter(res[k] for k in pos))},
            "kecocokan_palsu": {**wilson(k_fm, len(neg)), "kategori": false_match_category(k_fm, len(neg))},
            "penolakan_benar": wilson(len(neg) - k_fm, len(neg)),
            "tak_terjawab": sorted(k for k, r in res.items() if r == UNANSWERED), "_hasil": res}


def flip(labels: dict[str, dict[str, Any]], codes: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Salinan label dengan butir tertentu dibalik: nilai None = TIDAK ADA, himpunan id / ANY_IN_LIST = cocok."""
    out = {k: dict(v) for k, v in labels.items()}
    for k, target in codes.items():
        if k in out:
            out[k] |= {"positif": target is not None, "sasaran": target if target is not None else set(), "strata_selisih": None}
    return out


def sensitivities(final: dict[str, Any], main: dict[str, dict[str, Any]], retest_changes: list[dict[str, Any]],
                  kappa_band_name: str) -> dict[str, dict[str, dict[str, Any]]]:
    """Set label sensitivitas (6.2, 3, 7.4, 7.5). Butir yang sudah sama dengan arah balik tidak berubah."""
    from candidates.gap_result import DOUBTFUL_ACCEPTED, DOUBTFUL_REJECTED
    ragu = [k for k, v in main.items() if v["ragu"]]
    variants = {
        "label_awal_butir_audit": label_view(final, "label_awal"),
        "ragu_dihitung_cocok": flip(main, {k: (main[k]["sasaran"] or ANY_IN_LIST) for k in ragu}),
        "ragu_dihitung_TIDAK_ADA": flip(main, dict.fromkeys(ragu)),
        "p1_15_diterima_jadi_TIDAK_ADA": flip(main, {f"P1-{n}": None for n in DOUBTFUL_ACCEPTED}),
        "p1_15_ditolak_jadi_cocok": flip(main, {f"P1-{n}": (main[f"P1-{n}"]["sasaran"] or ANY_IN_LIST)
                                                for n in DOUBTFUL_REJECTED if f"P1-{n}" in main}),
    }
    if kappa_band_name == "dua_arah":  # 7.4: butir yang berubah pada uji ulang dibalik ke dua arah
        ids = {c["kode"]: {x for x in (c["lama"], c["sesi"]) if x != NONE} for c in retest_changes}
        variants["uji_ulang_berubah_dihitung_cocok"] = flip(main, ids)
        variants["uji_ulang_berubah_dihitung_TIDAK_ADA"] = flip(main, dict.fromkeys(ids))
    return variants


def discovery_stratum(l6_id: str, target: str, keys: dict[str, dict[str, Any]]) -> str:
    """Bagian 4 butir 2: (a) teratas embedding judul, (b) 5 teratas embedding bukan teratas, (c) hanya kata kunci."""
    s = keys[l6_id]
    emb = [x[0] for x in s["embedding_top"]]
    if emb and emb[0] == target:
        return "a_teratas_embedding"
    if target in emb:
        return "b_5_teratas_embedding"
    return "c_hanya_kata_kunci" if target in [x[0] for x in s["kata_kunci_top"]] else "di_luar_daftar_pencarian"


def positive_detail(labels: dict[str, dict[str, Any]], modes: dict[str, dict], cands: dict[str, list[str]], top3: dict[str, list[str]],
                    strata: dict[str, str]) -> dict[str, Any]:
    """6.1: Recall@3 bersyarat (per strata penemuan), ketepatan per selisih terbit dan putaran, dan pemisahan kegagalan."""
    pos = {k: v for k, v in labels.items() if v["positif"]}
    res = {k: outcome(v, modes[k], cands[k]) for k, v in pos.items()}
    rec = {k: bool(v["sasaran"] & set(top3[k])) if isinstance(v["sasaran"], set) else False for k, v in pos.items()}

    def acc(keys: list[str]) -> dict[str, Any]:
        ks = [k for k in keys if res[k] != UNANSWERED]
        return wilson(sum(res[k] == "benar" for k in ks), len(ks))

    by = lambda f: {g: sorted(k for k in pos if f(k) == g) for g in sorted({f(k) for k in pos}, key=str)}
    fails = []
    for k in sorted(pos):
        if res[k] in ("benar", UNANSWERED):
            continue
        kind = res[k]
        if kind == "penolakan_palsu":
            kind = "penolakan_lintas_gelombang" if pos[k]["strata_selisih"] == ">30" else "penolakan_lain"
        fails.append({"kode": k, "jenis": kind, "sasaran_di_top3": rec[k], "jawaban_modus": modes[k]["article_id"],
                      "jawaban_di_daftar_kandidat": modes[k]["article_id"] in cands[k] if modes[k]["article_id"] else None,
                      "strata_selisih": pos[k]["strata_selisih"], "strata_penemuan": strata.get(k)})
    return {"recall_at_3_bersyarat": {**wilson(sum(rec.values()), len(rec)),
                                      "per_strata_penemuan": {g: wilson(sum(rec[k] for k in ks), len(ks)) for g, ks in by(strata.get).items()}},
            "ketepatan": acc(list(pos)),
            "ketepatan_per_selisih": {g: acc(ks) for g, ks in by(lambda k: pos[k]["strata_selisih"]).items()},
            "ketepatan_per_putaran": {f"P{g}": acc(ks) for g, ks in by(lambda k: pos[k]["putaran"]).items()},
            "ketepatan_per_strata_penemuan": {g: acc(ks) for g, ks in by(strata.get).items()},
            "kegagalan_per_jenis": dict(Counter(f["jenis"] for f in fails)), "kegagalan": fails}


def negative_detail(labels: dict[str, dict[str, Any]], modes: dict[str, dict], cands: dict[str, list[str]],
                    top3: dict[str, list[str]]) -> dict[str, Any]:
    """6.2: kecocokan palsu dipecah di dalam / di luar daftar kandidat; yang di luar didaftar untuk adjudikasi."""
    neg = sorted(k for k, v in labels.items() if not v["positif"] and modes[k]["verdict"] != UNANSWERED)
    fm = [k for k in neg if modes[k]["verdict"] == "ditemukan"]
    rows = [{"kode": k, "jawaban_modus": modes[k]["article_id"], "di_daftar_kandidat": modes[k]["article_id"] in cands[k],
             "peringkat_di_top3": (top3[k].index(modes[k]["article_id"]) + 1) if modes[k]["article_id"] in top3[k] else None,
             "kesepakatan": modes[k]["kesepakatan"]} for k in fm]
    by_round = {f"P{r}": wilson(sum(labels[k]["putaran"] == r for k in fm), sum(labels[k]["putaran"] == r for k in neg)) for r in (1, 2)}
    return {"kecocokan_palsu_di_daftar": sum(r["di_daftar_kandidat"] for r in rows),
            "kecocokan_palsu_di_luar_daftar": [r["kode"] for r in rows if not r["di_daftar_kandidat"]],
            "per_putaran": by_round, "rinci": rows}


def regression_v1(archive_path: Path, new_path: Path) -> dict[str, Any]:
    """6.3: 44 butir non-batas + 4 batas (6 dikeluarkan); kemunduran bersih = (benar->salah) - (salah->benar)."""
    from evaluation.metrics import classify_error
    from evaluation.testset_analysis import V1_PATH, load_eval_records, load_v1_items
    items, old, new = load_v1_items(V1_PATH), load_eval_records(archive_path), load_eval_records(new_path)
    rows = []
    for i, it in items.items():
        if i in V1_EXCLUDED:
            continue
        mo, mn = item_mode(old[i]), item_mode(new[i])

        def ok(m: dict[str, Any], it: dict[str, Any] = it) -> bool | None:
            if m["verdict"] == UNANSWERED:
                return None
            return classify_error(it["expected_verdict"], it["expected_retrieval_article"], m["verdict"], m["article_id"]) is None

        tgt = it["expected_retrieval_article"]
        rows.append({"id": i, "batas": it["batas"], "tipe": it["tipe"], "benar_arsip": ok(mo), "benar_1532": ok(mn),
                     "sasaran_retrieval_di_top3_arsip": tgt in [c["article_id"] for c in old[i][0]["retrieval_top3"]] if tgt else None,
                     "sasaran_retrieval_di_top3_1532": tgt in [c["article_id"] for c in new[i][0]["retrieval_top3"]] if tgt else None,
                     "modus_arsip": [mo["verdict"], mo["article_id"]], "modus_1532": [mn["verdict"], mn["article_id"]],
                     "kesepakatan_1532": mn["kesepakatan"]})
    nb = [r for r in rows if not r["batas"]]
    down = [r for r in nb if r["benar_arsip"] and r["benar_1532"] is False]
    up = [r for r in nb if r["benar_arsip"] is False and r["benar_1532"]]
    net = len(down) - len(up)
    return {"butir": len(rows), "non_batas": len(nb), "benar_arsip_non_batas": sum(bool(r["benar_arsip"]) for r in nb),
            "benar_1532_non_batas": sum(bool(r["benar_1532"]) for r in nb), "benar_ke_salah": [r["id"] for r in down],
            "salah_ke_benar": [r["id"] for r in up], "kemunduran_bersih": net,
            "kategori": "mundur" if net >= NET_REGRESSION_LIMIT else "tidak_mundur",
            "batas_berpindah": [r for r in rows if r["batas"] and r["benar_arsip"] != r["benar_1532"]],
            "perpindahan_non_batas": [r for r in nb if r["benar_arsip"] != r["benar_1532"]]}


def compliance(eval_paths: dict[str, Path]) -> dict[str, Any]:
    """Aturan Wajib #3 dan format: URL keluaran mentah di luar metadata kandidat, parse_failures, id di luar kandidat."""
    from chunker import load_articles
    from evaluation.testset_analysis import (
        format_violations,
        load_eval_records,
        urls_outside_metadata,
    )
    arts = {a["article_id"]: a for a in load_articles()}
    out = {}
    for name, p in eval_paths.items():
        recs = load_eval_records(p)
        urls, fmt = urls_outside_metadata(recs, arts), format_violations(recs)
        out[name] = {"rekam": sum(len(v) for v in recs.values()),
                     "panggilan": sum(len(pc["calls"]) for v in recs.values() for r in v for pc in r["percobaan"]),
                     "url_di_luar_metadata": urls["total"], "butir_dengan_url_di_luar_metadata": len(urls["per_butir"]),
                     "pelanggaran_format_parse_failures": fmt["total"],
                     "id_di_luar_kandidat": sum(bool(pc.get("invalid_id")) for v in recs.values() for r in v for pc in r["percobaan"]),
                     "jawaban_gagal": sum(r["verdict"] == "gagal" for v in recs.values() for r in v)}
    return out


def cmd_reliability() -> int:
    out = reliability(load_frozen(), load_session(), json.loads(AUDIT_PATH.read_text(encoding="utf-8")))
    RELIABILITY_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_final_labels() -> int:
    if FINAL_LABELS_PATH.exists():
        raise SystemExit(f"{FINAL_LABELS_PATH.name} sudah ada: label final tidak ditimpa")
    from candidates.blind_workbook import article_lookup
    from candidates.gap_blocks import day_gap
    from candidates.gap_review import load_valid_sample
    cases, session = load_frozen(), load_session()
    _, _, valid = load_valid_sample()
    by_id = article_lookup()
    gaps = {d["kode"]: day_gap(valid[cases[d["kode"]]["l6_id"]]["tanggal"], by_id[d["keputusan"]]["date"])
            for d in session if d["jenis_butir"] == "audit" and d["keputusan"] != NONE}
    out = final_labels(cases, session, gaps)
    FINAL_LABELS_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "butir"}, ensure_ascii=False, indent=1))
    print(json.dumps([{k: it[k] for k in ("kode", "label_awal", "label_final", "selisih_hari")} for it in out["butir"]
                      if it["kode"] in out["berubah"]], ensure_ascii=False, indent=1))
    print(f"sha256 {FINAL_LABELS_PATH.name}: {hashlib.sha256(FINAL_LABELS_PATH.read_bytes()).hexdigest()}")
    return 0


# dicatat di docs/rancangan_evaluasi_eksternal.md 7.5 (commit yang sama) SEBELUM segel dibuka; --metrik menolak bila beda
FINAL_LABELS_SHA256 = "c24008d1cea343c037889b76001e3eeffb6617a5cbc12d5dd9f98a15f7dd28da"
LIPUTAN6_EVAL = DATA_DIR / "external_eval_liputan6_gemini-3.5-flash-lite.jsonl"
V1_ARCHIVE_EVAL = DATA_DIR / "testset_v1_eval_gemini-3.5-flash-lite.jsonl"
V1_1532_EVAL = DATA_DIR / "external_eval_v1_idx1532_gemini-3.5-flash-lite.jsonl"
METRICS_PATH = SESSION_DIR / "hasil_evaluasi_eksternal.json"  # lokal (memuat id artikel Liputan6 + alasan tidak; tanpa teks)
PUBLIC_TABLE_PATH = PROJECT_ROOT / "testset" / "eksternal_hasil_per_butir.json"  # yang boleh dipublikasikan (bagian 8)
BASELINE_PATH = SESSION_DIR / "retrieval_pembanding.json"
KEY_PATHS = {1: DATA_DIR / "candidates" / "celah_liputan6" / "kunci_kandidat.json",
             2: DATA_DIR / "candidates" / "celah_liputan6" / "kunci_kandidat_49.json"}


def locked_final_labels() -> dict[str, Any]:
    sha = hashlib.sha256(FINAL_LABELS_PATH.read_bytes()).hexdigest() if FINAL_LABELS_PATH.exists() else None
    if not FINAL_LABELS_SHA256 or sha != FINAL_LABELS_SHA256:
        raise SystemExit(f"label final belum terkunci atau berubah (sekarang {sha}, tercatat {FINAL_LABELS_SHA256!r}): segel tidak dibuka")
    return json.loads(FINAL_LABELS_PATH.read_text(encoding="utf-8"))


def candidate_lists() -> dict[str, list[str]]:
    """Daftar kandidat yang dulu ditampilkan ke pemilik proyek per butir (dibangun ulang dan diverifikasi seperti sesi buta)."""
    from candidates.blind_workbook import article_lookup, round1_items, round2_items
    from candidates.gap_review import load_valid_sample
    _, _, valid = load_valid_sample()
    by_id = article_lookup()
    src = {1: round1_items(valid, by_id), 2: round2_items(valid, by_id)}
    return {f"P{r}-{n}": [c["id"] for c in it["kandidat"]] for r, items in src.items() for n, it in items.items()}


def search_keys() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for p in KEY_PATHS.values():
        out |= json.loads(p.read_text(encoding="utf-8"))["skor"]
    return out


def cmd_metrics() -> int:
    from evaluation.testset_analysis import load_eval_records
    final = locked_final_labels()
    rel = json.loads(RELIABILITY_PATH.read_text(encoding="utf-8"))
    recs = load_eval_records(LIPUTAN6_EVAL)
    main_labels = label_view(final)
    if set(recs) != set(main_labels) or any(sorted(r["run"] for r in v) != [1, 2, 3] for v in recs.values()):
        raise SystemExit("berkas hasil tidak memuat tepat 3 run untuk ke-91 butir analisis")
    modes = {k: item_mode(v) for k, v in recs.items()}
    top3_runs = {k: {tuple(c["article_id"] for c in r["retrieval_top3"]) for r in v} for k, v in recs.items()}
    top3 = {k: list(next(iter(s))) for k, s in top3_runs.items()}
    cands, keys = candidate_lists(), search_keys()
    l6 = {it["kode"]: it["l6_id"] for it in final["butir"]}
    strata = {k: discovery_stratum(l6[k], next(iter(v["sasaran"])), keys) for k, v in main_labels.items() if v["positif"]}

    main = summarize(main_labels, modes, cands)
    variants = sensitivities(final, main_labels, rel["butir_berubah"], rel["ambang_7_4"]["kategori"])
    sens = {name: summarize(lab, modes, cands) for name, lab in variants.items()}
    per_round = {f"P{r}": summarize({k: v for k, v in main_labels.items() if v["putaran"] == r}, modes, cands) for r in (1, 2)}

    def cats(s: dict[str, Any]) -> dict[str, str]:
        return {"positif": s["positif"]["kategori"], "kecocokan_palsu": s["kecocokan_palsu"]["kategori"]}

    all_cats = {"utama": cats(main), **{n: cats(s) for n, s in sens.items()}}
    stable = {m: len({c[m] for c in all_cats.values()}) == 1 for m in ("positif", "kecocokan_palsu")}
    reported = {m: worst(m, [c[m] for c in all_cats.values()]) for m in ("positif", "kecocokan_palsu")}
    out = {
        "label_final_sha256": FINAL_LABELS_SHA256, "kappa_7_4": rel["ambang_7_4"],
        "keputusan_modus": {"kesepakatan": dict(Counter(m["kesepakatan"] for m in modes.values())),
                            "tidak_bulat": sorted(k for k, m in modes.items() if m["kesepakatan"] != "bulat"),
                            "tanpa_modus": sorted(k for k, m in modes.items() if m["kesepakatan"] == "tanpa_modus"),
                            "retrieval_top3_beda_antar_run": sorted(k for k, s in top3_runs.items() if len(s) > 1)},
        "butir": {"positif": sum(v["positif"] for v in main_labels.values()), "negatif": sum(not v["positif"] for v in main_labels.values())},
        "utama": {k: v for k, v in main.items() if k != "_hasil"},
        "positif_rinci": positive_detail(main_labels, modes, cands, top3, strata),
        "negatif_rinci": negative_detail(main_labels, modes, cands, top3),
        "sensitivitas": {n: {k: v for k, v in s.items() if k != "_hasil"} for n, s in sens.items()},
        "per_putaran_DESKRIPTIF_tanpa_uji": {n: {k: v for k, v in s.items() if k != "_hasil"} for n, s in per_round.items()},
        "kategori": {"semua": all_cats, "sama_di_semua_sensitivitas": stable, "terburuk_dilaporkan_6_2_7_4": reported,
                     "per_putaran": {n: cats(s) for n, s in per_round.items()}},
        "kemunduran_v1": regression_v1(V1_ARCHIVE_EVAL, V1_1532_EVAL),
        "kepatuhan": compliance({"liputan6": LIPUTAN6_EVAL, "testset_v1_1532": V1_1532_EVAL}),
    }
    METRICS_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    table = [{"kode": k, "l6_id": l6[k], "label_final": (next(iter(v["sasaran"])) if v["positif"] else NONE),
              "keputusan_modus": modes[k]["verdict"], "article_id_modus": modes[k]["article_id"],
              "kesepakatan_3_run": modes[k]["kesepakatan"], "hasil": main["_hasil"][k]}
             for k, v in sorted(main_labels.items(), key=lambda kv: (kv[1]["putaran"], int(kv[0].split("-")[1])))]
    PUBLIC_TABLE_PATH.write_text(json.dumps({"label_final_sha256": FINAL_LABELS_SHA256, "butir": table},
                                            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_retrieval_baselines() -> int:
    """Bagian 4 butir 3: Recall@3 kueri judul (tanpa kata vonis; kueri kunci kandidat) vs kueri kutipan, tanpa LLM."""
    from evaluation.external_eval import build_liputan6_cases
    from evaluation.testset_analysis import load_eval_records
    from ingest import get_collection, load_model
    from retriever import retrieve
    final, keys = locked_final_labels(), search_keys()
    labels = label_view(final)
    quotes = {c["kode"]: c["kutipan"] for c in build_liputan6_cases()}
    stored = {k: [c["article_id"] for c in v[0]["retrieval_top3"]] for k, v in load_eval_records(LIPUTAN6_EVAL).items()}
    l6 = {it["kode"]: it["l6_id"] for it in final["butir"]}
    model, coll = load_model(), get_collection()
    rows = []
    for k, v in sorted(labels.items()):
        if not v["positif"]:
            continue
        t = next(iter(v["sasaran"]))
        title = [h.article_id for h in retrieve(keys[l6[k]]["kueri"], model, coll, top_k=3)]
        quote = [h.article_id for h in retrieve(quotes[k], model, coll, top_k=3)]
        rows.append({"kode": k, "strata_penemuan": discovery_stratum(l6[k], t, keys), "judul": t in title, "kutipan": t in quote,
                     "kutipan_sama_dengan_top3_tersimpan": quote == stored[k]})
    by_s = {s: [r for r in rows if r["strata_penemuan"] == s] for s in sorted({r["strata_penemuan"] for r in rows})}
    out = {"n": len(rows), "kueri_judul": wilson(sum(r["judul"] for r in rows), len(rows)),
           "kueri_kutipan": wilson(sum(r["kutipan"] for r in rows), len(rows)),
           "per_strata": {s: {"n": len(rs), "judul": sum(r["judul"] for r in rs), "kutipan": sum(r["kutipan"] for r in rs)} for s, rs in by_s.items()},
           "judul_ya_kutipan_tidak": [r["kode"] for r in rows if r["judul"] and not r["kutipan"]],
           "judul_tidak_kutipan_ya": [r["kode"] for r in rows if not r["judul"] and r["kutipan"]],
           "kutipan_beda_dengan_top3_tersimpan": [r["kode"] for r in rows if not r["kutipan_sama_dengan_top3_tersimpan"]]}
    BASELINE_PATH.write_text(json.dumps({**out, "rinci": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--keandalan", action="store_true")
    g.add_argument("--label-final", action="store_true")
    g.add_argument("--metrik", action="store_true")
    g.add_argument("--retrieval-pembanding", action="store_true")
    args = ap.parse_args()
    if args.keandalan:
        return cmd_reliability()
    if args.label_final:
        return cmd_final_labels()
    return cmd_metrics() if args.metrik else cmd_retrieval_baselines()


if __name__ == "__main__":
    raise SystemExit(main())
