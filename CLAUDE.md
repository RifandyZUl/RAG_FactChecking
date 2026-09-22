# CLAUDE.md

Panduan konteks proyek untuk Claude Code. Baca berkas ini sebelum
mengerjakan tugas apa pun di repositori ini.

---

## Status Terkini

**Diperbarui setiap kali satu tahap selesai. Baca bagian ini LEBIH DULU saat memulihkan
sesi** (mis. setelah sesi terputus) -- sebelum bagian lain di berkas ini.

*(2026-09-23)*

- **Generasi Gemma SUNGGUHAN SELESAI** (2026-09-22 malam - 2026-09-23): 20 permintaan
  dijalankan sesuai jatah final (positif 7, negatif_angka_waktu 6, negatif_entitas_sama 2,
  negatif_mudah 5) -> 60 kandidat, **58 lolos pemeriksaan otomatis**, ditulis ke
  `data/candidates/gemma_candidates.jsonl`. Berkas tinjauan untuk pemilik proyek sudah dibuat:
  `data/candidates/tinjauan_tahap3_gemma.csv` (58 baris, TANPA kolom kelas usulan otomatis,
  sesuai permintaan) -- **menunggu tinjauan manusia sebelum bisa masuk set uji** (Aturan Wajib #5).
- **Bug ditemukan dan diperbaiki saat generasi berjalan**: pemeriksaan kemiripan judul
  (`run_checks`) semula membandingkan kandidat `negatif_angka_waktu`/`negatif_entitas_sama`
  terhadap SEMUA 150 judul TERMASUK judul artikel target kandidat itu sendiri -- padahal
  kandidat subtipe ini SEHARUSNYA mirip judul targetnya (itu maksud subtipenya: KIA sama, satu
  unsur diubah), sehingga 10 dari 18 kandidat `negatif_angka_waktu` batch pertama salah
  ditandai gagal. Diperbaiki (`target_article` kini dikecualikan dari perbandingan) dan
  DINILAI ULANG tanpa panggilan API baru (teks kandidat tidak berubah); ke-10 baris berbalik
  jadi lolos, ditandai `catatan_perbaikan_bug_2026-09-22` di jsonl. Batch
  `negatif_entitas_sama` (baru ditambahkan, lihat di bawah) dan sisanya sudah pakai kode yang
  benar sejak awal.
- **Slot `negatif_entitas_sama` ditambahkan ke `gemma_generate.py`**: skrip semula HANYA
  punya 3 slot (positif/negatif_angka_waktu/negatif_mudah), berdasarkan asumsi lama bahwa
  subtipe entitas_sama_klaim_beda tidak butuh Gemma -- asumsi itu sudah dikoreksi duluan
  (lihat `koreksi_asumsi_subtipe_entitas_sama_klaim_beda` di `v1.meta.json`) tapi skrip belum
  diperbarui. Ditambahkan sebelum generasi dijalankan, diuji offline dulu.
- **Label emas final** (2026-09-22, Aturan Wajib #5 + `kebijakan_label_emas_2026-09-22`):
  seluruh label tahap 1/2/tambahan adalah tinjauan pemilik proyek sendiri. Berkas draf ChatGPT
  (`tinjauan_hoaks_tahap1_revisi.xlsx`, creator `openpyxl`) sudah DIHAPUS pemilik proyek;
  catatan riwayatnya dipertahankan di `v1.meta.json`. Kesepakatan dengan draf ChatGPT TIDAK
  DIHITUNG (berkas pembanding sudah tidak ada). Asal teks klaim tahap 2: pemilik proyek
  **tidak ingat** (dicatat di `human_claims.jsonl`, field `asal_teks_kategori`), bukan
  diasumsikan ditulis sendiri.
- **36700 diputuskan opsi (b):** menggantikan 36596 di sel Politik-SALAH (manusia-topik7 tetap
  butir batas terpisah, tetangga=36596). `testset/targets_v1.json` sudah diperbarui (juga
  36521->36019 dan 36564->36282, penukaran Liputan6 yang sama-sama terpicu).
- **Menunggu keputusan pemilik proyek:** tinjauan 58 kandidat Gemma di
  `data/candidates/tinjauan_tahap3_gemma.csv` (kolom `keputusan`/`label_saya`/`alasan_saya`
  kosong, isi manual seperti tahap 1/2). Setelah itu: gabungkan seluruh butir final (manusia +
  liputan6 + arsip + Gemma) menjadi 50 butir set uji v1 dan bekukan (`butir`/`sha256_butir` di
  `v1.meta.json` masih `null`).
- **Belum di-commit:**
  - `testset/v1.meta.json` -- catatan hasil generasi & perbaikan bug (bagian ini).
  - `src/candidates/gemma_generate.py`, `tests/test_gemma_generate.py` -- perbaikan bug +
    slot baru + uji baru.
  - (`data/candidates/*.jsonl`, `tinjauan_tahap3_gemma.csv` juga baru/diperbarui, tapi
    `data/candidates/` tidak di-commit -- lihat `.gitignore`.)
- **Sudah di-commit & push:** 32 commit lama (hingga `22eda9c`) + 3 commit label emas/generator
  (hingga `922d4e6`), semua di `origin/main` per 2026-09-22, `.env` terverifikasi tidak ter-track.

---

## Ringkasan Proyek

Sistem RAG (Retrieval-Augmented Generation) untuk verifikasi klaim
berbahasa Indonesia. Pengguna memasukkan sebuah klaim atau pesan yang
ingin dicek, sistem mencari kecocokan pada basis pengetahuan artikel cek
fakta TurnBackHoax.id, lalu mengembalikan status verifikasi, klarifikasi
fakta yang sebenarnya, dan tautan rujukan yang sahih.

Proyek ini adalah proyek portofolio dengan tujuan pembelajaran. Nilai
utamanya ada pada kejelasan arsitektur dan kualitas evaluasi, bukan pada
kelengkapan fitur.

## Status Pengembangan

Proyek dibangun bertahap dalam dua versi:

- **Versi 1 — RAG dasar (sedang dikerjakan).** Pipeline linear:
  scraping, chunking, embedding, penyimpanan vektor, retrieval berbasis
  kemiripan, generasi jawaban. Berfungsi sebagai *baseline* pembanding.
- **Versi 2 — Corrective RAG (belum dimulai).** Menambahkan node penilai
  relevansi dokumen, penulis ulang kueri, dan penilaian kredibilitas
  sumber. **Kandidat fitur (dicatat, belum diputuskan):** verdict ketiga
  "artikel terkait" untuk klaim yang lebih umum daripada artikel (mis. "Malaysia
  marah soal asap" vs artikel "Malaysia Laporkan Indonesia ke PBB"). Di Versi 1
  klaim seperti itu menghasilkan "belum ditemukan" (Aturan Wajib #4); sengaja
  tidak ditambahkan sebelum set uji v1 dibekukan.

Tahap saat ini: lapisan generasi jawaban (`src/generator.py`) sudah ditulis,
lolos uji offline, dan dijalankan live pada 10 kueri pengembangan
(`gemini-3.5-flash-lite` dipilih sebagai generator Versi 1; lihat "Hipotesis
dan status"). Berikutnya: merancang set uji 50 kueri yang terpisah dari set
pengembangan. Modul ingestion dan scraping (150 artikel) sudah selesai, dengan
satu masalah terbuka pada duplikasi teks seksi (lihat "Masalah terbuka").

---

## Struktur Data Sumber

Setiap artikel TurnBackHoax memiliki seksi baku berikut:

| Seksi | Isi |
| --- | --- |
| **Narasi** | Klaim/narasi hoaks yang beredar, beserta tautan ke unggahan aslinya |
| **Penjelasan** | Proses penelusuran yang dilakukan tim pemeriksa fakta |
| **Kesimpulan** | Fakta yang sebenarnya, umumnya diawali kata "Faktanya..." |
| **Hasil Periksa Fakta** | Label kebenaran (Salah, Penipuan, dsb.) |
| **Referensi** | Daftar tautan rujukan sahih yang dipakai untuk verifikasi |

Label kebenaran juga tertanam di judul dalam kurung siku, misalnya
`[SALAH] Malaysia Laporkan Indonesia ke PBB soal Karhutla`.

Pola URL artikel: `https://turnbackhoax.id/articles/{id}-{slug}`

---

## Aturan Wajib

Aturan berikut bersifat mengikat. Jangan melanggarnya tanpa persetujuan
eksplisit dari pemilik proyek.

### 1. Pemisahan tautan sumber hoaks dan rujukan sahih

Tautan pada seksi **Narasi** adalah sumber hoaks itu sendiri (unggahan
media sosial asli). Tautan ini **tidak boleh** ditampilkan kepada
pengguna sebagai rujukan yang sahih. Hanya tautan dari seksi
**Referensi** yang boleh disajikan sebagai rujukan.

Keduanya tetap disimpan, tetapi pada medan terpisah: `references` untuk
rujukan sahih, `claim_sources` untuk sumber hoaks.

### 2. Chunking berbasis seksi, bukan jumlah karakter

Pemotongan dokumen dilakukan per seksi (Narasi, Penjelasan, Kesimpulan),
**bukan** dengan pemotongan buta berdasarkan jumlah karakter.

Alasannya: chunk per seksi memisahkan peran tiap seksi. Narasi memuat
klaim yang beredar, Penjelasan memuat proses penelusuran, dan
**Kesimpulan** memuat fakta yang ditampilkan sebagai jawaban dari artikel
yang sama. Pemotongan berbasis karakter merusak pemisahan ini karena satu
chunk dapat berisi campuran akhir Narasi dan awal Penjelasan.

> **Koreksi rasional (hasil uji Versi 1):** rumusan awal aturan ini
> menyatakan bahwa klaim pengguna paling cocok dengan chunk Narasi.
> Asumsi itu **tidak terbukti** pada pengujian; lihat "Temuan Ingestion
> dan Retrieval". Manfaat chunking per seksi adalah pemisahan peran seksi,
> bukan pencocokan lewat Narasi. Aturannya sendiri tidak berubah.

### 3. Jangan biarkan LLM mengarang tautan

Tautan rujukan diambil dari metadata dokumen hasil retrieval, tidak
pernah dihasilkan oleh LLM. LLM yang diminta menuliskan URL dari
ingatannya cenderung berhalusinasi.

### 4. Jawaban wajib berbasis dokumen

Prompt sistem harus menegaskan bahwa LLM hanya boleh menjawab
berdasarkan potongan dokumen yang diberikan. Bila tidak ada dokumen yang
cukup relevan, jawaban yang benar adalah menyatakan klaim tersebut belum
ditemukan dalam basis data — bukan memaksakan kesimpulan.

### 5. Label emas set uji: tinjauan manusia wajib, label final selalu manusia

Setiap kandidat yang akan masuk set uji — termasuk kandidat buatan Gemma —
**wajib** melalui tinjauan pemilik proyek sendiri sebelum dipakai sebagai
butir set uji. **Label final selalu ditetapkan manusia** (pemilik proyek),
tidak pernah oleh AI. Bila draf AI (ChatGPT, Gemma, Claude, atau lainnya)
dipakai pada tahap mana pun — draf awal label, draf teks klaim, atau
pendapat yang dibaca sebelum memutuskan — **penggunaannya wajib dicatat**
secara eksplisit (model/alat, tahap, dan sejauh mana dipakai), sekalipun
draf itu sendiri kemudian tidak disimpan.

Alasan: kejadian 2026-09-22 — sebuah berkas draf label tahap 1 yang
dihasilkan `openpyxl` (bukan diketik manusia di Excel) sempat berisiko
dianggap sebagai label emas karena nama berkasnya mirip dengan berkas
label emas yang sebenarnya. Berkas draf itu sudah dihapus pemilik proyek
setelah label final ditetapkan (`data/candidates/` tidak di-commit, jadi
ini bukan operasi git); **catatan riwayat kejadian ini dipertahankan**
di `kebijakan_label_emas_2026-09-22` pada `testset/v1.meta.json` meski
berkasnya sudah tidak ada — termasuk cara mendeteksi kejadian serupa
(periksa `docProps/core.xml` suatu `.xlsx`: creator `openpyxl` atau nama
aplikasi lain berarti dihasilkan kode, bukan diketik manusia).

---

## Lingkungan Pengembangan

- **Sistem operasi:** Windows
- **Shell:** PowerShell
- **Python:** 3.11.4 (64-bit)
- **IDE:** Antigravity (turunan VS Code)

### Virtual environment (wajib)

Proyek ini memakai virtual environment di `.venv/` (di-gitignore). Semua
perintah Python **harus dijalankan dari venv ini**, bukan dari Python
global, agar dependensi terisolasi. Python global mesin dev juga dipakai
proyek lain (mis. TensorFlow), dan memasang paket proyek ini ke sana
pernah menimbulkan konflik `protobuf`.

```powershell
python -m venv .venv                          # sekali saja
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # requirements.txt + pytest
.\.venv\Scripts\python.exe -m pytest                # uji offline di tests/ (tanpa jaringan/API)
.\.venv\Scripts\Activate.ps1                        # atau aktifkan dulu
```

Paket di `src/` (mis. `scraping`) dijalankan dari **root proyek** dengan
`PYTHONPATH=src`, sehingga jalur relatif tetap berbasis root:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m scraping     # menggantikan `python src\scraper.py`
.\.venv\Scripts\python.exe -m evaluation.generation_eval --check-budget   # skrip evaluasi LIVE
```

Skrip evaluasi (`evaluation.generation_eval`, `retrieval_eval`, `gemma_json_check`,
`probe_quota`) sengaja **tidak** berawalan `test_`: pytest hanya mengumpulkan
`tests/` (lihat `pytest.ini`) dan tidak pernah memanggil LLM. Uji `tests/`
memakai objek palsu dan aman dijalankan kapan saja.

`requirements.txt` mengunci versi (`torch==2.14.0`, build CPU dari PyPI).
torch harus >= 2.6 agar `transformers` 5.x mau memuat
`pytorch_model.bin` bge-m3 (CVE-2025-32434).

### Catatan PowerShell

Di PowerShell, `curl` adalah alias untuk `Invoke-WebRequest`, bukan curl
asli. Flag gaya Unix seperti `-I` tidak bekerja dan dapat membuat
perintah menggantung. Gunakan `curl.exe` bila benar-benar memerlukan
curl, atau `Invoke-WebRequest -Method Head` sebagai gantinya.

### Catatan jaringan

Server `turnbackhoax.id` berlatensi tinggi dan kerap lambat mengirimkan
respons pertama. **Setiap permintaan jaringan wajib memiliki timeout
eksplisit.** Perintah tanpa batas waktu pernah menggantung lebih dari 40
menit pada proyek ini.

Ketentuan yang berlaku:

- Timeout: 45 detik
- Retry: maksimal 3 kali dengan *exponential backoff*, hanya untuk read
  timeout dan connection error — jangan retry untuk galat 404
- Jeda antar-permintaan: minimal 1,5 detik agar tidak membebani server
- HTML mentah di-cache ke `data/raw_html/` agar pengembangan logika
  parsing tidak perlu memanggil server berulang kali

---

## Struktur Direktori

```
RAG_FactChecking/
├── src/
│   ├── paths.py          # Jalur proyek terpusat (root, data/, cache, articles.json)
│   ├── scraping/         # Pengambilan & parsing artikel TurnBackHoax
│   │   ├── links.py      #   normalisasi URL + daftar domain diblokir (Aturan #1)
│   │   ├── client.py     #   sesi HTTP, timeout/retry, cache HTML
│   │   ├── discovery.py  #   pengumpulan URL dari halaman daftar
│   │   ├── parser.py     #   parsing HTML artikel -> dict terstruktur
│   │   ├── pipeline.py   #   orkestrasi + CLI (python -m scraping)
│   │   └── reparse.py    #   parse ulang dari cache TANPA jaringan (python -m scraping.reparse)
│   ├── chunker.py        # Chunking per seksi + metadata (Aturan Wajib #2)
│   ├── ingest.py         # Embedding bge-m3 -> ChromaDB (idempoten)
│   ├── retriever.py      # Retrieval, diagregasi per article_id
│   ├── llm/              # Abstraksi penyedia LLM (Gemini), retry, throttling, kuota
│   │   ├── errors.py, base.py, secrets.py   # galat; LLMProvider + CallRecord; .env + samarkan kunci
│   │   ├── gemini.py, gemini_errors.py      # GeminiProvider; penafsiran galat HTTP Gemini
│   │   └── limits.py, throttle.py, ledger.py # angka kuota; jendela geser RPM/TPM; buku besar + anggaran
│   ├── generator.py      # Klaim -> retrieval -> LLM -> jawaban terstruktur
│   └── evaluation/       # Evaluasi & diagnostik LIVE (bukan uji otomatis)
│       ├── generation_eval.py  #   evaluasi generasi (--check-budget, --compare)
│       ├── retrieval_eval.py   #   verifikasi retrieval pada kueri sehari-hari
│       ├── gemma_json_check.py #   uji format JSON Gemma 4
│       ├── probe_quota.py      #   probe tunggal ke server (1 permintaan)
│       └── results_store.py, comparison.py  # simpan/lanjutkan hasil; perbandingan model
├── tests/                # Uji offline (pytest), satu berkas per modul
│   ├── fixtures/         #   HTML nyata untuk uji (di-commit)
│   └── _fakes.py         #   objek palsu bersama (bukan uji)
├── data/
│   ├── raw_html/         # Cache HTML mentah (tidak di-commit)
│   ├── articles.json     # Hasil scraping terstruktur (tidak di-commit)
│   └── chroma/           # Basis vektor ChromaDB (tidak di-commit)
├── requirements.txt, requirements-dev.txt   # dependensi; + pytest
├── pytest.ini            # testpaths = tests, pythonpath = src
└── CLAUDE.md
```

---

## Konvensi Kode

- Bahasa komentar dan docstring: **Indonesia**
- Nama variabel dan fungsi: **Inggris**
- Sertakan *type hint* pada tanda tangan fungsi
- Tangani galat secara eksplisit; jangan menelan *exception* diam-diam
- Setiap perubahan pada logika parsing wajib diikuti menjalankan `pytest`
  (khususnya `tests/test_parser.py`, `test_links.py`, `test_client.py`)
- **Setiap perubahan logika parsing atau chunking mewajibkan pembangunan ulang
  indeks vektor**, berurutan: `python -m scraping.reparse` (offline, dari cache)
  -> `python src/ingest.py --rebuild` (hapus koleksi lama, embed semua chunk
  dari nol) -> `python -m evaluation.index_check` (kode keluar 0 = indeks segar).
  Indeks basi tidak menimbulkan galat: retriever tetap mengembalikan hasil,
  hanya dari teks dan embedding lama. Ingestion **inkremental** (tanpa
  `--rebuild`) hanya aman bila isi teks chunk tidak berubah: ia membandingkan
  teks tersimpan dengan teks baru dan meng-embed ulang yang berbeda
  (`select_chunks_to_embed`), tetapi TIDAK mendeteksi perubahan tokenizer,
  batas token (`MAX_SEQ_LENGTH`), model, atau metadata pada chunk yang teksnya
  sama, dan hanya melaporkan (tidak menghapus) chunk usang. Contoh terukur:
  setelah perbaikan duplikasi, ingest inkremental akan meng-embed 300 chunk
  yang berubah (Narasi dan Penjelasan) dan melewati 150 Kesimpulan yang
  teksnya identik.

---

## Cara Kerja yang Diharapkan

Proyek ini bertujuan pembelajaran, sehingga cara mengerjakannya penting,
bukan hanya hasil akhirnya.

- **Laporkan temuan sebelum mengubah kode.** Bila diminta menyelidiki
  sesuatu, sampaikan hasil penyelidikan lebih dulu dan tunggu
  persetujuan sebelum menulis ulang apa pun.
- **Tunjukkan bukti mentah.** Saat melaporkan hasil pemeriksaan
  jaringan atau struktur HTML, sertakan status code dan potongan
  keluaran aslinya. Jangan menyajikan dugaan seolah-olah hasil
  pemeriksaan langsung.
- **Ubah seperlunya.** Jangan merefaktor bagian yang tidak diminta.
  Logika parsing pada `extract_sections`, `extract_references`, dan
  `extract_claim_sources` sudah tervalidasi — jangan diubah tanpa alasan
  kuat. (Pengecualian yang disetujui 2026-09-21: `extract_sections`
  diperbaiki karena menduplikasi teks; lihat "Masalah terbuka" dan
  `tests/test_parser.py`, yang kini gagal bila rasio panjang hasil parse
  terhadap teks HTML asli melebihi 1,1.)
- **Jelaskan keputusan desain.** Bila ada beberapa pendekatan, sebutkan
  pilihan yang diambil beserta alasan dan konsekuensinya.
- **Sampaikan ketidakpastian secara jujur.** Bila sesuatu belum
  terverifikasi, katakan demikian alih-alih menyajikannya sebagai fakta.

---

## Temuan Ingestion dan Retrieval (Versi 1)

> **CATATAN (2026-09-21): seluruh angka bertanda `[DIUKUR ULANG 2026-09-21]` semula diukur
> pada teks Narasi/Penjelasan yang terduplikasi (150 dari 150 artikel). Duplikasi itu sudah
> diperbaiki (`extract_sections`), `articles.json` di-parse ulang dari cache, indeks vektor
> dibangun ulang dari nol dan diverifikasi segar (`evaluation.index_check`), lalu semuanya
> diukur ulang. Angka lama dan baru ada berdampingan di "Pengukuran ulang setelah perbaikan
> duplikasi" (di bawah), dengan penanda mana temuan yang bertahan dan mana yang berubah.**
> Angka lama yang masih tertulis di teks tiap bagian dipertahankan sebagai riwayat.

Hasil pengujian pertama terhadap 450 chunk (150 artikel), memakai 5 kueri
berbahasa sehari-hari (`src/evaluation/retrieval_eval.py`). **Sampelnya baru 5
kueri**: cukup untuk sanity check dan menemukan masalah, bukan evaluasi
statistik.

### Penjelasan menang atas Narasi [DIUKUR ULANG 2026-09-21] — BERTAHAN (arah), angka berubah

Diukur ulang pada 10 kueri (bukan 5): chunk Penjelasan tetap paling sering menang.
Peringkat satu: Penjelasan 7, Narasi 2, Kesimpulan 1 (data lama pada 10 kueri yang sama:
6/2/2). Seluruh top-5 chunk (50 hasil): Penjelasan 22, Kesimpulan 14, Narasi 14 (lama:
20/12/18). Angka di paragraf berikut (5 kueri) adalah riwayat pengukuran pertama; jangan
dibandingkan langsung dengan angka 10 kueri.

Asumsi awal bahwa klaim pengguna paling cocok dengan chunk Narasi
**tidak terbukti**. Pada peringkat satu, chunk Penjelasan menang pada 3
dari 5 kueri, Narasi 1, Kesimpulan 1. Pada seluruh top-5 chunk (25 hasil):
Penjelasan 11, Kesimpulan 7, Narasi 7. Chunk Penjelasan yang terpotong
pada 512 token pun tetap cocok kuat. Chunking per seksi dipertahankan
karena jawaban diambil dari Kesimpulan artikel yang sama, tetapi
rasionalnya adalah pemisahan peran seksi, bukan pencocokan lewat Narasi
(lihat koreksi pada Aturan Wajib #2).

### Retrieval diagregasi per `article_id`

Skor sebuah artikel adalah skor tertinggi di antara chunk-chunknya, apa
pun seksinya (`src/retriever.py`, `aggregate_by_article`). Tanpa agregasi,
satu artikel bisa mengisi beberapa peringkat teratas. Jawaban tetap
diambil dari chunk Kesimpulan artikel pemenang, dan tautan dari metadata
(Aturan Wajib #3).

### Skor kemiripan berdaya pisah rendah [DIUKUR ULANG 2026-09-21] — BERTAHAN, angka berubah sedikit

Semua skor di paragraf berikut berasal dari embedding teks terduplikasi (riwayat). Diukur
ulang pada data diperbaiki: skor kasus "vaksin flu bikin mandul" **0,6508 -> 0,6671**
(artikel teratas tetap 36214); positif terendah 0,5669 -> 0,5739; negatif tertinggi
0,6508 -> 0,6671; celah (positif terendah dikurangi negatif tertinggi) -0,0839 ->
-0,0932. Tiga dari lima skor positif tetap di bawah skor kasus vaksin flu. **Kesimpulan bahwa
skor kemiripan tidak dapat memisahkan klaim yang ada dari yang tidak ada bertahan** (semua
skor naik tipis; urutannya hampir tidak berubah: artikel teratas sama pada 9 dari 10 kueri).

Pada level artikel: kueri 2 memberi artikel benar 0,6227 dan artikel lain
0,6213 (selisih ≈ 0,001); kueri 5 memberi artikel lain 0,6877 melawan
artikel benar 0,6922. Skor artikel benar berkisar 0,567 sampai 0,692,
sedangkan tetangga yang salah bisa mencapai 0,688.

Uji kueri negatif (5 klaim yang tidak ada di basis data; ketiadaan
kata kunci diperiksa otomatis di `evaluation/retrieval_eval.py`) menambah bukti.
Skor artikel teratas tiap kueri negatif: 0,5204 (kebijakan subsidi, gas
melon), **0,6508** (vaksin flu bikin mandul; tetangga dekat artikel vaksin
HPV bikin impoten), 0,4825 (gempa megathrust), 0,4813 (daun sirsak), 0,5037
(bumi datar). Skor positif: 0,5669 sampai 0,6922. Klaim "vaksin flu bikin
mandul" sengaja dipertahankan sebagai kueri negatif: itu kasus tersulit
sekaligus paling realistis, karena hoaks nyata sering bervariasi di sekitar
tema yang sama, dan menguji hanya dengan klaim yang jauh dari topik akan
memberi gambaran yang terlalu optimistis. Hasilnya:

- Negatif yang jauh dari topik basis data (0,48 sampai 0,52) masih
  terpisah dari positif terendah (0,5669), tetapi celahnya hanya ≈ 0,05
  dan dihitung dari sampel 5 lawan 5.
- Klaim yang **serupa bentuknya** dengan klaim yang ada (vaksin flu vs
  vaksin HPV) mencetak 0,6508, di atas 3 dari 5 skor positif. Ambang skor
  tidak bisa memisahkannya, karena embedding menilai kemiripan topik, bukan
  apakah klaimnya sama.

**Kesimpulan:** hasil kueri negatif membuktikan, pada sampel ini, bahwa
skor kemiripan tidak dapat memisahkan klaim yang ada dari yang tidak ada.
Klaim negatif "vaksin flu bikin mandul" mencetak 0,6508, di atas 3 dari 5
skor positif, sehingga ambang skor apa pun akan menerima klaim itu atau
menolak tiga klaim yang memang ada di basis data. Karena itu **Aturan Wajib
#4 (menyatakan klaim belum ditemukan) tidak akan diwujudkan dengan ambang
skor di Versi 1.** Ini justifikasi empiris bahwa node penilai relevansi
(grader) di Versi 2, yang menilai apakah klaim pengguna sama dengan klaim
pada artikel hasil retrieval, adalah jawabannya.

**Ukuran sampel: baru 5 positif dan 5 negatif.** Angka-angka di atas
(termasuk celah ≈ 0,05 untuk negatif yang jauh dari topik) adalah indikasi
yang kuat untuk arah keputusan, bukan evaluasi statistik.

### Pemuatan model: riwayat safetensors PR #130

`transformers` 5.x menolak memuat `pytorch_model.bin` bila torch < 2.6
(CVE-2025-32434). Saat torch global masih 2.5.1, embedding 450 chunk
dibuat dari varian safetensors milik PR konversi #130 di repo
`BAAI/bge-m3` (pembuat: `SFconvertbot`, akun konversi otomatis Hugging
Face; commit `9a0624b8…`). PR itu belum di-review atau di-merge BAAI,
sehingga sempat menjadi ketergantungan yang belum terverifikasi.

**Sudah dibuktikan:** bobot safetensors tersebut identik bit-per-bit dengan
`pytorch_model.bin` resmi di branch `main` (391 dari 391 tensor, tanpa
selisih nama, dibandingkan dengan `torch.load(mmap=True, weights_only=True)`
di dalam venv). Karena itu embedding yang tersimpan tetap valid tanpa
diulang, dan skor retrieval sebelum dan sesudah peralihan identik.

**Keadaan sekarang:** venv memakai torch >= 2.6, sehingga `src/ingest.py`
memuat `.bin` resmi dari branch `main` dan tidak lagi bergantung pada PR.

**Jebakan:** setiap kali `transformers` memuat `.bin` dari repo tanpa
safetensors, ia menjalankan `Thread` non-daemon yang mengunduh varian
safetensors dari PR konversi (2,3 GB) di latar belakang, sehingga proses
Python tidak berhenti sampai unduhan selesai. Skripnya tampak selesai
(hasil tercetak) tetapi proses menggantung. `use_safetensors=False` tidak
mencegahnya; yang efektif adalah variabel lingkungan
`DISABLE_SAFETENSORS_CONVERSION=1`, yang di-set di bagian atas
`src/ingest.py`. Jangan dihapus.

---

## Lapisan Generasi Jawaban (Versi 1)

Kode: `src/llm/` (abstraksi penyedia), `src/generator.py`
(alur klaim -> retrieval 3 artikel -> LLM -> jawaban), `src/evaluation/generation_eval.py`
(evaluasi live 5 positif + 5 negatif). Kunci API dibaca dari `.env`
(`GEMINI_API_KEY`; contoh di `.env.example`) dan tidak pernah dicetak:
semua log dan pesan galat melewati `redact()`.

### Keputusan jalur: API gratis (Gemini), bukan Claude API atau model lokal

- **Claude API dibatalkan** karena berbayar (estimasi ±$0,25 sampai $0,65
  per 10 kueri pada Opus 5; harga dari tabel cache skill bertanggal
  2026-06-24, tidak diverifikasi ulang).
- **Model lokal dibatalkan**: RAM tersedia ±3,9 GB dan CPU-only membuat
  model 3B memakan ±2,5-3,5 menit per kueri (perkiraan dari benchmark CPU,
  tidak diukur langsung).
- **Gemini tier gratis** dipilih sebagai implementasi pertama.

### Desain provider-agnostic

Pipeline hanya bergantung pada `LLMProvider.generate(system_prompt,
user_prompt, json_schema=None) -> str`; penyedia dipilih lewat `LLM_PROVIDER`
di `.env`. Alasan: tier gratis dapat memperketat batas tanpa pemberitahuan
atau berhenti total tanpa kompensasi, dan tahap evaluasi perlu membandingkan
beberapa model tanpa menulis ulang pipeline. Setiap panggilan dicatat
(model, token bila tersedia, latensi, keberhasilan, jumlah 429).

Penanganan 429 (diperbaiki setelah percobaan live pertama): 429 dibedakan
menurut `quotaId` pada rincian galat (`classify_429`). **Kuota harian** ->
`LLMQuotaExhaustedError`, tanpa retry, dan evaluasi berhenti dengan pesan
jelas. **Per menit / tidak diketahui** -> maksimal 3 retry, menunggu sesuai
saran server (`Retry-After` / `retryDelay`); saran > 120 dtk dianggap kuota
habis. Format `quotaId` dikenal dari galat Gemini API umumnya dan diuji dengan
transport palsu; **belum diamati pada 429 asli akun ini**.

**Jebakan SDK:** klien Interactions di `google-genai` 2.24 mengulang 429/5xx
sendiri (3 retry, menunggu `Retry-After` tanpa batas atas) tanpa log. Di
percobaan live pertama itu menjelaskan mengapa satu "percobaan" memakan 2-3
menit padahal log menulis "menunggu 2,3 dtk" (terukur dengan transport palsu:
4 permintaan per panggilan; bahwa itulah yang terjadi pada server nyata adalah
kesimpulan, bukan pengamatan langsung). `disable_sdk_retry()` mematikannya
lewat konfigurasi internal SDK (opsi publik `retry_options.attempts` tidak bisa
di bawah 1 retry); `test_provider_with_real_sdk_errors` akan gagal bila SDK
berubah dan retry internal kembali aktif. Uji lama memakai galat palsu
berbentuk lain (body `str`, header di `err.headers`), sehingga tidak
menangkap bahwa saran server tidak pernah terbaca.

`evaluation/generation_eval.py` menulis hasil ke `data/generation_eval_<model>.jsonl` per
kueri, dapat dilanjutkan (kueri yang sudah punya hasil dilewati; `--force` untuk
mengulang), dan berhenti bila kuota harian habis. Opsi: `--model ID`,
`--check-budget` (hanya laporan anggaran, tanpa panggilan LLM), dan
`--compare DASAR KANDIDAT` (tabel keputusan berdampingan antarmodel, tanpa
panggilan LLM; hanya informasi kesetaraan keputusan dan BUKAN kriteria H3,
lihat "Hipotesis dan status").

**Throttling proaktif dan anggaran harian** (`src/llm/limits.py`, `throttle.py`, `ledger.py`): batas
RPM/TPM/RPD per model dibaca dari `DEFAULT_LIMITS` (dapat ditimpa `LLM_RPM`,
`LLM_TPM`, `LLM_RPD`). Jendela geser 60 dtk menjaga RPM dan TPM tidak pernah
tersentuh (setiap percobaan, termasuk retry, melewatinya); retry 429 tinggal
jaring pengaman. RPD dicatat di `data/quota_ledger.json` per hari **Pasifik**
(reset tengah malam Pasifik menurut dokumentasi) dan **setiap permintaan yang
dikirim dihitung, termasuk yang ditolak 429**, karena dokumentasi tidak
menyatakan apakah 429 ikut terhitung. Sebelum evaluasi dimulai, kebutuhan
(minimal 1 panggilan/kueri; terburuk 1 + `MAX_FORMAT_RETRIES`) dibandingkan
dengan sisa; bila tidak cukup, evaluasi tidak dimulai (kode keluar 4) dan saat
anggaran habis di tengah jalan permintaan tidak dikirim. **Buku besar hanya
tahu permintaan dari kode ini.** Koreksi logika pengisian awal: buku besar
sempat diisi (`seed(21)`) dari kolom "penggunaan puncak 28 hari" di dashboard AI
Studio, padahal angka itu puncak historis, bukan pemakaian hari berjalan, jadi
tidak sah sebagai nilai awal; entri keliru itu sudah dihapus. Nilai awal hanya
boleh berasal dari hitungan yang dapat ditelusuri (mis. log panggilan kita
sendiri); bila pemakaian hari itu tidak diketahui, buktinya adalah probe tunggal
(`src/evaluation/probe_quota.py`, 1 permintaan), bukan dashboard.

### Model dan kuota (diverifikasi dari dokumentasi resmi pada 2026-09-20)

- **Model bawaan (keputusan 2026-09-21): `gemini-3.5-flash-lite`**, generator
  Versi 1. `gemini-3.8-flash` (sebelumnya bawaan) **dihentikan** karena
  ketidakstabilan layanan (lihat "Hipotesis dan status"). Sumber daftar model:
  https://ai.google.dev/gemini-api/docs/models (halaman diperbarui
  2026-09-17 UTC); Flash stabil lain di halaman itu: 3.8, 3.7, 3.6, 3.5,
  3.1-flash-lite, 2.5-flash, 2.5-flash-lite. Ganti lewat `LLM_MODEL`.
  `gemini-2.0-flash` dan `-lite` tercatat sudah dimatikan.
- **Tier gratis:** halaman harga (https://ai.google.dev/gemini-api/docs/pricing)
  mencantumkan `gemini-3.8-flash` "Free of charge" pada Free tier.
- **Batas kuota: angka konkret TIDAK dipublikasikan di dokumentasi**, hanya
  di AI Studio (https://aistudio.google.com/rate-limit; dokumentasi:
  https://ai.google.dev/gemini-api/docs/rate-limits, yang juga menyatakan
  batas "not guaranteed"). **Angka akun ini, diambil dari AI Studio pada
  2026-09-21 (kolom penggunaan puncak 28 hari / batas; tier gratis dapat
  berubah tanpa pemberitahuan, ambil ulang berkala):**

  | Model | RPM | TPM (input) | RPD |
  | --- | --- | --- | --- |
  | `gemini-3.8-flash` | 5 (puncak 7) | 250K (puncak 15,19K) | 20 (puncak 21) |
  | `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite` | 15 | 250K | 500 |
  | `gemma-4-26b-a4b-it`, `gemma-4-31b-it` | 30 | 16K | 14,4K |

  **Kolom "puncak" adalah puncak 28 hari terakhir, BUKAN penggunaan hari
  ini**: angka 21/20 RPD dan 7/5 RPM menunjukkan bahwa batas pernah
  terlampaui, tetapi tidak menunjukkan kapan, oleh apa, atau apakah kuota hari
  ini sudah habis/direset. Untuk itu satu-satunya bukti adalah probe tunggal
  (`src/evaluation/probe_quota.py`). (Buku besar lokal sempat di-seed 21 dari angka ini;
  itu keliru, karena puncak bukan pemakaian hari itu.) Nama di AI Studio
  ("gemma-4-26b", "gemma-4-31b") dipetakan ke ID API di atas; pemetaan itu
  asumsi.
- **Reset kuota harian:** dokumentasi rate-limits: "Requests per day (RPD)
  quotas reset at midnight Pacific time"; batas berlaku **per proyek**, bukan
  per kunci. Tidak dinyatakan: apakah 429 ikut terhitung, dan apakah TPM Gemma
  dihitung sama. Waktu Pasifik ber-DST (AS): **September-awal November = PDT
  (UTC-7): reset 07:00 UTC = 14:00 WIB (UTC+7)**; sejak 1 Nov 2026 = PST
  (UTC-8): 08:00 UTC = 15:00 WIB; DST AS mulai lagi 14 Mar 2027. Indonesia
  tidak ber-DST, jadi jam reset dalam WIB bergeser satu jam dua kali setahun.
  Selalu hitung dari UTC: zona jam mesin dev ini berubah pada sesi yang sama
  (tercatat +08:00 Singapore Standard Time, lalu +07:00 SE Asia Standard
  Time), sehingga jam lokal tidak boleh dipakai untuk memutuskan "sudah
  reset"; jam sistem UTC cocok dengan header `Date` server Google. Kode
  menghitungnya dari `America/Los_Angeles` (uji: 06:59 UTC
  masih hari lama, 07:01 UTC hari baru; sebaliknya 07:59/08:01 UTC pada PST).
- **ID model diverifikasi dari dokumentasi resmi pada 2026-09-21:**
  `gemini-3.5-flash-lite` dan `gemini-3.1-flash-lite` (halaman models, diperbarui
  2026-09-17 UTC); Gemma 4 lewat Gemini API: `gemma-4-31b-it` dan
  `gemma-4-26b-a4b-it` (https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api;
  tidak tercantum di halaman models). Semuanya "Free of charge" pada halaman
  harga, dengan konten Free tier dipakai untuk meningkatkan produk Google.
- **`thinking_level` yang didukung** (https://ai.google.dev/gemini-api/docs/thinking,
  2026-09-21): `gemini-3.8-flash` low/medium/high (bawaan medium; **tidak ada
  minimal**); Flash Lite minimal/low/medium/high (bawaan **minimal**); Gemma 4
  hanya `high` (aktif) atau `minimal` (nonaktif). Kode menolak nilai tak
  didukung sebelum mengirim (`supported_thinking_levels`). Proyek ini memakai
  `medium` eksplisit untuk semua model Gemini agar perbandingan model tidak
  bercampur dengan perbedaan thinking; bawaan Flash Lite sendiri `minimal`.
- **SDK:** `google-genai` 2.24.0, memakai Interactions API
  (`client.interactions.create`) sesuai quickstart resmi; bentuk permintaan
  dan tipe respons (`output_text`, `status`, `usage.total_*_tokens`, galat
  `GenAiError`) diverifikasi terhadap paket terpasang. Klien Interactions di
  SDK itu berlabel versi preview (`2.4.1-preview.5`, v1beta). Terhadap
  server nyata: 5 panggilan pertama (kueri positif 1-5) berhasil pada
  percobaan pertama dengan skema terstruktur dan token tercatat, jadi
  integrasi dasarnya bekerja; kueri 6-8 kena 429 (lihat penanganan 429).

### Privasi data

Halaman harga menyatakan konten pada **Free tier digunakan untuk
meningkatkan produk Google** ("Used to improve our products": Yes; Paid: No).
Dapat diterima di proyek ini karena sumber datanya publik (artikel cek fakta),
tetapi klaim yang diketik pengguna juga terkirim. Perlu dipertimbangkan ulang
bila proyek ini kelak menangani data sensitif. Permintaan memakai
`store=False`; bila `store` dibiarkan bawaan, dokumentasi menyatakan
interaksi Free tier disimpan 1 hari.

### Retry internal SDK dan kuota harian

Retry internal SDK (3 retry per panggilan, tanpa log) **kemungkinan besar ikut
menghabiskan kuota harian**: percobaan live pertama mencatat 5 panggilan
sukses, sedangkan AI Studio menampilkan puncak 28 hari 21 dari 20 RPD dan 7
dari 5 RPM. Itu sesuai dengan permintaan tertolak (dan retry tersembunyi) yang
ikut terhitung, tetapi belum terbukti: puncak 28 hari tidak dapat dikaitkan ke
percobaan itu, dan dokumentasi tidak menyatakan apakah 429 terhitung. Jadi menonaktifkan retry internal (`disable_sdk_retry`) bukan hanya
soal kejujuran log, melainkan juga **anggaran kuota**: dengan RPD 20, satu
kueri yang gagal dulu bisa memakan 24 permintaan.

### Pengaman di kode (bukan di prompt)

Status verifikasi diambil dari label metadata, bukan dari LLM. Tautan rujukan
hanya dari metadata `references` (Aturan Wajib #3); URL apa pun pada keluaran
LLM dibuang dan dihitung. LLM hanya memilih `article_id` dari 3 kandidat; id
di luar kandidat ditolak dan dianggap "tidak cocok". Artikel tanpa `references`
tetap dijawab tanpa bagian rujukan. Konteks per artikel: judul, label,
tanggal, Narasi, Kesimpulan, rujukan; Penjelasan tidak dikirim.

### Hipotesis dan status

- **H1** (LLM yang membaca Narasi dapat membedakan klaim identik dari klaim
  bertetangga topik; gugur bila pada "vaksin flu bikin mandul" LLM
  merujuk artikel 36214): **dukungan awal pada `gemini-3.5-flash-lite` untuk
  satu kasus inti** (kueri itu dijawab tidak ditemukan; alasan: berbeda dari
  artikel vaksin HPV dan cacar air) [DIUKUR ULANG 2026-09-21] — **BERTAHAN**: pada data diperbaiki
  (skor retrieval 0,6671, kandidat 36214, 36577, 36053) LLM kembali menjawab tidak
  ditemukan dan alasannya sama (vaksin flu berbeda dari vaksin HPV, cacar air, dan
  vaksinasi-autisme). **Belum konklusif sampai diuji pada set uji** (satu kasus, pada set
  pengembangan); jangan digeneralisasi.
- **H3** (model kelas Flash cukup untuk tugas ini; gugur bila format terstruktur
  dilanggar berulang atau keliru pada >= 2 dari 10 kueri). **Kriteria dinilai
  terhadap ground truth (label yang ditetapkan manusia), bukan terhadap model
  lain.** Sempat dirumuskan ulang secara relatif ("Flash Lite cukup bila
  keputusannya sama dengan 3.8 Flash"); itu **kesalahan desain hipotesis**:
  kesetaraan dengan model pembanding bukan kebenaran (kesalahan yang sama tampak
  "setara"), dan hasilnya bergantung pada ketersediaan layanan pembanding.
  Status pada 10 kueri [DIUKUR ULANG 2026-09-21] — **BERUBAH sedikit**: pada data lama 10/10 benar; pada
  data diperbaiki **9/10 benar** (positif 4/5, negatif 5/5, 0 pelanggaran format). Kueri 3
  ("malaysia marah ke indonesia soal asap", skor retrieval 0,5739, rumusan paling samar)
  kini dijawab "tidak ditemukan"; sebelumnya benar (36729), dan 3.8 Flash juga menolaknya
  pada data lama. **Penyebabnya tidak dapat dipastikan**: satu proses per kondisi, jadi
  variasi acak LLM tidak terpisah dari efek data. Satu kesalahan dari 10 masih di bawah
  ambang H3 (gugur bila >= 2), tetap **terdukung terhadap ground truth**, **dengan catatan bahwa
  10 kueri itu adalah set pengembangan yang sudah dipakai berulang** (menyusun
  uji retrieval, uji generasi, dan keputusan desain), sehingga **tidak sah
  sebagai bukti mutu**. Bukti mutu hanya dari set uji yang dibekukan (lihat
  "Set uji Versi 1").
- **`gemini-3.8-flash` dihentikan (keputusan 2026-09-21)** karena
  ketidakstabilan layanan: 503 dan `APITimeoutError` di server, serta 429 yang
  muncul saat hitungan permintaan lokal masih di bawah batas harian 20 (penyebab
  429 tidak didiagnosis; diagnosis dihentikan atas keputusan). Baseline 3.8
  Flash tidak selesai (1 dari 10 kueri valid) dan perbandingan mutu tidak
  pernah terjadi: **hasil itu tidak boleh ditafsirkan sebagai 3.8 Flash lebih
  buruk dari Flash Lite.** `--compare` dipertahankan hanya sebagai alat
  informasi.
- **H4** (Gemma 4 dapat menjadi model juri RAGAS): **belum diuji sebagai
  juri**. Uji format JSON (`src/evaluation/gemma_json_check.py`, `gemma-4-31b-it`,
  thinking `minimal`, 3 prompt x 2 mode, 2026-09-21): 6/6 panggilan berhasil;
  mode skema server berfungsi (dokumentasi tidak menyebutnya) dan
  mengembalikan JSON murni 3/3 dengan bentuk sesuai 3/3; mode teks
  (tanpa skema, cara RAGAS) selalu dibungkus pagar ```json (0/3 JSON murni)
  tetapi valid setelah pagar dibuang 3/3 dan bentuk sesuai 3/3. Yang belum
  diketahui: apakah pengurai RAGAS menerima pagar itu, dan mutu penilaian
  (satu alasan mengandung salah ketik "dilarat"; bentuk verdict wajar).
  **Latensi 31-52 dtk per panggilan** walau prompt kecil (121-2521 token
  masuk, tanpa throttling), jauh lebih lambat daripada Gemini (Flash Lite
  ~4-10 dtk). Cukup TPM 16K per panggilan, tetapi waktu jam-dinding menjadi
  kendala (lihat "Perencanaan kapasitas"). Karena mode skema berfungsi, risiko
  format untuk H4 sebagian besar gugur; yang tersisa adalah latensi dan mutu
  penilaian. **RAGAS belum dipasang: menunggu set uji selesai.**
- Eksperimen thinking ditunda sampai set uji dibekukan dan generator final
  ditetapkan (jangan ubah dua variabel sekaligus). Selama ini semua hasil
  Gemini memakai `thinking_level=medium` eksplisit, bukan bawaan Flash Lite
  (`minimal`).
- **Hasil live 2026-09-21** (bukan evaluasi statistik; 10 kueri) [DIUKUR ULANG 2026-09-21]: bagian di
  bawah ini adalah hasil pada data LAMA (terduplikasi); hasil pada data diperbaiki ada di
  "Pengukuran ulang setelah perbaikan duplikasi".
  - `gemini-3.5-flash-lite` (thinking medium): 10/10 selesai tanpa 429/503,
    positif 5/5 (artikel dan label benar), negatif 5/5 "tidak ditemukan",
    0 pelanggaran format, 0 URL di luar metadata, latensi rata-rata 6,9 dtk.
    Kueri 3 ("malaysia marah ke indonesia soal asap", skor 0,5669) dijawab
    benar (36729).
  - `gemini-3.8-flash` (thinking medium): probe OK (6,8 dtk); baseline
    **hanya 1/10 valid** (kueri 1: 36730, benar). Kueri 2-5 gagal di API:
    `APITimeoutError` 90 dtk, lalu 503 (saran tunggu 30 dtk), lalu 429 berulang
    dengan saran tunggu 54-59 dtk yang klasifikasinya "tidak_diketahui" (isi
    galat tidak memuat quotaId per `classify_429`; **isi aslinya belum tercatat**
    karena log baru menyertakannya setelah kejadian). Kueri 6 tidak dikirim:
    buku besar lokal mencapai 20/20 (menghitung SEMUA percobaan, termasuk
    503/timeout/429, jadi mungkin melebihi hitungan server). Penyebabnya belum
    diketahui: bukan RPM dari sisi kita (percobaan berjarak >= 30 dtk) dan 429
    muncul saat hitungan lokal baru ~8-19 dari 20, tetapi apakah ini beban/
    kapasitas server ("actual capacity may vary") atau batas lain belum dapat
    dibedakan. Dihentikan (lihat di atas); `data/generation_eval_gemini-3.8-flash.jsonl`
    hanya memuat 1 kueri valid dan tidak dipakai.
  - Pemutus baru: evaluasi berhenti setelah 2 kueri beruntun gagal di API.
- **Ulangan diagnostik 2026-09-21** (`evaluation.repeat_eval`; murni diagnostik, tidak boleh dipakai
  untuk menyetel apa pun): 10 kueri set pengembangan x 5 run = 50 panggilan `gemini-3.5-flash-lite`
  (thinking medium) pada data diperbaiki. **Keputusan (verdict + artikel) identik pada semua 5 run
  untuk 10 dari 10 kueri** (0 gagal, 0 pelanggaran format); kueri 3 ditolak 5 dari 5 kali dengan
  alasan yang sama ("klaim pengguna hanya menyatakan kemarahan Malaysia soal asap secara umum,
  sedangkan artikel membahas klaim spesifik pelaporan ke PBB"). Yang bervariasi hanya redaksi
  alasan. Kandidat retrieval sama di semua run. Jadi selisih kueri 3 antara proses lama (diterima) dan
  proses baru (ditolak) kemungkinan besar efek data, bukan variasi acak; ini belum terbukti karena data
  lama tidak dapat dijalankan ulang. Batas atas 95% laju pembalikan keputusan (0 dari 50): ~6%, hanya
  untuk jenis kueri yang jelas; kueri batas belum terwakili.
  **Setelan sampling generator** (tidak diubah): `generation_config` hanya berisi `thinking_level`
  (medium) dan `max_output_tokens` (8192); temperature, top-p, top-k, dan seed TIDAK diatur, jadi
  default server. Dokumentasi Gemini 3 (https://ai.google.dev/gemini-api/docs/gemini-3): default
  temperature 1,0 dan "sangat disarankan" tidak diubah; menurunkannya dapat menyebabkan looping atau
  penurunan mutu pada tugas penalaran. Field `generation_config` klien Interactions terpasang
  (google-genai 2.24) tidak memuat temperature/top_p/top_k; ada `seed` (tidak dipakai; apakah server
  menghormatinya belum diverifikasi).
- Sampel evaluasi hanya 5 positif dan 5 negatif dan berstatus set
  pengembangan: indikasi, bukan bukti statistik.

### Perencanaan kapasitas (evaluasi 50 kueri)

Perkiraan, bukan pengukuran; angka kuota per 2026-09-21. Perkiraan token
per panggilan (generator) [DIUKUR ULANG 2026-09-21]: 2,2-3,6K token masuk pada data lama -> 1,7-2,1K pada
data diperbaiki (terukur pada 10 kueri; sekitar 20-40% lebih kecil). Perkiraan RAGAS di
bawah dibuat dari angka lama dan belum dihitung ulang (RAGAS belum dipasang); anggap terlalu
besar.

- **Generator Flash Lite** (RPD 500, RPM 15): 50 panggilan (terburuk 100 dengan
  percobaan ulang format) = **1 hari**, >= 3,4 menit menurut RPM (terukur:
  ~6,9 dtk per kueri). Ini generator Versi 1.
- (Dihentikan) generator 3.8 Flash: RPD 20 akan membutuhkan 3 hari; tidak
  ditempuh.
- **Juri Gemma 4** (TPM 16K, RPM 30, RPD 14,4K), bila H4 layak: RAGAS ~6-7
  panggilan/sampel, ~8-14K token masuk/sampel (perkiraan dari struktur metrik
  dan konteks kita; RAGAS belum terpasang dan tidak diperiksa), prompt
  terbesar ~3-4K << 16K. **Koreksi setelah pengukuran:** latensi Gemma 31-52
  dtk per panggilan (terukur, 6 panggilan) sehingga ~350 panggilan berurutan
  ~3-5 jam; TPM (~1-2 sampel/menit) bukan lagi pembatas, latensi yang
  membatasi. Dengan konkurensi ~4 (RPM 30 dan TPM 16K masih cukup) sekitar
  ~1 jam; keduanya masih perkiraan. Tetap **1 hari**, kuotanya terpisah dari
  generator.
- **Skenario realistis:** Flash Lite + juri Gemma = 1 hari. RAGAS belum
  dipasang; menunggu set uji selesai.

### Set uji Versi 1 (pedoman dikunci; butir belum dibuat)

Set uji 50 kueri untuk bukti mutu, terpisah dari 10 kueri pengembangan. Prinsip yang ditetapkan pemilik proyek:
10 kueri pengembangan tidak boleh masuk; setelah set uji dibekukan, prompt sistem dan logika generator tidak boleh
diubah berdasarkan hasilnya (bila perlu diubah, dibuat set uji baru); komposisi 20 positif + 20 negatif sulit + 10
negatif mudah (tetangga topik seperti "vaksin flu bikin mandul" lebih penting daripada negatif mudah); sebaran
positif mengikuti label dan kategori 150 artikel (dengan PARODI di-oversample); ragam gaya bahasa; setiap butir
ditinjau manual; enam artikel dikecualikan sebagai target (36730, 36737, 36729, 36738, 36731, 36214); sumber butir:
buatan model (Gemma 4 dari Narasi), buatan manusia, dan teks nyata (negatif dari arsip TurnBackHoax di luar 150
artikel, positif dari situs cek fakta lain, dengan URL asal dan data pribadi dibersihkan).

- **Pedoman anotasi** `testset/ANNOTATION_GUIDE.md` **v1.0, DIKUNCI 2026-09-21** (commit `2500013`, tag
  `annotation-guide-v1.0`), sebelum satu butir pun dibuat. Definisi "klaim sama": klaim inti artikel (KIA = judul;
  123 dari 150 artikel mengutipnya di Kesimpulan) dengan unsur inti (subjek, tindakan, objek pembeda), uji dua arah
  dan uji Kesimpulan, serta aturan kasus khusus (lebih umum, lebih spesifik, sebagian, sinonim, pertanyaan, ambigu).
  `tests/test_testset_locks.py` gagal bila pedoman atau prompt/skema berubah diam-diam. **Aturan: pedoman tidak
  boleh direvisi selama pembuatan set uji v1**; kasus tak tercakup dicatat di `testset/kasus_terbuka.md` dan
  diputuskan dengan aturan terdekat.
- **Pra-registrasi** `testset/v1.meta.json` (ditulis sebelum data): metrik utama = **keputusan modus dari 3 run**;
  kesepakatan antar-run dilaporkan per nilai `kekhususan`; **seed tidak dipakai sebagai jaminan determinisme**
  (efeknya belum diverifikasi); interval Wilson 95% di seluruh laporan; ambang H1 (negatif sulit "ditemukan"
  pada keputusan modus: <= 1 dari 20 terdukung, 2 tidak konklusif, >= 3 gugur) dan H3 (>= 5 kesalahan dari 50 atau
  pelanggaran format >= 2 gugur); laporan wajib: akurasi per tipe/kekhususan/sumber (buatan model vs teks nyata),
  Recall@3 retrieval terpisah, analisis per pasangan minimal termasuk jumlah pasangan yang DUA-DUANYA benar (ukuran
  paling langsung untuk H1).
- **Keterbatasan:** pelabelan dilakukan **satu anotator manusia**, sehingga kesepakatan antar-anotator tidak
  terukur (hanya konsistensi dalam-anotator: 10 butir acak dianotasi ulang setelah satu minggu). Pedoman ditulis
  setelah melihat keluaran model pada set pengembangan (risiko rasionalisasi; dibatasi oleh jangkar KIA yang sudah
  ada dan pengunciannya sebelum butir dibuat).
- **Prompt sistem diselaraskan dengan pedoman sebelum pembekuan** (commit `37fcac9`; keputusan pemilik proyek).
  Definisi resmi "klaim sama" kini tertulis di dalam sistem: bahan pembanding utama adalah KIA (Judul) dan unsur
  inti, Narasi hanya rujukan pendukung; uji dua arah, uji Kesimpulan, dan aturan kasus khusus; contoh baru
  (tingkat kekhususan) hanya dari enam artikel yang dikecualikan dan tanpa memakai teks 10 kueri pengembangan
  (diuji `tests/test_prompt.py`). Tidak ada verdict ketiga. Skema tetap empat bidang (deskripsi `klaim_sama`
  disesuaikan).
- **Pelabelan ulang kueri 3 pada set pengembangan** (disetujui pemilik proyek): "malaysia marah ke indonesia soal
  asap" diubah dari positif (target 36729) menjadi **negatif sulit dengan `kekhususan=umum`**. **Perubahan ini
  dilakukan SETELAH melihat keluaran model** (yang menolaknya 5 dari 5 kali dengan alasan "terlalu umum"), dengan
  dasar pedoman yang berjangkar pada KIA (tindakan inti "melaporkan ke PBB" tidak ada pada klaim pengguna; uji dua
  arah dan uji Kesimpulan gagal). **Hanya berlaku untuk set pengembangan**, bukan bukti mutu.
  Kode kini memisahkan **dua label** per kueri (`evaluation/devset.py`): `expected_retrieval_article` (artikel yang
  seharusnya terjangkau retrieval, untuk Recall@3) dan `expected_verdict` (`ditemukan` | `belum_ditemukan`,
  keputusan akhir yang seharusnya). Kueri 3: `expected_retrieval_article=36729`, `expected_verdict=belum_ditemukan`,
  `kekhususan=umum`. Format butir set uji v1 memakai struktur dua label yang sama.
- **Kueri 2 = `kekhususan=batas`** (keputusan pemilik proyek): "orang tua" ambigu terhadap "lansia" (lebih sering
  berarti ayah-ibu) dan **tidak diputuskan secara umum**, karena menetapkannya untuk seluruh set uji sama dengan
  merevisi pedoman yang terkunci. Butir serupa di set uji v1 diputuskan **per butir lewat uji Kesimpulan**. Butir
  batas dilaporkan terpisah dan tidak masuk hitungan utama (ringkasan `generation_eval` kini memisahkannya).
- **Dua jenis kesalahan dilaporkan terpisah** (`evaluation/metrics.py`, dipra-registrasi di `v1.meta.json`):
  **kecocokan palsu** (expected `belum_ditemukan` dijawab ditemukan), **penolakan palsu** (expected `ditemukan`
  dijawab belum ditemukan), dan **artikel salah**, masing-masing dengan interval Wilson 95%, terpisah untuk butir batas
  dan non-batas. Alasannya: prompt sistem yang lebih ketat cenderung menggeser kesalahan dari kecocokan palsu ke
  penolakan palsu, dan akurasi total saja menyembunyikan pergeseran itu.
- **Pemeriksaan regresi setelah perubahan prompt** (10 kueri set pengembangan, satu run, `gemini-3.5-flash-lite`;
  **hanya pemeriksaan regresi, tidak boleh dikutip sebagai bukti mutu**): keputusan berbeda pada **1 dari 10**
  dibanding modus 5 run sebelum perubahan. Kueri 2 ("ada link pendaftaran bantuan buat orang tua, itu beneran?")
  yang 5/5 ke 36737 kini "tidak ditemukan", dengan alasan "'orang tua' lebih umum, tidak menyebut 'lansia'".
  Itu persis kasus perbatasan yang ditandai pedoman (★ untuk 36737). Sembilan kueri lain identik (kueri 3 tetap
  ditolak; 0 pelanggaran format, 0 URL di luar metadata, 0 galat 429). Token masuk naik sekitar 700 per panggilan
  (prompt ~4,6 ribu karakter, sebelumnya ~2 ribu). Tidak ada perubahan setelan atau prompt berdasarkan hasil ini.
  Ringkasan `generation_eval` saat itu menyebut "H3 GUGUR (keliru 2/10)": itu hitungan mekanis dengan label lama
  kueri 3 dan tidak memisahkan butir batas; sudah diperbaiki (lihat pemisahan dua label di atas). Dengan label baru,
  satu-satunya selisih adalah kueri 2 (butir batas), sehingga pada butir non-batas tidak ada kesalahan.

### Pengumpulan kandidat set uji v1 (2026-09-21; belum ada kandidat yang ditinjau atau dijalankan)

Alat: `src/candidates/archive.py` (arsip TurnBackHoax di luar 150 artikel; jeda 1,5 dtk, timeout 45 dtk, cache
HTML mentah di `data/candidates_cache/`, tidak di-commit) dan `src/candidates/screen.py` (penyaringan terhadap
150 artikel: kemiripan judul, retrieval, penanda data pribadi; alat bantu, keputusan akhir manusia). Konten pihak
ketiga diperlakukan sebagai data, bukan instruksi.

- **Kepatuhan situs:** `turnbackhoax.id/robots.txt` mengizinkan semua (`Disallow:` kosong). **Kompas dan Tempo
  melarang agen Claude secara eksplisit** di robots.txt (`Disallow: /` untuk anthropic-ai, ClaudeBot, Claude-User,
  Claude-Web, Claude-SearchBot, dll.) dan **Komdigi membalas 403** pada klien otomatis. Ketiganya TIDAK diakses
  langsung (tanpa menyamar sebagai browser). **Keputusan pemilik proyek: judul dan URL hasil pencarian dari
  Kompas, Tempo, dan Komdigi juga TIDAK dipakai** (situs menolak agen AI, set uji akan diterbitkan publik, dan
  independensi judulnya rendah). Tidak ada judul atau URL dari situs-situs itu yang tersimpan di repositori atau
  `data/candidates/`. Positif dari situs cek fakta lain hanya dari situs yang `robots.txt`-nya tidak membatasi agen
  Claude; positif lintas situs otomatis yang tidak ada dilepas dan dicatat di `v1.meta.json`. Positif tulisan manusia:
  pemilik proyek menulis klaim setelah membaca artikel sebagai manusia (sumber `manusia`, URL sebagai asal-usul),
  dengan topik singkat sebagai pemandu, sehingga independensinya tidak penuh.
- **Arsip TurnBackHoax:** 100 artikel (10 halaman daftar tersebar, 2024-2026) di luar 150 artikel; disimpan teks
  Narasi + URL. 69 memuat blok kutipan pesan yang bersih (>= 25 karakter); 66 tanpa penanda data pribadi pada
  teks klaim (3 memuat URL yang harus dibersihkan). **Tidak ada satu pun yang klaimnya sama dengan artikel basis
  data** (kemiripan judul tertinggi 0,86; 0 di atas 0,90), jadi arsip tidak menghasilkan calon positif; ia menghasilkan
  calon NEGATIF: 18 dengan pola judul dan label sama dengan artikel basis data tetapi entitas berbeda (calon negatif
  sulit "pola sama, entitas beda", mis. "Lowongan Kerja SPX Express" vs "Puskesmas"), dan 16 dengan skor retrieval
  < 0,60 (calon negatif mudah). **Kelas otomatis tidak dapat dipercaya**: 20 kandidat ditandai
  "kemungkinan_sama" ternyata keluarga tautan penipuan dengan entitas berbeda, bukan klaim yang sama.
- **Uji awal lintas situs (dilepas):** dari 10 artikel basis yang dicoba lewat pencarian, kecocokan jelas 4, ambigu
  3, tidak ada 3, dan judulnya mirip judul basis data (kemiripan karakter 0,61-0,94): independensi rendah. Hasil itu
  tidak dipakai dan tidak disimpan.
- **Kelas usulan otomatis** penyaring disimpan di berkas terpisah (`archive_screen_class.jsonl`) dan tidak
  ditampilkan pada berkas tinjauan (bias anchoring); setelah tinjauan selesai dibandingkan dan kesepakatannya
  dilaporkan sebagai keandalan penyaring.
- **Data pribadi:** nama akun hanya pada kalimat pembuka Narasi (bukan pada teks klaim yang dikutip), jadi
  butir memakai teks klaim yang dikutip, bukan seluruh Narasi.

### Catatan untuk tahap evaluasi (RAGAS)

Model juri sebaiknya **berbeda** dari model generator agar penilaian tidak
bias terhadap keluarannya sendiri. Abstraksi penyedia membuat ini mudah:
cukup instansiasi penyedia kedua dengan `LLM_MODEL` lain.

**Koreksi independensi (2026-09-22):** Gemma dan Gemini bukan "keluarga
berbeda" dari generator, melainkan **model berbeda dari pengembang yang
sama** — keduanya dikembangkan Google dari riset yang berkaitan. Pemisahan
pembuat butir (Gemma), generator (Gemini Flash Lite), dan juri (kandidat:
Gemma) hanya **mengurangi**, bukan menghilangkan, risiko bias bersama (mis.
kecenderungan gaya jawaban atau kesalahan sistematis yang sama-sama
diwariskan dari data/RLHF Google). Berlaku juga untuk H4 di atas dan
untuk pembuat butir buatan_model di set uji v1.

### Duplikasi teks seksi (TERSELESAIKAN 2026-09-21)

Ditemukan saat menyusun generator: teks **Narasi dan Penjelasan di `articles.json`
terduplikasi** pada 150 dari 150 artikel (panjang JSON / panjang teks seksi HTML asli:
median 2,00; Kesimpulan 1,00). Penyebabnya `extract_sections()` mengiterasi elemen bersarang
(induk `div` dan anak `p`/`strong`) sehingga isinya tercatat dua kali.

Perbaikan (commit `b29d91c`): pohon HTML ditelusuri sekali secara berurutan, bukan membuang
duplikat sesudahnya. Artikel 36590 (Penjelasan bersarang di dalam Narasi) dan 36483 (Kesimpulan
bersarang di dalam Penjelasan) kini terpisah benar; 36603 diuji sebagai regresi (seksinya
memang normal setelah duplikasi hilang). Uji `tests/test_parser.py` kini gagal bila rasio
panjang hasil parse terhadap teks HTML asli melebihi 1,1 (atau di bawah 0,9). Hasil pada 150
artikel: rasio Narasi/Penjelasan median 1,00 (maks 1,00); 148 dari 150 artikel dalam 0,5% dari
1,0 (dua sisanya, 36590 dan 36483, wajar karena seksi HTML-nya memuat seksi bersarang);
Kesimpulan, `references`, dan kolom lain tidak berubah. `articles.json` di-parse ulang dari
cache (`python -m scraping.reparse`), indeks dibangun ulang dengan `ingest.py --rebuild` dan
diverifikasi segar (`evaluation.index_check`: id, teks, metadata identik; vektor sampel di-embed
ulang, kosinus 1,000000). Retriever kini membaca teks baru (panjang Narasi ~50% dari sebelumnya,
sama dengan `articles.json`).

### Pengukuran ulang setelah perbaikan duplikasi (2026-09-21)

Data lama = `articles.json` dan indeks sebelum perbaikan; data baru = sesudah perbaikan dan
`--rebuild`. Kolom terakhir menandai apakah temuan **bertahan** atau **berubah**.

| Ukuran | Lama | Baru | Temuan |
| --- | --- | --- | --- |
| Rasio panjang seksi (parse / HTML asli), median Narasi | 2,00 (1,62-2,29) | 1,00 (0,41-1,00) | berubah (cacat hilang) |
| idem, Penjelasan | 2,00 (1,62-2,74) | 1,00 (0,83-1,00) | berubah (cacat hilang) |
| idem, Kesimpulan | 1,00 | 1,00 | bertahan |
| Artikel dengan rasio > 1,1 | 150 (Narasi), 149 (Penjelasan) | 0 | berubah |
| Token median Narasi / Penjelasan / Kesimpulan | 270 / 450 / 61 | 137 / 225 / 61 | berubah (Kesimpulan bertahan) |
| Token p90 Narasi / Penjelasan | 454 / 807 | 228 / 369 | berubah |
| Token maks Narasi / Penjelasan | 1442 / 1187 | 422 / 573 | berubah |
| Chunk terpotong 512 token (Narasi / Penjelasan / Kesimpulan) | 11 / 58 / 0 (69 dari 450, 15,3%) | 0 / 3 / 0 (3 dari 450, 0,7%) | berubah |
| Seksi pemenang, top-1 chunk, 10 kueri (P / N / K) | 6 / 2 / 2 | 7 / 2 / 1 | bertahan (Penjelasan tetap teratas) |
| Seksi pemenang, top-5 chunk, 50 hasil (P / N / K) | 20 / 18 / 12 | 22 / 14 / 14 | bertahan (arah) |
| Artikel top-1 sama dengan sebelumnya | - | 9 dari 10 kueri | bertahan |
| Skor kasus vaksin flu (artikel teratas 36214) | 0,6508 | 0,6671 | bertahan (tetap di atas 3 dari 5 positif) |
| Positif terendah / negatif tertinggi | 0,5669 / 0,6508 | 0,5739 / 0,6671 | bertahan (skor tak memisahkan) |
| Flash Lite, 10 kueri (benar terhadap ground truth) | 10/10 | 9/10 (kueri 3 kini "tidak ditemukan") | berubah (penyebab tak terpastikan) |
| Flash Lite, kasus vaksin flu | tidak ditemukan | tidak ditemukan | bertahan |
| Flash Lite, token masuk per panggilan | 2,2-3,6K | 1,7-2,1K | berubah |
| Flash Lite, pelanggaran format / URL di luar metadata / 429 | 0 / 0 / 0 | 0 / 0 / 0 | bertahan |

Catatan: (1) "Seksi pemenang" pada 10 kueri (5 positif dan 5 negatif, set pengembangan) tidak
sebanding dengan angka 5 kueri di riwayat. (2) Pada data baru, kriteria 4 evaluasi generasi
menandai `36730.` pada kueri 1: LLM menyebut id artikel di kolom alasan; itu penanda heuristik,
bukan klaim tak berdasar. (3) Selisih kueri 3 berasal dari satu proses per kondisi; ulangan
akan memisahkan variasi acak dari efek data (belum dilakukan).

---

## Daftar Pekerjaan Sebelum Portofolio

Tidak mendesak dan tidak memengaruhi evaluasi, tetapi harus beres sebelum repositori ditampilkan:
IDE akan menampilkan garis merah pada siapa pun yang membukanya.

- **22 galat tipe pyright (mode standar) di `tests/`** (per 2026-09-21): `test_generator.py` 11 (mis.
  `ScriptedProvider` bukan turunan `LLMProvider`), `test_client.py` 7, `test_discovery.py` 3,
  `test_reparse.py` 1. Periksa dengan `npx pyright tests` (atau Pylance). `test_gemini.py` dan
  `_fakes.py` sudah bersih (pyright standar dan strict, mypy, ruff).
- **Gaya kode:** `ruff check` masih menandai urutan impor di `src/llm/limits.py` (I001).
- **Konfigurasi alat statis** (saran, belum dikerjakan): satu `pyproject.toml` untuk pyright/ruff agar
  IDE dan CI konsisten, termasuk jalur `src` dan `tests`.

---

## Keterbatasan yang Diketahui

Batasan berikut sudah disadari dan diterima. Jangan memperlakukannya
sebagai cacat yang perlu diperbaiki tanpa diminta.

- Basis pengetahuan hanya memuat hoaks yang **sudah** diverifikasi
  Mafindo. Klaim yang baru viral belum tentu ada di dalamnya, sehingga
  jawaban "belum ditemukan" adalah keluaran yang sah dan benar.
- Situs sumber diperbarui secara berkala, bukan real-time. Diperlukan
  scraping ulang secara terjadwal agar basis pengetahuan tetap mutakhir.
- Total artikel di situs sumber sekitar 15.000 (1.558 halaman × 10
  artikel). Scraping penuh memakan waktu berjam-jam karena latensi
  server. Tahap awal dibatasi 100–200 artikel terbaru.
- Jalur retry dan backoff belum teruji pada beban nyata. Selama scraping
  150 artikel server merespons stabil: tidak ada read timeout maupun
  connection error, sehingga tidak satu pun retry terpicu (hanya satu
  `ConnectionError` yang di-retry, pada pengambilan ulang satu artikel
  sesudahnya). Selebihnya jalur ini hanya diuji dengan session palsu di
  `tests/` (`test_client.py`). Server juga pernah membalas 200 OK dengan halaman
  galat ("Terjadi kesalahan saat mengambil data"); kasus ini ditangani
  validasi HTML sebelum caching, yang juga baru diuji dengan fixture.
- Embedding dibatasi ke **512 token** (`MAX_SEQ_LENGTH` di
  `src/chunker.py`) meski bge-m3 mendukung 8192. Alasan: mesin dev
  hanya berCPU dengan RAM bebas ~2,5 GB, sehingga batas pendek menekan
  memori dan waktu embedding; dan target pencocokan utama adalah seksi
  Narasi (median 270 token) yang mayoritas muat utuh. Terukur pada 450
  chunk (150 artikel) [DIUKUR ULANG 2026-09-21] — **BERUBAH**: pada data lama Narasi terpotong 11/150
  (7,3%), Penjelasan 58/150 (38,7%), Kesimpulan 0/150 (median Narasi 270 token); pada data
  diperbaiki Narasi **0/150**, Penjelasan **3/150 (2,0%)**, Kesimpulan 0/150 (median Narasi
  137, Penjelasan 225, Kesimpulan 61 token). Angka lama menghitung teks ~2x; alasan
  "mayoritas Narasi muat utuh" justru makin kuat. Chunk terpotong ditandai `truncated` pada
  metadata untuk audit. Bagian ekor Narasi/Penjelasan yang terpotong tidak
  ikut terindeks; keputusan ini perlu ditinjau ulang di Versi 2 (mengubah
  batas berarti embedding ulang semua chunk: `python src/ingest.py --rebuild`).
- Penyaringan `references` bersifat konservatif dan berbasis domain:
  semua tautan ke media sosial (Instagram, Facebook, TikTok, X/Twitter,
  Threads, YouTube), arsip, dan hosting gambar dibuang, tanpa membedakan
  postingan dari beranda akun. Akibatnya sebagian artikel (16 dari 150
  pada scraping awal) berakhir dengan `references` kosong padahal
  Referensi aslinya berisi tautan. Tautan yang dibuang tetap tersimpan di
  `references_raw` dan `references_filtered`.
- **Ditunda ke Versi 2:** penyaringan berbasis kredibilitas sumber yang
  lebih cerdas, termasuk membedakan akun resmi instansi (mis.
  `instagram.com/kemensetneg.ri/`) dari akun penyebar hoaks. Alasan
  keputusan: (1) percobaan meloloskan beranda akun ("Opsi 2") tidak
  menyelamatkan satu pun dari 16 artikel yang `references`-nya kosong,
  karena artikel-artikel itu hanya berisi postingan dan arsip; (2) 11
  beranda akun yang lolos tidak bisa diverifikasi dari sini (Instagram dan
  TikTok menyajikan halaman kosong/login untuk klien HTTP biasa), sehingga
  sebagian bisa saja akun penyebar hoaks, yang melanggar Aturan Wajib #1.
  Trade-off-nya dinilai merugikan, jadi dipilih penyaringan penuh per
  domain. Penilaian kredibilitas sumber memang bagian dari lingkup
  Corrective RAG.
