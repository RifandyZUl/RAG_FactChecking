"""
Chunking artikel TurnBackHoax berbasis seksi (Aturan Wajib #2).

Setiap artikel dipecah menjadi satu chunk per seksi: Narasi, Penjelasan,
dan Kesimpulan. Pemotongan TIDAK berdasarkan jumlah karakter. Pencarian
semantik mencocokkan klaim pengguna dengan chunk Narasi, sedangkan jawaban
yang ditampilkan diambil dari chunk Kesimpulan pada artikel yang sama.

Metadata chunk sengaja hanya memuat `references` yang sudah tersaring.
`references_filtered`, `references_raw`, dan `claim_sources` TIDAK dibawa
karena metadata inilah yang nanti ditampilkan ke pengguna (Aturan Wajib #1).

Dijalankan langsung untuk mencetak laporan chunk yang terpotong pada
batas token model embedding.
"""

import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from paths import INDEX_ARTICLES_PATH


SECTIONS: tuple[str, ...] = ("narasi", "penjelasan", "kesimpulan")

# Batas token untuk model embedding (bge-m3 sebenarnya mendukung 8192).
# Lihat CLAUDE.md, bagian Keterbatasan, untuk alasan pembatasan ke 512.
MAX_SEQ_LENGTH = 512
TOKENIZER_NAME = "BAAI/bge-m3"

Chunk = dict[str, Any]  # {"id", "text", "metadata"}


def encode_references(references: list[str]) -> str:
    """
    Serialisasi daftar tautan ke JSON string.

    ChromaDB tidak menerima list sebagai nilai metadata. JSON dipilih
    ketimbang pemisah sederhana karena URL boleh memuat koma dan titik koma.
    """
    return json.dumps(references, ensure_ascii=False)


def decode_references(value: str) -> list[str]:
    """Kembalikan daftar tautan dari metadata hasil retrieval."""
    return json.loads(value) if value else []


def load_articles(path: Path = INDEX_ARTICLES_PATH) -> list[dict]:
    """
    Baca hasil scraping dari indeks aktif (bawaan `data/articles.json`; lihat RAG_INDEX_DIR di
    paths.py). Galat dilempar bila berkas belum ada.
    """
    if not path.exists():
        raise FileNotFoundError(f"{path} tidak ditemukan; jalankan `python -m scraping` dulu")
    return json.loads(path.read_text(encoding="utf-8"))


def make_token_counter() -> Callable[[str], int]:
    """
    Buat penghitung token memakai tokenizer bge-m3 (tanpa memuat modelnya).

    Hitungan menyertakan token khusus (<s>, </s>), sama seperti yang dihitung
    terhadap batas max_seq_length saat embedding.
    """
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)

    def count(text: str) -> int:
        return len(tokenizer(text, add_special_tokens=True)["input_ids"])

    return count


def chunk_article(article: dict, count_tokens: Callable[[str], int]) -> list[Chunk]:
    """Pecah satu artikel menjadi chunk per seksi; seksi kosong dilewati."""
    chunks: list[Chunk] = []
    for section in SECTIONS:
        text = (article.get(section) or "").strip()
        if not text:
            continue
        n_tokens = count_tokens(text)
        chunks.append({
            "id": f"{article['article_id']}_{section}",
            "text": text,
            "metadata": {
                "article_id": article["article_id"],
                "url": article["url"],
                "title": article["title"],
                "label": article["label"],
                "category": article.get("category") or "",
                "date": article.get("date") or "",
                "section": section,
                "references": encode_references(article.get("references", [])),
                "n_tokens": n_tokens,
                "truncated": n_tokens > MAX_SEQ_LENGTH,
            },
        })
    return chunks


def build_chunks(
    articles: list[dict], count_tokens: Callable[[str], int]
) -> list[Chunk]:
    """Chunk semua artikel."""
    chunks: list[Chunk] = []
    for article in articles:
        chunks.extend(chunk_article(article, count_tokens))
    return chunks


def truncation_report(chunks: list[Chunk]) -> str:
    """Ringkasan chunk yang melebihi MAX_SEQ_LENGTH, dipecah per seksi."""
    total = Counter(c["metadata"]["section"] for c in chunks)
    cut = Counter(c["metadata"]["section"] for c in chunks if c["metadata"]["truncated"])
    lines = [f"Batas token: {MAX_SEQ_LENGTH} (termasuk token khusus)"]
    for s in SECTIONS:
        toks = sorted(c["metadata"]["n_tokens"] for c in chunks
                      if c["metadata"]["section"] == s)
        if not toks:
            continue
        pct = 100 * cut[s] / total[s]
        lines.append(
            f"  {s:11s} terpotong {cut[s]:3d}/{total[s]:3d} ({pct:4.1f}%) | "
            f"token median={toks[len(toks) // 2]} p90={toks[int(len(toks) * 0.9)]} "
            f"maks={toks[-1]}"
        )
    lines.append(
        f"  TOTAL       terpotong {sum(cut.values())}/{len(chunks)} "
        f"({100 * sum(cut.values()) / max(len(chunks), 1):.1f}%)"
    )
    return "\n".join(lines)


def main() -> None:
    articles = load_articles()
    chunks = build_chunks(articles, make_token_counter())
    per_section = Counter(c["metadata"]["section"] for c in chunks)
    print(f"{len(articles)} artikel -> {len(chunks)} chunk {dict(per_section)}")
    print(truncation_report(chunks))

    # Aturan Wajib #1: metadata tidak boleh memuat sumber hoaks
    forbidden = {"claim_sources", "references_filtered", "references_raw"}
    for c in chunks:
        assert not forbidden & c["metadata"].keys(), f"{c['id']}: metadata terlarang"
    ids = [c["id"] for c in chunks]
    assert len(ids) == len(set(ids)), "id chunk tidak unik"


if __name__ == "__main__":
    main()
