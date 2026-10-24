> Dokumen riwayat: jalur di dalamnya adalah jalur saat ditulis. Jalur sejak Tahap 1b (2026-10-24): [pemetaan jalur](pemetaan_jalur.md).

# DRAF bagian "Evaluasi" untuk README (belum final)

> Draf 2026-10-21, dilengkapi setelah adjudikasi buta dan verifikasi testset-v1 dibaca. **SUDAH DITERAPKAN ke
> README 2026-10-21** (keputusan pemilik proyek; baris status, kolom bukti grader, dan butir keterbatasan label
> mengikuti rumusan pemilik proyek). README kini sumber yang berlaku; berkas ini dipertahankan sebagai riwayat draf
> dan tidak diperbarui lagi. Usulan penggantiannya ada di bagian terakhir berkas ini (bukan bagian README). Sumber semua angka:
> `docs/rancangan_evaluasi_eksternal.md` bagian 7.7, 7.8, 11, 11.8, 11.9, serta `testset/v1_analysis_report.txt`.

## Evaluasi

Semua proporsi disertai interval Wilson 95%. Keputusan per butir = modus dari 3 run. Generator
`gemini-3.5-flash-lite` (thinking medium); prompt, generator, dan retriever terkunci dengan hash selama
semua evaluasi di bawah.

### Ringkasan berdampingan

| Evaluasi | Indeks | Butir | Hasil |
| --- | --- | --- | --- |
| Set uji v1 (Versi 1, baseline) | `archive/v1`, 150 artikel | 50 non-batas | Akurasi **48/50** [86,5%; 98,9%]; Recall@3 36/40 |
| Set uji v1, uji kemunduran | produksi, 1.532 artikel | 44 non-batas (6 butir dikeluarkan karena labelnya tidak berlaku lagi) | Benar **37/44** = 84,1% [70,6%; 92,1%] vs 42/44 di arsip; **kemunduran bersih 5 -> MUNDUR** (ambang >= 3) |
| Set eksternal Liputan6, positif | produksi, 1.532 artikel | 46 | Ketepatan **36/46 = 78,3%** [64,4%; 87,7%] -> **memadai** (ambang: batas bawah >= 60%) |
| Set eksternal Liputan6, negatif | produksi, 1.532 artikel | 45 | Kecocokan palsu **10/45 = 22,2%** [12,5%; 36,3%] -> **gugur** (ambang: gugur bila batas bawah > 10%) |
| Set eksternal, retrieval | produksi, 1.532 artikel | 46 positif | Recall@3 bersyarat **41/46 = 89,1%** [77,0%; 95,3%] |

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
- Ambang ditetapkan dan di-commit sebelum evaluasi dijalankan; hasil per butir disegel sampai keandalan
  label dan label final di-commit.

### Set evaluasi eksternal

91 klaim nyata dari artikel cek fakta Liputan6 (dari 99; 8 kutipan yang hanya berisi tautan atau salam
dikeluarkan dengan aturan yang ditetapkan sebelum hasil dilihat). Kueri adalah kutipan pesan apa adanya,
seperti yang akan ditempel pengguna. Label emas diberikan pemilik proyek sendiri, tanpa bantuan AI:
**positif** = id artikel TurnBackHoax yang memuat klaim yang sama, **negatif** = tidak ada yang cocok di
daftar 5-8 kandidat yang diperiksanya.

### Keandalan label

Hanya ada satu anotator, jadi yang diukur adalah konsistensi dalam-anotator, bukan kesepakatan
antar-anotator.

- **Uji ulang buta 30 butir acak** (jeda 7 hari, urutan diacak, label lama disembunyikan): kappa biner
  **0,634** [0,308; 0,911] (bootstrap 10.000 ulangan), kappa id persis 0,707 [0,416; 0,921]; 25 dari 30
  sama. Lima yang berubah semuanya soal ada/tidaknya pasangan, tidak ada yang berpindah ke artikel lain.
  Menurut ambang yang dikunci (0,60-0,79), setiap metrik juga dihitung dengan kelima butir itu dibalik ke
  dua arah; kategorinya tidak berubah.
- **Audit jejak identik** (tanpa LLM: rangkaian 8 kata yang sama antara pesan dan Narasi artikel): 7
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

Kalau label diganti dengan hasil adjudikasi:

| | Positif benar | Kecocokan palsu |
| --- | --- | --- |
| Label final (angka resmi) | 36/46 = 78,3% [64,4; 87,7], memadai | 10/45 = 22,2% [12,5; 36,3], gugur |
| Adjudikasi, butir ragu tetap berlabel lama | 42/48 = 87,5% [75,3; 94,1], memadai | 5/43 = 11,6% [5,1; 24,5], tidak konklusif |
| Adjudikasi, butir ragu ikut adjudikasi | 44/50 = 88,0% [76,2; 94,4], memadai | 3/41 = 7,3% [2,5; 19,4], lulus |

- **Ini batas yang menguntungkan sistem, bukan perkiraan yang lebih akurat.** Hanya butir yang tidak
  sepakat yang ditinjau, jadi adjudikasi hanya bisa menggeser hasil ke arah sistem; kesalahan label pada
  butir yang sepakat tidak dicari. Angka sebenarnya ada di antara baris pertama dan baris adjudikasi.
- Kategori terburuk yang dilaporkan: positif **memadai**, kecocokan palsu **tidak konklusif**. Bahkan
  di batas ini kecocokan palsu tidak lulus dengan kokoh: "lulus" hanya tercapai kalau kedua butir ragu
  dihitung ke arah sistem, dengan batas atas 19,4%, tepat di bawah patokan 20%.
- Satu kecocokan palsu mengarah ke artikel di luar daftar kandidat yang dulu diperiksa. Adjudikasi
  menyatakannya bukan klaim yang sama (tokohnya berbeda), jadi itu tetap kesalahan sistem.
- Temuan yang lebih penting dari angkanya: **pada butir yang sulit, label sendiri tidak stabil.** 11 dari
  20 pilihan adjudikasi berbeda dari label final, dan satu butir sudah dinilai tiga kali dengan hasil
  berbeda. Batas "klaim yang sama" pada tautan penipuan berpola sama kabur bagi anotator maupun sistem.

### Verifikasi testset-v1 (sensitivitas)

Tiga butir negatif testset-v1 dijawab "ditemukan" pada indeks 1.532 karena ada artikel baru yang
dicocokkan sistem. Pemilik proyek membaca ketiga pasangan itu sendiri: **ketiganya memuat klaim yang
sama**. Jadi label negatifnya tidak berlaku lagi pada indeks besar, dan ketiga butir itu bukan kesalahan
sistem.

- Dengan ketiganya dikeluarkan, kemunduran bersih menjadi **2 dari 41 -> tidak mundur** (ambang >= 3).
  Angka resmi tetap 5/44, MUNDUR.
- Dua kemunduran yang tersisa nyata: dua butir positif kini ditolak walau artikel yang benar ada di
  top-3.
- Set uji v1 sendiri tidak diubah; statusnya hanya dicatat. Kini sembilan butir negatifnya tidak berlaku
  pada indeks 1.532, jadi set ini tetap sah hanya pada `archive/v1`.

### Pola kegagalan utama

- **Kecocokan ke artikel berpola sama dengan unsur inti berbeda** (10 dari 45 negatif). Sembilan dari
  sepuluh adalah artikel peringkat 1 retrieval, umumnya tautan penipuan dengan pola yang sama tetapi
  lembaga, tokoh, atau programnya berbeda; delapan bulat di ketiga run. Kesalahannya stabil, bukan acak.
  Adjudikasi menunjukkan sebagian dari sepuluh ini sebenarnya kesalahan label, tetapi tidak cukup untuk
  membuat kategorinya lulus.
- **Penolakan pasangan lintas gelombang** (6 dari 10 kegagalan positif). Pada pasangan yang terbit
  terpaut lebih dari 30 hari, ketepatan 11/18, dibanding 25/28 pada yang <= 30 hari. Label mengikuti
  aturan "lembaga dan tawaran yang sama = cocok walau gelombangnya berbeda", sedangkan prompt generator
  tidak mengenal aturan itu. Penolakan palsu lebih tahan adjudikasi: 6 dari 9 tetap kesalahan sistem.
- Separuh kegagalan positif (5 dari 10) terjadi di retrieval (artikel yang benar tidak masuk top-3),
  separuh di penilaian LLM.

### Kepatuhan aturan wajib

- **Aturan Wajib #3 (tautan tidak dikarang LLM):** 0 URL dari LLM yang tampil ke pengguna. Pada keluaran
  mentah ditemukan 4 URL yang tidak berasal dari metadata rujukan (2 di set eksternal, 2 di set uji v1).
  Keempatnya berdomain `.go.id`, tersalin dari teks seksi artikel kandidat (bukan karangan model), dan
  dibuang `strip_urls` sebelum jawaban disimpan atau ditampilkan.
- **Format:** 0 pelanggaran format terstruktur pada 274 panggilan set eksternal dan 162 panggilan set uji v1.

### Perubahan tampilan setelah evaluasi

Sejak 2026-10-21 demo menampilkan peringatan pada setiap hasil "ditemukan": pengguna diminta memastikan
sendiri bahwa tokoh, lembaga, dan program di artikel sama dengan pesan yang diperiksa, dengan judul dan
tanggal artikel di dekatnya. Ini perubahan tampilan saja; **angka di atas mengukur keputusan generator dan
tidak terpengaruh olehnya.**

### Keterbatasan

- Satu anotator; jeda uji ulang 7 hari; batas bawah interval kappa di bawah 0,60.
- Adjudikasi hanya meninjau butir yang tidak sepakat, dan anotator tahu setiap butirnya adalah
  ketidaksesuaian; hasilnya berat sebelah ke arah sistem.
- Recall@3 bersyarat (batas atas).
- Label negatif hanya berlaku terhadap daftar kandidat yang diperiksa, bukan seluruh basis data.
- Kutipan pendek (tautan saja, salam) dikeluarkan; pesan semacam itu tidak terukur.
- Prompt generator tidak mengenal aturan lintas gelombang yang dipakai label.
- Uji kemunduran pada indeks produksi mencampur efek data dengan efek sistem; label negatif set uji v1
  tidak otomatis berlaku saat basis data membesar.
- Dua berkas label tercatat tidak bersih: satu berkas sesi buta sempat tertimpa koreksi salah ketik, dan
  berkas adjudikasi pertama ditolak karena enam isian tidak sah lalu diperbaiki formatnya oleh anotator
  sendiri (hanya enam sel itu yang berubah). Keduanya tercatat di rancangan 7.2 dan 7.8.
- Set 99 butir ini **sekali pakai**: setelah hasilnya dilihat, perbaikan sistem tidak boleh dievaluasi
  ulang di set yang sama.

### Rencana perbaikan

1. **Pemeriksaan unsur inti** (subjek/lembaga, tindakan, objek pembeda) sebelum sistem menyatakan
   "ditemukan". Ambang skor kemiripan sudah tiga kali terbukti tidak memisahkan klaim yang sama dari
   tetangganya, jadi pemeriksaannya harus eksplisit. Kriterianya perlu cukup tegas untuk juga dipakai
   sebagai pedoman label, karena label pada kasus yang sama terbukti tidak stabil.
2. **Kebijakan lintas gelombang**, diputuskan bersama butir 1: menerima pasangan lintas gelombang bisa
   memperbaiki sebagian penolakan, tetapi berisiko menambah kecocokan palsu pada penipuan berpola sama.
3. **Uji pada sampel baru** dari periode lain, dengan ambang dikunci sebelum dijalankan.

Kemampuan mengenali klaim yang tidak ada di basis data saat ini **belum cukup** untuk memicu langkah
korektif (mencari ke situs cek fakta lain): menurut angka resmi sekitar satu dari lima klaim semacam itu
tidak akan pernah sampai ke langkah tersebut karena sistem sudah menampilkan artikel yang keliru, dan
bahkan di batas yang paling menguntungkan sistem hasilnya baru tidak konklusif.

---

## Usulan penggantian di README utama (catatan untuk pemilik proyek, BUKAN bagian README)

README belum diubah. Usulan, untuk dibaca dulu:

1. **Ganti seluruh `## Hasil Evaluasi` (README baris 121-217)** dengan `## Hasil Evaluasi` baru berisi
   bagian "Evaluasi" draf ini (judul `## Evaluasi` menjadi `## Hasil Evaluasi` agar tautan Daftar Isi tetap
   berlaku; subjudul `###` tidak berubah). Alasannya: bagian
   lama hanya memuat Versi 1 pada 150 artikel, dan subbagian "Cakupan evaluasi" menyatakan indeks 1.532
   "belum pernah dievaluasi dengan menjalankan generator" serta "enam butir negatif"; keduanya kini tidak
   benar.
2. **Angka Versi 1 tetap ada, tetapi diringkas** di subbagian `### Baseline Versi 1 (archive/v1)`:
   tabel komposisi, tabel metrik utama, status H1/H3, dan empat caveat dipertahankan apa adanya; paragraf
   "dua mode kegagalan" dipersingkat menjadi dua kalimat. Tabel Recall@k per indeks (150/922/1.532)
   dipindah ke sana sebagai riwayat retrieval.
3. **Urutan di bagian baru:** ringkasan berdampingan -> baseline Versi 1 -> set eksternal -> keandalan label
   -> adjudikasi -> verifikasi testset-v1 -> pola kegagalan -> kepatuhan -> perubahan tampilan.
   "Keterbatasan" dan "Rencana perbaikan" draf ini digabung ke bagian README yang sudah ada
   (`## Keterbatasan`, `## Rencana Versi 2`), bukan diduplikasi.
4. **Tiga tempat lain di README ikut terdampak** dan sebaiknya diputuskan sekalian:
   - baris status di bagian atas ("Versi 1 selesai dan terukur. Versi 2 ... belum dimulai") perlu menyebut
     evaluasi eksternal pada indeks 1.532;
   - tabel `## Rencana Versi 2` menyatakan grader relevansi "tidak masuk" karena buktinya lemah. Evaluasi
     eksternal kini memberi **bukti masalah** (kecocokan palsu 10/45, gugur), tetapi belum ada bukti bahwa
     komponen terpisah memperbaikinya. Kolom buktinya perlu diperbarui; apakah statusnya berubah adalah
     keputusan Anda, bukan bagian penggantian ini;
   - `## Keterbatasan` perlu butir baru tentang label negatif set uji v1 yang tidak berlaku pada indeks
     besar (kini sembilan butir).
5. Bagian "Cara Menjalankan" belum memuat perintah evaluasi eksternal (`evaluation.external_eval`,
   `evaluation.external_analysis`); usul satu blok perintah pendek di `### Menjalankan evaluasi`.
