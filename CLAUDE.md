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

Tahap saat ini: modul ingestion (chunking, embedding, penyimpanan vektor)
sudah ditulis; scraping (`src/scraper.py`) selesai untuk 150 artikel.

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
│   ├── scraper.py        # Pengambilan & parsing artikel TurnBackHoax
│   ├── test_parser.py    # Uji parsing/retry/penyaringan dengan HTML nyata
│   ├── fixtures/         # HTML nyata untuk uji (di-commit)
│   ├── chunker.py        # Chunking per seksi + metadata (Aturan Wajib #2)
│   ├── ingest.py         # Embedding bge-m3 -> ChromaDB (idempoten)
│   ├── retriever.py      # Retrieval, diagregasi per article_id
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

Hasil pengujian pertama terhadap 450 chunk (150 artikel), memakai 5 kueri
berbahasa sehari-hari (`src/test_retrieval.py`). **Sampelnya baru 5
kueri**: cukup untuk sanity check dan menemukan masalah, bukan evaluasi
statistik.

### Penjelasan menang atas Narasi

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

### Skor kemiripan berdaya pisah rendah

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
  chunk (150 artikel): Narasi terpotong 11/150 (7,3%), Penjelasan 58/150
  (38,7%), Kesimpulan 0/150. Chunk terpotong ditandai `truncated` pada
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
