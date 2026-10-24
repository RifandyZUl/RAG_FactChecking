"""
Gabungkan ANTREAN pembaruan berkala (artikel di data/expansion/ yang belum ada di articles.json) ke
data/articles.json. Dijalankan MANUAL oleh pemilik proyek, sebelum reparse dan ingest (README, "Ingest antrean").

Bawaan: hanya MELAPORKAN (tanpa menulis apa pun). Dengan --tulis --folder-cadangan FOLDER:
  1. menolak bila pemeriksaan kualitas antrean menahan penggabungan (label belum ditinjau, duplikat,
     tumpang tindih, seksi kosong, URL tidak sah) -- sama dengan pemeriksaan scraping.scheduled;
  2. menolak bila FOLDER belum berisi cadangan indeks (FOLDER/chroma/chroma.sqlite3, dibuat langkah
     sebelumnya di README), lalu menyalin articles.json lama ke FOLDER/articles.json (menolak menimpa).
     Nama FOLDER diberikan pemanggil, bukan dihitung skrip, supaya cadangan indeks dan articles.json
     pasti berada di folder yang sama walau tengah malam terlewati di antara kedua langkah;
  3. menambahkan antrean di AKHIR articles.json (urutan berkas forward_*/retry_*), lewat penulis yang sama
     dengan pipeline scraping;
  4. memeriksa: jumlah = lama + antrean, artikel lama identik dan berurutan sama, tanpa id ganda.
Indeks vektor TIDAK disentuh; langkah berikutnya reparse, ingest, index_check (README).

Pemakaian (dari root proyek, venv):  python scripts/gabung_antrean.py [--tulis --folder-cadangan FOLDER]
"""

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

from paths import ARTICLES_PATH, PROJECT_ROOT
from scraping import scheduled
from scraping.pipeline import write_articles


def merge(articles_path: Path, queue: list[dict], backup_dir: Path) -> dict:
    """Tambahkan `queue` di akhir `articles_path` setelah mencadangkannya. Mengembalikan ringkasan."""
    old = json.loads(articles_path.read_text(encoding="utf-8"))
    if not (backup_dir / "chroma" / "chroma.sqlite3").is_file():
        raise FileNotFoundError(f"cadangan indeks belum ada: {backup_dir / 'chroma'} (jalankan langkah cadangan dulu)")
    backup = backup_dir / "articles.json"
    if backup.exists():
        raise FileExistsError(f"cadangan sudah ada, tidak ditimpa: {backup}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(articles_path, backup)
    merged = old + queue
    ids = [a["article_id"] for a in merged]
    if len(set(ids)) != len(ids):
        raise ValueError("id ganda setelah penggabungan; tidak ditulis")
    write_articles(merged, articles_path)
    check = json.loads(articles_path.read_text(encoding="utf-8"))
    if len(check) != len(old) + len(queue) or check[: len(old)] != old:
        raise RuntimeError(f"pemeriksaan sesudah menulis gagal; pulihkan dari {backup}")
    return {"lama": len(old), "antrean": len(queue), "sekarang": len(check), "cadangan": str(backup)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--tulis", action="store_true", help="benar-benar menggabungkan (bawaan: hanya laporan)")
    ap.add_argument("--folder-cadangan", type=Path, default=None,
                    help="folder cadangan yang SUDAH berisi chroma/ (wajib dengan --tulis); relatif terhadap root proyek")
    args = ap.parse_args()
    if args.tulis and args.folder_cadangan is None:
        ap.error("--tulis wajib disertai --folder-cadangan (folder yang dibuat langkah cadangan indeks)")

    queue = scheduled.pending_articles()
    quality = scheduled.quality_report(queue, set())
    print(f"antrean belum digabung: {len(queue)} artikel; label: {dict(Counter(a['label'] for a in queue))}")
    print("kualitas: " + ", ".join(f"{k}={len(v) if isinstance(v, list) else v}" for k, v in quality.items()))
    if not queue:
        print("tidak ada yang perlu digabung")
        return 0
    if quality["tahan_penggabungan"]:
        print("DITAHAN: pemeriksaan kualitas menahan penggabungan; tinjau dulu (lihat pembaruan_status.json)")
        return 1
    if not args.tulis:
        print("laporan saja; jalankan dengan --tulis untuk menggabungkan")
        return 0
    folder = args.folder_cadangan if args.folder_cadangan.is_absolute() else PROJECT_ROOT / args.folder_cadangan
    out = merge(ARTICLES_PATH, queue, folder)
    print(f"DIGABUNG: {out['lama']} + {out['antrean']} = {out['sekarang']} artikel; cadangan {out['cadangan']}")
    print("berikutnya: python -m scraping.reparse, lalu ingest (README, 'Ingest antrean')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
