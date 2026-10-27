# Pedoman Anotasi "Klaim Sama" — Versi 2.0 (DRAF, BELUM DIKUNCI)

**Status:** draf 2026-10-27, disusun dari lembar persetujuan pedoman A6 dan jawaban pemilik proyek
(`docs/rancangan/rancangan_v2.md` A6). **Belum boleh dipakai untuk melabeli butir apa pun.** Sebelum dikunci, hal
yang belum diputuskan di bagian 9 harus ditutup pemilik proyek, lalu pedoman ini dikunci lewat tag
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
bukan penipuan. Versi 2.0 menambah aturan khusus untuk **penipuan berulang**: tautan pendaftaran, lowongan, bantuan,
dan pesan sejenis yang beredar berkali-kali dengan lembaga, tautan, atau tanggal yang berganti.

Semua contoh di pedoman ini **rekaan**: lembaga, program, tautan, nomor, dan nominalnya dikarang dan tidak mengacu
pada artikel, pesan, atau butir uji mana pun. Domain berakhiran `.example` dan nomor `0800-0000-…` sengaja tidak
nyata.

## 2. Definisi

- **Butir:** satu pesan beserta daftar artikel kandidat.
- **Pasangan:** satu pesan dengan satu artikel kandidat. Keputusan "klaim sama" dibuat per pasangan.
- **Unsur inti (pedoman v1.0):** subjek atau aktor; tindakan, peristiwa, atau pernyataan; objek atau kondisi pembeda.
- **Unsur inti penipuan:** lembaga atau tokoh yang dicatut, tawaran (jenis program atau keuntungan), dan saluran
  (tautan atau nomor). Nominal dan periode juga dibandingkan (aturan 3, 4, dan 9).
- **Periode:** tahun, atau nama gelombang atau tahap program (misalnya "Gelombang 2", "Tahap II"). **Tanggal batas
  pendaftaran dan tanggal hari tidak termasuk**, karena penipuan daur ulang hampir selalu memperbarui tanggalnya.
  Tanggal yang berbeda tetap dicatat di catatan wajib.
- **Status unsur:**
  - **sama:** disebut di kedua sisi dan sama;
  - **bertentangan:** disebut eksplisit di kedua sisi dan berbeda;
  - **tidak dapat dibandingkan:** hanya disebut di satu sisi, tidak disebut di kedua sisi, atau istilah umum
    berhadapan dengan program spesifik (aturan 8).
- **Ragu:** tanda bahwa keputusan sebuah pasangan atau butir tidak pasti menurut pedoman. Ragu tidak mengubah label
  (bagian 7).

## 3. Kapan aturan penipuan dipakai

Ditentukan **per pasangan pesan–artikel**. Sebuah pasangan memakai aturan penipuan (bagian 4) bila:

- (a) artikelnya berlabel **PENIPUAN** di TurnBackHoax, **atau**
- (b) pesannya meminta pembaca mendaftar, mengisi data pribadi, mentransfer uang, atau menghubungi tautan atau nomor
  atas nama lembaga atau tokoh.

Pasangan lain memakai pedoman v1.0 (klaim inti, unsur inti, uji dua arah, uji Kesimpulan). Dalam satu butir, pasangan
yang berbeda bisa memakai aturan yang berbeda. Bila ragu apakah sebuah pasangan termasuk penipuan, catat keraguannya
dan alasan memilih aturan yang dipakai.

## 4. Aturan 1–9 (pasangan penipuan)

Isi aturan sama dengan rancangan A6 (rujukan ke nomor keputusan rancangan dihilangkan). Setiap aturan diberi satu
contoh rekaan.

**Aturan 1. Lembaga atau tokoh berbeda, tawaran sama -> BUKAN klaim sama.**

> Pesan: "Pendaftaran Bantuan Modal Usaha dari Badan Beasiswa Rekaan, daftar di bantuan-bbr.example."
> Artikel: tautan pendaftaran Bantuan Modal Usaha atas nama Kementerian Kesejahteraan Contoh (KKC).
> Lembaga bertentangan, tawaran sama -> **BUKAN klaim sama.**

**Aturan 2. Lembaga atau tokoh tidak disebut di salah satu sisi -> tidak dapat dibandingkan, bukan pertentangan.**
Keputusan bergantung pada unsur inti lain.

> Pesan: "Ada Bantuan Modal Usaha Rp2 juta, daftar lewat bantuan-umkm.example." (tanpa lembaga)
> Artikel: tautan pendaftaran Bantuan Modal Usaha Rp2 juta atas nama KKC.
> Lembaga tidak dapat dibandingkan; tawaran sama; nominal sama; tidak ada yang bertentangan -> **klaim sama**
> (aturan 9, kalimat pertama).

**Aturan 3. Gelombang berbeda (tahun atau tanggal berbeda), lembaga dan tawaran sama -> klaim sama, kecuali tahun
atau periode disebut eksplisit di kedua sisi dan berbeda** (Aturan A evaluasi eksternal).

> Pesan: "Rekrutmen Petugas Lapangan PT Energi Fiktif 2027, daftar di sini." Artikel (terbit setahun sebelumnya):
> rekrutmen Petugas Lapangan PT Energi Fiktif, tanpa tahun di Narasi.
> Tahun hanya di satu sisi -> **klaim sama.**
> Bila Narasi artikel menyebut "Rekrutmen … 2026": tahun eksplisit di kedua sisi dan berbeda -> **BUKAN klaim
> sama.** Tanggal penutupan yang berbeda (misalnya 10 Januari dan 3 Maret) bukan periode, hanya dicatat.

**Aturan 4. Nominal berbeda pada tawaran yang sama -> BUKAN klaim sama bila nominal disebut eksplisit di kedua sisi.**
Ini berlaku juga bila gelombangnya terlihat berbeda dari tanggal terbit. Bila tahun atau periode disebut eksplisit di
kedua sisi dan berbeda, butir sudah bukan klaim sama menurut aturan 3, apa pun nominalnya. Bila hanya satu sisi
menyebut nominal: tidak dapat dibandingkan.

> Pesan: "Bantuan Modal Usaha KKC Rp5 juta." Artikel (terbit empat bulan sebelumnya): Bantuan Modal Usaha KKC
> Rp2 juta.
> Nominal bertentangan -> **BUKAN klaim sama**, walau jarak terbitnya menandakan gelombang lain.
> Bila pesan tidak menyebut nominal: nominal tidak dapat dibandingkan, dan keputusan bergantung pada unsur lain.

**Aturan 5. Tautan atau nomor berbeda, lembaga dan tawaran sama -> klaim sama.** Penipu sering berganti tautan.
Tautan atau nomor yang sama persis dengan sumber hoaks di artikel adalah bukti pendukung yang kuat, tetapi bukan
syarat.

> Pesan: Bantuan Modal Usaha KKC lewat daftar-kkc.example. Artikel: Bantuan Modal Usaha KKC lewat
> bantuan-kkc.example dan nomor 0800-0000-0001.
> Saluran berbeda, lembaga dan tawaran sama -> **klaim sama.**

**Aturan 6. Judul sama, isi tawaran berbeda -> BUKAN klaim sama.** Yang dibandingkan adalah isi pesan dengan Narasi,
bukan judul dengan judul.

> Judul artikel: "Tautan Pendaftaran Bantuan KKC"; Narasinya tentang paket sembako. Pesan berjudul sama persis,
> tetapi isinya Bantuan Modal Usaha.
> Tawaran bertentangan -> **BUKAN klaim sama.**

**Aturan 7. Bila lebih dari satu artikel cocok dengan pesan (lembaga dan tawaran sama), semua artikel yang sah dicatat,
dan jawaban dinilai benar bila memilih salah satunya.** Sebuah artikel hanya sah bila, terhadap pesan itu, ia lolos
semua aturan lain (aturan 1–6, 8, dan 9): tidak ada pertentangan tahun atau periode yang eksplisit (aturan 3), dan
tidak ada pertentangan nominal yang eksplisit (aturan 4).

> Pesan: Beasiswa Cendekia Rekaan dari Badan Beasiswa Rekaan, tanpa tahun dan nominal. Dua artikel: satu terbit
> 2025 dan satu 2026, keduanya Beasiswa Cendekia Rekaan dari lembaga yang sama, tanpa tahun di Narasi.
> Keduanya sah -> keduanya dicatat; label positif.
> Bila pesan menyebut "2026" dan Narasi artikel pertama menyebut "2025": artikel pertama tidak sah (aturan 3), hanya
> artikel kedua yang dicatat.

**Aturan 8. Tawaran berbeda (program spesifik berbeda) -> BUKAN klaim sama.** Istilah umum ("bansos", "bantuan",
"lowongan") dibandingkan dengan program spesifik dihitung tidak dapat dibandingkan.

> Pesan: Bantuan Modal Usaha KKC. Artikel: Bantuan Paket Sembako KKC.
> Tawaran bertentangan -> **BUKAN klaim sama.**
> Bila pesan hanya menyebut "bantuan dari KKC": tawaran tidak dapat dibandingkan -> lanjut ke aturan 9.

**Aturan 9 (aturan bawaan). Klaim sama membutuhkan tawaran yang sama dan tidak ada unsur inti yang bertentangan. Bila
tawaran tidak dapat dibandingkan, klaim sama hanya bila lembaga atau tokoh sama dan setidaknya satu unsur lain
(saluran, nominal, atau periode) sama. Selain itu: bukan klaim sama, dan butir ditandai ragu.**

Alasan aturan ini: aturan 1–8 berangkat dari "lembaga dan tawaran sama", sehingga tidak ada keputusan ketika tawaran
tidak dapat dibandingkan. Di celah itulah keputusan "narasi sama" dulu muncul. Aturan ini sengaja condong ke "bukan
klaim sama" ketika buktinya kurang.

> Pesan: "Bantuan dari KKC, daftar di bantuan-kkc.example." Artikel: Bantuan Modal Usaha KKC, sumber hoaksnya
> bantuan-kkc.example.
> Tawaran tidak dapat dibandingkan; lembaga sama; saluran sama persis -> **klaim sama.**
> Bila tautannya berbeda dan tidak ada nominal atau periode yang sama -> **BUKAN klaim sama, ragu.**

**Hubungan induk dan anak lembaga** (misalnya sebuah BUMN dan anak perusahaannya) belum diatur. Pasangan seperti itu
ditandai ragu dan dicatat.

## 5. Urutan langkah menilai satu butir

Urutan ini adalah cara kerja, bukan aturan baru. Bila urutan dan aturan berbeda, aturan di bagian 4 yang berlaku.

1. Baca pesan. Jangan melihat keluaran sistem, skor retrieval, atau label orang lain.
2. Untuk setiap artikel kandidat, tentukan apakah pasangannya memakai aturan penipuan (bagian 3). Bila tidak, nilai
   dengan pedoman v1.0 dan lanjut ke kandidat berikutnya.
3. Untuk pasangan penipuan, isi unsur di kedua sisi beserta statusnya (bagian 6). Bandingkan isi pesan dengan
   **Narasi** artikel, bukan judul dengan judul (aturan 6).
4. Periksa unsur yang bertentangan: lembaga atau tokoh (aturan 1), tawaran (aturan 6 dan 8), tahun atau periode
   (aturan 3), dan nominal (aturan 4). Bila ada yang bertentangan: **BUKAN klaim sama.**
5. Bila tidak ada yang bertentangan:
   - tawaran sama -> **klaim sama** (aturan 9, kalimat pertama; aturan 2, 3, dan 5 menjelaskan unsur yang boleh
     berbeda atau tidak disebut);
   - tawaran tidak dapat dibandingkan -> pakai aturan 9, kalimat kedua dan ketiga.
6. Bila lebih dari satu artikel sah, catat semuanya (aturan 7).
7. Label butir: **positif** bila setidaknya satu artikel sah, dengan daftar semua artikel yang sah; **negatif** bila
   tidak ada. Isi catatan wajib dan tanda ragu.

## 6. Cara mengisi catatan wajib

Setiap label pada pasangan penipuan, **positif maupun negatif**, wajib mencatat lembaga atau tokoh, tawaran, saluran,
nominal, dan tahun atau periode di kedua sisi, beserta statusnya (sama, bertentangan, tidak dapat dibandingkan).
Tanggal yang berbeda tetap dicatat.

Untuk label negatif, catatan dibuat pada **kandidat yang paling mirip menurut penilaian anotator** (tanpa skor
retrieval): sebutkan minimal satu unsur yang bertentangan dan aturan yang dipakai. Bila tidak ada unsur yang
bertentangan, tulis alasannya secara eksplisit (misalnya "aturan 9: tawaran tidak dapat dibandingkan, lembaga tidak
disebut").

Bentuk yang disarankan, satu baris per pasangan (pesan | artikel | status):

```
artikel <id>; lembaga: KKC | KKC | sama; tawaran: bantuan | Bantuan Modal Usaha | tidak dapat dibandingkan;
saluran: bantuan-kkc.example | bantuan-kkc.example | sama; nominal: - | Rp2 juta | tidak dapat dibandingkan;
periode: - | - | tidak dapat dibandingkan; tanggal: 10 Jan | 3 Mar | dicatat; aturan: 9; putusan: SAMA; ragu: -
```

Catatan seperti "narasi sama" atau "konteks sama" tanpa menyebut unsur yang dibandingkan **tidak memenuhi** catatan
wajib.

## 7. Cara menandai ragu

Tandai **ragu** dan tulis alasannya (dengan aturan terdekat yang dipakai) bila:

- aturan 9 berakhir pada "bukan klaim sama" karena buktinya kurang;
- pasangan melibatkan induk dan anak lembaga;
- tidak jelas apakah pasangan termasuk penipuan (bagian 3);
- kasusnya tidak tercakup pedoman (kasus terbuka).

Ragu tidak mengubah label. Label tetap ditetapkan dengan aturan terdekat. Cara butir ragu dipakai dalam metrik
ditetapkan di `testset/v2.meta.json` sebelum evaluasi (bagian 9, butir K13).

## 8. Keterbatasan dan asal-usul (dicatat, bukan disembunyikan)

- **Aturan disusun setelah melihat data.** Aturan 1–8 berangkat dari 11 butir adjudikasi evaluasi eksternal, dan
  aturan 4 diubah dua kali setelah data dilihat (setelah analisis eksploratif P2-21, lalu karena bertentangan dengan
  aturan 3). Pembatasnya: semua perubahan terjadi sebelum set (a) dan (b) ada, dan pedoman dikunci sebelum pelabelan.
- **Bantuan AI saat menyusun pedoman.** Pemilik proyek memakai Claude (Anthropic) dalam diskusi saat mengisi lembar
  persetujuan. Teks perubahan aturan 4 dan 7, catatan wajib, cakupan pedoman v1.0, aturan 9, dan klarifikasi periode
  disusun bersama AI lalu disetujui pemilik proyek. Semua keputusan setuju atau ubah adalah keputusan pemilik proyek.
  Pernyataan lengkapnya ada di rancangan A6.3. **Label butir dibuat manusia tanpa AI** (aturan wajib #5).
- Aturan 9 condong ke "bukan klaim sama". Pada pasangan yang buktinya tipis, sistem yang menjawab "ditemukan" akan
  dihitung salah, walau pembaca lain bisa menilainya cocok.

## 9. Hal yang belum diputuskan (wajib ditutup sebelum dikunci)

Rinciannya di rancangan A6.4. Ringkasnya:

| Kode | Hal |
| --- | --- |
| K1 | Pesan resmi yang benar (set a) bisa memenuhi bagian 3 (b), lalu dinilai klaim sama dengan artikel penipuan lewat aturan 5 |
| K2 | Jangkauan "selain itu … ditandai ragu" di aturan 9 |
| K3 | Saluran berbeda: aturan 5 (tidak menolak) dan aturan 9 ("tidak ada unsur inti yang bertentangan") |
| K4 | Urutan prioritas pedoman 2.0 dan v1.0 pada pasangan penipuan (lebih umum, keluarga artikel, KIA atau Narasi) |
| K5 | Nominal dan periode: unsur inti atau bukan, dalam kalimat pertama aturan 9 |
| K6 | Periode berbeda jenis (tahun di satu sisi, nama gelombang di sisi lain) |
| K7 | Definisi nominal |
| K8 | Lembaga umum ("pemerintah") |
| K9 | Tokoh dan lembaga yang dipimpinnya |
| K10 | Label TurnBackHoax harus terlihat di lembar pelabelan agar bagian 3 (a) bisa dipakai |
| K11 | Kolom `kekhususan` dan nilai `batas` v1.0 pada set Versi 2 |
| K12 | Kata "tahun atau tanggal berbeda" di aturan 3 |
| K13 | Pemakaian butir ragu dalam metrik |

## 10. Riwayat versi

| Versi | Tanggal | Perubahan |
| --- | --- | --- |
| 1.0 | 2026-09-21 | `testset/ANNOTATION_GUIDE.md`, dikunci sebelum set uji v1 dibuat. |
| 2.0 (draf) | 2026-10-27 | Aturan penipuan berulang 1–9, definisi periode, catatan wajib, tanda ragu. Belum dikunci. |
