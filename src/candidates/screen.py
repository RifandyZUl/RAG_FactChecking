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


def claim_candidate(narasi: str) -> str:
    """
    Usulan teks klaim dari Narasi: blok kutipan pertama yang cukup panjang (isi pesan hoaks yang beredar);
    bila tak ada, kalimat pertama. Hanya usulan untuk peninjauan.
    """
    quoted = re.findall(r"[“\"]([^”\"]{25,600})[”\"]", narasi)
    if quoted:
        return quoted[0].strip()
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
