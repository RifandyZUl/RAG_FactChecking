"""
Hasil konfirmasi celah "belum ditemukan" (docs/rancangan_v2.md bagian 11) dari berkas yang SUDAH diisi
pemilik proyek (konfirmasi_50_terisi.csv; format sama dengan konfirmasi_50.csv).

Kode ini hanya MEMVALIDASI dan MENGHITUNG. Keputusan tidak pernah diisi, diusulkan, atau diubah kode
(Aturan Wajib #5); kolom catatan tidak di-parse. Dua tahap yang sengaja dipisah:

  --hasil   validasi + hasil utama (bagian 11.2 apa adanya) + sensitivitas (EKSPLORATIF) + rincian.
            TIDAK membuka kunci_kandidat.json: butir dipetakan ke artikel Liputan6 lewat judul di sampel.
  --kunci   baru setelah hasil tersimpan: keputusan vs kandidat teratas tiap cara pencarian. Hanya untuk
            menilai pencarian otomatis; tidak boleh dipakai untuk mengubah label.

Pemakaian (dari root proyek):
  python -m labeling.gap.gap_result --hasil
  python -m labeling.gap.gap_result --kunci
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from labeling.gap.gap_review import (
    COLUMNS,
    OUT_DIR,
    SAMPLE_PATH,
    banner_label,
    conclusion_text,
    tbh_date_key,
)
from labeling.gap.gap_workbook import (
    CSV_PATH,
    HUMAN_COLUMNS,
    KEY_PATH,
    content_hash,
    proportion,
    read_csv_rows,
    read_decisions,
)

FILLED_PATH = OUT_DIR / "konfirmasi_50_terisi.csv"
RESULT_PATH = OUT_DIR / "hasil_konfirmasi.json"
KEY_RESULT_PATH = OUT_DIR / "perbandingan_kunci.json"
EXPECTED_ITEMS = 50
# Butir yang menurut pemilik proyek SENDIRI diputuskan dengan aturan yang tidak konsisten (dinyatakan setelah
# pelabelan selesai, 2026-10-08). Dipakai hanya untuk batas sensitivitas; label utama tidak diubah.
DOUBTFUL_ACCEPTED = (8, 14, 24, 28, 39, 40, 48, 49)  # diterima; batas ATAS: dibalik menjadi TIDAK ADA
DOUBTFUL_REJECTED = (15, 20, 21, 22, 25, 29, 32)  # ditolak; batas BAWAH: dibalik menjadi cocok


def validate(filled: list[dict[str, str]], template: list[dict[str, str]], expected_items: int = EXPECTED_ITEMS) -> list[str]:
    """Daftar masalah (kosong = lolos): jumlah butir, kolom selain KEPUTUSAN/catatan identik, keputusan terbaca."""
    problems = []
    n_items = len({r["butir"] for r in filled})
    if n_items != expected_items:
        problems.append(f"jumlah butir {n_items}, seharusnya {expected_items}")
    if len(filled) != len(template):
        problems.append(f"jumlah baris {len(filled)}, berkas asli {len(template)}")
    elif content_hash(filled) != content_hash(template):
        diff = [(i + 2, c) for i, (a, b) in enumerate(zip(filled, template)) for c in COLUMNS
                if c not in HUMAN_COLUMNS and a[c] != b[c]]
        problems.append(f"kolom selain KEPUTUSAN/catatan berbeda dari berkas asli pada {len(diff)} sel (baris, kolom): {diff[:10]}")
    filled_in_template = sum(bool(r[c].strip()) for r in template for c in HUMAN_COLUMNS)
    if filled_in_template:
        problems.append(f"berkas asli memuat {filled_in_template} sel KEPUTUSAN/catatan terisi (seharusnya kosong)")
    problems += [f"butir {p['butir']}: {p['masalah']} ({p['isi']!r})" for p in read_decisions(filled)["perlu_ditanyakan"]]
    return problems


def sensitivity(decisions: list[dict[str, Any]], accepted: tuple[int, ...] = DOUBTFUL_ACCEPTED,
                rejected: tuple[int, ...] = DOUBTFUL_REJECTED) -> dict[str, Any]:
    """
    Batas atas/bawah proporsi TIDAK ADA bila butir meragukan dibalik. Butir yang label utamanya tidak sesuai
    dengan daftar (mis. "diterima" padahal TIDAK ADA) dilaporkan dan TIDAK dibalik.
    """
    kind = {int(d["butir"]): d["jenis"] for d in decisions}
    valid = [k for k in kind.values() if k in ("tidak_ada", "sama")]
    k, n = valid.count("tidak_ada"), len(valid)
    up = [b for b in accepted if kind.get(b) == "sama"]
    down = [b for b in rejected if kind.get(b) == "tidak_ada"]
    main, upper, lower = proportion(k, n), proportion(k + len(up), n), proportion(k - len(down), n)
    return {"utama": main, "batas_atas": {**upper, "butir_dibalik": up}, "batas_bawah": {**lower, "butir_dibalik": down},
            "tidak_sesuai_daftar": sorted(set(accepted) - set(up)) + sorted(set(rejected) - set(down)),
            "kategori_sama_di_kedua_batas": main["status"] == upper["status"] == lower["status"]}


def first_rows(rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    return {int(r["butir"]): r for r in rows if r["L6_judul"]}


def l6_ids_by_title(titles: dict[int, str], sample_path: Path = SAMPLE_PATH) -> dict[int, str]:
    """butir -> id artikel Liputan6 lewat judul di sampel (tanpa kunci_kandidat.json); judul harus cocok tepat satu."""
    by_title: dict[str, list[str]] = {}
    for ln in sample_path.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            by_title.setdefault(r["judul"], []).append(r["id"])
    out = {}
    for n, title in titles.items():
        if len(by_title.get(title, [])) != 1:
            raise ValueError(f"butir {n}: judul cocok dengan {len(by_title.get(title, []))} artikel sampel")
        out[n] = by_title[title][0]
    return out


def timing(l6_iso: str, tbh_ddmmyyyy: str) -> str:
    """Artikel TurnBackHoax terbit "sebelum" | "hari_sama" | "sesudah" artikel Liputan6."""
    t, l6 = date(*tbh_date_key(tbh_ddmmyyyy)), date.fromisoformat(l6_iso)
    return "sebelum" if t < l6 else "sesudah" if t > l6 else "hari_sama"


def results() -> int:
    filled, template = read_csv_rows(FILLED_PATH), read_csv_rows(CSV_PATH)
    problems = validate(filled, template)
    if problems:
        print(json.dumps({"validasi": "GAGAL", "masalah": problems}, ensure_ascii=False, indent=2))
        raise SystemExit("validasi gagal: hasil TIDAK dihitung")
    decisions = read_decisions(filled)["butir"]
    kinds = Counter(d["jenis"] for d in decisions)
    firsts = first_rows(filled)
    l6_id = l6_ids_by_title({n: r["L6_judul"] for n, r in firsts.items()})
    banner = {n: banner_label(conclusion_text(aid)) or "(tanpa banner)" for n, aid in l6_id.items()}
    tbh = {(int(r["butir"]), r["TBH_id"]): r for r in filled}
    pairs = [{"butir": int(d["butir"]), "tbh_id": d["keputusan"], "label_l6": banner[int(d["butir"])], "label_tbh": d["label_tbh"],
              "tbh_asal": tbh[int(d["butir"]), d["keputusan"]]["TBH_asal"], "l6_tanggal": firsts[int(d["butir"])]["L6_tanggal"],
              "tbh_tanggal": tbh[int(d["butir"]), d["keputusan"]]["TBH_tanggal"],
              "tbh_terbit": timing(firsts[int(d["butir"])]["L6_tanggal"], tbh[int(d["butir"]), d["keputusan"]]["TBH_tanggal"])}
             for d in decisions if d["jenis"] == "sama"]
    sens = sensitivity(decisions)
    report = {
        "berkas": {"terisi": FILLED_PATH.name, "sha256_terisi": hashlib.sha256(FILLED_PATH.read_bytes()).hexdigest(),
                   "asli": CSV_PATH.name, "sha256_asli": hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()},
        "validasi": {"lolos": True, "butir": len(decisions), "baris": len(filled),
                     "catatan_terisi": sum(bool(r["catatan"].strip()) for r in filled)},
        "jenis_keputusan": dict(kinds),
        "hasil_utama_bagian_11_2": sens["utama"],
        "sensitivitas_EKSPLORATIF_tidak_dipraregistrasi": {k: v for k, v in sens.items() if k != "utama"},
        "bukan_putusan_hoaks": [{"butir": int(d["butir"]), "label_l6": banner[int(d["butir"])]} for d in decisions
                                if d["jenis"] == "bukan_putusan_hoaks"],
        "butir_banner_klarifikasi": [{"butir": n, "jenis": next(d["jenis"] for d in decisions if int(d["butir"]) == n)}
                                     for n, b in banner.items() if b == "klarifikasi"],
        "ujung_rentang_n_kecil_tanpa_kesimpulan": [{"butir": int(d["butir"]), "l6_tanggal": firsts[int(d["butir"])]["L6_tanggal"],
                                                    "jenis": d["jenis"], "keputusan": d["keputusan"]}
                                                   for d in decisions if d["ujung_rentang"]],
        "label_liputan6_semua_butir": dict(Counter(banner.values())),
        "label_liputan6_x_turnbackhoax_pasangan_cocok": dict(Counter(f"{p['label_l6']} x {p['label_tbh']}" for p in pairs)),
        "label_liputan6_pada_tidak_ada": dict(Counter(banner[int(d["butir"])] for d in decisions if d["jenis"] == "tidak_ada")),
        "tbh_terbit_relatif_liputan6": dict(Counter(p["tbh_terbit"] for p in pairs)),
        "pasangan_dari_antrean": sum(p["tbh_asal"].startswith("antrean") for p in pairs),
        "tbh_dipilih_lebih_dari_sekali": {i: c for i, c in Counter(p["tbh_id"] for p in pairs).items() if c > 1},
        "pasangan": pairs,
        "keputusan": [{"butir": int(d["butir"]), "jenis": d["jenis"], "keputusan": d["keputusan"]} for d in decisions],
        "l6_id": l6_id,
    }
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("keputusan", "l6_id")}, ensure_ascii=False, indent=2))
    return 0


def compare_with_key(decisions: list[dict[str, Any]], l6_id: dict[str, str], scores: dict[str, Any]) -> dict[str, Any]:
    """Keputusan manusia vs peringkat kandidat tiap cara pencarian (embedding 5 teratas, kata kunci 3 teratas)."""
    matched, none = [], []
    for d in decisions:
        s = scores[l6_id[str(d["butir"])]]
        emb, lex = [(str(i), float(v)) for i, v in s["embedding_top"]], [(str(x[0]), float(x[1])) for x in s["kata_kunci_top"]]
        if d["jenis"] == "sama":
            rank = {name: next((r for r, (i, _) in enumerate(lst, 1) if i == d["keputusan"]), None) for name, lst in (("embedding", emb), ("kata_kunci", lex))}
            matched.append({"butir": d["butir"], "tbh_id": d["keputusan"], "peringkat_embedding": rank["embedding"],
                            "peringkat_kata_kunci": rank["kata_kunci"],
                            "skor_embedding": next((v for i, v in emb if i == d["keputusan"]), None)})
        elif d["jenis"] == "tidak_ada":
            none.append({"butir": d["butir"], "embedding_teratas": emb[0], "kata_kunci_teratas": lex[0]})
    n = len(matched)
    chosen = sorted(m["skor_embedding"] for m in matched if m["skor_embedding"] is not None)
    median = chosen[len(chosen) // 2] if chosen else None
    none_top = sorted(x["embedding_teratas"][1] for x in none)
    return {
        "pasangan_cocok": n,
        "pilihan_adalah_teratas_embedding": sum(m["peringkat_embedding"] == 1 for m in matched),
        "pilihan_ada_di_5_teratas_embedding": sum(m["peringkat_embedding"] is not None for m in matched),
        "pilihan_adalah_teratas_kata_kunci": sum(m["peringkat_kata_kunci"] == 1 for m in matched),
        "pilihan_ada_di_3_teratas_kata_kunci": sum(m["peringkat_kata_kunci"] is not None for m in matched),
        "pilihan_teratas_di_keduanya": sum(m["peringkat_embedding"] == 1 and m["peringkat_kata_kunci"] == 1 for m in matched),
        "pilihan_bukan_teratas_di_keduanya": [m["butir"] for m in matched if m["peringkat_embedding"] != 1 and m["peringkat_kata_kunci"] != 1],
        "skor_embedding_pilihan_min_median_maks": [chosen[0], median, chosen[-1]] if chosen else None,
        "tidak_ada": len(none),
        "skor_embedding_teratas_pada_tidak_ada_min_median_maks": [none_top[0], none_top[len(none_top) // 2], none_top[-1]] if none_top else None,
        "tidak_ada_dengan_skor_embedding_di_atas_median_pilihan": sorted(
            (x for x in none if median is not None and x["embedding_teratas"][1] >= median), key=lambda x: -x["embedding_teratas"][1]),
        "tidak_ada_dengan_skor_embedding_di_atas_minimum_pilihan": sum(bool(chosen) and x["embedding_teratas"][1] >= chosen[0] for x in none),
        "rinci_cocok": matched,
        "rinci_tidak_ada": sorted(none, key=lambda x: -x["embedding_teratas"][1]),
    }


def key_comparison() -> int:
    if not RESULT_PATH.exists():
        raise SystemExit(f"{RESULT_PATH.name} belum ada: jalankan --hasil dulu (kunci dibuka hanya setelah hasil tersimpan)")
    res = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    key = json.loads(KEY_PATH.read_text(encoding="utf-8"))
    order = {str(n): aid for n, aid in enumerate(key["urutan_butir"], 1)}
    if order != res["l6_id"]:
        raise SystemExit("pemetaan butir -> artikel Liputan6 lewat judul tidak sama dengan urutan di kunci")
    report = {"catatan": "hanya untuk menilai pencarian otomatis; TIDAK dipakai untuk mengubah label",
              **compare_with_key(res["keputusan"], res["l6_id"], key["skor"])}
    KEY_RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--hasil", action="store_true", help="validasi dan hitung hasil (tanpa membuka kunci)")
    g.add_argument("--kunci", action="store_true", help="bandingkan keputusan dengan kandidat teratas (setelah --hasil)")
    args = ap.parse_args()
    return results() if args.hasil else key_comparison()


if __name__ == "__main__":
    raise SystemExit(main())
