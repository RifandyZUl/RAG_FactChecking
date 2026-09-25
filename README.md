# Sistem RAG Verifikasi Klaim Berbahasa Indonesia

Sistem tanya-jawab berbasis *Retrieval-Augmented Generation* yang memeriksa
apakah sebuah klaim sudah pernah diverifikasi oleh pemeriksa fakta, lalu
mengembalikan status verifikasi, klarifikasi faktanya, dan tautan rujukan yang
sahih.

**Status:** Versi 1 selesai dan terukur. Versi 2 (Corrective RAG) belum dimulai.

---

## Daftar Isi

- [Masalah](#masalah)
- [Posisi dalam Literatur](#posisi-dalam-literatur)
- [Arsitektur](#arsitektur)
- [Keputusan Desain Utama](#keputusan-desain-utama)
- [Hasil Evaluasi](#hasil-evaluasi)
- [Keterbatasan](#keterbatasan)
- [Rencana Versi 2](#rencana-versi-2)
- [Cara Menjalankan](#cara-menjalankan)
- [Struktur Repositori](#struktur-repositori)
- [Rujukan](#rujukan)

---

## Masalah

Hoaks di Indonesia menyebar jauh lebih cepat daripada kemampuan orang
memverifikasinya. Sebagian besar klaim yang beredar sebenarnya **sudah pernah
diperiksa** oleh organisasi pemeriksa fakta, tetapi hasil pemeriksaan itu sulit
ditemukan: pencarian berbasis kata kunci gagal ketika pengguna menuliskan klaim
dengan bahasa sehari-hari yang berbeda dari judul artikel pemeriksaan fakta.

Sistem ini mencocokkan klaim yang ditulis pengguna dengan basis data artikel
pemeriksaan fakta secara semantik, bukan leksikal, dan menolak menjawab ketika
tidak ada klaim yang benar-benar sepadan.

---

## Posisi dalam Literatur

Tugas ini dikenal dalam riset sebagai **deteksi klaim yang sudah pernah dicek
fakta** (*detecting previously fact-checked claims*, juga disebut *claim
matching*), yang diperkenalkan Shaar dkk. (ACL 2020) dan menjadi tugas bersama
tahunan di CLEF CheckThat! Lab.

Tolok ukur baku pada bidang ini mendefinisikan tugasnya sebagai **pemeringkatan**:
diberikan sebuah klaim dan kumpulan klaim terverifikasi, urutkan sehingga yang
paling relevan berada setinggi mungkin, dengan metrik Success@K. Dataset
rujukannya dibangun dengan asumsi setiap klaim memiliki pasangan.

Proyek ini menguji dimensi yang tidak tercakup asumsi itu: **kemampuan sistem
menyatakan bahwa klaim tidak ada di basis data**, diukur secara eksplisit
menggunakan *negatif sulit* — klaim yang bertetangga topik tetapi bukan klaim
yang sama. Dimensi ini penting karena di dunia nyata sebagian besar klaim yang
beredar memang belum diperiksa.

> Catatan kejujuran: penempatan ini berasal dari penelusuran terbatas, bukan
> tinjauan pustaka sistematis. Klaim kebaruan apa pun perlu diverifikasi lebih
> dulu melalui pencarian sistematis.

---

## Arsitektur

### Jalur pengindeksan (luring, dijalankan berkala)

```
TurnBackHoax.id  →  Scraping & parsing  →  Chunking per seksi  →  Embedding
  150 artikel        seksi & tautan          450 chunk              BGE-M3 → ChromaDB
```

### Jalur kueri (setiap pertanyaan pengguna)

```
Klaim pengguna
      ↓
Retrieval  (BGE-M3 → ChromaDB, agregasi skor per artikel, top-3)     [kode]
      ↓
LLM        (Gemini 3.5 Flash Lite — memilih artikel atau menolak)    [LLM]
      ↓
Perakitan  (status & rujukan diambil dari metadata)                  [kode]
      ↓
Jawaban    (status verifikasi, klarifikasi, tautan rujukan)
```

Hanya satu dari lima tahap yang memakai LLM, dan tugasnya sempit: menilai
apakah klaim pengguna benar-benar sama dengan salah satu dari tiga artikel
kandidat. Status verifikasi, tautan rujukan, dan validasi pilihan ditangani kode
secara deterministik.

---

## Keputusan Desain Utama

**Chunking mengikuti struktur dokumen, bukan jumlah karakter.**
Artikel TurnBackHoax memiliki seksi baku (Narasi, Penjelasan, Kesimpulan,
Referensi). Setiap seksi menjadi satu chunk, sehingga peran tiap bagian tetap
terpisah: klaim yang beredar, proses penelusuran, dan faktanya.

**Tautan sumber hoaks dipisahkan dari rujukan sahih.**
Seksi Referensi pada artikel nyata ternyata memuat campuran keduanya — tautan
ke unggahan hoaks aslinya berdampingan dengan rujukan media kredibel. Keduanya
disimpan pada medan terpisah; hanya rujukan sahih yang ditampilkan ke pengguna.

**LLM tidak pernah menghasilkan URL.**
Tautan diambil dari metadata dokumen hasil retrieval. Model bahasa yang diminta
menuliskan URL dari ingatannya cenderung berhalusinasi.

**Status verifikasi berasal dari metadata, bukan dari LLM.**
LLM hanya boleh memilih `article_id` dari tiga kandidat; id di luar kandidat
ditolak dan diperlakukan sebagai "tidak ditemukan".

**"Belum ditemukan" adalah jawaban yang sah.**
Bila tidak ada klaim yang sepadan, sistem menyatakannya secara eksplisit alih-alih
memaksakan kecocokan.

---

## Hasil Evaluasi

Evaluasi dijalankan pada set uji 54 butir yang **dibekukan sebelum evaluasi**
(tag `testset-v1`), dengan sidik jari prompt dan kode generator dikunci
sehingga hasil hanya dinyatakan sah bila keduanya tidak berubah. Ambang
hipotesis dipra-registrasi sebelum data dibuat. Setiap butir dijalankan **tiga
kali**, dan keputusan modus dipakai sebagai metrik utama.

### Komposisi set uji

| Tipe | Jumlah | Keterangan |
| --- | --- | --- |
| Positif | 20 | Klaim yang ada di basis data |
| Negatif sulit | 20 | Bertetangga topik, bukan klaim yang sama (7 pola sama entitas beda, 7 entitas sama klaim beda, 6 angka/waktu beda) |
| Negatif mudah | 10 | Topik jauh dari basis data |
| Batas | 4 | Kasus ambigu, dilaporkan terpisah, tidak masuk metrik utama |

### Metrik utama

| Metrik | Hasil | Wilson 95% |
| --- | --- | --- |
| Akurasi (50 butir non-batas) | 48/50 | 0,865 – 0,989 |
| Akurasi butir batas (terpisah) | 3/4 | 0,301 – 0,954 |
| Kecocokan palsu (negatif dijawab ditemukan) | 1/30 | — |
| Penolakan palsu (positif dijawab belum ditemukan) | 1/20 | — |
| Artikel salah dipilih | 0/20 | — |
| Recall@3 retrieval (non-batas) | 36/40 | — |
| Pelanggaran format | 0/162 panggilan | — |
| URL di luar metadata | 0/162 panggilan | — |

### Status hipotesis

| Hipotesis | Status |
| --- | --- |
| **H1** — LLM yang membaca Narasi dapat membedakan klaim identik dari klaim yang sekadar bertetangga topik | Terdukung: 1/20 kecocokan palsu pada basis penuh, **1/17 pada basis benar-benar teruji** (ambang ≤1 pada keduanya) — lihat catatan di bawah |
| **H3** — Model kelas Flash Lite cukup untuk tugas ini | Terdukung pada sampel ini (2/50 kesalahan, 0 pelanggaran format) |

### Temuan terpenting: dua mode kegagalan yang terpisah

**Kegagalan retrieval (4 butir).** Artikel yang seharusnya dibandingkan tidak
masuk tiga besar — dua nyaris masuk (peringkat 4), dua jauh (peringkat 6 dan
19). Pada keempatnya jawaban akhirnya kebetulan benar, karena butirnya negatif
dan LLM memang menolak mencocokkan. Artinya pada 3 dari 7 butir subtipe "pola
sama entitas beda", generator **tidak pernah benar-benar diuji** membedakan
klaim: kandidatnya sudah tersingkir sebelum sampai ke LLM. Dukungan H1 karena
itu bertumpu pada 17 butir yang benar-benar teruji, bukan 20.

**Kegagalan penilaian generator (2 kesalahan + 6 keputusan tidak bulat
antar-run).** Pada seluruh kasus ini artikel yang benar **selalu tersedia** di
top-3, sehingga kegagalannya murni pada penilaian LLM, bukan retrieval.

Pemisahan ini memetakan langsung kebutuhan Versi 2.

### Caveat yang wajib dibaca bersama angka di atas

1. **Ketergantungan antar-butir.** 44% butir berbagi artikel jangkar (satu
   artikel dipakai hingga 4 butir), sehingga interval Wilson yang menganggap
   butir saling bebas bersifat terlalu percaya diri.
2. **Pasangan minimal sebagian hasil konstruksi.** Pada subtipe "angka atau
   waktu beda", seluruh butir sengaja diarahkan ke artikel yang sudah punya
   butir positif, sehingga angka pasangannya bukan hasil pengamatan.
3. **Confound sumber.** Subtipe "angka atau waktu beda" 100% buatan model;
   negatif mudah 0% buatan model. Pada kedua sel itu, efek sumber dan tipe butir
   tidak dapat dipisahkan.
4. **Ukuran sampel.** 50 butir non-batas hanya mampu mendeteksi kegagalan yang
   jelas; angka ini tidak mendukung klaim akurasi di atas 95%.

---

## Keterbatasan

**Hanya andal untuk klaim pendek (keterbatasan utama).** Retrieval hanya membaca
512 token pertama dari pesan pengguna (batas jendela embedding BGE-M3 yang
dipakai). Pada pesan yang panjang, klaimnya bisa terdorong keluar dari jendela
itu sehingga tidak ikut dicari sama sekali. Terukur pada 20 butir positif set uji
dengan teks pengganggu sintetis bergaya pesan berantai, dibagi ke depan dan
belakang klaim:

| Panjang pesan | Recall@3 (klaim di tengah) | Recall@3 (klaim di awal pesan) |
| --- | --- | --- |
| Klaim asli (48–582 karakter) | 20/20 | 20/20 |
| ~1.500 karakter | 19/20 | 19/20 |
| ~3.000 karakter | 19/20 | 19/20 |
| ~5.000 karakter | **2/20** | 19/20 |

Pada ~5.000 karakter, klaim berada di luar 512 token pada 18 dari 20 butir. Kondisi
pembanding (klaim di awal pesan, pengganggu di belakang) tetap 19/20, jadi
penyebabnya adalah pemotongan token, bukan sekadar panjang teks. Karena itu demo
membatasi masukan pada 1.500 karakter dan memperingatkan pengguna sejak ~220 token.
Teks pengganggunya sintetis, sehingga angka ini indikatif. Rincian:
`testset/retrieval_ablation_report.txt`.

**Cakupan basis pengetahuan.** Hanya memuat hoaks yang **sudah** diverifikasi.
Klaim yang baru viral akan dijawab "belum ditemukan" walaupun sebenarnya hoaks.
Jawaban itu sah, bukan kegagalan sistem.

**Rentang waktu sempit.** 150 artikel berasal dari Agustus–September 2026.

**Rujukan tidak selalu tersedia.** 16 dari 150 artikel tidak memiliki rujukan
sahih setelah tautan sumber hoaks disaring; jawaban untuk artikel tersebut
disusun tanpa bagian rujukan.

**Penyaringan rujukan bersifat konservatif.** Seluruh domain media sosial dan
arsip disaring, termasuk akun resmi instansi, karena kredibilitas sumber tidak
dapat diverifikasi secara otomatis pada Versi 1.

**Anotasi satu orang.** Seluruh label ditetapkan satu anotator manusia, sehingga
kesepakatan antar-anotator tidak terukur. Draf awal label tahap pertama dibuat
dengan bantuan LLM (ChatGPT, OpenAI) dan telah dilihat anotator sebelum label
final ditetapkan — tercatat lengkap di `testset/v1.meta.json`.

**Tier gratis.** Batas kuota penyedia dapat berubah tanpa pemberitahuan.
Lapisan penyedia dibuat agnostik agar model dapat ditukar tanpa mengubah
pipeline.

---

## Rencana Versi 2

Setiap komponen menargetkan kelemahan yang terukur di Versi 1, bukan mengikuti
tren arsitektur.

| Komponen | Menargetkan | Bukti dari Versi 1 |
| --- | --- | --- |
| **Query rewriter** — (1) ekstraksi inti klaim dari pesan panjang sebelum retrieval | Klaim terdorong keluar jendela 512 token | 18 dari 20 butir positif gagal Recall@3 pada pesan ~5.000 karakter (dampak paling terukur) |
| **Query rewriter** — (2) penulisan ulang kueri saat retrieval gagal | Kegagalan retrieval | 4 butir dengan artikel benar di luar top-3, dua di antaranya nyaris masuk (peringkat 4) |
| **Grader relevansi** | Kegagalan penilaian generator | 2 kesalahan + 6 keputusan tidak bulat, seluruhnya dengan artikel benar sudah tersedia di top-3 |
| **Penilaian kredibilitas sumber** | Penyaringan rujukan yang terlalu konservatif | Tidak ada temuan langsung dari evaluasi; berasal dari keterbatasan desain Versi 1 |

Evaluasi Versi 2 akan memakai set uji baru — set uji v1 sudah dibekukan dan
tidak boleh dipakai untuk mengarahkan perubahan prompt atau logika.

---

## Cara Menjalankan

### Prasyarat

- Python 3.11
- Kunci API Gemini (tier gratis) pada berkas `.env`

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1                                  # Windows PowerShell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # requirements.txt + pytest
copy .env.example .env          # lalu isi GEMINI_API_KEY
```

> **Jangan pakai `pip install` atau `python` tanpa jalur eksplisit ke `.venv`.**
> `Activate.ps1` mengubah `python`/`pip` di sesi PowerShell yang sama, tapi bila
> aktivasi tidak berhasil atau sesi berbeda, perintah itu diam-diam memasang
> paket ke Python global mesin (dipakai proyek lain juga) alih-alih ke `.venv`.
> Jalur eksplisit `.\.venv\Scripts\python.exe -m pip ...` selalu aman terlepas
> dari status aktivasi.

### Membangun basis pengetahuan

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m scraping              # ambil artikel → data/articles.json
.\.venv\Scripts\python.exe src\ingest.py --rebuild  # chunking + embedding → data/chroma/
.\.venv\Scripts\python.exe -m evaluation.index_check   # verifikasi indeks segar
```

### Menjalankan evaluasi

```powershell
$env:PYTHONPATH = "src"                             # wajib diatur ulang bila sesi baru
.\.venv\Scripts\python.exe -m evaluation.testset_eval      # 3 run pada set uji beku
.\.venv\Scripts\python.exe -m evaluation.testset_analysis  # hitung metrik (tanpa panggilan API)
```

### Menjalankan demo

Antarmuka Streamlit satu halaman (`src/app.py`) di atas pipeline yang sama
dengan yang dievaluasi; tidak ada logika retrieval atau generasi tambahan.
Butuh indeks di `data/chroma/` (lihat "Membangun basis pengetahuan") dan
`GEMINI_API_KEY` di `.env`.

Masukan dibatasi **1.500 karakter** (wilayah yang terukur bekerja; lihat
"Keterbatasan"). Sejak ~220 token (sekitar 1.000–1.300 karakter), demo menampilkan
peringatan **sebelum** pemeriksaan dan menyarankan menyalin inti klaimnya saja.
Kalau teks panjang ditempel lalu tombol langsung ditekan, klik pertama hanya
menampilkan peringatan; klik berikutnya baru menjalankan pemeriksaan.

```powershell
.\.venv\Scripts\python.exe -m streamlit run src\app.py   # dari root repositori
```

Di Command Prompt (cmd), perintahnya sama tanpa `.\` di depan:
`.venv\Scripts\python.exe -m streamlit run src\app.py`. Browser terbuka ke
`http://localhost:8501`; hentikan dengan Ctrl+C.

**Waktu muat pertama sekitar 67 detik** (terukur di mesin pengembangan, CPU):
pemeriksaan pertama sejak aplikasi dinyalakan memuat model embedding bge-m3.
Indikator proses menampilkan langkah yang sedang berjalan. Pemeriksaan
berikutnya sekitar 4 detik.

**Mode penguji** (bawaan mati) menampilkan panel "Detail untuk penguji":
kandidat hasil retrieval beserta skor kemiripan, alasan LLM, latensi, token,
dan jenis galat. Aktifkan dengan salah satu cara:

```powershell
$env:DEMO_TESTER_MODE = "1"          # variabel lingkungan (diutamakan), sesi PowerShell ini saja
```

atau buat `.streamlit/secrets.toml` (di-gitignore) berisi
`demo_tester_mode = true`. Nilai `1`/`true`/`ya`/`yes`/`on` menyalakan; nilai lain
atau tidak diatur berarti mati. `.env` tidak dibaca untuk setelan ini.

> **Kuota bersama dengan evaluasi.** Demo dan evaluasi berbagi kuota harian
> yang sama: 500 permintaan per hari untuk `gemini-3.5-flash-lite`, tercatat di
> `data/quota_ledger.json`, satu permintaan per pemeriksaan. Bila keduanya
> diperlukan di hari yang sama, **jalankan evaluasi lebih dulu**, agar evaluasi
> tidak berhenti di tengah karena kuota sudah terpakai demo.

### Menjalankan uji

```powershell
.\.venv\Scripts\python.exe -m pytest
```

> Semua perintah di atas dijalankan dan diverifikasi langsung di PowerShell
> (2026-09-23) dari root repositori ini. Sesuaikan bila struktur repositori
> berubah.

---

## Struktur Repositori

```
src/
  scraping/     pengambilan & parsing artikel, penyaringan tautan
  llm/          abstraksi penyedia, pembatas laju, buku besar kuota
  evaluation/   runner evaluasi, analisis metrik, pemeriksaan indeks
  candidates/   pengumpulan & penyaringan kandidat set uji
  chunker.py    pemotongan per seksi
  ingest.py     embedding & vector store
  retriever.py  pencarian + agregasi per artikel
  generator.py  penyusunan jawaban  [terkunci sejak tag testset-v1]
  presentation.py  data tampilan demo (tanpa Streamlit, teruji offline)
  app.py        demo Streamlit (adapter tipis)
  paths.py      jalur proyek terpusat (root, data/, cache, articles.json)
testset/
  v1.jsonl                   set uji beku (54 butir)
  v1.meta.json               pra-registrasi, penyimpangan, catatan analisis
  ANNOTATION_GUIDE.md        pedoman anotasi v1.0 (terkunci)
  GUIDE_LOCK.json            hash pedoman terkunci
  targets_v1.json            20 artikel target positif terpilih
  v1_analysis.json           hasil evaluasi (data terstruktur)
  v1_analysis_report.txt     hasil evaluasi (laporan terbaca)
  v1_temuan_untuk_v2.md      kelemahan terukur → komponen Versi 2
tests/
```

---

## Rujukan

1. Shaar, S., Babulkov, N., Da San Martino, G., & Nakov, P. (2020). *That is a Known Lie: Detecting Previously Fact-Checked Claims.* Proceedings of ACL 2020, 3607–3618.
2. Shaar, S., dkk. (2021). *Overview of the CLEF-2021 CheckThat! Lab Task 2 on Detecting Previously Fact-Checked Claims.* CEUR-WS Vol. 2936.
3. Lewis, P., dkk. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020.
4. Gao, Y., dkk. (2023). *Retrieval-Augmented Generation for Large Language Models: A Survey.* arXiv:2312.10997.
5. Chen, J., dkk. (2024). *M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation.* Findings of ACL 2024, 2318–2335.
6. Yan, S.-Q., dkk. (2024). *Corrective Retrieval Augmented Generation.* arXiv:2401.15884.

---

## Sumber Data

Basis pengetahuan berasal dari [TurnBackHoax.id](https://turnbackhoax.id)
(MAFINDO), organisasi pemeriksa fakta tersertifikasi IFCN. Sebagian butir set uji
diambil dari [Liputan6 Cek Fakta](https://www.liputan6.com/cek-fakta). Repositori
ini tidak mendistribusikan ulang isi artikel; hanya kutipan klaim dan tautan
sumber yang disimpan.

Proyek ini dibuat untuk keperluan pembelajaran dan portofolio, bukan sebagai
pengganti layanan pemeriksa fakta resmi.
