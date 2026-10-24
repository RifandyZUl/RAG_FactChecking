"""
Gabungkan ANTREAN pembaruan berkala (artikel di data/expansion/ yang belum ada di articles.json) ke
data/articles.json. Dijalankan MANUAL oleh pemilik proyek, sebelum reparse dan ingest (README, "Ingest antrean").

Bawaan: hanya MELAPORKAN (tanpa menulis apa pun). Dengan --tulis:
  1. menolak bila pemeriksaan kualitas antrean menahan penggabungan (label belum ditinjau, duplikat,
     tumpang tindih, seksi kosong, URL tidak sah) -- sama dengan pemeriksaan scraping.scheduled;
  2. menyalin articles.json lama ke data/backups/pre_antrean_<tanggal>/articles.json (menolak menimpa);
  3. menambahkan antrean di AKHIR articles.json (urutan berkas forward_*/retry_*), lewat penulis yang sama
     dengan pipeline scraping;
  4. memeriksa: jumlah = lama + antrean, artikel lama identik dan berurutan sama, tanpa id ganda.
Indeks vektor TIDAK disentuh; langkah berikutnya reparse, ingest, index_check (README).

Pemakaian (dari root proyek, venv):  python scripts/gabung_antrean.py [--tulis]
"""

import argparse
import json
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from paths import ARTICLES_PATH, DATA_DIR
from scraping import scheduled
from scraping.pipeline import write_articles


def merge(articles_path: Path, queue: list[dict], backup_dir: Path) -> dict:
    """Tambahkan `queue` di akhir `articles_path` setelah mencadangkannya. Mengembalikan ringkasan."""
    old = json.loads(articles_path.read_text(encoding="utf-8"))
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
    args = ap.parse_args()

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
    out = merge(ARTICLES_PATH, queue, DATA_DIR / "backups" / f"pre_antrean_{datetime.now(ZoneInfo('Asia/Jakarta')).date().isoformat()}")
    print(f"DIGABUNG: {out['lama']} + {out['antrean']} = {out['sekarang']} artikel; cadangan {out['cadangan']}")
    print("berikutnya: python -m scraping.reparse, lalu ingest (README, 'Ingest antrean')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
