"""
Verifikasi retrieval Versi 1 terhadap ChromaDB hasil ingest.py.

Kueri sengaja berbahasa sehari-hari dan berbeda kata dari judul artikel.
Hasil diagregasi per article_id (skor tertinggi per artikel), lihat
retriever.py. Untuk tiap artikel dicetak skor, seksi asal chunk terbaik,
article_id, dan judul.

Prasyarat: python src/ingest.py sudah dijalankan.
"""

import sys
from collections import Counter

from chunker import load_articles
from ingest import get_collection, load_model
from retriever import retrieve

TOP_K = 5
# Artikel yang diharapkan wajib muncul dalam TOP_PASS artikel teratas
TOP_PASS = 3

# (kueri, article_id yang diharapkan)
QUERIES: list[tuple[str, str]] = [
    ("katanya ojol nggak boleh isi pertalite lagi ya?", "36730"),
    ("ada link pendaftaran bantuan buat orang tua, itu beneran?", "36737"),
    ("malaysia marah ke indonesia soal asap", "36729"),
    ("polisi mau razia motor sampai ke rumah-rumah warga?", "36738"),
    ("daftar cek kesehatan gratis lewat link yang beredar, asli gak sih?", "36731"),
]


# Kueri negatif: klaim yang TIDAK ada di basis data. Kata kunci pada kolom ke-3
# harus nol kemunculannya di judul/Narasi/Penjelasan/Kesimpulan seluruh artikel
# (diperiksa otomatis, jadi uji gagal bila basis data kelak memuat klaim itu).
# Catatan: pemeriksaan berbasis kata kunci, bukan bukti ketiadaan makna.
# (kueri, jenis, kata kunci yang harus absen)
NEGATIVE_QUERIES: list[tuple[str, str, list[str]]] = [
    ("katanya gas melon 3 kg mau dihapus bulan depan, harus beli yang nonsubsidi?",
     "sulit: ranah kebijakan/subsidi seperti artikel Pertalite dan bansos",
     ["elpiji", "gas melon", "3 kg"]),
    ("vaksin flu bikin laki-laki jadi mandul, benar nggak sih?",
     "sulit: tetangga dekat 36214 (vaksin HPV bikin impoten)",
     ["vaksin flu", "influenza", "infertil"]),
    ("katanya BMKG bilang bakal ada gempa megathrust besar di Jawa minggu ini",
     "sedang: ranah gempa ada, tetapi bukan klaim prediksi",
     ["megathrust"]),
    ("minum rebusan daun sirsak tiap pagi katanya bisa sembuhin diabetes",
     "mudah: ranah kesehatan tetapi klaimnya tidak ada",
     ["sirsak", "diabetes"]),
    ("NASA ngaku kalau bumi ternyata datar ya?",
     "mudah: tidak berhubungan dengan isi basis data",
     ["bumi datar", "bumi itu datar"]),
]


def check_negative_absence(articles: list[dict]) -> list[str]:
    """Kembalikan daftar pelanggaran: kata kunci 'absen' yang ternyata ada."""
    violations: list[str] = []
    for query, _, keywords in NEGATIVE_QUERIES:
        for kw in keywords:
            for a in articles:
                blob = " ".join([a["title"], a["narasi"], a["penjelasan"], a["kesimpulan"]])
                if kw.lower() in blob.lower():
                    violations.append(f"{query!r}: kata kunci {kw!r} ada di {a['article_id']}")
    return violations


def run_negative(model, collection, positive_scores: list[float]) -> float:
    """Cetak skor tertinggi tiap kueri negatif; kembalikan skor negatif maksimum."""
    print("\n\n=== Kueri negatif (klaim TIDAK ada di basis data) ===")
    neg_top: list[float] = []
    for query, kind, _ in NEGATIVE_QUERIES:
        hits = retrieve(query, model, collection, top_k=3)
        neg_top.append(hits[0].score)
        print(f"\nKueri : {query}\nJenis : {kind}")
        for rank, h in enumerate(hits, 1):
            print(f"  {rank}. skor={h.score:.4f}  {h.best_section:<10s} {h.article_id}  "
                  f"{h.title[:60]}")

    lo_pos, hi_neg = min(positive_scores), max(neg_top)
    print("\n--- Perbandingan skor artikel teratas ---")
    print(f"Negatif : {', '.join(f'{s:.4f}' for s in neg_top)}  (maks {hi_neg:.4f})")
    print(f"Positif : {', '.join(f'{s:.4f}' for s in sorted(positive_scores))}  "
          f"(min {lo_pos:.4f})")
    if lo_pos > hi_neg:
        print(f"Ada celah: positif terendah {lo_pos:.4f} > negatif tertinggi {hi_neg:.4f} "
              f"(selisih {lo_pos - hi_neg:.4f}) pada sampel ini.")
    else:
        print(f"TIDAK ada celah: negatif tertinggi {hi_neg:.4f} >= positif terendah "
              f"{lo_pos:.4f} (tumpang tindih {hi_neg - lo_pos:.4f}).")
    print(f"Sampel: {len(positive_scores)} positif, {len(neg_top)} negatif; hanya indikasi.")
    return hi_neg


def main() -> int:
    collection = get_collection()
    if collection.count() == 0:
        print("Koleksi kosong; jalankan python src/ingest.py dulu.")
        return 1

    articles = load_articles()
    violations = check_negative_absence(articles)
    if violations:
        print("Kueri negatif tidak lagi negatif:\n  " + "\n  ".join(violations))
        return 1

    claim_sources = {a["article_id"]: set(a["claim_sources"]) for a in articles}
    model = load_model()

    top1_sections: Counter[str] = Counter()
    failures: list[str] = []
    positive_scores: list[float] = []

    for query, expected in QUERIES:
        hits = retrieve(query, model, collection, top_k=TOP_K)
        print(f"\nKueri   : {query}")
        print(f"Harapan : {expected}")
        found_rank = None
        for rank, h in enumerate(hits, 1):
            mark = " <== diharapkan" if h.article_id == expected else ""
            secs = " ".join(f"{s[:3]}={v:.3f}" for s, v in
                            sorted(h.section_scores.items(), key=lambda x: -x[1]))
            print(f"  {rank}. skor={h.score:.4f}  {h.best_section:<10s} {h.article_id}  "
                  f"{h.title[:50]}  [{secs}]{mark}")
            if h.article_id == expected and found_rank is None:
                found_rank = rank
        top1_sections[hits[0].best_section] += 1
        if found_rank is not None:
            positive_scores.append(next(h.score for h in hits if h.article_id == expected))

        if found_rank is None or found_rank > TOP_PASS:
            failures.append(f"{query!r}: {expected} peringkat {found_rank} (batas {TOP_PASS})")

        # Peragaan desain: Kesimpulan artikel yang sama + rujukan dari metadata
        top = hits[0]
        print(f"  -> Kesimpulan {top.article_id}: {top.kesimpulan[:110].replace(chr(10), ' ')}...")
        print(f"  -> Rujukan (metadata): {top.references}")
        # Aturan Wajib #1: rujukan yang ditampilkan tidak boleh sumber hoaks
        leaked = [r for r in top.references if r in claim_sources.get(top.article_id, set())]
        assert not leaked, f"sumber hoaks bocor ke references: {leaked}"

    n = len(QUERIES)
    print("\n=== Ringkasan ===")
    print(f"Kueri: {n} | artikel diharapkan dalam top-{TOP_PASS}: {n - len(failures)}/{n}")
    print(f"Seksi chunk terbaik pada artikel peringkat 1: {dict(top1_sections)}")
    print(f"Skor artikel benar: min={min(positive_scores):.4f} maks={max(positive_scores):.4f}")
    print(f"Catatan: sampel hanya {n} kueri, cukup untuk sanity check, bukan evaluasi statistik.")
    run_negative(model, collection, positive_scores)
    if failures:
        print("\nGAGAL:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nSemua kueri menemukan artikel yang diharapkan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
