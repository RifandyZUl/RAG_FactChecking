# testset/: data uji beku, hasil analisis, dan bukti pra-registrasi

**`testset/` BUKAN `tests/`.**
- `testset/` berisi **data**: butir set uji, label, catatan pra-registrasi dan pembekuan, serta hasil
  analisis yang dirujuk catatan itu. Isinya tidak dijalankan.
- `tests/` berisi **kode uji otomatis** (pytest), yang berjalan offline tanpa API dan tanpa data lokal.

**Aturan:**
- Tidak ada berkas di sini yang dipindah atau diubah tanpa catatan. Berkas yang dirujuk `v1.meta.json`
  sebagai bukti tetap di jalur aslinya (keputusan pemilik proyek 2026-10-24).
- Salinan kerja berkas di folder ini **CRLF** (kecuali `ANNOTATION_GUIDE.md`, LF), lewat `.gitattributes`.
  Alasannya, dua hash bukti dicatat dari byte salinan kerja CRLF:

  | Berkas | sha256 byte CRLF (tercatat) | sha256 isi git LF (pembanding) |
  | --- | --- | --- |
  | `eksternal_butir.json` | `87e2ad83…` | `667a67a0…` |
  | `v1.jsonl` | `ecef6636…` | `d948addc…` |

  Hash lengkapnya dan ujinya ada di `tests/core/test_frozen_bytes.py`. Hash lain (pedoman, `sha256_butir`,
  berkas terkunci) dihitung setelah normalisasi akhir baris, sehingga tidak bergantung pada CRLF/LF.

| Berkas | Jenis | Dibuat / dibaca oleh | Pembekuan / commit |
| --- | --- | --- | --- |
| `ANNOTATION_GUIDE.md` | data beku (pedoman anotasi v1.0) | ditulis manusia; dibaca `evaluation.devset`, `labeling.*` (teks pedoman di berkas tinjauan), uji kunci | dikunci `2500013` 2026-09-21, tag `annotation-guide-v1.0` |
| `GUIDE_LOCK.json` | bukti pembekuan (hash pedoman) | ditulis saat penguncian; dibaca `tests/core/test_testset_locks.py` | `2500013` 2026-09-21 |
| `v1.meta.json` | bukti pra-registrasi + catatan bertanggal (entri baru ditambahkan, pra-registrasi tidak diubah) | manual; dibaca `evaluation.{testset_eval, testset_analysis, index_check, index_comparison, external_eval}`, `labeling.*`, uji kunci | pra-registrasi `2500013` 2026-09-21; entri terakhir `ddcbf5c` 2026-10-21 |
| `v1.jsonl` | data beku (54 butir set uji v1) | disusun manual dari kandidat (`labeling.candidates.*`); dibaca evaluasi dan uji kunci | tag `testset-v1` (`028bea7`) 2026-09-23 |
| `targets_v1.json` | data beku (20 artikel target positif) | `labeling.candidates.targets` | `922d4e6` 2026-09-22 |
| `archive_sample_v1.json` | data beku (sampel arsip untuk kandidat negatif) | alur pengumpulan kandidat (`labeling.candidates`), lihat commit `a67d472` | `a67d472` 2026-09-22 |
| `eksternal_butir.json` | data beku (91+8 butir set eksternal, sidik jari indeks, hash berkas terkunci) | `evaluation.external_eval --freeze`; dibaca `evaluation.external_*`, `webapp.evaluation_facts`, uji kunci | `fa7464c` 2026-10-17 |
| `eksternal_sesi_buta_pilihan.json` | data beku (pilihan sesi buta) | `labeling.sessions.blind_session --select` | `fa7464c` 2026-10-17 |
| `v1_analysis.json`, `v1_analysis_report.txt` | hasil analisis, **dirujuk `v1.meta.json`** | `evaluation.testset_analysis` | `b0ee4fd` 2026-09-23 |
| `v1_temuan_untuk_v2.md` | hasil analisis (temuan untuk Versi 2), **dirujuk `v1.meta.json`** | ditulis manual dari hasil analisis | terakhir `7c5bd2b` 2026-10-03 |
| `retrieval_ablation.json` (+ `_report.txt`) | hasil analisis (ablasi pada arsip v1), **dirujuk `v1.meta.json`** | `evaluation.retrieval_ablation` | `036189e` 2026-09-25 |
| `retrieval_ablation_prod922.json` (+ `_report.txt`) | hasil analisis (indeks 922), **dirujuk `v1.meta.json`** | `evaluation.retrieval_ablation --out-json/--out-report` | `9bee0af` 2026-09-27 |
| `retrieval_ablation_prod1532.json` (+ `_report.txt`) | hasil analisis (indeks 1.532) | `evaluation.retrieval_ablation --out-json/--out-report` | `acc75e6` 2026-10-03 |
| `v1_perbandingan_indeks_922.json`, `_1532.json` | hasil analisis, **dirujuk `v1.meta.json`** | `evaluation.index_comparison` | `9bee0af` 2026-09-27; `d0e1e74` 2026-10-03 |
| `retriever_exactness_1532.json` | hasil analisis (HNSW vs eksak) | `evaluation.retriever_exactness` | `c6cb45b` 2026-10-03 |
| `devset_retrieval_1532.json` | hasil analisis (set pengembangan, retrieval saja) | pengukuran penutupan 2026-10-03 (CLAUDE.md butir (l)); skrip penghasilnya tidak tercatat di kode | `c84e44a` 2026-10-03 |
| `eksternal_hasil_per_butir.json` | hasil analisis yang dipublikasikan (per butir) | `evaluation.external_analysis`; dibaca `webapp.evaluation_facts` (halaman "Tentang") | `a56cac4` 2026-10-20 |
| `v2_pesan_berantai_ringkasan.json` | hasil analisis (panjang pesan berantai asli) | pengukuran rancangan Versi 2 (commit `2ce1665`) | `2ce1665` 2026-10-03 |
| `v2_ukuran_sampel.json`, `.txt` | hasil analisis (perhitungan ukuran sampel) | `evaluation.sample_size` | `66004c4` 2026-10-03 |
