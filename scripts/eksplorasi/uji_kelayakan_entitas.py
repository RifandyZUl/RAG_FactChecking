"""
Uji kelayakan pemeriksaan entitas (EKSPLORATIF; rancangan Versi 2 bagian A2.5).

Menerapkan aturan A2 (setelah koreksi 2026-10-26: domain dan nomor hanya bukti pendukung) pada keluaran
evaluasi eksternal yang SUDAH tersimpan, tanpa panggilan LLM dan tanpa jaringan. Data ini sudah pernah dilihat,
jadi hasilnya BUKAN bukti kinerja Versi 2; gunanya hanya menilai apakah rancangan entitas layak dilanjutkan
sebelum pelabelan.

Masukan (lokal, tidak di-commit): teks kutipan Liputan6 dari berkas pelabelan (dibangun ulang lewat
`evaluation.external_eval.build_liputan6_cases`, dicocokkan dengan `sha256_kutipan` di
`testset/eksternal_butir.json`), artikel dari `data/articles.json`. Keputusan modus per butir dari
`testset/eksternal_hasil_per_butir.json` (ter-commit).

Keluaran: `data/eksplorasi/uji_kelayakan_entitas.json` (lokal) berisi kode butir dan STATUS entitas saja;
tidak ada teks pesan, judul, atau nilai entitas dari pesan. Ringkasan dicetak ke layar.

Daftar lembaga dan program di bawah disusun dari pengetahuan umum tentang nama lembaga dan program pemerintah
Indonesia, SEBELUM skrip dijalankan, bukan dari artikel basis data. Untuk Versi 2, daftar ini harus diganti
daftar dari sumber resmi (rancangan A2.1). Perubahan apa pun setelah melihat hasil wajib dicatat di A2.5.

Pemakaian (dari root proyek): python scripts/eksplorasi/uji_kelayakan_entitas.py
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

OUT_PATH = ROOT / "data" / "eksplorasi" / "uji_kelayakan_entitas.json"

# -- Lembaga: nama kanonik -> pola alias (huruf kecil, batas kata) ----------------------------------------------
LEMBAGA = {
    "kemensos": ["kemensos", "kementerian sosial"],
    "kemenag": ["kemenag", "kementerian agama"],
    "kemenkes": ["kemenkes", "kementerian kesehatan"],
    "kemendikdasmen": ["kemendikbud", "kemendikbudristek", "kemendikdasmen", "kementerian pendidikan"],
    "kemnaker": ["kemnaker", "kemenaker", "kementerian ketenagakerjaan"],
    "kemenhub": ["kemenhub", "kementerian perhubungan"],
    "kemenkeu": ["kemenkeu", "kementerian keuangan"],
    "kemendagri": ["kemendagri", "kementerian dalam negeri"],
    "kementan": ["kementan", "kementerian pertanian"],
    "kkp": ["kementerian kelautan"],
    "komdigi": ["kominfo", "komdigi", "kementerian komunikasi"],
    "kemenpupr": ["kemenpupr", "kementerian pupr", "kementerian pekerjaan umum"],
    "kemenesdm": ["kementerian esdm", "kementerian energi"],
    "kemenkop": ["kemenkop", "kemenkopukm", "kementerian koperasi"],
    "kemendes": ["kemendes", "kemendesa", "kementerian desa"],
    "kemenpora": ["kemenpora", "kementerian pemuda"],
    "kemenpppa": ["kemenpppa", "kementerian pemberdayaan perempuan"],
    "kemenparekraf": ["kemenparekraf", "kementerian pariwisata"],
    "kementerian bumn": ["kementerian bumn"],
    "bp bumn": ["bp bumn"],
    "danantara": ["danantara"],
    "setneg": ["setneg", "sekretariat negara", "kemensetneg"],
    "bkn": ["bkn", "badan kepegawaian negara"],
    "bpjs kesehatan": ["bpjs kesehatan"],
    "bpjs ketenagakerjaan": ["bpjs ketenagakerjaan", "bpjamsostek"],
    "ojk": ["ojk", "otoritas jasa keuangan"],
    "bank indonesia": ["bank indonesia"],
    "polri": ["polri", "kepolisian"],
    "tni": ["tni"],
    "bmkg": ["bmkg"],
    "bnpb": ["bnpb"],
    "bpom": ["bpom"],
    "bnn": ["bnn"],
    "baznas": ["baznas"],
    "lpdp": ["lpdp"],
    "kpu": ["kpu"],
    "bps": ["badan pusat statistik"],
    "atr/bpn": ["atr/bpn", "badan pertanahan"],
    "pln": ["pln"],
    "pertamina": ["pertamina"],
    "bri": ["bri", "bank rakyat indonesia"],
    "bni": ["bni", "bank negara indonesia"],
    "bank mandiri": ["bank mandiri"],
    "bsi": ["bsi", "bank syariah indonesia"],
    "btn": ["btn", "bank tabungan negara"],
    "bca": ["bca"],
    "telkom": ["telkom", "telkomsel"],
    "kai": ["kai", "kereta api indonesia"],
    "garuda": ["garuda indonesia"],
    "pos indonesia": ["pos indonesia"],
    "pegadaian": ["pegadaian"],
    "bulog": ["bulog"],
    "jasa marga": ["jasa marga"],
    "asdp": ["asdp"],
    "pelni": ["pelni"],
    "pgn": ["pgn", "perusahaan gas negara"],
    "angkasa pura": ["angkasa pura", "injourney"],
    "pupuk indonesia": ["pupuk indonesia"],
}
# Pemerintah daerah: "pemprov/pemkot/pemkab <nama>" diambil apa adanya sebagai satu lembaga.
PEMDA_RE = re.compile(r"\b(pemprov|pemkot|pemkab|pemerintah provinsi|pemerintah kota|pemerintah kabupaten)\s+([a-z]+(?:\s[a-z]+)?)")

# -- Program spesifik (istilah umum seperti "bansos", "bantuan", "lowongan" sengaja TIDAK dimasukkan, karena
#    istilah umum tidak boleh dianggap bertentangan dengan program spesifik) ---------------------------------------
PROGRAM = {
    "pkh": ["pkh", "program keluarga harapan"],
    "bpnt": ["bpnt", "bantuan pangan non tunai"],
    "blt dana desa": ["blt dana desa", "blt dd"],
    "kip": ["kip kuliah", "kartu indonesia pintar", "kip"],
    "pip": ["pip", "program indonesia pintar"],
    "kis": ["kis", "kartu indonesia sehat"],
    "bsu": ["bsu", "bantuan subsidi upah"],
    "prakerja": ["prakerja", "kartu prakerja"],
    "mudik gratis": ["mudik gratis"],
    "cpns": ["cpns"],
    "pppk": ["pppk"],
    "kur": ["kur", "kredit usaha rakyat"],
    "mbg": ["mbg", "makan bergizi gratis"],
    "bpum": ["bpum", "banpres"],
    "umrah gratis": ["umrah gratis", "umroh gratis"],
    "haji": ["haji"],
    "lpg 3 kg": ["lpg 3 kg", "gas melon", "elpiji 3 kg"],
    "subsidi listrik": ["subsidi listrik", "diskon listrik", "token listrik gratis"],
    "kuota internet": ["kuota internet", "kuota gratis"],
    "dana hibah": ["dana hibah"],
    "beasiswa": ["beasiswa"],
}

NOMINAL_RE = re.compile(
    r"\brp\.?\s*([\d.,]+)\s*(juta|jt|ribu|rb|miliar|m)?\b|\b([\d.,]+)\s*(juta|jt|ribu|rb|miliar)\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?62[\s\-–—]?|0)8[\d\-–—\s]{8,13}\d")
URL_RE = re.compile(r"(?:https?://)?(?:www\.)?([a-z0-9-]+(?:\.[a-z0-9-]+)+)(?:/\S*)?", re.IGNORECASE)
ORG_HINT_RE = re.compile(r"\b(kementerian|badan|dinas|pt\.?|bank|lembaga|direktorat|otoritas|pemerintah)\b")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def _find_terms(text: str, table: dict[str, list[str]]) -> set[str]:
    found = set()
    for canon, aliases in table.items():
        if any(re.search(rf"(?<![\w/]){re.escape(a)}(?![\w/])", text) for a in aliases):
            found.add(canon)
    return found


def lembaga(text: str) -> set[str]:
    t = _norm(text)
    return _find_terms(t, LEMBAGA) | {f"pemda {m.group(2)}" for m in PEMDA_RE.finditer(t)}


def program(text: str) -> set[str]:
    return _find_terms(_norm(text), PROGRAM)


def nominal(text: str) -> set[int]:
    """Nominal rupiah sebagai bilangan bulat (Rp 600.000, Rp600 ribu, 1,2 juta)."""
    out = set()
    mult = {"juta": 10**6, "jt": 10**6, "ribu": 10**3, "rb": 10**3, "miliar": 10**9, "m": 10**9}
    for m in NOMINAL_RE.finditer(_norm(text)):
        num, unit = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        if unit:  # 1,2 juta / 1.5 juta: koma atau titik sebagai desimal
            try:
                val = float(num.replace(",", ".").strip(".")) * mult[unit]
            except ValueError:
                continue
        else:     # Rp 600.000 / Rp 600,000: pemisah ribuan
            digits = re.sub(r"[.,]", "", num)
            if not digits.isdigit():
                continue
            val = int(digits)
        if val >= 1000:
            out.add(round(val))
    return out


def domains(text: str) -> set[str]:
    out = set()
    for m in URL_RE.finditer(text or ""):
        host = m.group(1).lower()
        if "." in host and not host.replace(".", "").isdigit() and not re.fullmatch(r"[\d.,]+", host):
            out.add(host.removeprefix("www."))
    return out


def phones(text: str) -> set[str]:
    out = set()
    for m in PHONE_RE.finditer(text or ""):
        d = re.sub(r"\D", "", m.group(0))
        out.add("0" + d[2:] if d.startswith("62") else d)
    return out


def compare(msg_vals: set, art_vals: set) -> str:
    if not msg_vals or not art_vals:
        return "tidak_dapat_dibandingkan"
    return "sama" if msg_vals & art_vals else "bertentangan"


def main() -> int:
    from evaluation.external_eval import build_liputan6_cases, norm_sha

    frozen = {b["kode"]: b for b in json.loads((ROOT / "testset" / "eksternal_butir.json").read_text(encoding="utf-8"))["butir"]}
    results = {b["kode"]: b for b in json.loads((ROOT / "testset" / "eksternal_hasil_per_butir.json").read_text(encoding="utf-8"))["butir"]}
    articles = {a["article_id"]: a for a in json.loads((ROOT / "data" / "articles.json").read_text(encoding="utf-8"))}
    cases = {c["kode"]: c for c in build_liputan6_cases()}
    for kode, c in cases.items():  # teks kutipan harus sama dengan yang dibekukan
        if norm_sha(c["kutipan"]) != frozen[kode]["sha256_kutipan"]:
            raise SystemExit(f"{kode}: hash kutipan tidak cocok dengan testset/eksternal_butir.json")

    rows, missed_hint = [], Counter()
    for kode, r in results.items():
        if r["keputusan_modus"] != "ditemukan":
            continue  # aturan hanya bisa menurunkan jawaban "ditemukan"
        msg = cases[kode]["kutipan"]
        art = articles[r["article_id_modus"]]
        sec = {k: art.get(k, "") for k in ("narasi", "kesimpulan")}
        head_narasi = f"{art['title']}\n{sec.get('narasi', '')}"
        all_text = f"{head_narasi}\n{sec.get('kesimpulan', '')}"
        status = {
            "lembaga": compare(lembaga(msg), lembaga(head_narasi)),
            "program": compare(program(msg), program(head_narasi)),
            "nominal": compare(nominal(msg), nominal(all_text)),
        }
        src_domains = set().union(*(domains(u) for u in art.get("claim_sources", []))) | domains(sec.get("narasi", ""))
        support = {
            "domain_sama_persis": bool(domains(msg) & src_domains),
            "nomor_sama_persis": bool(phones(msg) & phones(sec.get("narasi", ""))),
        }
        # di sisi mana entitas terbaca (hanya ada/tidak; nilainya tidak disimpan)
        found = {"lembaga": (bool(lembaga(msg)), bool(lembaga(head_narasi))),
                 "program": (bool(program(msg)), bool(program(head_narasi))),
                 "nominal": (bool(nominal(msg)), bool(nominal(all_text)))}
        conflict = [k for k, v in status.items() if v == "bertentangan"]
        # kemungkinan meleset: pesan memuat kata penanda lembaga, tetapi daftar tidak menemukan lembaga apa pun
        hint = bool(ORG_HINT_RE.search(_norm(msg))) and not lembaga(msg)
        missed_hint["lembaga"] += hint
        rows.append({"kode": kode, "hasil_v1": r["hasil"], "status": status, "pendukung": support,
                     "terbaca_pesan_artikel": found,
                     "bertentangan": conflict, "jawaban_v2": "pola_mirip" if conflict else "klaim_sama",
                     "lembaga_mungkin_meleset": hint})

    def count(hasil: str) -> tuple[int, int]:
        sub = [x for x in rows if x["hasil_v1"] == hasil]
        return sum(x["jawaban_v2"] == "pola_mirip" for x in sub), len(sub)

    summary = {
        "kecocokan_palsu_turun": count("kecocokan_palsu"),
        "benar_ikut_turun": count("benar"),
        "artikel_salah_turun": count("artikel_salah"),
        "tidak_dapat_dibandingkan_per_entitas": {
            k: sum(x["status"][k] == "tidak_dapat_dibandingkan" for x in rows) for k in ("lembaga", "program", "nominal")},
        "bertentangan_per_entitas": {k: sum(x["status"][k] == "bertentangan" for x in rows) for k in ("lembaga", "program", "nominal")},
        "terbaca_di_pesan": {k: sum(x["terbaca_pesan_artikel"][k][0] for x in rows) for k in ("lembaga", "program", "nominal")},
        "terbaca_di_artikel": {k: sum(x["terbaca_pesan_artikel"][k][1] for x in rows) for k in ("lembaga", "program", "nominal")},
        "butir_dinilai": len(rows),
        "lembaga_mungkin_meleset": missed_hint["lembaga"],
        "pendukung_domain_sama": sum(x["pendukung"]["domain_sama_persis"] for x in rows),
        "pendukung_nomor_sama": sum(x["pendukung"]["nomor_sama_persis"] for x in rows),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({"ringkasan": summary, "butir": rows}, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    for x in sorted(rows, key=lambda x: (x["hasil_v1"], x["kode"])):
        s = x["status"]
        print(f"{x['kode']:6s} {x['hasil_v1']:16s} lembaga={s['lembaga'][:5]:5s} program={s['program'][:5]:5s} "
              f"nominal={s['nominal'][:5]:5s} -> {x['jawaban_v2']:10s} domain={int(x['pendukung']['domain_sama_persis'])} "
              f"nomor={int(x['pendukung']['nomor_sama_persis'])} meleset?={int(x['lembaga_mungkin_meleset'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
