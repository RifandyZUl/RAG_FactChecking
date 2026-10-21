"""
Verifikasi label butir negatif testset-v1 yang pada indeks 1.532 dicocokkan sistem ke artikel baru
(docs/rancangan_evaluasi_eksternal.md 11.8). Pertanyaannya: apakah artikel itu memuat klaim yang SAMA dengan kueri
butir menurut pedoman v1.0 (testset/ANNOTATION_GUIDE.md)? Jawaban SAMA | BEDA | RAGU, dengan catatan.

Berkas menampilkan kueri testset-v1 dan artikel yang dicocokkan sistem (judul, tanggal, label, Narasi, Kesimpulan),
dalam format dan proteksi seperti berkas sesi buta (candidates.gap_blocks). Keputusan dan penjelasan generator TIDAK
ditampilkan; nomor butir v1 hanya ada di kunci. testset/v1.jsonl tidak diubah. Keputusan diisi pemilik proyek
sendiri, tanpa bantuan AI (Aturan Wajib #5).

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m candidates.v1_verification --make   # menolak menimpa
  PYTHONPATH=src python -m candidates.v1_verification --read [--berkas <..._terisi_v2.xlsx>]
"""

import argparse
import hashlib
import json
import random
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from candidates.blind_workbook import archive_copy, article_lookup
from candidates.gap_blocks import (
    INPUT_COLS,
    evidence_hash,
    layout,
    normalize_decision,
    read_grid,
    write_workbook,
)
from candidates.gap_workbook import provenance
from paths import DATA_DIR

VER_DIR = DATA_DIR / "candidates" / "verifikasi_v1"
XLSX_PATH = VER_DIR / "verifikasi_v1_negatif.xlsx"
FILLED_PATH = VER_DIR / "verifikasi_v1_negatif_terisi.xlsx"
TEMPLATE_PATH = VER_DIR / "sidik_jari_templat_verifikasi_v1.json"
KEY_PATH = VER_DIR / "kunci_verifikasi_v1.json"  # peta nomor -> id butir v1 dan artikel; hanya dibuka --read
RESULT_PATH = VER_DIR / "hasil_verifikasi_v1.json"
README_PATH = VER_DIR / "BACA_SAYA.txt"
ARCHIVE_DIR = VER_DIR / "arsip_baca"
ARCHIVE_LOG = ARCHIVE_DIR / "arsip_baca.jsonl"
GENERATED_BY = "candidates.v1_verification (openpyxl; tata letak dihasilkan kode, KEPUTUSAN/catatan diisi manusia)"
ITEMS = ("v1-024", "v1-026", "v1-027")  # bagian 11.4: negatif sulit yang kini dicocokkan ke artikel di luar indeks 150
ANSWERS = ("SAMA", "BEDA", "RAGU")
NET_REGRESSION_LIMIT = 3  # 6.3, tidak diubah
# dicatat di docs/rancangan_evaluasi_eksternal.md 11.8 (commit yang sama) SEBELUM diisi; --read berhenti bila beda
RECORDED_SHA256: dict[str, str] = {
    "verifikasi_v1_negatif.xlsx": "2a1cff46132444add6d9973bc5883c9bdd0cd41c48be4f4bbd0656bb66efea83",
    "kunci_verifikasi_v1.json": "f824f4fb293e3bdcd3db5d21b8a528aa36410fe4791abed344946dd906243244",
    "sidik_jari_templat_verifikasi_v1.json": "829d7771a4eaf49f1c160d3486bb93531a3b3993ff825746efc3793341053f43",
}
GUIDE = [
    "Berkas ini disiapkan kode (candidates.v1_verification). KEPUTUSAN dan catatan diisi pemilik proyek sendiri, tanpa bantuan AI.",
    ("Tiap butir: satu kueri dari set uji v1 dan satu artikel TurnBackHoax di bawahnya. Pertanyaan: apakah artikel itu memuat "
     "klaim yang SAMA dengan kueri menurut pedoman testset/ANNOTATION_GUIDE.md v1.0 (klaim inti = judul; unsur inti; uji dua arah; "
     "uji Kesimpulan)?"),
    "Isi HANYA sel kuning. KEPUTUSAN: SAMA | BEDA | RAGU. Tulis alasan singkat di catatan. Kolom ragu tidak dipakai (biarkan kosong).",
    "Kandidat yang tampil adalah artikel yang perlu dinilai; tidak ada skor dan tidak ada keterangan lain tentang asalnya.",
    "Lembar terkunci tanpa kata sandi. Jangan membuka kuncinya, menyisipkan/menghapus baris, atau mengurutkan ulang.",
    (f"Simpan hasil sebagai {FILLED_PATH.name} di folder yang sama; koreksi selalu berkas baru (_v2, _v3, ...). "
     f"{KEY_PATH.name}: JANGAN dibuka sebelum selesai."),
]


def matched_articles(metrics: dict[str, Any]) -> dict[str, str]:
    """Artikel yang dicocokkan sistem (modus 3 run, indeks 1.532) untuk ketiga butir, dari hasil --metrik."""
    rows = {r["id"]: r for r in metrics["kemunduran_v1"]["perpindahan_non_batas"]}
    out = {}
    for i in ITEMS:
        verdict, art = rows[i]["modus_1532"]
        if verdict != "ditemukan" or not art:
            raise SystemExit(f"{i}: modus 1.532 bukan 'ditemukan'")
        out[i] = art
    return out


def build(items: list[dict[str, Any]], by_id: dict[str, dict[str, Any]], rng: random.Random) -> tuple[list, list, list]:
    """Kisi + peta blok dengan label baris diganti untuk kueri v1 (tanpa id butir v1 dan tanpa tanggal Liputan6)."""
    items = list(items)
    rng.shuffle(items)
    shaped = [{"id": it["v1_id"], "judul": "(kueri set uji v1 -- tanpa judul)", "tanggal": "-", "pesan": it["klaim"],
               "ujung_rentang": False,
               "kandidat": [{"id": a, "tanggal": by_id[a]["date"], "label": by_id[a]["label"], "asal": by_id[a]["asal"],
                             "judul": by_id[a]["title"], "narasi": by_id[a].get("narasi") or "", "kesimpulan": by_id[a]["kesimpulan"]}
                            for a in [it["article_id"]]]} for it in items]
    grid, blocks = layout(shaped, sort_by_date=False)
    for b in blocks:
        top = b["baris_masukan"] - 4  # baris "BUTIR n" (lihat gap_blocks.layout)
        grid[top][1] = "verifikasi label set uji v1"
        grid[top + 1][0], grid[top + 2][0] = "kueri", "kueri_set_uji_v1"
        grid[b["baris_masukan"] - 1][2] = "(kolom ini tidak dipakai)"
    return grid, blocks, items


def write_files(items: list[dict[str, Any]], by_id: dict[str, dict[str, Any]], rng: random.Random,
                source: dict[str, str]) -> dict[str, Any]:
    grid, blocks, items = build(items, by_id, rng)
    VER_DIR.mkdir(parents=True, exist_ok=True)
    stats = write_workbook(grid, blocks, XLSX_PATH, title="Verifikasi label negatif set uji v1 pada indeks 1.532 (11.8)",
                           guide_lines=GUIDE, generated_by=GENERATED_BY)
    back = read_grid(XLSX_PATH)
    now = datetime.now(UTC).isoformat(timespec="seconds")
    key = {"dibuat_utc": now, "catatan": "peta nomor butir -> butir v1 dan artikel; JANGAN dibuka sebelum selesai", "sumber": source,
           "peta": [{"butir": b["butir"], "v1_id": it["v1_id"], "article_id": it["article_id"]} for b, it in zip(blocks, items)]}
    KEY_PATH.write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    plain = [{k: v for k, v in b.items() if k != "l6_id"} for b in blocks]
    fp = {"dibuat_utc": now, "butir": len(blocks), "sidik_jari_bukti": evidence_hash(back, blocks),
          "sha256_templat_xlsx": hashlib.sha256(XLSX_PATH.read_bytes()).hexdigest(),
          "sha256_kunci": hashlib.sha256(KEY_PATH.read_bytes()).hexdigest(),
          "masukan_terisi_saat_dibuat": sum(bool(back[b["baris_masukan"] - 1][c - 1].strip()) for b in blocks for c in INPUT_COLS.values()),
          "asal_usul": provenance(XLSX_PATH), **stats, "blok": plain}
    TEMPLATE_PATH.write_text(json.dumps(fp, ensure_ascii=False, indent=1), encoding="utf-8")
    README_PATH.write_text(
        f"{XLSX_PATH.name} -- verifikasi label negatif set uji v1 (docs/rancangan_evaluasi_eksternal.md 11.8), disiapkan kode. "
        "KEPUTUSAN (SAMA/BEDA/RAGU) dan catatan diisi pemilik proyek sendiri, tanpa bantuan AI.\n"
        f"Simpan hasil sebagai {FILLED_PATH.name} (koreksi: berkas baru _v2, ...), lalu: python -m candidates.v1_verification --read\n"
        f"{KEY_PATH.name}: JANGAN dibuka sebelum selesai.\n", encoding="utf-8")
    return fp


def make() -> int:
    from evaluation.external_analysis import METRICS_PATH
    from evaluation.testset_analysis import V1_PATH, load_v1_items
    if XLSX_PATH.exists() or KEY_PATH.exists() or TEMPLATE_PATH.exists():
        raise SystemExit(f"{XLSX_PATH.name}, {KEY_PATH.name}, atau {TEMPLATE_PATH.name} sudah ada: tidak ditimpa")
    arts = matched_articles(json.loads(METRICS_PATH.read_text(encoding="utf-8")))
    v1 = load_v1_items(V1_PATH)
    items = [{"v1_id": i, "klaim": v1[i]["klaim"], "article_id": arts[i]} for i in ITEMS]
    source = {"sha256_v1_jsonl": hashlib.sha256(V1_PATH.read_bytes()).hexdigest(),
              "sha256_hasil_evaluasi": hashlib.sha256(METRICS_PATH.read_bytes()).hexdigest()}
    fp = write_files(items, article_lookup(), random.SystemRandom(), source)
    print(json.dumps({k: v for k, v in fp.items() if k != "blok"}, ensure_ascii=False, indent=2))
    for p in (XLSX_PATH, KEY_PATH, TEMPLATE_PATH):
        print(f"sha256 {p.name}: {hashlib.sha256(p.read_bytes()).hexdigest()}")
    return 0


def regression_sensitivity(regression: dict[str, Any], same: list[str], doubtful: list[str]) -> dict[str, Any]:
    """
    11.8 (ditetapkan sebelum diisi): butir SAMA dikeluarkan dari analisis kemunduran sebagai perubahan status label;
    RAGU dihitung dua arah (dikeluarkan / tetap). Ambang >= 3 tidak diubah. Hanya sensitivitas; angka utama tetap.
    """
    def recount(excluded: set[str]) -> dict[str, Any]:
        down = [i for i in regression["benar_ke_salah"] if i not in excluded]
        up = [i for i in regression["salah_ke_benar"] if i not in excluded]
        net = len(down) - len(up)
        return {"dikeluarkan": sorted(excluded), "non_batas": regression["non_batas"] - len(excluded), "benar_ke_salah": down,
                "salah_ke_benar": up, "kemunduran_bersih": net, "kategori": "mundur" if net >= NET_REGRESSION_LIMIT else "tidak_mundur"}
    out = {"utama_tidak_berubah": {"kemunduran_bersih": regression["kemunduran_bersih"], "kategori": regression["kategori"]},
           "SAMA_dikeluarkan": recount(set(same))}
    if doubtful:
        out["RAGU_juga_dikeluarkan"] = recount(set(same) | set(doubtful))
    return out


def read(path: Path = FILLED_PATH) -> int:
    from evaluation.external_analysis import METRICS_PATH
    archived = archive_copy(path, ARCHIVE_DIR, ARCHIVE_LOG)
    print(f"diarsipkan sebelum validasi: {archived['salinan']} (sha256 {archived['sha256']})")
    now = {p.name: (hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "(tidak ada)")
           for p in (XLSX_PATH, KEY_PATH, TEMPLATE_PATH)}
    if not RECORDED_SHA256 or any(now[n] != RECORDED_SHA256.get(n) for n in now):
        print(json.dumps({n: {"sekarang": h, "tercatat": RECORDED_SHA256.get(n)} for n, h in now.items()}, indent=2))
        raise SystemExit("templat, kunci, atau sidik jari tidak sama dengan hash tercatat (11.8): berhenti, tidak ada yang dibaca")
    fp = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    blocks, grid, prov = fp["blok"], read_grid(path), provenance(path)
    checks = {"bukti_sama_dengan_templat": evidence_hash(grid, blocks) == fp["sidik_jari_bukti"],
              "berkas_berubah_sejak_templat": archived["sha256"] != fp["sha256_templat_xlsx"],
              "terakhir_disimpan_aplikasi_lain": bool(prov["lastModifiedBy"])}
    answers, problems = {}, []
    for b in blocks:
        r = b["baris_masukan"] - 1
        val = normalize_decision(grid[r][INPUT_COLS["KEPUTUSAN"] - 1])
        if val not in ANSWERS:
            problems.append({"butir": b["butir"], "masalah": "KEPUTUSAN bukan SAMA/BEDA/RAGU", "isi": grid[r][INPUT_COLS["KEPUTUSAN"] - 1]})
        if grid[r][INPUT_COLS["ragu"] - 1].strip():
            problems.append({"butir": b["butir"], "masalah": "kolom ragu tidak dipakai tetapi terisi", "isi": grid[r][INPUT_COLS["ragu"] - 1]})
        answers[b["butir"]] = {"keputusan": val, "catatan": grid[r][INPUT_COLS["catatan"] - 1].strip()}
    report: dict[str, Any] = {"berkas": {"terisi": path.name, "sha256_terisi": archived["sha256"]}, "arsip": archived,
                              "asal_usul": prov, "pemeriksaan": checks, "perlu_ditanyakan": problems}
    if not checks["bukti_sama_dengan_templat"] or problems:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit("bukti berubah dari templat atau ada butir yang belum/tidak terbaca: hasil TIDAK dipetakan")
    key = {m["butir"]: m for m in json.loads(KEY_PATH.read_text(encoding="utf-8"))["peta"]}
    out = [{"v1_id": key[n]["v1_id"], "article_id": key[n]["article_id"], **a} for n, a in sorted(answers.items())]
    reg = json.loads(METRICS_PATH.read_text(encoding="utf-8"))["kemunduran_v1"]
    report |= {"jawaban": dict(Counter(o["keputusan"] for o in out)), "butir": out,
               "sensitivitas_kemunduran": regression_sensitivity(reg, [o["v1_id"] for o in out if o["keputusan"] == "SAMA"],
                                                                 [o["v1_id"] for o in out if o["keputusan"] == "RAGU"]),
               "catatan": "testset/v1.jsonl tidak diubah; angka kemunduran utama tetap"}
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
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
