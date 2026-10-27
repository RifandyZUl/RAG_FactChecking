> Dokumen riwayat: jalur di dalamnya adalah jalur saat ditulis. Jalur sejak Tahap 1b (2026-10-24): [pemetaan jalur](../riwayat/pemetaan_jalur.md).
> Hash commit di dokumen ini adalah hash riwayat asli; pemetaannya ke riwayat sekarang ada di [pemetaan hash](../riwayat/pemetaan_hash.md).

# Rancangan Versi 2

**Status (2026-10-27, revisi 8): K4 (a), K4 (b), K11, dan N5-N8 sudah diputuskan (keputusan 44-51), tetapi BELUM diterapkan ke teks aturan: pemilik proyek sedang menimbang prinsip utama "Kesimpulan membantah pesan" (A6.10), yang menentukan bentuk K4 (c), N1-N4, dan N8. Pedoman 2.0 [`testset/ANNOTATION_GUIDE_v2.md`](../../testset/ANNOTATION_GUIDE_v2.md) tetap DRAF revisi 7; belum boleh dipakai dan belum dikunci. Lembar uji coba pedoman sudah dibuat (A6.5). Versi 2 mengukur
sistem Versi 1 tanpa mengubah keputusannya: pedoman yang dipertegas, anotator kedua, set uji (a) dan (b), dan tombol
salin klarifikasi. Pemeriksaan entitas dan "pola mirip" tidak masuk (A2.7, keputusan 13-14).** Bagian A di bawah adalah rancangan yang berlaku. Bagian B adalah rancangan 2026-10-03 beserta
pengukurannya; isinya dipertahankan, dan setiap bagiannya diberi tanda **[MASIH BERLAKU]**, **[SEBAGIAN
BERLAKU]**, atau **[TIDAK BERLAKU LAGI]**. Tempat yang perlu keputusan pemilik proyek ditandai
**KEPUTUSAN PEMILIK PROYEK**.

**Mengapa cakupannya berubah.** Rancangan 2026-10-03 berpusat pada pesan panjang. Pengukuran pada pesan asli
menunjukkan 0 dari 200 pesan melebihi 512 token (B.10.7), jadi masalah itu jarang terjadi. Evaluasi
eksternal kemudian menunjukkan kegagalan yang lebih penting: kecocokan palsu 10/45 = 22,2% [12,5%; 36,3%],
gugur, terutama pada penipuan yang polanya sama tetapi lembaga atau programnya berbeda
(`rancangan_evaluasi_eksternal.md` 11.3, 11.7). Rancangan baru menyasar kegagalan itu.

---

# Bagian A. Rancangan Versi 2 (2026-10-26, revisi 5)

**Versi 2 mengukur sistem Versi 1; ia tidak mengubah keputusan sistem.** Retrieval, generator (termasuk prompt), dan
cara sistem memutuskan "ditemukan" atau "belum ditemukan" tetap persis seperti Versi 1 di sisi kode. Model Gemini dan
pustaka di luar kode bisa berubah, jadi perilaku sistem diawasi dengan uji pergeseran (A4.f). Uji itu hanya bisa menangkap perubahan besar; lolos uji tidak membuktikan modelnya sama. Yang dibangun Versi 2 adalah
ukuran yang lebih bisa dipercaya (pedoman yang dipertegas, anotator kedua, set uji baru) dan satu alat bantu tampilan
(tombol salin klarifikasi). Angka Versi 2 karena itu adalah angka **sistem Versi 1 yang diukur ulang**, bukan bukti
bahwa perilaku sistem membaik. Perbaikan perilaku sistem dicatat sebagai arah versi berikutnya (A13).

**Riwayat revisi Bagian A.** Versi pertama `b1691c0`; revisi 1 `1ebbba4` (keputusan pertama, koreksi A-E, tambahan
F-H); revisi 2 `8bce7d9` (hasil uji ekstraksi LLM: berhenti); revisi 3 (2026-10-26): ruang lingkup dipersempit
(keputusan 13-15), tinjauan kunci dua tahap, alat bantu tampilan nominal dan saluran (A11.3), arah perbaikan sistem
(A13); revisi 4 `c5be0cd` (2026-10-26): uji pergeseran (A4.f) menggantikan penghapusan uji kemunduran, keputusan 16-19; revisi 5 (2026-10-26): ambang uji pergeseran disetujui dengan label "Tidak terdeteksi pergeseran", uji pergeseran mengapit setiap evaluasi, kuota A8 dihitung ulang, rancangan dibekukan (keputusan 20-22); revisi 6 (2026-10-27): lembar persetujuan pedoman diisi, A6 direvisi, pedoman 2.0 berdiri sendiri, pemeriksaan konsistensi dan rencana penguncian pedoman (keputusan 23-31); revisi 7 (2026-10-27): keputusan atas K1-K13 (keputusan 32-43), perbandingan pilihan K1, usulan K4 dan K11, pemeriksaan konsistensi kedua; revisi 8 (2026-10-27): keputusan 44-52, penilaian prinsip utama (A6.10), uji coba pedoman dan pemeriksaan independen sebelum kunci (A6.5), lembar uji coba.

**Keputusan pemilik proyek:**

| # | Hal | Keputusan | Status di revisi 3 |
| --- | --- | --- | --- |
| 1 | Domain atau nomor yang sama persis | Tidak boleh menaikkan "belum ditemukan" | tidak relevan lagi (tidak ada pemeriksaan entitas) |
| 2 | Bukti waktu luar | GitHub Release pada tag dan Internet Archive (A3.4) | berlaku |
| 3 | Set (a) | 150 butir, target salah menuduh di bawah 5% | berlaku |
| 4 | Periode set (b) | 28 September-31 Desember 2026 | berlaku |
| 5 | Ambang A4.e | Disetujui | berlaku untuk tiga ambang metrik; dua ambang gugur bersama pemeriksaan entitas; ambang kemunduran diganti uji pergeseran (A4.e, A4.f) |
| 6 | Aturan 3 (gelombang) | Gelombang berbeda tetap klaim sama; sistem tidak diperbaiki untuk ini | berlaku |
| 7 | Ambang kappa | 0,60; anotator kedua dicari pemilik proyek | berlaku |
| 8 | Arah entitas | Uji ekstraksi LLM secara eksploratif | selesai: berhenti (A2.7) |
| 9 | Nominal antar-gelombang | Gelombang jelas berbeda -> tetap klaim sama walau nominal berbeda (A6 aturan 4) | **digantikan keputusan 23 (2026-10-27)** |
| 10 | Penyimpanan set (a) | Yang di-commit hanya URL, tanggal terbit, hash teks, dan metadata | berlaku |
| 11 | Anotator kedua | 40 + 40; set (a) juga dengan kesepakatan mentah, Gwet AC1, PABAK (A7) | berlaku |
| 12 | Kriteria analisis | Kriteria ditulis dan di-commit sebelum skrip dijalankan | berlaku |
| 13 | Hasil uji ekstraksi | BERHENTI diterima; Versi 2 dipersempit | berlaku |
| 14 | "Pola mirip" | Tidak ada (pilihan a); Versi 2 tidak mengubah keputusan sistem | berlaku |
| 15 | Lembar pemeriksaan ekstraksi | Tidak diisi sekarang; pemisahan penyebab tetap sementara (A2.5, A2.7) | berlaku |
| 16 | Kunci dua tahap | Dikonfirmasi, dengan alasan definisi dikunci sebelum data (A3.1) | berlaku |
| 17 | Evaluasi set (a) | Dijalankan segera setelah Kunci 1, didahului uji pergeseran | berlaku |
| 18 | Pemeriksaan ketepatan alat bantu tampilan (A11.3) | Ditunda sampai pedoman disetujui dan set (a) selesai dilabeli | berlaku |
| 19 | Uji kemunduran Versi 1 | **Tidak dihapus**; diganti nama menjadi **uji pergeseran**, karena model Gemini dan pustaka bisa berubah walau kode tidak (A4.f) | berlaku |
| 20 | Ambang uji pergeseran | Disetujui, dengan label "Sebanding" diganti "Tidak terdeteksi pergeseran": dengan 54 butir hanya perubahan besar yang tertangkap | berlaku |
| 21 | Waktu uji pergeseran | Mengapit evaluasi: sebelum evaluasi dimulai dan diulang penuh setelah evaluasi selesai, untuk set (a) dan set (b) (A4.f, A8) | berlaku |
| 22 | Revisi rancangan | Dibekukan sampai lembar persetujuan pedoman selesai diisi pemilik proyek (A12) | selesai: lembar diisi 2026-10-27 |
| 23 | A6 aturan 4 (nominal) | Nominal eksplisit berbeda di kedua sisi -> bukan klaim sama, juga bila gelombangnya terlihat berbeda dari tanggal terbit; menggantikan keputusan 9 karena bertentangan dengan pengecualian aturan 3 (A6.2) | berlaku |
| 24 | A6 aturan 7 | Artikel sah hanya bila lolos semua aturan lain (1-6, 8, dan 9) | berlaku |
| 25 | Catatan wajib | Untuk label positif dan negatif pasangan penipuan, termasuk tahun atau periode; untuk label negatif dicatat pada kandidat yang paling mirip menurut penilaian anotator, tanpa skor retrieval | berlaku |
| 26 | Kapan A6 dipakai | Per pasangan pesan-artikel: artikel berlabel PENIPUAN, atau pesan meminta mendaftar, mengisi data pribadi, mentransfer uang, atau menghubungi tautan atau nomor atas nama lembaga atau tokoh | berlaku |
| 27 | "Periode" (aturan 3) | Tahun, atau nama gelombang atau tahap program; tanggal batas pendaftaran dan tanggal hari tidak termasuk (tetap dicatat) | berlaku |
| 28 | A6 aturan 9 (bawaan) | Klaim sama butuh tawaran sama tanpa pertentangan; bila tawaran tidak dapat dibandingkan, butuh lembaga atau tokoh sama + satu unsur lain sama; selain itu bukan klaim sama, ragu | berlaku |
| 29 | Induk dan anak lembaga | Belum diatur; ditandai ragu dan dicatat saat pelabelan | berlaku |
| 30 | Pedoman 2.0 | Dokumen berdiri sendiri `testset/ANNOTATION_GUIDE_v2.md`; dikunci lewat tag `annotation-guide-v2.0` sebelum pelabelan apa pun (A6.5) | rencana, menunggu persetujuan |
| 31 | Perkiraan jam set (a) | Tidak ditebak ulang; diukur ulang setelah 10 butir pertama dilabeli (A12) | berlaku |
| 32 | K1: saluran resmi | Pengecualian aturan 5: saluran resmi terverifikasi di satu sisi lawan tidak resmi di sisi lain = pertentangan, bukan klaim sama; cara verifikasi ditulis (A6); istilah "butir penipuan" diganti "pola pendaftaran atau tawaran" | berlaku |
| 33 | K2: ragu di aturan 9 | Hanya untuk keadaan kedua (tawaran tidak dapat dibandingkan, bukti tambahan kurang); bukan untuk penolakan karena pertentangan | berlaku |
| 34 | K3: saluran | Berbeda = netral; sama persis = bukti pendukung; resmi lawan tidak resmi = pertentangan | berlaku |
| 35 | K4: prioritas | Untuk pasangan A6, A6 didahulukan bila bertentangan dengan v1.0; penyelesaian tiga titik masih usulan (A6.8) | prinsip berlaku |
| 36 | K5: unsur inti | Lembaga atau tokoh, tawaran, saluran, nominal, periode | berlaku |
| 37 | K6: jenis periode | Hanya dibandingkan dengan jenis yang sama; jenis berbeda = tidak dapat dibandingkan, kecuali satu sisi memuat keduanya | berlaku |
| 38 | K7: nominal | Jumlah uang yang ditawarkan atau diminta; armada, kuota peserta, dan sejenisnya bukan nominal | berlaku |
| 39 | K8: lembaga umum | Lawan lembaga tertentu = tidak dapat dibandingkan | berlaku |
| 40 | K9: tokoh lawan lembaganya | Tidak dapat dibandingkan, ragu; keputusan lewat aturan 9; dikumpulkan untuk versi berikutnya | berlaku |
| 41 | K10: label kandidat | Label TurnBackHoax tiap kandidat tampil di lembar pelabelan (metadata, bukan keluaran sistem) | berlaku |
| 42 | K12: aturan 3 | Gelombang yang hanya terlihat dari tanggal terbit = sama; tahun atau periode tertulis di kedua teks dan berbeda = bukan sama | berlaku |
| 43 | K13: butir ragu di metrik | Metrik utama memakai label akhir; sensitivitas tanpa butir ragu (A4.d, dikunci di Kunci 1) | berlaku |
| 44 | Periode di satu sisi | Kalimat "Tahun atau periode yang hanya tertulis di satu sisi: tidak dapat dibandingkan" (tambahan Claude Code di revisi 7) disetujui | berlaku |
| 45 | K4 (a) | Untuk pasangan A6, aturan 8 dan 9 menggantikan baris "lebih umum -> TIDAK SAMA" v1.0 | berlaku; belum diterapkan ke teks |
| 46 | K4 (b) | Untuk pasangan A6, aturan 7 menggantikan baris "keluarga artikel -> ambigu" v1.0; jumlah artikel sah dicatat per butir dan akurasi butir dengan > 1 artikel sah dilaporkan terpisah | berlaku; belum diterapkan ke teks |
| 47 | K11 | Ragu menggantikan `batas`; `kekhususan` hanya untuk butir yang semua pasangannya dinilai v1.0 (lainnya `a6`); `ambigu` tidak dipakai untuk pasangan A6 | berlaku; belum diterapkan ke teks |
| 48 | N5: peran nominal | Nominal hanya dibandingkan bila perannya sama (ditawarkan dengan ditawarkan, diminta dengan diminta); peran berbeda = tidak dapat dibandingkan | berlaku; belum diterapkan ke teks |
| 49 | N6: daftar acuan | Daftar acuan saluran resmi bertanggal disiapkan di lembar pelabelan, supaya kedua pelabel memakai acuan yang sama tanpa internet | berlaku; daftar belum disusun |
| 50 | N7: butir ragu | Analisis sensitivitas mengeluarkan butir yang ditandai ragu oleh salah satu pelabel | berlaku (A4.d) |
| 51 | N8 | Mengikuti pendekatan yang dipilih; di bawah prinsip baru, saluran resmi yang sama di kedua sisi bukan bukti klaim sama | menunggu A6.10 |
| 52 | Sebelum kunci | Uji coba pedoman (~10 butir set eksternal lama) dan pemeriksaan independen oleh sesi agent baru (A6.5) | berlaku |

**Pembacaan hasil uji kelayakan A2.5 (dari pemilik proyek), beserta tanggapan saya.** Dari 10 kecocokan palsu, 7
menurut adjudikasi adalah kesalahan label. Jadi kesalahan sistem yang terbukti pada kecocokan palsu hanya 3, dan
ketiganya (tokoh, tindakan, nominal yang tidak disebut) memang di luar jangkauan pemeriksaan daftar. Artinya, sumber
ketidakpastian terbesar adalah **definisi "klaim sama" dan konsistensi label**, bukan sistemnya. Karena itu
**pedoman A6 dan anotator kedua A7 menjadi inti Versi 2**, dan pemeriksaan entitas menjadi komponen yang menunggu bukti.

Saya setuju dengan arah pembacaan ini, dengan dua batasan yang perlu ikut dicatat:

1. **"Hanya 3 yang terbukti" adalah batas yang menguntungkan sistem, bukan angka yang lebih tepat.** Adjudikasi hanya
   meninjau 20 butir yang tidak sepakat, penilainya tahu setiap butir adalah ketidaksesuaian, dan dua pilihan yang
   disajikan bisa membuat penilai condong menerima pilihan yang tampak masuk akal (`rancangan_evaluasi_eksternal.md`
   11.9). Jumlah kesalahan sistem yang sebenarnya di antara 10 itu ada di antara 3 dan 10. Yang terbukti bukan
   "sistemnya baik", melainkan "kita belum bisa mengukurnya dengan tepat selama label tidak stabil".
2. **Kesalahan sistem di luar kecocokan palsu tetap nyata.** Setelah adjudikasi, 6 dari 9 penolakan palsu tetap
   kesalahan sistem, dan 5 dari 10 kegagalan positif terjadi di retrieval. Pedoman dan anotator kedua menstabilkan
   ukuran, tetapi tidak memperbaiki kesalahan itu.

Kesimpulan untuk rancangan: inti Versi 2 adalah **ukuran yang bisa dipercaya** (pedoman, anotator kedua, set uji pesan
benar, kunci dua tahap). Komponen yang mengubah jawaban (pemeriksaan entitas, tiga jenis jawaban) hanya masuk bila lolos
uji kelayakan dengan kriteria yang dikunci lebih dulu. *(Revisi 3: keduanya tidak lolos dan dikeluarkan dari Versi 2;
keputusan 13 dan 14.)*

## A1. Tujuan dan ruang lingkup

**Tujuan:** mengukur sistem Versi 1 dengan cara yang lebih bisa dipercaya, terutama dua kesalahan yang paling
merugikan pengguna: **salah menuduh** (pesan yang benar ditampilkan seolah klaimnya pernah dinyatakan salah) dan
**kecocokan palsu** (klaim yang tidak ada di arsip dicocokkan dengan artikel lain). Evaluasi eksternal menunjukkan
bahwa sumber ketidakpastian terbesar adalah definisi "klaim sama" dan konsistensi label (pembacaan hasil di atas).

**Ruang lingkup Versi 2 (semuanya mengukur sistem Versi 1 tanpa mengubah keputusannya):**

| Komponen | Isi | Bagian |
| --- | --- | --- |
| Pedoman yang dipertegas | aturan "klaim sama" untuk penipuan berulang | A6 |
| Anotator kedua | 40 butir set (a) + 40 butir set (b), buta terhadap label pemilik proyek dan keluaran sistem | A7 |
| Set (a) | 150 pengumuman resmi yang benar, untuk tingkat salah menuduh | A4.a |
| Set (b) | sampel Liputan6 periode baru, untuk mengukur ulang ketepatan temuan dan kecocokan palsu dengan pedoman yang dipertegas dan diperiksa anotator kedua | A4.b |
| Uji pergeseran | set uji v1 pada `archive/v1` dijalankan ulang sebelum dan sesudah setiap evaluasi, untuk menangkap perubahan besar pada model atau pustaka (lolos uji tidak membuktikan keduanya sama) | A4.f |
| Tombol salin klarifikasi | menyalin label, Kesimpulan TurnBackHoax apa adanya, dan tautan artikel pada jawaban "ditemukan"; tidak ada tombol untuk "belum ditemukan" | -- |

Tombol salin klarifikasi adalah perubahan tampilan saja: ia muncul setelah keputusan dibuat, tidak memengaruhi
keputusan, dan tidak tercatat di berkas hasil evaluasi.

**Sengaja di luar ruang lingkup:**

| Hal | Alasan |
| --- | --- |
| Pemeriksaan entitas dan jawaban "pola mirip" | Tidak lolos uji kelayakan (A2.5, A2.7); keputusan 13 dan 14 |
| Perubahan retrieval, generator, prompt, atau keputusan sistem | Versi 2 hanya mengukur; perbaikan perilaku dicatat di A13 |
| Bot WhatsApp atau Telegram, layanan publik | Prasyaratnya belum ada (A9) |
| Sumber data kedua | Menunggu izin API Yudistira dari Mafindo |
| Grader LLM, penulis ulang kueri, juri LLM, LangGraph, pesan panjang | Tetap tidak masuk (B.0, B.8, B.10.7) |
| Alat bantu tampilan nominal dan saluran | Diusulkan di A11.3; hanya tampil setelah lolos pemeriksaan ketepatan sendiri |
| Fitur lain di A11 | Setelah Versi 2 |

## A2. Pemeriksaan entitas **[TIDAK BERLAKU LAGI untuk ruang lingkup; A2.5-A2.7 tetap berlaku sebagai bukti]**

Bagian ini mencatat rancangan pemeriksaan entitas dan dua uji kelayakannya. Rancangannya (A2.1-A2.4) tidak dipakai
Versi 2. Hasil ujinya (A2.5-A2.7) tetap menjadi dasar keputusan dan bahan versi berikutnya (A13).

### A2.1 Entitas yang dibandingkan **[TIDAK BERLAKU LAGI]**

**[TIDAK BERLAKU LAGI: Versi 2 tidak memakai pemeriksaan entitas; keputusan 13 dan 14. Dipertahankan sebagai riwayat.]**

| Entitas | Peran | Cara mengambil dari teks | Sumber di sisi artikel |
| --- | --- | --- | --- |
| Lembaga | **inti** (bisa menurunkan) | daftar eksplisit kementerian, lembaga, BUMN, dan pemerintah daerah dari sumber resmi, bukan dari artikel basis data (agar tidak melingkar) | judul dan Narasi |
| Nama program | **inti** | daftar program **spesifik** (mis. PKH, BPNT, BSU, KIP, Prakerja, mudik gratis, CPNS). Istilah umum seperti "bansos", "bantuan", atau "lowongan" tidak dimasukkan, karena istilah umum tidak boleh dianggap bertentangan dengan program spesifik | judul dan Narasi |
| Nominal | **inti** | pola `Rp`, `juta`, `ribu`, angka dengan satuan | judul, Narasi, Kesimpulan |
| Periode (tanggal, bulan, tahun, gelombang) | **penanda gelombang** (tidak pernah menurunkan) | pola tahun, nama bulan, tanggal, dan kata "gelombang" | judul dan Narasi |
| Domain dan tautan | **pendukung** (tidak pernah menurunkan) | pola URL, termasuk yang tanpa skema dan `wa.me`, dinormalkan ke domain | `claim_sources` dan Narasi |
| Nomor telepon | **pendukung** | pola yang sudah ada di `labeling.candidates.screen.pii_flags` | Narasi |

**Daftar lembaga dan program dikunci di Kunci 1** sebagai berkas data dengan hash (A3.1), sebelum kode ditulis.
Daftar disusun dari sumber resmi (daftar kementerian dan lembaga, daftar BUMN, nama program dari situs resmi),
dan **tidak boleh** disusun atau disesuaikan dari artikel basis data, terutama artikel yang terbit sejak
28 September 2026 (A3.2).

### A2.2 Hasil per entitas **[TIDAK BERLAKU LAGI]**

**[TIDAK BERLAKU LAGI: Versi 2 tidak memakai pemeriksaan entitas; keputusan 13 dan 14. Dipertahankan sebagai riwayat.]**

Setiap entitas diberi salah satu status: **sama** (ada nilai yang sama di kedua sisi), **bertentangan**
(keduanya menyebut entitas jenis itu dan tidak ada nilai yang sama), atau **tidak dapat dibandingkan** (salah
satu sisi tidak menyebutnya). "Tidak dapat dibandingkan" tidak dihitung sebagai pertentangan, sesuai Aturan B
lama (hanya detail yang bertentangan yang menolak; B.11.6) dan aturan 2 pedoman A6.

### A2.3 Aturan keputusan **[TIDAK BERLAKU LAGI]**

**[TIDAK BERLAKU LAGI: Versi 2 tidak memakai pemeriksaan entitas; keputusan 13 dan 14. Dipertahankan sebagai riwayat.]**

- Generator memilih artikel dan ada minimal satu **entitas inti** (lembaga, nama program, nominal) yang
  bertentangan -> **"pola mirip"**.
- Generator memilih artikel dan tidak ada pertentangan entitas inti -> **"klaim sama"**.
- **Pertentangan nominal diabaikan bila gelombangnya jelas berbeda:** periode disebut eksplisit di kedua sisi dan
  nilainya berbeda (keputusan 9, A6 aturan 4). Pertentangan lembaga atau program tidak terpengaruh periode.
- Generator tidak memilih artikel -> **"belum ditemukan"**, apa pun hasil pemeriksaan entitas (keputusan 1).
- Domain atau nomor yang **sama persis** dengan artikel ditampilkan sebagai bukti pendukung pada jawaban apa pun
  yang menampilkan artikel ("pola mirip" atau "klaim sama"). Domain atau nomor yang **berbeda** tidak memengaruhi
  apa pun, sesuai aturan 5 pedoman (penipu sering berganti tautan).
- Analisis tambahan, tidak memengaruhi jawaban: pada butir "belum ditemukan", berapa yang domain atau nomornya
  sama persis dengan salah satu artikel kandidat.

### A2.4 Batas yang diketahui sebelum dibangun **[TIDAK BERLAKU LAGI]**

**[TIDAK BERLAKU LAGI: Versi 2 tidak memakai pemeriksaan entitas; keputusan 13 dan 14. Dipertahankan sebagai riwayat.]**

- **Pencatutan tokoh tidak tertangani Versi 2.** Pedoman A6 tetap memperlakukan tokoh yang dicatut seperti
  lembaga (aturan 1), tetapi sistem tidak memeriksanya. Alasan memilih ini daripada menambah entitas tokoh:
  1. Tokoh yang dicatut sangat beragam (pejabat pusat dan daerah, selebritas, tokoh agama, pengusaha) dan
     berganti dari waktu ke waktu. Daftar resmi yang bisa dirawat hanya mencakup sebagian kecil, misalnya menteri
     dan gubernur, sehingga cakupannya akan tampak lebih baik daripada kenyataannya.
  2. Nama tokoh sering ditulis dengan ejaan atau sapaan berbeda, dan tokoh juga muncul sebagai latar (dikutip
     sebagai sumber), bukan sebagai pihak yang dicatut. Pencocokan daftar akan sering keliru menganggapnya
     bertentangan dan menurunkan jawaban yang benar.
  3. Satu-satunya bukti bahwa tokoh berguna berasal dari data yang sudah dilihat (P2-17, A2.5). Menambahkannya
     sekarang sama dengan menyetel aturan pada data evaluasi.
  Bila tinjauan ulang A2.5 memilih ekstraksi unsur inti dengan LLM, tokoh tercakup secara alami sebagai
  "subjek", tanpa daftar.
- Pengambilan lembaga dan program dengan daftar bisa meleset (sinonim, singkatan, salah ketik). Kegagalan ini
  membuat entitas "tidak dapat dibandingkan", sehingga sistem kembali ke keputusan Versi 1. Uji kelayakan A2.5
  menunjukkan masalah ini besar.
- **Gelombang berbeda** (tahun atau tanggal) bukan entitas inti (keputusan 6). Versi 2 tidak memperbaiki
  penolakan lintas gelombang oleh generator.
- **Perbedaan tindakan** (mis. "pendaftaran sudah dibuka" dibanding "program itu ada") tidak tertangkap entitas
  apa pun (lihat P2-33 di A2.5).

### A2.5 Uji kelayakan pemeriksaan entitas (EKSPLORATIF, 2026-10-26) **[MASIH BERLAKU, sebagai bukti]**

**Status pemisahan penyebab "tidak dapat dibandingkan" (keputusan 15): tetap SEMENTARA.** Lembar pemeriksaan
ekstraksi tidak diisi, jadi hitungan di A2.7 memakai acuan hasil run 1 yang belum diperiksa manusia dan tidak
boleh dikutip sebagai angka final.

**EKSPLORATIF. Data ini sudah pernah dilihat (evaluasi eksternal dan adjudikasinya), jadi hasilnya tidak boleh
dilaporkan sebagai bukti kinerja Versi 2.** Gunanya hanya menilai apakah rancangan entitas layak diteruskan
sebelum sekitar 40 jam pelabelan.

**Cara:** `scripts/eksplorasi/uji_kelayakan_entitas.py` menerapkan aturan A2.3 (setelah koreksi: domain dan
nomor hanya pendukung) pada keputusan modus evaluasi eksternal yang tersimpan, tanpa panggilan LLM. Teks kutipan
dibangun ulang dari berkas pelabelan lokal dan dicocokkan dengan `sha256_kutipan` di `testset/eksternal_butir.json`.
Daftar lembaga (58 entri) dan program (21 entri) di skrip disusun dari pengetahuan umum tentang nama lembaga dan
program pemerintah, sebelum skrip dijalankan; daftar itu **bukan** daftar resmi yang akan dikunci. Keluaran
lokal: `data/eksplorasi/uji_kelayakan_entitas.json` (kode butir dan status saja).

**Hasil (47 butir yang dijawab "ditemukan": 36 benar, 10 kecocokan palsu, 1 artikel salah):**

| Ukuran | Hasil |
| --- | --- |
| Kecocokan palsu yang turun menjadi "pola mirip" | **0 dari 10** |
| Jawaban benar yang ikut turun | **2 dari 36** (P2-21, P2-31) |
| Artikel salah yang turun | 0 dari 1 |
| "Tidak dapat dibandingkan": lembaga / program / nominal | 35 / 36 / 35 dari 47 |
| Entitas terbaca di pesan: lembaga / program / nominal | 16 / 11 / 14 dari 47 |
| Entitas terbaca di artikel: lembaga / program / nominal | 12 / 14 / 17 dari 47 |
| Pesan dengan kata penanda lembaga ("kementerian", "badan", "PT", "bank", ...) tetapi tidak ada lembaga yang cocok dengan daftar (perkiraan meleset) | 7 dari 47 |
| Bukti pendukung domain sama persis / nomor sama persis | 2 / 0 |

**Rincian per butir** (S = sama, B = bertentangan, - = tidak dapat dibandingkan; L = lembaga, P = program,
N = nominal):

| Hasil Versi 1 | Butir dan status (L/P/N) | Jawaban Versi 2 |
| --- | --- | --- |
| Kecocokan palsu | P1-15 S/-/-, P1-16 -/-/-, P1-17 -/S/-, P1-21 -/-/-, P1-23 -/S/-, P2-17 -/-/S, P2-2 -/S/-, P2-33 -/S/-, P2-38 -/S/S, P2-41 -/-/- | semuanya "klaim sama" |
| Benar, ikut turun | P2-21 S/S/B, P2-31 -/-/B | "pola mirip" |
| Benar, tetap | 34 butir lain; status "sama" pada sedikitnya satu entitas di 18 butir, sisanya seluruhnya "-" | "klaim sama" |
| Artikel salah | P2-1 S/-/S (domain sama persis) | "klaim sama" |

**Pemeriksaan lokal atas dua jawaban benar yang turun** (nilainya tidak dicatat di sini): P2-21 memang menyebut
nominal yang berbeda dari artikelnya, dan pasangan itu terpaut 37 hari (gelombang lain dengan nominal baru).
P2-31 turun karena pola nominal salah membaca angka di artikel (kesalahan pola).

**Mengapa tidak ada kecocokan palsu yang tertangkap.** Menurut adjudikasi (`rancangan_evaluasi_eksternal.md`
11.9), 7 dari 10 kecocokan palsu sebenarnya kesalahan label, jadi wajar bila entitasnya sama. Tiga sisanya
tetap kesalahan sistem, dan perbedaannya bukan pada lembaga, program, atau nominal:

| Butir | Perbedaan menurut catatan adjudikasi | Tertangkap entitas A2.1? |
| --- | --- | --- |
| P2-17 | tokoh yang disebut berbeda | Tidak; tokoh tidak diperiksa (A2.4) |
| P2-33 | tindakan berbeda (pendaftaran sudah dibuka vs program itu ada) | Tidak; tindakan tidak diperiksa |
| P2-38 | artikel tidak menyebut nominal dan jumlah penerima | Tidak; menurut aturan 4 baru justru "tidak dapat dibandingkan" |

**Kriteria lanjut atau berhenti** (ditulis 2026-10-26 **setelah** hasil di atas dilihat, jadi bukan
pra-registrasi; dicatat supaya keputusannya bisa diperiksa):

- **Lanjut** dengan rancangan daftar bila: minimal 2 dari 3 kecocokan palsu yang terkonfirmasi kesalahan sistem
  (P2-17, P2-33, P2-38) turun, **dan** jawaban benar yang turun paling banyak 2 dari 36, **dan** "tidak dapat
  dibandingkan" paling banyak 50% per entitas inti.
- **Tinjau ulang** bila salah satu tidak terpenuhi.

**Hasilnya: TINJAU ULANG.** Tidak satu pun dari 3 kecocokan palsu yang terkonfirmasi turun, dan "tidak dapat
dibandingkan" 74-77% per entitas. Batas "benar yang turun" terpenuhi (2 dari 36), tetapi salah satunya karena
kesalahan pola.

**Pilihan tinjauan ulang** (diputuskan pemilik proyek 2026-10-26: pilihan 1 diuji secara eksploratif, dengan yang diukur adalah ketepatan ekstraksi; keputusan 8, A2.6):

1. **Ekstraksi unsur inti dengan LLM.** Satu panggilan per pesan untuk mengambil subjek atau lembaga atau tokoh,
   tindakan, tawaran, dan nominal dalam bentuk terstruktur. Unsur artikel diambil sekali secara luring dan
   disimpan. Pembandingannya tetap aturan deterministik. Kelebihannya, tokoh dan tindakan (P2-17, P2-33) bisa
   tertangkap. Kekurangannya: menambah 1 panggilan per pemeriksaan (sekitar 450 + 300 panggilan tambahan untuk
   evaluasi), dan keluaran LLM bisa keliru atau berubah antar-run, jadi perlu diukur kesepakatannya.
2. **Perbaiki daftar saja** (daftar resmi yang lebih lengkap, sinonim). Murah dan tetap deterministik, tetapi
   tidak menyentuh penyebab pada tiga kesalahan terkonfirmasi, jadi kemungkinan hasilnya tetap mendekati nol.
3. **Persempit Versi 2 menjadi pengukuran dan tampilan:** set (a) untuk mengukur salah menuduh, tiga jenis jawaban
   di tampilan, dan tombol salin klarifikasi, tanpa mengklaim perbaikan kecocokan palsu. Perbaikan kecocokan palsu
   ditunda sampai ada pendekatan yang lolos uji kelayakan.

Usul saya: **pilihan 1 diuji dulu secara eksploratif dengan cara yang sama**, pada 47 butir yang sama dan dengan
kriteria lanjut yang sama, sebelum memutuskan. Biayanya sekitar 47 panggilan untuk pesan, ditambah unsur
artikel yang diambil sekali. Bila pilihan 1 juga gagal, ambil pilihan 3.

**Aturan yang diubah karena analisis ini (dicatat sebagai DIUBAH):**

- A2.4: pencatutan tokoh dan perbedaan tindakan ditambahkan sebagai batas yang diketahui. Keputusan tidak menambah
  entitas tokoh diambil setelah melihat P2-17.
- A6 aturan 4 dan aturan 3: pertentangan nominal antar-gelombang muncul dari P2-21. Diputuskan pemilik proyek
  (keputusan 9): bila gelombang jelas berbeda, nominal yang berbeda tidak membuat klaim menjadi berbeda.
  **[DIGANTIKAN 2026-10-27, keputusan 23]:** nominal eksplisit yang berbeda kini selalu membuat pasangan bukan klaim
  sama, juga lintas gelombang (A6 aturan 4, A6.2).
- Tidak ada daftar lembaga atau program di skrip yang diubah setelah hasil dilihat.
- **Perbaikan pola setelah hasil dilihat (2026-10-26):** pola nominal membaca jumlah reaksi media sosial
  ("... ribu tanda suka", "... ribu komentar") sebagai uang pada artikel P2-31. Angka bersatuan tanpa "Rp" yang
  langsung diikuti kata hitungan media sosial kini tidak dihitung. Hasil A2.5 di atas adalah hasil SEBELUM perbaikan;
  hasil sesudahnya ditulis di A2.7.

**Hasil setelah perbaikan pola nominal (dijalankan ulang 2026-10-26, tanpa LLM; masih EKSPLORATIF):**

| Ukuran | Sebelum perbaikan | Sesudah perbaikan |
| --- | --- | --- |
| Kecocokan palsu yang turun | 0 dari 10 | 0 dari 10 |
| Jawaban benar yang ikut turun | 2 dari 36 (P2-21, P2-31) | **1 dari 36** (P2-21) |
| "Tidak dapat dibandingkan": lembaga / program / nominal | 35 / 36 / 35 | 35 / 36 / 36 |
| Nominal terbaca di artikel | 17 dari 47 | 16 dari 47 |

P2-31 kini "tidak dapat dibandingkan" pada nominal (jumlah reaksi media sosial tidak lagi dibaca sebagai uang). P2-21
tetap turun, karena nominalnya memang berbeda; menurut aturan 4 yang baru (keputusan 9), kasus seperti ini tetap klaim
sama bila periodenya eksplisit dan berbeda di kedua sisi, jadi sistem perlu membaca periode (A2.1). Kriteria lanjut
tetap tidak terpenuhi. **[Catatan 2026-10-27]:** keputusan 9 digantikan keputusan 23; menurut aturan 4 yang berlaku
sekarang P2-21 bukan klaim sama (A6.2). Hasil A2.5 sendiri tidak berubah.

### A2.6 Rencana uji ketepatan ekstraksi unsur inti dengan LLM (EKSPLORATIF; ditulis dan di-commit SEBELUM dijalankan) **[MASIH BERLAKU, sebagai riwayat]**

**Aturan baru pemilik proyek (2026-10-26):** untuk analisis apa pun, kriteria ditulis dan di-commit sebelum skrip
dijalankan. Bagian ini mengikuti aturan itu. Hasilnya ditulis di A2.7 setelah dijalankan.

**Tujuan.** Mengukur **ketepatan ekstraksi** per unsur (keputusan pemilik proyek), bukan jumlah kecocokan palsu yang
tertangkap. Data yang dipakai sudah pernah dilihat, jadi hasilnya hanya menjawab "apakah LLM bisa mengambil unsur
dengan tepat", bukan "apakah Versi 2 bekerja".

**Data.** 47 pesan (kutipan Liputan6 dari butir evaluasi eksternal yang dijawab "ditemukan") dan 45 artikel
TurnBackHoax yang dipilih sistem untuk butir itu (judul + Narasi + Kesimpulan). Teks dan hasil hanya disimpan di
`data/eksplorasi/` (di-gitignore).

**Alat.** `scripts/eksplorasi/uji_ekstraksi_llm.py`. Modul ini memakai lapisan penyedia `src/llm/` (pembatas laju
dan buku besar kuota yang sama dengan evaluasi) dan tidak menyentuh `src/generator.py`. Model:
`gemini-3.5-flash-lite`, `thinking_level` medium (sama dengan generator), keluaran terstruktur dengan skema JSON.

**Prompt** (teks lengkap di `SYSTEM_PROMPT` modul itu): LLM diminta mencatat hanya yang tertulis eksplisit, tanpa
menilai benar-salah dan tanpa pengetahuan luar. Untuk artikel, unsur diambil dari klaim yang diperiksa, bukan dari
bantahan pemeriksa fakta. Unsur yang diambil:

| Unsur | Isi | Bentuk |
| --- | --- | --- |
| subjek | lembaga, instansi, perusahaan, atau tokoh yang menawarkan, mengumumkan, atau melakukan sesuatu dalam klaim; pihak yang hanya disebut sebagai latar tidak dimasukkan | daftar `{nama, jenis: lembaga atau tokoh}` |
| tawaran | program, bantuan, lowongan, hadiah, atau keuntungan; bila bukan tawaran, pokok klaim dalam frasa pendek | teks |
| tindakan | apa yang diklaim terjadi atau diminta dari pembaca (mis. "pendaftaran dibuka") | teks |
| nominal | semua jumlah uang yang disebut; jumlah suka, komentar, atau tayangan bukan nominal | daftar |
| saluran | tautan, domain, nomor telepon atau WhatsApp, atau aplikasi tempat pembaca diminta mendaftar atau menghubungi | daftar |
| periode | tanggal, bulan, tahun, atau gelombang yang disebut sebagai waktu tawaran atau peristiwa | daftar |

Unsur **periode** ditambahkan di luar lima unsur yang diminta, karena aturan 4 pedoman yang baru bergantung pada
tanda gelombang (A6).

**Jalannya.** Dua run penuh (run 1 dan run 2), masing-masing 92 panggilan, total **184 panggilan** pada kuota hari
yang sama, untuk mengukur kestabilan antar-run. Galat kuota menghentikan jalan; galat lain dicatat per sumber dan
dicoba lagi.

**Pemeriksaan manual oleh pemilik proyek, tanpa AI.** Lembar `data/eksplorasi/lembar_pemeriksaan_ekstraksi.xlsx`
dibuat dari run 1: satu baris per sumber (pesan butir, lalu artikelnya; artikel yang sudah muncul tidak diulang),
dengan teks sumber di sebelah hasil ekstraksi, dan kolom B/S per unsur. Definisi:

- **B (benar):** semua yang tertulis eksplisit untuk unsur itu terambil, dan tidak ada tambahan yang tidak ada di teks.
  "(tidak disebut)" juga B bila unsur itu memang tidak ada di teks. Kata-kata tidak harus persis.
- **S (salah):** ada yang terlewat, ada tambahan yang tidak ada di teks, salah jenis (lembaga/tokoh), atau unsur
  diambil dari bantahan pemeriksa fakta, bukan dari klaim.

Claude Code tidak mengisi atau menilai kolom B/S, dan hasil run 2 tidak ditampilkan di lembar supaya tidak
memengaruhi penilaian.

**Ukuran.**

- **Ketepatan** per unsur = B / (B + S), dihitung terpisah untuk pesan (47) dan artikel (45).
- **Kestabilan** per unsur = jumlah sumber yang hasil run 1 dan run 2-nya sama setelah dinormalkan (huruf kecil,
  spasi, urutan daftar), terpisah untuk pesan dan artikel.

**Kriteria lanjut atau berhenti (dikunci di commit ini, sebelum ada panggilan):**

| Keputusan | Syarat |
| --- | --- |
| **Lanjut** (ekstraksi LLM dipakai di rancangan Versi 2) | ketepatan >= 90% untuk subjek, nominal, saluran, dan periode, **dan** >= 80% untuk tawaran dan tindakan, di **kedua** sisi (pesan dan artikel); **dan** kestabilan >= 85% per unsur di kedua sisi |
| **Berhenti** (ambil pilihan "persempit Versi 2", A10) | ketepatan < 70% untuk salah satu dari subjek, tawaran, atau tindakan di salah satu sisi; **atau** kestabilan < 70% untuk salah satu unsur |
| **Tidak konklusif** | selain dua di atas. Prompt boleh direvisi sekali, tetapi uji ulangnya **wajib memakai data lain** (bukan 47 butir ini), misalnya butir set (a) yang sudah dilabeli, dengan kriteria yang sama |

Alasan angka: 90% berarti sekitar 4-5 kesalahan dari 45-47 sumber per unsur, batas yang menurut saya masih bisa
ditangani aturan pembanding; tawaran dan tindakan lebih bersifat penilaian, jadi diberi 80%. Angka ini usulan saya,
dikunci atas permintaan pemilik proyek; ia tidak berasal dari data.

**Yang juga dihitung dari lembar yang sudah diisi** (tanpa panggilan tambahan):

- Pemisahan penyebab "tidak dapat dibandingkan" pada daftar lama (A2.5): unsur **memang tidak disebut**, atau
  **daftar gagal membacanya**, memakai unsur yang ditandai B sebagai acuan
  (`uji_kelayakan_entitas.py --pisah-penyebab <lembar terisi>`). Sebelum lembar diisi, hitungan sementara memakai
  run 1 yang belum diperiksa, dan diberi label SEMENTARA.
- Dampak kuota bila ekstraksi dipakai di sistem (A8).

### A2.7 Hasil uji ekstraksi unsur inti dengan LLM (EKSPLORATIF, dijalankan 2026-10-26) **[MASIH BERLAKU, sebagai bukti]**

**EKSPLORATIF.** Rencana dan kriteria di-commit lebih dulu (A2.6, commit `96a8888`), sebelum ada panggilan.

**Pelaksanaan.** Dua run penuh, masing-masing 92 sumber (47 pesan, 45 artikel): **184 panggilan**, 0 gagal, 0 sumber
yang perlu diulang. Buku besar kuota: 127 panggilan di hari Pasifik 2026-10-25 dan 57 di 2026-10-26 (reset kuota
pukul 14.00 WIB terjadi di tengah jalan). Hasil lokal: `data/eksplorasi/ekstraksi_run1.jsonl` dan `_run2.jsonl`.

**Kestabilan antar-run** (sama setelah dinormalkan, ukuran yang dikunci di A2.6):

| Unsur | Pesan (47) | Artikel (45) |
| --- | --- | --- |
| subjek | 38 (81%) | 33 (73%) |
| tawaran | **28 (60%)** | **20 (44%)** |
| tindakan | **20 (43%)** | **23 (51%)** |
| nominal | 46 (98%) | 44 (98%) |
| saluran | 42 (89%) | 41 (91%) |
| periode | 42 (89%) | **26 (58%)** |

Huruf tebal: di bawah 70%.

**Keputusan menurut kriteria yang dikunci: BERHENTI.** Kriteria A2.6 menyatakan berhenti bila kestabilan salah satu
unsur di bawah 70%. Lima nilai di bawah 70% (tawaran dan tindakan di kedua sisi, periode di artikel). Keputusan ini
sudah pasti dari kestabilan saja: hasil pemeriksaan ketepatan, apa pun nilainya, tidak bisa mengubahnya, karena
kriteria "lanjut" juga mensyaratkan kestabilan >= 85% per unsur. Sesuai A2.6, pilihannya adalah "persempit Versi 2"
(A10).

**Catatan jujur tentang ukuran kestabilan.** Ukuran "sama setelah dinormalkan" keras untuk unsur teks bebas: dua
frasa berbeda dengan makna sama dihitung tidak stabil. Kriterianya tidak diubah setelah hasil keluar. Untuk melihat
apakah ketidakstabilan itu soal kata-kata atau soal isi, saya menghitung satu analisis tambahan (**EKSPLORATIF,
dibuat setelah hasil di atas dilihat; tidak mengubah keputusan**): tumpang tindih kata antara run 1 dan run 2 pada
pasangan yang tidak sama.

| Unsur | Pasangan tidak sama (pesan / artikel) | Salah satu run kosong | Median tumpang tindih kata, sisanya |
| --- | --- | --- | --- |
| subjek | 9 / 12 | 1 / 1 | 0,75 / 0,75 |
| tawaran | 19 / 25 | 4 / 1 | 0,67 / 0,63 |
| tindakan | 27 / 22 | 1 / 1 | **0,33 / 0,33** |
| periode | 5 / 19 | 0 / **8** | 0,67 / 0,50 |

Pembacaan:

- **Subjek dan tawaran:** sebagian besar perbedaannya soal kata-kata. Ukuran kestabilan semantik (diperiksa manusia)
  kemungkinan akan menaikkan angkanya.
- **Tindakan:** perbedaannya soal isi. LLM tidak konsisten memutuskan apa "tindakan" dalam sebuah klaim, padahal
  tindakan adalah pembeda pada salah satu kesalahan sistem yang terbukti (P2-33).
- **Periode di artikel:** pada 8 artikel, satu run mengisi periode dan run lain mengosongkannya. Aturan nominal
  antar-gelombang (keputusan 9) bergantung pada periode, jadi ketidakstabilan ini langsung memengaruhi keputusan.
  **[Catatan 2026-10-27]:** keputusan 9 digantikan keputusan 23, tetapi periode tetap menentukan lewat aturan 3, jadi
  pembacaan ini tetap berlaku.
- **Nominal dan saluran** stabil (89-98%). Bagian yang deterministik (pola teks) untuk nominal juga sudah bekerja
  cukup baik pada daftar lama (lihat pemisahan penyebab di bawah).

**Pelajaran untuk uji berikutnya:** untuk unsur teks bebas, kestabilan sebaiknya didefinisikan secara semantik (dua
hasil dinilai manusia "bermakna sama"), dan definisi itu dikunci sebelum dijalankan. Ini dicatat sebagai pelajaran,
bukan alasan mengulang uji ini dengan kriteria baru.

**Ketepatan per unsur:** belum dihitung. Lembar `data/eksplorasi/lembar_pemeriksaan_ekstraksi.xlsx` sudah dibuat
(92 baris, hasil run 1, kolom B/S per unsur). Karena keputusan sudah pasti, pengisiannya **tidak wajib** untuk keputusan
ini. Gunanya bila diisi: mengetahui apakah hasil yang stabil juga tepat, dan menyelesaikan pemisahan penyebab di bawah
dengan acuan yang sudah diperiksa. Bila diisi, cukup kolom subjek dan nominal (sekitar 1 jam), karena kedua unsur itu
yang dipakai pemisahan penyebab.

**Pemisahan penyebab "tidak dapat dibandingkan" pada daftar lama (A2.5), SEMENTARA** (acuan: hasil run 1 yang belum
diperiksa; dihitung per sisi, 47 butir x 2 sisi):

| Entitas daftar | Daftar tidak membaca | Memang tidak disebut | Daftar gagal membaca | Catatan |
| --- | --- | --- | --- | --- |
| Lembaga | 66 | 41 | **25** | acuan = subjek berjenis lembaga |
| Program | 69 | 2 | 67 | **tidak bermakna**: acuan "tawaran" jauh lebih luas daripada daftar program spesifik, jadi hampir semua sisi punya "tawaran" |
| Nominal | 64 | **60** | 4 | daftar nominal hampir selalu benar; yang tidak terbaca umumnya memang tidak menyebut nominal |

Pembacaan sementara: untuk lembaga, sekitar sepertiga dari yang tidak terbaca adalah kegagalan daftar (nama yang
tidak ada di daftar, singkatan, atau ejaan lain); dua pertiga memang tidak menyebut lembaga. Untuk nominal, hampir
semuanya memang tidak disebut. Angka ini menjadi final bila kolom subjek dan nominal di lembar sudah diisi
(`uji_kelayakan_entitas.py --pisah-penyebab <lembar terisi>`).

**Akibatnya bagi rancangan.** Pemilik proyek menerima keputusan BERHENTI (keputusan 13): A2.1-A2.4 tidak berlaku lagi,
dan Versi 2 tidak memakai pemeriksaan entitas maupun "pola mirip".

## A3. Urutan kerja yang menjaga kejujuran evaluasi

### A3.1 Apakah kunci dua tahap masih perlu?

Alasan awal kunci dua tahap adalah supaya **kode keputusan** (pemeriksaan entitas) boleh ditulis sesudah Kunci 1,
sebelum data set (b) ada. Kode itu kini tidak ada. Pertanyaannya: apakah satu kunci di Januari 2027 sudah cukup?

**Penilaian saya: dua tahap masih perlu, tetapi alasannya berubah.** Yang sekarang dilindungi bukan kode, melainkan
**urutan definisi sebelum data**:

1. **Pedoman harus dikunci sebelum set (b) dilabeli.** Pelabelan set (b) membutuhkan pedoman final. Dengan satu kunci
   di Januari, pedoman masih bisa berubah selama pemilik proyek melihat butir set (b) satu per satu, sehingga aturan
   bisa (tanpa sengaja) disesuaikan dengan butir yang sedang dilabeli. Ini persis masalah yang ditunjukkan catatan
   adjudikasi lama: keputusan dibuat dari kesan "narasi sama". Mengunci pedoman lebih dulu adalah satu-satunya cara
   memastikan label set (b) mengikuti aturan yang ditetapkan sebelum datanya ada.
2. **Set (a) dan pedoman bisa selesai sekarang, tiga bulan sebelum set (b).** Tanpa kunci awal, keduanya tetap bisa
   diubah selama tiga bulan, sementara pemilik proyek terus melihat keluaran demo. Kunci awal dengan bukti waktu luar
   menutup celah itu.
3. **Biayanya kecil:** satu commit, satu tag, satu Release, dan tiga snapshot Internet Archive.

**Argumen untuk satu kunci, dan mengapa tidak saya pilih:** kode sistem Versi 1 tidak bisa berubah, jadi tidak ada risiko
kode disetel pada data, dan satu kunci lebih sederhana. Tetapi risiko yang tersisa justru ada di sisi label, bukan
kode, dan satu kunci di Januari tidak melindungi pedoman selama pelabelan set (b).

### A3.2 Isi kedua kunci

| | **Kunci 1** (setelah pedoman dan set (a) selesai) | **Kunci 2** (Januari 2027, sebelum evaluasi set (b)) |
| --- | --- | --- |
| Pedoman | **Sudah dikunci lebih dulu** lewat tag `annotation-guide-v2.0` (A6.5); Kunci 1 mencatat tag dan hash-nya | -- |
| Set (a) | 150 butir yang sudah dilabeli dan lolos ambang kesepakatan (A7) | -- |
| Set (b) | **Prosedur saja:** periode, benih `20261026`, aturan pemilihan dan penghentian, pengecualian 100 `l6_id` lama | Butir yang sudah dilabeli dan lolos kappa |
| Metrik dan ambang | Semua (A4.d, A4.e), termasuk ambang uji pergeseran (A4.f) | -- |
| Indeks | -- | Indeks beku dan sidik jarinya (A4.c) |
| Bukti | `testset/v2.meta.json` versi 1, tag `testset-v2-kunci1`, GitHub Release, Internet Archive | `testset/v2.meta.json` versi 2, tag `testset-v2-kunci2`, GitHub Release, Internet Archive |

**Kapan evaluasi dijalankan (keputusan 17):** evaluasi set (a) segera setelah Kunci 1, dan evaluasi set (b) setelah
Kunci 2. **Masing-masing diapit uji pergeseran (A4.f): satu sebelum evaluasi dimulai, satu setelah evaluasi selesai;
jadwal per hari kuota di A8.** Risiko yang tersisa, yaitu pemilik
proyek melihat perilaku sistem pada pesan yang benar sebelum melabeli set (b), dicatat dan diterima; risikonya kecil
karena set (b) berisi klaim hoaks, bukan pengumuman resmi.

### A3.3 Pengaman yang tersisa

1. Metrik, ambang, dan prosedur set (b) dikunci di Kunci 1; pedoman dikunci lebih dulu, sebelum pelabelan apa pun
   (A6.5, revisi 6). Perubahan setelahnya dicatat sebagai penyimpangan dan membatalkan klaim pra-registrasi untuk
   bagian yang berubah.
2. Pemilik proyek melabeli set (b) **tanpa** menjalankan sistem pada butir-butirnya; sistem baru dijalankan pada set
   (b) setelah Kunci 2.
3. Anotator kedua, yang tidak tahu cara kerja sistem, menjadi pembanding untuk label pemilik proyek pada kedua set.

Pengaman lama tentang indeks pengembangan dan tidak membuka artikel periode set (b) selama menulis kode tidak
diperlukan lagi, karena tidak ada kode keputusan yang ditulis.

### A3.4 Langkah bukti waktu luar (dilakukan pemilik proyek, pada setiap kunci)

1. Commit kunci di-push ke GitHub bersama tag-nya: `git push origin main --tags`.
2. Buat GitHub Release pada tag itu, misalnya
   `gh release create testset-v2-kunci1 --title "Kunci 1 Versi 2" --notes "Pedoman, set (a), prosedur set (b), metrik dan ambang Versi 2."`.
   Tanggal rilis tercatat di GitHub.
3. Simpan tiga halaman di Internet Archive: halaman commit kunci, halaman tag, dan halaman Release. Caranya: buka
   `https://web.archive.org/save/<alamat halaman>` untuk masing-masing.
4. Catat ketiga alamat snapshot Internet Archive, beserta hash commit kunci, di commit berikutnya (misalnya di
   `testset/v2.meta.json` bagian bukti).

### A3.5 Berkas terkunci Versi 1 tetap utuh

`src/generator.py` (termasuk prompt), `src/retriever.py`, dan `src/chunker.py` tidak disentuh, dan hash-nya tetap dijaga
`tests/core/test_testset_locks.py`. Versi 2 tidak menambah modul keputusan. Perubahan kode hanya dua: tombol salin klarifikasi di lapisan tampilan
(`src/webapp/`), yang tidak mengubah keputusan, dan **pencatatan versi** di skrip evaluasi (A4.f), yang hanya menambah
kolom di berkas hasil. **Catatan:** kode yang terkunci tidak berarti perilaku sistem tidak berubah; model di balik nama
yang sama dan pustaka bisa berubah. Itu sebabnya ada uji pergeseran.
Hasil Versi 1 tetap bisa direproduksi lewat tag `testset-v1` dan `annotation-guide-v1.0`, indeks `archive/v1`, dan
cadangan indeks evaluasi 1.532 artikel (`data/backups/pre_antrean_2026-10-25`).

## A4. Set uji, indeks, dan metrik

### A4.a Set pesan benar yang mirip pola hoaks atau penipuan (150 butir; keputusan 3)

**Isi:** pengumuman resmi yang benar, dengan topik yang juga sering dipakai penipuan: bantuan sosial, lowongan
dan rekrutmen BUMN, CPNS, beasiswa, mudik gratis, haji dan umrah, dan program pendaftaran pemerintah. Topik
dipilih dari daftar kategori yang memang ada di basis data, bukan dari skor sistem.

**Sumber, `robots.txt`, dan ketentuan layanan** (diperiksa 2026-10-25 dan 2026-10-26; tidak ada data yang
diambil):

| Sumber | `robots.txt` | Ketentuan layanan atau penggunaan konten yang ditemukan |
| --- | --- | --- |
| Liputan6 (`/cek-fakta`) | tidak dilarang; tidak ada aturan khusus agen AI | Halaman [Disclaimer](https://www.liputan6.com/info/disclaimer): hanya pemberitahuan "Copyright © 2026 Liputan6.com" dan "KLY KapanLagi Youniverse All Right Reserved", serta aturan untuk konten yang dikirim pengguna. **Tidak ada pasal tentang menyalin, mengutip, atau mengambil otomatis artikel.** [Pedoman Media Siber](https://www.liputan6.com/info/pedoman-media-siber) butir 7: "Media siber wajib menghormati hak cipta sebagaimana diatur dalam peraturan perundang-undangan yang berlaku." |
| `kemensos.go.id` | `Disallow:` kosong | **Tidak ditemukan** ketentuan untuk situs utama. Halaman PPID (`ppid.kemensos.go.id`) menyebut data dan informasi yang diperoleh "dipergunakan sesuai dengan ketentuan dan perundang-undangan yang berlaku", dengan dasar UU 14/2008 tentang Keterbukaan Informasi Publik |
| `kemenag.go.id` | `Allow: /`; hanya `/admin/` dan `/private/` dilarang | **Tidak ditemukan** ketentuan untuk situs utama. Hanya subdomain yang punya ketentuan sendiri (mis. JDIH, Pusaka), dan isinya tentang layanan masing-masing |
| `bumn.go.id` | `Disallow:` kosong | **Tidak ditemukan** ketentuan untuk situs utama. JDIH BP BUMN memuat sanggahan bahwa dokumen resmi yang berlaku bila ada perbedaan |
| `dephub.go.id` | `Disallow:` kosong | **Tidak ditemukan** ketentuan untuk situs utama. Hanya kebijakan privasi di subdomain layanan |
| `www.bpjsketenagakerjaan.go.id` | `User-agent: *` tanpa larangan | **Tidak ditemukan** untuk situs utama. Ketentuan aplikasi JMO menyatakan hak cipta atas materi aplikasi dan melarang memakai logo tanpa izin tertulis; itu ketentuan aplikasi, bukan situs berita |
| `bkn.go.id` | berkas kosong | **Tidak ditemukan** ketentuan. Kaki halaman: "Hak cipta ©2021 Badan Kepegawaian Negara. Semua hak cipta dilindungi." |

Catatan: ketentuan untuk situs pemerintah dicari lewat mesin pencari, bukan dengan membuka halaman utama tiap
situs, jadi bisa ada tautan ketentuan di kaki halaman yang belum terbaca. Saya bukan penasihat hukum. Yang
relevan secara umum: set ini hanya menyimpan potongan teks pendek (judul atau kalimat inti pengumuman) beserta
alamat sumbernya, untuk penelitian nonkomersial, dan teks lengkap tidak diterbitkan. Bentuk penyimpanannya
sudah diputuskan (keputusan 10, di bawah). **KEPUTUSAN PEMILIK PROYEK:** sumber mana yang dipakai, setelah membaca
sendiri halaman hak cipta tiap situs.

**Penyimpanan (keputusan 10):** yang di-commit hanya URL, tanggal terbit, hash teks (`sha256`, seperti
`sha256_kutipan` evaluasi eksternal), dan metadata (kategori topik, label, kode butir). Potongan teks pengumuman
disimpan lokal di `data/`, sama dengan kebijakan `articles.json`. Sumber yang dipakai diputuskan pemilik proyek setelah
membaca sendiri halaman hak cipta tiap situs.

**Aturan butir:**

- "Pesan" diambil dari teks pengumuman resmi apa adanya (judul atau kalimat inti), tidak ditulis ulang. Data
  pribadi diperiksa dan dibersihkan seperti set uji sebelumnya.
- Setiap butir harus benar menurut sumber resmi pada tanggal terbitnya, dan klaimnya tidak pernah dinyatakan
  salah oleh TurnBackHoax (diperiksa manusia terhadap indeks beku).
- Label yang diharapkan: "belum ditemukan" (tidak ada artikel yang memeriksa klaim yang sama).
- Batasan yang dicatat: pengumuman resmi bahasanya lebih rapi daripada pesan berantai, jadi set ini mengukur pesan
  benar yang ditulis resmi.

**Metrik:** tingkat salah menuduh = butir yang dijawab **"ditemukan"** oleh sistem Versi 1 / 150, dengan interval
Wilson 95%.

**Ukuran sampel (dihitung dengan `evaluation.metrics.wilson_interval`, 2026-10-25).** Butir minimal agar batas
atas Wilson 95% di bawah 5% bila teramati k kali salah menuduh:

| k teramati | butir minimal |
| --- | --- |
| 0 | 73 |
| 1 | 110 |
| 2 | 142 |
| 3 | 173 |
| 4 | 202 |

Peluang berhasil membuktikan "di bawah 5%" bila tingkat sebenarnya p:

| Butir | Lolos bila k <= | p = 0,5% | p = 1% | p = 2% | p = 3% |
| --- | --- | --- | --- | --- | --- |
| 80 | 0 | 67% | 45% | 20% | 9% |
| 100 | 0 | 61% | 37% | 13% | 5% |
| 120 | 1 | 88% | 66% | 31% | 12% |
| 150 | 2 | 96% | 81% | 42% | 17% |
| 200 | 3 | 98% | 86% | 43% | 15% |

Dengan 150 butir: lolos bila salah menuduh <= 2; terbukti buruk (batas bawah > 5%) bila >= 13; di antaranya tidak
konklusif.

### A4.b Sampel klaim baru untuk recall dan kecocokan palsu (prosedur dikunci di Kunci 1)

- **Sumber:** Liputan6 Cek Fakta, seperti evaluasi eksternal.
- **Periode:** artikel yang terbit **28 September-31 Desember 2026** (keputusan 4). Tidak tumpang tindih dengan
  sampel lama (terbit 30 September 2025-27 September 2026, B.10.2). Seluruh 100 `l6_id` sampel lama dikeluarkan
  secara eksplisit.
- **Benih acak:** **`20261026`**, dicatat sekarang, sebelum ada artikel periode itu yang dikumpulkan untuk Versi 2.
- **Cara memilih:** pencacahan lewat halaman indeks per tanggal Liputan6 (`/cek-fakta/indeks/YYYY/MM/DD`) untuk
  seluruh tanggal di periode itu; daftar artikel kasus tunggal ("Cek Fakta: ...") diacak dengan benih di atas;
  butir diproses berurutan menurut hasil acak. Aturan kutipan yang tidak memuat klaim (K1 dan K2,
  `rancangan_evaluasi_eksternal.md` 2.2) dipakai apa adanya.
- **Aturan penghentian:** pengolahan berhenti setelah 50 positif **dan** 50 negatif terkumpul menurut label
  pemilik proyek, atau setelah 200 artikel diproses, mana yang lebih dulu. Bila batas 200 tercapai sebelum salah
  satu jenis mencapai 50, jumlah yang ada dipakai, dan ambang dihitung dengan aturan Wilson pada n yang sebenarnya.
- **Konsekuensi waktu:** pengambilan dimulai Januari 2027. Indeks evaluasi memuat artikel TurnBackHoax sampai
  sekitar pertengahan Januari 2027 (efek ujung rentang, B.11.3).
- **Ambang pada 50 butir per jenis:** positif memadai bila benar >= 37/50; kecocokan palsu gugur bila >= 10/50,
  lolos bila <= 4/50.

### A4.c Indeks evaluasi Versi 2 (dikunci di Kunci 2)

- Setelah antrean sampai pertengahan Januari 2027 di-ingest, indeks produksi **disalin** menjadi indeks beku,
  misalnya `data/backups/snapshot_v2_<tanggal>/`. Indeks tidak disimpan di `archive/` dan tidak di-commit.
- `index_check` dan `retriever_exactness` dijalankan pada salinan, dan sidik jari isinya (7 kunci, seperti
  `indeks_beku` evaluasi eksternal) dicatat di `testset/v2.meta.json` sebelum Kunci 2 di-push.
- Indeks demo tetap bertambah setiap hari dan tidak dipakai untuk evaluasi Versi 2. Salinan beku dibuka hanya lewat
  salinan kedua (ChromaDB menulis ulang berkas saat dibuka).
- Uji pergeseran (A4.f) tetap memakai `archive/v1` dengan set uji v1 (aturan wajib #6).

### A4.d Cara menghitung

Sistem Versi 1 hanya punya dua jawaban, jadi perhitungannya langsung:

| Set | Jawaban sistem | Dihitung sebagai |
| --- | --- | --- |
| (a) pesan benar | "ditemukan" (artikel apa pun) | **salah menuduh** |
| (a) pesan benar | "belum ditemukan" | benar |
| (b) positif | "ditemukan" + artikel yang benar (atau salah satu artikel sah, A6 aturan 7) | benar |
| (b) positif | "ditemukan" + artikel lain | artikel salah (dilaporkan terpisah) |
| (b) positif | "belum ditemukan" | penolakan palsu |
| (b) negatif | "ditemukan" | **kecocokan palsu** |
| (b) negatif | "belum ditemukan" | benar |

Keputusan per butir = keputusan modus dari 3 run, seperti evaluasi sebelumnya.

**Butir ragu (keputusan 43; dikunci di Kunci 1).** Metrik utama memakai label akhir semua butir, termasuk butir yang
ditandai ragu. Analisis sensitivitas menghitung ulang setiap metrik tanpa butir ragu, seperti di evaluasi eksternal.
Hasil sensitivitas tidak menggantikan hasil utama. **Butir ragu = butir yang ditandai ragu oleh salah satu pelabel**
(pemilik proyek atau anotator kedua; keputusan 50). Untuk butir yang hanya dilabeli pemilik proyek, yang berlaku tanda
ragunya sendiri.

### A4.e Ambang (dikunci di Kunci 1)

| Metrik | Set | Memadai / lolos | Gugur |
| --- | --- | --- | --- |
| Salah menuduh | (a), 150 | batas atas Wilson < 5% (salah <= 2) | batas bawah > 5% (salah >= 13) |
| Ketepatan positif | (b), 50 | batas bawah >= 60% (benar >= 37) | batas bawah < 60% |
| Kecocokan palsu | (b), 50 | batas atas <= 20% (<= 4) | batas bawah > 10% (>= 10) |

Di antara "lolos" dan "gugur" berarti **tidak konklusif**. Bila jumlah butir set (b) bukan 50, ambang dihitung dengan
aturan Wilson yang sama pada n yang sebenarnya.

**Koreksi revisi 4:** revisi 3 juga menghapus ambang kemunduran Versi 1 dengan alasan "sistem tidak berubah". Alasan itu
hanya benar untuk kode kita; model Gemini dan pustaka bisa berubah. Ambang itu dipertahankan sebagai **uji pergeseran**
(A4.f, keputusan 19).

**Ambang yang gugur bersama pemeriksaan entitas** (disetujui di revisi 1, tidak berlaku lagi karena Versi 2 tidak
mengubah keputusan sistem):

| Ambang lama | Mengapa tidak relevan |
| --- | --- |
| "Terlalu berhati-hati" (Versi 2 menurunkan jawaban benar Versi 1) | Tidak ada "pola mirip" dan tidak ada penurunan jawaban |
| Perbandingan Versi 1 dan Versi 2 (McNemar) | Keputusan Versi 1 dan Versi 2 identik; tidak ada yang dibandingkan |

**Perbandingan dengan evaluasi eksternal lama** (36/46 dan 10/45) hanya deskriptif. Set, periode, pedoman, dan
anotatornya berbeda, jadi selisihnya tidak boleh dibaca sebagai perubahan sistem.

### A4.f Uji pergeseran (keputusan 19; ambang dikunci di Kunci 1)

**Mengapa perlu.** Kode keputusan Versi 1 terkunci, tetapi tiga hal di luar kode bisa berubah tanpa diketahui:

1. **Model Gemini.** Proyek memakai `gemini-3.5-flash-lite`. Menurut halaman model resmi
   (https://ai.google.dev/gemini-api/docs/models, diperiksa 2026-10-26), nama itu tercantum sebagai model **Stable**,
   dengan definisi "Points to a specific stable model. Stable models usually don't change." Kata kuncinya *usually*:
   tidak ada jaminan. **Tidak ada versi bertanggal atau bernomor** untuk model ini (seperti `-001`) yang bisa dipatok.
   Konfigurasi tidak diubah.
2. **Informasi versi dari API.** Respons Interactions API di `google-genai` 2.24.0 punya medan `model`, `id`, `created`,
   `updated`, `usage`, dan `service_tier`, tetapi **tidak punya medan versi model khusus** (berbeda dengan
   `generateContent`, yang punya `modelVersion`). Apakah medan `model` di respons berisi nama yang sudah diselesaikan
   server belum diperiksa. Pemeriksaannya dilakukan pada **panggilan nyata pertama berikutnya**; tidak ada panggilan
   khusus hanya untuk itu. Berkas hasil evaluasi lama hanya menyimpan nama model yang diminta.
3. **Pustaka** seperti ChromaDB, sentence-transformers, transformers, dan torch. Versinya dipatok di `requirements.txt`,
   tetapi lingkungan bisa berbeda bila venv dibangun ulang.

**Cara kerja.**

1. Set uji v1 (54 butir) dijalankan ulang 3 run pada `archive/v1` (`ef_search` 100), sesuai aturan wajib #6. Uji ini
   **mengapit** setiap evaluasi: **uji awal** di hari kuota pertama sebelum evaluasi dimulai, dan **uji akhir** setelah
   evaluasi selesai, untuk set (a) maupun set (b). Uji akhir diulang penuh (54 butir x 3 run), bukan subset: subset
   membuat ambang di bawah tidak berlaku lagi, padahal ulangan penuh masih muat di dua hari kuota (jadwal di A8).
2. Keputusan modus per butir (vonis dan `article_id`) pada uji awal dan pada uji akhir masing-masing dibandingkan dengan
   keputusan modus dari 3 run yang tersimpan di `data/testset_v1_eval_gemini-3.5-flash-lite.jsonl`, dengan ambang yang
   sama.
3. Top-3 retrieval per butir dibandingkan dengan yang tersimpan. Bagian ini deterministik dan tidak memanggil LLM.

**Membedakan pergeseran dari keacakan biasa.** Pembandingnya adalah variasi antar-run yang sudah tercatat pada evaluasi
lama yang sama:

- Dari 54 butir, **48 bulat** di ketiga run dan **6 tidak bulat** (2-1: v1-006, v1-010, v1-036, v1-039, v1-040, v1-053).
- Top-3 retrieval identik di ketiga run untuk **54 dari 54** butir.
- Model keacakan (berhati-hati): pada butir bulat, peluang satu run menyimpang dianggap sebesar batas atas Wilson 95% dari
  0 penyimpangan dalam 144 keputusan, yaitu **2,6%**; pada butir tidak bulat, **1/3**. Modus baru berbeda bila sedikitnya
  2 dari 3 run baru jatuh ke keputusan lain. Hasilnya: peluang modus berubah 0,2% per butir bulat dan 25,9% per butir
  tidak bulat.

| Jumlah butir yang modusnya berubah, karena keacakan saja | Peluang | Kumulatif |
| --- | --- | --- |
| 0 | 15,0% | 15,0% |
| 1 | 33,0% | 48,0% |
| 2 | 30,7% | 78,7% |
| 3 | 15,7% | 94,3% |
| 4 | 4,7% | 99,1% |
| 5 | 0,9% | 99,9% |

Peluang sedikitnya 1 butir **bulat** berubah karena keacakan: 9,1%; sedikitnya 2: 0,4%. Rata-rata total yang berubah:
1,65 butir.

Batas model ini: ia menganggap run dan butir saling bebas, padahal 44% butir set uji v1 berbagi artikel jangkar; jadi
angkanya perkiraan, bukan peluang yang tepat.

**Ambang (disetujui pemilik proyek di revisi 5, keputusan 20; dikunci di Kunci 1):**

| Hasil | Syarat |
| --- | --- |
| **Tidak terdeteksi pergeseran** | top-3 retrieval identik 54/54, **dan** modus berubah pada paling banyak 1 butir yang dulu bulat, **dan** total modus berubah paling banyak 4 butir |
| **Pergeseran retrieval** | ada top-3 yang berbeda. Penyebabnya pasti di luar LLM (pustaka, indeks, atau lingkungan); evaluasi ditunda sampai penyebabnya ditemukan |
| **Pergeseran model** | top-3 identik, tetapi modus berubah pada >= 2 butir yang dulu bulat, **atau** total >= 5 butir |

**Arti hasil "Tidak terdeteksi pergeseran".** Dengan 54 butir, uji ini hanya bisa menangkap perubahan besar. Hasil itu
berarti tidak ada perubahan yang cukup besar untuk tertangkap, **bukan** bukti bahwa model dan pustaka sama. Laporan
hasil evaluasi memakai kalimat itu, tidak memakai "model tidak berubah" atau "sebanding".

**Membaca dua uji yang mengapit:**

| Uji awal | Uji akhir | Laporan |
| --- | --- | --- |
| Tidak terdeteksi | Tidak terdeteksi | Tidak terdeteksi pergeseran selama rentang evaluasi |
| Tidak terdeteksi | Pergeseran | Pergeseran mungkin terjadi **selama** evaluasi; hasil evaluasi dilaporkan dengan catatan itu, dan run yang tanggalnya berbeda dilaporkan terpisah |
| Pergeseran | apa pun | Pergeseran sudah ada sebelum evaluasi (lihat akibat di bawah) |

Pergeseran retrieval pada uji awal menunda evaluasi, jadi uji akhir baru dijalankan setelah evaluasi yang tertunda itu
selesai.

**Akibat bila terjadi pergeseran model:** evaluasi tetap boleh dijalankan, tetapi hasilnya dilaporkan **tidak sebanding**
dengan angka evaluasi lama, dan, bila pergeseran terdeteksi di antara evaluasi set (a) dan set (b), hasil kedua set
juga dilaporkan tidak sebanding satu sama lain. Pergeseran dilaporkan apa adanya, termasuk butir yang berubah.

**Yang dicatat pada setiap evaluasi (set a, set b, dan uji pergeseran):**

- nama model yang diminta, `thinking_level`, dan seluruh medan respons yang tersedia (`model`, `id`, `created`, `updated`,
  `service_tier`, `usage`) per panggilan;
- versi Python dan versi pustaka yang terpasang (`google-genai`, `chromadb`, `sentence-transformers`, `transformers`,
  `torch`), revisi bge-m3 (`ingest.MODEL_REVISION`), dan sidik jari indeks yang dipakai;
- tanggal dan jam (UTC) setiap run.

Skrip evaluasi sekarang belum mencatat medan respons dan versi pustaka. Menambahkannya adalah perubahan kecil di skrip
evaluasi, bukan di kode keputusan, dan harus selesai sebelum Kunci 1 (A12).

## A5. Ukuran kegunaan nyata: jeda sampai hoaks bisa ditemukan

Diukur tanpa LLM, dari data yang sudah tercatat:

1. **Jeda pemeriksaan:** tanggal terbit artikel TurnBackHoax dikurangi tanggal terbit artikel Liputan6 yang cocok
   (set b). Ini perkiraan kapan hoaks mulai beredar, karena tanggal beredar sebenarnya tidak diketahui.
2. **Jeda pengambilan:** tanggal artikel masuk antrean (`data/expansion/forward_<tanggal>.json`,
   `pembaruan_riwayat.jsonl`) dikurangi tanggal terbitnya.
3. **Jeda ingest:** tanggal ingest (catatan di CLAUDE.md) dikurangi tanggal masuk antrean. Antrean yang di-ingest
   2026-10-25 memuat artikel yang sudah menunggu sejak 3 Oktober, jadi jeda ini kemungkinan yang terbesar dan paling
   bisa diperbaiki.

Hasil dilaporkan sebagai median dan rentang, tanpa ambang. Batasannya: ini jeda menurut satu situs cek fakta
pembanding, bukan menurut kapan pengguna menerima pesan.

## A6. Pedoman "klaim sama" untuk pola pendaftaran atau tawaran (disetujui lewat lembar 2026-10-27; revisi 7: K1-K13 diputuskan; DRAF; revisi 8: keputusan 44-51 belum diterapkan ke teks aturan di bawah, menunggu prinsip utama A6.10; dikunci lewat tag sebelum pelabelan, A6.5)

Pedoman ini mengatur **label** (apa yang dianggap klaim sama oleh manusia). Ia tidak mengubah cara sistem memutuskan.

**Teks untuk pelabelan** ada di dokumen yang berdiri sendiri, [`testset/ANNOTATION_GUIDE_v2.md`](../../testset/ANNOTATION_GUIDE_v2.md)
(pedoman 2.0), untuk pemilik proyek dan anotator kedua. Dokumen itu memuat aturan yang sama dengan bagian ini, ditambah
definisi, contoh rekaan, urutan langkah, cara mengisi catatan wajib, dan cara menandai ragu. Bila isi aturan di kedua
tempat berbeda, itu cacat yang harus dilaporkan, bukan ditafsirkan. Riwayat teks: revisi 5 (`9b94077`), revisi 6
(`35d14e1`).

**Nama (keputusan 32).** Sejak revisi 7 istilah "butir penipuan" diganti **"pola pendaftaran atau tawaran"**, karena
pengumuman resmi bukan penipuan tetapi tetap dinilai dengan A6.

**Dasar dan prioritas (keputusan 35).** Pedoman v1.0 dan Aturan A/B evaluasi eksternal tetap menjadi dasar. Untuk
pasangan yang memakai A6, **A6 didahulukan bila bertentangan dengan v1.0**. Penyelesaian tiga titik tabrakan yang
diketahui (klaim lebih umum, keluarga artikel, jangkar KIA lawan Narasi) masih usulan (A6.8).

**Unsur inti pola pendaftaran atau tawaran (keputusan 36):** lembaga atau tokoh, tawaran (jenis program atau
keuntungan), saluran (tautan, akun, atau nomor), nominal, dan periode.

**Kapan A6 dipakai (keputusan 26).** Ditentukan per pasangan pesan-artikel. Sebuah pasangan memakai A6 bila (a) artikelnya
berlabel PENIPUAN di TurnBackHoax, atau (b) pesannya meminta pembaca mendaftar, mengisi data pribadi, mentransfer uang,
atau menghubungi tautan atau nomor atas nama lembaga atau tokoh. Pasangan lain memakai pedoman v1.0 (klaim inti, unsur
inti, uji dua arah, uji Kesimpulan). Bila ragu, catat keraguannya dan alasan pilihan aturan yang dipakai. **Lembar
pelabelan menampilkan label TurnBackHoax setiap kandidat** (keputusan 41): itu metadata artikel, bukan keluaran sistem.

**Definisi unsur:**

- **Periode (keputusan 27 dan 37):** tahun, atau nama gelombang atau tahap program (misalnya "Gelombang 2", "Tahap II").
  Tanggal batas pendaftaran atau tanggal hari tidak termasuk, karena penipuan daur ulang hampir selalu memperbarui
  tanggalnya; tanggal yang berbeda tetap dicatat di catatan wajib. **Periode hanya dibandingkan dengan jenis yang sama**
  (tahun dengan tahun, nama gelombang atau tahap dengan nama gelombang atau tahap). Jenis berbeda berarti tidak dapat
  dibandingkan, kecuali satu sisi memuat keduanya; maka yang dibandingkan adalah jenis yang ada di kedua sisi.
- **Nominal (keputusan 38):** jumlah uang yang ditawarkan atau diminta. Jumlah armada, kuota peserta, dan sejenisnya
  bukan nominal.
- **Lembaga umum (keputusan 39):** "pemerintah", "kementerian" tanpa nama, dan sejenisnya, lawan lembaga tertentu, berarti
  tidak dapat dibandingkan, sejalan dengan aturan 2.
- **Tokoh lawan lembaga yang dipimpinnya (keputusan 40):** tidak dapat dibandingkan dan ditandai ragu. Keputusannya dari
  unsur lain lewat aturan 9. Kasus seperti ini dikumpulkan saat pelabelan untuk ditinjau di versi pedoman berikutnya.
- **Saluran resmi yang terverifikasi (keputusan 32):** domain, akun, atau nomor milik lembaga yang disebut, yang
  dicocokkan pelabel dengan **sumber acuan**: (a) situs resmi lembaga itu, dibuka dari alamat yang sudah diketahui atau
  diketik sendiri, bukan dari tautan di pesan atau di sumber hoaks; atau (b) saluran yang dinyatakan resmi di Kesimpulan
  atau Referensi artikel TurnBackHoax. Cara memverifikasi:
  1. Yang dicocokkan adalah **teks alamat**. Tautan di pesan atau di sumber hoaks **tidak dibuka**.
  2. Cocok bila host sama persis dengan saluran di sumber acuan, atau subdomain sejatinya (`daftar.contoh.go.id` dari
     `contoh.go.id`). Nama yang mirip (`contoh-go-id.example`, `contoh.go.id.example`), subdomain layanan hosting, dan
     pemendek URL tidak pernah dihitung resmi kecuali persis tercantum di sumber acuan. Nomor telepon atau WhatsApp resmi
     hanya bila tercantum di sumber acuan.
  3. Sumber acuan dan tanggal pemeriksaan dicatat di catatan wajib.
  4. Pada set (a), saluran yang disebut di dalam pengumuman yang diambil dari situs resmi lembaga (A4.a) dianggap
     terverifikasi; sumber acuannya adalah URL butir itu.
  5. Bila status resmi suatu saluran tidak dapat dipastikan: saluran **tidak dapat dibandingkan**, dan pasangan
     **ditandai ragu**.

**Aturan:**

1. **Lembaga atau tokoh berbeda, tawaran sama -> BUKAN klaim sama.**
2. **Lembaga atau tokoh tidak disebut di salah satu sisi -> tidak dapat dibandingkan, bukan pertentangan.**
   Keputusan bergantung pada unsur inti lain. Lembaga umum lawan lembaga tertentu juga tidak dapat dibandingkan.
3. **Gelombang berbeda yang hanya terlihat dari tanggal terbit, lembaga dan tawaran sama -> klaim sama. Tahun atau
   periode yang tertulis di kedua teks dan berbeda -> BUKAN klaim sama** (Aturan A; keputusan 6 dan 42). Tahun atau
   periode yang hanya tertulis di satu sisi: tidak dapat dibandingkan.
4. **Nominal berbeda pada tawaran yang sama -> BUKAN klaim sama bila nominal disebut eksplisit di kedua sisi.** Ini
   berlaku juga bila gelombangnya terlihat berbeda dari tanggal terbit (kasus P2-21). Bila tahun atau periode tertulis di
   kedua teks dan berbeda, butir sudah bukan klaim sama menurut aturan 3, apa pun nominalnya. Bila hanya satu sisi
   menyebut nominal: tidak dapat dibandingkan. *Aturan ini diubah dua kali setelah melihat data, keduanya sebelum
   Kunci 1: pertama setelah A2.5 (P2-21, keputusan 9), kedua 2026-10-27 lewat lembar persetujuan, karena kalimat
   keputusan 9 bertentangan dengan pengecualian aturan 3 (keputusan 23).*
5. **Tautan atau nomor berbeda, lembaga dan tawaran sama -> klaim sama.** Penipu sering berganti tautan. Saluran berbeda
   bersifat **netral**; saluran yang sama persis dengan sumber hoaks di artikel adalah **bukti pendukung** yang kuat,
   tetapi bukan syarat. **Pengecualian saluran resmi (keputusan 32 dan 34):** bila satu sisi memakai saluran resmi
   lembaga yang terverifikasi dan sisi lain tidak, saluran **bertentangan** dan pasangan itu **BUKAN klaim sama**. Bila
   kedua sisi bukan saluran resmi, kalimat pertama aturan ini tetap berlaku.
6. **Judul sama, isi tawaran berbeda -> BUKAN klaim sama.** Yang dibandingkan adalah isi pesan dengan Narasi, bukan
   judul dengan judul.
7. **Bila lebih dari satu artikel cocok dengan pesan (lembaga dan tawaran sama), semua artikel yang sah dicatat, dan
   jawaban dinilai benar bila memilih salah satunya.** Sebuah artikel hanya sah bila, terhadap pesan itu, ia lolos
   semua aturan lain (aturan 1-6, 8, dan 9; keputusan 24): tidak ada pertentangan tahun atau periode (aturan 3),
   nominal (aturan 4), atau saluran resmi (aturan 5). Contoh P2-1 (dua artikel dengan sasaran sama tetapi tawaran
   berbeda): hanya artikel dengan tawaran yang sama yang sah.
8. **Tawaran berbeda (program spesifik berbeda) -> BUKAN klaim sama.** Istilah umum ("bansos", "bantuan",
   "lowongan") dibandingkan dengan program spesifik dihitung tidak dapat dibandingkan.
9. **Aturan bawaan (keputusan 28, 33, 34).** Klaim sama membutuhkan tawaran yang sama dan tidak ada unsur inti yang
   bertentangan. Bila tawaran tidak dapat dibandingkan, klaim sama hanya bila lembaga atau tokoh sama, setidaknya satu
   unsur lain (saluran sama persis, nominal, atau periode) sama, dan tidak ada unsur inti yang bertentangan. Bila
   keadaan kedua ini tidak memenuhi syarat: bukan klaim sama, dan butir ditandai ragu. **Penolakan karena ada unsur inti
   yang bertentangan tidak ditandai ragu oleh aturan ini.** Saluran berbeda tidak dihitung bertentangan, kecuali
   pengecualian saluran resmi (aturan 5). Alasan (pemilik proyek): aturan lain berangkat dari "lembaga dan tawaran
   sama", sehingga tidak ada keputusan ketika tawaran tidak dapat dibandingkan; di celah inilah keputusan "narasi sama"
   dulu muncul. Aturan ini sengaja condong ke "bukan klaim sama" ketika bukti kurang, sejalan dengan fokus Versi 2 pada
   salah menuduh.

**Hubungan induk dan anak lembaga (keputusan 29)** (misalnya Pertamina dan anak perusahaannya) tidak diatur sekarang.
Kasus seperti itu ditandai ragu dan dicatat saat pelabelan.

**Catatan wajib (keputusan 25).** Setiap label pada pasangan pola pendaftaran atau tawaran, baik positif maupun negatif,
wajib mencatat lembaga atau tokoh, tawaran, saluran, nominal, dan tahun atau periode di kedua sisi, beserta statusnya
(sama, bertentangan, tidak dapat dibandingkan), dan untuk saluran juga sumber acuan verifikasinya bila ada. Untuk label
negatif yang menolak kandidat terdekat, sebutkan minimal satu unsur yang bertentangan dan aturan yang dipakai;
"kandidat terdekat" berarti **kandidat yang paling mirip menurut penilaian anotator, tanpa skor retrieval**. Bila tidak
ada unsur yang bertentangan, tulis alasannya secara eksplisit. Catatan adjudikasi sebelumnya sering hanya berbunyi
"narasi sama", tanpa menyebut unsur yang dibandingkan.

**Contoh dari 11 butir adjudikasi yang berbeda dengan label final** (`rancangan_evaluasi_eksternal.md` 11.9). Teks
pesan Liputan6 tidak dikutip; yang ditulis hanya kode butir, artikel TurnBackHoax, dan pola perbedaannya:

| Butir | Label final -> adjudikasi | Artikel TurnBackHoax | Pola | Aturan yang menjawab |
| --- | --- | --- | --- | --- |
| P1-31 | cocok 32774 -> TIDAK ADA | 32774 Tautan Pendaftaran Program Mudik Gratis 2026 | pesan hanya menyebut "pemerintah"; artikel menyebut lembaga tertentu dan jumlah armada | 2 dan 4 (tidak dapat dibandingkan, bukan alasan menolak); keputusan dari tawaran |
| P1-8 | cocok 36654 -> TIDAK ADA | 36654 Tautan Pendaftaran Bansos Digital | pesan tidak menyebut lembaga dan nominal | 2 dan 4; jangan menolak hanya karena unsur tidak disebut |
| P1-28 | cocok 36654 -> TIDAK ADA | 36654 Tautan Pendaftaran Bansos Digital | judul sama, isi berbeda | 6 |
| P1-15 | TIDAK ADA -> cocok 32612 | 32612 Tautan Pendaftaran Rekrutmen PLN 2026 | catatan adjudikasi hanya "narasi sama" | 1 dan 3 |
| P1-17 | TIDAK ADA -> cocok 33548 | 33548 Pendaftaran Lowongan Petugas Haji 2026 | "konteks sama, lowongan petugas haji" | 1, 3, 8 |
| P1-21 | TIDAK ADA -> cocok 32360 | 32360 Tautan Pendaftaran Bantuan Alat Pertanian 2026 | "maksud dan konteks sama" | 1, 4, 8 |
| P2-2 (ragu) | TIDAK ADA -> cocok 31894 | 31894 Tautan Pendaftaran CPNS 2026 | dinilai tiga kali dengan hasil berbeda | 1, 3, 5 |
| P2-41 | TIDAK ADA -> cocok 36547 | 36547 Wayan Koster Bagi-Bagi Dana Bantuan | "narasi sama"; tokoh yang dicatut | 1 (tokoh) |
| P1-16 | TIDAK ADA -> cocok 32770 | 32770 Polisi: Akibat Cuaca Ekstrem, Barang Bukti Sabu Terurai Jadi Udara | bukan penipuan; "narasi sama" | pedoman v1.0 |
| P1-23 (ragu) | TIDAK ADA -> cocok 36156 | 36156 MBG Bakal Disalurkan Lewat Kartu ATM | bukan penipuan; tanpa catatan | pedoman v1.0 |
| P2-1 | cocok 31400 -> cocok 29505 | 31400 bantuan dari Bimas Kristen Kemenag; 29505 Dana Bantuan DAP 2025 untuk umat Kristen | dua artikel dengan sasaran sama, tawaran berbeda | 8, atau 7 bila keduanya sah |

Tabel ini adalah dasar penyusunan aturan. Pedoman 2.0 sengaja **tidak** memakai butir-butir ini sebagai contoh; contohnya
rekaan.

### A6.1 Pedoman dan perilaku generator Versi 1 (selisih yang diketahui)

Tabel konsistensi lama (pedoman lawan pemeriksaan entitas) tidak berlaku lagi. Yang tersisa adalah selisih antara label
menurut pedoman dan keputusan generator Versi 1 yang terkunci. Selisih ini akan muncul sebagai kesalahan dalam metrik
dan **tidak** diperbaiki Versi 2:

| Aturan pedoman | Perilaku generator Versi 1 yang teramati | Akibat di metrik |
| --- | --- | --- |
| 3. Gelombang yang hanya terlihat dari tanggal terbit -> sama | sering menolak pasangan lintas gelombang (6 dari 9 penolakan palsu evaluasi eksternal ada di pasangan > 30 hari) | penolakan palsu pada set (b) |
| 1. Tokoh berbeda -> bukan sama | tidak selalu dibedakan (P2-17) | kecocokan palsu |
| Tindakan berbeda (pedoman v1.0) | tidak selalu dibedakan (P2-33) | kecocokan palsu |
| 4. Nominal eksplisit berbeda -> bukan sama, juga lintas gelombang (keputusan 23) | belum diukur khusus; P2-21 dijawab "ditemukan" padahal menurut aturan ini bukan klaim sama (A6.2) | kecocokan palsu |
| 5. Pengecualian saluran resmi -> bukan sama | belum diukur; generator tidak memeriksa apakah saluran resmi | salah menuduh pada set (a), kecocokan palsu pada set (b) |
| 9. Bukti kurang -> bukan sama, ragu | belum diukur | pasangan berbukti tipis yang dijawab "ditemukan" dihitung kecocokan palsu; butir ragu dilaporkan juga tanpa ragu (A4.d) |

### A6.2 Dampak aturan 4 baru: P2-21 (contoh perubahan yang merugikan sistem)

Pada evaluasi eksternal, **P2-21 berlabel cocok dan dijawab benar oleh sistem** (A2.5: "jawaban benar yang ikut turun").
Menurut pemeriksaan pola A2.5, pesan dan artikelnya menyebut nominal yang berbeda, dan pasangan itu terpaut 37 hari
(gelombang lain). Keputusan 9 dulu sengaja mempertahankannya sebagai klaim sama. **Menurut aturan 4 yang berlaku sekarang
(keputusan 23), P2-21 bukan klaim sama**, sehingga seandainya pedoman 2.0 dipakai pada butir itu, jawaban benar sistem
berubah menjadi kecocokan palsu.

Jadi perubahan aturan 4 ini **merugikan sistem**: ia bukan aturan yang disetel agar angka sistem terlihat lebih baik.
Batasannya: status nominal P2-21 berasal dari pola teks (A2.5), belum diperiksa manusia dengan pedoman 2.0.

**Yang tidak berubah:** label P2-21 dan seluruh angka evaluasi eksternal. Set 99 butir itu sekali pakai dan tidak
dilabeli ulang; pedoman 2.0 hanya berlaku untuk set (a) dan set (b).

### A6.3 Lembar persetujuan dan asal-usul keputusan (2026-10-27)

**Berkas** (lokal, `data/candidates/` tidak di-commit):

| Berkas | SHA-256 |
| --- | --- |
| `data/candidates/pedoman_v2/lembar_persetujuan_pedoman_A6_terisi.xlsx` | `46714dabc05fa1bba711d9b083402b8d8f9b8888487cbf701520681aefa5830e` |
| `data/candidates/pedoman_v2/lembar_persetujuan_pedoman_A6.xlsx` (templat) | `9b58cef81323627cac7e60cc8f76361cd160e5bff67140a2ca6fba8efd5841b4` |

- **Templat ikut tertimpa.** Templat dibuat kode (`creator` openpyxl, 2026-10-26 07.26 UTC) lalu ikut tersimpan dari
  Excel (`lastModifiedBy` Lenovo Ideapad 5, 2026-10-27 06.39 UTC); isi selnya identik dengan berkas terisi. Templat
  kosongnya tidak ada lagi dan hash-nya tidak pernah di-commit. Keutuhan kolom A-C (aturan dan contoh) karena itu
  diperiksa dengan membandingkannya ke teks A6 revisi 5: 9 dari 10 baris sama persis (aturan 4 sama setelah tanda `*`
  diabaikan); baris "pedoman v1.0" adalah ringkasan yang ditulis saat templat dibuat. Pemilik proyek mengakui templat
  tertimpa; **ke depan, hash templat di-commit sebelum diisi.**
- **Keputusan di lembar:** Setuju untuk aturan 1, 2, 3, 5, 6, 8; Ubah untuk aturan 4, aturan 7, catatan wajib, dan
  cakupan pedoman v1.0. **Jawaban dan tambahan pemilik proyek di luar lembar (2026-10-27):** empat klarifikasi (aturan 7
  merujuk aturan 1-6, 8, dan 9; "kandidat terdekat"; definisi penipuan per pasangan; arti "periode"), aturan 9, dan
  catatan induk-anak lembaga. **Keputusan atas temuan K1-K13 (2026-10-27, revisi 7):** A6.6.
- **Peran Claude Code:** memeriksa lembar (keutuhan berkas, analisis per perubahan) dan melaporkan pertentangan
  rujukan aturan 7, dampak pada P2-21, serta empat hal yang perlu diklarifikasi. Usulan untuk "kandidat terdekat" dan
  "penipuan per pasangan" berasal dari laporan itu dan diterima pemilik proyek. Claude Code juga menemukan K1-K13
  (A6.4) dan menyusun teks pedoman 2.0 serta contoh rekaannya dari keputusan pemilik proyek.

**Pernyataan pemakaian AI, lembar persetujuan** (pemilik proyek, 2026-10-27; dicatat apa adanya, aturan wajib #5):

> Saya memakai asisten AI Claude (Anthropic) lewat aplikasi Claude dalam diskusi saat mengisi lembar ini. Rinciannya:
>
> Aturan 1, 2, 5, 6, dan 8 (Setuju): saya putuskan sendiri dari teks dan contoh di lembar.
> Aturan 3 (Setuju): saya putuskan setelah AI menjelaskan maksud pengecualiannya dengan contoh.
> Aturan 4, aturan 7, catatan wajib, dan cakupan pedoman v1.0 (Ubah): pertentangan aturan 3 dan 4 ditemukan dalam diskusi dengan AI, dan teks di kolom E dan F disusun oleh AI, lalu saya salin hampir kata per kata setelah saya baca dan setujui.
> Aturan 9 dan klarifikasi di bawah juga disusun bersama AI.
>
> Semua keputusan Setuju/Ubah adalah keputusan saya. Label butir set (a) dan (b) akan saya buat sendiri tanpa AI. Saya juga mengakui templat lembar ikut tertimpa. Ke depan, hash templat di-commit sebelum diisi.

**Pernyataan pemakaian AI, keputusan K1-K13** (pemilik proyek, 2026-10-27; dicatat apa adanya):

> K2 dan K3 berasal dari aturan 9 yang disusun dalam diskusi saya dengan AI, dan koreksinya saya terima. Keputusan di bawah juga saya susun bersama asisten AI (Claude) lalu saya setujui.

**Pernyataan pemakaian AI, keputusan 44-52 dan usulan prinsip utama** (pemilik proyek, 2026-10-27; dicatat apa adanya):

> Keputusan dan usulan di bawah saya susun bersama asisten AI (Claude) lalu saya setujui.

Akibatnya bagi tafsir: teks aturan 4, 5 (pengecualian saluran resmi), 7, dan 9, catatan wajib, definisi kapan A6 dipakai,
dan definisi unsur adalah rumusan yang disusun bersama AI lalu disetujui manusia, bukan rumusan manusia sendiri. Ini tidak
membatalkannya (label butir tetap dibuat manusia tanpa AI), tetapi dicatat sebagai keterbatasan pedoman 2.0. Selain itu,
dua AI terlibat (Claude di aplikasi, dalam diskusi pemilik proyek; Claude Code, yang memeriksa dan menulis teks), jadi
pemeriksaan konsistensi oleh Claude Code bukan pemeriksaan yang independen terhadap rumusan itu.

### A6.4 Pemeriksaan konsistensi pertama (2026-10-27, revisi 6; keputusannya di A6.6)

Diperiksa: aturan 1-9, catatan wajib, definisi penipuan, definisi periode, dan pedoman v1.0. Kode temuan sama dengan
pedoman 2.0 bagian 9. Tabel ini adalah keadaan revisi 6 dan tidak diubah.

| Kode | Jenis | Temuan | Pilihan (usulan revisi 6) |
| --- | --- | --- | --- |
| **K1** | **pertentangan, berat** | Pengumuman resmi set (a) yang mengajak mendaftar lewat tautan resmi memenuhi definisi penipuan (b), jadi pasangannya dengan artikel PENIPUAN berlembaga dan bertawaran sama dinilai dengan A6. Aturan 5 lalu menyatakan **klaim sama** (tautan berbeda tidak menolak). Itu bertentangan dengan A4.a, yang menetapkan label set (a) "belum ditemukan", dan dengan metrik salah menuduh. A6 mengandaikan kedua sisi adalah penipuan; tidak ada aturan untuk saluran resmi lawan saluran penipuan. | (i) saluran resmi lawan saluran sumber hoaks = bertentangan; (ii) kriteria (b) hanya untuk pesan yang bukan pengumuman dari sumber resmi; (iii) set (a) dinilai dengan pedoman v1.0 saja |
| **K2** | ambiguitas | Aturan 9: "Selain itu: bukan klaim sama, dan butir ditandai ragu." Bila dibaca harfiah, setiap pasangan yang ditolak karena pertentangan jelas juga ditandai ragu. | ragu hanya untuk cabang "tawaran tidak dapat dibandingkan dan syarat tambahan tidak terpenuhi" |
| **K3** | pertentangan | Saluran yang disebut di kedua sisi dan berbeda berstatus "bertentangan", sehingga kalimat pertama aturan 9 menolak pasangan yang menurut aturan 5 klaim sama. | saluran berbeda tidak dihitung pertentangan |
| **K4** | tumpang tindih dengan v1.0 | Belum ada urutan prioritas untuk pasangan penipuan bila A6 dan v1.0 berbeda: (a) "lebih umum"; (b) keluarga artikel; (c) KIA lawan Narasi. | satu kalimat prioritas, ditambah penyelesaian ketiga titik |
| **K5** | ambiguitas | Nominal dan periode tidak tercantum sebagai unsur inti. | sebut unsur secara lengkap |
| **K6** | tidak tercakup | Periode berbeda jenis (tahun lawan nama gelombang). | jenis berbeda = tidak dapat dibandingkan |
| **K7** | tidak tercakup | "Nominal" tidak didefinisikan. | jumlah uang atau nilai bantuan |
| **K8** | tidak tercakup | Lembaga umum ("pemerintah") lawan lembaga tertentu. | tidak dapat dibandingkan |
| **K9** | tidak tercakup | Tokoh lawan lembaga yang dipimpinnya. | ragu dan dicatat |
| **K10** | prosedur | Kriteria (a) butuh label TurnBackHoax tiap kandidat tampil di lembar pelabelan. | tampilkan label |
| **K11** | tidak tercakup | Hubungan `kekhususan` dan `batas` v1.0 dengan tanda ragu. | ragu menggantikan `batas` |
| **K12** | rumusan | "Tahun atau tanggal berbeda" di aturan 3 mudah salah baca. | rumuskan ulang |
| **K13** | prosedur | Pemakaian butir ragu dalam metrik belum ditetapkan. | tetapkan sebelum pelabelan |

### A6.5 Rencana penguncian pedoman 2.0 (usulan; menunggu persetujuan pemilik proyek)

Mengikuti cara pedoman v1.0 (`testset/ANNOTATION_GUIDE.md`, `testset/GUIDE_LOCK.json`, tag `annotation-guide-v1.0`):

1. **Sebelum commit kunci (keputusan 52; revisi 8).** Urutannya:
   - **Keputusan dan revisi.** Pemilik proyek memutuskan prinsip utama (A6.10) dan sisa temuan (A6.8, A6.9); pedoman
     2.0 dan A6 direvisi, termasuk keputusan 44-51; pemilik proyek memeriksa teksnya.
   - **Daftar acuan saluran resmi bertanggal** (keputusan 49) disusun dan ditampilkan di lembar pelabelan.
   - **Uji coba pedoman (EKSPLORATIF).** Pemilik proyek melabeli 10 butir dari set evaluasi eksternal lama (sudah sekali
     pakai) dengan pedoman draf **yang sudah direvisi menurut A6.10** (commit pedoman ditulis di lembar), mencatat waktu
     per butir dan bagian yang membuat ragu.
     - Lembar: `data/candidates/uji_coba_pedoman_v2/uji_coba_pedoman_v2.xlsx` (lokal, memuat kutipan Liputan6; tidak
       di-commit), dibuat `python -m labeling.sessions.guide_trial --make` pada 2026-10-27, **sebelum diisi**.
     - Pemilihan: benih `20261027`, acak terstratifikasi menurut label final (positif/negatif) dan ada atau tidaknya
       kandidat berlabel PENIPUAN: positif-penipuan 3, negatif-penipuan 3, positif-non 2, negatif-non 2 (dari 35, 36, 11,
       dan 9 butir yang tersedia; 8 butir yang dikeluarkan tidak ikut). 10 butir, 68 baris kandidat. Label final hanya
       dipakai untuk strata dan tidak ditulis ke lembar.
     - Kandidat = kandidat yang dulu tampil (P1: `konfirmasi_50.csv`; P2: peta blok templat 49), teks dari
       `articles.json` saat ini. Untuk P1, judul, label, tanggal, dan Kesimpulan dicocokkan dengan `konfirmasi_50.csv`: 0
       selisih. Kolom asal ("indeks"/"antrean") tidak ditampilkan, karena antrean sudah di-ingest 2026-10-25. Narasi dan
       Referensi ikut ditampilkan; label TurnBackHoax tiap kandidat tampil (keputusan 41).
     - Tidak ditampilkan: label lama atau final, keputusan dan catatan lama, keluaran sistem, skor. Urutan butir dan
       kandidat diacak dengan `random.SystemRandom`; peta ke kode butir hanya di kunci.
     - **Hash (dicatat sebelum diisi):**

       | Berkas | SHA-256 |
       | --- | --- |
       | `uji_coba_pedoman_v2.xlsx` (templat) | `fd1f9d92132a078f45aed1deb6b29c70137c828b2975c1b7aa514500a1b384f5` |
       | `kunci_uji_coba.json` | `d9304a575da6ba6a8375dc5b3b9eed21fcb5df2580cb5f10358294cf5bf60d03` |
       | `sidik_jari_templat_uji_coba.json` | `a710b6365ef82dfac89b9ba7b69d98032e6b74637d7abe551f5adb7f553086c9` |
       | sidik jari bukti (semua sel selain sel masukan) | `7cc0f82e923b914ceefe88ba7e944d8d4b8e54c38b40be3d9d8c8f42f568cddf` |

       Hasil disimpan sebagai `uji_coba_pedoman_v2_terisi.xlsx`; templat tidak ditimpa.
     - **Keterbatasan:** semua butir sudah pernah dilabeli dan sebagian diadjudikasi oleh pemilik proyek, jadi uji coba
       mengukur kejelasan pedoman dan waktu, bukan kesepakatan; waktu per butir kemungkinan lebih singkat daripada pada
       butir baru. Kandidat lama dicari dari judul Liputan6, berbeda dari cara kandidat set (a) dan (b) nanti. Daftar
       acuan saluran resmi belum ada pada lembar ini (petunjuk lembar: pakai Kesimpulan dan Referensi saja, dan catat bila
       tidak cukup).
     - Alat pembaca belum dibuat; dibuat bila diminta. Membandingkan hasil uji coba dengan label lama **tidak**
       direncanakan; bila diinginkan, diputuskan sebelum lembar dibaca. Revisi pedoman sesudah uji coba dicatat sebagai
       revisi sebelum kunci, beserta bagian pedoman yang memicunya. Perkiraan jam set (a) tetap diukur ulang pada 10 butir
       pertama set (a) (keputusan 31); waktu uji coba hanya indikasi awal.
   - **Pemeriksaan independen.** Setelah revisi sesudah uji coba, pedoman 2.0 diperiksa oleh sesi agent baru yang hanya
     membaca `testset/ANNOTATION_GUIDE_v2.md`, tanpa rancangan dan tanpa riwayat diskusi. Cara menjalankan (pemilik
     proyek):
     1. Buat folder kosong **di luar repositori** (misalnya `C:\pemeriksaan_pedoman_v2\`) dan salin hanya
        `testset/ANNOTATION_GUIDE_v2.md` ke sana. Alasannya: Claude Code otomatis memuat `CLAUDE.md` dan memori proyek
        bila dijalankan dari folder repositori; di folder baru keduanya tidak ada.
     2. Jalankan `claude` di folder itu sebagai sesi baru, lalu tempelkan instruksi di bawah.
     3. Simpan laporannya dan serahkan ke sesi kerja proyek untuk dicatat di sini. Setiap temuan diputuskan pemilik proyek.

     Batasan: pemeriksanya model yang sama (Claude), jadi ia independen terhadap riwayat diskusi, bukan terhadap model.
     Pemeriksaan tambahan oleh model lain atau oleh manusia yang belum mengenal proyek akan lebih independen.

     Instruksi untuk sesi itu:

     ```text
     Anda memeriksa satu dokumen: ANNOTATION_GUIDE_v2.md di folder ini. Jangan membuka berkas lain, jangan mencari
     di web, dan jangan memakai pengetahuan tentang proyek atau dokumen lain. Anggap pedoman ini satu-satunya acuan
     bagi dua pelabel manusia yang bekerja terpisah.

     Tugas:
     1. Cari pertentangan antar-aturan, istilah yang dipakai tanpa definisi, keadaan yang tidak tercakup, dan kalimat
        yang bisa ditafsirkan dua cara oleh dua pelabel yang sama-sama teliti.
     2. Periksa apakah urutan langkah (bagian 5) selalu menghasilkan keputusan yang sama dengan aturan (bagian 4).
     3. Periksa apakah setiap contoh rekaan benar menurut aturan yang dirujuknya.
     4. Sebutkan bagian yang paling mungkin membuat dua pelabel tidak sepakat, dan mengapa.

     Aturan pelaporan:
     - Setiap temuan: kode; jenis (pertentangan | tidak didefinisikan | tidak tercakup | tafsir ganda | contoh keliru |
       urutan langkah); kutipan kalimat pedoman yang bersangkutan; masalahnya; satu contoh rekaan yang
       memperlihatkannya (lembaga, tautan, dan nominal karangan; jangan memakai lembaga, orang, atau kasus nyata);
       dampak (tinggi | sedang | rendah); tingkat keyakinan Anda.
     - Jangan menulis ulang pedoman dan jangan mengusulkan perubahan cakupan. Usulan perbaikan paling banyak satu
       kalimat per temuan.
     - Laporkan juga bagian yang menurut Anda jelas dan konsisten, supaya terlihat apa yang sudah diperiksa.
     ```
2. **Commit kunci** (Claude Code, di branch, lalu digabung ke `main` atas persetujuan pemilik proyek): status pedoman
   menjadi "DIKUNCI" dengan tanggal; `testset/GUIDE_LOCK_v2.json` berisi `sha256_ternormalisasi` (akhir baris
   dinormalkan ke LF, seperti v1.0), versi `2.0`, dan tanggal; uji baru di `tests/core/test_testset_locks.py` yang gagal
   bila pedoman 2.0 berubah, dengan kontrol mutasi (satu karakter diubah -> uji gagal).
3. **Tag dan bukti waktu luar** (pemilik proyek): tag beranotasi `annotation-guide-v2.0` pada commit kunci di `main`;
   `git push origin main` lalu `git push origin annotation-guide-v2.0`; GitHub Release, misalnya
   `gh release create annotation-guide-v2.0 --title "Pedoman anotasi 2.0" --notes "Pedoman klaim sama 2.0, dikunci sebelum pelabelan set (a) dan (b) Versi 2."`;
   Internet Archive untuk halaman commit, tag, dan Release (A3.4). Alamat snapshot dicatat di commit berikutnya.
4. **Baru setelah itu** pelabelan apa pun dimulai: latihan anotator kedua, set (a), dan nanti set (b).
5. **Hubungan dengan Kunci 1:** pedoman tidak lagi dikunci di Kunci 1 (A3.2 diubah di revisi 6), tetapi lebih dulu,
   supaya definisi terkunci sebelum butir set (a) mana pun dilihat untuk dilabeli. Kunci 1 tidak mengunci ulang pedoman;
   ia mencatat tag dan hash pedoman 2.0 di `testset/v2.meta.json`, dan uji kunci memastikan pedoman tidak berubah antara
   tag pedoman, Kunci 1, dan Kunci 2.
6. **Setelah dikunci,** pedoman hanya berubah lewat versi baru (2.1 dan seterusnya, tag baru), misalnya bila
   kesepakatan anotator jatuh ke "pedoman direvisi" (A7). Butir yang sudah dilabeli tetap tercatat dengan versi
   pedomannya; versi pedoman dicatat per butir. Kasus tak tercakup selama pelabelan ditangani seperti v1.0: ditandai
   ragu, dicatat sebagai kasus terbuka, diputuskan dengan aturan terdekat, tanpa merevisi pedoman di tengah jalan.

### A6.6 Keputusan atas K1-K13 (pemilik proyek, 2026-10-27; disusun bersama AI, A6.3)

| Temuan | Keputusan | Nomor keputusan | Diterapkan di revisi 7 |
| --- | --- | --- | --- |
| K1 | Aturan 5 ditambah pengecualian saluran resmi; istilah "butir penipuan" diganti "pola pendaftaran atau tawaran"; cara verifikasi saluran resmi ditulis; perbandingan dengan alternatif diminta (A6.7) | 32 | ya |
| K2 | Ragu di aturan 9 hanya untuk keadaan kedua (tawaran tidak dapat dibandingkan, bukti tambahan kurang) | 33 | ya |
| K3 | Saluran berbeda netral, sama persis = bukti pendukung, resmi lawan tidak resmi = pertentangan; aturan 9 disesuaikan | 34 | ya |
| K4 | Untuk pasangan A6, A6 didahulukan bila bertentangan dengan v1.0; penyelesaian tiga titik diusulkan untuk disetujui | 35 | prinsip ya; tiga titik usulan (A6.8) |
| K5 | Nominal dan periode masuk daftar unsur inti | 36 | ya |
| K6 | Periode hanya dibandingkan dengan jenis yang sama; jenis berbeda = tidak dapat dibandingkan, kecuali satu sisi memuat keduanya | 37 | ya |
| K7 | Nominal = jumlah uang yang ditawarkan atau diminta; armada, kuota peserta, dan sejenisnya bukan nominal | 38 | ya |
| K8 | Lembaga umum lawan lembaga tertentu = tidak dapat dibandingkan | 39 | ya |
| K9 | Tokoh lawan lembaga yang dipimpinnya = tidak dapat dibandingkan, ragu; keputusan dari unsur lain lewat aturan 9; dikumpulkan untuk versi berikutnya | 40 | ya |
| K10 | Label TurnBackHoax tiap kandidat ditampilkan di lembar pelabelan | 41 | ya (A6, A7) |
| K11 | Hubungan `kekhususan`, `batas`, dan ragu diusulkan untuk disetujui | -- | usulan (A6.8) |
| K12 | Aturan 3 dirumuskan ulang: gelombang yang hanya terlihat dari tanggal terbit = sama; tahun atau periode tertulis di kedua teks dan berbeda = bukan sama | 42 | ya |
| K13 | Metrik utama memakai label akhir, ditambah sensitivitas tanpa butir ragu; ditulis di A4 sebagai bagian yang dikunci | 43 | ya (A4.d) |

**Satu kalimat yang ditambahkan Claude Code saat menerapkan K12 (perlu diperiksa pemilik proyek):** "Tahun atau periode
yang hanya tertulis di satu sisi: tidak dapat dibandingkan." Kalimat ini tidak ada di keputusan K12, tetapi mengikuti
definisi status unsur dan pengecualian aturan 3 sebelumnya ("kecuali disebut eksplisit di kedua sisi"); tanpanya,
keadaan itu tidak tercakup rumusan baru.

### A6.7 K1: pengecualian saluran resmi lawan alternatif "set (a) tanpa A6"

Pemilik proyek meminta kedua pilihan dibandingkan sebelum diterapkan. **Penilaian Claude Code: alternatif tidak lebih
baik secara keseluruhan, jadi pengecualian saluran resmi diterapkan.** Satu celah tetap ada pada keduanya (temuan N1, A6.9).

| Sisi | Pengecualian saluran resmi (diterapkan) | Set (a) tanpa A6, label dari cara set disusun |
| --- | --- | --- |
| Beban pelabel, set (a) | Rendah: saluran di pengumuman resmi terverifikasi lewat asal butir (cara verifikasi butir 4); yang diperiksa hanya sisi artikel | Paling rendah: tidak ada pelabelan klaim sama; hanya pemeriksaan pengecualian A4.a ("tidak pernah dinyatakan salah oleh TurnBackHoax") |
| Beban pelabel, set (b) | Bertambah: setiap saluran perlu dicocokkan dengan sumber acuan, dan sumber acuan dicatat | Tidak berubah, tetapi set (b) tetap tanpa aturan saluran resmi |
| Risiko ketidaksepakatan | Ada: domain tiruan yang terlihat resmi, akun media sosial, nomor WhatsApp, dan pemendek URL; dua pelabel bisa memakai sumber acuan berbeda. Dikurangi dengan aturan "host persis atau subdomain sejati" dan larangan menebak | Nol di set (a), karena tidak ada pelabelan; tetapi pemeriksaan pengecualian A4.a tetap butuh aturan, dan tanpa A6 aturannya v1.0 yang tidak mengenal saluran |
| Pesan set (b) yang meneruskan pengumuman resmi | **Tertangani** bila pengumumannya menyebut saluran resmi | **Tidak tertangani:** aturan 5 akan menilainya klaim sama dengan artikel penipuan berlembaga dan bertawaran sama |
| Pengukuran kesepakatan set (a) (A7, keputusan 11) | Tetap bisa dijalankan seperti rencana | Kehilangan isi: 40 butir set (a) untuk anotator kedua tidak punya label klaim sama untuk dibandingkan; A7 harus dirancang ulang |
| Pengumuman resmi tanpa saluran | **Tidak tertangani** (N1) | Tertangani di set (a) karena label ditetapkan dari cara set disusun; tidak tertangani di set (b) |

Alasan utama: pengecualian dibutuhkan untuk set (b) apa pun pilihannya, dan alternatif mengorbankan rencana kesepakatan
set (a) yang sudah disetujui. Celah N1 lebih tepat ditutup dengan uji Kesimpulan (usulan K4 titik c, A6.8) daripada
dengan membebaskan set (a) dari A6.

### A6.8 Usulan untuk K4 (tiga titik) dan K11 (menunggu persetujuan pemilik proyek)

**K4, dengan prinsip "A6 didahulukan untuk pasangan A6":**

| Titik | v1.0 | Usulan untuk pasangan A6 | Alasan |
| --- | --- | --- | --- |
| (a) Klaim lebih umum | "lebih umum -> TIDAK SAMA" (`kekhususan=umum`) | Aturan 8 dan 9 menggantikan baris itu: istilah umum -> tawaran tidak dapat dibandingkan -> aturan 9 | Pada pola pendaftaran, istilah umum ("bantuan") sering hanya gaya bahasa, sementara lembaga dan saluran bisa sama persis dengan sumber hoaks. Aturan 9 tetap konservatif: butuh lembaga atau tokoh sama dan satu unsur lain sama, selain itu bukan klaim sama dan ragu. Konsekuensi: sedikit lebih banyak positif dibanding v1.0, hanya bila ada bukti tambahan |
| (b) Keluarga artikel | "cocok dengan lebih dari satu artikel tanpa unsur pembeda -> TIDAK SAMA, `ambigu`" | Aturan 7 menggantikan baris itu: semua artikel sah dicatat, jawaban benar bila memilih salah satunya | Baris v1.0 dibuat karena set uji v1 hanya punya satu artikel target; A4.d Versi 2 menerima artikel sah mana pun, dan setiap artikel wajib lolos aturan sendiri-sendiri. Risiko: keluarga besar memudahkan jawaban "benar". Mitigasi yang diusulkan: jumlah artikel sah dicatat per butir, dan akurasi butir dengan lebih dari satu artikel sah dilaporkan terpisah (deskriptif) |
| (c) Jangkar KIA lawan Narasi | KIA (judul) adalah jangkar; uji dua arah dan uji Kesimpulan | Unsur dibandingkan dengan Narasi (aturan 6); KIA hanya untuk mengenali topik. Uji dua arah digantikan perbandingan unsur. **Uji Kesimpulan dipertahankan sebagai uji penolak:** bila Kesimpulan artikel membenarkan isi pesan (misalnya menyatakan programnya memang ada, atau saluran di pesan memang resmi), pasangan bukan klaim sama | Judul artikel pola pendaftaran ("Tautan Pendaftaran X") jarang memuat lembaga, nominal, atau saluran; Narasi yang memuatnya. Uji Kesimpulan sebagai penolak menutup N1 (pengumuman resmi tanpa saluran) dan pesan set (b) yang meneruskan pengumuman resmi, tanpa beban verifikasi tambahan, karena Kesimpulan artikel penipuan umumnya menyebut bahwa program atau saluran resminya berbeda dari yang beredar |

**K11:**

1. **Ragu menggantikan `batas` di seluruh set Versi 2** (pasangan A6 maupun v1.0). Alasan: keduanya berarti "tidak pasti
   menurut pedoman", tetapi set uji v1 mengeluarkan `batas` dari hitungan utama, sedangkan keputusan 43 memasukkan butir
   ragu ke metrik utama dan mengeluarkannya hanya di sensitivitas. Dua tanda dengan perlakuan berbeda akan membingungkan
   pelabel dan metrik.
2. **`kekhususan` diisi hanya untuk butir yang semua pasangannya dinilai dengan v1.0**, tanpa nilai `batas`. Untuk butir
   dengan pasangan A6, kolom itu diisi `a6`. Alasan: catatan wajib sudah merekam unsur secara lebih rinci, dan nilai
   seperti `umum` atau `spesifik_inti` akan bertabrakan dengan status unsur A6 (titik a). Hasil per `kekhususan`
   dilaporkan hanya untuk butir non-A6, sebagai deskripsi.
3. **`ambigu` v1.0 tidak dipakai untuk pasangan A6** (aturan 7 menggantikannya, titik b).

### A6.9 Pemeriksaan konsistensi kedua (2026-10-27, revisi 7; TEMUAN, BELUM DIPERBAIKI)

Diperiksa ulang: definisi unsur, aturan 1-9 setelah revisi 7, catatan wajib, kapan A6 dipakai, dan hubungannya dengan
v1.0, A4, dan A7, terutama dampak K1 terhadap aturan 5, 7, dan 9. Kode N agar tidak tertukar dengan K.

| Kode | Jenis | Temuan | Pilihan (usulan) |
| --- | --- | --- | --- |
| **N1** | **pertentangan, berat** | **K1 baru tertutup sebagian.** Pengecualian saluran resmi hanya bekerja bila kedua sisi menyebut saluran. Pengumuman resmi yang tidak menyebut tautan atau nomor ("Pendaftaran Program X Tahun 2027 dibuka mulai 1 Maret") lawan artikel PENIPUAN "Tautan Pendaftaran Program X" dengan lembaga dan tawaran sama: saluran tidak dapat dibandingkan, tidak ada pertentangan, sehingga aturan 9 kalimat pertama menyatakan **klaim sama**. Itu bertentangan dengan label set (a) (A4.a). Hal yang sama terjadi pada pesan set (b) yang meneruskan pengumuman resmi tanpa saluran. | uji Kesimpulan sebagai uji penolak (usulan K4 titik c); atau label set (a) dari cara set disusun (A6.7) |
| **N2** | **pertentangan, sedang** | **Sisi yang memakai saluran resmi bisa tetap hoaks.** Pesan penipuan kadang menyebut situs resmi sambil meminta transfer ke rekening atau nomor lain. Bila Narasi artikel memakai saluran resmi itu dan pesan yang dicek memakai tautan tiruan untuk penipuan yang sama, pengecualian menyatakan bukan klaim sama. Lagi pula satu sisi bisa memuat saluran resmi dan tidak resmi sekaligus, dan keadaan itu belum diatur. | pengecualian hanya berlaku bila saluran resmi adalah satu-satunya saluran di sisi itu; sisi campuran -> saluran tidak dapat dibandingkan, ragu |
| **N3** | ambiguitas, sedang | **Ragu bisa membengkak.** Menurut cara verifikasi butir 5, setiap saluran yang status resminya tidak dapat dipastikan membuat pasangan ragu. Pemendek URL dan nomor WhatsApp sangat umum di pesan penipuan, dan lembaga resmi pun kadang memakai pemendek. Bila dibaca harfiah, banyak pasangan set (b) yang kedua sisinya jelas penipuan menjadi ragu, sehingga analisis sensitivitas tanpa butir ragu (keputusan 43) kehilangan banyak butir. | verifikasi hanya menentukan bila sisi lain saluran resmi yang terverifikasi; bila tidak ada sisi yang terverifikasi resmi, aturan 5 kalimat pertama berlaku tanpa ragu |
| **N4** | tumpang tindih, sedang | **Tindakan dan syarat tidak termasuk unsur A6.** Dengan A6 didahulukan (keputusan 35), tidak jelas apakah unsur v1.0 "tindakan" dan "kondisi pembeda" masih dipakai pada pasangan A6, karena ketiadaan aturan bukan pertentangan. Contoh: pesan resmi lawan hoaks yang menyebut saluran resmi yang sama tetapi menambah syarat palsu ("tanpa tes"); semua unsur A6 sama, sehingga A6 menyatakan klaim sama. Ini juga jenis kesalahan sistem P2-33. | unsur v1.0 yang tidak diatur A6 (tindakan, kondisi pembeda) tetap dibandingkan; perbedaannya = pertentangan |
| **N5** | tidak tercakup, ringan | **Nominal dengan peran berbeda.** Keputusan 38 mencakup uang yang ditawarkan dan yang diminta. Pesan menawarkan Rp2 juta, artikel menyebut biaya pendaftaran Rp100 ribu: keduanya nominal, tetapi tidak jelas apakah dibandingkan. | nominal hanya dibandingkan dengan peran yang sama (ditawarkan dengan ditawarkan, diminta dengan diminta) |
| **N6** | prosedur, ringan | **Verifikasi bergantung pada waktu dan akses.** Domain resmi bisa berubah antara tanggal pesan dan tanggal pelabelan, dan anotator kedua butuh akses internet untuk sumber acuan (a). A7 belum menyebut keduanya. | tanggal pemeriksaan dicatat (sudah di catatan wajib); A7 menyebut bahwa anotator kedua boleh membuka situs resmi lembaga dengan cara verifikasi yang sama |
| **N7** | prosedur, ringan | **"Butir ragu" untuk sensitivitas belum didefinisikan pemiliknya**: tanda ragu dari pemilik proyek pada label akhir, dari salah satu anotator, atau dari keduanya. | butir ragu = ditandai ragu pada label akhir pemilik proyek; tanda ragu anotator kedua dilaporkan terpisah |
| N8 | rumusan, ringan | Di aturan 9, "saluran sama" pada keadaan kedua ditulis "saluran sama persis", sedangkan kalimat pertama aturan 5 menyebut "sama persis dengan sumber hoaks di artikel". Untuk set (a), "sama persis" bisa berarti kedua sisi memakai saluran resmi yang sama (lihat N4). | nyatakan bahwa saluran resmi yang sama di kedua sisi bukan bukti pendukung pola penipuan |

Yang **diperiksa dan tidak bertentangan:** aturan 7 dengan pengecualian saluran resmi (pesan resmi -> setiap artikel
penipuan bertentangan pada saluran -> tidak ada artikel sah -> negatif, sesuai A4.a); aturan 9 setelah K2 dan K3
(penolakan karena pertentangan tidak lagi ragu, saluran berbeda tidak lagi menolak); aturan 3 dan 4 setelah K12; K8 dan
K9 dengan aturan 9 (bila tawaran sama, lembaga yang tidak dapat dibandingkan tidak menghalangi klaim sama; bila tawaran
juga tidak dapat dibandingkan, hasilnya bukan klaim sama dan ragu); K13 dengan A7 (label akhir = label pemilik proyek
setelah adjudikasi).

### A6.10 Penilaian prinsip utama "Kesimpulan membantah pesan" (usulan pemilik proyek, disusun bersama AI; dinilai Claude Code 2026-10-27; BELUM diputuskan)

**Usulan.** Untuk pasangan pola pendaftaran atau tawaran, pesan dan artikel adalah klaim sama hanya bila pesan memuat
unsur yang dinyatakan salah atau palsu oleh Kesimpulan artikel (tautan atau nomor tidak resmi, program yang dinyatakan
tidak ada, permintaan biaya atau transfer, syarat palsu). Lembaga, tawaran, nominal, dan periode dipakai untuk
memastikan pesan dan artikel membicarakan program yang sama. Ini menjadikan K4 (c) syarat utama, bukan penolak tambahan.
Alasan pemilik proyek: setiap putaran tambalan memunculkan celah baru dan pedoman makin rumit.

**Dua pengukuran sebelum menilai** (heuristik pola kata, EKSPLORATIF, luring, tidak diperiksa manusia; dibuat setelah
usulan diterima dan sebelum keputusan; hanya hitungan yang dicatat, tanpa kutipan teks):

| Yang diukur | Hasil |
| --- | --- |
| Kesimpulan 479 artikel PENIPUAN (indeks 1.611): jenis bantahan yang tersurat | saluran tidak resmi 269 (56%); program tidak ada atau belum dibuka 16 (3%); biaya, transfer, atau data pribadi 35 (7%); **hanya rekayasa media atau tanpa bukti 98 (20%); tidak ada penanda sama sekali 80 (17%)** |
| Kutipan pesan 99 artikel Liputan6 sampel evaluasi eksternal | **memuat URL 12**; menyebut tautan, link, klik, atau daftar tanpa URL 22; memuat nomor telepon 0 |

Pola kata bisa meleset ke dua arah; angka ini hanya menunjukkan besarnya, bukan nilai pasti. Bacaannya: sekitar
sepertiga Kesimpulan tidak menunjuk unsur tertentu yang dibantah, dan sebagian besar kutipan Liputan6 tidak memuat
tautannya.

**Penilaian.** Arah prinsip ini benar, dan ia mengembalikan pedoman 2.0 ke jangkar pedoman v1.0 (uji Kesimpulan). Tetapi
dalam **bentuk ketat** ("pesan memuat unsur spesifik yang dibantah") ia lebih buruk daripada pendekatan sekarang pada dua
hal yang terukur:

1. **Kesimpulan generik (sekitar 37%)**: unsur yang dibantah tidak bisa ditunjuk, jadi pelabel harus menebak, dan itu
   sumber ketidaksepakatan baru.
2. **Kutipan tanpa tautan (87 dari 99 tanpa URL)**: bila Kesimpulan membantah tautannya, pesan yang tautannya tidak
   dikutip tidak memuat unsur itu, sehingga dinilai bukan klaim sama walau penipuannya sama. Set (b) akan kehilangan
   positif yang sah karena cara Liputan6 mengutip, bukan karena isi pesannya.

**Usulan bentuk yang dimodifikasi: dua pertanyaan.**

- **Pertanyaan 1, program sama?** Aturan 1, 2, 3, 4 (dengan keputusan 48), 6, 8, dan 9 beserta definisi unsur; aturan 7
  untuk lebih dari satu artikel.
- **Pertanyaan 2, Kesimpulan membantah pesan?** Pasangan klaim sama bila Kesimpulan artikel, dibaca sebagai jawaban,
  membantah apa yang dinyatakan atau diajak pesan. Dinilai **per jenis bantahan**, bukan per untaian teks:
  - (a) **saluran tidak resmi**: membantah pesan yang memakai **atau merujuk** saluran yang tidak ada di daftar acuan
    (keputusan 49), termasuk "klik tautan berikut" tanpa alamat. Pemendek URL dan nomor WhatsApp yang tidak ada di daftar
    acuan dihitung tidak resmi, tanpa tanda ragu;
  - (b) **program atau tawaran tidak ada atau belum dibuka**: membantah pesan yang menyatakan program itu ada atau dibuka;
  - (c) **biaya, transfer, data pribadi, syarat, atau nominal palsu**: membantah pesan yang memuat unsur itu;
  - (d) **bantahan menyeluruh** (konten rekayasa, tanpa bukti, atau hanya "unggahan berisi klaim ... palsu"): membantah
    pesan yang menyatakan klaim yang dikutip Kesimpulan, jadi keputusan praktis kembali ke pertanyaan 1.

  Pesan yang sesuai dengan fakta di Kesimpulan (memakai saluran yang disebut resmi, atau tidak menyebut cara mendaftar dan
  tidak memuat unsur yang dibantah) bukan klaim sama.

**Dampak pada aturan dan temuan:**

| Aturan atau temuan | Bentuk ketat | Bentuk dimodifikasi |
| --- | --- | --- |
| N1 (pengumuman resmi tanpa saluran) | tertutup | tertutup |
| N2 (situs resmi + transfer) | tertutup bila Kesimpulan membantah transfer; bila hanya membantah tautan, bukan klaim sama | sama |
| N3 (ragu membengkak) | bergeser: "pemendek URL dan WhatsApp bukan resmi" adalah asumsi, karena lembaga resmi juga memakainya | tertutup lewat daftar acuan: tidak ada di daftar = tidak resmi; risiko sisa terbatas pada saluran resmi yang lupa dimasukkan ke daftar |
| N4 (syarat palsu) | tertutup bila syaratnya dibantah Kesimpulan | sama |
| N8 | tertutup | tertutup |
| K1, pengecualian saluran resmi di aturan 5 | tidak diperlukan | tidak diperlukan |
| Bagian 2.1 pedoman (verifikasi lima langkah) | masih perlu untuk menilai resmi atau tidak | diganti pencarian di daftar acuan |
| Aturan 5 kalimat pertama (penipu berganti tautan) | tetap berlaku hanya bila bantahan dibaca per jenis | tetap berlaku (jenis a) |
| Aturan 1-4, 6-9 | tetap (identitas program) | tetap (pertanyaan 1) |
| K4 (c) | menjadi inti | menjadi inti |
| K2, K5-K13, keputusan 44-50 | tidak terpengaruh | tidak terpengaruh |

**Yang bisa dihapus dengan bentuk dimodifikasi:** pengecualian saluran resmi (aturan 5 kalimat kedua dan ketiga), bagian
2.1 (diganti dua kalimat tentang daftar acuan), tanda ragu karena saluran tidak terverifikasi, dan "sumber acuan + tanggal"
di catatan wajib (diganti "ada atau tidak di daftar acuan"). Yang ditambahkan: satu pertanyaan dengan empat jenis bantahan,
dan "jenis bantahan" di catatan wajib.

**Celah baru yang muncul (kedua bentuk, kecuali disebut lain):**

| Kode | Celah |
| --- | --- |
| G1 | Bantahan yang bergantung waktu: Kesimpulan "program belum dibuka" bisa kedaluwarsa bila program itu kemudian benar-benar dibuka. Pengumuman resmi set (a) yang terbit sesudahnya, tanpa periode tertulis, akan dinilai dibantah (jenis b). Frekuensinya kecil (sekitar 3% Kesimpulan menurut heuristik), tetapi tepat mengenai set (a). Perlu keputusan, misalnya: jenis (b) tidak berlaku bila pesan terbit setelah tanggal artikel dan berasal dari saluran di daftar acuan |
| G2 | Bantahan beda jenis: artikel membantah tautannya, pesan memuat permintaan transfer tanpa tautan. Kedua bentuk menyatakan bukan klaim sama. Ini konservatif dan sejalan dengan fokus salah menuduh, tetapi mengurangi positif set (b) |
| G3 | Menilai "apakah Kesimpulan membantah pesan" adalah penilaian baru, dan dua pelabel bisa berbeda, terutama pada jenis (d). Diukur di uji coba |
| G4 | Daftar acuan menjadi titik gagal tunggal: harus disusun sebelum pelabelan, bertanggal, dan dibekukan bersama pedoman. Saluran resmi yang tidak ada di daftar membuat pengumuman resmi tampak tidak resmi. Untuk set (a), saluran di pengumuman resmi dimasukkan ke daftar saat butir dikumpulkan |
| G5 | Hanya bentuk ketat: pesan yang menyatakan program ada tanpa saluran, lawan artikel yang membantah tautan, dinilai bukan klaim sama, padahal mungkin pesan berantai yang sama dengan tautan terpotong |

**Lebih sederhana atau lebih rumit?** Bentuk ketat lebih pendek di kertas, tetapi memindahkan kerumitan ke penilaian yang
sulit (menunjuk unsur yang dibantah pada sekitar sepertiga Kesimpulan) dan mengubah definisi menurut cara sumber
mengutip. Bentuk dimodifikasi tidak mengurangi jumlah aturan identitas program, tetapi menghapus pengecualian dan
prosedur verifikasi yang terbukti memunculkan celah (K1, N1-N4, N8), dan menggantinya dengan satu pertanyaan yang sudah
dikenal dari pedoman v1.0 ditambah satu daftar. Menurut saya itu lebih sederhana dipakai. Itu belum terbukti; uji coba
yang akan menunjukkannya.

**Rekomendasi:** bentuk dimodifikasi, dengan G1 diputuskan lebih dulu, lalu uji coba dijalankan dengan pedoman yang sudah
direvisi menurut bentuk itu.


## A7. Protokol anotator kedua

- **Jumlah dan pembagian (disesuaikan dengan kunci dua tahap):** 80 butir. **40 dari set (a)** dilabeli sebelum
  Kunci 1, dan **40 dari set (b)** (20 positif dan 20 negatif menurut label pemilik proyek) dilabeli sebelum
  Kunci 2. Pemilihan acak berbenih dan terstratifikasi. Anotator kedua tidak tahu proporsinya.
- **Yang dilihat anotator kedua:** pedoman A6 dan pedoman v1.0, pesan, dan daftar kandidat artikel yang sama dengan
  yang dilihat pemilik proyek, dalam urutan acak, **beserta label TurnBackHoax setiap kandidat** (keputusan 41;
  metadata artikel, bukan keluaran sistem). **Tidak** melihat label pemilik proyek, keluaran sistem, skor
  retrieval, maupun catatan adjudikasi.
- **Latihan:** 5 butir latihan dari set lama yang sudah sekali pakai, tidak dihitung.
- **Berkas:** dibuat kode dengan sel terkunci, seperti sesi buta sebelumnya; hash templat di-commit sebelum diisi.
  Pemakaian AI oleh anotator kedua dicatat (aturan wajib #5).
- **Kappa:** kappa Cohen biner (sama / tidak sama) dan kappa per artikel, dengan interval bootstrap 10.000
  ulangan, dihitung terpisah untuk set (a) dan set (b).
- **Revisi pedoman setelah dikunci (revisi 6):** setiap "pedoman direvisi" di bagian ini berarti versi baru (2.1 dan
  seterusnya) dengan tag baru, bukan mengubah pedoman 2.0; versi pedoman dicatat per butir (A6.5).
- **Ambang (disetujui, keputusan 7):** label dipakai bila kappa biner >= 0,60. Bila 0,40-0,59, pedoman direvisi,
  butir yang tidak sepakat dibahas, lalu 20 butir baru dilabeli ulang oleh keduanya. Bila < 0,40, evaluasi ditunda.
  Dengan 40 butir per set, interval kappa masih lebar, jadi ambang dibaca dari estimasi titik dan intervalnya
  dilaporkan apa adanya.
- **Set (a): ukuran kesepakatan dan ambangnya (keputusan 11; ditetapkan 2026-10-26, sebelum ada data).** Sebagian
  besar butir set (a) kemungkinan dilabeli "tidak sama" oleh keduanya. Bila hampir semua butir jatuh di satu kategori,
  kappa bisa rendah walau kesepakatannya tinggi (paradoks prevalensi). Karena itu untuk set (a) dilaporkan kesepakatan
  mentah, kappa Cohen, **Gwet AC1**, dan **PABAK**, masing-masing dengan interval bootstrap 10.000 ulangan.

  | Hasil | Syarat (set a, 40 butir) |
  | --- | --- |
  | **Label dipakai** | kesepakatan mentah >= 90% **dan** Gwet AC1 >= 0,80 |
  | **Pedoman direvisi**, butir yang tidak sepakat dibahas, 20 butir baru dilabeli ulang oleh keduanya | kesepakatan mentah 80-89% **atau** AC1 0,60-0,79 |
  | **Ditunda** | kesepakatan mentah < 80% **atau** AC1 < 0,60 |

  Kappa dan PABAK dilaporkan tanpa ambang sendiri untuk set (a). PABAK = 2 x kesepakatan mentah - 1, jadi syarat
  kesepakatan 90% setara PABAK 0,80. Bila kappa < 0,60 tetapi syarat di atas terpenuhi, label tetap dipakai dengan
  catatan paradoks prevalensi. Untuk set (b), yang proporsi positif dan negatifnya seimbang, ambang kappa 0,60
  (keputusan 7) tetap berlaku, dan AC1 serta kesepakatan mentah dilaporkan sebagai pendamping.
- **Label akhir:** tetap ditetapkan pemilik proyek. Butir yang tidak sepakat diadjudikasi pemilik proyek tanpa melihat
  keluaran sistem, dan hasilnya dicatat.

## A8. Kuota, jam kerja, dan jumlah butir (perkiraan)

**Butir yang dilabeli pemilik proyek:**

| Bagian | Butir | Perkiraan jam |
| --- | --- | --- |
| Pedoman A6 (menyetujui dan mengunci) | -- | 2-3 |
| Set (a) | 150 | 15-25 (tebakan awal; diukur ulang setelah 10 butir pertama, A12, keputusan 31) |
| Set (b), sampai 50 positif dan 50 negatif | ~100 (paling banyak 200 diproses) | 8-12 |
| Adjudikasi butir yang tidak sepakat dengan anotator kedua | ~15-20 | 1-2 |
| **Jumlah** | **~250** | **~26-42 jam** |

Anotator kedua: 80 butir + 5 latihan, sekitar 5-8 jam, dibagi dua tahap. Angka jam ini perkiraan kasar, bukan
pengukuran.

**Kuota Gemini** (`gemini-3.5-flash-lite`, RPD 500; biasanya 1 permintaan per pemeriksaan):

| Tahap | Panggilan |
| --- | --- |
| Penyusunan pedoman, set, dan pelabelan | 0 |
| Uji kelayakan ekstraksi LLM (A2.6, A2.7) | 184, sudah terpakai |
| Uji pergeseran awal set (a): 54 butir x 3 run | 162 |
| Evaluasi set (a), 150 butir x 3 run | 450 |
| Uji pergeseran akhir set (a): 54 butir x 3 run | 162 |
| Uji pergeseran awal set (b): 54 butir x 3 run | 162 |
| Evaluasi set (b), ~100 butir x 3 run | ~300 |
| Uji pergeseran akhir set (b): 54 butir x 3 run | 162 |
| Tombol salin klarifikasi | 0 |
| **Jumlah yang masih akan dipakai** | **~1.398** |

**Jadwal per hari kuota** (hari Pasifik, berturut-turut; demo dimatikan selama hari evaluasi). Setiap hari dibatasi
**400 panggilan terencana**, sehingga 100 tersisa untuk percobaan ulang (kasus terburuk 8 permintaan per pemeriksaan).
Evaluasi berhenti di batas itu dan dilanjutkan keesokan harinya dari butir berikutnya; butir yang sudah punya jawaban
tidak diulang.

| Set | Hari 1 | Hari 2 | Jumlah |
| --- | --- | --- | --- |
| (a) | uji awal 162 + evaluasi 238 = 400 | sisa evaluasi 212 + uji akhir 162 = 374 | 774 |
| (b), ~100 butir | uji awal 162 + evaluasi 238 = 400 | sisa evaluasi ~62 + uji akhir 162 = ~224 | ~624 |

Uji akhir dijalankan setelah butir terakhir evaluasi selesai. Bila sisa kuota hari 2 tidak cukup (misalnya karena banyak
percobaan ulang), uji akhir dijalankan pada hari kuota berikutnya, tanpa perubahan apa pun pada lingkungan di
antaranya, dan penundaan itu dicatat. **Subset tidak diusulkan:** ulangan penuh muat di dua hari, dan subset (misalnya
satu run saja atau hanya butir bulat) tidak bisa memakai ambang modus 3 run yang sudah disetujui. Kapasitas demo tidak
berubah, karena Versi 2 tidak menambah panggilan per pemeriksaan.

## A9. Prasyarat sebelum layanan publik (tidak dikerjakan di Versi 2)

1. **Izin konten dari Mafindo** untuk menampilkan isi artikel TurnBackHoax kepada publik, idealnya lewat API
   Yudistira.
2. **API berbayar atau model lokal.** Konten tier gratis Gemini dipakai Google untuk meningkatkan produknya, padahal
   pengguna bisa menempel data pribadi. Laptop pengembangan tidak cukup untuk model lokal (B.7.2).
3. **Kebijakan privasi** yang menjelaskan apa yang dikirim ke penyedia LLM dan apa yang dicatat.
4. **Batas pemakaian** per pengguna dan per hari yang sesuai dengan kuota berbayar.
5. **Tahap 3: catatan aktivitas tanpa isi pesan** (ADR 0006).

## A10. Keputusan yang masih terbuka

1. **Sumber set (a):** dipilih pemilik proyek setelah membaca sendiri halaman hak cipta tiap situs (A4.a).

Ambang uji pergeseran sudah disetujui di revisi 5 (keputusan 20).

## A11. Setelah Versi 2: fitur lanjutan dan umpan balik pengguna (tidak masuk ruang lingkup, tidak dikunci)

### A11.1 Daftar fitur

| Fitur | LLM atau kuota | Risiko terhadap keamanan pengguna | Ketergantungan | Boleh sebelum Versi 2 selesai? | Urutan yang disarankan |
| --- | --- | --- | --- | --- | --- |
| 1. Daftar "hoaks terbaru" di beranda dari arsip | Tanpa LLM, tanpa kuota | Rendah. Isinya judul, label, dan tautan artikel TurnBackHoax apa adanya. Perlu menyaring judul yang memuat nomor atau tautan penipu (pemeriksaan PII judul seperti manifest) | Pembaruan berkala dan ingest | **Ya**: tidak menyentuh retrieval, generator, maupun evaluasi | 1 |
| 3. Kartu edukasi per pola penipuan | Tanpa LLM; teks kartu ditulis manusia dan ditinjau | Rendah-sedang. Kartu yang salah kategori bisa menyesatkan, jadi kartu hanya muncul bila kategori jelas | Label atau kategori artikel yang ditampilkan | **Ya**, bila kartu dipilih dari label atau kategori artikel saja, tanpa mengubah keputusan | 2 |
| 4. Tombol umpan balik (A11.2) | Tanpa LLM | Sedang: bisa dimanipulasi (A11.2) | **Tahap 3** (catatan tanpa isi pesan) | Tidak; tunggu Tahap 3 | 3 |
| 2. Klarifikasi berbentuk gambar kartu untuk WhatsApp, dengan atribusi TurnBackHoax | Tanpa LLM; gambar dibuat dari teks artikel | Sedang-tinggi. Gambar mudah diteruskan tanpa konteks; kartu yang salah sasaran menyebar lebih jauh daripada teks. Hanya untuk jawaban "ditemukan", dan wajib memuat tautan artikel, tanggal, dan atribusi | Tombol salin klarifikasi Versi 2; izin konten Mafindo bila disebar luas | Tidak; setelah salah menuduh terukur | 4 |
| 5. Cek dari tangkapan layar (OCR) | OCR lokal atau layanan; kuota bila memakai LLM multimodal | Tinggi. Tangkapan layar sering memuat nama, nomor, dan foto orang lain; hasil OCR bisa salah baca | Tahap 3, kebijakan privasi (A9), evaluasi terpisah untuk teks hasil OCR | Tidak | 5 |

### A11.2 Rancangan umpan balik pengguna

**Prinsip:** umpan balik dipakai untuk memperbaiki sistem lewat tinjauan manusia. Sistem tidak belajar langsung
darinya. Model di sistem ini tidak belajar terus; pengetahuan baru datang dari pembaruan arsip.

**Yang dicatat** (mengikuti ADR 0006 dan Tahap 3):

- penilaian: "tepat" atau "tidak tepat";
- alasan pilihan ganda (opsional), misalnya "artikel membahas hal lain", "lembaga atau tokoh berbeda", "informasi
  ini benar", "sudah kedaluwarsa";
- id artikel yang ditampilkan, jenis jawaban, versi sistem, dan waktu.

Isi pesan **tidak** disimpan.

**Alur:**

1. Umpan balik masuk sebagai sinyal ke **antrean tinjauan manusia**. Tidak ada perubahan otomatis pada indeks,
   aturan, prompt, atau tampilan.
2. Peninjau melihat agregat per artikel, misalnya artikel yang sering dinilai "tidak tepat" pada jawaban
   "ditemukan".
3. Hasil tinjauan bisa menjadi butir set uji berikutnya, atau dasar perbaikan aturan dan pedoman.
4. Perbaikan dirilis sebagai versi baru setelah dievaluasi ulang dengan set uji yang dikunci.

**Ancaman dan pengamannya:**

| Ancaman | Pengaman |
| --- | --- |
| Manipulasi massal (mis. artikel hoaks ditandai "tidak tepat" beramai-ramai agar tampak benar) | Umpan balik tidak pernah mengubah jawaban; batas laju per sesi dan per proses; agregasi per artikel dan per hari; lonjakan mendadak ditandai untuk diperiksa, bukan dihitung |
| Umpan balik mencerminkan keyakinan pengguna, bukan kebenaran (mis. "tidak tepat" karena pengguna percaya hoaksnya) | Penilaian dibaca sebagai "pengguna tidak setuju", bukan sebagai label. Label hanya ditetapkan peninjau dengan pedoman. Alasan "informasi ini benar" diperlakukan sebagai permintaan periksa, bukan bukti |
| Spam dan isian otomatis | Satu penilaian per hasil pemeriksaan; tidak ada kolom teks bebas; batas laju yang sama dengan pemeriksaan |

**Kenapa tidak ada pembelajaran daring:** angka evaluasi hanya sah untuk sistem yang dievaluasi. Bila sistem berubah
sendiri dari umpan balik, setiap jawaban berasal dari sistem yang sedikit berbeda, sehingga angka pra-registrasi dan
uji kunci kehilangan artinya. Selain itu, umpan balik yang dimanipulasi atau keliru langsung masuk ke perilaku
sistem tanpa ada yang memeriksa. Dengan perbaikan lewat versi, setiap versi tetap bisa dievaluasi dan
direproduksi.

**Kenapa tinjauan butuh pesannya, padahal pesan tidak disimpan:** penilaian "tidak tepat" pada sebuah artikel tidak
bisa diperiksa tanpa tahu pesan apa yang dicocokkan dengannya. Tanpa pesan, peninjau hanya bisa melihat bahwa ada
ketidaksetujuan, bukan penyebabnya.

**Opsi persetujuan eksplisit (usulan):**

- Setelah memberi penilaian "tidak tepat", pengguna bisa memilih kotak "Sertakan pesan saya untuk ditinjau". Bawaannya
  **tidak dicentang**.
- Sebelum dikirim, pesan ditampilkan kembali, dan pengguna diminta menghapus data pribadi. Sistem juga menjalankan
  pemeriksaan data pribadi otomatis (pola yang sama dengan `pii_flags`) dan menolak menyimpan bila ditemukan nomor,
  surel, atau tautan pribadi, sampai pengguna menghapusnya.
- Pesan disimpan **terpisah** dari catatan aktivitas, dengan masa simpan terbatas (misalnya 90 hari), hanya bisa
  dibaca peninjau, dan dihapus setelah ditinjau atau setelah masa simpan habis.
- Pesan yang disertakan tidak pernah dipakai untuk pelatihan model, dan tidak diterbitkan. Bila dijadikan butir set
  uji, pesannya diperlakukan seperti kutipan Liputan6: dibersihkan, dan yang di-commit hanya hash-nya.
- Kebijakan ini dijelaskan di halaman Tentang dan di kebijakan privasi (A9).

### A11.3 Alat bantu tampilan: nominal dan saluran berdampingan (usulan; tidak mengubah keputusan)

**Usulan.** Di kotak "Pastikan klaimnya benar-benar sama" pada jawaban "ditemukan", tampilkan nominal dan saluran
(tautan atau nomor) yang terbaca dari pesan pengguna dan dari artikel, berdampingan. Ekstraksinya **deterministik**
(pola teks), bukan LLM. Fitur ini muncul setelah keputusan dibuat, tidak memengaruhi keputusan, dan tidak tercatat di
berkas hasil evaluasi, jadi **tidak memengaruhi metrik**.

**Dasarnya masih tipis, dan perlu dicatat apa adanya.** Kestabilan 89-98% pada uji kemarin (A2.7) adalah kestabilan
**ekstraksi LLM**. Itu hanya menunjukkan bahwa kedua unsur itu umumnya tertulis jelas di teks, bukan bahwa pola
deterministik membacanya dengan benar. Untuk ekstraksi deterministik, buktinya baru: pola nominal gagal membaca 4 kali
(hitungan sementara, A2.7), dan pola saluran **belum diukur sama sekali**.

**Risiko bila ekstraksi salah baca:**

1. Pengguna membandingkan nilai yang keliru, lalu menyimpulkan "sama" atau "berbeda" dari tampilan itu. Tampilan yang
   tampak rapi bisa memberi rasa pasti yang tidak semestinya.
2. **Menyebarkan ulang kontak penipu.** Narasi artikel memuat tautan dan nomor penipu (aturan wajib #1). Menampilkannya
   apa adanya, apalagi sebagai tautan yang bisa diklik, sama dengan menyebarkannya lagi.
3. "Tidak terbaca" dibaca pengguna sebagai "tidak ada", padahal bisa berarti pola gagal membaca.

**Cara menampilkan:**

- Dua kolom: "Di pesan Anda" dan "Di artikel". Nilai ditampilkan sebagai teks biasa, **tidak pernah sebagai tautan**.
- Dari artikel: tautan hanya ditampilkan **domainnya**, dengan titik dipisah (mis. `contoh[.]com`); nomor telepon disamarkan
  kecuali 4 digit terakhir (mis. `08xx-xxxx-1234`). Dari pesan pengguna: nilai ditampilkan seperti yang ditulis pengguna,
  karena itu teksnya sendiri.
- Bila tidak ada nilai yang terbaca: tulis **"Tidak terbaca otomatis. Periksa sendiri di teks."**, bukan "tidak ada" atau
  "tidak disebut".
- Tidak ada tanda centang, silang, warna hijau atau merah, maupun kesimpulan otomatis "sama" atau "berbeda". Pengguna
  yang membandingkan.
- Baris disembunyikan bila kedua sisi sama-sama tidak terbaca.

**Pemeriksaan ketepatan sebelum tampil di demo (kriteria dikunci di commit tersendiri sebelum diperiksa):**

- **Sampel:** 120 teks yang belum pernah dipakai, dipilih acak dengan benih yang dicatat saat kriteria dikunci: 60 Narasi
  dari arsip TurnBackHoax sebelum September 2025 (di luar indeks; mewakili teks bergaya pesan) dan 60 artikel dari indeks
  1.532 artikel (terbit sampai 27 September 2026, supaya tidak menyentuh periode set (b)). Ke-45 artikel dan 47 pesan uji
  kelayakan kemarin dikeluarkan.
- **Pemeriksaan manual oleh pemilik proyek, tanpa AI,** per teks dan per unsur (nominal, saluran): nilai yang ditampilkan
  benar atau salah, dan nilai yang ada di teks tetapi tidak ditampilkan.
- **Ukuran per unsur:**
  - *salah tampil* = nilai yang ditampilkan tetapi salah baca atau tidak ada di teks, dibagi semua nilai yang ditampilkan;
  - *terlewat* = teks yang menyebut unsur itu tetapi tampil "tidak terbaca", dibagi semua teks yang menyebut unsur itu.
- **Kriteria (usulan):** sebuah unsur boleh tampil di demo bila batas atas Wilson 95% *salah tampil* < 5% **dan** batas
  atas Wilson *terlewat* < 20%. Bila salah satu tidak terpenuhi, unsur itu tidak ditampilkan. Bila jumlah nilai yang
  ditampilkan kurang dari 73 (jumlah minimal agar batas atas < 5% bisa tercapai dengan 0 kesalahan, A4.a), sampel ditambah
  60 teks lagi dengan aturan yang sama, satu kali saja.
- **Biaya:** 0 panggilan LLM; sekitar 2-3 jam pemeriksaan manual.

**Tempatnya:** fitur setelah Versi 2 (A11), tetapi boleh dikerjakan bersamaan dengan Versi 2 karena tidak menyentuh
keputusan maupun evaluasi. **Keputusan 18:** pemeriksaan ketepatannya ditunda sampai pedoman disetujui dan set (a)
selesai dilabeli.

## A12. Urutan kerja sampai Kunci 1

**Langkah berikutnya (revisi 8): pemilik proyek memutuskan prinsip utama (A6.10, baris 2a-1).** Urutan sampai kunci:
2a-1 -> revisi pedoman -> 2a-2 (daftar acuan) -> 2d (uji coba) -> revisi -> 2e (pemeriksaan independen) -> revisi
-> 2b -> 2c. Lembar persetujuan sudah diisi 2026-10-27 (baris 1), pedoman sudah direvisi menjadi draf 2.0
(baris 2), dan K1-K13 sudah diputuskan (A6.6). Pelabelan apa
pun, termasuk latihan anotator kedua, baru dimulai setelah pedoman dikunci (baris 2c).

| No | Pekerjaan | Siapa | Perkiraan jam | Bisa dicicil? |
| --- | --- | --- | --- | --- |
| 1 | ~~Menyetujui pedoman A6 lewat lembar persetujuan~~ **Selesai 2026-10-27** (A6.3) | Pemilik proyek | -- | -- |
| 2 | Merevisi pedoman sesuai lembar: **draf 2.0 selesai 2026-10-27** (`testset/ANNOTATION_GUIDE_v2.md`); pemilik proyek memeriksa teksnya | Claude Code + pemilik proyek | 0,5 (pemeriksaan) | Tidak |
| 2a | ~~Memutuskan K1-K13 (A6.4)~~ **selesai 2026-10-27 (A6.6)**; tersisa: usulan K4 dan K11 (A6.8) dan temuan N1-N8 (A6.9), lalu pedoman 2.0 direvisi dan diperiksa ulang | Pemilik proyek, lalu Claude Code | belum diperkirakan | Ya, per temuan |
| 2b | Menyetujui rencana penguncian pedoman (A6.5) | Pemilik proyek | 0,5 | Tidak |
| 2a-1 | Memutuskan prinsip utama "Kesimpulan membantah pesan" (A6.10), lalu pedoman 2.0 direvisi (keputusan 44-51 ikut diterapkan) | Pemilik proyek, lalu Claude Code | belum diperkirakan | Tidak |
| 2a-2 | Menyusun daftar acuan saluran resmi bertanggal (keputusan 49): lembaga yang muncul di kandidat, sumber acuan, tanggal | belum ditetapkan | belum diperkirakan | Ya |
| 2d | **Uji coba pedoman** (A6.5 langkah 2): ~10 butir di `uji_coba_pedoman_v2.xlsx`, setelah 2a-1; waktu per butir dan bagian yang meragukan dicatat; revisi sesudahnya dicatat sebagai revisi sebelum kunci | Pemilik proyek, lalu Claude Code | ~1-2 (perkiraan) | Ya |
| 2e | **Pemeriksaan independen** (A6.5 langkah 3): sesi agent baru yang hanya membaca pedoman 2.0; temuannya dilaporkan, revisi diputuskan pemilik proyek | Pemilik proyek menjalankan sesi | ~0,5 | Tidak |
| 2c | **Mengunci pedoman 2.0** (setelah 2d dan 2e): commit kunci (Claude Code), lalu tag `annotation-guide-v2.0`, push, GitHub Release, Internet Archive (pemilik proyek) | Claude Code + pemilik proyek | 0,5 + 0,5 | Tidak |
| 3 | ~~Menyetujui ambang uji pergeseran (A4.f)~~ **Selesai di revisi 5** (keputusan 20) | Pemilik proyek | -- | -- |
| 4 | Membaca halaman hak cipta sumber set (a) dan memilih sumber (A10 no. 1) | Pemilik proyek | 1 | Ya |
| 5 | Mengumpulkan dan melabeli set (a), 150 butir; **perkiraan jam diukur ulang setelah 10 butir pertama dilabeli** (waktu per butir dicatat, keputusan 31) | Pemilik proyek | 15-25 (tebakan awal) | **Ya**, misalnya 10-20 butir per sesi |
| 6 | Mencari anotator kedua; latihan 5 butir; melabeli 40 butir set (a) | Pemilik proyek dan anotator kedua | 3-4 (anotator) | Ya |
| 7 | Menghitung kesepakatan set (a) (mentah, kappa, AC1, PABAK) dan mengadjudikasi yang tidak sepakat | Claude Code + pemilik proyek | 1-2 | Tidak |
| 8a | Menambah pencatatan versi (medan respons API, versi pustaka, revisi model embedding, sidik jari indeks) ke skrip evaluasi; uji offline | Claude Code + tinjauan pemilik proyek | 1-2 + 0,5 | Tidak |
| 8 | Menulis `testset/v2.meta.json` versi 1 (pedoman, set a, prosedur set b, metrik, ambang, ambang uji pergeseran) | Claude Code + tinjauan pemilik proyek | 2 + 1 | Tidak |
| 9 | Kunci 1: commit, tag `testset-v2-kunci1`, push, GitHub Release, Internet Archive (A3.4) | Pemilik proyek | 0,5 | Tidak |

**Boleh dikerjakan kapan saja, karena tidak menyentuh keputusan maupun evaluasi:** tombol salin klarifikasi (1-2 jam
Claude Code + tinjauan).

**Ditunda (keputusan 18):** pemeriksaan ketepatan alat bantu tampilan A11.3, sampai pedoman disetujui dan set (a) selesai
dilabeli.

**Setelah Kunci 1 (keputusan 17 dan 21):** hari 1, uji pergeseran awal (162 panggilan) lalu evaluasi set (a) dimulai;
hari 2, evaluasi set (a) selesai (total 450 panggilan) lalu uji pergeseran akhir (162 panggilan). Januari 2027: set (b)
dilabeli, Kunci 2, lalu jadwal yang sama untuk set (b). Rincian di A8.

## A13. Arah perbaikan perilaku sistem untuk versi berikutnya (belum dikunci)

Kesalahan sistem yang terbukti, dan kandidat perbaikannya. Semua kandidat dibangun sebagai **modul baru**; berkas
terkunci Versi 1 tetap utuh, dan setiap kandidat diuji pada set uji baru dengan kriteria yang dikunci lebih dulu.
Angka di bawah berasal dari evaluasi eksternal (`rancangan_evaluasi_eksternal.md` 11.2, 11.3, 11.9).

| Kesalahan yang terbukti | Bukti | Kandidat perbaikan (modul baru) | Risiko yang harus diukur |
| --- | --- | --- | --- |
| **Kegagalan retrieval** (artikel yang benar tidak masuk 3 teratas) | 5 dari 10 kegagalan positif; pencarian dengan judul Liputan6 menemukan 44/46, sedangkan dengan kutipan pesan 41/46, jadi ada sinyal kata kunci yang hilang | pencarian hibrida (kata kunci seperti BM25 + embedding), atau reranker setelah retrieval | memori laptop (reranker berbasis model menambah beban CPU dan RAM); kandidat baru bisa memunculkan tetangga yang lebih mirip dan menaikkan kecocokan palsu |
| **Penolakan palsu oleh generator** | setelah adjudikasi, 6 dari 9 penolakan palsu tetap kesalahan sistem; sebagian besar pasangan lintas gelombang | generator baru dengan prompt yang memuat pedoman A6 (terutama aturan gelombang), sebagai berkas baru yang dikunci terpisah | menaikkan kecocokan palsu pada penipuan berpola sama, jenis kesalahan yang sudah gugur; keduanya tidak boleh disetel terpisah |
| **Pencatutan tokoh dan perbedaan tindakan** | P2-17 (tokoh), P2-33 (tindakan) | perbandingan unsur inti yang eksplisit (subjek atau tokoh, tindakan), dengan ekstraksi yang lolos uji kestabilan **secara makna** | uji kemarin menunjukkan tindakan tidak stabil secara isi (A2.7); tanpa ekstraksi yang stabil, perbandingan ini tidak bisa dipercaya |

**Pelajaran dari uji ekstraksi (A2.7):** untuk unsur teks bebas, kestabilan harus dinilai **secara makna** (dua hasil
dinilai manusia "bermakna sama"), bukan dengan kesamaan teks persis, dan definisi itu dikunci sebelum uji dijalankan.

**Urutan yang saya sarankan:** retrieval lebih dulu, karena separuh kegagalan positif ada di sana dan pencarian hibrida
tidak memakai kuota LLM. Perubahan generator menyusul, setelah Versi 2 memberi ukuran yang stabil, karena tanpa label
yang stabil perbaikan generator tidak bisa diukur.

---

# Bagian B. Rancangan 2026-10-03 dan pengukurannya (riwayat)

**Status: riwayat.** Isinya dipertahankan apa adanya. Penanda di tiap judul bagian menyatakan apakah isinya masih
berlaku untuk rancangan Bagian A. Rujukan "bagian N" di dalam Bagian B menunjuk bagian B.N.

**Status bagian lama (ringkasan):**

| Bagian | Status | Alasan |
| --- | --- | --- |
| 0. Keputusan 2026-10-03 | SEBAGIAN BERLAKU | Keputusan 1 (cakupan pesan panjang) dan 3 (verdict ketiga di luar cakupan) digantikan Bagian A; keputusan 2, 4, 6, 9, 10, 11 tetap |
| 1. Masalah dan buktinya | SEBAGIAN BERLAKU | M3 (ambang skor tidak memisahkan) dan M4 (rujukan) tetap menjadi dasar; M1 tidak lagi menjadi masalah utama |
| 2. Komponen | TIDAK BERLAKU LAGI | Komponen pesan panjang tidak dibangun; 2.2 kebersihan rujukan boleh dipakai sebagai metrik tambahan |
| 3. Pemisahan dari Versi 1 | MASIH BERLAKU | Prinsipnya sama dengan A3; struktur modulnya diganti |
| 4. Hipotesis | TIDAK BERLAKU LAGI | Diganti metrik dan ambang A4.e |
| 5. Rencana evaluasi | SEBAGIAN BERLAKU | 5.1 (uji kemunduran di `archive/v1`, indeks beku terpisah) dan 5.4 tetap; ablasi K0-K2 tidak berlaku |
| 6. Set uji | SEBAGIAN BERLAKU | 6.1 tetap; 6.2-6.4 (pesan panjang) tidak berlaku |
| 7. Kendala nyata | MASIH BERLAKU | Angka kuota dan memori tetap; hitungan panggilan diganti A8 |
| 8. Di luar cakupan | SEBAGIAN BERLAKU | Baris verdict ketiga digantikan A1 |
| 9. Yang masih terbuka | TIDAK BERLAKU LAGI | Diganti A10 |
| 10. Pengukuran pesan panjang | MASIH BERLAKU (sebagai bukti) | Dasar keputusan meninggalkan cakupan pesan panjang |
| 11. Celah terhadap Liputan6 | MASIH BERLAKU (sebagai bukti) | Dasar penilaian cakupan dan pedoman A6 |

## Status asli rancangan 2026-10-03

**Status: dokumen rancangan; belum ada kode Versi 2.** Disusun 2026-10-03 dari berkas di
repositori (daftar di bagian akhir); diperbarui pada hari yang sama dengan keputusan pemilik
proyek atas dua belas pertanyaan terbuka (bagian 0). Bila datanya tidak cukup untuk disimpulkan,
itu ditulis terus terang.

**Rancangan ini BELUM boleh dilanjutkan ke pembangunan.** Langkah pertama yang ditetapkan pemilik
proyek adalah mengukur apakah masalah pesan panjang memang terjadi pada pesan berantai ASLI
(bagian 10). Bila ternyata jarang, cakupan Versi 2 dipikir ulang.

Dokumen ini mengoreksi pemetaan lama di `testset/v1_temuan_untuk_v2.md` bagian 7 dan tabel
"Rencana Versi 2" di README: beberapa komponen di sana dicantumkan dengan bukti yang, setelah
diperiksa ulang, tidak mendukungnya.

---

## 0. Keputusan pemilik proyek (2026-10-03) **[SEBAGIAN BERLAKU]**

| # | Pertanyaan | Keputusan |
| --- | --- | --- |
| 1 | Cakupan | **Dipersempit: penanganan pesan panjang + pengukuran kebersihan rujukan.** Komponen lain tidak masuk, bahkan sebagai eksperimen (kuota terbatas, tidak ada bukti). |
| 2 | Grader | **Tidak masuk.** Generator sudah menilai kesamaan klaim; empat perbedaan yang mungkin dibawa grader tidak punya bukti. |
| 3 | "Mungkin terkait", verdict ketiga | **Tetap mati; verdict ketiga di luar cakupan** (perubahan produk, bukan perbaikan yang dijawab data). |
| 4 | Kerangka | **Pipeline Python biasa.** |
| 5 | Snapshot | **Disetujui, tidak dikerjakan sekarang.** Bila rancangan dilanjutkan: antrean digabung dan di-ingest dulu (ingest dimulai pemilik proyek), baru snapshot dibekukan, sebelum set uji v2 dibangun. Aturan Wajib #6 ditambah (CLAUDE.md). |
| 6 | Juri | **Tanpa juri LLM.** |
| 7 | Ukuran set uji | **140 butir terlalu berat. Dua tujuan dipisah:** uji kemunduran memakai set uji v1 di atas `archive/v1`; uji kemampuan baru memakai butir pesan panjang baru (bagian 6). |
| 8 | Sumber pesan panjang | **Positif: Liputan6 Cek Fakta** (sering mengutip pesan berantai utuh; `robots.txt`-nya mengizinkan), asalkan hoaksnya juga ada di basis data. **Negatif: arsip TurnBackHoax sebelum September 2025**, setelah diverifikasi tidak ada di basis data. Pemeriksaan data pribadi wajib untuk keduanya. |
| 9 | Mutu klarifikasi | **Di luar cakupan** (mengubah prompt mencampur efeknya dengan perbaikan pesan panjang). |
| 10 | Menghapus Penjelasan dari indeks | **Ditunda** (mengubah indeks dan snapshot; tidak berkaitan dengan masalah yang dijawab). |
| 11 | `retriever.py` | **Dikunci dengan hash sebelum evaluasi**, karena Versi 2 mengimpornya. |
| 12 | Pedoman anotasi | **Tambahan, bukan revisi: versi 1.1** untuk pesan berantai yang memuat beberapa klaim; dikunci sebelum pelabelan; aturan v1.0 lainnya tidak diubah (bagian 6.4). |

Ketentuan tambahan: **hipotesis Versi 2 beserta ambangnya dikunci sebelum pelabelan dimulai**,
seperti Versi 1; perhitungan ukuran sampel disimpan di repositori
(`src/evaluation/sample_size.py`, `testset/v2_ukuran_sampel.json`).

---

## 1. Masalah yang dijawab Versi 2, dan kekuatan buktinya **[SEBAGIAN BERLAKU]**

Untuk tiap masalah dibedakan **bukti bahwa masalahnya ada** dan **bukti bahwa solusi yang
diusulkan menyelesaikannya**. Skala: *kuat* = terukur, selisihnya jauh di atas kebetulan; *lemah* =
terukur tetapi sampel kecil, sintetis, atau tidak dapat dibedakan dari kebetulan; *tidak ada* =
belum pernah diukur.

| # | Masalah | Bukti masalah | Bukti solusi |
| --- | --- | --- | --- |
| M1 | Klaim di dalam pesan panjang tidak ikut dicari (terpotong 512 token) | **Kuat untuk mekanismenya**, lemah untuk besarnya pada pesan nyata | Tidak ada |
| M2 | Keputusan "klaim sama" generator kadang keliru atau tidak stabil antar-run | Lemah (2 kesalahan, 5 butir non-batas tidak bulat, dari 50) | Tidak ada |
| M3 | Fitur "Mungkin terkait" tidak dapat diwujudkan dengan ambang skor | **Kuat** | Tidak ada |
| M4 | Kebersihan dan kredibilitas RUJUKAN yang ditampilkan | **Kuat** (temuan data), tetapi tidak pernah diukur pada jawaban | Sebagian sudah diperbaiki di Versi 1; sisanya tidak ada |
| M5 | Klarifikasi sulit dibaca / terlalu tipis | Lemah (pengamatan, bukan pengukuran) | Tidak ada |
| -- | Retrieval gagal menemukan artikel yang benar pada klaim pendek | **Tidak ada bukti masalah** | -- |
| -- | Kredibilitas DOKUMEN hasil retrieval | **Tidak ada** (satu sumber) | -- |

### M1. Pesan panjang: klaim terdorong keluar dari jendela embedding

- **Bukti masalah (mekanisme): kuat.** Retrieval hanya meng-embed 512 token pertama kueri
  (`MAX_SEQ_LENGTH`). Pada 20 butir positif dengan pengganggu di depan dan belakang klaim,
  Recall@3 pada ~5.000 karakter adalah **2/20 pada arsip** (`testset/retrieval_ablation_report.txt`
  baris 115), **0/20 pada indeks 922** dan **0/20 pada indeks 1.532**
  (`retrieval_ablation_prod922_report.txt`, `retrieval_ablation_prod1532_report.txt` baris 115);
  klaim berada di luar 512 token pada 18/20. Kondisi pembanding (klaim di awal pesan, pengganggu
  di belakang) tetap **19/20** pada ketiga indeks (baris 121), jadi penyebabnya pemotongan token,
  bukan panjang itu sendiri. Pada ~1.500 dan ~3.000 karakter: 19/20.
- **Yang tidak diketahui: besar masalahnya pada pesan nyata.** Teks pengganggunya **sintetis**
  (sapaan, ajakan menyebarkan, tanda baca berlebihan; laporan ablasi menandainya "INDIKATIF"). Belum
  ada satu pun pesan berantai asli yang diukur: tidak diketahui seberapa sering pesan nyata
  melebihi 512 token, dan di mana klaimnya berada di dalam pesan. Set uji v1 tidak menguji rentang
  ini (klaim terpanjang 749 karakter / 152 token; `v1_temuan_untuk_v2.md` bagian 4.2).
- **Mitigasi yang sudah ada di Versi 1:** demo membatasi masukan 1.500 karakter dan memperingatkan
  sejak ~220 token (CLAUDE.md, "Keterbatasan yang Diketahui"). Jadi bagi pengguna demo masalah ini
  sekarang berbentuk "pesan panjang ditolak", bukan "pesan panjang dijawab keliru".
- **Bukti solusi: tidak ada.** Belum pernah diukur apakah ekstraksi klaim oleh LLM memulihkan
  recall, maupun apakah ekstraksi itu merusak klaim pendek.

### M2. Penilaian "klaim sama" oleh generator

- **Bukti masalah: lemah.** Pada set uji v1 (3 run x 54 butir; `testset/v1_analysis_report.txt`):
  akurasi non-batas modus **48/50**, Wilson95 [0,865; 0,989]. Kesalahan: `v1-020` (penolakan
  palsu, keliru di ketiga run) dan `v1-036` (kecocokan palsu, keliru di 2 dari 3 run). Enam butir
  tidak bulat antar-run (`v1-006`, `v1-010`, `v1-036`, `v1-039`, `v1-040`, dan `v1-053` yang
  berstatus batas); pada ketujuh butir unik itu artikel yang benar sudah ada di top-3
  (`v1_temuan_untuk_v2.md` bagian 2). Akurasi non-batas per run tunggal, dihitung dari
  `data/testset_v1_eval_gemini-3.5-flash-lite.jsonl`: **46/50, 47/50, 48/50**.
- **Mengapa "lemah":** 2 kesalahan dari 50 berada di dalam interval yang sama dengan 0 kesalahan;
  44% butir berbagi artikel jangkar (caveat 1 laporan analisis), sehingga interval itu pun terlalu
  percaya diri; dan subtipe `angka_waktu_beda` (tempat `v1-036`, `v1-039`, `v1-040` berada) 100%
  buatan model (caveat 3: confound sumber).
- **Bukti solusi: tidak ada.** Lihat bagian 2.2: belum ada bukti bahwa node grader terpisah
  menilai lebih baik daripada generator yang sudah menilai hal yang sama.

### M3. "Mungkin terkait" dengan ambang skor

- **Bukti masalah: kuat.** (a) Pada indeks 922 dan 1.532 tidak ada ambang yang memisahkan: kueri
  tak terkait "bumi datar" berskor 0,6385, di atas kandidat yang layak tampil (0,5739-0,63)
  (`config/related_threshold.json`; `testset/devset_retrieval_1532.json`). (b) Kegagalannya
  struktural: skor kandidat teratas sebuah kueri tidak bisa turun saat indeks diperbesar (chunk
  lama dan embedding-nya tetap), sehingga jarak antara "tak terkait" dan "layak tampil" hanya bisa
  menyempit. Terukur: skor top-1 tertinggi negatif mudah yang klaimnya tidak ada di basis data
  0,5351 (150 artikel) -> 0,5666 (922) -> 0,6308 (1.532, `v1-046`) (`v1_temuan_untuk_v2.md` bagian
  6.1). Fitur ini dimatikan sejak indeks 922.
- **Bukti solusi: tidak ada.** `v1_temuan_untuk_v2.md` bagian 6.1 mengusulkan grader sebagai
  pengganti. Itu **usulan, bukan temuan**: belum ada pengukuran apa pun bahwa LLM dapat memisahkan
  "topik sama, klaim berbeda" dari "tidak terkait" dengan andal. Yang ada hanyalah alasan di kolom
  `alasan` generator pada butir negatif sulit, yang tidak pernah dinilai benar-salahnya.
- **Ini fitur tampilan, bukan vonis.** Tidak ada temuan bahwa ketiadaan fitur ini merugikan
  pengguna; ia berkaitan dengan kandidat verdict ketiga "artikel terkait" (CLAUDE.md, "Status
  Pengembangan"), yang juga belum diputuskan.

### M4. Rujukan yang ditampilkan

Dua hal yang selama ini tercampur dalam "penilaian kredibilitas sumber" dipisahkan:

**(a) Kredibilitas dokumen hasil retrieval -- tidak ada temuan, dan tidak bisa ada.** Konsep
Corrective RAG menilai kredibilitas dokumen yang ditemukan. Di proyek ini semua dokumen berasal
dari satu sumber (artikel TurnBackHoax), jadi tidak ada variasi kredibilitas dokumen untuk dinilai.
`v1_temuan_untuk_v2.md` bagian 3 mencatat "tidak ada temuan kuantitatif"; itu benar untuk
pengertian ini.

**(b) Kredibilitas dan kebersihan RUJUKAN -- banyak temuan** (CLAUDE.md, "Temuan Aturan Wajib #1";
`v1_temuan_untuk_v2.md` bagian 9):

- Baris "Sumber:" di seksi Hasil Periksa Fakta bercampur: sumber hoaks dan situs pembanding yang
  sah. Dari 2.106 URL di baris itu, 1.987 berdomain daftar-blokir; pada 3 artikel (32110, 31532,
  33497) baris itu memuat situs resmi/media. Sebelum diperbaiki, URL "Sumber:" tampil sebagai
  rujukan pada 10 artikel (8 di indeks produksi).
- Pemendek URL: 13 rujukan tampil berpemendek pada 1.532 artikel; tujuannya tidak dapat
  diverifikasi sebelum diklik. Penyaringannya ikut membuang rujukan yang kemungkinan sah (36089).
- Pengecualian `*.go.id` berisiko: situs pemerintah dapat diretas (CLAUDE.md, "Keterbatasan").
- Daftar media/cek fakta tepercaya (`links.TRUSTED_SOURCE_DOMAINS`) disusun melingkar dari domain
  yang muncul sebagai rujukan di data.
- Media sosial disaring seluruhnya per domain, termasuk akun resmi instansi; 205 dari 1.532
  artikel tidak punya rujukan yang boleh ditampilkan.
- **Celah evaluasi:** evaluasi Versi 1 mengukur URL karangan LLM (0), tetapi tidak pernah mengukur
  kebersihan rujukan yang berasal dari data, dan berkas hasil tidak menyimpan rujukan jawaban.

**Bukti solusi:** perbaikan berbasis aturan (daftar domain, baris "Sumber:", penyaringan ulang saat
tampil) **sudah diterapkan di Versi 1** dan terverifikasi lewat parse ulang 1.532 artikel (0
rujukan tampil berdomain daftar-blokir, 0 yang juga `claim_sources`). Untuk penilaian kredibilitas
per-URL oleh LLM (mis. membedakan akun resmi dari akun penyebar hoaks) **tidak ada bukti sama
sekali**, dan percobaan meloloskan beranda akun pernah gagal diverifikasi (CLAUDE.md,
"Keterbatasan": 11 beranda akun tidak dapat diperiksa dari klien HTTP).

### M5. Mutu klarifikasi (di luar cakupan; keputusan 9)

- **Bukti masalah: lemah.** Tiga contoh keluaran untuk satu artikel (36730) yang dinilai padat dan
  sulit diikuti (`v1_temuan_untuk_v2.md` bagian 4.1) -- pengamatan pemilik proyek, bukan
  pengukuran. Ditambah temuan data: pada artikel Sep-Nov 2025 Kesimpulan hanya satu kalimat (median
  136-140 karakter vs 239), sehingga klarifikasi yang disusun darinya tipis (CLAUDE.md,
  "Keterbatasan").
- **Bukti solusi: tidak ada.** Mengubah prompt membatalkan baseline Versi 1 dan pengaruhnya pada
  akurasi belum diukur.

### Yang BUKAN masalah terbukti

- **"Retrieval gagal menemukan artikel yang benar."** Empat kegagalan Recall@3 Versi 1 (`v1-022`,
  `v1-024`, `v1-027`, `v1-033`) **semuanya butir negatif sulit** (`testset/v1.jsonl`:
  `expected_verdict = belum_ditemukan`); yang "gagal ditemukan" di sana adalah artikel TETANGGA,
  dan jawaban yang benar untuk keempatnya memang "belum ditemukan". Itu bukan bukti bahwa retrieval
  menggagalkan jawaban. Untuk butir positif, Recall@3 adalah **20/20** pada arsip, indeks 922, dan
  indeks 1.532 (ketiga laporan ablasi, eksperimen 1), baik pencarian eksak maupun retriever
  produksi. Akibat sebenarnya dari keempat butir itu adalah batas tafsir H1 (H1 hanya teruji pada
  17 dari 20 negatif sulit; `v1.meta.json`, `batas_tafsir_H1_recall_2026-09-23`), bukan kebutuhan
  akan penulis ulang kueri.
- **Parameter retrieval (top-k, agregasi).** Tidak ada yang dapat dibedakan dari kebetulan pada
  ketiga indeks (ablasi eksperimen 1 dan 2).

---

## 2. Komponen Versi 2 (setelah keputusan) **[TIDAK BERLAKU LAGI]**

Hanya dua, sesuai keputusan 1.

### 2.1 Penanganan pesan panjang (menjawab M1)

- **Tugas:** bila pesan terkena pemotongan (definisi mekanistik di bagian 10), klaimnya tetap
  ikut dicari.
- **Dua kandidat, diukur dulu pada tahap retrieval (tanpa generator):**
  - *Pencarian per potongan pesan, tanpa LLM:* pesan dipecah menjadi jendela <= 512 token, tiap
    jendela di-embed dan dicari, skor artikel = maksimum antar-jendela. Nol panggilan LLM,
    deterministik, tidak bisa mengarang klaim. Yang perlu diukur: pengganggu ikut dicari sehingga
    bisa memunculkan artikel yang mirip pengganggunya.
  - *Ekstraksi klaim oleh LLM:* satu panggilan tambahan untuk pesan yang terkena. Yang perlu
    diukur: klaim yang berubah makna, dan biaya kuota.
- **Aturan pemilihan (V2-H3):** bila pencarian per potongan menyamai ekstraksi LLM (selisih <= 2
  butir), yang dipilih pencarian per potongan.
- **Hanya aktif pada pesan yang terkena.** Untuk klaim di bawah batas token, jalur Versi 2 harus
  identik dengan Versi 1 (kueri yang sama, kandidat yang sama). Ini yang diperiksa uji kemunduran.
- Belum ada bukti untuk solusi mana pun (bagian 1, M1).

### 2.2 Pengukuran kebersihan rujukan (menjawab M4) **[MASIH BERLAKU, sebagai metrik tambahan]**

Bukan komponen LLM. Berkas hasil evaluasi menyimpan daftar rujukan tiap jawaban "ditemukan", dan
metrik di bagian 5.4 dihitung untuk kedua versi. Kelemahan daftar domain (melingkar, `.go.id`)
tetap dicatat sebagai keterbatasan, tidak diselesaikan Versi 2.

### 2.3 Yang ditimbang lalu tidak dimasukkan

- **Grader** (keputusan 2). Generator Versi 1 sudah menilai "klaim sama": prompt sistemnya memuat
  definisi resmi (KIA, unsur inti, uji dua arah, uji Kesimpulan), ia membaca tiga kandidat
  sekaligus, dan mengeluarkan `klaim_sama` serta `alasan`. Yang secara konkret bisa berbeda pada
  grader hanya empat hal -- satu kandidat per panggilan, keluaran per unsur, kategori "topik sama,
  klaim berbeda", dan pemungutan suara -- dan tidak satu pun punya bukti. Satu-satunya data:
  modus 3 run 48/50 vs run tunggal 46-48/50, tetapi `v1-020` keliru di ketiga run dan selisih 0-2
  butir tidak dapat dibedakan dari kebetulan.
- **Penulis ulang kueri saat retrieval gagal, "Mungkin terkait" lewat grader, penilai kredibilitas
  per-URL, perubahan gaya klarifikasi:** lihat bagian 8.

### 2.4 Kerangka: pipeline Python biasa (keputusan 4)

Alur yang dibutuhkan:

```
klaim -> [bila terkena pemotongan: pencarian per potongan / ekstraksi] -> retrieval -> generator Versi 1 (tak berubah) -> jawaban
```

Linear dengan satu cabang bersyarat, tanpa putaran. `langgraph` tidak ada di `requirements.txt`;
lapisan `src/llm/` (throttle, kuota, pencatatan panggilan) dipakai apa adanya; komponen
dinyalakan/dimatikan untuk ablasi lewat parameter fungsi.

---

## 3. Pemisahan dari Versi 1 **[MASIH BERLAKU (prinsip); struktur modul diganti A3]**

`src/generator.py` terkunci sejak tag `testset-v1`: `v1.meta.json` (`sidik_jari_generator_v1`)
menyimpan hash seluruh berkas, hash prompt+skema, model (`gemini-3.5-flash-lite`), dan
`thinking_level` (`medium`); `tests/test_testset_locks.py` gagal bila salah satunya berubah. Yang
di-hash saat ini hanya `generator.py`.

Karena cakupan dipersempit, **Versi 2 tidak punya prompt baru**: generator Versi 1 dipanggil apa
adanya. Struktur yang diusulkan (belum dibuat):

```
src/
  generator.py            # Versi 1 -- TIDAK disentuh; uji kunci tetap lolos
  retriever.py            # dipakai bersama; DIKUNCI dengan hash sebelum evaluasi (keputusan 11)
  v2/
    __init__.py
    long_message.py       # deteksi pesan terkena pemotongan; pencarian per potongan; (bila terpilih) ekstraksi LLM
    pipeline.py           # orkestrasi: klaim -> kandidat (v1 atau jalur pesan panjang) -> generator v1
  evaluation/
    testset_eval.py       # Versi 1 -- tidak diubah
    v2_eval.py            # menjalankan kondisi K0..K2 pada set uji; satu berkas hasil per kondisi, memuat rujukan jawaban
```

Ketentuan:

1. Versi 2 mengimpor dari Versi 1 (retriever, generator, lapisan `llm/`, `links`), tidak pernah
   sebaliknya, dan tidak mengubah berkas Versi 1.
2. Pengaman Versi 1 berlaku tanpa perubahan karena generatornya sama: status dari metadata,
   rujukan hanya dari metadata, `article_id` hanya dari kandidat, URL keluaran LLM dibuang.
3. Sebelum evaluasi: hash `retriever.py` ditambahkan ke sidik jari terkunci, dan `src/v2/` mendapat
   sidik jari serta uji kunci sendiri.
4. Demo memilih versi lewat setelan; bawaannya tetap Versi 1 sampai Versi 2 terukur.
5. Menyuntikkan kandidat tanpa mengubah `generator.py` dimungkinkan oleh kode yang ada:
   `AnswerGenerator` menerima `retrieve_fn(claim, top_k)` sebagai parameter konstruktor
   (`src/generator.py`), jadi Versi 2 cukup memberikan fungsi pencarian lain. Konsekuensinya:
   generator tetap menerima pesan UTUH sebagai `claim` (dipakai `build_user_prompt`), sehingga LLM
   membaca seluruh pesan panjang; pengaruhnya pada token masuk dan pada penilaian belum diukur.

---

## 4. Hipotesis yang dipra-registrasi (usulan; dikunci sebelum pelabelan) **[TIDAK BERLAKU LAGI]**

Bentuknya mengikuti H1 dan H3 Versi 1 (`v1.meta.json`, `ambang`). "Komponen tidak memberi
perbaikan" adalah hasil yang sah. Aturan tafsir mengikuti ablasi Versi 1: selisih bermakna hanya
bila McNemar eksak dua sisi p < 0,05 **dan** selisih bersih >= 3 butir. McNemar memberi p < 0,05
paling sedikit pada 6 perbaikan tanpa kemunduran (`testset/v2_ukuran_sampel.json`).

| Kode | Hipotesis | Ukuran | Terdukung | Gugur |
| --- | --- | --- | --- | --- |
| V2-H1 | Pada pesan panjang ASLI yang terkena pemotongan, penanganan pesan panjang menaikkan Recall@3 butir positif | Recall@3 Versi 1 vs Versi 2 pada butir positif pesan panjang, berpasangan | p < 0,05 dan selisih bersih >= 6 butir | Selisih bersih <= 2 butir |
| V2-H2 | Versi 2 tidak lebih buruk pada klaim pendek | (a) deterministik: untuk 54 butir set uji v1 pada `archive/v1`, kueri dan top-3 Versi 2 identik dengan Versi 1; (b) akurasi modus 3 run non-batas | (a) 54/54 identik; (b) kemunduran bersih <= 2 butir terhadap 48/50 | (a) ada satu saja yang berbeda; (b) kemunduran bersih >= 3 butir |
| V2-H3 | Ekstraksi oleh LLM lebih baik daripada pencarian per potongan tanpa LLM | Recall@3 butir positif pesan panjang, dua kondisi | LLM unggul bersih >= 3 butir, p < 0,05 | Selisih <= 2 butir -> **dipilih yang tanpa LLM** |
| V2-H4 | Penanganan pesan panjang tidak menaikkan kecocokan palsu | Kecocokan palsu pada butir negatif pesan panjang, Versi 1 vs Versi 2 | Kenaikan bersih <= 1 butir | Kenaikan bersih >= 3 butir |
| V2-H5 | Rujukan yang ditampilkan bersih | Rujukan pada jawaban "ditemukan" yang melanggar kebijakan penyaringan atau termasuk sumber klaim | 0 pada kedua versi | >= 1 (dilaporkan per artikel; pemeriksaan sifat, bukan uji statistik) |
| V2-H6 | Biaya Versi 2 | Panggilan LLM dan latensi per kueri | Dilaporkan; tanpa ambang | -- |

**Batas tafsir V2-H2, ditulis eksplisit atas permintaan pemilik proyek:** set uji v1 **hanya sah
untuk menunjukkan Versi 2 tidak lebih buruk, tidak untuk mengklaim perbaikan**. Set itu sudah
dibedah berkali-kali; butir mana yang salah dan mengapa sudah diketahui, dan rancangan Versi 2
disusun dengan pengetahuan itu. Selain itu seluruh klaim di set uji v1 pendek (terpanjang 749
karakter / 152 token), jadi jalur pesan panjang tidak aktif di sana: yang diperiksa (a) adalah
bahwa jalur klaim pendek memang tidak berubah, dan selisih pada (b) hanyalah variasi acak LLM
(run tunggal Versi 1: 46, 47, 48 dari 50).

Urutan pengunci: hipotesis dan ambang ditulis ke `testset/v2.meta.json` -> pedoman 1.1 dikunci ->
baru pelabelan dimulai. Kode hipotesis lama H4 (Gemma sebagai juri) tidak dibawa (keputusan 6).

---

## 5. Rencana evaluasi **[SEBAGIAN BERLAKU]**

### 5.1 Dua tujuan, dua tempat **[MASIH BERLAKU (uji kemunduran di archive/v1, indeks beku terpisah)]**

| Tujuan | Set uji | Indeks | Parameter retrieval |
| --- | --- | --- | --- |
| Uji kemunduran (V2-H2) | set uji v1 (54 butir, beku) | `archive/v1` (150 artikel) | milik arsip: `ef_search` 100 |
| Uji kemampuan baru (V2-H1, H3, H4, H5) | butir pesan panjang baru (set uji v2) | snapshot baru yang dibekukan | `ef_search` 2000 |

- **Kedua versi selalu dijalankan pada set, indeks, dan parameter yang sama** di tiap baris.
  `top_k` = 3, `CHUNK_FETCH` = 30, agregasi maksimum, model embedding dan `MAX_SEQ_LENGTH` tidak
  diubah.
- **Snapshot baru** (keputusan 5): belum dibuat. Urutannya bila rancangan dilanjutkan: antrean
  digabung dan di-ingest (dimulai pemilik proyek) -> `index_check` dan `retriever_exactness` ->
  indeks disalin sebagai snapshot beku dengan daftar id dan sidik jari isi -> set uji v2 dibangun
  dan diverifikasi terhadapnya. `evaluation.retriever_exactness` dijalankan juga pada kueri set
  uji v2; Recall dilaporkan dari retriever yang benar-benar dipakai dan dari pencarian eksak.
- **Aturan Wajib #6 ditambah** (CLAUDE.md): perbandingan Versi 1 dan Versi 2 pada kemampuan baru
  wajib memakai snapshot itu; angka asli Versi 1 (48/50, Recall@3 36/40, ablasi) tetap hanya lewat
  `archive/v1`.

### 5.2 Metrik retrieval dipisah dari metrik jawaban

- *Retrieval:* Recall@1/3/5 per tipe butir, peringkat artikel sasaran, dan keterbacaan klaim
  (utuh/terpotong).
- *Jawaban:* keputusan modus 3 run (verdict + `article_id`); kecocokan palsu, penolakan palsu,
  artikel salah, masing-masing dengan Wilson 95%; kesepakatan antar-run; pelanggaran format; URL di
  luar metadata -- sama dengan pra-registrasi Versi 1 (`v1.meta.json`, `evaluasi`).
- Butir tidak disaring berdasarkan hasil sistem.

### 5.3 Ablasi per komponen **[TIDAK BERLAKU LAGI]**

| Kondisi | Penanganan pesan panjang |
| --- | --- |
| K0 = Versi 1 (terkunci) | -- |
| K1 | pencarian per potongan (tanpa LLM) |
| K2 | ekstraksi LLM |

K1 vs K2 diputuskan lebih dulu pada tahap retrieval saja (V2-H3). Hanya kondisi yang terpilih
dilanjutkan ke tahap jawaban; yang kalah tidak dijalankan generatornya.

### 5.4 Kebersihan rujukan **[MASIH BERLAKU, sebagai metrik tambahan]**

Per jawaban "ditemukan" dihitung: rujukan yang melanggar `links.blocked_reason` (kebijakan
terkini), rujukan yang termasuk `claim_sources` artikel itu (termasuk baris "Sumber:"), jawaban
tanpa rujukan, dan rujukan yang lolos hanya karena daftar tepercaya atau `.go.id`. Diukur untuk
kedua versi pada indeks yang sama; deterministik, tanpa LLM. Pada `archive/v1` hasil yang
diharapkan sudah diketahui sebagian: metadata 36089 masih memuat satu tautan pemendek
(`v1_temuan_untuk_v2.md` bagian 9), jadi pada indeks itu metrik ini mengukur keadaan arsip, bukan
mutu Versi 2.

### 5.5 Juri

Tidak dipakai (keputusan 6). Metrik utama objektif; juri hanya relevan untuk mutu klarifikasi,
yang di luar cakupan. Sebagai catatan dasar keputusan: Gemma belum pernah diuji sebagai juri,
latensinya 31-52 detik per panggilan, dan RAGAS belum pernah dipasang (CLAUDE.md, "Hipotesis dan
status").

---

## 6. Set uji **[SEBAGIAN BERLAKU]**

### 6.1 Uji kemunduran: set uji v1 pada `archive/v1` **[MASIH BERLAKU]**

Dipakai apa adanya (54 butir beku; label sah pada arsip). Batas tafsirnya ada di bagian 4
(V2-H2). Tidak ada butir baru, tidak ada pelabelan.

### 6.2 Uji kemampuan baru: butir pesan panjang (set uji v2) **[TIDAK BERLAKU LAGI]**

Persyaratan, dikumpulkan dari catatan yang ada (`v1_temuan_untuk_v2.md` bagian 4, 5.2, 8, 9;
`v1.meta.json`; caveat laporan analisis; CLAUDE.md Aturan Wajib #5):

1. **Diberi versi bersama snapshot basis data**; hasil hanya sah pada snapshot itu. Dasar: enam
   butir negatif v1 gugur pada indeks yang lebih besar.
2. **Positif** dari Liputan6 Cek Fakta, hanya bila hoaksnya juga ada di basis data (artikel
   sasaran dipastikan manusia). **Negatif** dari arsip TurnBackHoax sebelum September 2025,
   **diverifikasi terhadap snapshot dengan top-3 retrieval**, bukan sekadar memeriksa keberadaan
   artikelnya. Butir dari situs cek fakta lain diperiksa ulang terhadap snapshot (bukti: `v1-050`).
3. **Pesan asli, tidak disunting panjangnya**, dengan posisi klaim apa adanya. Tidak ada
   pengganggu sintetis.
4. **Label final ditetapkan manusia**; pemakaian draf AI pada tahap mana pun dicatat (Aturan Wajib
   #5).
5. **Pemeriksaan data pribadi wajib** pada setiap teks (nomor, surel, akun, tautan), termasuk yang
   tertulis tanpa skema; pesan berantai lebih sering memuat nomor dan tautan daripada klaim
   pendek. Teks yang memuat kontak penipu tidak di-commit apa adanya.
6. **Confound sumber dicatat, tidak dapat dihindari:** positif seluruhnya dari Liputan6 dan negatif
   seluruhnya dari arsip TurnBackHoax, jadi tipe butir dan sumber tidak terpisah. Perbandingan
   kecocokan palsu vs penolakan palsu pada set ini wajib disertai catatan itu.
7. **Tidak boleh bocor** dari set uji v1 maupun set pengembangan.
8. Kepatuhan situs diperiksa ulang saat pengambilan (`robots.txt`), seperti pada v1.

### 6.3 Ukuran sampel **[TIDAK BERLAKU LAGI (hitungan baru di A4.a)]**

Sumber angka: `src/evaluation/sample_size.py` -> `testset/v2_ukuran_sampel.json` (rumus saja:
Wilson 95%, McNemar eksak dua sisi, binomial; uji `tests/test_sample_size.py`).

**(a) Mengapa set uji besar ditinggalkan.** Agar interval Wilson dua kondisi tidak tumpang tindih:
96% vs 99% butuh >= 413 butir per kondisi; 90% vs 96% butuh 276; 80% vs 95% butuh 68. Pada
perbandingan berpasangan, peluang 80% mengamati 6 perbaikan butuh 197 butir bila laju perbaikan
sejati 4% (kesalahan modus Versi 1: 2/50) dan 78 butir bila 10%. Jadi perbaikan akurasi pada klaim
pendek tidak dapat ditunjukkan dengan set yang sanggup dilabeli satu orang -- dan setelah cakupan
dipersempit, Versi 2 memang tidak mengklaimnya.

**(b) Berapa butir pesan panjang yang cukup.** V2-H1 terdukung bila ada >= 6 perbaikan bersih.
Laju perbaikan sejati = (bagian butir yang benar-benar terkena pemotongan) x (bagian yang
dipulihkan Versi 2). Butir positif yang dibutuhkan agar peluang mengamati >= 6 perbaikan mencapai
80%, tanpa kemunduran:

| Bagian butir yang terkena | dipulihkan 50% | dipulihkan 70% | dipulihkan 90% |
| --- | --- | --- | --- |
| 20% | 78 | 55 | 43 |
| 40% | 39 | 27 | 21 |
| 60% | 25 | 18 | 13 |
| 80% | 19 | 13 | 10 |
| 100% | 15 | 10 | 7 |

**Kedua faktor belum diketahui.** "Bagian yang terkena" adalah persis yang diukur di bagian 10;
"bagian yang dipulihkan" baru diketahui setelah komponen dibangun. Karena itu jumlah butir **tidak
dapat ditetapkan sekarang**. Yang dapat dikatakan: bila butir positif dipilih HANYA dari pesan
yang terbukti terkena (baris 100%), 15 butir cukup pada pemulihan 50% dan 10 pada 70%; bila
pengukuran menunjukkan pesan yang terkena sulit ditemukan, jumlah pesan yang harus disaring naik
sebanding.

**(c) Ketelitian yang didapat.** Batas bawah Wilson 95% bila semua butir benar: 0,722 (n = 10),
0,796 (15), 0,839 (20), 0,886 (30). Batas atas bila tidak ada kecocokan palsu pada butir negatif:
27,8% (10), 20,4% (15), 16,1% (20), 11,4% (30).

**(d) Usulan (ditetapkan setelah bagian 10):** 20 butir positif pesan panjang yang terkena + 20
butir negatif pesan panjang. Dengan 20 positif, V2-H1 berpeluang >= 80% terdukung bila Versi 2
memulihkan sedikitnya ~40% butir; dengan 20 negatif tanpa kecocokan palsu, batas atasnya 16%. Itu
40 butir baru (set uji v1: 54). Angka ini disesuaikan bila pengukuran bagian 10 mengubah
gambarannya.

### 6.4 Pedoman anotasi versi 1.1 (usulan tambahan; belum dikunci) **[TIDAK BERLAKU LAGI]**

**Koreksi atas premis:** pedoman v1.0 **sudah** memuat satu baris untuk kasus ini
(`testset/ANNOTATION_GUIDE.md`, bagian 4): *"Pesan berantai berisi beberapa klaim -- SAMA bila KIA
adalah salah satu klaim utamanya dan tidak dibantah pesan itu sendiri -- catat di `catatan`"*. Yang
belum diatur adalah cara menentukan "klaim utama" dan apa yang dilakukan bila pesan cocok dengan
lebih dari satu artikel. Versi 1.1 mengoperasionalkan baris itu; aturan lain tidak diubah.

Usulan teks tambahan:

1. **Klaim utama sebuah pesan** adalah klaim yang (i) dinyatakan pesan itu sebagai fakta -- bukan
   dikutip untuk dibantah atau dipertanyakan -- **dan** (ii) menjadi pokok yang diminta dipercaya,
   diwaspadai, atau disebarkan, atau ditonjolkan pesan itu sendiri (judul, pengulangan, huruf
   besar).
2. **SAMA** bila ketiga unsur inti KIA muncul lengkap pada satu klaim utama, dan klaim itu lolos
   uji dua arah serta uji Kesimpulan. Klaim lain di dalam pesan diperlakukan seperti unsur
   perifer: jumlahnya dan letak klaim utama di dalam pesan (awal, tengah, akhir) tidak mengubah
   keputusan.
3. **TIDAK SAMA** bila KIA hanya disinggung sebagai latar atau contoh (setara `sebagian_perifer`),
   atau bila pesan itu sendiri membantahnya.
4. **Cocok dengan lebih dari satu artikel basis data** (pesan memuat beberapa klaim utama yang
   masing-masing punya artikel): butir TIDAK dikeluarkan; semua artikel yang sah dicatat di
   `expected_alt`, dan jawaban dinilai benar bila memilih salah satunya. (v1.0 untuk kasus `ambigu`
   pada klaim pendek tetap berlaku.)
5. **Unsur perifer tambahan untuk pesan berantai:** sapaan, ajakan menyebarkan, doa atau sumpah,
   daftar penerima, tanda baca dan emoji berlebihan.
6. **Kolom baru per butir:** `jumlah_klaim_utama`, dan posisi klaim yang cocok (token awal dan
   akhir menurut tokenizer bge-m3; lihat bagian 10).

Yang perlu diputuskan pemilik proyek sebelum dikunci: definisi (ii) pada butir 1 bersifat
penilaian, dan dengan satu anotator konsistensinya tidak terukur.

---

## 7. Kendala nyata **[MASIH BERLAKU; hitungan panggilan diganti A8]**

### 7.1 Kuota LLM

Angka tercatat (`src/llm/limits.py`, dari AI Studio 2026-09-21): `gemini-3.5-flash-lite` RPM 15,
TPM 250.000, **RPD 500**. Tier gratis **dapat berubah tanpa pemberitahuan**; `gemini-3.8-flash`
pernah dihentikan karena ketidakstabilan layanan. Setiap permintaan yang dikirim dihitung, termasuk
yang ditolak; demo berbagi kuota yang sama. Versi 1 memakai 1 panggilan per kueri (evaluasi v1: 162
panggilan untuk 162 baris; rata-rata 2.516 token masuk; latensi rata-rata 10-18 detik).

Panggilan untuk evaluasi 3 run dengan cakupan sekarang:

| Bagian | Butir | Kondisi | Panggilan |
| --- | --- | --- | --- |
| Uji kemunduran (b), set uji v1 | 54 | Versi 2 saja (hasil Versi 1 sudah tercatat) | 162 |
| Uji kemampuan baru | 40 (usulan) | K0 + kondisi terpilih | 240 bila tanpa LLM; 240 + 3 x (jumlah butir terkena) bila ekstraksi LLM |
| Pemilihan K1 vs K2 (retrieval saja) | butir positif | K2 saja yang memanggil LLM | 1 x jumlah butir positif |

Totalnya sekitar **400-480 panggilan**, yaitu satu hari kuota bila demo tidak dipakai, dua hari
bila ingin aman. Token masuk untuk pesan panjang lebih besar daripada 2.516 (pesan utuh ikut
dikirim ke generator); besarnya belum diukur, tetapi TPM 250.000 pada RPM 15 memberi ruang ~16.000
token per panggilan.

Bagi pengguna demo: pencarian per potongan tidak menambah panggilan; ekstraksi LLM menambah satu
panggilan hanya untuk pesan yang terkena.

### 7.2 Memori

Laptop pengembangan: 15,7 GB RAM, memori bebas teramati 2,3-3,4 GB; memuat model embedding menekan
memori tersedia sampai ~0,9-1,0 GB (`data/pending_2026-10-03.log`). Proses pernah dihentikan
sistem karena memori rendah: ingest 2026-09-27 dan ablasi 2026-10-03 tercatat di CLAUDE.md (pemilik
proyek menyebut tiga kejadian). Konsekuensi: tidak ada model lokal tambahan; satu proses pemuat
model pada satu waktu; pencarian per potongan meng-embed beberapa jendela per pesan dengan model
yang sama (tanpa tambahan memori, hanya waktu); evaluasi dapat dilanjutkan antar-hari.

### 7.3 Lain-lain

Satu anotator; satu sumber data; `generator.py` terkunci; pembaruan berkala terus mengubah indeks
produksi (karena itu perlu snapshot); ingest hanya dimulai pemilik proyek; permintaan API key
Yudistira belum dijawab.

---

## 8. Di luar cakupan **[SEBAGIAN BERLAKU; baris verdict ketiga digantikan A1]**

| Hal | Alasan |
| --- | --- |
| Grader / node penilai relevansi | Keputusan 2: generator sudah menilai kesamaan klaim; tidak ada bukti untuk perbedaan yang dibawa grader; kuota terbatas |
| Penulis ulang kueri saat retrieval gagal (putaran "cari lagi") | Tidak ada bukti masalah: empat kegagalan Recall@3 semuanya butir negatif; positif 20/20 di semua indeks |
| "Mungkin terkait" dan verdict ketiga "artikel terkait" | Keputusan 3: perubahan produk, bukan perbaikan yang dijawab data; ambang skor terbukti gagal dan tidak ada bukti untuk penggantinya |
| Mutu / gaya bahasa klarifikasi | Keputusan 9: mengubah prompt mencampur efeknya dengan perbaikan pesan panjang |
| Menghapus Penjelasan dari indeks | Keputusan 10: mengubah indeks dan snapshot; tidak berkaitan dengan masalah yang dijawab |
| Penilaian kredibilitas dokumen hasil retrieval | Satu sumber data; tidak ada yang dinilai |
| Penilai kredibilitas rujukan per-URL oleh LLM | Tidak ada bukti solusi; LLM tidak dapat membuka tautan; daftar eksplisit lebih mudah diaudit |
| Mengganti top-k atau agregasi | Tidak dapat dibedakan dari kebetulan pada tiga indeks |
| Model embedding lain, batas token indeks lain, skema chunking lain | Butuh pembangunan ulang indeks dan memori; tidak ada temuan yang menuntutnya |
| Juri LLM (RAGAS + Gemma) | Keputusan 6 |
| LangGraph | Keputusan 4 |
| Set uji umum v2 berukuran besar (140 butir) | Keputusan 7 |
| Mengubah `archive/v1`, `v1.jsonl`, `generator.py` | Baseline |
| Integrasi API Yudistira, penjadwalan ingest | Tahap lain |

---

## 9. Yang masih terbuka **[TIDAK BERLAKU LAGI; diganti A10]**

1. **Hasil pengukuran bagian 10** -- menentukan apakah Versi 2 dilanjutkan dengan cakupan ini.
2. **Beban penandaan** (bagian 10.3) -- setelah sampel diukur: berapa pesan di atas 512 token dan
   berapa pesan Liputan6 yang dikonfirmasi; diperkecil dengan sampel acak bila terlalu banyak.
3. **Jumlah butir pesan panjang** (bagian 6.3 d) -- ditetapkan setelah pengukuran.
4. **Teks pedoman 1.1** (bagian 6.4) -- disetujui lalu dikunci sebelum pelabelan.
5. **Ambang hipotesis** (bagian 4) -- dikunci di `testset/v2.meta.json` sebelum pelabelan.
6. **Pengaruh pesan utuh pada generator** (bagian 3, butir 5): generator Versi 1 membaca seluruh
   pesan panjang; belum pernah diukur apakah penilaian "klaim sama"-nya tetap andal pada masukan
   sepanjang itu (set uji v1 tidak memuat pesan panjang).
7. **Batas masukan demo** (bagian 10.6) bila Versi 2 menangani pesan panjang.

---

## 10. Langkah pertama: apakah masalah pesan panjang terjadi pada pesan berantai asli? **[MASIH BERLAKU, sebagai bukti]**

Ditetapkan pemilik proyek. Bukti M1 berasal dari pengganggu sintetis yang sengaja menaruh klaim di
belakang separuh pengganggu. Belum diketahui apakah pesan berantai asli sering seperti itu. Bila
klaimnya hampir selalu di awal, Versi 1 sudah menanganinya (klaim di awal pesan: 19/20 pada ~5.000
karakter) dan Versi 2 memecahkan masalah yang jarang terjadi.

### 10.1 Yang diukur

1. Panjang tiap pesan dalam token bge-m3 (tokenizer yang sama dengan retrieval).
2. Posisi klaim inti relatif terhadap batas 512 token.
3. Persentase sampel yang benar-benar terkena masalah, menurut definisi mekanistik di 10.4.

### 10.2 Sampel (disetujui 2026-10-03)

Diambil **acak berbenih** (benih 20261003, dicatat sebelum pengambilan), bukan dipilih yang
kebetulan panjang. Alat: `python -m candidates.chain_sample` (keluaran lokal di
`data/candidates/pesan_berantai/`, tidak di-commit). `robots.txt` kedua situs diperiksa
2026-10-03: liputan6.com tidak melarang `/cek-fakta` (daftar larangan tidak memuatnya, tidak ada
aturan khusus agen AI); turnbackhoax.id `Disallow:` kosong.

- **Liputan6 Cek Fakta, 100 artikel kasus tunggal** ("Cek Fakta: ...") terbit 30 Sep 2025-27 Sep
  2026 (rentang basis data). Pencacahan lewat halaman indeks per tanggal
  (`/cek-fakta/indeks/YYYY/MM/DD`): 60 tanggal dipilih acak, lalu 100 artikel dipilih acak dari
  gabungannya; artikel yang tanggal terbitnya di luar rentang dibuang.
- **Arsip TurnBackHoax sebelum September 2025, 100 artikel** di luar basis data: 30 halaman daftar
  dipilih acak dari halaman 175-1.558, lalu sampai 4 artikel acak per halaman; artikel bertanggal
  1 September 2025 atau sesudahnya dibuang.
- **"Pesan"** = kutipan terpanjang di artikel (Liputan6: halaman pertama; TurnBackHoax: seksi
  Narasi, atau teks setelah kata "narasi" bila tidak dikutip). **Kelemahan yang dicatat:** kutipan
  diambil otomatis dari tanda kutip, sehingga pesan yang memuat tanda kutip di dalamnya bisa
  terpotong (panjangnya terukur lebih pendek dari aslinya), dan artikel cek fakta bisa saja hanya
  mengutip sebagian pesan berantai.

### 10.3 Metode (disetujui 2026-10-03 dengan dua perubahan dari pemilik proyek)

Tanpa LLM. Tiga bagian:

- **C -- uji kegagalan, sebagai definisi.** Untuk tiap pesan positif (artikel sasarannya
  terkonfirmasi), pesan dicari dengan cara Versi 1 (512 token pertama). Hasil pencarian per
  jendela atas seluruh pesan **boleh dilaporkan sebagai pengamatan, tetapi BUKAN bagian dari
  definisi**: pencarian per jendela adalah salah satu kandidat solusi Versi 2, dan mendefinisikan
  "terkena" sebagai "yang bisa ditemukannya" akan membuat solusi itu tampak memulihkan semua butir
  secara melingkar.
- **A -- penandaan manual oleh pemilik proyek**, tanpa bantuan AI: kalimat pembawa klaim inti
  ditandai pada pesan di atas 512 token; posisi tokennya dihitung dari tanda itu. Dipakai untuk
  memisahkan penyebab kegagalan: klaimnya memang di luar 512 token pertama, atau gagal karena hal
  lain.
- **B -- pencocokan kata dengan judul artikel cek fakta**, dihitung untuk semua pesan sebagai
  pembanding; yang dilaporkan adalah seberapa sering ia sepakat dengan A.

**Artikel sasaran pesan Liputan6 dikonfirmasi pemilik proyek, tanpa bantuan AI.** Daftar kandidat
yang disodorkan **tidak dicari memakai pesan panjangnya**: bila dicari dengan pesan itu, pada
pesan yang memang gagal dicari -- persis kasus yang ingin dihitung -- artikel yang benar tidak
muncul, butirnya tersisih, dan prevalensinya terukur terlalu rendah. Kandidat dicari dari **judul
artikel Liputan6** (pendek) ditambah **pencarian kata kunci pada judul 1.532 artikel**, dan selalu
ada pilihan **"tidak ada yang cocok"**.

Urutan yang ditetapkan: sampel diambil dan diukur panjangnya lebih dulu; jumlah pesan di atas 512
token dan jumlah pesan Liputan6 yang perlu dikonfirmasi dilaporkan; bila terlalu banyak untuk
dikerjakan dengan teliti, diperkecil dengan **sampel acak**, bukan dengan bantuan AI; baru
kemudian berkas penandaan disiapkan.

### 10.4 Definisi (mekanistik, bukan jumlah karakter)

- **Pesan panjang** = pesan yang melebihi 512 token bge-m3, sehingga sebagian isinya tidak ikut
  di-embed.
- **Pesan terkena** = pesan panjang yang artikel sasarannya **tidak masuk tiga besar saat dicari
  dengan cara Versi 1**. Definisi ini hanya dari sisi kegagalan.
- **Penyebab** dipisahkan dengan penandaan manual: (i) klaim inti berada di luar 512 token pertama
  (seluruhnya atau sebagian); (ii) klaim inti utuh di dalam 512 token pertama tetapi tetap gagal
  (sebab lain).

### 10.5 Pelaporan: setiap angka dengan penyebutnya

Tidak ada angka "prevalensi" tanpa penyebut. Yang dilaporkan, masing-masing dengan interval Wilson
95%:

1. pesan di atas 512 token **dari seluruh sampel** (per sumber, dan dari sampel yang punya kutipan
   pesan);
2. pesan yang klaim intinya berada di luar 512 token pertama **dari pesan panjang**;
3. kegagalan Versi 1 (artikel sasaran di luar tiga besar) **dari butir positif yang artikel
   sasarannya terkonfirmasi**, dipisah untuk pesan panjang dan pesan pendek;
4. berapa pesan yang harus disaring untuk mendapat satu butir yang terkena (masukan untuk 6.3).

Tidak ditetapkan angka ambang "jarang"; pemilik proyek melihat hasilnya lebih dulu, lalu
memutuskan apakah cakupan Versi 2 dipikir ulang.

### 10.6 Dua hal yang ikut dicatat (2026-10-03)

- **Generator Versi 1 tetap membaca seluruh pesan panjang.** `AnswerGenerator` menerima pesan utuh
  sebagai `claim` dan mengirimkannya ke LLM; hanya pencariannya yang terpotong. Pengaruh masukan
  sepanjang itu pada penilaian "klaim sama" **belum pernah diukur** (set uji v1 tidak memuat pesan
  panjang). Ini **wajib ikut dievaluasi**: pada butir pesan panjang, kegagalan pencarian dan
  kegagalan penilaian dilaporkan terpisah, termasuk untuk butir yang artikelnya sudah masuk tiga
  besar.
- **Demo menolak pesan di atas 1.500 karakter**, sedangkan 512 token setara kira-kira 2.300-3.000
  karakter menurut rasio yang terukur (335 token pada 1.500 karakter; 998 token pada 5.000
  karakter; `presentation.py` dan `v1_temuan_untuk_v2.md` bagian 4.2). Artinya pesan yang terkena
  pemotongan saat ini **tidak bisa dimasukkan ke demo sama sekali**: bagi pengguna demo masalahnya
  berbentuk "pesan ditolak", bukan "pesan dijawab keliru". Bila Versi 2 menangani pesan panjang,
  **batas masukan demo harus ikut dipikirkan ulang** (dan peringatan 220 token), dengan batas baru
  yang diukur, bukan ditebak -- batas 5.000 karakter dulu ditetapkan tanpa pengukuran.

### 10.7 Hasil pengukuran panjang (2026-10-03) -- langkah sebelum penandaan

Sumber: `testset/v2_pesan_berantai_ringkasan.json` (hitungan saja; teks pesan tetap lokal). 200
artikel diambil, 0 gagal, 0 dibuang karena tanggal.

| Sumber | Sampel | Punya kutipan pesan | Di atas 512 token | Wilson 95% (dari sampel) | Token median / p90 / maks |
| --- | --- | --- | --- | --- | --- |
| Liputan6 Cek Fakta (terbit 2 Okt 2025-23 Sep 2026) | 100 | 99 | **0** | [0; 3,7%] | 66 / 162 / 312 |
| Arsip TurnBackHoax (terbit 2 Jan 2022-24 Nov 2024) | 100 | 100 | **0** | [0; 3,7%] | 34 / 69 / 297 |

- **Tidak ada satu pun pesan panjang menurut definisi 10.4.** Akibatnya angka 2 dan 3 pada 10.5
  tidak dapat dihitung: penyebutnya (pesan panjang) nol.
- **Hasilnya tahan terhadap cara pengukuran.** Untuk Liputan6: kutipan terpanjang di SEMUA halaman
  artikel maks 331 token (0 di atas 512); seluruh kutipan halaman pertama digabung maks 397 token
  (0 di atas 512). Baru bila seluruh kutipan di semua halaman digabung -- termasuk kutipan
  narasumber di bagian penelusuran, yang bukan pesan hoaks -- ada 3 dari 100 di atas 512. Untuk
  arsip TurnBackHoax: seksi Narasi PENUH (termasuk kalimat pengantar redaksi) maks 300 token.
- **Yang TIDAK dapat disimpulkan dari sini.** Yang diukur adalah pesan *sebagaimana dikutip artikel
  cek fakta*: artikel bisa saja hanya mengutip sebagian pesan berantai, dan sebagian besar yang
  dikutip adalah unggahan media sosial, bukan pesan yang diteruskan lewat aplikasi percakapan.
  Seberapa panjang pesan yang benar-benar akan ditempel pengguna ke demo tetap **tidak diketahui**
  (tidak ada data pemakaian). Arsip TurnBackHoax yang tersampel berasal dari 2022-2024, bukan dari
  rentang basis data.
- **Konsekuensi untuk rancangan.** Dengan sumber yang ditetapkan (keputusan 8), butir pesan panjang
  yang "terkena" tidak dapat dibangun: di 200 pesan acak tidak ada satu pun kandidatnya. Batas atas
  Wilson 3,7% per sumber berarti perlu menyaring puluhan sampai ratusan artikel untuk menemukan satu
  pesan di atas 512 token, bila ada. Rancangan Versi 2 dengan cakupan "penanganan pesan panjang"
  karenanya **menunggu keputusan pemilik proyek** (aturan yang ditetapkan sebelumnya: bila masalahnya
  jarang, cakupan dipikir ulang). Berkas penandaan TIDAK disiapkan.

---

## 11. Arah yang sedang ditimbang: klaim yang dijawab "belum ditemukan" (pengukuran pendahuluan) **[MASIH BERLAKU, sebagai bukti]**

**Status 2026-10-04: hanya pengukuran; belum ada rancangan dan belum ada yang dibangun.** Setelah
hasil 10.7, pemilik proyek menimbang arah lain yang mungkin lebih bernilai daripada penanganan
pesan panjang: klaim yang saat ini dijawab "belum ditemukan". Sebelum merancang apa pun, besar
celahnya diukur dulu.

### 11.1 Pertanyaan

Dari klaim yang diperiksa situs cek fakta lain (Liputan6 Cek Fakta), berapa bagian yang **tidak**
diperiksa TurnBackHoax, yaitu tidak ada di basis data 1.532 artikel?

### 11.2 Ambang keputusan (ditetapkan pemilik proyek SEBELUM melihat data)

> **Kalau lebih dari separuh klaim Liputan6 yang sah tidak ada di basis data TurnBackHoax, tahap
> berikutnya layak dikerjakan.**

Dicatat di sini pada 2026-10-04, sebelum berkas konfirmasi dibuat dan sebelum pemilik proyek
membukanya. Operasionalisasi (usulan Claude Code, ikut dicatat sebelum data dilihat):

- **Ukuran:** butir berkeputusan "tidak ada yang cocok" dibagi **butir yang sah**. Butir yang sah =
  butir tersampel dikurangi yang dinyatakan pemilik proyek "bukan putusan hoaks".
- **Keputusan** dibaca dari proporsi teramati: di atas 50% -> layak dikerjakan; 50% atau kurang ->
  tidak.
- **Dilaporkan bersama interval Wilson 95%.** Pemilik proyek menyatakan sampel diperluas bila
  hasilnya ambigu.

**Dikonfirmasi pemilik proyek 2026-10-04, sebelum berkas konfirmasi dibuka:**

- Ambangnya memang **"lebih dari separuh"** (kurung siku pada rumusan awal adalah sisa templat,
  bukan angka yang masih terbuka).
- **Hasil dianggap jelas** bila interval Wilson 95%-nya **seluruhnya di atas atau seluruhnya di
  bawah 50%**; **ambigu** bila interval itu melintasi 50% (pada 50 butir sah kira-kira proporsi
  teramati antara 37% dan 63%; batas persisnya dihitung dari jumlah butir sah yang sebenarnya).
- **Bila ambigu, sampel diperluas ke 100 butir** (seluruh sampel Liputan6 yang sah), lalu aturan
  yang sama diterapkan pada hasil 100 butir itu.
- Akibatnya aturan "proporsi teramati di atas 50%" di atas hanya memutuskan bila hasilnya jelas;
  hasil ambigu tidak diputuskan dari 50 butir.

### 11.3 Sampel dan aturan (ditetapkan 2026-10-04)

- **50 butir** dipilih acak berbenih (benih 20261004) dari 100 artikel Liputan6 pada sampel 10.2,
  **setelah** artikel yang bukan putusan hoaks dikeluarkan.
- **Dikeluarkan: 1 artikel** -- "Cek Fakta: Klarifikasi Polri soal Deretan Kabupaten Siap ke Jakarta
  27 Agustus 2026": penanda vonis Liputan6 sendiri adalah "klarifikasi" (judul dan label
  banner), dan Kesimpulannya hanya menyatakan postingan itu "telah diklarifikasi", bukan bahwa
  klaimnya tidak benar. Aturan (`candidates.gap_review.is_non_hoax_verdict`): dikeluarkan bila judul
  berkata vonis "klarifikasi", atau banner berlabel "klarifikasi" sementara judul tanpa kata vonis
  salah/hoaks dan Kesimpulan tidak menyatakan klaimnya keliru. **Dua artikel yang penandanya tidak
  tegas TIDAK dikeluarkan otomatis:** "Tidak Benar Maladewa Putus Hubungan Diplomatik dengan Israel
  ..." (banner "Klarifikasi", tetapi judul dan Kesimpulan menyatakan "tidak benar") dan "Video Sri
  Mulyani Diperiksa Bareskrim Polri Ini Terjadi pada 2015" (tanpa kata vonis dan tanpa banner;
  Kesimpulan: "video lama pada 2015"). Berkas konfirmasi menyediakan pilihan "BUKAN PUTUSAN HOAKS"
  agar pemilik proyek yang memutuskan butir seperti itu.
- **Berkas yang dihasilkan (2026-10-04):** `data/candidates/celah_liputan6/konfirmasi_50.csv` -- 50
  butir, 326 baris kandidat (5-8 per butir, median 7); 2 butir di ujung rentang (terbit 18 dan 23
  September 2026); 3 butir memuat kandidat dari antrean (16 artikel antrean, terbit 27 Sep-2 Okt
  2026); kolom KEPUTUSAN kosong. Skor kemiripan disimpan terpisah (`kunci_kandidat.json`).
- **Kandidat** dicari dari JUDUL artikel Liputan6 (kata vonis di awal dibuang), bukan dari pesan:
  5 teratas pencarian embedding pada indeks 1.532 artikel + 3 teratas pencocokan kata kunci pada
  judul 1.532 artikel. Skor kemiripan TIDAK ditampilkan di berkas, dan kandidat diurutkan menurut
  tanggal, bukan menurut skor.
- **Efek ujung rentang.** TurnBackHoax bisa memeriksa hoaks yang sama beberapa hari setelah Liputan6
  (bukti: `v1-050`). Karena itu judul artikel dari **antrean pembaruan terjadwal** (belum di-ingest;
  termasuk yang terbit setelah 27 September 2026) ikut dijadikan kandidat lewat pencocokan kata kunci
  pada judul, dan butir Liputan6 yang terbit pada dua minggu terakhir rentang (14-27 September 2026)
  ditandai agar hasilnya dapat dibandingkan.
- **Kesamaan klaim ditentukan pemilik proyek sendiri dengan pedoman anotasi v1.0, tanpa bantuan AI.**
  Berkas disiapkan kode (kandidat dan tata letak); keputusan diisi manusia (Aturan Wajib #5).
- Berkas dan teksnya lokal (`data/candidates/celah_liputan6/`, tidak di-commit).
- **Versi `.xlsx` (2026-10-04, permintaan pemilik proyek; inilah yang diisi dan dibaca):**
  `konfirmasi_50.xlsx`, dibuat `python -m candidates.gap_workbook --make` dari `konfirmasi_50.csv`
  tanpa mengambil ulang sampel (326 baris, 50 butir; isi dibaca ulang identik dengan CSV). Teks
  dibungkus, baris judul dibekukan, lebar kolom diatur, Kesimpulan tetap paling kanan, semua sel
  bertipe teks, tanpa skor.
- **Asal-usul berkas (Aturan Wajib #5).** Berkas buatan `openpyxl` ber-*creator* kode, persis tanda
  yang dipakai untuk mendeteksi kejadian 2026-09-22. Karena itu: (1) *creator*-nya ditulis
  eksplisit "tata letak dihasilkan kode, KEPUTUSAN diisi manusia"; (2) sidik jari templat kosong
  disimpan saat dibuat (`sidik_jari_templat_xlsx.json`): KEPUTUSAN terisi 0, catatan terisi 0,
  sidik jari isi selain kolom manusia `501df3816f509baa...`, SHA-256 berkas `387147e2edc768f4...`;
  (3) pembacaan (`--read`) menolak menghitung bila sel selain KEPUTUSAN/catatan berbeda dari
  templat, dan melaporkan apakah berkas terakhir disimpan aplikasi lain (`lastModifiedBy`).
  Pemeriksaan ini membuktikan berkas disimpan lewat Excel, **bukan** siapa yang mengetik; yang
  terakhir tetap pernyataan pemilik proyek.
- **Pembacaan tidak menebak.** Keputusan dibaca dari baris pertama tiap butir. Sel kosong, tulisan
  di luar tiga pilihan, id di luar daftar kandidat, dan keputusan yang diketik di baris kandidat
  hanya dilaporkan untuk ditanyakan; hasil tidak dihitung sampai semuanya jelas.

### 11.4 Batas tafsir

- Mengukur celah terhadap SATU situs cek fakta lain pada artikel kasus tunggal ("Cek Fakta: ...");
  artikel rangkuman tidak tersampel. Ini bukan ukuran celah terhadap klaim yang diketik pengguna.
- **Label Liputan6** (100 artikel sampel; koreksi 2026-10-04 atas laporan awal yang menyebut "tanpa
  banner 62" -- pola pembacaan banner waktu itu keliru): halaman Kesimpulan memuat **banner
  berlabel**, yaitu "Cek Fakta: Salah" 58, "Hoax" 39, "Klarifikasi" 2, tanpa banner 1. Kata vonis di
  awal judul: "Tidak Benar" 57, "Hoaks" 40, "Klarifikasi" 1, tanpa 2. Keduanya hampir selalu
  berpasangan (judul "Tidak Benar" dengan banner "Salah" 55; judul "Hoaks" dengan banner "Hoax" 37),
  jadi Liputan6 membedakan setidaknya tiga label: Salah, Hoax, Klarifikasi. **Pemetaannya ke label
  TurnBackHoax (SALAH, PENIPUAN, PARODI, ...) tidak diasumsikan**; hanya dilaporkan dari pasangan
  yang dikonfirmasi.

### 11.5 Hasil 50 butir (2026-10-08)

Alat: `python -m candidates.gap_result --hasil` lalu `--kunci` (uji `tests/test_gap_result.py`).
Keluaran lokal, tidak di-commit: `hasil_konfirmasi.json`, `perbandingan_kunci.json`.

**Asal-usul label (Aturan Wajib #5; dicatat apa adanya menurut pernyataan pemilik proyek).**

- Keputusan diisi pemilik proyek. **Butir 1-5 dibahas bersama Claude** sebagai contoh cara mengisi;
  **butir 6-50 dikerjakan pemilik proyek sendiri tanpa bantuan AI.** Ini berbeda dari rencana di 11.3
  ("tanpa bantuan AI" untuk seluruh butir).
- **Setelah selesai, Claude memeriksa berkas terisi** dan menunjukkan dua aturan yang diterapkan
  tidak konsisten (lihat sensitivitas). Pemilik proyek **mempertahankan semua keputusan apa adanya**
  dan melaporkan inkonsistensinya sebagai keterbatasan; tidak ada label yang direvisi setelah data
  dilihat. Pembahasan dan pemeriksaan itu terjadi di luar sesi Claude Code yang menghitung hasil ini;
  tidak ada catatannya di repositori.
- **Berkas yang dihitung bukan `konfirmasi_50.xlsx` (templat kode pada 11.3)**, melainkan
  `konfirmasi_50_terisi.csv`: pemilik proyek mengisi versi `.xlsx` lain
  (`konfirmasi_50_rapi_terisi.xlsx`) lalu mengonversinya kembali ke CSV dan menyeragamkan penulisan
  "Tidak Ada" menjadi "TIDAK ADA". Akibatnya pemeriksaan sidik jari templat `.xlsx`
  (`gap_workbook --read`) **tidak dijalankan**; penggantinya adalah pembandingan CSV terisi dengan
  `konfirmasi_50.csv`. `konfirmasi_50.xlsx` dan `konfirmasi_50.csv` tidak ditimpa (KEPUTUSAN tetap
  kosong). SHA-256 berkas terisi `f8e8909e8ae67753...`.
- `kunci_kandidat.json` dibuka kode baru setelah hasil utama, sensitivitas, dan rincian tersimpan.
  Label Liputan6 untuk tabel silang didapat tanpa kunci (butir dipetakan ke artikel sampel lewat
  judul; pemetaannya kemudian terbukti sama dengan urutan di kunci).

**Validasi: lolos.** 50 butir, 326 baris; setiap KEPUTUSAN adalah id kandidat butirnya atau TIDAK
ADA; tidak ada keputusan di baris bukan-pertama; kolom selain KEPUTUSAN/catatan identik dengan
`konfirmasi_50.csv`. Kolom catatan (terisi 50/50) tidak di-parse.

**Hasil utama (aturan 11.2 diterapkan apa adanya).**

| | TIDAK ADA / butir sah | Proporsi | Wilson 95% | Kategori 11.2 |
| --- | --- | --- | --- | --- |
| Label utama | 29 / 50 | 58,0% | [44,2%; 70,6%] | **AMBIGU** (interval melintasi 50%) |

Proporsi teramati di atas separuh, tetapi menurut 11.2 hasil ambigu **tidak diputuskan dari 50
butir**: sampel diperluas ke 100 butir, lalu aturan yang sama diterapkan. Jadi 50 butir ini **belum
mendukung dan belum menolak** arah "belum ditemukan". BUKAN PUTUSAN HOAKS: **0 butir**, sehingga
penyebutnya tetap 50; butir 44 (Maladewa, banner "Klarifikasi") diperlakukan pemilik proyek sebagai
butir sah dan diputuskan TIDAK ADA.

**Sensitivitas -- EKSPLORATIF, tidak dipra-registrasi.** Pemilik proyek menyatakan dua aturan
diterapkan tidak konsisten: (1) *selisih waktu/gelombang* -- kandidat butir 2 ditolak karena
tahun/periodenya berbeda, tetapi butir 8, 14, 28, 49 diterima walau selisih waktunya lebih jauh
(8 dan 28 sama-sama dicocokkan ke 36654); (2) *detail yang tidak disebut di judul TurnBackHoax* --
ditolak di butir 15, 20, 21, 22, 25, 29, 32; diterima di butir 24, 39, 40, 48. Label utama tidak
diubah; yang dihitung hanya batasnya.

| Batas | Butir dibalik | TIDAK ADA / sah | Proporsi | Wilson 95% | Kategori 11.2 |
| --- | --- | --- | --- | --- | --- |
| Atas | 8, 14, 24, 28, 39, 40, 48, 49 -> TIDAK ADA | 37 / 50 | 74,0% | [60,5%; 84,1%] | jelas di atas 50% |
| Bawah | 15, 20, 21, 22, 25, 29, 32 -> cocok | 22 / 50 | 44,0% | [31,2%; 57,7%] | ambigu |

**Kategori keputusan TIDAK sama di kedua batas: kesimpulan bergantung pada aturan pelabelan.**
Dengan aturan ketat hasilnya menjadi "layak dikerjakan"; dengan aturan longgar tetap ambigu dengan
proporsi teramati di bawah separuh. Pada tidak satu pun batas hasilnya "jelas di bawah 50%". Lima
belas dari 50 butir (30%) berada di daftar meragukan, lebih lebar daripada jarak hasil utama ke
ambang (4 butir).

**Rincian pendukung.**

- *Ujung rentang (n = 2; tidak ditarik kesimpulan):* butir 3 (18 Sep 2026) cocok dengan 36776;
  butir 21 (23 Sep 2026) TIDAK ADA.
- *Label banner Liputan6 pada 50 butir:* salah 26, hoax 22, hoaks 1 (ejaan banner apa adanya),
  klarifikasi 1. Pada 29 butir TIDAK ADA: salah 15, hoax 12, hoaks 1, klarifikasi 1.
- *Tabel silang, hanya 21 pasangan yang dikonfirmasi cocok:*

  | Banner Liputan6 | SALAH | PENIPUAN | PARODI | SATIR | Jumlah |
  | --- | --- | --- | --- | --- | --- |
  | salah | 3 | 7 | 1 | 0 | 11 |
  | hoax | 5 | 4 | 0 | 1 | 10 |

  Kedua label Liputan6 berpasangan dengan SALAH maupun PENIPUAN; pada 21 pasangan ini tidak tampak
  pemetaan satu-ke-satu (n kecil; tidak diuji).
- *Waktu terbit artikel TurnBackHoax terhadap artikel Liputan6 (21 pasangan):* sebelum 7, hari yang
  sama 1, sesudah 13. Tidak ada pasangan dari antrean (semua dari indeks). Di antara "sesudah" ada
  butir 28 (selisih ~11 bulan), butir 8 (~8 bulan), dan butir 49 (~5 bulan) -- ketiganya di daftar
  meragukan; 36654 dipilih dua kali.

**Keputusan vs pencarian otomatis (kunci dibuka setelah semua di atas tersimpan; TIDAK dipakai
untuk mengubah label).**

- Dari 21 pasangan cocok, id pilihan pemilik proyek adalah kandidat **teratas pencarian embedding
  pada 18** (ada di 5 teratas: 20) dan **teratas pencocokan kata kunci judul pada 20** (ada di 3
  teratas: 21). Teratas di keduanya: 18. Bukan teratas di keduanya: butir 3 (36776: di luar 5
  teratas embedding, peringkat 2 kata kunci). Embedding peringkat 2: butir 31 dan 49.
- **Skor tidak memisahkan cocok dari tidak cocok.** Skor embedding pilihan: 0,5733-0,7831 (median
  0,6903). Skor kandidat teratas pada 29 butir TIDAK ADA: 0,4833-0,7294 (median 0,6270); **22 dari
  29 berada di atas skor pilihan terendah.** Dua butir TIDAK ADA di atas median pilihan: butir 10
  (0,7294) dan butir 20 (0,7271).
- Butir TIDAK ADA dengan tumpang tindih kata kunci judul tertinggi: 21 (0,75), 20 (0,67), 15 (0,60),
  22 (0,50) -- keempatnya juga ada di daftar "ditolak secara meragukan". Ini pengamatan, bukan dasar
  untuk membalik label.
- Tafsir yang sah: bila ada pasangan, kandidat teratas hampir selalu pasangan itu; tetapi kandidat
  teratas selalu ada juga saat tidak ada pasangan, dan skornya tidak membedakan kedua keadaan
  (sejalan dengan temuan Versi 1). Catatan: kandidat hanya berasal dari kedua pencarian ini, jadi
  pasangan yang luput dari keduanya tidak mungkin dipilih -- angka di atas adalah kesepakatan
  **dengan syarat** pasangannya ada di daftar, bukan recall.

**Keterbatasan.**

- **Satu anotator**; kesepakatan antar-anotator tidak terukur.
- **Butir 1-5 dibahas bersama AI** (3 di antaranya cocok, 2 TIDAK ADA), dan berkas terisi diperiksa
  AI sebelum dihitung (tanpa revisi label).
- **Dua aturan diterapkan tidak konsisten** pada 15 butir, dan kategori keputusan berubah di batas
  atas. Daftar butir meragukan disusun setelah pelabelan, jadi sensitivitasnya eksploratif.
- **Perbandingan hanya berbasis judul dan Kesimpulan** artikel TurnBackHoax (Narasi tidak
  ditampilkan), dan kandidat dicari dari judul Liputan6.
- Pemeriksaan sidik jari templat `.xlsx` tidak berlaku untuk berkas yang dipakai (lihat asal-usul).
- Batas tafsir 11.4 tetap berlaku (satu situs pembanding; bukan klaim yang diketik pengguna).

**Langkah berikutnya (menurut 11.2 dan keputusan pemilik proyek 2026-10-08).** Sampel diperluas ke
100 butir. **Berkas 50 butir berikutnya BELUM dibuat:** dua aturan pelabelan tertulis (selisih
waktu/gelombang tautan penipuan; detail tidak disebut vs detail bertentangan) dikunci pemilik proyek
lebih dulu, sebelum data baru dilihat. Aturan itu hanya berlaku untuk butir baru; 50 butir di atas
tidak dilabel ulang.

### 11.6 Aturan untuk perluasan ke 99 butir (DIKUNCI pemilik proyek 2026-10-09, sebelum berkas butir baru dibuat)

Dikunci setelah hasil 50 butir pertama dilihat (11.5) dan **sebelum** berkas konfirmasi butir baru
dibuat, kandidatnya dicari, atau kuncinya ada. Berlaku **hanya untuk butir baru**; 50 butir lama
tidak dilabel ulang.

**Jumlah butir (dipastikan dari berkas sampel, bukan diasumsikan).** `sampel_liputan6.jsonl`: 100
artikel, 100 id unik; 1 dikeluarkan aturan `is_non_hoax_verdict` (11.3); 99 sah. Pengambilan
berbenih 20261004 direproduksi dan sama persis dengan 50 butir yang sudah dikonfirmasi; **sisanya 49
butir**. Total setelah perluasan: **99**, bukan 100 seperti tertulis di 11.2.

**Aturan A -- selisih waktu atau gelombang.** Unsur inti (subjek, tindakan, objek pembeda)
menentukan; **tanggal terbit tidak**. Untuk tautan penipuan berulang, lembaga dan jenis tawaran yang
sama berarti cocok walaupun gelombangnya berbeda. Tahun atau periode hanya menjadi pembeda bila
**disebut eksplisit di kedua sisi dan berbeda**.
*Keterbatasan yang diterima:* pada penipuan tahunan, tahun di judul sering hanya penanda gelombang,
sehingga aturan ini bisa memisahkan dua artikel yang sebenarnya gelombang dari penipuan yang sama.
Aturan ini dipilih karena **objektif**, bukan karena pasti benar.

**Aturan B -- detail tidak disebut versus detail bertentangan.** Detail yang tidak disebut **bukan**
alasan menolak; hanya detail yang **bertentangan pada unsur inti** yang menjadi alasan menolak.
Pembandingnya adalah **kutipan pesan Liputan6 dengan Narasi TurnBackHoax**, bukan hanya judul dan
Kesimpulan. Butir baru boleh ditandai ragu **hanya setelah Narasinya dibaca**. Tanda ragu disimpan
di kolom tersendiri `ragu` (`YA` atau kosong), bukan di catatan.

**Sensitivitas butir baru (ditetapkan di muka).** Dua arah: semua butir bertanda ragu dihitung
cocok (batas bawah proporsi TIDAK ADA), dan semua butir bertanda ragu dihitung TIDAK ADA (batas
atas). Label utama tidak diubah.

**Aturan berhenti.** Bila pada 99 butir interval Wilson 95% **masih mencakup 50%**, sampling
dihentikan dan **ambang dinyatakan tidak terpenuhi**: sumber kedua tidak diprioritaskan sekarang.
**Tidak ada perluasan ketiga.** Bila interval seluruhnya di atas 50%: layak dikerjakan; seluruhnya di
bawah 50%: tidak.

**Pelaporan.**

- **Hasil utama = 99 butir gabungan** (50 lama + 49 baru), sesuai pra-registrasi 11.2; butir BUKAN
  PUTUSAN HOAKS keluar dari penyebut.
- **Hasil sekunder = 49 butir baru saja**, yang dilabel dengan aturan terkunci di atas.
- Sensitivitas 50 butir lama tetap memakai batas 11.5 (37/50 dan 22/50); tidak dihitung ulang.
  Operasionalisasi untuk gabungan (usulan Claude Code, dicatat sebelum data baru ada; eksploratif):
  batas atas gabungan = batas atas lama + batas atas baru, begitu juga batas bawah.

**Berkas konfirmasi butir baru (rancangan; dibuat setelah bagian ini di-push).**

- Tata letak **blok per butir**: judul dan kutipan pesan Liputan6 di atas; sel masukan KEPUTUSAN,
  ragu, catatan; lalu tabel kandidat berkolom id, tanggal, label, asal, judul, **Narasi TurnBackHoax
  utuh**, Kesimpulan. Kandidat tanpa Narasi ditandai dan jumlahnya dilaporkan.
- Masukan **hanya** di sel blok. Lembar Rekap berisi rumus saja dan diproteksi (tanpa kata sandi):
  pada 50 butir pertama pemilik proyek sempat mengetik di lembar rekap karena tidak ada yang
  mencegahnya.
- Pembaca mengambil keputusan dari sel blok, menolak berkas yang kolom buktinya berubah dari
  templat, dan menyeragamkan huruf besar-kecil (`Tidak Ada` -> `TIDAK ADA`); selain itu tidak
  menafsirkan apa pun.
- Kandidat dicari dengan cara yang sama (11.3: dari judul Liputan6; 5 teratas embedding + 3 teratas
  kata kunci judul), diurutkan menurut tanggal, tanpa skor; kunci skor disimpan terpisah dan tidak
  dibuka sampai pemilik proyek selesai.

**Perbedaan antara 50 butir lama dan 49 butir baru yang ikut membatasi hasil gabungan** (dicatat di
muka): (1) aturan pelabelan berbeda (lama: pedoman v1.0 dengan dua inkonsistensi; baru: Aturan A dan
B); (2) bukti yang dilihat berbeda (lama: judul dan Kesimpulan; baru: juga Narasi utuh); (3) antrean
yang ikut dijadikan kandidat berbeda (lama: 16 artikel; baru: antrean pada saat berkas dibuat).

**Berkas dibuat 2026-10-09, setelah aturan di atas di-push (commit `c347e20`).**
`python -m candidates.gap_blocks --make` -> `konfirmasi_49.xlsx` (lokal, tidak di-commit): **49
butir**, 319 baris kandidat (5-8 per butir, median 7), 1 butir ujung rentang, antrean 32 artikel (6
butir memuat kandidat dari antrean), **kandidat tanpa Narasi: 0**, sel masukan terisi saat dibuat: 0.
Sidik jari bukti `932e756ae3a87d21...`; peta blok dan sidik jari di `sidik_jari_templat_49.json`;
skor di `kunci_kandidat_49.json` (ditulis, tidak dibaca alat ini). Lembar konfirmasi dan Rekap
diproteksi tanpa kata sandi; yang tidak terkunci hanya sel KEPUTUSAN, ragu, dan catatan di tiap blok
(proteksi lembar konfirmasi adalah tambahan Claude Code agar masukan memang hanya bisa di sel blok;
lebar kolom dan tinggi baris tetap bisa diubah). Pembacaan: `python -m candidates.gap_blocks --read`
(uji `tests/test_gap_blocks.py`); pada templat kosong ia menolak menghitung (49 butir kosong).
Isi berkas tidak dibuka atau diringkas Claude Code.

### 11.7 Selisih hari terbit pada 21 pasangan cocok (EKSPLORATIF; dari 50 butir pertama)

Selisih = tanggal terbit TurnBackHoax dikurangi tanggal terbit Liputan6 (positif = TurnBackHoax
belakangan). Hanya untuk menimbang apakah cakupan *saat hoaks beredar* perlu diukur terpisah nanti;
bukan dasar keputusan sekarang.

- Bertanda: minimum -197, kuartil bawah -5, **median +3**, kuartil atas +6, maksimum +323 hari.
- Nilai mutlak: kuartil bawah 3, median 6, kuartil atas 36 hari. **Dalam 14 hari: 15 dari 21;
  di atas 30 hari: 6 dari 21.**
- 13 pasangan "sesudah": **10 terpaut 1-14 hari** (1, 2, 3, 3, 4, 4, 5, 6, 8, 14) dan 3 terpaut jauh
  (159, 248, 323 hari: butir 49, 8, 28). 7 pasangan "sebelum": 4 terpaut 3-9 hari, 3 terpaut jauh
  (36, 42, 197 hari: butir 42, 48, 14). Satu pasangan terbit di hari yang sama.
- Jadi sebagian besar pasangan "sesudah" adalah TurnBackHoax terlambat beberapa hari, bukan
  gelombang lain. Lima dari enam pasangan yang terpaut lebih dari 30 hari ada di daftar "diterima
  secara meragukan" (8, 14, 28, 48, 49); yang keenam butir 42.
- Batas: n = 21, satu anotator, dan tanggal yang dibandingkan adalah tanggal terbit artikel cek
  fakta, bukan tanggal hoaks beredar.

### 11.8 Hasil 99 butir (2026-10-13): ambang TIDAK terpenuhi, sampling dihentikan

Alat: `python -m candidates.gap_blocks --read` (bawaan membaca `konfirmasi_49_terisi.xlsx`; uji
`tests/test_gap_blocks.py`). Keluaran lokal, tidak di-commit: `hasil_konfirmasi_49.json`. Bagian ini
(langkah 1-6) di-commit **sebelum** `kunci_kandidat_49.json` dibuka; perbandingan dengan kunci ada di
11.9.

**Asal-usul label (Aturan Wajib #5; dicatat apa adanya menurut pernyataan pemilik proyek).**

- Ke-49 butir dilabel pemilik proyek sendiri, tanpa bantuan AI, dengan Aturan A dan B (11.6).
- Claude (di luar sesi Claude Code yang menghitung hasil ini) **tidak membahas satu butir pun**.
  Bantuannya hanya teknis: cara keluar dari Protected View, letak sel isian, penjelasan umum Aturan
  A/B, dan pola penulisan catatan dengan contoh rekaan yang tidak diambil dari data.
- **Satu perubahan pada berkas oleh Claude:** templat menampilkan baris kandidat setinggi satu
  baris sehingga Narasi terpotong di layar, jadi tinggi baris diperbesar lewat openpyxl. Menurut
  pemilik proyek, isi sel, proteksi, sel terbuka, dan sel gabungan sudah dicek identik dengan
  templat. Diperiksa ulang di sesi ini pada berkas terisi: proteksi kedua lembar aktif; sel tak
  terkunci = tepat 245 sel masukan (49 blok x KEPUTUSAN, ragu, dan sel catatan gabungan F-H); 147
  sel gabungan sama dengan yang dibuat kode; tinggi baris kandidat 43,5-409,5 poin. Satu jejak kecil
  perubahan itu: *creator* berkas terisi kehilangan satu spasi (`openpyxl;tata letak ...`, templat
  `openpyxl; tata letak ...`).
- **Cacat alat yang diperbaiki:** `gap_blocks.write_workbook` dulu tidak menyetel tinggi baris
  kandidat. Kini disetel dari panjang teks dan lebar kolom (`wrapped_height`), dibatasi 409 poin
  (batas Excel; Narasi yang sangat panjang tetap terpotong di layar, isi sel utuh). Hanya berlaku
  untuk berkas yang dibuat kemudian; berkas 49 butir tidak dibuat ulang.
- **Templat tidak lagi kosong.** `konfirmasi_49.xlsx` disimpan Excel pada 2026-10-13 23.28 WIB
  dengan 45 KEPUTUSAN terisi (butir 2, 14, 18, 30 kosong) dan SHA-256-nya tidak lagi sama dengan
  sidik jari templat (`5c4ba627...` -> `d2a73ac6...`). Pembacaan pertama sesi ini (berkas terisi
  belum ada) berhenti dan melaporkannya; pemilik proyek lalu mengisi keempat butir dan menyimpan
  `konfirmasi_49_terisi.xlsx` (23.42 WIB), yang dihitung di sini. Bukti tidak terdampak: sidik
  jari sel bukti kedua berkas sama dengan templat (`932e756a...`).

**Langkah 1 -- validasi: lolos.** `konfirmasi_49_terisi.xlsx` (SHA-256 `b99e5bfef83e500b...`,
terakhir disimpan Microsoft Excel). Sidik jari seluruh sel selain KEPUTUSAN/ragu/catatan **sama**
dengan templat, jadi pemeriksaan tidak perlu dan tidak dilonggarkan: ia membandingkan nilai sel,
bukan format (tinggi baris tidak ikut). 49/49 KEPUTUSAN terisi dan sah (25 id kandidat butirnya, 24
TIDAK ADA, 0 BUKAN PUTUSAN HOAKS); kolom ragu hanya YA (butir 2, 14, 18, 30) atau kosong; catatan
terisi 46/49 (tidak di-parse).

**Langkah 2 -- hasil utama (11.2 dan 11.6 diterapkan apa adanya).**

| | TIDAK ADA / butir sah | Proporsi | Wilson 95% | Kategori |
| --- | --- | --- | --- | --- |
| **Gabungan 99 butir** | **53 / 99** | **53,5%** | **[43,8%; 63,0%]** | **AMBIGU** (interval mencakup 50%) |

BUKAN PUTUSAN HOAKS: 0 pada putaran lama dan 0 pada putaran baru, jadi penyebutnya 99. Menurut
aturan berhenti 11.6: **sampling selesai dan ambang dinyatakan TIDAK terpenuhi**; sumber kedua tidak
diprioritaskan sekarang. Proporsi teramati di atas separuh, tetapi ambang 11.2 menuntut interval
yang seluruhnya di atas 50%, dan itu tidak tercapai.

**Langkah 3 -- hasil sekunder dan sensitivitas (EKSPLORATIF selain baris "utama").**

| | TIDAK ADA / sah | Proporsi | Wilson 95% | Kategori |
| --- | --- | --- | --- | --- |
| 49 butir baru, label utama | 24 / 49 | 49,0% | [35,6%; 62,5%] | ambigu |
| Baru, butir ragu dihitung TIDAK ADA (butir 18 dibalik) | 25 / 49 | 51,0% | [37,5%; 64,4%] | ambigu |
| Baru, butir ragu dihitung cocok (butir 2, 14, 30 dibalik) | 21 / 49 | 42,9% | [30,0%; 56,7%] | ambigu |
| Gabungan, batas atas (37/50 + 25/49) | 62 / 99 | 62,6% | [52,8%; 71,5%] | **jelas di atas 50%** |
| Gabungan, batas bawah (22/50 + 21/49) | 43 / 99 | 43,4% | [34,1%; 53,3%] | ambigu |

**Kategori TIDAK sama di semua batas:** semuanya ambigu kecuali batas atas gabungan, yang jelas di
atas 50%. Batas atas itu sepenuhnya digerakkan oleh batas atas 50 butir lama (37/50; butir baru
hanya menambah satu). Pada putaran baru sendiri, keempat butir ragu tidak mengubah kategori.

**Langkah 4 -- dua putaran berdampingan (DESKRIPTIF, tanpa uji signifikansi).**

| Putaran | TIDAK ADA / sah | Proporsi | Wilson 95% |
| --- | --- | --- | --- |
| 50 butir pertama (11.5) | 29 / 50 | 58,0% | [44,2%; 70,6%] |
| 49 butir sisa | 24 / 49 | 49,0% | [35,6%; 62,5%] |

Selisih 9 poin persentase tidak diuji dan tidak ditafsirkan sebagai perbedaan populasi: ia tidak
dapat dipisahkan dari tiga perbedaan yang dicatat di muka pada 11.6 (aturan pelabelan, bukti yang
dilihat -- kini dengan Narasi utuh --, dan isi antrean kandidat).

**Langkah 5 -- rincian pendukung.**

- *BUKAN PUTUSAN HOAKS:* 0 butir (tidak ada alasan untuk dilaporkan).
- *Banner Liputan6 pada 49 butir baru:* salah 32, hoax 16, tanpa banner 1. Pada 24 butir TIDAK ADA:
  salah 15, hoax 8, tanpa banner 1.
- *Tabel silang banner Liputan6 x label TurnBackHoax, pasangan cocok:*

  | Banner Liputan6 | Pasangan | SALAH | PENIPUAN | PARODI | SATIR | Jumlah |
  | --- | --- | --- | --- | --- | --- | --- |
  | salah | baru (25) | 1 | 16 | 0 | 0 | 17 |
  | hoax | baru (25) | 3 | 5 | 0 | 0 | 8 |
  | salah | gabungan (46) | 4 | 23 | 1 | 0 | 28 |
  | hoax | gabungan (46) | 8 | 9 | 0 | 1 | 18 |

  Seperti pada 11.5, kedua label Liputan6 berpasangan dengan SALAH maupun PENIPUAN; tidak tampak
  pemetaan satu-ke-satu (tidak diuji). Pasangan baru didominasi PENIPUAN (21 dari 25; putaran lama
  11 dari 21).
- *Selisih hari terbit pasangan baru (TurnBackHoax dikurangi Liputan6; kuartil metode inklusif, sama
  dengan 11.7 -- diperiksa: metode ini memberi ulang angka 11.7 pada 21 pasangan lama):* bertanda
  min -212, kuartil bawah -134, **median -16**, kuartil atas +7, maks +95; mutlak kuartil bawah 7,
  **median 38**, kuartil atas 134 hari. Dalam 14 hari: 9 dari 25; **di atas 30 hari: 14 dari 25**
  (putaran lama: 6 dari 21). TurnBackHoax terbit sebelum Liputan6 pada 15 pasangan, sesudah pada 10.
  **Ke-14 pasangan yang terpaut lebih dari 30 hari semuanya PENIPUAN** -- sejalan dengan Aturan A
  (lembaga dan jenis tawaran sama = cocok walau gelombangnya berbeda). Artinya pada pasangan itu
  artikel TurnBackHoax membantah klaim yang sama dari gelombang sebelumnya/sesudahnya, bukan
  unggahan yang sama.
- *Pasangan yang artikel TurnBackHoax-nya hanya ada di antrean (belum di-ingest): 0 dari 25.*
  Seluruh 25 artikel pilihan ada di `data/articles.json` (1.532 artikel) dan indeks produksi. Enam
  butir memuat kandidat dari antrean (butir 3, 7, 17, 27, 28, 49); tidak satu pun kandidat antrean
  dipilih (butir 7 dan 28 cocok dengan artikel indeks; empat lainnya TIDAK ADA). Putaran lama juga
  0. Jadi pada 99 butir **tidak ada** pasangan yang ada di TurnBackHoax tetapi belum terjangkau
  sistem karena belum di-ingest.
- *Ujung rentang (n = 1, tanpa kesimpulan):* butir 49 TIDAK ADA.
- Tidak ada artikel TurnBackHoax yang dipilih dua kali pada putaran baru, dan tidak ada yang juga
  dipilih pada putaran lama.

**Langkah 6 -- catatan interpretasi (keterbatasan; kualitatif, tanpa melabel ulang).** 50 butir lama
dilabel dengan aturan yang berbeda dan, dalam satu hal, lebih ketat daripada aturan yang kini
dikunci. Arah pergeserannya, dinilai hanya dari uraian 11.5 (butirnya tidak dilihat ulang). **Semua
penilaian di butir-butir berikut adalah pembacaan agent (Claude Code) atas uraian itu, bukan label,
dan tidak mengubah hasil** (rumusan dirapikan 2026-10-17 atas permintaan pemilik proyek):

- *Diterima secara meragukan (8 butir: 8, 14, 24, 28, 39, 40, 48, 49).* Alasan keraguan 11.5 adalah
  selisih waktu yang jauh (8, 14, 28, 49; juga 48 menurut 11.7) atau detail yang tidak disebut
  judul TurnBackHoax (24, 39, 40, 48). Di bawah Aturan A dan B keduanya **bukan** alasan menolak,
  jadi penerimaan itu, **menurut pembacaan agent, konsisten dengan Aturan A/B; ini bukan label dan
  tidak mengubah hasil**. Bila pembacaan itu benar, batas atas lama (37/50), yang membalik kedelapan
  butir ini menjadi TIDAK ADA, kurang didukung aturan terkunci, padahal hanya batas itulah yang
  membuat gabungan "jelas di atas 50%". Sebagai ilustrasi aritmetika saja: tanpa
  empat butir selisih-waktu itu, batas atas gabungan menjadi 58/99 = 58,6% [48,7%; 67,8%] -- ambigu.
- *Ditolak secara meragukan (7 butir: 15, 20, 21, 22, 25, 29, 32)* karena detail "tidak disebut".
  Di bawah Aturan B itu bukan alasan menolak; sebagian bisa menjadi cocok, sebagian tetap ditolak
  bila Narasi (yang dulu tidak ditampilkan) memuat detail yang bertentangan. Jumlahnya tidak
  diketahui tanpa melabel ulang. Butir 2 (ditolak karena tahun/periode) hanya tetap ditolak bila
  tahunnya eksplisit dan berbeda di kedua sisi.
- *Arah bersih (pembacaan agent, bukan label):* bila aturan terkunci diterapkan seragam, TIDAK ADA pada 50 butir lama kemungkinan
  **berkurang atau tetap**, tidak bertambah. Jadi 53/99 kemungkinan **melebih-lebihkan** proporsi
  TIDAK ADA relatif terhadap aturan terkunci; dengan label utama butir baru, nilai seragamnya berada
  antara 46/99 (46,5% [37,0%; 56,2%], bila ketujuh butir menjadi cocok) dan 53/99.
  Pergeseran itu menjauh dari ambang, bukan mendekatinya, sehingga tidak mengubah kesimpulan
  "ambang tidak terpenuhi". Yang tidak dapat dinilai: arah pengaruh Narasi pada butir lama (bisa
  menambah maupun mengurangi kecocokan).
- Keterbatasan lain tetap berlaku: satu anotator, 1-5 butir lama dibahas bersama AI (11.5), kandidat
  hanya dari dua cara pencarian berbasis judul (pasangan yang luput dari keduanya tidak mungkin
  dipilih, jadi TIDAK ADA bisa sedikit melebih-lebihkan celah), dan batas tafsir 11.4.

### 11.9 Keputusan 49 butir baru vs pencarian otomatis (kunci dibuka 2026-10-17, setelah 11.8 di-commit `d6add92`)

`python -m candidates.gap_blocks --kunci` -> `perbandingan_kunci_49.json` (lokal). Fungsinya sama
dengan putaran pertama (`gap_result.compare_with_key`); urutan butir di kunci diperiksa sama dengan
peta blok templat. **Hanya untuk menilai pencarian otomatis; TIDAK dipakai untuk mengubah label.**

| Ukuran (pasangan cocok) | Putaran 1 (21) | Putaran 2 (25) |
| --- | --- | --- |
| Pilihan = teratas embedding | 18 | 17 |
| Pilihan di 5 teratas embedding | 20 | 25 |
| Pilihan = teratas kata kunci judul | 20 | 18 |
| Pilihan di 3 teratas kata kunci | 21 | 24 |
| Teratas di keduanya | 18 | 15 |
| Skor embedding pilihan, min / median / maks | 0,5733 / 0,6903 / 0,7831 | 0,5879 / 0,7046 / 0,7663 |

- Bukan teratas di keduanya: butir 1 (embedding peringkat 5, kata kunci 3), 4 (2, di luar 3 teratas
  kata kunci), 34, 42, 46 (embedding peringkat 2). Butir ragu yang cocok (18) teratas di keduanya.
- **Skor tetap tidak memisahkan cocok dari tidak cocok.** Skor embedding teratas pada 24 butir TIDAK
  ADA: 0,5850 / 0,6400 / 0,7582 (min / median / maks); **23 dari 24 di atas skor pilihan terendah**
  (putaran 1: 22 dari 29). Di atas median pilihan (0,7046): butir 8 (0,7582), 41 (0,7509), 17
  (0,7393), 30 (0,7083; butir ragu).
- Tumpang tindih kata kunci judul tertinggi pada butir TIDAK ADA: butir 2 (1,00; butir ragu), 8
  (0,90), 33 (0,71), 17 (0,56). Butir 8 dan 17 tinggi di kedua cara. Pengamatan, bukan dasar untuk
  membalik label: pada putaran ini pembanding manusia adalah Narasi utuh, sedangkan skor hanya
  membaca judul.
- Tafsir sama dengan 11.5: bila ada pasangan, ia hampir selalu ada di daftar dan sering teratas;
  kandidat berskor tinggi selalu ada juga saat tidak ada pasangan. Kesepakatan ini bersyarat pada
  pasangan ada di daftar, bukan recall.

### 11.10 Implikasi (ditulis 2026-10-17, setelah angka 11.8-11.9 keluar)

**Ambang yang ditetapkan sebelum data dilihat tidak terpenuhi:** pada 99 butir, 53,5% klaim Liputan6
tidak ada di basis data TurnBackHoax, dengan interval [43,8%; 63,0%] yang mencakup 50%. Menurut
aturan berhenti 11.6, sumber cek fakta kedua dan langkah korektif bergaya CRAG yang dibatasi ke situs
cek fakta **tidak diprioritaskan sekarang**, dan pengukuran ini tidak diperluas lagi. Itu bukan
bukti bahwa celahnya kecil: sekitar separuh klaim Liputan6 memang tidak diperiksa TurnBackHoax
(batas-batas eksploratif 43-63%), jadi "belum ditemukan" tetap akan sering menjadi jawaban yang sah
dan perlu dikomunikasikan di demo apa adanya. Yang tidak ditunjukkan data adalah bahwa celah itu
**jelas** melebihi separuh, dan menurut pembacaan agent pada 11.8 langkah 6 (bukan label) aturan terkunci kemungkinan
justru menurunkan angkanya. Dua temuan sampingan ikut membatasi rancangan apa pun di arah ini bila
kelak dibuka lagi: (1) skor kemiripan tidak memisahkan ada dari tidak ada pada kedua putaran (23/24
dan 22/29 butir TIDAK ADA berskor di atas pasangan sah terendah), jadi pemicu langkah korektif tidak
dapat berupa ambang skor -- ia membutuhkan penilai kesamaan klaim, yang sudah dikeluarkan dari
cakupan Versi 2; (2) 0 dari 46 pasangan hanya ada di antrean, jadi keterlambatan ingest bukan
penyebab celah pada sampel ini, dan sebagian besar pasangan baru adalah PENIPUAN berulang yang
cocok lintas gelombang (14 dari 25 terpaut lebih dari 30 hari), sehingga cakupan nyata untuk hoaks
semacam itu bergantung pada apakah generator menilai gelombang berbeda sebagai klaim yang sama
(pedoman v1.0 dan Aturan A tidak identik; belum diukur). Batas tafsir 11.4 tetap: ini celah terhadap
satu situs cek fakta, bukan terhadap klaim yang diketik pengguna.

---

## Sumber

| Berkas | Dipakai untuk |
| --- | --- |
| `testset/v1_temuan_untuk_v2.md` | temuan per bagian (1, 2, 3, 4, 5, 6, 6.1, 8, 9, 10, 11) |
| `testset/v1_analysis_report.txt` | akurasi, jenis kesalahan, kesepakatan antar-run, caveat, latensi dan token |
| `testset/v1.meta.json` | ambang H1/H3, rancangan evaluasi, sidik jari generator, batas tafsir H1, butir negatif yang berubah status, keputusan `v1-046` |
| `testset/v1.jsonl` | tipe dan label empat butir gagal Recall@3; panjang klaim |
| `testset/ANNOTATION_GUIDE.md` | aturan v1.0 untuk pesan berantai berisi beberapa klaim |
| `data/testset_v1_eval_gemini-3.5-flash-lite.jsonl` | akurasi per run (46, 47, 48 dari 50); 1 panggilan per butir |
| `testset/retrieval_ablation_report.txt`, `_prod922_report.txt`, `_prod1532_report.txt` | Recall@k per indeks; pesan panjang (2/20, 0/20, 0/20; 19/20) |
| `testset/v1_perbandingan_indeks_1532.json`, `testset/devset_retrieval_1532.json` | recall positif pada indeks 1.532; skor set pengembangan |
| `config/related_threshold.json` | dasar keputusan mematikan "Mungkin terkait" |
| `src/candidates/chain_sample.py` | pengambilan sampel acak pesan berantai (bagian 10.2) |
| `src/evaluation/sample_size.py`, `testset/v2_ukuran_sampel.json`, `testset/v2_ukuran_sampel.txt` | seluruh angka ukuran sampel (bagian 4 dan 6.3) |
| `src/llm/limits.py` | kuota (RPM 15, TPM 250.000, RPD 500; 2026-09-21) |
| `src/generator.py`, `tests/test_testset_locks.py` | apa yang sudah dilakukan generator; apa yang terkunci |
| `CLAUDE.md` | keterbatasan, temuan Aturan Wajib #1, latensi Gemma, catatan memori |
| `docs/rancangan/rancangan_evaluasi_eksternal.md` (11.2-11.9) | Bagian A: kecocokan palsu yang gugur, pola kegagalan, 11 butir adjudikasi |
| `testset/eksternal_hasil_per_butir.json` | Bagian A6: keputusan sistem dan label final per butir adjudikasi |
| `data/candidates/adjudikasi_eksternal/hasil_adjudikasi.json` (lokal, tidak di-commit) | Bagian A6: pola dari catatan adjudikasi pemilik proyek; teks pesan tidak dikutip |
| `src/evaluation/metrics.py` (`wilson_interval`) | Bagian A4: seluruh hitungan ukuran sampel dan ambang |
| `robots.txt` situs sumber (diperiksa 2026-10-25) | Bagian A4.a |
