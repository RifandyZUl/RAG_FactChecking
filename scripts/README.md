# scripts/

| Berkas | Untuk | Catatan |
| --- | --- | --- |
| `pembaruan_berkala.cmd`, `pembaruan_berkala.pyw` | Task Scheduler: scraping berkala (`scraping.scheduled`) | jangan dipindah tanpa memperbarui tugas terjadwal; `.cmd` tetap CRLF |
| `screenshots.py` | tangkapan layar bukti tampilan (Playwright, dev saja), termasuk potongan atas 2x (`--only beranda-atas --only ditemukan-atas`) | demo harus sudah berjalan. **Memakai kuota Gemini**: `ditemukan`, `belum-ditemukan`, dan `ditemukan-atas` masing-masing 1 pemeriksaan sungguhan (biasanya 1 permintaan, paling banyak 8 bila ada percobaan ulang); `beranda`, `tentang`, `beranda-atas` tidak memanggil Gemini |
| `anonymize_fixtures.py` | menyamarkan fixture HTML uji sebelum di-commit | `python scripts/anonymize_fixtures.py <asli> <keluaran>` |
| `eksplorasi/uji_kelayakan_entitas.py` | uji kelayakan pemeriksaan entitas Versi 2 (EKSPLORATIF, rancangan_v2 A2.5) pada keluaran evaluasi eksternal yang tersimpan | tanpa LLM; butuh data lokal; keluaran ke `data/eksplorasi/` (kode butir dan status saja); hasilnya bukan bukti kinerja |
