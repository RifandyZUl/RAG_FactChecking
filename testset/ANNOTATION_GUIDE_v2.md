# Pedoman Anotasi "Klaim Sama" — Versi 2.0 (DRAF, BELUM DIKUNCI)

**Status:** draf 2026-10-27 (revisi 7 rancangan), disusun dari lembar persetujuan pedoman A6 dan keputusan pemilik
proyek (`docs/rancangan/rancangan_v2.md` A6). **Belum boleh dipakai untuk melabeli butir apa pun.** Sebelum dikunci,
hal yang belum diputuskan di bagian 9 harus ditutup pemilik proyek, lalu pedoman ini dikunci lewat tag
`annotation-guide-v2.0` (rencana: rancangan A6.5).

**Aturan setelah dikunci** (sama dengan v1.0). Pedoman tidak boleh direvisi selama pelabelan set (a) dan set (b).
Kasus yang tidak tercakup: (1) tandai ragu dan catat sebagai kasus terbuka (butir, artikel, alasan tidak tercakup),
(2) putuskan dengan aturan yang paling dekat, (3) jangan merevisi pedoman di tengah jalan. Perubahan hanya lewat
versi baru (2.1 dan seterusnya) dengan tag baru, dan versi pedoman dicatat per butir.

## 1. Tujuan dan hubungan dengan pedoman v1.0

Pedoman ini menetapkan kapan sebuah pesan dianggap **klaim sama** dengan artikel TurnBackHoax. Ia mengatur
**label manusia**, bukan cara sistem memutuskan. Sistem Versi 1 tidak diubah; selisih antara pedoman ini dan perilaku
sistem muncul sebagai kesalahan di metrik (rancangan A6.1).

Pedoman v1.0 (`testset/ANNOTATION_GUIDE.md`, tag `annotation-guide-v1.0`) tetap berlaku untuk semua pasangan yang
tidak memakai aturan bagian 4. Versi 2.0 menambah aturan untuk **pola pendaftaran atau tawaran**: tautan pendaftaran,
lowongan, bantuan, dan pesan sejenis yang beredar berkali-kali dengan lembaga, tautan, atau tanggal yang berganti,
termasuk pengumuman resmi yang memakai pola yang sama. **Untuk pasangan yang memakai bagian 4, pedoman 2.0 didahulukan
bila bertentangan dengan v1.0.**

Semua contoh di pedoman ini **rekaan**: lembaga, program, tautan, nomor, dan nominalnya dikarang dan tidak mengacu
pada artikel, pesan, atau butir uji mana pun. Domain berakhiran `.example` dan nomor `0800-0000-…` sengaja tidak
nyata. Dalam contoh, domain resmi rekaan Kementerian Kesejahteraan Contoh (KKC) adalah `kkc.example`.

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
  sisi memuat keduanya; maka yang dibandingkan adalah jenis yang ada di kedua sisi.
- **Nominal:** jumlah uang yang ditawarkan atau diminta. Jumlah armada, kuota peserta, dan sejenisnya **bukan** nominal.
- **Lembaga umum:** "pemerintah", "kementerian" tanpa nama, dan sejenisnya. Lawan lembaga tertentu: tidak dapat
  dibandingkan.
- **Tokoh lawan lembaga yang dipimpinnya** (misalnya kepala lembaga lawan lembaganya): tidak dapat dibandingkan,
  ditandai ragu, dan dicatat sebagai kasus untuk versi pedoman berikutnya.
- **Status unsur:**
  - **sama:** disebut di kedua sisi dan sama;
  - **bertentangan:** disebut eksplisit di kedua sisi dan berbeda (untuk saluran, lihat aturan 5);
  - **tidak dapat dibandingkan:** hanya disebut di satu sisi, tidak disebut di kedua sisi, istilah umum berhadapan
    dengan istilah spesifik (aturan 2 dan 8), atau jenis periode berbeda.
- **Ragu:** tanda bahwa keputusan sebuah pasangan atau butir tidak pasti menurut pedoman. Ragu tidak mengubah label
  (bagian 7).

### 2.1 Saluran resmi yang terverifikasi

Saluran resmi adalah domain, akun, atau nomor milik lembaga yang disebut, yang dicocokkan pelabel dengan **sumber
acuan**:

- (a) situs resmi lembaga itu, dibuka dari alamat yang sudah diketahui atau diketik sendiri, **bukan** dari tautan di
  pesan atau di sumber hoaks; atau
- (b) saluran yang dinyatakan resmi di Kesimpulan atau Referensi artikel TurnBackHoax.

Cara memverifikasi:

1. Yang dicocokkan adalah **teks alamat**. Tautan di pesan atau di sumber hoaks **tidak dibuka**.
2. Cocok bila host sama persis dengan saluran di sumber acuan, atau subdomain sejatinya (`daftar.kkc.example` dari
   `kkc.example`). Nama yang mirip (`kkc-resmi.example`, `kkc.example.daftar.example`), subdomain layanan hosting, dan
   pemendek URL tidak pernah dihitung resmi, kecuali persis tercantum di sumber acuan. Nomor telepon atau WhatsApp
   resmi hanya bila tercantum di sumber acuan.
3. Sumber acuan dan tanggal pemeriksaan dicatat di catatan wajib.
4. Pada set (a), saluran yang disebut di dalam pengumuman yang diambil dari situs resmi lembaga dianggap terverifikasi;
   sumber acuannya adalah URL butir itu.
5. Bila status resmi suatu saluran tidak dapat dipastikan: saluran **tidak dapat dibandingkan**, dan pasangan
   **ditandai ragu**.

## 3. Kapan aturan pola pendaftaran atau tawaran dipakai

Ditentukan **per pasangan pesan–artikel**. Sebuah pasangan memakai aturan bagian 4 bila:

- (a) artikelnya berlabel **PENIPUAN** di TurnBackHoax, **atau**
- (b) pesannya meminta pembaca mendaftar, mengisi data pribadi, mentransfer uang, atau menghubungi tautan atau nomor
  atas nama lembaga atau tokoh.

Pengumuman resmi yang mengajak mendaftar memenuhi (b), jadi ikut dinilai dengan bagian 4. Pasangan lain memakai
pedoman v1.0 (klaim inti, unsur inti, uji dua arah, uji Kesimpulan). Dalam satu butir, pasangan yang berbeda bisa
memakai aturan yang berbeda. Bila ragu apakah sebuah pasangan termasuk pola ini, catat keraguannya dan alasan memilih
aturan yang dipakai.

## 4. Aturan 1–9 (pasangan pola pendaftaran atau tawaran)

Isi aturan sama dengan rancangan A6 (rujukan ke nomor keputusan rancangan dihilangkan). Setiap aturan diberi contoh
rekaan.

**Aturan 1. Lembaga atau tokoh berbeda, tawaran sama -> BUKAN klaim sama.**

> Pesan: "Pendaftaran Bantuan Modal Usaha dari Badan Beasiswa Rekaan, daftar di bantuan-bbr.example."
> Artikel: tautan pendaftaran Bantuan Modal Usaha atas nama KKC.
> Lembaga bertentangan, tawaran sama -> **BUKAN klaim sama.**

**Aturan 2. Lembaga atau tokoh tidak disebut di salah satu sisi -> tidak dapat dibandingkan, bukan pertentangan.**
Keputusan bergantung pada unsur inti lain. Lembaga umum lawan lembaga tertentu juga tidak dapat dibandingkan.

> Pesan: "Ada Bantuan Modal Usaha Rp2 juta dari pemerintah, daftar lewat bantuan-umkm.example."
> Artikel: tautan pendaftaran Bantuan Modal Usaha Rp2 juta atas nama KKC.
> Lembaga tidak dapat dibandingkan ("pemerintah" lawan KKC); tawaran sama; nominal sama; tidak ada yang bertentangan
> -> **klaim sama** (aturan 9, kalimat pertama).

**Aturan 3. Gelombang berbeda yang hanya terlihat dari tanggal terbit, lembaga dan tawaran sama -> klaim sama. Tahun
atau periode yang tertulis di kedua teks dan berbeda -> BUKAN klaim sama.** Tahun atau periode yang hanya tertulis di
satu sisi: tidak dapat dibandingkan.

> Pesan: "Rekrutmen Petugas Lapangan PT Energi Fiktif, daftar di sini." Artikel (terbit setahun sebelumnya):
> rekrutmen Petugas Lapangan PT Energi Fiktif, tanpa tahun di Narasi.
> Gelombang berbeda hanya terlihat dari tanggal terbit -> **klaim sama.**
> Bila pesan menulis "Rekrutmen … 2027" dan Narasi menulis "Rekrutmen … 2026" -> **BUKAN klaim sama.**
> Bila pesan menulis "Gelombang 2" dan Narasi hanya "2026": jenis periode berbeda -> tidak dapat dibandingkan.
> Tanggal penutupan yang berbeda (misalnya 10 Januari dan 3 Maret) bukan periode, hanya dicatat.

**Aturan 4. Nominal berbeda pada tawaran yang sama -> BUKAN klaim sama bila nominal disebut eksplisit di kedua sisi.**
Ini berlaku juga bila gelombangnya terlihat berbeda dari tanggal terbit. Bila tahun atau periode tertulis di kedua teks
dan berbeda, butir sudah bukan klaim sama menurut aturan 3, apa pun nominalnya. Bila hanya satu sisi menyebut nominal:
tidak dapat dibandingkan.

> Pesan: "Bantuan Modal Usaha KKC Rp5 juta." Artikel (terbit empat bulan sebelumnya): Bantuan Modal Usaha KKC
> Rp2 juta.
> Nominal bertentangan -> **BUKAN klaim sama**, walau jarak terbitnya menandakan gelombang lain.
> "Kuota 1.000 peserta" di salah satu sisi bukan nominal.

**Aturan 5. Tautan atau nomor berbeda, lembaga dan tawaran sama -> klaim sama.** Penipu sering berganti tautan.
Saluran berbeda bersifat **netral**; saluran yang sama persis dengan sumber hoaks di artikel adalah **bukti
pendukung** yang kuat, tetapi bukan syarat.
**Pengecualian saluran resmi:** bila satu sisi memakai saluran resmi lembaga yang terverifikasi (bagian 2.1) dan sisi
lain tidak, saluran **bertentangan** dan pasangan itu **BUKAN klaim sama**. Bila kedua sisi bukan saluran resmi,
kalimat pertama aturan ini tetap berlaku.

> Pesan: Bantuan Modal Usaha KKC lewat daftar-kkc.example. Artikel: Bantuan Modal Usaha KKC lewat
> bantuan-kkc.example dan nomor 0800-0000-0001. Situs resmi KKC (`kkc.example`) tidak mencantumkan kedua alamat itu.
> Kedua sisi bukan saluran resmi; saluran berbeda netral -> **klaim sama.**

> **Pengecualian.** Pesan (set a, diambil dari `kkc.example`): "Pendaftaran Bantuan Modal Usaha KKC dibuka melalui
> layanan.kkc.example." Artikel berlabel PENIPUAN: tautan pendaftaran Bantuan Modal Usaha KKC lewat
> bantuan-kkc.example.
> Pesan memakai saluran resmi terverifikasi (subdomain sejati `kkc.example`, asal butir); artikel tidak -> saluran
> bertentangan -> **BUKAN klaim sama.**

> **Tiruan.** Pesan meneruskan "daftar di kkc-resmi.example". Nama mirip tidak dihitung resmi (bagian 2.1 butir 2), jadi
> pengecualian tidak berlaku; dinilai dengan kalimat pertama aturan 5.

**Aturan 6. Judul sama, isi tawaran berbeda -> BUKAN klaim sama.** Yang dibandingkan adalah isi pesan dengan Narasi,
bukan judul dengan judul.

> Judul artikel: "Tautan Pendaftaran Bantuan KKC"; Narasinya tentang paket sembako. Pesan berjudul sama persis,
> tetapi isinya Bantuan Modal Usaha.
> Tawaran bertentangan -> **BUKAN klaim sama.**

**Aturan 7. Bila lebih dari satu artikel cocok dengan pesan (lembaga dan tawaran sama), semua artikel yang sah dicatat,
dan jawaban dinilai benar bila memilih salah satunya.** Sebuah artikel hanya sah bila, terhadap pesan itu, ia lolos
semua aturan lain (aturan 1–6, 8, dan 9): tidak ada pertentangan tahun atau periode (aturan 3), nominal (aturan 4),
atau saluran resmi (aturan 5).

> Pesan: Beasiswa Cendekia Rekaan dari Badan Beasiswa Rekaan, tanpa tahun dan nominal. Dua artikel: satu terbit
> 2025 dan satu 2026, keduanya Beasiswa Cendekia Rekaan dari lembaga yang sama, tanpa tahun di Narasi.
> Keduanya sah -> keduanya dicatat; label positif.
> Bila pesan menulis "2026" dan Narasi artikel pertama menulis "2025": artikel pertama tidak sah (aturan 3), hanya
> artikel kedua yang dicatat.

**Aturan 8. Tawaran berbeda (program spesifik berbeda) -> BUKAN klaim sama.** Istilah umum ("bansos", "bantuan",
"lowongan") dibandingkan dengan program spesifik dihitung tidak dapat dibandingkan.

> Pesan: Bantuan Modal Usaha KKC. Artikel: Bantuan Paket Sembako KKC.
> Tawaran bertentangan -> **BUKAN klaim sama.**
> Bila pesan hanya menyebut "bantuan dari KKC": tawaran tidak dapat dibandingkan -> lanjut ke aturan 9.

**Aturan 9 (aturan bawaan).** Klaim sama membutuhkan tawaran yang sama dan tidak ada unsur inti yang bertentangan.
Bila tawaran tidak dapat dibandingkan, klaim sama hanya bila lembaga atau tokoh sama, setidaknya satu unsur lain
(saluran sama persis, nominal, atau periode) sama, dan tidak ada unsur inti yang bertentangan. Bila keadaan kedua ini
tidak memenuhi syarat: bukan klaim sama, dan butir ditandai ragu. **Penolakan karena ada unsur inti yang bertentangan
tidak ditandai ragu oleh aturan ini.** Saluran berbeda tidak dihitung bertentangan, kecuali pengecualian saluran resmi
(aturan 5).

Alasan aturan ini: aturan 1–8 berangkat dari "lembaga dan tawaran sama", sehingga tidak ada keputusan ketika tawaran
tidak dapat dibandingkan. Di celah itulah keputusan "narasi sama" dulu muncul. Aturan ini sengaja condong ke "bukan
klaim sama" ketika buktinya kurang.

> Pesan: "Bantuan dari KKC, daftar di bantuan-kkc.example." Artikel: Bantuan Modal Usaha KKC, sumber hoaksnya
> bantuan-kkc.example.
> Tawaran tidak dapat dibandingkan; lembaga sama; saluran sama persis -> **klaim sama.**
> Bila tautannya berbeda dan tidak ada nominal atau periode yang sama -> **BUKAN klaim sama, ragu.**
> Bila lembaganya berbeda -> **BUKAN klaim sama** karena aturan 1, **tanpa** tanda ragu.

**Hubungan induk dan anak lembaga** (misalnya sebuah BUMN dan anak perusahaannya) belum diatur. Pasangan seperti itu
ditandai ragu dan dicatat.

## 5. Urutan langkah menilai satu butir

Urutan ini adalah cara kerja, bukan aturan baru. Bila urutan dan aturan berbeda, aturan di bagian 4 yang berlaku.

1. Baca pesan. Jangan melihat keluaran sistem, skor retrieval, atau label orang lain.
2. Untuk setiap artikel kandidat, tentukan apakah pasangannya memakai bagian 4 (bagian 3; label TurnBackHoax kandidat
   ada di lembar). Bila tidak, nilai dengan pedoman v1.0 dan lanjut ke kandidat berikutnya.
3. Isi unsur di kedua sisi beserta statusnya (bagian 6). Bandingkan isi pesan dengan **Narasi** artikel, bukan judul
   dengan judul (aturan 6). Periksa status resmi saluran bila perlu (bagian 2.1), tanpa membuka tautan dari pesan atau
   sumber hoaks.
4. Periksa unsur yang bertentangan: lembaga atau tokoh (aturan 1), tawaran (aturan 6 dan 8), tahun atau periode
   (aturan 3), nominal (aturan 4), dan saluran resmi lawan tidak resmi (aturan 5). Bila ada yang bertentangan:
   **BUKAN klaim sama**, tanpa tanda ragu karena aturan 9.
5. Bila tidak ada yang bertentangan:
   - tawaran sama -> **klaim sama** (aturan 9, kalimat pertama; aturan 2, 3, dan 5 menjelaskan unsur yang boleh
     berbeda atau tidak disebut);
   - tawaran tidak dapat dibandingkan -> keadaan kedua aturan 9.
6. Bila lebih dari satu artikel sah, catat semuanya (aturan 7).
7. Label butir: **positif** bila setidaknya satu artikel sah, dengan daftar semua artikel yang sah; **negatif** bila
   tidak ada. Isi catatan wajib dan tanda ragu.

## 6. Cara mengisi catatan wajib

Setiap label pada pasangan pola pendaftaran atau tawaran, **positif maupun negatif**, wajib mencatat lembaga atau
tokoh, tawaran, saluran, nominal, dan tahun atau periode di kedua sisi, beserta statusnya (sama, bertentangan, tidak
dapat dibandingkan). Untuk saluran, catat juga apakah resmi, sumber acuan, dan tanggal pemeriksaannya. Tanggal yang
berbeda tetap dicatat.

Untuk label negatif, catatan dibuat pada **kandidat yang paling mirip menurut penilaian anotator** (tanpa skor
retrieval): sebutkan minimal satu unsur yang bertentangan dan aturan yang dipakai. Bila tidak ada unsur yang
bertentangan, tulis alasannya secara eksplisit (misalnya "aturan 9: tawaran tidak dapat dibandingkan, lembaga tidak
disebut").

Bentuk yang disarankan, satu baris per pasangan (pesan | artikel | status):

```
artikel <id>; lembaga: KKC | KKC | sama; tawaran: bantuan | Bantuan Modal Usaha | tidak dapat dibandingkan;
saluran: bantuan-kkc.example | bantuan-kkc.example | sama persis, keduanya tidak resmi (acuan kkc.example, 2027-01-10);
nominal: - | Rp2 juta | tidak dapat dibandingkan; periode: - | - | tidak dapat dibandingkan;
tanggal: 10 Jan | 3 Mar | dicatat; aturan: 9; putusan: SAMA; ragu: -
```

Catatan seperti "narasi sama" atau "konteks sama" tanpa menyebut unsur yang dibandingkan **tidak memenuhi** catatan
wajib.

## 7. Cara menandai ragu

Tandai **ragu** dan tulis alasannya (dengan aturan terdekat yang dipakai) bila:

- keadaan kedua aturan 9 tidak memenuhi syarat (tawaran tidak dapat dibandingkan dan bukti tambahan kurang);
- status resmi suatu saluran tidak dapat dipastikan (bagian 2.1 butir 5);
- pasangan melibatkan tokoh lawan lembaga yang dipimpinnya, atau induk dan anak lembaga;
- tidak jelas apakah pasangan memakai bagian 4 (bagian 3);
- kasusnya tidak tercakup pedoman (kasus terbuka).

Penolakan karena ada unsur yang bertentangan **tidak** ditandai ragu hanya karena aturan 9. Ragu tidak mengubah label.
Label tetap ditetapkan dengan aturan terdekat. Metrik utama memakai label akhir semua butir, termasuk butir ragu; analisis
sensitivitas mengulang metrik tanpa butir ragu (rancangan A4.d).

## 8. Keterbatasan dan asal-usul (dicatat, bukan disembunyikan)

- **Aturan disusun setelah melihat data.** Aturan 1–8 berangkat dari 11 butir adjudikasi evaluasi eksternal, dan
  aturan 4 diubah dua kali setelah data dilihat (setelah analisis eksploratif P2-21, lalu karena bertentangan dengan
  aturan 3). Pembatasnya: semua perubahan terjadi sebelum set (a) dan (b) ada, dan pedoman dikunci sebelum pelabelan.
- **Bantuan AI saat menyusun pedoman.** Pemilik proyek memakai Claude (Anthropic) dalam diskusi saat mengisi lembar
  persetujuan dan saat memutuskan temuan konsistensi. Teks perubahan aturan 4, 5, 7, dan 9, catatan wajib, kapan
  bagian 4 dipakai, dan definisi unsur disusun bersama AI lalu disetujui pemilik proyek. Semua keputusan adalah
  keputusan pemilik proyek. Pernyataan lengkapnya ada di rancangan A6.3. **Label butir dibuat manusia tanpa AI**
  (aturan wajib #5).
- Aturan 9 condong ke "bukan klaim sama". Pada pasangan yang buktinya tipis, sistem yang menjawab "ditemukan" akan
  dihitung salah, walau pembaca lain bisa menilainya cocok.
- Verifikasi saluran resmi bergantung pada sumber acuan dan tanggal pemeriksaan; dua pelabel bisa memakai sumber
  acuan yang berbeda.

## 9. Hal yang belum diputuskan (wajib ditutup sebelum dikunci)

Rinciannya di rancangan A6.8 (usulan) dan A6.9 (temuan konsistensi kedua).

| Kode | Hal |
| --- | --- |
| K4 | Penyelesaian tiga titik tabrakan dengan v1.0: klaim lebih umum, keluarga artikel, jangkar KIA lawan Narasi (termasuk usulan uji Kesimpulan sebagai uji penolak) |
| K11 | Hubungan kolom `kekhususan` dan nilai `batas` v1.0 dengan tanda ragu |
| N1 | Pengumuman resmi tanpa saluran lawan artikel penipuan berlembaga dan bertawaran sama: menurut teks sekarang klaim sama |
| N2 | Sisi yang memakai saluran resmi bisa tetap hoaks; sisi yang memuat saluran resmi dan tidak resmi sekaligus |
| N3 | Ragu bisa membengkak karena pemendek URL dan nomor WhatsApp tidak dapat diverifikasi |
| N4 | Tindakan dan syarat (unsur v1.0) belum jelas berlaku pada pasangan bagian 4 |
| N5 | Nominal dengan peran berbeda (ditawarkan lawan diminta) |
| N6 | Verifikasi bergantung pada waktu dan akses internet anotator kedua |
| N7 | Tanda ragu siapa yang dipakai untuk analisis sensitivitas |
| N8 | Saluran resmi yang sama di kedua sisi dan arti "saluran sama persis" di aturan 9 |

## 10. Riwayat versi

| Versi | Tanggal | Perubahan |
| --- | --- | --- |
| 1.0 | 2026-09-21 | `testset/ANNOTATION_GUIDE.md`, dikunci sebelum set uji v1 dibuat. |
| 2.0 (draf) | 2026-10-27 | Aturan penipuan berulang 1–9, definisi periode, catatan wajib, tanda ragu. Belum dikunci. |
| 2.0 (draf, revisi 7) | 2026-10-27 | Nama "pola pendaftaran atau tawaran"; pengecualian saluran resmi dan cara verifikasinya; definisi nominal, jenis periode, lembaga umum, tokoh lawan lembaganya; aturan 3 dan 9 dirumuskan ulang; label kandidat tampil di lembar. Belum dikunci. |
