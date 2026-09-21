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
# Repo BAAI/bge-m3 di main hanya punya .bin. Setiap kali memuat .bin,
# transformers menjalankan Thread non-daemon yang mengunduh varian safetensors
# dari PR konversi (2,3 GB) di latar belakang, sehingga proses tidak berhenti
# sampai unduhan selesai (use_safetensors=False tidak mencegahnya). Variabel
# ini mematikan konversi otomatis itu (transformers/modeling_utils.py).
os.environ.setdefault("DISABLE_SAFETENSORS_CONVERSION", "1")

import chromadb
from chromadb.config import Settings

from chunker import (
    MAX_SEQ_LENGTH,
    Chunk,
    build_chunks,
    load_articles,
    make_token_counter,
    truncation_report,
)
from paths import PROJECT_ROOT

MODEL_NAME = "BAAI/bge-m3"
# Model dimuat dari branch main (pytorch_model.bin resmi BAAI). transformers
# >= 5 hanya mau memuat .bin bila torch >= 2.6 (CVE-2025-32434), yang dipenuhi
# venv proyek (lihat requirements.txt). Embedding awal sempat dibuat dari
# varian safetensors PR #130 (SFconvertbot) saat torch masih 2.5.1; bobotnya
# sudah dibuktikan identik bit-per-bit dengan .bin (391/391 tensor), sehingga
# embedding yang tersimpan tetap valid.
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


def reset_collection(path: Path = CHROMA_DIR) -> Any:
    """
    Hapus koleksi lama (bila ada) lalu buat koleksi kosong: pembangunan ulang indeks dari nol.

    Ingestion inkremental hanya membandingkan TEKS chunk yang tersimpan dengan teks baru; ia tidak
    mendeteksi perubahan tokenizer, batas token, model, atau metadata pada chunk yang teksnya sama,
    dan tidak menghapus chunk usang. Setiap perubahan logika parsing atau chunking wajib memakai ini.
    """
    client = chromadb.PersistentClient(
        path=str(path), settings=Settings(anonymized_telemetry=False)
    )
    existing = [str(getattr(c, "name", c)) for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        print(f"Koleksi lama '{COLLECTION_NAME}' dihapus; indeks dibangun ulang dari nol.")
    return get_collection(path)


def load_model() -> Any:
    """Muat bge-m3 di CPU dengan batas token MAX_SEQ_LENGTH."""
    from sentence_transformers import SentenceTransformer

    # CPU eksplisit: build torch terpasang hanya CPU, dan GPU MX550 (2 GB VRAM)
    # sengaja tidak dipakai.
    model = SentenceTransformer(MODEL_NAME, device="cpu")
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
    parser.add_argument("--rebuild", action="store_true",
                        help="hapus koleksi lama lalu bangun ulang dari nol (wajib setelah logika "
                             "parsing/chunking berubah); mencakup --force")
    parser.add_argument("--limit", type=int, default=None, help="batasi jumlah chunk (uji)")
    args = parser.parse_args()

    articles = load_articles()
    chunks = build_chunks(articles, make_token_counter())
    if args.limit:
        chunks = chunks[: args.limit]
    print(f"{len(articles)} artikel -> {len(chunks)} chunk")
    print(truncation_report(chunks), "\n")

    collection = reset_collection() if args.rebuild else get_collection()
    ingest(chunks, collection, force=args.force or args.rebuild)

    stored_ids = set(collection.get(include=[])["ids"])
    stale = stored_ids - {c["id"] for c in build_chunks(articles, make_token_counter())}
    print(f"Isi koleksi '{COLLECTION_NAME}': {collection.count()} chunk"
          + (f" | {len(stale)} id usang (tidak ada di articles.json)" if stale else ""))


if __name__ == "__main__":
    main()
