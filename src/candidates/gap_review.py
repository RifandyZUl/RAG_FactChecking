"""
Siapkan berkas KONFIRMASI MANUSIA untuk mengukur celah "belum ditemukan" (docs/rancangan_v2.md bagian 11):
dari klaim yang diperiksa Liputan6 Cek Fakta, berapa yang juga ada di basis data TurnBackHoax?

Kode ini hanya menyiapkan kandidat dan tata letak. KEPUTUSAN (klaim sama / tidak ada yang cocok) diisi
pemilik proyek sendiri dengan pedoman anotasi v1.0, tanpa bantuan AI (Aturan Wajib #5). Tanpa LLM.

Aturan (ditetapkan sebelum data dilihat):
- 50 butir dipilih acak berbenih dari sampel 100 artikel Liputan6 (candidates.chain_sample), setelah
  artikel yang bukan putusan hoaks dikeluarkan (penanda vonis Liputan6 = "klarifikasi").
- Kandidat dicari dari JUDUL Liputan6 (kata vonis di awal dibuang), BUKAN dari pesannya: 5 teratas
  pencarian embedding + 3 teratas kata kunci pada judul. Artikel antrean pembaruan terjadwal (belum
  di-ingest, termasuk yang terbit setelah rentang basis data) ikut bersaing di kedua pencarian; untuk
  pencarian embedding, chunk-nya di-embed di memori saja (indeks tidak diubah).
- Berkas TIDAK menampilkan skor kemiripan, dan kandidat diurutkan menurut tanggal, bukan skor. Skor
  disimpan terpisah (kunci_kandidat.json) untuk audit sesudah konfirmasi.

Keluaran lokal (tidak di-commit; memuat teks hoaks apa adanya): data/candidates/celah_liputan6/.

Pemakaian (dari root proyek): PYTHONPATH=src python -m candidates.gap_review
"""

import csv
import difflib
import json
import random
import re
from datetime import date
from pathlib import Path
from typing import Any

from paths import ARTICLES_PATH, DATA_DIR

SEED = 20261004  # dicatat di docs/rancangan_v2.md bagian 11 sebelum berkas dibuat
SAMPLE_SIZE = 50
EMB_TOP, LEX_TOP = 5, 3
RANGE_END = date(2026, 9, 27)
RANGE_TAIL_DAYS = 14  # butir yang terbit pada dua minggu terakhir rentang ditandai
SAMPLE_PATH = DATA_DIR / "candidates" / "pesan_berantai" / "sampel_liputan6.jsonl"
L6_CACHE = DATA_DIR / "candidates_cache" / "liputan6"
OUT_DIR = DATA_DIR / "candidates" / "celah_liputan6"
QUEUE_GLOBS = ("forward_*.json", "retry_*.json", "batch_*.json")

_VERDICT = re.compile(r"^(tidak benar|hoaks|hoax|klarifikasi|benar|salah|keliru|menyesatkan|disinformasi)\b[\s,:-]*", re.IGNORECASE)
_STOP = frozenset(["yang", "dan", "di", "ke", "dari", "untuk", "pada", "ini", "itu", "dengan", "soal", "atau", "akan", "ada", "tidak", "benar", "hoaks", "cek", "fakta", "link", "tautan", "video", "foto", "artikel", "pendaftaran", "program", "bantuan", "resmi", "baru", "tahun", "periode", "via", "melalui", "oleh", "sebagai", "dalam", "jadi", "bagi", "para", "tentang", "klaim"])
DECISION_HELP = "isi di baris PERTAMA tiap butir: id artikel TurnBackHoax yang klaimnya SAMA | TIDAK ADA | BUKAN PUTUSAN HOAKS"
COLUMNS = ["butir", "L6_tanggal", "ujung_rentang", "L6_judul", "L6_kutipan_pesan", "KEPUTUSAN", "catatan",
           "kandidat", "TBH_id", "TBH_tanggal", "TBH_label", "TBH_asal", "TBH_judul", "TBH_kesimpulan"]


def clean_title(title: str) -> tuple[str, str]:
    """(judul tanpa "Cek Fakta:" dan kata vonis, kata vonis di awal judul atau "")."""
    t = re.sub(r"^cek fakta:\s*", "", title.strip(), flags=re.IGNORECASE)
    m = _VERDICT.match(t)
    return (t[m.end():].strip() if m else t), (m.group(1).lower() if m else "")


_FALSE_CLAIM = re.compile(r"tidak benar|\bhoaks\b|\bhoax\b|\bkeliru\b|\bsalah\b", re.IGNORECASE)


def banner_label(conclusion: str) -> str:
    """Label banner di halaman Kesimpulan Liputan6: "salah" | "hoax" | "klarifikasi" | "" (tidak ada)."""
    m = re.search(r"banner\s+(?:cek\s+fakta\s*[:-]\s*)?([a-z]+)", conclusion, re.IGNORECASE)
    return m.group(1).lower() if m else ""


def is_non_hoax_verdict(title: str, conclusion: str) -> bool:
    """
    Bukan putusan hoaks: judul berkata vonis "klarifikasi", ATAU banner berlabel "klarifikasi" sementara
    judul tidak memuat kata vonis salah/hoaks dan Kesimpulan tidak menyatakan klaimnya keliru. Artikel yang
    penandanya bertentangan (banner "klarifikasi" tetapi judul dan Kesimpulan menyatakan "tidak benar")
    TIDAK dikeluarkan otomatis; pemilik proyek memutuskannya lewat pilihan "BUKAN PUTUSAN HOAKS" di berkas.
    """
    verdict = clean_title(title)[1]
    if verdict == "klarifikasi":
        return True
    body = re.sub(r"banner[^()]*\(", " ", conclusion, flags=re.IGNORECASE)  # label banner bukan bagian pernyataan Kesimpulan
    return banner_label(conclusion) == "klarifikasi" and verdict == "" and _FALSE_CLAIM.search(body) is None


def content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP and len(w) > 2}


def lexical_top(query: str, titles: dict[str, str], k: int = LEX_TOP) -> list[tuple[str, float, float]]:
    """k judul teratas menurut tumpang tindih kata isi (Jaccard), seri diputus kemiripan karakter."""
    qw = content_words(query)
    scored = []
    for aid, title in titles.items():
        tw = content_words(title)
        jac = len(qw & tw) / len(qw | tw) if qw | tw else 0.0
        scored.append((aid, round(jac, 4), round(difflib.SequenceMatcher(None, query.lower(), title.lower()).ratio(), 4)))
    return sorted(scored, key=lambda x: (-x[1], -x[2], x[0]))[:k]


def draw_sample(ids: list[str], seed: int = SEED, n: int = SAMPLE_SIZE) -> list[str]:
    """n id acak berbenih; masukan diurutkan dulu agar hasil tidak bergantung pada urutan berkas."""
    pool = sorted(ids)
    return random.Random(seed).sample(pool, min(n, len(pool)))


def in_range_tail(published: str) -> bool:
    d = date.fromisoformat(published)
    return 0 <= (RANGE_END - d).days < RANGE_TAIL_DAYS


def tbh_date_key(ddmmyyyy: str) -> tuple[int, int, int]:
    d, m, y = (int(x) for x in ddmmyyyy.split("/"))
    return y, m, d


def build_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Baris berkas konfirmasi: satu baris per kandidat; data butir dan kolom KEPUTUSAN hanya di baris
    pertama. Kandidat diurutkan dari tanggal terbaru (BUKAN menurut skor); tidak ada kolom skor.
    """
    rows = []
    for n, item in enumerate(items, 1):
        cands = sorted(item["kandidat"], key=lambda c: (tbh_date_key(c["tanggal"]), c["id"]), reverse=True)
        for i, c in enumerate(cands, 1):
            first = i == 1
            rows.append({
                "butir": n,
                "L6_tanggal": item["tanggal"] if first else "", "ujung_rentang": ("YA" if item["ujung_rentang"] else "") if first else "",
                "L6_judul": item["judul"] if first else "", "L6_kutipan_pesan": item["pesan"] if first else "",
                "KEPUTUSAN": "", "catatan": "",
                "kandidat": i, "TBH_id": c["id"], "TBH_tanggal": c["tanggal"], "TBH_label": c["label"],
                "TBH_asal": c["asal"], "TBH_judul": c["judul"], "TBH_kesimpulan": c["kesimpulan"],
            })
    return rows


def load_queue(merged_ids: set[str]) -> list[dict]:
    """Artikel yang sudah diambil pembaruan terjadwal tetapi belum digabung ke articles.json."""
    queue: dict[str, dict] = {}
    for pattern in QUEUE_GLOBS:
        for f in sorted((DATA_DIR / "expansion").glob(pattern)):
            if f.name.endswith("_report.json"):
                continue
            for a in json.loads(f.read_text(encoding="utf-8")):
                if a["article_id"] not in merged_ids:
                    queue.setdefault(a["article_id"], a)
    return list(queue.values())


def conclusion_text(article_id: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup((L6_CACHE / f"{article_id}.html").read_text(encoding="utf-8"), "html.parser")
    for page in soup.select("div.article-content-body__item-page"):
        text = page.get_text(" ", strip=True)
        if text.lower().startswith("kesimpulan"):
            return text
    return ""


def main() -> int:
    import numpy as np

    from ingest import get_collection, load_model
    from retriever import retrieve

    sample = [json.loads(ln) for ln in SAMPLE_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    excluded = [r for r in sample if is_non_hoax_verdict(r["judul"], conclusion_text(r["id"]))]
    valid = {r["id"]: r for r in sample if r not in excluded}
    chosen = draw_sample(list(valid))

    db = json.loads(Path(ARTICLES_PATH).read_text(encoding="utf-8"))
    queue = load_queue({a["article_id"] for a in db})
    by_id = {a["article_id"]: {**a, "asal": "indeks"} for a in db}
    by_id.update({a["article_id"]: {**a, "asal": "antrean (belum di-ingest)"} for a in queue})
    titles = {aid: a["title"] for aid, a in by_id.items()}

    model, coll = load_model(), get_collection()
    # chunk antrean di-embed di memori saja agar bersaing setara di pencarian embedding (indeks tidak diubah)
    q_chunks = [(a["article_id"], a[s]) for a in queue for s in ("narasi", "penjelasan", "kesimpulan") if a.get(s)]
    q_vecs = np.asarray(model.encode([t for _, t in q_chunks], normalize_embeddings=True, batch_size=8)) if q_chunks else None

    items, key = [], {}
    for aid in chosen:
        r = valid[aid]
        query, verdict = clean_title(r["judul"])
        hits = [(h.article_id, float(h.score)) for h in retrieve(query, model, coll, top_k=EMB_TOP)]
        if q_vecs is not None:
            qv = np.asarray(model.encode([query], normalize_embeddings=True))[0]
            best: dict[str, float] = {}
            for (qid, _), score in zip(q_chunks, q_vecs @ qv):
                best[qid] = max(best.get(qid, -1.0), float(score))
            hits = sorted(hits + list(best.items()), key=lambda x: -x[1])[:EMB_TOP]
        lex = lexical_top(query, titles)
        cand_ids = list(dict.fromkeys([i for i, _ in hits] + [i for i, _, _ in lex]))
        items.append({"id": aid, "judul": r["judul"], "tanggal": r["tanggal"], "pesan": r["pesan"],
                      "ujung_rentang": in_range_tail(r["tanggal"]),
                      "kandidat": [{"id": c, "tanggal": by_id[c]["date"], "label": by_id[c]["label"], "asal": by_id[c]["asal"],
                                    "judul": by_id[c]["title"], "kesimpulan": by_id[c]["kesimpulan"]} for c in cand_ids]})
        key[aid] = {"kueri": query, "vonis_judul": verdict, "embedding_top": [(i, round(s, 4)) for i, s in hits], "kata_kunci_top": lex}

    rows = build_rows(items)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "konfirmasi_50.csv"
    if out.exists():
        raise SystemExit(f"{out} sudah ada: tidak ditimpa (bisa berisi keputusan yang sudah diisi)")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:  # BOM agar Excel membaca UTF-8
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    (OUT_DIR / "kunci_kandidat.json").write_text(json.dumps({
        "benih": SEED, "dikeluarkan_bukan_putusan_hoaks": [{"id": r["id"], "judul": r["judul"]} for r in excluded],
        "urutan_butir": chosen, "skor": key}, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT_DIR / "BACA_SAYA.txt").write_text(
        "konfirmasi_50.csv -- disiapkan kode (candidates.gap_review); KEPUTUSAN diisi pemilik proyek sendiri, tanpa bantuan AI.\n"
        f"Kolom KEPUTUSAN: {DECISION_HELP}.\n"
        "Kesamaan klaim menurut testset/ANNOTATION_GUIDE.md v1.0. Kandidat diurutkan menurut tanggal (terbaru dulu), bukan menurut "
        "kemiripan; tidak ada skor.\nTBH_asal 'antrean' = artikel yang sudah diambil pembaruan terjadwal tetapi belum di-ingest.\n"
        "ujung_rentang YA = artikel Liputan6 terbit 14-27 September 2026.\nkunci_kandidat.json memuat skor: JANGAN dibuka sebelum "
        "konfirmasi selesai.\n", encoding="utf-8")
    n_cand = [len(i["kandidat"]) for i in items]
    print(json.dumps({
        "sampel_awal": len(sample), "dikeluarkan": [r["judul"] for r in excluded], "butir": len(items), "baris_kandidat": len(rows),
        "kandidat_per_butir_min_median_maks": [min(n_cand), sorted(n_cand)[len(n_cand) // 2], max(n_cand)],
        "butir_ujung_rentang": sum(i["ujung_rentang"] for i in items), "artikel_antrean": len(queue),
        "butir_dengan_kandidat_dari_antrean": sum(any(c["asal"].startswith("antrean") for c in i["kandidat"]) for i in items),
        "butir_tanpa_kutipan_pesan": sum(not i["pesan"] for i in items), "berkas": str(out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
