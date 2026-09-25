"""
Verifikasi kesegaran indeks vektor terhadap articles.json (tanpa LLM, tanpa jaringan).

Indeks basi tidak menimbulkan galat: retriever tetap mengembalikan hasil, hanya dari teks/embedding
lama. Pemeriksaan: (1) himpunan id chunk sama, (2) teks tiap chunk di indeks identik dengan teks hasil
chunking articles.json saat ini (yang juga yang dibaca retriever untuk Narasi/Kesimpulan), (3) metadata
sama, dan (4) opsional: sampel chunk di-embed ulang dan dibandingkan dengan vektor tersimpan.

Sidik jari isi (`--fingerprint`): hash atas ISI indeks (id, teks, metadata, dan byte embedding
float32), bukan atas berkas -- ChromaDB menulis ulang berkasnya setiap kali koleksi dibuka, jadi
hash berkas tidak bermakna. `--expect-v1-archive` membandingkan sidik jari dengan yang tercatat
untuk arsip Versi 1 di testset/v1.meta.json.

Indeks yang diperiksa mengikuti RAG_INDEX_DIR (bawaan data/; lihat paths.py), mis.:
  $env:RAG_INDEX_DIR = "archive/v1"; python -m evaluation.index_check --expect-v1-archive

Pemakaian (dari root proyek): PYTHONPATH=src python -m evaluation.index_check [--embed-sample N]
    [--fingerprint] [--expect-v1-archive]
Kode keluar: 0 = segar (dan sidik jari cocok bila diminta), 1 = basi atau sidik jari beda.
"""

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from typing import Any

METADATA_KEYS = ("article_id", "url", "title", "label", "category", "date", "section", "references",
                 "n_tokens", "truncated")


def compare_index(chunks: list[dict], stored_ids: list[str], stored_docs: list[str],
                  stored_metas: list[dict]) -> list[str]:
    """Daftar masalah kesegaran (kosong bila indeks sama persis dengan hasil chunking saat ini)."""
    expected = {c["id"]: c for c in chunks}
    stored = {i: (d, m) for i, d, m in zip(stored_ids, stored_docs, stored_metas)}
    problems: list[str] = []
    missing, extra = sorted(set(expected) - set(stored)), sorted(set(stored) - set(expected))
    if missing:
        problems.append(f"{len(missing)} chunk belum ada di indeks (mis. {missing[:3]})")
    if extra:
        problems.append(f"{len(extra)} chunk usang di indeks (mis. {extra[:3]})")
    for cid in sorted(set(expected) & set(stored)):
        doc, meta = stored[cid]
        want = expected[cid]
        if doc != want["text"]:
            problems.append(f"{cid}: teks beda (indeks {len(doc)} kar vs articles.json {len(want['text'])} kar)")
        for key in METADATA_KEYS:
            if meta.get(key) != want["metadata"].get(key):
                problems.append(f"{cid}: metadata '{key}' beda ({meta.get(key)!r} vs {want['metadata'].get(key)!r})")
    return problems


V1_ARCHIVE_META_KEY = "arsip_indeks_v1_2026-09-25"
FINGERPRINT_KEYS = ("jumlah_artikel", "jumlah_chunk", "sha256_daftar_artikel", "sha256_articles_json_isi",
                    "sha256_teks_metadata", "sha256_embedding_float32")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def articles_content_hash(articles: list[dict]) -> str:
    """Hash isi articles.json yang dinormalisasi (urutan kunci, tanpa spasi), bukan hash berkas."""
    return _sha(json.dumps(articles, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def content_fingerprint(ids: Sequence[str], docs: Sequence[str], metas: Sequence[dict],
                        embeddings: Sequence[Any]) -> dict[str, Any]:
    """
    Sidik jari ISI indeks, tidak bergantung urutan penyimpanan maupun byte berkas ChromaDB.

    `sha256_teks_metadata`: id + teks + metadata (JSON urut kunci) per chunk, urut id -- tahan
    terhadap pembangunan ulang dari articles.json yang sama. `sha256_embedding_float32`: id + byte
    float32 little-endian vektor tersimpan -- cocok untuk SALINAN; setelah pembangunan ulang bisa
    berbeda di digit presisi walau kosinusnya 1,000000 (verifikasi lalu lewat index_check + ablasi).
    """
    import numpy as np

    order = sorted(range(len(ids)), key=lambda i: ids[i])
    h_text, h_emb = hashlib.sha256(), hashlib.sha256()
    for i in order:
        meta = json.dumps(metas[i], sort_keys=True, ensure_ascii=False)
        h_text.update(f"{ids[i]}\x1f{docs[i]}\x1f{meta}\x1e".encode())
        h_emb.update(f"{ids[i]}\x1f".encode())
        h_emb.update(np.asarray(embeddings[i], dtype="<f4").tobytes())
    article_ids = sorted({str(m["article_id"]) for m in metas})
    return {
        "jumlah_artikel": len(article_ids),
        "jumlah_chunk": len(ids),
        "sha256_daftar_artikel": _sha("\n".join(article_ids).encode("utf-8")),
        "sha256_teks_metadata": h_text.hexdigest(),
        "sha256_embedding_float32": h_emb.hexdigest(),
    }


def compare_fingerprints(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Daftar selisih sidik jari (kosong bila sama pada semua kunci FINGERPRINT_KEYS)."""
    problems = []
    for key in FINGERPRINT_KEYS:
        if actual.get(key) != expected.get(key):
            note = (" (mungkin arsip dibangun ulang dari articles.json: embedding bisa beda di digit "
                    "presisi; periksa kosinus sampel dan ulangi ablasi)" if key == "sha256_embedding_float32" else "")
            problems.append(f"sidik jari '{key}' beda: {actual.get(key)} vs tercatat {expected.get(key)}{note}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--embed-sample", type=int, default=8,
                    help="jumlah chunk yang di-embed ulang untuk dibandingkan dengan vektor tersimpan (0 = lewati)")
    ap.add_argument("--fingerprint", action="store_true", help="cetak sidik jari isi indeks (JSON)")
    ap.add_argument("--expect-v1-archive", action="store_true",
                    help="bandingkan sidik jari dengan arsip Versi 1 yang tercatat di testset/v1.meta.json")
    args = ap.parse_args()

    from chunker import build_chunks, load_articles, make_token_counter
    from ingest import CHROMA_DIR, get_collection, load_model
    from paths import INDEX_ARTICLES_PATH, PROJECT_ROOT

    print(f"indeks: {CHROMA_DIR} | articles.json: {INDEX_ARTICLES_PATH}")
    articles = load_articles()
    chunks = build_chunks(articles, make_token_counter())
    coll = get_collection()
    got = coll.get(include=["documents", "metadatas", "embeddings"])
    problems = compare_index(chunks, got["ids"], got["documents"], got["metadatas"])
    print(f"articles.json: {len(articles)} artikel -> {len(chunks)} chunk | indeks: {coll.count()} chunk")

    if args.fingerprint or args.expect_v1_archive:
        fp = content_fingerprint(got["ids"], got["documents"], got["metadatas"], got["embeddings"])
        fp["sha256_articles_json_isi"] = articles_content_hash(articles)
        print("sidik jari isi:", json.dumps(fp, indent=2, ensure_ascii=False))
        if args.expect_v1_archive:
            meta = json.loads((PROJECT_ROOT / "testset" / "v1.meta.json").read_text(encoding="utf-8"))
            recorded = meta.get(V1_ARCHIVE_META_KEY, {}).get("sidik_jari_isi")
            if recorded is None:
                problems.append(f"v1.meta.json belum memuat {V1_ARCHIVE_META_KEY}.sidik_jari_isi")
            else:
                mismatch = compare_fingerprints(fp, recorded)
                problems += mismatch
                if not mismatch:
                    print("SIDIK JARI COCOK dengan arsip Versi 1 yang tercatat")

    if args.embed_sample > 0 and not problems:
        import numpy as np

        step = max(1, len(chunks) // args.embed_sample)
        sample = chunks[::step][:args.embed_sample]
        model = load_model()
        fresh = model.encode([c["text"] for c in sample], normalize_embeddings=True)
        stored = coll.get(ids=[c["id"] for c in sample], include=["embeddings"])
        by_id = dict(zip(stored["ids"], stored["embeddings"]))
        for c, vec in zip(sample, fresh):
            cos = float(np.dot(vec, np.asarray(by_id[c["id"]], dtype=float)))
            print(f"  embed ulang {c['id']:<22} kosinus dengan vektor tersimpan: {cos:.6f}")
            if cos < 0.999:
                problems.append(f"{c['id']}: vektor tersimpan tidak cocok dengan embedding teks saat ini (kosinus {cos:.4f})")

    if problems:
        print(f"INDEKS BASI: {len(problems)} masalah")
        for p in problems[:15]:
            print("  -", p)
        return 1
    print("INDEKS SEGAR: id, teks, metadata (dan sampel embedding) sama dengan articles.json saat ini")
    return 0


if __name__ == "__main__":
    sys.exit(main())
