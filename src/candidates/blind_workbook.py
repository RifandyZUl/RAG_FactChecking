"""
Berkas sesi buta gabungan evaluasi eksternal (docs/rancangan_evaluasi_eksternal.md bagian 7.2) dan pembacaannya.

Isi: 30 butir uji ulang dari testset/eksternal_sesi_buta_pilihan.json (commit fa7464c, benih 20261027) + 7 butir
audit, dicampur dalam urutan acak dan dinomori ulang 1-37, tanpa penanda mana butir audit. Kandidat tiap butir =
kandidat yang DULU ditampilkan pada berkas konfirmasi aslinya (P1: konfirmasi_50.csv; P2: peta blok templat 49),
dalam urutan acak; teksnya diambil ulang dari articles.json + antrean dan dicocokkan dengan berkas asli (P1: teks
per sel; P2: sidik jari bukti templat 49). Urutan acak memakai random.SystemRandom (tanpa benih, sehingga tidak
dapat direkonstruksi dari kode); peta nomor sesi -> butir asli hanya disimpan di kunci.

Yang TIDAK dibaca kode ini: label/keputusan lama (hasil_konfirmasi*.json, *_terisi.*), kunci skor kandidat, dan
apa pun dari evaluasi eksternal yang tersegel (data/external_eval_*, testset/eksternal_butir.json). KEPUTUSAN,
ragu, dan catatan tidak pernah diisi, diusulkan, atau dikoreksi kode (Aturan Wajib #5).

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m candidates.blind_workbook --make    # menolak menimpa; menulis kunci terpisah
  PYTHONPATH=src python -m candidates.blind_workbook --read    # setelah pemilik proyek selesai; baru di sini kunci dibuka
  PYTHONPATH=src python -m candidates.blind_workbook --read --berkas <..._terisi_v2.xlsx>   # koreksi = berkas baru
Setiap --read menyalin berkas terisi + hash-nya ke arsip_baca/ sebelum validasi apa pun.
"""

import argparse
import hashlib
import json
import random
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from candidates import gap_blocks
from candidates.blind_session import AUDIT, SELECTION_PATH, select
from candidates.gap_blocks import (
    INPUT_COLS,
    NO_NARASI,
    evidence_hash,
    layout,
    read_grid,
    read_inputs,
    write_workbook,
)
from candidates.gap_review import draw_sample, load_queue, load_valid_sample
from candidates.gap_workbook import CSV_PATH, provenance, read_csv_rows
from paths import ARTICLES_PATH, DATA_DIR

SESSION_DIR = DATA_DIR / "candidates" / "sesi_buta_eksternal"
XLSX_PATH = SESSION_DIR / "sesi_buta_37.xlsx"
FILLED_PATH = SESSION_DIR / "sesi_buta_37_terisi.xlsx"  # salinan yang diisi pemilik proyek; inilah yang dibaca --read
TEMPLATE_PATH = SESSION_DIR / "sidik_jari_templat_sesi_buta.json"  # tanpa peta ke butir asli
KEY_PATH = SESSION_DIR / "kunci_sesi_buta.json"  # peta nomor sesi -> butir asli; hanya dibuka --read
RESULT_PATH = SESSION_DIR / "hasil_sesi_buta.json"
README_PATH = SESSION_DIR / "BACA_SAYA.txt"
# setiap berkas yang dibaca --read disalin ke sini lebih dulu (7.2: versi pertama pernah tertimpa koreksi bernama sama)
ARCHIVE_DIR = SESSION_DIR / "arsip_baca"
ARCHIVE_LOG = ARCHIVE_DIR / "arsip_baca.jsonl"
GENERATED_BY = "candidates.blind_workbook (openpyxl; tata letak dihasilkan kode, KEPUTUSAN/ragu/catatan diisi manusia)"
SESSION_SIZE = 37
# dicatat di docs/rancangan_evaluasi_eksternal.md 7.2 (commit yang sama) SEBELUM sesi diisi; --read berhenti bila beda
RECORDED_SHA256 = {
    "sesi_buta_37.xlsx": "ba5f6f8a7886f6b880c340132e510053346c54551c41409628a5a0ef5b3ca6c1",
    "kunci_sesi_buta.json": "75263881065e111f5d9430046620060c30a88fe5e6e5816e4d94dc6937bd9d17",
    "sidik_jari_templat_sesi_buta.json": "3efbfa953f888bc8412d56e967abbd4ff03e11aa12a00ee1dd52ae3e791b45c4",
}
GUIDE = [
    "Berkas ini disiapkan kode (candidates.blind_workbook). KEPUTUSAN, ragu, dan catatan diisi pemilik proyek sendiri, tanpa bantuan AI.",
    "Isi HANYA sel kuning di tiap blok. KEPUTUSAN: id artikel TurnBackHoax yang klaimnya SAMA | TIDAK ADA | BUKAN PUTUSAN HOAKS.",
    "Kesamaan klaim menurut testset/ANNOTATION_GUIDE.md v1.0, ditambah aturan A dan B (docs/rancangan_v2.md bagian 11.6):",
    ("Aturan A -- selisih waktu atau gelombang. Unsur inti (subjek, tindakan, objek pembeda) menentukan; tanggal terbit tidak. "
    "Untuk tautan penipuan berulang, lembaga dan jenis tawaran yang sama berarti cocok walaupun gelombangnya berbeda. "
    "Tahun atau periode hanya menjadi pembeda bila disebut eksplisit di kedua sisi dan berbeda."),
    ("Aturan B -- detail tidak disebut versus detail bertentangan. Detail yang tidak disebut BUKAN alasan menolak; hanya detail "
    "yang bertentangan pada unsur inti yang menjadi alasan menolak. Pembandingnya adalah kutipan pesan Liputan6 dengan Narasi "
    "TurnBackHoax, bukan hanya judul dan Kesimpulan."),
    "ragu: YA atau kosong; hanya boleh ditandai setelah Narasi kandidat dibaca. Tanda ragu di kolom ragu, bukan di catatan.",
    "Urutan butir dan urutan kandidat diacak; tidak ada skor. Nomor butir di berkas ini bukan nomor butir di berkas konfirmasi lama.",
    f"Kandidat tanpa Narasi di sumber ditandai {NO_NARASI}.",
    "Lembar terkunci tanpa kata sandi. Jangan membuka kuncinya, menyisipkan/menghapus baris, atau mengurutkan ulang: pembacaan memeriksanya.",
    f"Simpan hasil sebagai {FILLED_PATH.name} di folder yang sama. {KEY_PATH.name}: JANGAN dibuka sebelum sesi selesai.",
]


def session_refs(selection: dict[str, Any]) -> list[dict[str, Any]]:
    """
    37 butir sesi sebagai (putaran, nomor butir asli, jenis). Pilihan uji ulang harus sama dengan yang dihitung
    ulang dari benih; audit diambil dari pilihan tersimpan dan dicocokkan dengan AUDIT.
    """
    if selection != select():
        raise SystemExit(f"{SELECTION_PATH.name} tidak sama dengan pemilihan berbenih yang dihitung ulang")
    audit = [(int(code[1]), int(code.split("-")[1])) for code in selection["audit_dicampur_tanpa_penanda"]]
    if audit != [(int(p[1]), n) for p, n in AUDIT]:
        raise SystemExit("daftar audit di berkas pilihan tidak sama dengan AUDIT")
    refs = [{"putaran": r, "butir_asli": n, "jenis": "uji_ulang"} for r in (2, 1) for n in selection["uji_ulang"][f"putaran_{r}"]]
    refs += [{"putaran": r, "butir_asli": n, "jenis": "audit"} for r, n in audit]
    if len(refs) != SESSION_SIZE or len({(x["putaran"], x["butir_asli"]) for x in refs}) != SESSION_SIZE:
        raise SystemExit("isi sesi bukan 37 butir unik")
    return [{**x, "kode": f"P{x['putaran']}-{x['butir_asli']}"} for x in refs]


def article_lookup() -> dict[str, dict[str, Any]]:
    """Artikel basis (articles.json) + antrean (belum digabung), dengan asal seperti pada berkas konfirmasi."""
    db = json.loads(Path(ARTICLES_PATH).read_text(encoding="utf-8"))
    by_id = {a["article_id"]: {**a, "asal": "indeks"} for a in db}
    by_id.update({a["article_id"]: {**a, "asal": "antrean (belum di-ingest)"} for a in load_queue(set(by_id))})
    return by_id


def make_item(l6: dict[str, Any], cand_ids: list[str], by_id: dict[str, dict[str, Any]], ujung: bool) -> dict[str, Any]:
    """Butir dalam bentuk candidates.gap_review.build_items (tanpa pencarian ulang: kandidat diberikan)."""
    return {"id": l6["id"], "judul": l6["judul"], "tanggal": l6["tanggal"], "pesan": l6["pesan"], "ujung_rentang": ujung,
            "kandidat": [{"id": c, "tanggal": by_id[c]["date"], "label": by_id[c]["label"], "asal": by_id[c]["asal"],
                          "judul": by_id[c]["title"], "narasi": by_id[c].get("narasi") or "", "kesimpulan": by_id[c]["kesimpulan"]}
                         for c in cand_ids]}


def _same(a: str, b: str) -> bool:
    return a.replace("\r\n", "\n").replace("\r", "\n") == b.replace("\r\n", "\n").replace("\r", "\n")


def round1_items(valid: dict[str, dict], by_id: dict[str, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """
    Putaran 1 (50 butir): urutan butir dari pengambilan berbenih (gap_review.draw_sample), kandidat dari
    konfirmasi_50.csv (templat buatan kode; KEPUTUSAN/catatan wajib kosong). Setiap teks yang dulu tampil
    dicocokkan dengan teks yang diambil ulang; Narasi tidak ada di berkas lama, jadi tidak dapat dicocokkan.
    """
    rows = read_csv_rows(CSV_PATH)
    if any(r["KEPUTUSAN"].strip() or r["catatan"].strip() for r in rows):
        raise SystemExit(f"{CSV_PATH.name} memuat keputusan/catatan: bukan templat kosong, tidak dibaca")
    order = draw_sample(list(valid))
    by_butir: dict[int, list[dict[str, str]]] = {}
    for r in rows:
        by_butir.setdefault(int(r["butir"]), []).append(r)
    if sorted(by_butir) != list(range(1, len(order) + 1)):
        raise SystemExit("nomor butir konfirmasi_50.csv tidak sama dengan pengambilan berbenih")
    items = {}
    for n, l6_id in enumerate(order, 1):
        first, l6 = by_butir[n][0], valid[l6_id]
        item = make_item(l6, [r["TBH_id"] for r in by_butir[n]], by_id, first["ujung_rentang"] == "YA")
        checks = [(first["L6_judul"], l6["judul"]), (first["L6_tanggal"], l6["tanggal"]), (first["L6_kutipan_pesan"], l6["pesan"])]
        for r, c in zip(by_butir[n], item["kandidat"]):
            checks += [(r["TBH_tanggal"], c["tanggal"]), (r["TBH_label"], c["label"]), (r["TBH_asal"], c["asal"]),
                       (r["TBH_judul"], c["judul"]), (r["TBH_kesimpulan"], c["kesimpulan"])]
        if not all(_same(a, b) for a, b in checks):
            raise SystemExit(f"P1-{n}: teks yang diambil ulang tidak sama dengan konfirmasi_50.csv")
        items[n] = item
    return items


def round2_items(valid: dict[str, dict], by_id: dict[str, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """
    Putaran 2 (49 butir): butir dan kandidat dari peta blok templat 49 (tanpa keputusan). Seluruh lembar 49
    disusun ulang dan sidik jari buktinya wajib sama dengan saat templat dibuat, jadi teks yang tampil identik.
    """
    fp = json.loads(gap_blocks.TEMPLATE_PATH.read_text(encoding="utf-8"))
    items = {b["butir"]: make_item(valid[b["l6_id"]], [c["id"] for c in b["kandidat"]], by_id, b["ujung_rentang"])
             for b in fp["blok"]}
    grid, blocks = layout([items[n] for n in sorted(items)])
    if evidence_hash(grid, blocks) != fp["sidik_jari_bukti"]:
        raise SystemExit("P2: lembar yang disusun ulang tidak sama dengan sidik jari templat 49")
    return items


def make() -> int:
    if XLSX_PATH.exists() or KEY_PATH.exists() or TEMPLATE_PATH.exists():
        raise SystemExit(f"{XLSX_PATH.name}, {KEY_PATH.name}, atau {TEMPLATE_PATH.name} sudah ada: tidak ditimpa")
    selection_bytes = SELECTION_PATH.read_bytes()
    refs = session_refs(json.loads(selection_bytes))
    _, _, valid = load_valid_sample()
    by_id = article_lookup()
    source = {1: round1_items(valid, by_id), 2: round2_items(valid, by_id)}
    fp = write_session(refs, source, random.SystemRandom(), hashlib.sha256(selection_bytes).hexdigest())
    print(json.dumps({k: v for k, v in fp.items() if k != "blok"}, ensure_ascii=False, indent=2))
    return 0


def write_session(refs: list[dict[str, Any]], source: dict[int, dict[int, dict[str, Any]]], rng: random.Random,
                  selection_sha: str) -> dict[str, Any]:
    """
    Acak urutan butir dan kandidat, tulis berkas sesi, kunci (peta ke butir asli), dan sidik jari templat (TANPA
    peta ke butir asli). `rng` = SystemRandom pada pemakaian nyata; uji memakai Random berbenih.
    """
    refs = list(refs)
    rng.shuffle(refs)
    items = []
    for ref in refs:
        item = source[ref["putaran"]][ref["butir_asli"]]
        cands = list(item["kandidat"])
        rng.shuffle(cands)
        items.append({**item, "kandidat": cands})
    grid, blocks = layout(items, sort_by_date=False)
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    stats = write_workbook(grid, blocks, XLSX_PATH, title="Sesi buta gabungan evaluasi eksternal (7.2)",
                           guide_lines=GUIDE, generated_by=GENERATED_BY)
    back = read_grid(XLSX_PATH)
    if evidence_hash(back, blocks) != evidence_hash(grid, blocks) and not any(stats.values()):
        raise SystemExit("isi .xlsx tidak sama dengan yang ditulis setelah dibaca ulang")

    key = {"dibuat_utc": datetime.now(UTC).isoformat(timespec="seconds"),
           "catatan": "peta nomor butir sesi -> butir asli; JANGAN dibuka sebelum sesi selesai",
           "peta": [{"butir_sesi": b["butir"], **ref, "l6_id": item["id"]} for b, ref, item in zip(blocks, refs, items)]}
    KEY_PATH.write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    # peta blok templat TANPA l6_id dan tanpa butir asli: cukup untuk memeriksa dan membaca berkas terisi
    plain = [{k: v for k, v in b.items() if k != "l6_id"} for b in blocks]
    n_cand = [len(b["kandidat"]) for b in blocks]
    fp = {"dibuat_utc": key["dibuat_utc"], "butir": len(blocks), "baris_kandidat": sum(n_cand),
          "kandidat_per_butir_min_median_maks": [min(n_cand), sorted(n_cand)[len(n_cand) // 2], max(n_cand)],
          "sha256_berkas_pilihan": selection_sha,
          "sidik_jari_bukti": evidence_hash(back, blocks), "sha256_templat_xlsx": hashlib.sha256(XLSX_PATH.read_bytes()).hexdigest(),
          "sha256_kunci": hashlib.sha256(KEY_PATH.read_bytes()).hexdigest(),
          "masukan_terisi_saat_dibuat": sum(bool(back[b["baris_masukan"] - 1][c - 1].strip()) for b in blocks for c in INPUT_COLS.values()),
          "asal_usul": provenance(XLSX_PATH), **stats, "blok": plain}
    TEMPLATE_PATH.write_text(json.dumps(fp, ensure_ascii=False, indent=1), encoding="utf-8")
    README_PATH.write_text(
        f"{XLSX_PATH.name} -- sesi buta gabungan (docs/rancangan_evaluasi_eksternal.md 7.2), disiapkan kode "
        "(candidates.blind_workbook). KEPUTUSAN, ragu, dan catatan diisi pemilik proyek sendiri, tanpa bantuan AI.\n"
        f"Simpan hasil sebagai {FILLED_PATH.name} di folder ini, lalu jalankan: python -m candidates.blind_workbook --read\n"
        f"{KEY_PATH.name}: JANGAN dibuka sebelum sesi selesai. Jangan membuka berkas konfirmasi lama selama sesi.\n",
        encoding="utf-8")
    return fp


def archive_copy(path: Path, archive_dir: Path | None = None, log_path: Path | None = None) -> dict[str, Any]:
    """
    Salin berkas terisi apa adanya ke ARCHIVE_DIR (atau `archive_dir`) dan catat hash-nya, SEBELUM validasi apa pun.
    Berkas yang sudah diserahkan tidak boleh ditimpa (koreksi disimpan sebagai _v2, _v3, ...): bila nama yang sama
    pernah dibaca dengan hash lain, salinan tetap dibuat lalu pembacaan berhenti.
    """
    if not path.exists():
        raise SystemExit(f"berkas terisi tidak ada: {path}")
    archive_dir, log_path = archive_dir or ARCHIVE_DIR, log_path or ARCHIVE_LOG
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC)
    dest = archive_dir / f"{stamp.strftime('%Y%m%dT%H%M%S%fZ')}_{sha[:12]}_{path.name}"
    with dest.open("xb") as f:  # "x": salinan arsip juga tidak pernah ditimpa
        f.write(data)
    if hashlib.sha256(dest.read_bytes()).hexdigest() != sha:
        raise SystemExit(f"salinan arsip tidak sama dengan berkas asli: {dest}")
    earlier = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()] \
        if log_path.exists() else []
    entry = {"waktu_utc": stamp.isoformat(timespec="seconds"), "berkas": path.name, "sha256": sha, "ukuran": len(data),
             "salinan": dest.name}
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    overwritten = sorted({e["sha256"] for e in earlier if e["berkas"] == path.name and e["sha256"] != sha})
    if overwritten:
        raise SystemExit(f"{path.name} pernah dibaca dengan hash lain ({', '.join(h[:12] for h in overwritten)}): berkas yang "
                         "sudah diserahkan tidak boleh ditimpa; simpan koreksi sebagai berkas baru berakhiran _v2, _v3, ...")
    return entry


def read(path: Path = FILLED_PATH) -> int:
    """
    Arsipkan berkas terisi (archive_copy), lalu periksa (bukti sama dengan templat, asal-usul), laporkan butir yang
    kosong/tidak terbaca tanpa menebak, dan BARU SETELAH semuanya terbaca buka kunci untuk memetakan keputusan ke butir
    asli. Tidak menghitung kappa atau metrik evaluasi; tidak membaca label lama.
    """
    archived = archive_copy(path)
    print(f"diarsipkan sebelum validasi: {archived['salinan']} (sha256 {archived['sha256']})")
    recorded = {p.name: (hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "(tidak ada)",
                         RECORDED_SHA256.get(p.name)) for p in (XLSX_PATH, KEY_PATH, TEMPLATE_PATH)}
    if any(now != want for now, want in recorded.values()):
        print(json.dumps({name: {"sekarang": now, "tercatat": want} for name, (now, want) in recorded.items()}, indent=2))
        raise SystemExit("templat, kunci, atau sidik jari templat tidak sama dengan hash tercatat (7.2): berhenti, tidak ada yang dibaca")
    fp = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    blocks, grid, prov = fp["blok"], read_grid(path), provenance(path)
    checks = {"bukti_sama_dengan_templat": evidence_hash(grid, blocks) == fp["sidik_jari_bukti"],
              "berkas_berubah_sejak_templat": hashlib.sha256(path.read_bytes()).hexdigest() != fp["sha256_templat_xlsx"],
              "terakhir_disimpan_aplikasi_lain": bool(prov["lastModifiedBy"]),
              "kunci_tidak_berubah": hashlib.sha256(KEY_PATH.read_bytes()).hexdigest() == fp["sha256_kunci"]}
    if path != XLSX_PATH and XLSX_PATH.exists():  # templat seharusnya tetap kosong; dilaporkan apa adanya bila tidak
        checks["templat_masih_seperti_saat_dibuat"] = hashlib.sha256(XLSX_PATH.read_bytes()).hexdigest() == fp["sha256_templat_xlsx"]
    res = read_inputs(grid, blocks)
    report: dict[str, Any] = {"berkas": {"terisi": path.name, "sha256_terisi": hashlib.sha256(path.read_bytes()).hexdigest()},
                              "arsip": archived, "asal_usul": prov, "pemeriksaan": checks, "perlu_ditanyakan": res["perlu_ditanyakan"]}
    if not checks["bukti_sama_dengan_templat"] or not checks["kunci_tidak_berubah"] or res["perlu_ditanyakan"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit("bukti/kunci berubah dari templat atau ada butir yang belum/tidak terbaca: hasil TIDAK dipetakan")
    key = {str(m["butir_sesi"]): m for m in json.loads(KEY_PATH.read_text(encoding="utf-8"))["peta"]}
    if set(key) != {str(b["butir"]) for b in blocks}:
        raise SystemExit("nomor butir di kunci tidak sama dengan peta blok templat")
    catatan = {str(b["butir"]): grid[b["baris_masukan"] - 1][INPUT_COLS["catatan"] - 1].strip() for b in blocks}
    decisions = [{"butir_sesi": int(d["butir"]), "kode": key[d["butir"]]["kode"], "putaran": key[d["butir"]]["putaran"],
                  "butir_asli": key[d["butir"]]["butir_asli"], "jenis_butir": key[d["butir"]]["jenis"], "l6_id": key[d["butir"]]["l6_id"],
                  "jenis": d["jenis"], "keputusan": d["keputusan"], "ragu": d["ragu"], "catatan": catatan[d["butir"]]}
                 for d in res["butir"]]
    report.update({"jenis_keputusan": dict(Counter(d["jenis"] for d in decisions)),
                   "butir_per_jenis": dict(Counter(d["jenis_butir"] for d in decisions)),
                   "catatan_terisi": sum(bool(c) for c in catatan.values()), "keputusan": decisions})
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "keputusan"}, ensure_ascii=False, indent=2))
    print(f"keputusan per butir tersimpan di {RESULT_PATH}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--make", action="store_true", help="buat berkas sesi buta (menolak menimpa)")
    g.add_argument("--read", action="store_true", help="baca keputusan dari berkas terisi dan petakan ke butir asli")
    ap.add_argument("--berkas", type=Path, default=FILLED_PATH, help=f"berkas terisi untuk --read (bawaan {FILLED_PATH.name})")
    args = ap.parse_args()
    return make() if args.make else read(args.berkas)


if __name__ == "__main__":
    raise SystemExit(main())
