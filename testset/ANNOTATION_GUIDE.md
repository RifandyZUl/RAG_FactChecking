# Pedoman Anotasi "Klaim Sama" — Versi 1.0 (DIKUNCI)

**Status:** dikunci pada 2026-09-21, sebelum satu butir set uji v1 pun ditulis. Isi berkas ini diperiksa
oleh `tests/test_testset_locks.py` terhadap `GUIDE_LOCK.json`; mengubahnya tanpa memperbarui kunci dan
menaikkan versi membuat uji gagal.

**Aturan setelah dikunci.** Pedoman TIDAK boleh direvisi selama pembuatan set uji v1. Bila ditemukan kasus
yang tidak tercakup: (1) catat sebagai *kasus terbuka* di `testset/kasus_terbuka.md` (butir, klaim, artikel,
alasan tidak tercakup), (2) putuskan dengan aturan yang paling dekat, (3) beri butir itu `kekhususan=batas`,
(4) jangan merevisi pedoman di tengah jalan. Perubahan pedoman hanya untuk set uji BARU (v2), dengan versi
baru dan kunci baru.

## 1. Tujuan

Menetapkan kapan klaim pengguna dianggap **sama** dengan sebuah artikel TurnBackHoax, agar label set uji
tidak mencampur kesalahan sistem dengan ketidaksepakatan definisi. Definisi yang sama tertulis di dalam
prompt sistem generator (aturan 2 dan 3).

## 2. Definisi

- **Klaim inti artikel (KIA)** = judul artikel tanpa label (mis. `[SALAH] Ojol Dilarang Beli Pertalite` ->
  "Ojol Dilarang Beli Pertalite"). Pada 123 dari 150 artikel, kalimat penutup Kesimpulan mengutip klaim
  yang sama ("Jadi, unggahan berisi klaim “…” adalah…"), dengan kemiripan terhadap judul median 1,0.
  Untuk artikel tanpa kutipan, anotator menulis KIA satu kalimat SEBELUM menulis kueri apa pun untuk artikel
  itu, disimpan di kolom `klaim_inti`.
- **Unsur inti**: (a) subjek atau aktor; (b) tindakan, peristiwa, atau pernyataan; (c) objek atau kondisi
  pembeda (mis. jenis vaksin, sasaran, jenis bantuan).
- **Unsur perifer** (diabaikan saat menilai): nama akun dan platform, tanggal unggah, jumlah tayangan atau
  suka, komentar pengunggah, gaya bahasa, dan bentuk pertanyaan ("benar nggak sih?").

## 3. Aturan keputusan

Klaim pengguna **SAMA** dengan artikel bila lolos **kedua** uji:

1. **Uji dua arah**: bila klaim pengguna benar, KIA pasti benar, dan sebaliknya, pada ketiga unsur inti.
   Perbedaan hanya boleh pada unsur perifer atau sinonim sehari-hari.
2. **Uji Kesimpulan**: kalimat "Faktanya…" pada Kesimpulan, dibaca sebagai jawaban, langsung menjawab klaim
   pengguna tanpa penyesuaian.

Selain itu, **TIDAK SAMA**. Kemiripan topik atau tema bukan kesamaan klaim.

## 4. Kasus khusus

| Kasus | Keputusan | Catatan |
| --- | --- | --- |
| Lebih **umum** (unsur inti dilemahkan atau dihilangkan) | TIDAK SAMA | `kekhususan=umum`; tipe negatif sulit |
| Lebih **spesifik**, tambahan hanya perifer atau sudah ada di Narasi | SAMA | `spesifik_perifer` |
| Lebih spesifik, menambah atau mengubah unsur inti (subjek, tindakan, objek pembeda) | TIDAK SAMA | `spesifik_inti` |
| **Sebagian** isi hoaks, yang disebut adalah KIA | SAMA | `sebagian_inti` |
| Sebagian isi hoaks, yang disebut hanya bagian pendukung atau perifer | TIDAK SAMA | `sebagian_perifer` |
| Sinonim sehari-hari (bahasa santai, singkatan, salah ketik) | SAMA | `sinonim` |
| Istilah berbeda secara faktual (mis. "impoten" vs "mandul") | putuskan dengan uji Kesimpulan; catat alasan | `batas` |
| Bentuk pertanyaan | diperlakukan sama dengan pernyataan | — |
| Negasi atau kebalikan klaim (mis. "ojol boleh isi Pertalite") | tidak dipakai; dikeluarkan dari set | — |
| Cocok dengan lebih dari satu artikel tanpa unsur pembeda (keluarga tautan pendaftaran bantuan) | TIDAK SAMA; `ambigu`; dikeluarkan atau diberi `expected_alt` | — |
| Pesan berantai berisi beberapa klaim | SAMA bila KIA adalah salah satu klaim utamanya dan tidak dibantah pesan itu sendiri | catat di `catatan` |

**Kolom `kekhususan`** (wajib per butir): `setara`, `umum`, `spesifik_perifer`, `spesifik_inti`,
`sebagian_inti`, `sebagian_perifer`, `sinonim`, `ambigu`, `batas`. Hasil dilaporkan total dan tanpa butir
`batas`, serta per nilai `kekhususan`.

## 5. Prosedur anotasi

1. Tetapkan KIA setiap artikel (judul; kutipan Kesimpulan bila ada; tulis sendiri bila tidak ada) sebelum
   menulis atau menyetujui kueri untuk artikel itu.
2. Tetapkan label dan `kekhususan` SEBELUM sistem dijalankan pada butir itu; jangan melihat keluaran sistem.
3. Butir tidak boleh dipilih atau dibuang berdasarkan keluaran sistem.
4. Setiap butir `batas` dicatat beserta alasan dan aturan terdekat yang dipakai.
5. Konsistensi dalam-anotator: setelah satu minggu, anotasi ulang 10 butir acak tanpa melihat label lama.

## 6. Contoh berpasangan

Semua diambil dari enam artikel yang dikecualikan dari target set uji (36730, 36214, 36729, 36737, 36738,
36731), sehingga tidak ada kebocoran. ★ = kasus perbatasan.

| Artikel (KIA) | SAMA | TIDAK SAMA |
| --- | --- | --- |
| 36730 "Ojol Dilarang Beli Pertalite" | "katanya ojol nggak boleh isi pertalite lagi ya?" (parafrase, pertanyaan) | "Pertalite mau dibatasi untuk kendaraan tertentu" (lebih umum) |
| 36214 "Vaksin HPV Bikin Anak Laki-Laki Impoten" | ★ "vaksin HPV bikin cowok mandul katanya" (impoten ≠ mandul secara medis, tetapi Kesimpulan — "melindungi … kesuburan … laki-laki dan perempuan" — menjawab keduanya) | "vaksin flu bikin laki-laki mandul" (jenis vaksin berbeda); "vaksin HPV sebabkan HIV" (artikel lain) |
| 36729 "Malaysia Laporkan Indonesia ke PBB soal Karhutla" | "Malaysia lapor ke PBB gara-gara asap kebakaran hutan Indonesia" | ★ "Malaysia marah ke Indonesia soal asap" (lebih umum: tindakan inti "melaporkan ke PBB" tidak ada; Kesimpulan tidak menjawab apakah Malaysia marah); "Singapura laporkan Indonesia ke PBB soal karhutla" (subjek berbeda) |
| 36737 "Tautan Pendaftaran Program Bantuan Lansia" | ★ "ada link pendaftaran bantuan buat lansia, beneran?" ("orang tua" ambigu; butuh pembeda "lansia") | "link daftar bantuan beras 30 kg" (artikel lain); "ada link daftar bantuan sosial, asli nggak?" (ambigu: cocok banyak artikel) |
| 36738 "Ada Kebijakan Razia Kendaraan dari Rumah ke Rumah" | "pengumuman razia kendaraan pajak mati sampai ke rumah warga akhir September" (tanggal perifer) | "razia kendaraan nunggak pajak di jalan raya" (unsur inti "rumah ke rumah" hilang); "kendaraan over-kredit ilegal akan disita" (sebagian perifer) |
| 36731 "Tautan Pendaftaran Cek Kesehatan Gratis" | "daftar cek kesehatan gratis lewat link yang beredar, asli gak sih?" | "cek kesehatan gratis itu agenda plandemi" (program sama, klaim berbeda) |

## 7. Keterbatasan (dicatat, bukan disembunyikan)

- **Satu anotator manusia.** Kesepakatan antar-anotator tidak terukur; hanya konsistensi dalam-anotator
  (langkah 5.5) yang dapat diperiksa. Label set uji mencerminkan satu penafsiran atas pedoman ini.
- **Pedoman ditulis setelah melihat keluaran model pada set pengembangan** (khususnya kueri "Malaysia
  marah soal asap"). Ini berisiko rasionalisasi. Pembatasnya: jangkar KIA adalah teks yang sudah ada
  sebelumnya (judul dan kutipan Kesimpulan yang ditulis pengarsip cek fakta), aturannya mekanis, dan
  pedoman dikunci sebelum butir set uji ditulis.
- KIA berasal dari judul artikel; judul yang terlalu singkat atau tidak lazim dapat menyempitkan atau
  melebarkan klaim inti. Kasus seperti itu dicatat sebagai `batas`.
- Pedoman menetapkan bahwa klaim yang lebih umum "belum ditemukan" walau ada artikel terkait. Ini pilihan
  desain Versi 1 (Aturan Wajib #4); artikel terkait sebagai verdict tersendiri adalah kandidat Versi 2.

## 8. Riwayat versi

| Versi | Tanggal | Perubahan |
| --- | --- | --- |
| 1.0 | 2026-09-21 | Versi awal, dikunci sebelum set uji v1 dibuat. |
