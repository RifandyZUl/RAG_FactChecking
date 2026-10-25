# scripts/

| Berkas | Untuk | Catatan |
| --- | --- | --- |
| `pembaruan_berkala.cmd`, `pembaruan_berkala.pyw` | Task Scheduler: scraping berkala (`scraping.scheduled`) | jangan dipindah tanpa memperbarui tugas terjadwal; `.cmd` tetap CRLF |
| `screenshots.py` | tangkapan layar bukti tampilan (Playwright, dev saja), termasuk potongan atas 2x (`--only beranda-atas --only ditemukan-atas`) | demo harus sudah berjalan. **Memakai kuota Gemini**: `ditemukan`, `belum-ditemukan`, dan `ditemukan-atas` masing-masing 1 pemeriksaan sungguhan (biasanya 1 permintaan, paling banyak 8 bila ada percobaan ulang); `beranda`, `tentang`, `beranda-atas` tidak memanggil Gemini |
| `anonymize_fixtures.py` | menyamarkan fixture HTML uji sebelum di-commit | `python scripts/anonymize_fixtures.py <asli> <keluaran>` |
