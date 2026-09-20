"""
Retrieval Versi 1: kueri -> chunk terdekat -> agregasi per artikel.

Skor sebuah artikel adalah skor TERTINGGI di antara chunk-chunknya, apa pun
seksinya. Hasil uji awal menunjukkan chunk Penjelasan sering lebih cocok
daripada Narasi, jadi retrieval tidak bergantung pada seksi tertentu.
Jawaban yang ditampilkan diambil dari chunk Kesimpulan artikel yang sama.

Tautan rujukan diambil dari metadata hasil retrieval, tidak pernah dihasilkan
oleh LLM (Aturan Wajib #3).
"""

from dataclasses import dataclass, field
from typing import Any

from chunker import decode_references

# Jumlah chunk yang diambil sebelum diagregasi. Satu artikel punya maksimal 3
# chunk, sehingga 30 chunk mencakup minimal 10 artikel berbeda.
CHUNK_FETCH = 30


@dataclass
class ArticleHit:
    article_id: str
    title: str
    url: str
    label: str
    score: float  # kemiripan kosinus chunk terbaik artikel ini
    best_section: str  # seksi asal chunk terbaik
    section_scores: dict[str, float] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)  # sudah tersaring
    date: str = ""
    narasi: str = ""  # klaim yang beredar; dipakai untuk menilai kesamaan klaim
    kesimpulan: str = ""


def aggregate_by_article(
    metadatas: list[dict], distances: list[float]
) -> list[ArticleHit]:
    """
    Gabungkan hasil per chunk menjadi per artikel (skor tertinggi per artikel).

    Fungsi murni tanpa akses database agar mudah diuji. Hasil terurut dari
    skor tertinggi. Skor = 1 - jarak kosinus.
    """
    hits: dict[str, ArticleHit] = {}
    for meta, dist in zip(metadatas, distances):
        score = 1.0 - dist
        aid = meta["article_id"]
        hit = hits.get(aid)
        if hit is None:
            hit = hits[aid] = ArticleHit(
                article_id=aid,
                title=meta["title"],
                url=meta["url"],
                label=meta["label"],
                score=score,
                best_section=meta["section"],
                references=decode_references(meta["references"]),
                date=meta.get("date", ""),
            )
        hit.section_scores[meta["section"]] = max(
            score, hit.section_scores.get(meta["section"], float("-inf"))
        )
        if score > hit.score:
            hit.score = score
            hit.best_section = meta["section"]
    return sorted(hits.values(), key=lambda h: h.score, reverse=True)


def retrieve(
    query: str, model: Any, collection: Any, top_k: int = 5
) -> list[ArticleHit]:
    """Cari `top_k` artikel paling mirip dengan kueri, lengkap dengan Kesimpulan."""
    emb = model.encode([query], normalize_embeddings=True)
    res = collection.query(
        query_embeddings=[emb[0].tolist()],
        n_results=min(CHUNK_FETCH, collection.count()),
        include=["metadatas", "distances"],
    )
    hits = aggregate_by_article(res["metadatas"][0], res["distances"][0])[:top_k]

    # Jawaban berasal dari chunk Kesimpulan artikel yang sama; Narasi diambil
    # agar klaim pengguna bisa dibandingkan dengan klaim artikel.
    ids = [f"{h.article_id}_{s}" for h in hits for s in ("narasi", "kesimpulan")]
    stored = collection.get(ids=ids, include=["documents"])
    docs = dict(zip(stored["ids"], stored["documents"]))
    for h in hits:
        h.narasi = docs.get(f"{h.article_id}_narasi", "")
        h.kesimpulan = docs.get(f"{h.article_id}_kesimpulan", "")
    return hits
