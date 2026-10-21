# Sistem RAG Verifikasi Klaim Berbahasa Indonesia

Sistem tanya-jawab berbasis *Retrieval-Augmented Generation* yang memeriksa
apakah sebuah klaim sudah pernah diverifikasi oleh pemeriksa fakta, lalu
mengembalikan status verifikasi, klarifikasi faktanya, dan tautan rujukan yang
sahih.

Proyek ini mencocokkan klaim yang beredar dengan artikel cek fakta TurnBackHoax.id lewat RAG (embedding
BGE-M3, basis vektor ChromaDB, generator Gemini): bila klaimnya pernah diperiksa, sistem menampilkan label,
klarifikasi, dan rujukan dari artikel itu. Sistem ini bukan pemeriksa fakta; ia tidak menilai sendiri
benar-salahnya klaim baru. Sistem diuji dengan set uji yang dibekukan dan dengan set eksternal 91 klaim
nyata dari Liputan6 Cek Fakta, dengan ambang lulus/gugur yang ditetapkan sebelum evaluasi dijalankan.
Hasilnya: pada klaim yang ada di basis data, ketepatannya memadai (36/46 = 78,3%, Wilson 95% [64,4%;
87,7%]), tetapi pada klaim yang tidak ada, sistem terlalu sering menampilkan artikel yang keliru (kecocokan
palsu 10/45 = 22,2% [12,5%; 36,3%], gugur), terutama pada penipuan berpola sama. Pelajaran utamanya: pada
penipuan yang berulang, definisi "klaim yang sama" belum cukup tajam, bahkan bagi penilai manusia.

**Status:** Versi 1 terukur pada indeks 150 artikel (`archive/v1`). Evaluasi eksternal pada indeks
produksi 1.532 artikel sudah selesai: ketepatan positif memadai (36/46 = 78,3%, Wilson 95% [64,4%;
87,7%]), kecocokan palsu gugur pada label resmi (10/45 = 22,2% [12,5%; 36,3%]), dan uji kemunduran
set uji v1 mundur pada angka utama (kemunduran bersih 5) tetapi tidak mundur setelah verifikasi (2).
Sistem belum siap menjadi pemicu langkah korektif bergaya CRAG, dan hasil "ditemukan" perlu diperiksa
ulang oleh pengguna; peringatan di demo menyatakan ini. Versi 2 (Corrective RAG) belum dimulai.
Rincian: [Hasil Evaluasi](#hasil-evaluasi).

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

Ada dua evaluasi yang dijalankan dengan generator, masing-masing pada indeks yang berbeda: **set uji v1**
pada indeks arsip 150 artikel (baseline Versi 1), dan **evaluasi eksternal** pada indeks produksi 1.532
artikel, yaitu indeks yang dipakai demo. Pada keduanya set uji dibekukan dan ambang ditetapkan sebelum
evaluasi dijalankan, prompt, generator, dan retriever dikunci dengan hash, dan setiap butir dijalankan
**tiga kali** dengan keputusan modus sebagai metrik utama. Generatornya `gemini-3.5-flash-lite` (thinking
medium). Semua proporsi disertai interval Wilson 95%.

### Ringkasan berdampingan

| Evaluasi | Indeks | Butir | Hasil |
| --- | --- | --- | --- |
| Set uji v1 (Versi 1, baseline) | `archive/v1`, 150 artikel | 50 non-batas | Akurasi **48/50** [86,5%; 98,9%]; Recall@3 36/40 |
| Set uji v1, uji kemunduran | produksi, 1.532 artikel | 44 non-batas (6 butir dikeluarkan karena labelnya tidak berlaku lagi) | Benar **37/44** = 84,1% [70,6%; 92,1%] vs 42/44 di arsip; **kemunduran bersih 5 -> MUNDUR** (ambang >= 3) |
| Set eksternal Liputan6, positif | produksi, 1.532 artikel | 46 | Ketepatan **36/46 = 78,3%** [64,4%; 87,7%] -> **memadai** (ambang: batas bawah >= 60%) |
| Set eksternal Liputan6, negatif | produksi, 1.532 artikel | 45 | Kecocokan palsu **10/45 = 22,2%** [12,5%; 36,3%] -> **gugur** (ambang: gugur bila batas bawah > 10%) |
| Set eksternal, retrieval | produksi, 1.532 artikel | 46 positif | Recall@3 bersyarat **41/46 = 89,1%** [77,0%; 95,3%] |

Angka produksi berlaku untuk indeks 1.532 artikel / 4.593 chunk yang dibekukan selama evaluasi, dengan
sidik jari tercatat (embedding `9851a6dc`, teks dan metadata `6283f0f6`;
[`docs/rancangan_evaluasi_eksternal.md`](docs/rancangan_evaluasi_eksternal.md) bagian 5). Indeks demo bisa
bertambah setelah pembaruan berkala, jadi angka ini tidak otomatis berlaku untuk indeks yang lebih besar.

Angka di tabel ini adalah angka resmi. Pemeriksaan label sesudahnya (adjudikasi dan verifikasi, di bawah)
dilaporkan sebagai sensitivitas dan tidak menggantikannya; aturan pemakaiannya ditetapkan sebelum berkasnya
diisi.

**Cara membaca:**
- Angka Versi 1 dan angka produksi **tidak sebanding langsung**: indeksnya berbeda (150 vs 1.532 artikel),
  jadi selisihnya mencampur efek data dan bukan uji arsitektur.
- **Recall@3 bersyarat** hanya dihitung pada pasangan yang memang terjangkau pencarian judul saat set
  disusun. Ia batas atas; Recall@3 atas seluruh klaim yang ada di TurnBackHoax tidak dapat diukur dari
  set ini. Sebagai pembanding tanpa LLM: kueri judul Liputan6 menemukan 44/46, kueri kutipan pesan 41/46.
- **"Lulus" pada kecocokan palsu berarti tidak terbukti buruk, bukan terbukti aman.** Di sini hasilnya
  gugur: interval seluruhnya di atas 10%.
- Hasil per butir evaluasi eksternal disegel sampai keandalan label dan label final di-commit.

### Baseline Versi 1 (set uji v1, `archive/v1`, 150 artikel)

Set uji 54 butir dibekukan sebelum evaluasi (tag `testset-v1`), dengan ambang hipotesis dipra-registrasi
sebelum data dibuat.

| Tipe | Jumlah | Keterangan |
| --- | --- | --- |
| Positif | 20 | Klaim yang ada di basis data |
| Negatif sulit | 20 | Bertetangga topik, bukan klaim yang sama (7 pola sama entitas beda, 7 entitas sama klaim beda, 6 angka/waktu beda) |
| Negatif mudah | 10 | Topik jauh dari basis data |
| Batas | 4 | Kasus ambigu, dilaporkan terpisah, tidak masuk metrik utama |

| Metrik (set uji v1, `archive/v1`) | Hasil | Wilson 95% |
| --- | --- | --- |
| Akurasi, 50 butir non-batas | 48/50 | 0,865 – 0,989 |
| Akurasi, 4 butir batas (terpisah) | 3/4 | 0,301 – 0,954 |
| Kecocokan palsu (negatif dijawab ditemukan) | 1/30 | — |
| Penolakan palsu (positif dijawab belum ditemukan) | 1/20 | — |
| Artikel salah dipilih | 0/20 | — |
| Recall@3 retrieval (non-batas) | 36/40 | — |
| Pelanggaran format | 0/162 panggilan | — |
| URL di luar metadata | 0/162 panggilan | — |

| Hipotesis | Status |
| --- | --- |
| **H1** — LLM yang membaca Narasi dapat membedakan klaim identik dari klaim yang sekadar bertetangga topik | Terdukung: 1/20 kecocokan palsu pada basis penuh, **1/17 pada basis benar-benar teruji** (ambang ≤1 pada keduanya) |
| **H3** — Model kelas Flash Lite cukup untuk tugas ini | Terdukung pada sampel ini (2/50 kesalahan, 0 pelanggaran format) |

**Dua mode kegagalan yang terpisah.** Empat kegagalan retrieval semuanya pada butir negatif, sehingga pada
3 dari 7 butir "pola sama entitas beda" generator tidak pernah benar-benar diuji (dasar angka 1/17 di atas).
Sebaliknya, pada semua kesalahan dan keputusan tidak bulat generator, artikel yang benar sudah ada di top-3.

**Caveat yang wajib dibaca bersama angka ini:**
1. **Ketergantungan antar-butir.** 44% butir berbagi artikel jangkar (satu artikel dipakai hingga 4
   butir), sehingga interval Wilson yang menganggap butir saling bebas bersifat terlalu percaya diri.
2. **Pasangan minimal sebagian hasil konstruksi.** Pada subtipe "angka atau waktu beda", seluruh butir
   sengaja diarahkan ke artikel yang sudah punya butir positif, sehingga angka pasangannya bukan hasil
   pengamatan.
3. **Confound sumber.** Subtipe "angka atau waktu beda" 100% buatan model; negatif mudah 0% buatan model.
   Pada kedua sel itu, efek sumber dan tipe butir tidak dapat dipisahkan.
4. **Ukuran sampel.** 50 butir non-batas hanya mampu mendeteksi kegagalan yang jelas; batas bawah Wilson
   86,5% tidak mendukung klaim bahwa akurasi pada set ini di atas 95%.

**Riwayat retrieval saat indeks diperluas** (tanpa LLM; Recall@k butir positif set uji v1, dari 20):

| Indeks | @1 | @3 | @5 | @10 | @20 |
| --- | --- | --- | --- | --- | --- |
| Arsip, 150 artikel | 19/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| Produksi, 922 artikel (2026-09-27) | 18/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| Produksi, 1.532 artikel (2026-10-03) | 18/20 | 20/20 | 20/20 | 20/20 | 20/20 |

Label negatif set uji v1 tidak otomatis berlaku pada indeks yang lebih besar: kini **sembilan** butir
negatif menemukan klaim yang sama di basis data 1.532 artikel (enam tercatat saat perluasan, tiga lagi
diverifikasi setelah evaluasi; lihat di bawah). Karena itu set uji v1 tetap sah sebagai baseline hanya pada
`archive/v1/`. Rincian: `testset/v1_analysis_report.txt`, `testset/v1_perbandingan_indeks_1532.json`,
`testset/v1_temuan_untuk_v2.md`.

### Set evaluasi eksternal

91 klaim nyata dari artikel cek fakta Liputan6 (dari 99; 8 kutipan yang hanya berisi tautan atau salam
dikeluarkan dengan aturan yang ditetapkan sebelum hasil dilihat). Kueri adalah kutipan pesan apa adanya,
seperti yang akan ditempel pengguna. **Positif** = id artikel TurnBackHoax yang memuat klaim yang sama,
**negatif** = tidak ada yang cocok di daftar 5-8 kandidat yang diperiksa. Teks pesan dan artikel Liputan6 tidak diterbitkan di repositori ini; yang
di-commit hanya id, label, dan keputusan per butir. Rancangan lengkap, ambang, dan hasil:
[`docs/rancangan_evaluasi_eksternal.md`](docs/rancangan_evaluasi_eksternal.md).

**Asal-usul label.** Semua label diputuskan pemilik proyek. Butir 1-5 putaran pertama dibahas bersama
asisten AI sebagai contoh cara mengisi. Sesudah putaran pertama, asisten AI memeriksa berkas terisi dan
menunjukkan aturan yang diterapkan tidak konsisten, tanpa mengubah label. Butir lain putaran pertama,
seluruh putaran kedua (asisten AI hanya membantu teknis berkas), sesi buta, adjudikasi, dan verifikasi
dikerjakan tanpa bantuan AI.

### Keandalan label

Hanya ada satu anotator, jadi yang diukur adalah konsistensi dalam-anotator, bukan kesepakatan
antar-anotator.

- **Uji ulang buta 30 butir acak** (jeda 7 hari, urutan diacak, label lama disembunyikan): kappa biner
  **0,634** [0,308; 0,911] (bootstrap 10.000 ulangan), kappa id persis 0,707 [0,416; 0,921]; 25 dari 30
  sama. Lima yang berubah semuanya soal ada/tidaknya pasangan, tidak ada yang berpindah ke artikel lain.
  Menurut ambang yang dikunci (0,60-0,79), setiap metrik juga dihitung dengan kelima butir itu dibalik ke
  dua arah; kategorinya tidak berubah.
- **Audit jejak identik** (tanpa LLM dan tanpa embedding) mencocokkan dua sinyal antara pesan dan setiap
  kandidat: (a) domain tautan hoaks yang sama, setelah pemendek URL, domain media sosial dan arsip, serta
  sumber tepercaya disaring; dan (b) rangkaian minimal 8 kata identik antara pesan dan Narasi artikel. 7
  butir negatif berjejak ditinjau ulang secara buta, dicampur dengan butir uji ulang. **4 dari 7 berubah
  menjadi cocok**, keempatnya ke artikel yang ditunjuk jejak itu. Label final memakai hasil ini, sehingga
  set menjadi 46 positif dan 45 negatif. Dengan label awal (42/49) kecocokan palsu justru lebih tinggi
  (14/49).

### Adjudikasi buta (sensitivitas)

Setelah segel dibuka, ke-20 butir yang keputusan sistemnya berbeda dari label ditinjau ulang oleh
pemilik proyek: dua pilihan per butir dalam urutan acak, tanpa keterangan mana pilihan sistem.

| Jenis | Butir | Ternyata kesalahan label | Tetap kesalahan sistem |
| --- | --- | --- | --- |
| Kecocokan palsu | 10 | 7 (2 di antaranya ditandai ragu) | 3 |
| Penolakan palsu | 9 | 3 | 6 |
| Artikel salah | 1 | 1 | 0 |

Angka resmi lebih dulu, lalu angka bila label diganti dengan hasil adjudikasi:

| | Positif benar | Kecocokan palsu |
| --- | --- | --- |
| **Label final (angka resmi)** | 36/46 = 78,3% [64,4; 87,7], memadai | 10/45 = 22,2% [12,5; 36,3], gugur |
| Batas yang menguntungkan sistem: adjudikasi, butir ragu tetap berlabel lama | 42/48 = 87,5% [75,3; 94,1], memadai | 5/43 = 11,6% [5,1; 24,5], tidak konklusif |
| Batas yang menguntungkan sistem: adjudikasi, butir ragu ikut adjudikasi | 44/50 = 88,0% [76,2; 94,4], memadai | 3/41 = 7,3% [2,5; 19,4], lulus |

- **Ini batas yang menguntungkan sistem, bukan perkiraan yang lebih akurat.** Hanya butir yang tidak
  sepakat yang ditinjau, jadi adjudikasi hanya bisa menggeser hasil ke arah sistem; kesalahan label pada
  butir yang sepakat tidak dicari. Nilai kecocokan palsu sebenarnya kemungkinan besar berada di antara batas
  ini dan angka resmi, tetapi tidak dijamin: kesalahan label pada butir yang sepakat tidak diperiksa, dan
  sebagian kesalahan semacam itu (misalnya butir berlabel positif yang sebenarnya negatif) justru akan
  menaikkan kecocokan palsu di atas angka resmi. Selain itu penilai yang diperlihatkan dua opsi bisa
  cenderung menerima opsi yang tampak masuk akal, sehingga adjudikasi sendiri berpotensi bias ke arah
  sistem.
- Kategori terburuk pada batas ini: positif **memadai**, kecocokan palsu **tidak konklusif**. Bahkan di
  batas ini kecocokan palsu tidak lulus dengan kokoh: "lulus" hanya tercapai kalau kedua butir ragu
  dihitung ke arah sistem, dengan batas atas 19,4%, tepat di bawah patokan 20%.
- Satu kecocokan palsu mengarah ke artikel di luar daftar kandidat yang dulu diperiksa. Adjudikasi
  menyatakannya bukan klaim yang sama (tokohnya berbeda), jadi itu tetap kesalahan sistem.
- Temuan yang lebih penting dari angkanya: **pada butir yang sulit, label sendiri tidak stabil** (lihat
  [Keterbatasan](#keterbatasan)).

### Verifikasi testset-v1 (sensitivitas)

Tiga butir negatif set uji v1 dijawab "ditemukan" pada indeks 1.532 karena ada artikel baru yang
dicocokkan sistem. Pemilik proyek membaca ketiga pasangan itu sendiri: **ketiganya memuat klaim yang
sama**. Jadi label negatifnya tidak berlaku lagi pada indeks besar, dan ketiga butir itu bukan kesalahan
sistem.

- Angka resmi tetap **kemunduran bersih 5/44, MUNDUR**. Dengan ketiga butir dikeluarkan (sensitivitas),
  kemunduran bersih menjadi **2 dari 41 -> tidak mundur** (ambang >= 3).
- Dua kemunduran yang tersisa nyata: dua butir positif kini ditolak walau artikel yang benar ada di
  top-3.
- Berkas set uji v1 tidak diubah; status ketiga butir hanya dicatat di `testset/v1.meta.json`.

### Pola kegagalan utama

- **Kecocokan ke artikel berpola sama dengan unsur inti berbeda** (10 dari 45 negatif, angka resmi).
  Sembilan dari sepuluh adalah artikel peringkat 1 retrieval, umumnya tautan penipuan dengan pola yang
  sama tetapi lembaga, tokoh, atau programnya berbeda; delapan bulat di ketiga run. Kesalahannya stabil,
  bukan acak. Menurut adjudikasi, 7 dari 10 adalah kesalahan label (batas yang menguntungkan sistem),
  tetapi itu tidak cukup untuk membuat kategorinya lulus.
- **Penolakan pasangan lintas gelombang** (6 dari 10 kegagalan positif). Pada pasangan yang terbit
  terpaut lebih dari 30 hari, ketepatan 11/18, dibanding 25/28 pada yang <= 30 hari. Label mengikuti
  aturan "lembaga dan tawaran yang sama = cocok walau gelombangnya berbeda", sedangkan prompt generator
  tidak mengenal aturan itu. Penolakan palsu lebih tahan adjudikasi: 6 dari 9 tetap kesalahan sistem.
- Separuh kegagalan positif (5 dari 10) terjadi di retrieval (artikel yang benar tidak masuk top-3),
  separuh di penilaian LLM.

Kemampuan mengenali klaim yang tidak ada di basis data saat ini **belum cukup** untuk memicu langkah
korektif bergaya CRAG (mencari ke situs cek fakta lain): menurut angka resmi sekitar satu dari lima klaim
semacam itu tidak akan pernah sampai ke langkah tersebut karena sistem sudah menampilkan artikel yang
keliru, dan bahkan pada batas yang menguntungkan sistem hasilnya baru tidak konklusif.

### Kepatuhan aturan wajib

- **Tautan tidak dikarang LLM:** 0 URL dari LLM yang tampil ke pengguna. Pada keluaran mentah ditemukan
  4 URL yang tidak berasal dari metadata rujukan (2 di set eksternal, 2 di set uji v1 pada indeks
  1.532). Keempatnya berdomain `.go.id`, tersalin dari teks seksi artikel kandidat (bukan karangan
  model), dan dibuang sebelum jawaban disimpan atau ditampilkan.
- **Format:** 0 pelanggaran format terstruktur pada 274 panggilan set eksternal dan 162 panggilan set uji
  v1 pada indeks 1.532.

### Perubahan tampilan setelah evaluasi

Sejak 2026-10-21 demo menampilkan peringatan pada setiap hasil "ditemukan": pengguna diminta memastikan
sendiri bahwa tokoh, lembaga, dan program di artikel sama dengan pesan yang diperiksa, dengan judul dan
tanggal artikel di dekatnya. Ini perubahan tampilan saja; **angka di atas mengukur keputusan generator dan
tidak terpengaruh olehnya.**

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

**"Sudah diperiksa" sering berarti "pola ini pernah dinyatakan palsu".** Pada
pengukuran celah terhadap Liputan6 Cek Fakta (`docs/rancangan_v2.md` bagian 11.8),
21 dari 25 pasangan cocok di putaran kedua adalah PENIPUAN, dan 14 dari 25 terpaut
lebih dari 30 hari dari artikel Liputan6-nya (semuanya PENIPUAN): tautan penipuan
berulang dengan lembaga dan jenis tawaran yang sama, tetapi dari gelombang lain.
Jadi cakupan TurnBackHoax untuk hoaks semacam itu banyak berupa artikel yang
membantah pola yang sama, bukan pemeriksaan atas pesan yang sama persis; tanggal,
tautan, dan rincian pesan yang ditempel pengguna bisa berbeda dari artikel yang
ditampilkan.

**Pesan yang hanya berisi tautan tidak ditangani.** Pengguna nyata bisa menempel
tautan saja (5 dari 99 kutipan pesan pada sampel Liputan6). Sistem tidak membuka
tautan dan hanya meng-embed teks URL-nya, jadi pesan seperti itu hampir pasti
dijawab "belum ditemukan"; evaluasi eksternal mengeluarkannya
(`docs/rancangan_evaluasi_eksternal.md` bagian 2.2). Pencocokan URL/domain
deterministik ke sumber hoaks yang tercatat di artikel, tanpa LLM, dicatat sebagai
fitur masa depan dan belum dibangun.

**Rentang waktu.** Basis data baseline Versi 1 (150 artikel) berasal dari
Agustus–September 2026. Basis data demo, yang juga dipakai evaluasi eksternal, memuat 1.532 artikel dari
30 September 2025 sampai 27 September 2026; hoaks di luar rentang itu tidak tercakup, dan artikel
yang sudah diambil tidak disegarkan bila diperbarui di sumbernya.

**Rujukan tidak selalu tersedia.** Pada basis data demo, 205 dari 1.532 artikel
tidak memiliki rujukan yang boleh ditampilkan setelah penyaringan (16 dari 150 pada
basis data baseline Versi 1, dengan aturan saat itu); jawaban untuk artikel tersebut
disusun tanpa bagian rujukan.

**Penyaringan rujukan bersifat konservatif.** Seluruh domain media sosial, arsip,
hosting gambar, dan pemendek URL disaring, termasuk akun resmi instansi dan tautan
pendek yang sebenarnya sah, karena kredibilitas sumber tidak dapat diverifikasi
secara otomatis pada Versi 1 dan tujuan tautan pendek tidak dapat diperiksa sebelum
diklik. Tautan pada baris "Sumber:" artikel (sumber klaim yang diperiksa) tidak
ditampilkan sebagai rujukan, kecuali situs pemerintah (`.go.id`) dan media/cek
fakta pada daftar eksplisit di `src/scraping/links.py`; pengecualian `.go.id`
membawa risiko karena situs pemerintah dapat diretas. Rujukan disaring dua kali:
saat artikel di-parse dan sekali lagi saat akan ditampilkan di demo.

**Klarifikasi bisa tipis.** Klarifikasi disusun dari seksi Kesimpulan artikel.
Pada artikel September–November 2025, Kesimpulan umumnya hanya satu kalimat yang
menyatakan klaimnya palsu, tanpa uraian fakta.

**Anotasi satu orang.** Seluruh label ditetapkan satu anotator manusia, sehingga
kesepakatan antar-anotator tidak terukur. Draf awal label tahap pertama dibuat
dengan bantuan LLM (ChatGPT, OpenAI) dan telah dilihat anotator sebelum label
final ditetapkan — tercatat lengkap di `testset/v1.meta.json`. Untuk set eksternal, asal-usul label
(termasuk bagian yang dibahas bersama asisten AI) ada di [Set evaluasi eksternal](#set-evaluasi-eksternal).

**Label manusia pada penipuan berpola sama tidak stabil.** Pada evaluasi eksternal, kappa biner uji
ulang 0,63 dengan interval lebar [0,31; 0,91], 11 dari 20 pilihan adjudikasi berbeda dari label final,
dan satu butir dinilai tiga kali dengan hasil berbeda. Karena itu tingkat kecocokan palsu sebenarnya
kemungkinan besar berada di antara batas yang menguntungkan sistem (5/43 = 11,6% [5,1%; 24,5%]) dan angka
resmi (10/45 = 22,2% [12,5%; 36,3%]), tetapi tidak dijamin (lihat
[Adjudikasi buta](#adjudikasi-buta-sensitivitas)), dan definisi "klaim yang sama" untuk penipuan berulang perlu
dipertajam sebelum pengukuran berikutnya.

**Batas evaluasi eksternal.** Adjudikasi hanya meninjau butir yang tidak sepakat, dan anotator tahu
setiap butirnya adalah ketidaksesuaian, jadi hasilnya berat sebelah ke arah sistem. Recall@3 bersyarat
adalah batas atas. Label negatif hanya berlaku terhadap daftar kandidat yang diperiksa, bukan seluruh
basis data. Prompt generator tidak mengenal aturan lintas gelombang yang dipakai label. Uji kemunduran
pada indeks produksi mencampur efek data dengan efek sistem, dan label negatif set uji v1 tidak otomatis
berlaku saat basis data membesar. Dua berkas label tercatat tidak bersih (satu berkas tertimpa koreksi
salah ketik; satu berkas adjudikasi ditolak lalu diperbaiki formatnya oleh anotator sendiri, hanya enam
sel yang berubah); keduanya tercatat di `docs/rancangan_evaluasi_eksternal.md` bagian 7.2 dan 7.8.

**Tier gratis.** Batas kuota penyedia dapat berubah tanpa pemberitahuan.
Lapisan penyedia dibuat agnostik agar model dapat ditukar tanpa mengubah
pipeline.

---

## Rencana Versi 2

Rancangannya ada di [`docs/rancangan_v2.md`](docs/rancangan_v2.md); belum ada kode. Rencana awal
(Corrective RAG lengkap: penulis ulang kueri, grader relevansi, penilaian kredibilitas sumber)
**dipersempit** setelah tiap komponen diperiksa terhadap buktinya. Sebuah komponen masuk hanya bila
masalahnya terukur.

| Komponen | Status | Bukti |
| --- | --- | --- |
| **Penanganan pesan panjang** (klaim terdorong keluar jendela 512 token) | Masuk, **menunggu pengukuran pada pesan berantai asli** | Mekanismenya terukur: Recall@3 butir positif pada pesan ~5.000 karakter 2/20 (150 artikel) dan 0/20 (1.532 artikel), tetapi teks pengganggunya sintetis; besar dampaknya pada pesan nyata belum diketahui |
| **Pengukuran kebersihan rujukan** | Masuk | Evaluasi Versi 1 tidak pernah mengukur kebersihan rujukan yang berasal dari data |
| Penulisan ulang kueri saat retrieval gagal | **Dicoret** | Tidak ada bukti masalah: empat kegagalan Recall@3 Versi 1 seluruhnya butir negatif (yang di luar tiga besar adalah artikel tetangga); untuk butir positif Recall@3 20/20 pada semua ukuran indeks |
| Grader relevansi | **Tidak masuk** | Masalah terbukti (kecocokan palsu ke artikel berpola sama dengan unsur inti berbeda); solusi belum diuji |
| Penilaian kredibilitas sumber oleh LLM | **Tidak masuk** | Semua dokumen berasal dari satu sumber; masalah rujukan ditangani dengan aturan penyaringan yang dapat diaudit |

Dari evaluasi eksternal, yang perlu diperbaiki lebih dulu, berurutan:

1. **Pemeriksaan unsur inti** (subjek/lembaga, tindakan, objek pembeda) sebelum sistem menyatakan
   "ditemukan". Ambang skor kemiripan sudah tiga kali terbukti tidak memisahkan klaim yang sama dari
   tetangganya, jadi pemeriksaannya harus eksplisit. Kriterianya perlu cukup tegas untuk juga dipakai
   sebagai pedoman label, karena label pada kasus yang sama terbukti tidak stabil.
2. **Kebijakan lintas gelombang**, diputuskan bersama butir 1: menerima pasangan lintas gelombang bisa
   memperbaiki sebagian penolakan, tetapi berisiko menambah kecocokan palsu pada penipuan berpola sama.
3. **Uji pada sampel baru** dari periode lain, dengan ambang dikunci sebelum dijalankan. Set 99 butir
   Liputan6 sudah dipakai sekali dan tidak boleh dipakai lagi untuk menilai perbaikan.

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

# evaluasi eksternal (indeks produksi; butuh berkas label lokal yang tidak di-commit)
.\.venv\Scripts\python.exe -m evaluation.external_eval --set liputan6 --run 1   # satu run; --status untuk status teknis
.\.venv\Scripts\python.exe -m evaluation.external_analysis --metrik            # metrik (tanpa panggilan API)
```

Evaluasi yang hasilnya akan **dibandingkan dengan baseline Versi 1** wajib memakai
indeks arsip (bagian berikut), bukan indeks utama yang akan diperluas.

### Arsip indeks Versi 1

`archive/v1/` berisi salinan indeks ChromaDB dan `articles.json` (150 artikel,
450 chunk, ~9,5 MB) persis seperti saat Versi 1 dievaluasi. Tujuannya agar
evaluasi Versi 1 tetap dapat direproduksi setelah basis data diperluas, dan agar
Versi 2 dapat dievaluasi pada data yang sama, sehingga perbedaan hasil murni
karena arsitektur. Arsip **tidak di-commit**: isinya teks artikel pihak ketiga,
dan ChromaDB menulis ulang berkasnya setiap kali dibuka. Sidik jari **isinya**
(bukan hash berkas) tercatat di `testset/v1.meta.json`
(`arsip_indeks_v1_2026-09-25`).

Memakai arsip, tanpa mengubah kode:

```powershell
$env:PYTHONPATH = "src"
$env:RAG_INDEX_DIR = "archive/v1"
.\.venv\Scripts\python.exe -m evaluation.index_check --expect-v1-archive   # wajib lolos (kode 0)
.\.venv\Scripts\python.exe -m evaluation.testset_eval                      # atau skrip lain
Remove-Item Env:RAG_INDEX_DIR                                              # kembali ke data/
```

**Bila arsip hilang, bangun ulang dari daftar artikel.** Yang ter-commit hanya
`archive/v1/article_ids.json`: id, URL, judul, label, kategori, dan tanggal ke-150
artikel, dalam urutan arsip. `articles.json` sengaja tidak di-commit karena memuat
teks hoaks apa adanya, termasuk nomor dan tautan penipuan.

1. Pulihkan `archive/v1/articles.json` lewat scraping ulang berdasarkan daftar
   URL itu. Artikel diambil dari cache `data/raw_html/` bila ada, dan dari situs
   sumber bila tidak (timeout 45 dtk, retry, jeda 1,5 dtk). Proses gagal tanpa
   menulis berkas bila ada artikel yang tidak dapat dipulihkan:

   ```powershell
   $env:PYTHONPATH = "src"
   .\.venv\Scripts\python.exe -m scraping.restore archive\v1\article_ids.json --out archive\v1\articles.json
   ```

2. Bangun ulang indeksnya. `ingest` menolak menulis ke `archive/` tanpa
   `--allow-archive`:

   ```powershell
   $env:PYTHONPATH = "src"
   .\.venv\Scripts\python.exe src\ingest.py --rebuild --articles archive\v1\articles.json --chroma-dir archive\v1\chroma --allow-archive
   ```

3. Verifikasi:

   ```powershell
   $env:RAG_INDEX_DIR = "archive/v1"
   .\.venv\Scripts\python.exe -m evaluation.index_check --expect-v1-archive
   .\.venv\Scripts\python.exe -m evaluation.retrieval_ablation --out-json cek.json --out-report cek.txt
   ```

   `sha256_teks_metadata` dan `sha256_articles_json_isi` harus cocok persis, dan
   `cek.json` harus identik dengan `testset/retrieval_ablation.json` (selain
   tanggal). Prosedur ini sudah diuji (2026-09-25, mesin
   pengembangan, ke direktori sementara): keenam sidik jari cocok, **termasuk byte
   embedding**, dalam ~8 menit di CPU. Pada mesin atau versi pustaka lain,
   `sha256_embedding_float32` bisa berbeda di digit presisi. Dalam kasus itu,
   kesetaraan dibuktikan lewat kosinus `index_check` dan ablasi yang identik.

Pemulihan dari cache sudah diuji (2026-09-26): `scraping.restore` menghasilkan
`articles.json` dengan `sha256_articles_json_isi` identik dengan yang tercatat.
Jalur jaringan belum diuji.

**Keterbatasan pemulihan lewat scraping ulang:**

- Bergantung pada artikel yang **masih tersedia** di situs sumber. Artikel yang
  dihapus atau dipindahkan penerbit membuat pemulihan gagal.
- Artikel yang **diperbarui penerbitnya** setelah diambil (September 2026) menghasilkan teks
  berbeda, sehingga sidik jari (`sha256_articles_json_isi`, `sha256_teks_metadata`)
  tidak cocok lagi. Arsip seperti itu **bukan** arsip Versi 1 dan tidak sah
  untuk dibandingkan dengan baseline.
- Hasil parse juga bergantung pada parser. Selama parser berubah, pemulihan hanya
  setara bila dijalankan dengan kode pada tag atau commit yang sama.

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
diambil dari [Liputan6 Cek Fakta](https://www.liputan6.com/cek-fakta).

Repositori ini tidak mendistribusikan ulang isi artikel. Yang disimpan hanya:

- **Daftar artikel** basis pengetahuan (`archive/v1/article_ids.json`): id, URL,
  judul, label, kategori, dan tanggal, tanpa isi seksi.
- **Butir set uji** (`testset/v1.jsonl`): teks klaim, berupa kutipan pesan yang
  beredar (dibersihkan dari data pribadi dan tautan) atau klaim tulisan model dan
  manusia, beserta URL asal-usulnya.
- **Fixture uji** (`tests/fixtures/`): struktur HTML halaman asli dengan isi yang
  **disamarkan** (`tests/anonymize_fixtures.py`). Teks diganti kata semu, tautan
  sumber hoaks diganti jalur fiktif, dan nomor serta surel diganti nilai fiktif.

Teks lengkap artikel dan indeks vektor hanya ada di mesin lokal (`data/`,
`archive/`) dan tidak di-commit. Selain menyangkut hak penerbit, teks itu memuat
isi hoaks apa adanya: pemeriksaan 2026-09-26 menemukan **12 dari 150 artikel**
(semuanya berlabel PENIPUAN) memuat nomor telepon atau tautan WhatsApp penipu, dan
**62 dari 150** memuat domain di luar daftar aman (media, pemerintah, cek fakta,
platform sosial), termasuk domain yang tampak phishing. Klasifikasi domain itu
heuristik. Menerbitkan `articles.json` berarti ikut menyebarkan kontak dan tautan
penipuan tersebut. **Catatan:** riwayat git sebelum 2026-09-26 masih
memuat fixture versi asli. Riwayat sengaja tidak ditulis ulang agar hash commit
dan tag `testset-v1` tetap sah; alasannya tercatat di `testset/v1.meta.json`
(`pemeriksaan_data_terpublikasi_2026-09-26`).

Proyek ini dibuat untuk keperluan pembelajaran dan portofolio, bukan sebagai
pengganti layanan pemeriksa fakta resmi.
