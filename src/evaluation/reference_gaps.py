"""
Hitung artikel yang tidak punya rujukan untuk ditampilkan (`references` kosong setelah penyaringan), lalu
simpan ANGKANYA SAJA bersama sidik jari isi indeks yang bersangkutan. Tanpa LLM, tanpa jaringan.

Mengapa ada: README menyebut "205 dari 1.532" dan "210 dari 1.611" artikel tanpa rujukan. articles.json
tidak di-commit (memuat teks hoaks dan kontak penipu), jadi angka itu perlu berkas hasil ter-commit yang
bisa ditelusuri. Berkas keluaran tidak memuat id, judul, URL, atau teks artikel.

Folder yang diperiksa harus berisi `articles.json` dan `chroma/` (mis. `data` atau
`data/backups/pre_antrean_2026-10-25`). Indeks TIDAK dibuka langsung: `chroma/` disalin ke folder sementara
lebih dulu, karena ChromaDB menulis ulang berkasnya setiap kali koleksi dibuka. Alat menolak bila daftar
artikel di indeks berbeda dengan articles.json di folder yang sama.

Pemakaian (dari root proyek), satu label per jalan; entri dengan label yang sama ditimpa:
  python -m evaluation.reference_gaps --label evaluasi_1532 --folder data/backups/pre_antrean_2026-10-25
  python -m evaluation.reference_gaps --label demo_1611 --folder data
"""

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from paths import PROJECT_ROOT

OUT_PATH = PROJECT_ROOT / "docs" / "evaluasi" / "rujukan_kosong.json"
FROZEN_PATH = PROJECT_ROOT / "testset" / "eksternal_butir.json"


def count_missing_references(articles: list[dict]) -> dict[str, int]:
    """Jumlah artikel dan jumlah yang `references`-nya kosong (fungsi murni; hanya angka yang keluar)."""
    return {"jumlah_artikel": len(articles),
            "artikel_tanpa_rujukan": sum(1 for a in articles if not a.get("references"))}


def index_fingerprint_of_copy(chroma_dir: Path) -> dict[str, Any]:
    """Sidik jari isi indeks, dihitung pada SALINAN sementara `chroma_dir` (sumber tidak pernah dibuka)."""
    from chromadb.api.shared_system_client import SharedSystemClient

    from evaluation.index_check import content_fingerprint
    from ingest import collection_ef_search, get_collection

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        copy = Path(tmp) / "chroma"
        shutil.copytree(chroma_dir, copy)
        before = set(SharedSystemClient._identifier_to_system)
        try:
            coll = get_collection(copy)
            if coll.count() == 0:
                raise SystemExit(f"{chroma_dir}: indeks kosong atau tidak ada")
            got = coll.get(include=["documents", "metadatas", "embeddings"])
            fp = content_fingerprint(got["ids"], got["documents"], got["metadatas"], got["embeddings"])
            fp["ef_search"] = collection_ef_search(coll)
        finally:
            # Hentikan backend yang dibuka di sini (atribut privat chromadb 1.5.9, sama dengan tests/conftest.py);
            # tanpa itu Windows menolak menghapus berkas HNSW salinan yang masih terbuka.
            for identifier in set(SharedSystemClient._identifier_to_system) - before:
                SharedSystemClient._identifier_to_refcount.pop(identifier, None)
                SharedSystemClient._identifier_to_system.pop(identifier).stop()
    return fp


def build_entry(folder: Path) -> dict[str, Any]:
    from evaluation.index_check import articles_content_hash

    articles = json.loads((folder / "articles.json").read_text(encoding="utf-8"))
    fp = index_fingerprint_of_copy(folder / "chroma")
    fp["sha256_articles_json_isi"] = articles_content_hash(articles)
    counts = count_missing_references(articles)
    if fp["jumlah_artikel"] != counts["jumlah_artikel"]:
        raise SystemExit(f"indeks memuat {fp['jumlah_artikel']} artikel, articles.json {counts['jumlah_artikel']}: "
                         "bukan pasangan yang sama")
    frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))["indeks_beku"]
    same_as_eval = all(fp.get(k) == v for k, v in frozen.items())
    return {**counts, "diukur": datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat(), "sidik_jari_indeks": fp,
            "sama_dengan_indeks_beku_evaluasi_eksternal": same_as_eval}


def main() -> int:
    from hf_env import prepare_hf_env

    prepare_hf_env()  # ingest diimpor (tidak memuat model, tetapi titik masuk tetap menyetelnya)
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--label", required=True, help="nama entri, mis. evaluasi_1532 atau demo_1611")
    ap.add_argument("--folder", type=Path, required=True, help="folder berisi articles.json dan chroma/")
    args = ap.parse_args()

    entry = build_entry(args.folder)
    out = json.loads(OUT_PATH.read_text(encoding="utf-8")) if OUT_PATH.exists() else {
        "keterangan": ("Artikel tanpa rujukan yang boleh ditampilkan (references kosong setelah penyaringan). "
                       "Hanya angka; tanpa id, judul, URL, atau teks artikel. Dibuat dengan "
                       "python -m evaluation.reference_gaps."),
        "entri": {}}
    out["entri"][args.label] = entry
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({args.label: entry}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
