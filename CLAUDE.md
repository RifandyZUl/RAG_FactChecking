# CLAUDE.md

Panduan konteks proyek untuk Claude Code. Baca berkas ini sebelum
mengerjakan tugas apa pun di repositori ini.

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
  sumber.

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
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\test_parser.py       # contoh menjalankan
.\.venv\Scripts\Activate.ps1                        # atau aktifkan dulu
```

Paket di `src/` (mis. `scraping`) dijalankan dari **root proyek** dengan
`PYTHONPATH=src`, sehingga jalur relatif tetap berbasis root:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m scraping     # menggantikan `python src\scraper.py`
```

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
│   │   └── pipeline.py   #   orkestrasi + CLI (python -m scraping)
│   ├── test_parser.py    # Uji parsing/retry/penyaringan dengan HTML nyata
│   ├── fixtures/         # HTML nyata untuk uji (di-commit)
│   ├── chunker.py        # Chunking per seksi + metadata (Aturan Wajib #2)
│   ├── ingest.py         # Embedding bge-m3 -> ChromaDB (idempoten)
│   ├── retriever.py      # Retrieval, diagregasi per article_id
│   ├── llm_provider.py   # Abstraksi penyedia LLM (Gemini) + retry/backoff
│   ├── generator.py      # Klaim -> retrieval -> LLM -> jawaban terstruktur
│   ├── test_generation.py # Evaluasi live 5 positif + 5 negatif (butuh .env)
│   └── test_retrieval.py # Verifikasi retrieval pada kueri sehari-hari
├── data/
│   ├── raw_html/         # Cache HTML mentah (tidak di-commit)
│   ├── articles.json     # Hasil scraping terstruktur (tidak di-commit)
│   └── chroma/           # Basis vektor ChromaDB (tidak di-commit)
├── requirements.txt
└── CLAUDE.md
```

---

## Konvensi Kode

- Bahasa komentar dan docstring: **Indonesia**
- Nama variabel dan fungsi: **Inggris**
- Sertakan *type hint* pada tanda tangan fungsi
- Tangani galat secara eksplisit; jangan menelan *exception* diam-diam
- Setiap perubahan pada logika parsing wajib diikuti menjalankan
  `src/test_parser.py`

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
  kuat.
- **Jelaskan keputusan desain.** Bila ada beberapa pendekatan, sebutkan
  pilihan yang diambil beserta alasan dan konsekuensinya.
- **Sampaikan ketidakpastian secara jujur.** Bila sesuatu belum
  terverifikasi, katakan demikian alih-alih menyajikannya sebagai fakta.

---

## Temuan Ingestion dan Retrieval (Versi 1)

> **PERINGATAN: angka di bagian ini, di "Hipotesis dan status", dan di
> "Keterbatasan" yang bertanda `[DIUKUR PADA DATA CACAT]` diukur pada teks
> Narasi/Penjelasan yang terduplikasi (150 dari 150 artikel; lihat "Masalah
> terbuka"), yaitu embedding, statistik token, pemotongan 512 token, seksi
> pemenang retrieval, skor kemiripan, dan konteks yang dikirim ke LLM. Semua
> itu TIDAK SAH sebagai temuan sampai diukur ulang setelah perbaikan duplikasi
> dan pengindeksan ulang. Perlakukan sebagai indikasi awal yang menunggu
> pengukuran ulang, bukan sebagai kesimpulan.**

Hasil pengujian pertama terhadap 450 chunk (150 artikel), memakai 5 kueri
berbahasa sehari-hari (`src/test_retrieval.py`). **Sampelnya baru 5
kueri**: cukup untuk sanity check dan menemukan masalah, bukan evaluasi
statistik.

### Penjelasan menang atas Narasi [DIUKUR PADA DATA CACAT]

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

### Skor kemiripan berdaya pisah rendah [DIUKUR PADA DATA CACAT]

Semua skor di bagian ini (termasuk 0,6508 pada kasus "vaksin flu bikin
mandul") berasal dari embedding teks terduplikasi; angkanya dapat berubah
setelah pengukuran ulang, dan kesimpulan tentang daya pisah skor belum sah.

Pada level artikel: kueri 2 memberi artikel benar 0,6227 dan artikel lain
0,6213 (selisih ≈ 0,001); kueri 5 memberi artikel lain 0,6877 melawan
artikel benar 0,6922. Skor artikel benar berkisar 0,567 sampai 0,692,
sedangkan tetangga yang salah bisa mencapai 0,688.

Uji kueri negatif (5 klaim yang tidak ada di basis data; ketiadaan
kata kunci diperiksa otomatis di `test_retrieval.py`) menambah bukti.
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

Kode: `src/llm_provider.py` (abstraksi penyedia), `src/generator.py`
(alur klaim -> retrieval 3 artikel -> LLM -> jawaban), `src/test_generation.py`
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

`test_generation.py` menulis hasil ke `data/generation_eval_<model>.jsonl` per
kueri, dapat dilanjutkan (kueri yang sudah punya hasil dilewati; `--force` untuk
mengulang), dan berhenti bila kuota harian habis. Opsi: `--model ID`,
`--check-budget` (hanya laporan anggaran, tanpa panggilan LLM), dan
`--compare DASAR KANDIDAT` (tabel keputusan berdampingan antarmodel, tanpa
panggilan LLM; hanya informasi kesetaraan keputusan dan BUKAN kriteria H3,
lihat "Hipotesis dan status").

**Throttling proaktif dan anggaran harian** (`src/rate_limit.py`): batas
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
(`src/probe_quota.py`, 1 permintaan), bukan dashboard.

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
  (`src/probe_quota.py`). (Buku besar lokal sempat di-seed 21 dari angka ini;
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
  artikel vaksin HPV dan cacar air) [DIUKUR PADA DATA CACAT]: kandidat retrieval (skor 0,6508)
  dan konteks yang dibaca LLM berasal dari data terduplikasi, sehingga
  dukungan ini menunggu pengukuran ulang. **Belum konklusif sampai diuji pada
  set uji** (satu kasus, pada set pengembangan); jangan digeneralisasi.
- **H3** (model kelas Flash cukup untuk tugas ini; gugur bila format terstruktur
  dilanggar berulang atau keliru pada >= 2 dari 10 kueri). **Kriteria dinilai
  terhadap ground truth (label yang ditetapkan manusia), bukan terhadap model
  lain.** Sempat dirumuskan ulang secara relatif ("Flash Lite cukup bila
  keputusannya sama dengan 3.8 Flash"); itu **kesalahan desain hipotesis**:
  kesetaraan dengan model pembanding bukan kebenaran (kesalahan yang sama tampak
  "setara"), dan hasilnya bergantung pada ketersediaan layanan pembanding.
  Status pada 10 kueri [DIUKUR PADA DATA CACAT]: **terdukung terhadap ground truth** (Flash
  Lite 5/5 positif dan 5/5 negatif benar, 0 pelanggaran format; diukur pada
  konteks terduplikasi, menunggu pengukuran ulang), **dengan catatan bahwa
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
  juri**. Uji format JSON (`src/test_gemma_json.py`, `gemma-4-31b-it`,
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
- **Hasil live 2026-09-21** (bukan evaluasi statistik; 10 kueri) [DIUKUR PADA DATA CACAT]:
  konteks yang dikirim ke LLM dan kandidat retrieval berasal dari teks
  terduplikasi; menunggu jalankan ulang setelah perbaikan dan pengindeksan ulang.
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
- Sampel evaluasi hanya 5 positif dan 5 negatif dan berstatus set
  pengembangan: indikasi, bukan bukti statistik.

### Perencanaan kapasitas (evaluasi 50 kueri)

Perkiraan, bukan pengukuran; angka kuota per 2026-09-21. Perkiraan token
per panggilan (2,2-2,6K masuk untuk generator; basis perkiraan RAGAS) [DIUKUR PADA DATA CACAT]:
konteks terduplikasi membuatnya membengkak; ukur ulang setelah perbaikan.

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

### Set uji Versi 1 (dalam perancangan; menunggu persetujuan pemilik proyek)

Set uji 50 kueri untuk bukti mutu, terpisah dari 10 kueri pengembangan.
Prinsip yang sudah ditetapkan pemilik proyek: 10 kueri pengembangan tidak boleh
masuk; setelah set uji dibekukan, prompt sistem dan logika generator tidak
boleh diubah berdasarkan hasilnya (bila perlu diubah, dibuat set uji baru);
komposisi mencakup positif, negatif sulit (tetangga topik, seperti "vaksin flu
bikin mandul"), dan negatif mudah; sebaran positif mengikuti label dan
kategori 150 artikel; ragam gaya bahasa (formal, percakapan, pesan berantai
WhatsApp, salah ketik); setiap butir ditinjau manual oleh pemilik proyek;
disimpan sebagai berkas bernomor versi dan di-commit. Rancangan rinci
(komposisi, prosedur, kuota) menunggu persetujuan; datanya belum dibuat.

### Catatan untuk tahap evaluasi (RAGAS)

Model juri sebaiknya **berbeda** dari model generator agar penilaian tidak
bias terhadap keluarannya sendiri. Abstraksi penyedia membuat ini mudah:
cukup instansiasi penyedia kedua dengan `LLM_MODEL` lain.

### Masalah terbuka (belum diperbaiki, menunggu persetujuan)

Ditemukan saat menyusun generator: teks **Narasi dan Penjelasan di
`articles.json` terduplikasi** pada 150 dari 150 artikel (panjang JSON /
panjang teks seksi HTML asli: median 2,00; Kesimpulan 1,00). Penyebabnya
`extract_sections()` mengiterasi elemen bersarang (induk `div` dan anak
`p`/`strong`) sehingga isinya tercatat dua kali. Artikel 36590 juga tidak
punya seksi Penjelasan terpisah di HTML, sehingga bagian Penjelasan ikut
masuk Narasi; 36603 dan 36483 menunjukkan awal Kesimpulan di Narasi/Penjelasan.
Dampak: statistik token dan pemotongan 512 token, embedding, dan angka
"Penjelasan menang atas Narasi" dihitung pada teks yang terduplikasi dan
perlu diukur ulang setelah perbaikan.

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
  `src/test_parser.py`. Server juga pernah membalas 200 OK dengan halaman
  galat ("Terjadi kesalahan saat mengambil data"); kasus ini ditangani
  validasi HTML sebelum caching, yang juga baru diuji dengan fixture.
- Embedding dibatasi ke **512 token** (`MAX_SEQ_LENGTH` di
  `src/chunker.py`) meski bge-m3 mendukung 8192. Alasan: mesin dev
  hanya berCPU dengan RAM bebas ~2,5 GB, sehingga batas pendek menekan
  memori dan waktu embedding; dan target pencocokan utama adalah seksi
  Narasi (median 270 token) yang mayoritas muat utuh. Terukur pada 450
  chunk (150 artikel) [DIUKUR PADA DATA CACAT]: Narasi terpotong 11/150 (7,3%), Penjelasan
  58/150 (38,7%), Kesimpulan 0/150; median token dan angka pemotongan dihitung
  pada teks terduplikasi (Narasi/Penjelasan tercatat ~2x) sehingga terlalu besar,
  dan alasan "mayoritas muat utuh" perlu diperiksa ulang. Chunk terpotong ditandai `truncated` pada
  metadata untuk audit. Bagian ekor Narasi/Penjelasan yang terpotong tidak
  ikut terindeks; keputusan ini perlu ditinjau ulang di Versi 2 (mengubah
  batas berarti embedding ulang semua chunk: `python src/ingest.py --force`).
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
