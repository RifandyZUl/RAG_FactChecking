"""
Ingestion Versi 1: chunk artikel -> embedding bge-m3 -> ChromaDB persisten.

Idempoten: id chunk adalah `{article_id}_{section}` dan penyimpanan memakai
upsert, jadi menjalankan ulang tidak menggandakan data. Chunk yang sudah
tersimpan dengan teks identik dilewati (tidak di-embed ulang); gunakan
--force untuk memaksa embedding ulang semuanya, mis. setelah mengganti
MAX_SEQ_LENGTH.

Pemakaian:
    python src/ingest.py            # ingest semua chunk yang belum ada
    python src/ingest.py --force    # embed ulang semua
    python src/ingest.py --limit 16 # uji cepat pada 16 chunk
"""

import argparse
import os
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import chromadb
from chromadb.config import Settings

from chunker import (
    MAX_SEQ_LENGTH,
    PROJECT_ROOT,
    Chunk,
    build_chunks,
    load_articles,
    make_token_counter,
    truncation_report,
)

MODEL_NAME = "BAAI/bge-m3"
# Repo BAAI/bge-m3 di branch main hanya menyediakan pytorch_model.bin, dan
# transformers >= 5 menolak memuat .bin bila torch < 2.6 (CVE-2025-32434;
# torch terpasang 2.5.1). Solusinya memakai varian safetensors dari PR
# konversi otomatis milik SFconvertbot (akun konversi resmi Hugging Face,
# PR #130), dikunci ke hash commit agar reproducible. Bobot berasal dari
# konversi .bin yang sama, tetapi PR ini belum di-merge/di-review BAAI dan
# kesamaan numeriknya dengan .bin belum diverifikasi di sini.
MODEL_REVISION = "9a0624b896d81da7492a910ffa53731274b6cf3d"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "turnbackhoax"
BATCH_SIZE = 8  # batch kecil menahan puncak RAM (mesin dev hanya ~2,5 GB bebas)


def get_collection(path: Path = CHROMA_DIR) -> Any:
    """Buka (atau buat) koleksi ChromaDB persisten dengan jarak kosinus."""
    client = chromadb.PersistentClient(
        path=str(path), settings=Settings(anonymized_telemetry=False)
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        configuration={"hnsw": {"space": "cosine"}},
    )


def load_model() -> Any:
    """Muat bge-m3 di CPU dengan batas token MAX_SEQ_LENGTH."""
    from sentence_transformers import SentenceTransformer

    # CPU eksplisit: build torch terpasang hanya CPU, dan GPU MX550 (2 GB VRAM)
    # sengaja tidak dipakai.
    model = SentenceTransformer(
        MODEL_NAME,
        device="cpu",
        revision=MODEL_REVISION,
        model_kwargs={"use_safetensors": True},
    )
    model.max_seq_length = MAX_SEQ_LENGTH
    return model


def select_chunks_to_embed(
    chunks: list[Chunk], collection: Any, force: bool
) -> list[Chunk]:
    """Pilih chunk yang belum tersimpan (atau teksnya berubah)."""
    if force:
        return list(chunks)
    stored = collection.get(ids=[c["id"] for c in chunks], include=["documents"])
    existing = dict(zip(stored["ids"], stored["documents"]))
    return [c for c in chunks if existing.get(c["id"]) != c["text"]]


def upsert_chunks(collection: Any, chunks: list[Chunk], embeddings: Any) -> None:
    """Simpan chunk beserta embedding-nya (upsert: aman dijalankan ulang)."""
    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=[list(map(float, e)) for e in embeddings],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )


def fmt_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m} mnt {s:02d} dtk"


def ingest(chunks: list[Chunk], collection: Any, force: bool = False) -> None:
    todo = select_chunks_to_embed(chunks, collection, force)
    print(f"{len(chunks)} chunk total | {len(chunks) - len(todo)} sudah tersimpan "
          f"(dilewati) | {len(todo)} akan di-embed")
    if not todo:
        return

    # Terpanjang lebih dulu: bila memori tidak cukup, gagal di awal, bukan
    # setelah puluhan menit. Konsekuensinya ETA di awal cenderung pesimistis.
    todo.sort(key=lambda c: c["metadata"]["n_tokens"], reverse=True)

    t0 = time.time()
    print(f"Memuat model {MODEL_NAME} (unduhan ~2,3 GB pada run pertama)...")
    model = load_model()
    t_load = time.time() - t0
    print(f"Model siap dalam {fmt_duration(t_load)}\n")

    t1 = time.time()
    for start in range(0, len(todo), BATCH_SIZE):
        batch = todo[start:start + BATCH_SIZE]
        embeddings = model.encode(
            [c["text"] for c in batch],
            batch_size=BATCH_SIZE,
            normalize_embeddings=True,  # dengan ruang kosinus Chroma
            show_progress_bar=False,
        )
        upsert_chunks(collection, batch, embeddings)  # tersimpan bertahap

        done = start + len(batch)
        elapsed = time.time() - t1
        eta = elapsed / done * (len(todo) - done)
        bar = "#" * (30 * done // len(todo))
        print(f"[{bar:<30}] {done:3d}/{len(todo)} ({100 * done // len(todo):3d}%) "
              f"berlalu {fmt_duration(elapsed)} | sisa ~{fmt_duration(eta)}", flush=True)

    t_embed = time.time() - t1
    print(f"\nEmbedding {len(todo)} chunk selesai dalam {fmt_duration(t_embed)} "
          f"({t_embed / len(todo):.1f} dtk/chunk); muat model {fmt_duration(t_load)}; "
          f"total {fmt_duration(t_load + t_embed)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--force", action="store_true", help="embed ulang semua chunk")
    parser.add_argument("--limit", type=int, default=None, help="batasi jumlah chunk (uji)")
    args = parser.parse_args()

    articles = load_articles()
    chunks = build_chunks(articles, make_token_counter())
    if args.limit:
        chunks = chunks[: args.limit]
    print(f"{len(articles)} artikel -> {len(chunks)} chunk")
    print(truncation_report(chunks), "\n")

    collection = get_collection()
    ingest(chunks, collection, force=args.force)

    stored_ids = set(collection.get(include=[])["ids"])
    stale = stored_ids - {c["id"] for c in build_chunks(articles, make_token_counter())}
    print(f"Isi koleksi '{COLLECTION_NAME}': {collection.count()} chunk"
          + (f" | {len(stale)} id usang (tidak ada di articles.json)" if stale else ""))


if __name__ == "__main__":
    main()
