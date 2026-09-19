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
sedangkan tetangga yang salah bisa mencapai 0,688. Akibatnya
**Aturan Wajib #4 (menyatakan klaim belum ditemukan) tidak dapat
diwujudkan dengan ambang skor kemiripan yang sederhana.** Ini justifikasi
empiris kebutuhan node penilai relevansi (grader) di Versi 2.

### Pemuatan model: safetensors dari PR konversi #130

`transformers` 5.x menolak memuat `pytorch_model.bin` bila torch < 2.6
(CVE-2025-32434), sedangkan torch terpasang 2.5.1. Repo `BAAI/bge-m3`
hanya menyediakan `.bin` di branch `main`, sehingga model dimuat dari
varian safetensors milik PR konversi #130 (pembuat: `SFconvertbot`, akun
konversi otomatis Hugging Face) dengan `revision` dikunci ke hash commit
`9a0624b8…` (`MODEL_REVISION` di `src/ingest.py`). Yang **belum
terverifikasi**: PR itu belum di-review atau di-merge BAAI, dan kesamaan
numerik bobotnya dengan `.bin` belum dibandingkan. Yang cocok: ukuran
berkas, 391 tensor, dan 567,8 juta parameter. Embedding 450 chunk saat ini
dihasilkan dari bobot ini.

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
