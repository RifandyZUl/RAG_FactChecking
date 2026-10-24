# scripts/

| Berkas | Untuk | Catatan |
| --- | --- | --- |
| `pembaruan_berkala.cmd`, `pembaruan_berkala.pyw` | Task Scheduler: scraping berkala (`scraping.scheduled`) | jangan dipindah tanpa memperbarui tugas terjadwal; `.cmd` tetap CRLF |
| `screenshots.py` | tangkapan layar bukti tampilan (Playwright, dev saja) | demo harus sudah berjalan |
| `anonymize_fixtures.py` | menyamarkan fixture HTML uji sebelum di-commit | `PYTHONPATH=src python scripts/anonymize_fixtures.py <asli> <keluaran>` |
