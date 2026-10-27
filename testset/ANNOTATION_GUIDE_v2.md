# Pedoman Anotasi "Klaim Sama" — Versi 2.0 (DRAF, BELUM DIKUNCI)

**Status:** draf 2026-10-27 (revisi 9 rancangan): bentuk dua pertanyaan. Disusun dari lembar persetujuan pedoman A6
dan keputusan pemilik proyek (`docs/rancangan/rancangan_v2.md` A6). **Belum boleh dipakai untuk melabeli butir set
uji.** Revisi berikutnya hanya berdasarkan uji coba 10 butir, lalu pemeriksaan independen; sesudah itu pedoman dikunci
lewat tag `annotation-guide-v2.0` (rancangan A6.5, A12).

**Aturan setelah dikunci** (sama dengan v1.0). Pedoman tidak boleh direvisi selama pelabelan set (a) dan set (b).
Kasus yang tidak tercakup: (1) tandai ragu dan catat sebagai kasus terbuka (butir, artikel, alasan tidak tercakup),
(2) putuskan dengan aturan yang paling dekat, (3) jangan merevisi pedoman di tengah jalan. Perubahan hanya lewat
versi baru (2.1 dan seterusnya) dengan tag baru, dan versi pedoman dicatat per butir.

## 1. Tujuan dan hubungan dengan pedoman v1.0

Pedoman ini menetapkan kapan sebuah pesan dianggap **klaim sama** dengan artikel TurnBackHoax. Ia mengatur
**label manusia**, bukan cara sistem memutuskan.

Pedoman v1.0 (`testset/ANNOTATION_GUIDE.md`, tag `annotation-guide-v1.0`) tetap berlaku untuk semua pasangan yang
tidak memakai bagian 4. Versi 2.0 menambah aturan untuk **pola pendaftaran atau tawaran**: tautan pendaftaran,
lowongan, bantuan, dan pesan sejenis yang beredar berkali-kali dengan lembaga, tautan, atau tanggal yang berganti,
termasuk pengumuman resmi yang memakai pola yang sama.

**Untuk pasangan yang memakai bagian 4, pedoman 2.0 didahulukan bila bertentangan dengan v1.0.** Secara khusus:

- baris "lebih umum -> TIDAK SAMA" v1.0 diganti aturan 8 dan 9;
- baris "cocok dengan lebih dari satu artikel tanpa unsur pembeda -> TIDAK SAMA, `ambigu`" v1.0 diganti aturan 7;
- unsur dibandingkan dengan **Narasi** artikel, bukan judul (KIA hanya untuk mengenali topik); uji dua arah v1.0 diganti
  perbandingan unsur (pertanyaan 1); uji Kesimpulan v1.0 menjadi pertanyaan 2.

Semua contoh di pedoman ini **rekaan**: lembaga, program, tautan, nomor, dan nominalnya dikarang dan tidak mengacu
pada artikel, pesan, atau butir uji mana pun. Domain berakhiran `.example` dan nomor `0800-0000-…` sengaja tidak
nyata. Dalam contoh, Kementerian Kesejahteraan Contoh (KKC) punya domain resmi rekaan `kkc.example`, yang dianggap ada
di daftar acuan.

## 2. Definisi

- **Butir:** satu pesan beserta daftar artikel kandidat. Lembar pelabelan menampilkan **label TurnBackHoax setiap
  kandidat** (metadata artikel, bukan keluaran sistem).
- **Pasangan:** satu pesan dengan satu artikel kandidat. Keputusan "klaim sama" dibuat per pasangan.
- **Unsur inti (pedoman v1.0):** subjek atau aktor; tindakan, peristiwa, atau pernyataan; objek atau kondisi pembeda.
- **Unsur inti pola pendaftaran atau tawaran:** lembaga atau tokoh, tawaran (jenis program atau keuntungan), saluran
  (tautan, akun, atau nomor), nominal, dan periode.
- **Periode:** tahun, atau nama gelombang atau tahap program (misalnya "Gelombang 2", "Tahap II"). **Tanggal batas
  pendaftaran dan tanggal hari tidak termasuk**, karena penipuan daur ulang hampir selalu memperbarui tanggalnya;
  tanggal yang berbeda tetap dicatat. Periode **hanya dibandingkan dengan jenis yang sama** (tahun dengan tahun, nama
  gelombang atau tahap dengan nama gelombang atau tahap). Jenis berbeda berarti tidak dapat dibandingkan, kecuali satu
  sisi memuat keduanya; maka yang dibandingkan adalah jenis yang ada di kedua sisi. Tahun atau periode yang hanya
  tertulis di satu sisi: tidak dapat dibandingkan.
- **Nominal:** jumlah uang yang ditawarkan atau diminta. Jumlah armada, kuota peserta, dan sejenisnya **bukan** nominal.
  Nominal **hanya dibandingkan bila perannya sama** (ditawarkan dengan ditawarkan, diminta dengan diminta); peran
  berbeda berarti tidak dapat dibandingkan.
- **Lembaga umum:** "pemerintah", "kementerian" tanpa nama, dan sejenisnya. Lawan lembaga tertentu: tidak dapat
  dibandingkan.
- **Tokoh lawan lembaga yang dipimpinnya** (misalnya kepala lembaga lawan lembaganya): tidak dapat dibandingkan,
  ditandai ragu, dan dicatat sebagai kasus untuk versi pedoman berikutnya.
- **Status unsur:**
  - **sama:** disebut di kedua sisi dan sama;
  - **bertentangan:** disebut eksplisit di kedua sisi dan berbeda (saluran tidak pernah bertentangan; lihat aturan 5);
  - **tidak dapat dibandingkan:** hanya disebut di satu sisi, tidak disebut di kedua sisi, istilah umum berhadapan
    dengan istilah spesifik (aturan 2 dan 8), jenis periode berbeda, atau peran nominal berbeda.
- **Saluran resmi:** saluran yang ada di **daftar acuan saluran resmi** (lembar terpisah yang ikut ditampilkan saat
  pelabelan), atau yang disebut resmi oleh Kesimpulan artikel itu sendiri. Satu entri domain di daftar acuan mencakup
  subdomain sejatinya (`layanan.kkc.example` dari `kkc.example`); nama yang hanya mirip (`kkc-resmi.example`) tidak.
  Setiap entri daftar acuan punya URL halaman resmi sebagai bukti dan tanggal pemeriksaan. Tautan di pesan atau di
  sumber hoaks **tidak dibuka**; yang dicocokkan teks alamatnya. **Saluran yang tidak ada di daftar acuan dan tidak
  disebut resmi oleh Kesimpulan dihitung tidak resmi**, termasuk pemendek URL dan nomor WhatsApp.
- **Saluran tampak resmi tetapi tidak ada di daftar:** bila pelabel menilai sebuah saluran tampak resmi (misalnya
  domain go.id lembaga yang tidak ada di daftar), ia tetap dihitung tidak resmi, pasangan **ditandai ragu**, dan
  salurannya dicatat supaya daftar acuan bisa diperbaiki di versi berikutnya.
- **Ragu:** tanda bahwa keputusan sebuah pasangan atau butir tidak pasti menurut pedoman. Ragu tidak mengubah label
  (bagian 7).

## 3. Kapan aturan pola pendaftaran atau tawaran dipakai

Ditentukan **per pasangan pesan–artikel**. Sebuah pasangan memakai bagian 4 bila:

- (a) artikelnya berlabel **PENIPUAN** di TurnBackHoax, **atau**
- (b) pesannya meminta pembaca mendaftar, mengisi data pribadi, mentransfer uang, atau menghubungi tautan atau nomor
  atas nama lembaga atau tokoh.

Pengumuman resmi yang mengajak mendaftar memenuhi (b), jadi ikut dinilai dengan bagian 4. Pasangan lain memakai
pedoman v1.0 (klaim inti, unsur inti, uji dua arah, uji Kesimpulan). Dalam satu butir, pasangan yang berbeda bisa
memakai aturan yang berbeda. Bila ragu apakah sebuah pasangan termasuk pola ini, catat keraguannya dan alasan memilih
aturan yang dipakai.

## 4. Dua pertanyaan (pasangan pola pendaftaran atau tawaran)

**Pasangan adalah klaim sama hanya bila jawaban kedua pertanyaan "ya".**

- **Pertanyaan 1. Program sama?** Diputuskan aturan 1–6, 8, dan 9: lembaga atau tokoh, tawaran, periode, dan nominal
  memastikan pesan dan artikel membicarakan program dan gelombang yang sama.
- **Pertanyaan 2. Kesimpulan membantah pesan?** Diputuskan aturan 10: Kesimpulan artikel, dibaca sebagai jawaban,
  membantah apa yang dinyatakan atau diajak pesan.

Aturan 7 berlaku bila lebih dari satu artikel menjawab "ya" pada kedua pertanyaan.

### 4.1 Pertanyaan 1: program sama?

**Aturan 1. Lembaga atau tokoh berbeda, tawaran sama -> BUKAN klaim sama.**

> Pesan: Bantuan Modal Usaha dari Badan Beasiswa Rekaan. Artikel: Bantuan Modal Usaha atas nama KKC.
> Lembaga bertentangan -> pertanyaan 1 "tidak" -> **BUKAN klaim sama.**

**Aturan 2. Lembaga atau tokoh tidak disebut di salah satu sisi -> tidak dapat dibandingkan, bukan pertentangan.**
Keputusan bergantung pada unsur inti lain. Lembaga umum lawan lembaga tertentu juga tidak dapat dibandingkan.

> Pesan: "Ada Bantuan Modal Usaha Rp2 juta dari pemerintah." Artikel: Bantuan Modal Usaha Rp2 juta atas nama KKC.
> Lembaga tidak dapat dibandingkan; tawaran sama; nominal sama; tidak ada yang bertentangan -> pertanyaan 1 "ya"
> (aturan 9, kalimat pertama).

**Aturan 3. Gelombang berbeda yang hanya terlihat dari tanggal terbit, lembaga dan tawaran sama -> program sama.
Tahun atau periode yang tertulis di kedua teks dan berbeda -> BUKAN klaim sama.**

> Pesan: Rekrutmen Petugas Lapangan PT Energi Fiktif. Artikel (terbit setahun sebelumnya): rekrutmen yang sama, tanpa
> tahun di Narasi -> pertanyaan 1 "ya".
> Bila pesan menulis "2027" dan Narasi "2026" -> **BUKAN klaim sama.** Bila pesan menulis "Gelombang 2" dan Narasi
> hanya "2026": jenis periode berbeda -> tidak dapat dibandingkan. Tanggal penutupan yang berbeda hanya dicatat.

**Aturan 4. Nominal berbeda pada tawaran yang sama -> BUKAN klaim sama bila nominal dengan peran yang sama disebut
eksplisit di kedua sisi.** Ini berlaku juga bila gelombangnya terlihat berbeda dari tanggal terbit. Bila tahun atau
periode tertulis di kedua teks dan berbeda, pasangan sudah bukan klaim sama menurut aturan 3. Bila hanya satu sisi
menyebut nominal, atau perannya berbeda: tidak dapat dibandingkan.

> Pesan: Bantuan Modal Usaha KKC Rp5 juta. Artikel: Bantuan Modal Usaha KKC Rp2 juta -> **BUKAN klaim sama.**
> Pesan menawarkan Rp2 juta; artikel menyebut biaya pendaftaran Rp100 ribu: peran berbeda -> tidak dapat dibandingkan.

**Aturan 5. Saluran berbeda bersifat netral pada pertanyaan 1.** Penipu sering berganti tautan, jadi tautan atau nomor
yang berbeda tidak menolak. Saluran yang sama persis dengan sumber hoaks di artikel adalah **bukti pendukung** bahwa
programnya sama. **Saluran resmi yang sama di kedua sisi bukan bukti pendukung** (pengumuman resmi dan hoaks bisa
menyebut situs resmi yang sama). Apakah saluran itu dibantah ditentukan di pertanyaan 2.

> Pesan: Bantuan Modal Usaha KKC lewat daftar-kkc.example. Artikel: Bantuan Modal Usaha KKC lewat bantuan-kkc.example
> -> saluran netral -> pertanyaan 1 "ya".

**Aturan 6. Judul sama, isi tawaran berbeda -> BUKAN klaim sama.** Yang dibandingkan adalah isi pesan dengan Narasi,
bukan judul dengan judul.

> Judul artikel "Tautan Pendaftaran Bantuan KKC", Narasinya tentang paket sembako; pesan berjudul sama tentang
> Bantuan Modal Usaha -> **BUKAN klaim sama.**

**Aturan 8. Tawaran berbeda (program spesifik berbeda) -> BUKAN klaim sama.** Istilah umum ("bansos", "bantuan",
"lowongan") dibandingkan dengan program spesifik dihitung tidak dapat dibandingkan.

> Pesan: Bantuan Modal Usaha KKC. Artikel: Bantuan Paket Sembako KKC -> **BUKAN klaim sama.**
> Pesan hanya "bantuan dari KKC": tawaran tidak dapat dibandingkan -> aturan 9.

**Aturan 9 (aturan bawaan pertanyaan 1).** Pertanyaan 1 "ya" bila tawaran sama dan tidak ada unsur inti yang
bertentangan. Bila tawaran tidak dapat dibandingkan, "ya" hanya bila lembaga atau tokoh sama, setidaknya satu unsur lain
(saluran sama persis dengan sumber hoaks, nominal, atau periode) sama, dan tidak ada unsur inti yang bertentangan. Bila
keadaan kedua ini tidak memenuhi syarat: **BUKAN klaim sama**, dan pasangan ditandai ragu. **Penolakan karena ada unsur
inti yang bertentangan tidak ditandai ragu oleh aturan ini.**

> Pesan: "Bantuan dari KKC, daftar di bantuan-kkc.example." Artikel: Bantuan Modal Usaha KKC, sumber hoaksnya
> bantuan-kkc.example -> tawaran tidak dapat dibandingkan, lembaga sama, saluran sama persis -> pertanyaan 1 "ya".
> Bila tautannya berbeda dan tidak ada nominal atau periode yang sama -> **BUKAN klaim sama, ragu.**

**Hubungan induk dan anak lembaga** (misalnya sebuah BUMN dan anak perusahaannya) belum diatur. Pasangan seperti itu
ditandai ragu dan dicatat.

### 4.2 Pertanyaan 2: Kesimpulan membantah pesan?

**Aturan 10.** Pertanyaan 2 "ya" bila Kesimpulan artikel membantah apa yang dinyatakan atau diajak pesan. Dinilai
**per jenis bantahan**, bukan per untaian teks. Bila Kesimpulan memuat beberapa jenis bantahan, cukup satu jenis yang
membantah pesan.

- **(a) Saluran tidak resmi.** Kesimpulan menyatakan tautan, akun, atau nomor yang beredar tidak resmi. Membantah pesan
  yang memakai **atau merujuk** saluran tidak resmi (bagian 2), termasuk "klik tautan berikut" tanpa alamat.
- **(b) Program atau tawaran tidak ada atau belum dibuka.** Membantah pesan yang menyatakan program itu ada atau
  dibuka. **Pengecualian:** tidak berlaku bila pesan terbit setelah tanggal artikel **dan** memakai saluran yang ada di
  daftar acuan.
- **(c) Biaya, transfer, data pribadi, syarat, atau nominal palsu.** Membantah pesan yang memuat unsur itu.
- **(d) Bantahan menyeluruh** (konten rekayasa, tanpa bukti, atau hanya "unggahan berisi klaim … palsu"). Membantah
  pesan yang menyatakan klaim yang dikutip Kesimpulan.

Pesan yang **sesuai dengan fakta di Kesimpulan** tidak dibantah: misalnya memakai saluran yang disebut resmi, atau tidak
menyebut cara mendaftar dan tidak memuat unsur yang dibantah. Pertanyaan 2 "tidak" -> **BUKAN klaim sama**, tanpa tanda
ragu kecuali ada alasan ragu lain.

> (a) Artikel: "tautan pendaftaran Bantuan Modal Usaha KKC tidak mengarah ke laman resmi KKC". Pesan: daftar lewat
> daftar-kkc.example (tidak ada di daftar acuan) -> dibantah -> dengan pertanyaan 1 "ya": **klaim sama.**
> Pesan: "klik tautan berikut untuk mendaftar" (alamat tidak dikutip) -> merujuk saluran tidak resmi -> dibantah.

> (a), pengumuman resmi. Pesan: "Pendaftaran Bantuan Modal Usaha KKC dibuka melalui layanan.kkc.example"
> (subdomain `kkc.example`, ada di daftar acuan) -> tidak dibantah -> **BUKAN klaim sama.**

> (b) Artikel: "KKC tidak pernah mengadakan Bantuan Modal Usaha". Pesan: "KKC membuka Bantuan Modal Usaha" ->
> dibantah. Bila pesan terbit setelah artikel dan memakai layanan.kkc.example -> pengecualian berlaku, tidak dibantah.

> (c) Artikel: "KKC tidak memungut biaya apa pun". Pesan meminta biaya administrasi Rp50 ribu -> dibantah.

> (d) Artikel: "unggahan berisi klaim 'Bantuan Modal Usaha KKC Rp2 juta' merupakan konten palsu". Pesan menyatakan
> klaim yang sama -> dibantah; keputusan praktis ditentukan pertanyaan 1.

### 4.3 Lebih dari satu artikel

**Aturan 7. Bila lebih dari satu artikel menjawab "ya" pada kedua pertanyaan, semua artikel itu sah dan dicatat, dan
jawaban dinilai benar bila memilih salah satunya.** Jumlah artikel sah dicatat per butir.

> Pesan: Beasiswa Cendekia Rekaan, tanpa tahun dan nominal, lewat tautan tidak resmi. Dua artikel (2025 dan 2026)
> tentang beasiswa yang sama, keduanya menyatakan tautannya tidak resmi -> keduanya sah; label positif.

## 5. Urutan langkah menilai satu butir

Urutan ini adalah cara kerja, bukan aturan baru. Bila urutan dan aturan berbeda, aturan di bagian 4 yang berlaku.

1. Baca pesan. Jangan melihat keluaran sistem, skor retrieval, atau label orang lain.
2. Untuk setiap artikel kandidat, tentukan apakah pasangannya memakai bagian 4 (bagian 3). Bila tidak, nilai dengan
   pedoman v1.0 dan lanjut ke kandidat berikutnya.
3. Isi unsur di kedua sisi beserta statusnya (bagian 6), dibandingkan dengan **Narasi** artikel. Cocokkan saluran
   dengan daftar acuan tanpa membuka tautan.
4. **Pertanyaan 1:** periksa pertentangan lembaga atau tokoh (aturan 1), tawaran (aturan 6, 8), tahun atau periode
   (aturan 3), dan nominal (aturan 4). Ada pertentangan -> **BUKAN klaim sama**, tanpa tanda ragu karena aturan 9.
   Tidak ada -> aturan 9.
5. **Pertanyaan 2** (hanya bila pertanyaan 1 "ya"): tentukan jenis bantahan di Kesimpulan (aturan 10) dan apakah
   bantahan itu mengenai pesan.
6. Klaim sama bila kedua pertanyaan "ya". Bila lebih dari satu artikel sah, catat semuanya (aturan 7).
7. Label butir: **positif** bila setidaknya satu artikel sah, dengan daftar semua artikel yang sah; **negatif** bila
   tidak ada. Isi catatan wajib, tanda ragu, dan kolom `kekhususan` (bagian 7).

## 6. Cara mengisi catatan wajib

Setiap label pada pasangan pola pendaftaran atau tawaran, **positif maupun negatif**, wajib mencatat lembaga atau
tokoh, tawaran, saluran, nominal (dengan perannya), dan tahun atau periode di kedua sisi, beserta statusnya (sama,
bertentangan, tidak dapat dibandingkan); untuk saluran, apakah ada di daftar acuan; dan **jenis bantahan Kesimpulan
(a–d) serta apakah bantahan itu mengenai pesan**. Tanggal yang berbeda tetap dicatat.

Untuk label negatif, catatan dibuat pada **kandidat yang paling mirip menurut penilaian anotator** (tanpa skor
retrieval): sebutkan pertanyaan mana yang "tidak", dan unsur yang bertentangan atau alasan Kesimpulan tidak membantah
pesan, beserta aturannya.

Bentuk yang disarankan, satu baris per pasangan (pesan | artikel | status):

```
artikel <id>; lembaga: KKC | KKC | sama; tawaran: bantuan | Bantuan Modal Usaha | tidak dapat dibandingkan;
saluran: bantuan-kkc.example | bantuan-kkc.example | sama persis, tidak di daftar acuan;
nominal (ditawarkan): - | Rp2 juta | tidak dapat dibandingkan; periode: - | - | tidak dapat dibandingkan;
tanggal: 10 Jan | 3 Mar | dicatat; P1: ya (aturan 9); P2: ya (a, tautan tidak resmi); putusan: SAMA; ragu: -
```

Catatan seperti "narasi sama" atau "konteks sama" tanpa menyebut unsur yang dibandingkan **tidak memenuhi** catatan
wajib.

## 7. Ragu dan kolom `kekhususan`

Tandai **ragu** dan tulis alasannya (dengan aturan terdekat yang dipakai) bila:

- keadaan kedua aturan 9 tidak memenuhi syarat (tawaran tidak dapat dibandingkan dan bukti tambahan kurang);
- saluran tampak resmi tetapi tidak ada di daftar acuan (catat salurannya);
- pasangan melibatkan tokoh lawan lembaga yang dipimpinnya, atau induk dan anak lembaga;
- tidak jelas apakah pasangan memakai bagian 4 (bagian 3);
- kasusnya tidak tercakup pedoman (kasus terbuka).

Penolakan karena ada unsur yang bertentangan, atau karena Kesimpulan tidak membantah pesan, **tidak** ditandai ragu
hanya karena itu. Ragu tidak mengubah label. Metrik utama memakai label akhir semua butir, termasuk butir ragu; analisis
sensitivitas mengulang metrik tanpa butir yang ditandai ragu oleh salah satu pelabel.

**Ragu menggantikan nilai `batas` pedoman v1.0** di seluruh set Versi 2. Kolom `kekhususan` diisi hanya untuk butir yang
semua pasangannya dinilai dengan pedoman v1.0 (tanpa nilai `batas`); butir yang punya pasangan bagian 4 diisi `a6`.
Nilai `ambigu` v1.0 tidak dipakai untuk pasangan bagian 4 (aturan 7 menggantikannya).

## 8. Keterbatasan dan asal-usul (dicatat, bukan disembunyikan)

- **Aturan disusun setelah melihat data.** Aturan 1–8 berangkat dari 11 butir adjudikasi evaluasi eksternal, aturan 4
  diubah dua kali setelah data dilihat, dan bentuk dua pertanyaan dipilih setelah pengukuran heuristik atas Kesimpulan
  dan kutipan Liputan6. Pembatasnya: semua perubahan terjadi sebelum set (a) dan (b) ada, dan pedoman dikunci sebelum
  pelabelan.
- **Bantuan AI saat menyusun pedoman.** Pemilik proyek memakai Claude (Anthropic) dalam diskusi saat mengisi lembar
  persetujuan dan saat memutuskan setiap revisi. Teks aturan disusun bersama AI lalu disetujui pemilik proyek; semua
  keputusan adalah keputusan pemilik proyek. Pernyataan lengkapnya ada di rancangan A6.3. **Label butir dibuat manusia
  tanpa AI** (aturan wajib #5).
- **Daftar acuan saluran resmi disusun AI dan diverifikasi pemilik proyek** entri per entri. Ia data acuan, bukan label.
  Saluran resmi yang tidak ada di daftar membuat pengumuman resmi tampak tidak resmi; karena itu ada tanda ragu untuk
  saluran yang tampak resmi.
- **Sikap berhati-hati mengurangi positif set (b).** Bila Kesimpulan membantah satu unsur (misalnya tautannya) dan pesan
  tidak memuat unsur itu (misalnya hanya meminta transfer, atau kutipan pesannya tidak memuat tautan), pasangan bukan
  klaim sama walau penipuannya mungkin sama.
- Aturan 9 condong ke "bukan klaim sama". Pada pasangan yang buktinya tipis, sistem yang menjawab "ditemukan" akan
  dihitung salah, walau pembaca lain bisa menilainya cocok.
- Menilai "apakah Kesimpulan membantah pesan" adalah penilaian yang bisa berbeda antar-pelabel, terutama pada bantahan
  menyeluruh (jenis d).

## 9. Riwayat versi

| Versi | Tanggal | Perubahan |
| --- | --- | --- |
| 1.0 | 2026-09-21 | `testset/ANNOTATION_GUIDE.md`, dikunci sebelum set uji v1 dibuat. |
| 2.0 (draf) | 2026-10-27 | Aturan penipuan berulang 1–9, definisi periode, catatan wajib, tanda ragu. |
| 2.0 (draf, revisi 7) | 2026-10-27 | Nama "pola pendaftaran atau tawaran"; pengecualian saluran resmi; definisi nominal, jenis periode, lembaga umum, tokoh lawan lembaganya; aturan 3 dan 9 dirumuskan ulang. |
| 2.0 (draf, revisi 9) | 2026-10-27 | Bentuk dua pertanyaan (program sama; Kesimpulan membantah pesan, aturan 10); pengecualian saluran resmi dan verifikasi lima langkah dihapus, diganti daftar acuan; prioritas atas v1.0 untuk tiga titik; peran nominal; ragu menggantikan `batas`. Belum dikunci; revisi berikutnya hanya dari uji coba dan pemeriksaan independen. |
