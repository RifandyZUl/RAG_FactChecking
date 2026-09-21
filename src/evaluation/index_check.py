"""
Verifikasi kesegaran indeks vektor terhadap articles.json (tanpa LLM, tanpa jaringan).

Indeks basi tidak menimbulkan galat: retriever tetap mengembalikan hasil, hanya dari teks/embedding
lama. Pemeriksaan: (1) himpunan id chunk sama, (2) teks tiap chunk di indeks identik dengan teks hasil
chunking articles.json saat ini (yang juga yang dibaca retriever untuk Narasi/Kesimpulan), (3) metadata
sama, dan (4) opsional: sampel chunk di-embed ulang dan dibandingkan dengan vektor tersimpan.

Pemakaian (dari root proyek): PYTHONPATH=src python -m evaluation.index_check [--embed-sample N]
Kode keluar: 0 = segar, 1 = basi.
"""

import argparse
import sys

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--embed-sample", type=int, default=8,
                    help="jumlah chunk yang di-embed ulang untuk dibandingkan dengan vektor tersimpan (0 = lewati)")
    args = ap.parse_args()

    from chunker import build_chunks, load_articles, make_token_counter
    from ingest import get_collection, load_model

    articles = load_articles()
    chunks = build_chunks(articles, make_token_counter())
    coll = get_collection()
    got = coll.get(include=["documents", "metadatas"])
    problems = compare_index(chunks, got["ids"], got["documents"], got["metadatas"])
    print(f"articles.json: {len(articles)} artikel -> {len(chunks)} chunk | indeks: {coll.count()} chunk")

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
