"""
Peluncur pembaruan berkala TANPA JENDELA (scraping saja; ingest tetap manual).

Dijalankan Task Scheduler dengan pythonw.exe dari venv proyek, sehingga tidak ada jendela konsol
yang muncul atau merebut fokus. Tidak bergantung pada direktori kerja maupun variabel lingkungan
pemanggil: root proyek diturunkan dari letak berkas ini. Kode keluar = kode keluar
scraping.scheduled (lihat src/scraping/scheduled.py). Keluaran masuk ke log per jalan di
data/expansion/logs/.

Untuk dijalankan dari terminal dengan keluaran terlihat, pakai scripts/pembaruan_berkala.cmd.
"""

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

try:
    from scraping import scheduled

    code = scheduled.main()
except SystemExit as e:  # argparse (--help, argumen salah)
    code = e.code if isinstance(e.code, int) else 2
except BaseException:  # noqa: BLE001 -- tanpa konsol, galat di sini akan hilang tanpa jejak
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    text = f"{stamp} peluncur pembaruan berkala gagal sebelum atau di luar scraping.scheduled:\n{traceback.format_exc()}\n"
    log = ROOT / "data" / "expansion" / "logs" / "peluncur_galat.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(text)
    (ROOT / "PERHATIAN_PEMBARUAN.txt").write_text(
        "PEMBARUAN BERKALA: PELUNCUR GAGAL (kode 8)\n\n" + text + f"\nRincian: {log}\n", encoding="utf-8")
    code = 8
sys.exit(code)
