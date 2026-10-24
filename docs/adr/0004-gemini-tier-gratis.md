# ADR 0004: Gemini tier gratis sebagai LLM generator

## Konteks

Generator Versi 1 butuh LLM yang bisa memutuskan apakah klaim pengguna sama dengan klaim artikel, dengan
keluaran terstruktur. Mesin pengembangan hanya punya CPU dan RAM bebas sekitar 2,5-3,9 GB. Proyek tidak punya
anggaran layanan berbayar.

## Keputusan

- `gemini-3.5-flash-lite` (thinking `medium`) lewat `google-genai`, tier gratis (RPD 500, RPM 15), ditetapkan
  2026-09-21.
- Pipeline hanya bergantung pada antarmuka `LLMProvider.generate(...)`, sehingga penyedia bisa diganti tanpa
  menulis ulang pipeline.
- Pengaman dipasang di kode, bukan di prompt: status diambil dari metadata, tautan hanya dari metadata, LLM
  hanya memilih id dari tiga kandidat, dan URL dari LLM dibuang.
- Kuota dijaga sendiri: jendela geser RPM/TPM, buku besar harian per hari Pasifik yang menghitung setiap
  permintaan (termasuk yang ditolak), dan retry internal SDK dimatikan.

## Alternatif yang ditolak

- **Claude API**: dibatalkan karena berbayar (perkiraan $0,25-0,65 per 10 kueri).
- **Model lokal**: dibatalkan. Dengan RAM sekitar 3,9 GB dan CPU saja, model 3B diperkirakan butuh 2,5-3,5
  menit per kueri.
- **`gemini-3.8-flash`** (model bawaan sebelumnya): dihentikan 2026-09-21 karena layanannya tidak stabil (503,
  timeout, 429 di bawah batas lokal) dan RPD-nya hanya 20.

## Konsekuensi

- Batas tier gratis bisa berubah tanpa pemberitahuan, dan kuota harian dibagi antara demo dan evaluasi.
- Konten tier gratis dipakai Google untuk memperbaiki produknya, termasuk klaim yang diketik pengguna demo.
  Ini dicatat di halaman Tentang dan README; demo tidak cocok untuk data sensitif.
- Temperatur dan seed tidak diatur, jadi keputusan bisa bervariasi antar-run. Karena itu evaluasi memakai
  keputusan modus dari 3 run.
