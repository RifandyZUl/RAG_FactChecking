# Rencana Tahap 1b: perapian struktur (BELUM ada yang dipindah)

Branch `tahap-1b-struktur`, dari main `29514c0`. Berkas ini satu-satunya perubahan; nanti dipindah ke
`docs/audit/`. Menunggu persetujuan pemilik proyek.

## 1. Keadaan sekarang (git ls-files, diringkas)

akar 8 · `.streamlit/` 1 · `archive/` 1 · `assets/` 4 · `config/` 1 · `docs/` 14 · `manifests/` 1 ·
`scripts/` 3 · `src/` 11 · `src/candidates/` 16 · `src/evaluation/` 19 · `src/llm/` 9 · `src/scraping/` 12 ·
`src/ui/` 5 · `tests/` 67 (52 berkas + 15 fixture) · `testset/` 25. Pytest mengumpulkan **548** uji.

## 2. Struktur baru (usulan)

```
src/  chunker.py ingest.py retriever.py generator.py paths.py   (inti RAG, tetap)
      hf_env.py (BARU, bagian 6)   README.md (BARU)
      llm/ scraping/ evaluation/ (tetap; evaluation/README.md BARU)
      labeling/ candidates/ gap/ sessions/   (dari src/candidates/)
      webapp/ app.py settings.py resources.py service.py evaluation_facts.py presentation.py ui/
tests/ conftest.py _fakes.py fixtures/  core/ scraping/ llm/ evaluation/ labeling/ webapp/
testset/ (input, data beku, hasil yang dirujuk v1.meta.json) + README.md
reports/ retrieval/ eksternal/ perencanaan_v2/ + README.md
docs/ README.md rancangan/ evaluasi/ audit/ adr/ riwayat/ tampilan/
scripts/ + anonymize_fixtures.py + README.md
archive/ v1/ (tetap) fitur_mati/related_threshold.json + README.md
manifests/README.md  data/README.md  LICENSE  .gitattributes
```

**Nama subpaket labeling:** `labeling.candidates` (screen, crosssite, gemma_generate, targets, chain_sample,
archive), `labeling.gap` (gap_review, gap_workbook, gap_blocks, gap_result), `labeling.sessions`
(blind_session, blind_workbook, adjudication_workbook, v1_verification, trace_audit). Ada impor silang
antarsubpaket (mis. `sessions` memakai `gap` dan `candidates.screen`); semuanya ikut diperbarui.

## 3. Tabel pemindahan dan rujukan yang harus diperbarui

| Jalur lama | Jalur baru | Rujukan yang diperbarui |
| --- | --- | --- |
| `src/app.py`, `settings.py`, `resources.py`, `service.py`, `evaluation_facts.py`, `presentation.py`, `ui/` | `src/webapp/...` | impor di modul itu; `settings.STYLE_PATH`; `tests/test_ui.py` (jalur app), uji webapp; `tests/test_scheduled.py` (memakai `presentation`, satu-satunya pemakai di luar demo; tetap impor `webapp.presentation`); README/CLAUDE.md. **Perintah demo:** `$env:PYTHONPATH="src"; python -m streamlit run src\webapp\app.py` (direktori skrip bukan lagi `src/`). Tanpa modul pembungkus. |
| `src/candidates/*.py` | `src/labeling/{candidates,gap,sessions}/` | ±60 baris impor di 15 modul + 13 uji + `evaluation/external_analysis.py`, `external_eval.py`; perintah `python -m candidates.X` di README/CLAUDE.md/rancangan → `labeling.<sub>.X` |
| `testset/eksternal_hasil_per_butir.json` | `reports/eksternal/` | `evaluation.external_analysis.PUBLIC_TABLE_PATH`, `webapp.evaluation_facts.RESULTS_PATH`, README |
| `testset/retrieval_ablation_prod1532.json` + `_report.txt`, `retriever_exactness_1532.json`, `devset_retrieval_1532.json` | `reports/retrieval/` | README/CLAUDE.md (hanya teks; tidak dibaca kode) |
| `testset/v2_pesan_berantai_ringkasan.json`, `v2_ukuran_sampel.json/.txt` | `reports/perencanaan_v2/` | `evaluation.sample_size` (keluaran bawaan), `tests/test_sample_size.py`, rancangan_v2 |
| `docs/rancangan_*.md` (3) | `docs/rancangan/` | README, CLAUDE.md, catatan riwayat |
| `docs/audit_tahap0.md`, `laporan_tahap1.md`, rencana ini | `docs/audit/` | README, CLAUDE.md |
| `docs/draf_readme_evaluasi.md` | `docs/riwayat/` | CLAUDE.md |
| `tests/anonymize_fixtures.py` | `scripts/` | CLAUDE.md ("Cara Kerja"), README |
| `tests/test_*.py` (52) | `tests/<kelompok>/` | jalur `Path(__file__)` di 8 uji (+1 tingkat); `pytest.ini` `pythonpath = src tests` agar `import _fakes` tetap jalan |
| `config/related_threshold.json` | `archive/fitur_mati/` | tidak dibaca kode (grep); `.gitignore` perlu `!archive/fitur_mati/` karena `archive/*` diabaikan |

**Tidak berubah:** Task Scheduler (`scripts/pembaruan_berkala.*` memanggil `scraping.scheduled` dengan
`src` di jalur; `scraping/` tetap), `manifests/`, `archive/v1/`, `data/`, berkas inti di akar `src/`.

**Teks jalur di dalam kode yang TIDAK diubah:** kalimat seperti "docs/rancangan_v2.md bagian 11.6" di modul
labeling dan evaluasi ikut tertulis ke berkas tinjauan dan catatan bukti; mengubahnya mengubah isi, bukan
jalur. Hanya jalur yang benar-benar DIBUKA kode yang diperbarui. Rujukan lama diselesaikan lewat
`docs/riwayat/pemetaan_jalur.md`.

## 4. testset/: yang tetap (keputusan diperlukan)

Tetap sebagai input/data beku: `v1.jsonl`, `v1.meta.json`, `ANNOTATION_GUIDE.md`, `GUIDE_LOCK.json`,
`eksternal_butir.json`, `eksternal_sesi_buta_pilihan.json`, `targets_v1.json`, `archive_sample_v1.json`.

**Berbeda dari dugaan Anda:**
- `devset_retrieval_1532.json` adalah HASIL pengukuran (set pengembangan pada indeks 1.532), tidak dirujuk
  catatan beku → usul pindah ke `reports/retrieval/`.
- Tujuh berkas hasil **dirujuk `v1.meta.json`** sebagai bukti (`v1_analysis.json`, `v1_analysis_report.txt`,
  `retrieval_ablation.json`, `retrieval_ablation_prod922.json`, `v1_perbandingan_indeks_922.json`,
  `v1_perbandingan_indeks_1532.json`, `v1_temuan_untuk_v2.md`) → menurut aturan Anda TETAP di `testset/`,
  bersama pasangan laporannya (`retrieval_ablation_report.txt`, `_prod922_report.txt`). Akibatnya
  `reports/v1/` tidak dibuat dan `v1_temuan_untuk_v2.md` TIDAK pindah ke `docs/evaluasi/`.
  **Perlu keputusan:** (a) tetap di `testset/` (usul saya), atau (b) pindah dan andalkan tabel pemetaan.

## 5. .gitattributes (diuji di klon sementara, bukan di repo)

Keadaan: `core.autocrlf=true`; **semua 185 berkas teks di indeks sudah LF**; 139 salinan kerja CRLF.
Usulan: `* text=auto eol=lf`, `*.cmd/*.bat eol=crlf`, `*.png/*.jpg/*.xlsx/*.sqlite3/*.bin binary`, dan
**`testset/** text eol=crlf` + `testset/ANNOTATION_GUIDE.md text eol=lf`**.

Hasil uji di klon: `git add --renormalize .` → **0 perubahan isi indeks** (hanya `.gitattributes`
bertambah). Hash berkas terkunci tetap (dihitung setelah normalisasi; salinan kerja menjadi LF).

**DILAPORKAN, belum dilanjutkan:** dua hash bukti dihitung dari byte salinan kerja **CRLF**:
`eksternal_butir.json` `87e2ad83…` (rancangan 7.7, `data/candidates/sesi_buta_eksternal/label_final.json`)
dan `v1.jsonl` `ecef6636…` (`data/candidates/verifikasi_v1/kunci_verifikasi_v1.json`; hanya baris hash yang
dibaca). Dengan LF penuh keduanya menjadi `667a67a0…` dan `d948addc…`. Itulah alasan pengecualian
`testset/** eol=crlf`: dengannya salinan kerja testset byte-identik dengan hari ini **di Windows dan di
container Linux**, sehingga hash tercatat bisa direproduksi di mana pun. Hash lain di dokumen yang di-track
(berkas terkunci, `ANNOTATION_GUIDE.md`, `sha256_butir`) memakai bentuk ternormalisasi: aman.
Berkas hasil yang pindah ke `reports/` menjadi LF (tidak ada hash byte tercatat untuknya).

## 6. Persiapan lingkungan Hugging Face (ganti efek samping impor)

Sekarang `import ingest` dan `import settings` mengubah `os.environ` (3 variabel; terukur). Mengimpor
`ingest`, `retriever`, `chunker`, `generator`, `evaluation.*` **tidak** memuat `huggingface_hub`/`transformers`
(terukur), jadi pemanggilan di awal `main()` masih tepat waktu.

Usul: `src/hf_env.py` → `prepare_hf_env()` (set `HF_HUB_OFFLINE=1`, `DISABLE_SAFETENSORS_CONVERSION=1`,
`HF_HUB_DISABLE_SYMLINKS_WARNING=1` dengan `setdefault`; **melempar galat** bila `huggingface_hub` atau
`transformers` sudah termuat). Dipanggil di: `ingest.main` (termasuk `--update-metadata`), `main` di
`evaluation.{index_check, retriever_exactness, retrieval_ablation, index_comparison, testset_eval,
external_eval, external_analysis, generation_eval, repeat_eval, retrieval_eval}`, `labeling` `{screen,
chain_sample, gap_review}`, dan baris pertama `webapp/app.py`. Uji: impor semua modul di subproses tidak
mengubah `os.environ`; setiap titik masuk memanggil `prepare_hf_env` sebelum hal lain (uji AST + uji
perilaku); setelah persiapan, `huggingface_hub.constants.HF_HUB_OFFLINE` benar; panggilan terlambat gagal.

## 7. Lain-lain
- **LICENSE:** usul **MIT** (sederhana, lazim untuk portofolio); alternatif Apache-2.0 (klausul paten).
  README: lisensi hanya untuk kode; data TurnBackHoax tidak ada di repo dan tunduk pada ketentuan Mafindo.
- **docs/adr/:** belum ada ADR. Usul menulis 7 ADR (Streamlit, berkas terkunci, ChromaDB lokal, Gemini tier
  gratis, Docker dengan volume, pencatatan tanpa isi pesan, tanpa microservice) di 1b sebagai dokumentasi.
- `docs/desain_tampilan/` masuk `.gitignore`; logo sudah di `assets/brand/` dan tidak ada berkas yang
  merujuk folder itu kecuali catatan sejarah di laporan Tahap 1 (dipetakan).
- README per folder sesuai permintaan; `data/README.md` di-track (pola `.gitignore` di `data/` spesifik).

## 8. Bukti yang akan dilaporkan setelah pemindahan
jumlah uji 548 sama dan lolos; uji kunci; ruff; `retriever_exactness` + sidik jari indeks; hash berkas
terkunci dan testset tetap; demo berjalan + tangkapan layar beranda; `scraping.scheduled --help`/mode aman;
pemeriksa tautan antardokumen otomatis; pohon sebelum/sesudah.
