# ADR 0002: Berkas inti dikunci dengan hash

## Konteks

Angka evaluasi hanya sah untuk kode yang dievaluasi. Versi 1 dievaluasi pada set uji v1 yang dibekukan (tag
`testset-v1`), dan evaluasi eksternal dibekukan 2026-10-17 (`fa7464c`). Bila generator, prompt, retriever, atau
chunker berubah diam-diam, angka di README tidak lagi berlaku untuk kode yang ada.

## Keputusan

- `src/generator.py` (termasuk prompt sistem dan skema), `src/retriever.py`, dan `src/chunker.py` **dikunci**.
  Hash ternormalisasinya dicatat di bukti beku `testset/v1.meta.json` (`sidik_jari_generator_v1`) dan
  `testset/eksternal_butir.json` (`hash_berkas_terkunci`). Kuncinya ditegakkan
  `tests/core/test_testset_locks.py` di setiap jalan uji, termasuk CI.
- Pedoman anotasi dikunci dengan `testset/GUIDE_LOCK.json` dan tag `annotation-guide-v1.0` (di origin sejak
  2026-10-24). `testset/v1.jsonl` dibandingkan byte demi byte dengan isinya pada tag `testset-v1`.
- Hash byte dua berkas bukti dihitung dari salinan kerja CRLF. `.gitattributes` menjaga `testset/**` tetap CRLF
  di setiap checkout (`tests/core/test_frozen_bytes.py`).
- Perapian di Tahap 1b dikerjakan **di sekitar** berkas terkunci: berkas itu tidak dipindah atau disunting.

## Alternatif yang ditolak

- **Mengandalkan disiplin tanpa uji**: ditolak, karena kunci yang tidak diuji tidak bisa dibuktikan.
- **Memperbarui hash setiap kali kode berubah**: ditolak, karena itu meniadakan arti pembekuan. Mengubah
  berkas terkunci berarti evaluasi baru dengan set uji baru.

## Konsekuensi

- Temuan ruff lama di berkas terkunci tidak diperbaiki, melainkan dikecualikan per berkas dan per aturan di
  `pyproject.toml`.
- Perbaikan tampilan dan keamanan dilakukan di lapisan lain (`presentation`, `service`), bukan di generator.
- CI mengambil seluruh riwayat dan tag, dan gagal bila ada uji yang dilewati, karena uji kunci `v1.jsonl`
  melewati dirinya sendiri bila tag tidak ada.
