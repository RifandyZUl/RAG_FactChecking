"""
Audit jejak identik pada 99 butir celah "belum ditemukan" (docs/rancangan_evaluasi_eksternal.md bagian 7.1).

Untuk setiap butir dan setiap kandidat di daftarnya, dicari kecocokan PERSIS antara kutipan pesan Liputan6 dan
artikel TurnBackHoax -- tanpa LLM dan tanpa embedding:

  (a) domain tautan hoaks yang sama: host tautan di kutipan vs host di `claim_sources` + tautan di Narasi
      kandidat. Tautan berdomain daftar-blokir (media sosial, arsip, hosting gambar, pemendek URL;
      `links.blocked_reason`), sumber tepercaya (`links.is_trusted_source`: pemerintah, media, cek fakta), dan
      domain kedua situs cek fakta sendiri tidak dihitung: domain itu dipakai bersama banyak hoaks berbeda.
  (b) rangkaian kata identik: minimal NGRAM kata berurutan sama setelah normalisasi (NFKC, huruf kecil, tautan
      dibuang, tanda baca menjadi pemisah).

Parameter ditetapkan dan di-commit SEBELUM audit dijalankan. Hasil ini tidak pernah mengubah label (Aturan Wajib
#5): butir berlabel TIDAK ADA yang punya jejak hanya diserahkan untuk ditinjau ulang secara buta oleh pemilik
proyek. Karena itu ringkasan yang dicetak hanya memuat jumlah dan nomor butir; sinyal per butir hanya ada di
berkas keluaran lokal, yang TIDAK boleh dibuka pemilik proyek sebelum tinjauan buta selesai.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m labeling.sessions.trace_audit
"""

import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from labeling.gap.gap_review import OUT_DIR, SAMPLE_PATH, load_queue
from paths import ARTICLES_PATH
from scraping.links import blocked_reason, is_trusted_source

NGRAM = 8  # panjang minimum rangkaian kata identik (ditetapkan di muka)
OWN_SITES = ("turnbackhoax.id", "liputan6.com")  # tautan ke situs cek fakta sendiri bukan jejak hoaks
URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"'\])]+", re.IGNORECASE)  # hanya tautan berskema atau www.
WORD_RE = re.compile(r"[^\W_]+")
OUT_PATH = OUT_DIR / "audit_jejak_identik.json"  # memuat sinyal per butir: JANGAN dibuka sebelum tinjauan buta
ROUND1_CSV = OUT_DIR / "konfirmasi_50.csv"
ROUND1_RESULT = OUT_DIR / "hasil_konfirmasi.json"
ROUND2_TEMPLATE = OUT_DIR / "sidik_jari_templat_49.json"
ROUND2_RESULT = OUT_DIR / "hasil_konfirmasi_49.json"


def words(text: str) -> list[str]:
    """Kata setelah normalisasi: NFKC (huruf hias Unicode menjadi huruf biasa), tautan dibuang, huruf kecil."""
    return WORD_RE.findall(URL_RE.sub(" ", unicodedata.normalize("NFKC", text or "")).lower())


def ngrams(tokens: list[str], n: int = NGRAM) -> set[tuple[str, ...]]:
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def hoax_hosts(urls: list[str]) -> set[str]:
    """Host tautan yang bisa menjadi jejak hoaks (tanpa www.); domain bersama banyak hoaks tidak dihitung."""
    out = set()
    for url in urls:
        url = url.rstrip(".,;:!?")
        if not url.lower().startswith("http"):
            url = "http://" + url
        if blocked_reason(url) is not None or is_trusted_source(url):
            continue
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        if host and not any(host == s or host.endswith("." + s) for s in OWN_SITES):
            out.add(host)
    return out


def traces(message: str, article: dict[str, Any]) -> dict[str, Any]:
    """Jejak identik antara satu kutipan dan satu artikel kandidat."""
    narasi = article.get("narasi") or ""
    domains = hoax_hosts(URL_RE.findall(message)) & hoax_hosts([*(article.get("claim_sources") or []), *URL_RE.findall(narasi)])
    shared = ngrams(words(message)) & ngrams(words(narasi))
    return {"domain": sorted(domains), "rangkaian_kata": len(shared), "ada": bool(domains or shared)}


def load_items() -> list[dict[str, Any]]:
    """99 butir: putaran, nomor, id Liputan6, kutipan, daftar kandidat, dan label pemilik proyek."""
    sample = {json.loads(ln)["id"]: json.loads(ln) for ln in SAMPLE_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()}
    with ROUND1_CSV.open(encoding="utf-8-sig", newline="") as f:
        r1_cands: dict[str, list[str]] = {}
        for row in csv.DictReader(f):
            r1_cands.setdefault(row["butir"], []).append(row["TBH_id"])
    r2_cands = {str(b["butir"]): [c["id"] for c in b["kandidat"]]
                for b in json.loads(ROUND2_TEMPLATE.read_text(encoding="utf-8"))["blok"]}
    items = []
    for rnd, result_path, cands in ((1, ROUND1_RESULT, r1_cands), (2, ROUND2_RESULT, r2_cands)):
        res = json.loads(result_path.read_text(encoding="utf-8"))
        for d in res["keputusan"]:
            n = str(d["butir"])
            items.append({"putaran": rnd, "butir": int(n), "l6_id": res["l6_id"][n], "kutipan": sample[res["l6_id"][n]]["pesan"] or "",
                          "jenis": d["jenis"], "keputusan": d["keputusan"], "kandidat": cands[n]})
    return items


def audit(items: list[dict[str, Any]], articles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for it in items:
        per_cand = {c: traces(it["kutipan"], articles[c]) for c in it["kandidat"]}
        flagged = sorted(c for c, t in per_cand.items() if t["ada"])
        chosen = it["keputusan"] if it["jenis"] == "sama" else None
        status = ("tanpa_jejak" if not flagged else "jejak_pada_butir_tidak_ada" if it["jenis"] == "tidak_ada"
                  else "jejak_hanya_pada_pilihan" if flagged == [chosen] else "jejak_pada_pilihan_dan_lainnya" if chosen in flagged
                  else "jejak_hanya_pada_kandidat_lain")
        rows.append({"putaran": it["putaran"], "butir": it["butir"], "jenis": it["jenis"], "status": status,
                     "kandidat_berjejak": flagged, "sinyal": {c: per_cand[c] for c in flagged}})
    pos_pairs = [(r, c) for r in rows if r["jenis"] == "sama" for c in r["kandidat_berjejak"]]
    return {
        "parameter": {"ngram": NGRAM, "situs_sendiri_dikecualikan": OWN_SITES,
                      "tautan": "hanya berskema http(s) atau www.; daftar-blokir dan sumber tepercaya tidak dihitung"},
        "butir": len(rows),
        "butir_terdeteksi": sum(r["status"] != "tanpa_jejak" for r in rows),
        "status_per_label": {f"{j}: {s}": c for (j, s), c in sorted(Counter((r["jenis"], r["status"]) for r in rows).items())},
        # presisi diukur hanya di tempat label diketahui: pada butir cocok, apakah kandidat berjejak = pilihan
        "presisi_pada_butir_cocok": {"pasangan_berjejak": len(pos_pairs),
                                     "pasangan_berjejak_adalah_pilihan": sum(c == next(i["keputusan"] for i in items
                                                                                       if (i["putaran"], i["butir"]) == (r["putaran"], r["butir"]))
                                                                             for r, c in pos_pairs)},
        "tidak_ada_berjejak_untuk_ditinjau_buta": [f"P{r['putaran']}-{r['butir']}" for r in rows if r["status"] == "jejak_pada_butir_tidak_ada"],
        "rinci": rows,
    }


def main() -> int:
    db = json.loads(Path(ARTICLES_PATH).read_text(encoding="utf-8"))
    articles = {a["article_id"]: a for a in db}
    for a in load_queue(set(articles)):
        articles.setdefault(a["article_id"], a)
    report = audit(load_items(), articles)
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    # ringkasan tanpa sinyal per butir (tinjauan ulang harus buta)
    print(json.dumps({k: v for k, v in report.items() if k != "rinci"}, ensure_ascii=False, indent=2))
    print(f"Rincian per butir (memuat sinyal; jangan dibuka sebelum tinjauan buta): {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
