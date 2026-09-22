"""
Saring KANDIDAT arsip terhadap 150 artikel basis data (alat bantu peninjauan; keputusan akhir manusia).

Yang dihitung per kandidat: (a) kemiripan judul tertinggi terhadap 150 judul, (b) tiga artikel teratas dari
retrieval (memakai teks Narasi sebagai kueri) beserta skornya, (c) penanda data pribadi, dan (d) usulan
kelas: `kemungkinan_sama` (klaimnya mungkin sama dengan artikel basis data -> pindah ke calon positif),
`tetangga` (topik dekat, calon negatif sulit), atau `jauh` (calon negatif mudah). Ini ALAT BANTU: skor
embedding menilai kemiripan topik, bukan kesamaan klaim (lihat CLAUDE.md), sehingga setiap kelas harus
ditinjau manusia. Tidak ada LLM generatif yang dipanggil.

Pemakaian (dari root proyek): PYTHONPATH=src python -m candidates.screen [--in JALUR] [--out JALUR]
"""

import argparse
import difflib
import json
import re
from pathlib import Path
from typing import Any

from paths import DATA_DIR

IN_PATH = DATA_DIR / "candidates" / "archive.jsonl"
OUT_PATH = DATA_DIR / "candidates" / "archive_screened.jsonl"
CLASS_PATH = DATA_DIR / "candidates" / "archive_screen_class.jsonl"

TITLE_SAME = 0.60  # kemiripan judul ke atas dianggap kemungkinan sama
SCORE_SAME = 0.80  # skor retrieval Narasi->chunk ke atas dianggap kemungkinan sama
SCORE_NEIGHBOR = 0.55  # di bawah ini dianggap jauh


def pii_flags(text: str) -> list[str]:
    """Penanda data pribadi yang harus dibersihkan sebelum masuk berkas (bukan pembersihan otomatis)."""
    flags = []
    if re.search(r"(?<!\d)(?:\+?62[\s\-]?|0)8[\d\-\s]{8,13}\d", text):
        flags.append("nomor_telepon")
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
        flags.append("email")
    if re.search(r"(?<!\w)@\w{3,}", text):
        flags.append("handle_akun")
    if re.search(r"https?://|www\.", text):
        flags.append("url_di_teks")
    if re.search(r"(?:akun|channel|kanal)\s+\w+\s+[“\"][^”\"]{2,40}[”\"]", text, re.I):
        flags.append("nama_akun")
    return flags


QUOTE_CHARS = "“”\""
MIN_QUOTE_LEN = 25
NARASI_WORD_RE = re.compile(r"narasi\b", re.IGNORECASE)
_LEADING_ARCHIVE_TAG_RE = re.compile(r"^\s*\[\s*arsip\s*\]\s*", re.IGNORECASE)
_LEADING_CUE_PHRASE_RE = re.compile(r"^(?:sebagai berikut|lengkapnya)\s*", re.IGNORECASE)


def _strip_leading_cue(rest: str) -> str:
    """
    Buang sisa penanda "[arsip]" dan/atau "sebagai berikut"/"lengkapnya" di awal teks setelah
    kata "narasi", lalu tanda baca (titik dua/titik) dan spasi. Dilakukan bertahap (bukan satu
    regex gabungan): pola gabungan `[^\\w]*(?:\\[arsip\\])?...` pernah gagal karena `[^\\w]*`
    yang rakus sudah memakan karakter "[" sebelum alternatif "[arsip]" sempat mencoba mencocokkan.
    """
    rest = rest.lstrip()
    rest = _LEADING_ARCHIVE_TAG_RE.sub("", rest)
    rest = _LEADING_CUE_PHRASE_RE.sub("", rest.lstrip())
    return rest.lstrip(" \t:.–—\n")
TRAILING_METRICS_RE = re.compile(r"\n\s*Hingga\s+\w+", re.IGNORECASE)  # "Hingga Senin (.../..), unggahan..."


def _split_quote_spans(text: str) -> list[str]:
    """
    Sama seperti candidates.crosssite.split_quote_spans (lihat penjelasan di sana): memasangkan
    tanda kutip berurutan dengan jendela geser, BUKAN regex kelas karakter `[".."]`, karena
    pasangan indeks tetap salah saat jumlah tanda kutip ganjil (kutipan ganda/salah ketik pada
    unggahan asli). Diduplikasi (bukan diimpor) agar ambang panjang kutipan arsip (25) tidak
    ikut berubah mengikuti ambang Liputan6 (15).
    """
    positions = [i for i, ch in enumerate(text) if ch in QUOTE_CHARS]
    spans = []
    i = 0
    while i < len(positions) - 1:
        start, end = positions[i], positions[i + 1]
        span = text[start + 1:end].strip()
        if len(span) >= MIN_QUOTE_LEN:
            spans.append(span)
            i += 2
        else:
            i += 1
    return spans


def claim_candidate(narasi: str) -> str:
    """
    Usulan teks klaim dari Narasi: dicari HANYA pada teks setelah kata "narasi" PERTAMA (isi
    pesan hoaks yang beredar), baik dikutip tanda kutip maupun tidak. Artikel TurnBackHoax memakai
    kedua pola: '...dengan narasi: "<kutipan>"' MAUPUN '...berikut narasi lengkapnya:\\n<teks tanpa
    kutip>', dengan tanda baca setelah "narasi" yang tidak seragam (titik dua, titik, atau
    langsung baris baru) -- karena itu dicari lewat KATA "narasi", bukan tanda baca sesudahnya.

    Membatasi pencarian ke SETELAH kata "narasi" (bukan seluruh teks) penting: kalimat pembuka
    sering memuat kutipan lain yang tidak berkaitan (mis. nama akun dalam tanda kutip, "Akun
    Facebook 'pureblood.id' ... mengunggah narasi ...") SEBELUM kata "narasi"; memasangkan tanda
    kutip pada seluruh teks bisa salah menangkap kutipan nama akun itu. Dipakai kemunculan
    PERTAMA (bukan terakhir): kutipan panjang kadang memuat kata "narasi" lagi di tengah isinya
    sendiri (mis. "...Dalam narasi yang beredar luas, Trump disebut...", atau kalimat penutup
    "konten dengan narasi serupa dibagikan oleh akun lain..."); memakai kemunculan terakhir pernah
    memotong ke tengah kutipan asli atau melompat ke kalimat tidak berkaitan (bug nyata pada
    30061, 31689 saat pertama diperbaiki -- lihat tests/test_screen.py).

    Bug lama: hanya menangani pola berkutip (regex kelas karakter, dengan kerentanan pasangan yang
    sama seperti candidates.crosssite -- lihat commit perbaikan ekstraktor Liputan6). Pola TANPA
    kutip (tidak jarang di arsip) jatuh ke fallback kalimat pertama, yang selalu menangkap kalimat
    pembuka ("Akun X pada [tanggal] mengunggah...") alih-alih pesan yang beredar (bug nyata pada
    32490, 35310, 35850 -- lihat tests/test_screen.py).

    Bila tak ada kata "narasi" sama sekali, fallback ke kalimat pertama seperti semula.
    """
    words = list(NARASI_WORD_RE.finditer(narasi))
    if words:
        rest = narasi[words[0].end():]
        spans = _split_quote_spans(rest)
        if spans:
            return spans[0]
        rest = _strip_leading_cue(rest)
        m = TRAILING_METRICS_RE.search(rest)
        end = m.start() if m else len(rest)
        para_break = rest.find("\n\n")
        if para_break != -1 and para_break < end:
            end = para_break
        candidate = rest[:end].strip()
        if len(candidate) >= MIN_QUOTE_LEN:
            return candidate[:600]
    first = re.split(r"(?<=[.!?])\s+", narasi.strip())[0]
    return first[:300]


def propose_class(title_sim: float, top_score: float) -> str:
    if title_sim >= TITLE_SAME or top_score >= SCORE_SAME:
        return "kemungkinan_sama"
    return "tetangga" if top_score >= SCORE_NEIGHBOR else "jauh"


def screen_one(cand: dict[str, Any], db_titles: dict[str, str], hits: list[Any]) -> dict[str, Any]:
    best_id, best_sim = max(
        ((aid, difflib.SequenceMatcher(None, cand["judul"].lower(), t.lower()).ratio()) for aid, t in db_titles.items()),
        key=lambda x: x[1],
    )
    top_score = hits[0].score if hits else 0.0
    out = dict(cand)
    out.update({
        "klaim_kandidat": claim_candidate(cand["narasi"]),
        "pii": pii_flags(cand["narasi"]),
        "tetangga_article_id": hits[0].article_id if hits else None,
    })
    # Kelas usulan dan skor disimpan di berkas TERPISAH dan tidak ditampilkan pada berkas tinjauan (bias anchoring);
    # setelah tinjauan manusia selesai, keduanya dibandingkan dan tingkat kesepakatan dilaporkan.
    out["_penyaring"] = {
        "article_id": cand["article_id"], "kelas_usulan": propose_class(best_sim, top_score),
        "judul_mirip_id": best_id, "judul_mirip_skor": round(best_sim, 3),
        "retrieval_top3": [{"id": h.article_id, "skor": round(h.score, 4)} for h in hits],
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--in", dest="inp", type=Path, default=IN_PATH)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument("--out-class", type=Path, default=CLASS_PATH, help="berkas terpisah untuk kelas usulan otomatis")
    args = ap.parse_args()

    from chunker import load_articles
    from ingest import get_collection, load_model
    from retriever import retrieve

    db_titles = {a["article_id"]: a["title"] for a in load_articles()}
    cands = [json.loads(x) for x in args.inp.read_text(encoding="utf-8").splitlines() if x.strip()]
    model, coll = load_model(), get_collection()
    rows = []
    for c in cands:
        hits = retrieve(c["narasi"], model, coll, top_k=3)
        rows.append(screen_one(c, db_titles, hits))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    classes = [r.pop("_penyaring") for r in rows]
    args.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    args.out_class.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in classes) + "\n", encoding="utf-8")
    from collections import Counter

    print(f"{len(rows)} kandidat disaring -> {args.out} (tanpa kelas usulan); kelas terpisah -> {args.out_class}")
    print("kelas usulan:", dict(Counter(c["kelas_usulan"] for c in classes)))
    print("penanda data pribadi:", dict(Counter(f for r in rows for f in r["pii"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
