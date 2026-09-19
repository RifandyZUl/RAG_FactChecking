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

Tahap saat ini: penyempurnaan modul scraping (`src/scraper.py`).

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

Alasannya: pencarian semantik mencocokkan klaim pengguna dengan chunk
seksi **Narasi**, sementara jawaban yang ditampilkan diambil dari chunk
seksi **Kesimpulan** pada artikel yang sama. Pemotongan berbasis
karakter merusak logika ini karena satu chunk dapat berisi campuran
akhir Narasi dan awal Penjelasan.

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
│   └── test_parser.py    # Uji logika parsing dengan HTML tiruan
├── data/
│   ├── raw_html/         # Cache HTML mentah (tidak di-commit)
│   └── articles.json     # Hasil scraping terstruktur
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
