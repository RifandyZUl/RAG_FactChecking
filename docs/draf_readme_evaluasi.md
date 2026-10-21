# DRAF bagian "Evaluasi" untuk README (belum final)

> Draf 2026-10-21. Belum menggantikan README. Angka hasil adjudikasi buta (rancangan evaluasi eksternal
> 7.8) dan verifikasi tiga butir negatif testset-v1 (11.8) **menyusul**; keduanya tidak mengubah angka
> utama di bawah. Sumber semua angka: `docs/rancangan_evaluasi_eksternal.md` bagian 7.7 dan 11, serta
> `testset/v1_analysis_report.txt`.

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

### Pola kegagalan utama

- **Kecocokan ke artikel berpola sama dengan unsur inti berbeda** (10 dari 45 negatif). Sembilan dari
  sepuluh adalah artikel peringkat 1 retrieval, umumnya tautan penipuan dengan pola yang sama tetapi
  lembaga, tokoh, atau programnya berbeda; delapan bulat di ketiga run. Kesalahannya stabil, bukan acak.
- **Penolakan pasangan lintas gelombang** (6 dari 10 kegagalan positif). Pada pasangan yang terbit
  terpaut lebih dari 30 hari, ketepatan 11/18, dibanding 25/28 pada yang <= 30 hari. Label mengikuti
  aturan "lembaga dan tawaran yang sama = cocok walau gelombangnya berbeda", sedangkan prompt generator
  tidak mengenal aturan itu.
- Separuh kegagalan positif (5 dari 10) terjadi di retrieval (artikel yang benar tidak masuk top-3),
  separuh di penilaian LLM.
- Pada set uji v1, dua butir positif kini ditolak walau artikelnya ada di top-3, dan tiga butir negatif
  kini dicocokkan ke artikel yang baru masuk indeks; apakah ketiga artikel itu memuat klaim yang sama
  sedang diverifikasi.

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
- Recall@3 bersyarat (batas atas).
- Label negatif hanya berlaku terhadap daftar kandidat yang diperiksa, bukan seluruh basis data.
- Kutipan pendek (tautan saja, salam) dikeluarkan; pesan semacam itu tidak terukur.
- Prompt generator tidak mengenal aturan lintas gelombang yang dipakai label.
- Uji kemunduran pada indeks produksi mencampur efek data dengan efek sistem.
- Satu berkas label terisi sempat tertimpa koreksi salah ketik; tidak berubahnya butir lain bersandar
  pada pernyataan anotator (tercatat di rancangan 7.2).
- Set 99 butir ini **sekali pakai**: setelah hasilnya dilihat, perbaikan sistem tidak boleh dievaluasi
  ulang di set yang sama.

### Rencana perbaikan

1. **Pemeriksaan unsur inti** (subjek/lembaga, tindakan, objek pembeda) sebelum sistem menyatakan
   "ditemukan". Ambang skor kemiripan sudah tiga kali terbukti tidak memisahkan klaim yang sama dari
   tetangganya, jadi pemeriksaannya harus eksplisit.
2. **Kebijakan lintas gelombang**, diputuskan bersama butir 1: menerima pasangan lintas gelombang bisa
   memperbaiki sebagian penolakan, tetapi berisiko menambah kecocokan palsu pada penipuan berpola sama.
3. **Uji pada sampel baru** dari periode lain, dengan ambang dikunci sebelum dijalankan.

Kemampuan mengenali klaim yang tidak ada di basis data saat ini **belum cukup** untuk memicu langkah
korektif (mencari ke situs cek fakta lain): sekitar satu dari lima klaim semacam itu tidak akan pernah
sampai ke langkah tersebut karena sistem sudah menampilkan artikel yang keliru.
