"""
Berkas adjudikasi buta evaluasi eksternal (docs/rancangan_evaluasi_eksternal.md bagian 7.6) dan pembacaannya.

Isi: HANYA butir yang keputusan modus sistemnya berbeda dari label final (penolakan palsu, artikel salah, kecocokan
palsu). Tiap butir menampilkan judul, tanggal, dan kutipan Liputan6 seperti berkas sesi buta, lalu dua opsi tanpa
keterangan mana dari sistem: opsi label dan opsi sistem. Opsi "tidak ada yang cocok" tidak berupa baris; artikel
yang tampil adalah artikel dari opsi yang berupa artikel (satu atau dua, urutan acak). KEPUTUSAN = id artikel yang
klaimnya sama, atau TIDAK ADA. Urutan butir dan artikel memakai random.SystemRandom; peta ke butir asli dan opsi mana
yang dari sistem hanya disimpan di kunci.

Hasil adjudikasi dicatat terpisah dan TIDAK mengubah label final maupun metrik utama (7.6). KEPUTUSAN, ragu, dan
catatan diisi pemilik proyek sendiri, tanpa bantuan AI (Aturan Wajib #5).

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m candidates.adjudication_workbook --make   # menolak menimpa
  PYTHONPATH=src python -m candidates.adjudication_workbook --read [--berkas <..._terisi_v2.xlsx>]
"""

import argparse
import hashlib
import json
import random
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from candidates.blind_workbook import GUIDE as SESSION_GUIDE
from candidates.blind_workbook import archive_copy, article_lookup, make_item
from candidates.gap_blocks import (
    INPUT_COLS,
    evidence_hash,
    layout,
    read_grid,
    read_inputs,
    write_workbook,
)
from candidates.gap_review import load_valid_sample
from candidates.gap_workbook import provenance
from paths import DATA_DIR

ADJ_DIR = DATA_DIR / "candidates" / "adjudikasi_eksternal"
XLSX_PATH = ADJ_DIR / "adjudikasi_buta.xlsx"
FILLED_PATH = ADJ_DIR / "adjudikasi_buta_terisi.xlsx"
TEMPLATE_PATH = ADJ_DIR / "sidik_jari_templat_adjudikasi.json"  # tanpa peta ke butir asli dan tanpa opsi sistem
KEY_PATH = ADJ_DIR / "kunci_adjudikasi.json"  # peta nomor -> butir asli + opsi label/sistem; hanya dibuka --read
RESULT_PATH = ADJ_DIR / "hasil_adjudikasi.json"
README_PATH = ADJ_DIR / "BACA_SAYA.txt"
ARCHIVE_DIR = ADJ_DIR / "arsip_baca"
ARCHIVE_LOG = ARCHIVE_DIR / "arsip_baca.jsonl"
GENERATED_BY = "candidates.adjudication_workbook (openpyxl; tata letak dihasilkan kode, KEPUTUSAN/ragu/catatan diisi manusia)"
NONE = "TIDAK ADA"
# dicatat di docs/rancangan_evaluasi_eksternal.md 7.8 (commit yang sama) SEBELUM diisi; --read berhenti bila beda
RECORDED_SHA256: dict[str, str] = {
    "adjudikasi_buta.xlsx": "e721bd943d0abd64b1c14c947f5ddb03a99584272283dd1f6d4acb9e40b8b45b",
    "kunci_adjudikasi.json": "8f8cf5aaeccb1004ab86e6aae8fab809dbe49a1fbd17454072a93db3a2c65fd1",
    "sidik_jari_templat_adjudikasi.json": "1d0a88dc5a57de2a2581de8d41f3203afd68558dc6f2940e346128f3af8e20ef",
}
GUIDE = [
    "Berkas ini disiapkan kode (candidates.adjudication_workbook). KEPUTUSAN, ragu, dan catatan diisi pemilik proyek sendiri, tanpa bantuan AI.",
    ("Tiap butir punya dua opsi dalam urutan acak, tanpa keterangan asalnya. Opsi bisa berupa artikel yang tampil di bawah "
     "butir, atau 'tidak ada yang cocok'. Bila hanya satu artikel tampil, opsi lainnya adalah TIDAK ADA."),
    "Isi HANYA sel kuning di tiap blok. KEPUTUSAN: id artikel TurnBackHoax yang klaimnya SAMA | TIDAK ADA.",
    *SESSION_GUIDE[2:6],  # pedoman v1.0 + aturan A dan B + ragu, persis seperti sesi buta
    "Urutan butir dan urutan artikel diacak; tidak ada skor. Nomor butir di berkas ini bukan nomor butir di berkas lain.",
    "Lembar terkunci tanpa kata sandi. Jangan membuka kuncinya, menyisipkan/menghapus baris, atau mengurutkan ulang: pembacaan memeriksanya.",
    (f"Simpan hasil sebagai {FILLED_PATH.name} di folder yang sama; koreksi selalu berkas baru (_v2, _v3, ...). "
     f"{KEY_PATH.name}: JANGAN dibuka sebelum selesai."),
]


def disagreements(final: dict[str, Any], modes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Butir analisis yang keputusan modus sistemnya berbeda dari label final, dengan opsi label dan opsi sistem."""
    from evaluation.external_analysis import UNANSWERED
    out = []
    for it in final["butir"]:
        if it["dikeluarkan"]:
            continue
        lab, m = it["label_final"], modes[it["kode"]]
        if m["verdict"] == UNANSWERED:
            continue
        label_opt = lab["expected_article"] if lab["expected_verdict"] == "ditemukan" else NONE
        sys_opt = m["article_id"] if m["verdict"] == "ditemukan" else NONE
        if label_opt == sys_opt:
            continue
        kind = ("kecocokan_palsu" if label_opt == NONE else "penolakan_palsu" if sys_opt == NONE else "artikel_salah")
        out.append({"kode": it["kode"], "l6_id": it["l6_id"], "jenis": kind, "opsi_label": label_opt, "opsi_sistem": sys_opt})
    return out


def write_adjudication(rows: list[dict[str, Any]], valid: dict[str, dict], by_id: dict[str, dict[str, Any]],
                       rng: random.Random, source_hashes: dict[str, str]) -> dict[str, Any]:
    """Acak urutan butir dan artikel, tulis berkas, kunci, dan sidik jari templat (tanpa peta dan tanpa opsi sistem)."""
    rows = list(rows)
    rng.shuffle(rows)
    items = []
    for r in rows:
        arts = [x for x in (r["opsi_label"], r["opsi_sistem"]) if x != NONE]
        rng.shuffle(arts)
        items.append(make_item(valid[r["l6_id"]], arts, by_id, False))
    grid, blocks = layout(items, sort_by_date=False)
    ADJ_DIR.mkdir(parents=True, exist_ok=True)
    stats = write_workbook(grid, blocks, XLSX_PATH, title="Adjudikasi buta evaluasi eksternal (7.6)", guide_lines=GUIDE,
                           generated_by=GENERATED_BY)
    back = read_grid(XLSX_PATH)
    if evidence_hash(back, blocks) != evidence_hash(grid, blocks) and not any(stats.values()):
        raise SystemExit("isi .xlsx tidak sama dengan yang ditulis setelah dibaca ulang")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    key = {"dibuat_utc": now, "catatan": "peta nomor butir -> butir asli dan opsi label/sistem; JANGAN dibuka sebelum selesai",
           "sumber": source_hashes, "peta": [{"butir_adjudikasi": b["butir"], **r} for b, r in zip(blocks, rows)]}
    KEY_PATH.write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    plain = [{k: v for k, v in b.items() if k != "l6_id"} for b in blocks]
    fp = {"dibuat_utc": now, "butir": len(blocks), "baris_artikel": sum(len(b["kandidat"]) for b in blocks),
          "sidik_jari_bukti": evidence_hash(back, blocks), "sha256_templat_xlsx": hashlib.sha256(XLSX_PATH.read_bytes()).hexdigest(),
          "sha256_kunci": hashlib.sha256(KEY_PATH.read_bytes()).hexdigest(),
          "masukan_terisi_saat_dibuat": sum(bool(back[b["baris_masukan"] - 1][c - 1].strip()) for b in blocks for c in INPUT_COLS.values()),
          "asal_usul": provenance(XLSX_PATH), **stats, "blok": plain}
    TEMPLATE_PATH.write_text(json.dumps(fp, ensure_ascii=False, indent=1), encoding="utf-8")
    README_PATH.write_text(
        f"{XLSX_PATH.name} -- adjudikasi buta (docs/rancangan_evaluasi_eksternal.md 7.6), disiapkan kode. KEPUTUSAN, ragu, dan "
        "catatan diisi pemilik proyek sendiri, tanpa bantuan AI.\n"
        f"Simpan hasil sebagai {FILLED_PATH.name} di folder ini (koreksi: berkas baru _v2, _v3, ...), lalu jalankan: "
        "python -m candidates.adjudication_workbook --read\n"
        f"{KEY_PATH.name}: JANGAN dibuka sebelum selesai. Hasil adjudikasi tidak mengubah metrik utama.\n", encoding="utf-8")
    return fp


def make() -> int:
    from evaluation.external_analysis import (
        FINAL_LABELS_SHA256,
        LIPUTAN6_EVAL,
        item_mode,
        locked_final_labels,
    )
    from evaluation.testset_analysis import load_eval_records
    if XLSX_PATH.exists() or KEY_PATH.exists() or TEMPLATE_PATH.exists():
        raise SystemExit(f"{XLSX_PATH.name}, {KEY_PATH.name}, atau {TEMPLATE_PATH.name} sudah ada: tidak ditimpa")
    final = locked_final_labels()
    modes = {k: item_mode(v) for k, v in load_eval_records(LIPUTAN6_EVAL).items()}
    rows = disagreements(final, modes)
    _, _, valid = load_valid_sample()
    hashes = {"label_final": FINAL_LABELS_SHA256,
              "hasil_liputan6": hashlib.sha256(LIPUTAN6_EVAL.read_bytes()).hexdigest()}
    fp = write_adjudication(rows, valid, article_lookup(), random.SystemRandom(), hashes)
    print(json.dumps({k: v for k, v in fp.items() if k != "blok"}, ensure_ascii=False, indent=2))
    print(json.dumps(dict(Counter(r["jenis"] for r in rows)), ensure_ascii=False))
    for p in (XLSX_PATH, KEY_PATH, TEMPLATE_PATH):
        print(f"sha256 {p.name}: {hashlib.sha256(p.read_bytes()).hexdigest()}")
    return 0


def read(path: Path = FILLED_PATH) -> int:
    """Arsipkan, periksa hash tercatat dan bukti, laporkan butir tak terbaca tanpa menebak, lalu petakan ke opsi label/sistem."""
    archived = archive_copy(path, ARCHIVE_DIR, ARCHIVE_LOG)
    print(f"diarsipkan sebelum validasi: {archived['salinan']} (sha256 {archived['sha256']})")
    now = {p.name: (hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "(tidak ada)")
           for p in (XLSX_PATH, KEY_PATH, TEMPLATE_PATH)}
    if not RECORDED_SHA256 or any(now[n] != RECORDED_SHA256.get(n) for n in now):
        print(json.dumps({n: {"sekarang": h, "tercatat": RECORDED_SHA256.get(n)} for n, h in now.items()}, indent=2))
        raise SystemExit("templat, kunci, atau sidik jari tidak sama dengan hash tercatat (7.8): berhenti, tidak ada yang dibaca")
    fp = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    blocks, grid, prov = fp["blok"], read_grid(path), provenance(path)
    checks = {"bukti_sama_dengan_templat": evidence_hash(grid, blocks) == fp["sidik_jari_bukti"],
              "berkas_berubah_sejak_templat": archived["sha256"] != fp["sha256_templat_xlsx"],
              "terakhir_disimpan_aplikasi_lain": bool(prov["lastModifiedBy"])}
    res = read_inputs(grid, blocks)
    problems = res["perlu_ditanyakan"] + [{"butir": d["butir"], "masalah": "bukan id/TIDAK ADA", "isi": d["keputusan"]}
                                          for d in res["butir"] if d["jenis"] not in ("sama", "tidak_ada")]
    report: dict[str, Any] = {"berkas": {"terisi": path.name, "sha256_terisi": archived["sha256"]}, "arsip": archived,
                              "asal_usul": prov, "pemeriksaan": checks, "perlu_ditanyakan": problems}
    if not checks["bukti_sama_dengan_templat"] or problems:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit("bukti berubah dari templat atau ada butir yang belum/tidak terbaca: hasil TIDAK dipetakan")
    key = {str(m["butir_adjudikasi"]): m for m in json.loads(KEY_PATH.read_text(encoding="utf-8"))["peta"]}
    catatan = {str(b["butir"]): grid[b["baris_masukan"] - 1][INPUT_COLS["catatan"] - 1].strip() for b in blocks}
    out = []
    for d in res["butir"]:
        m = key[d["butir"]]
        pick = d["keputusan"]
        side = "label" if pick == m["opsi_label"] else "sistem" if pick == m["opsi_sistem"] else "keduanya_tidak"
        out.append({"butir_adjudikasi": int(d["butir"]), "kode": m["kode"], "jenis_ketidaksesuaian": m["jenis"],
                    "keputusan": pick, "memihak": side, "ragu": d["ragu"], "catatan": catatan[d["butir"]]})
    report |= {"memihak": dict(Counter(o["memihak"] for o in out)),
               "memihak_per_jenis": {j: dict(Counter(o["memihak"] for o in out if o["jenis_ketidaksesuaian"] == j))
                                     for j in sorted({o["jenis_ketidaksesuaian"] for o in out})},
               "catatan": "dicatat terpisah; TIDAK mengubah label final maupun metrik utama (7.6)", "keputusan": out}
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "keputusan"}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--make", action="store_true")
    g.add_argument("--read", action="store_true")
    ap.add_argument("--berkas", type=Path, default=FILLED_PATH)
    args = ap.parse_args()
    return make() if args.make else read(args.berkas)


if __name__ == "__main__":
    raise SystemExit(main())
