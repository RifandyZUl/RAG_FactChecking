# Rancangan pembaruan berkala

Status: **usulan rancangan, belum dibangun.** Bagian "Usulan" di bawah adalah salinan persis usulan
Claude Code pada 2026-10-03 (akhir tahap perluasan basis data). Persetujuan dan tambahan pemilik
proyek dicatat di bagian sesudahnya.

## Usulan rancangan pembaruan berkala (belum dikerjakan)

**Penjadwalan.**
- Satu skrip pembungkus yang dijalankan Task Scheduler sekali sehari, di jam Anda biasanya tidak memakai laptop.
- Skrip memakai Python venv dengan jalur lengkap dan direktori kerja di root proyek.
- Hanya satu instans yang boleh berjalan (berkas kunci), dan ada batas waktu total.
- Tugas dijalankan hanya bila jaringan tersedia dan laptop terhubung ke listrik, tanpa "jalankan ulang bila terlewat" yang menumpuk.

**Dua tahap terpisah.**
- *Scraping (ringan, harian):* mode maju, lalu reparse dan pemeriksaan kualitas (seksi kosong, label tak dikenal, tumpang tindih, URL tidak sah). Hasilnya masuk antrean, belum digabung.
- *Ingest (berat):* tidak ikut jadwal harian. Saran saya dijalankan manual, atau terjadwal mingguan dengan syarat memori. Urutannya: cadangan, gabung ke `articles.json`, ingest inkremental, `index_check` lengkap.

**Kegagalan tanpa pengawas.**
- Pemutus sirkuit yang sudah ada dipakai apa adanya: kode keluar 4, tidak ada berkas yang ditulis, dan jalan berikutnya mengulang dari cache.
- Kode keluar dicatat dari proses Python sendiri ke berkas status per jalan, bukan dari pembungkusnya.
- Setelah beberapa jalan gagal beruntun (misalnya tiga), skrip berhenti mencoba dan meninggalkan penanda yang terlihat.
- Dua celah wajib ditutup dulu, karena mode maju tidak akan pernah menjangkau artikel yang gagal: jalan yang selesai dengan kegagalan non-jaringan tidak boleh memajukan batas "sudah dimiliki", dan artikel gagal perlu langkah coba-ulang dari `failed_ids.json` (agenda (b)).
- Label baru dan judul `TIDAK DIKETAHUI` menahan penggabungan sampai Anda tinjau.

**Konsistensi tiap data bertambah.**
- *Manifest:* diperbarui otomatis hanya bila pemeriksaan data pribadi pada judul bersih; judul yang ditandai menahan pembaruan.
- *"Mungkin terkait":* tetap mati. Karena ambang skor gagal secara struktural, tidak ada kalibrasi ulang yang dijadwalkan sampai diganti di Versi 2.
- *Rujukan:* aturan penyaringan diterapkan saat parse; bila aturannya berubah, pembaruan metadata terarah dijalankan sebelum ingest.
- *Catatan cakupan* di README dan demo memuat jumlah artikel dan angka pencarian, jadi harus ikut diperbarui, atau diubah menjadi kalimat yang tidak menyebut angka.
- *Pemeriksaan pencarian:* perbandingan retriever lawan eksak pada set kueri tetap dijalankan setelah tiap ingest.

**Risiko.**
- *Memori (terbesar):* proses kita dihentikan sistem tiga kali. Ingest memuat model yang menekan memori tersedia hingga di bawah 1 GB. Tanpa pengawas, ingest bisa mati di tengah. Chunk tersimpan bertahap sehingga aman dilanjutkan, tetapi indeks sementara tidak cocok dengan `articles.json`. Mitigasinya: ingest hanya dimulai bila memori tersedia cukup (misalnya 3 GB), pemantau memori yang berhenti rapi seperti yang dipakai hari ini, dan `articles.json` baru diganti setelah `index_check` lolos.
- *Demo terbuka saat ingest:* dua proses membuka indeks yang sama, dan berkas indeks ditulis ulang tiap dibuka. Ingest sebaiknya menolak berjalan bila demo aktif.
- *Laptop mati atau tidur di tengah jalan:* cadangan sebelum ingest menjadi satu-satunya jalan pulih, dan ukurannya bertambah tiap kali; perlu aturan berapa cadangan yang disimpan.
- *Perubahan di sumber:* artikel yang sudah diambil tidak disegarkan, dan perubahan struktur HTML bisa membuat semua artikel gagal di-parse. Jenis kegagalan `galat_kode` kini membuat hal itu terlihat di laporan, tetapi tidak ada yang membacanya tanpa pemberitahuan.
- *Mutu pencarian turun diam-diam* seiring indeks membesar, seperti pada v1-048, kecuali pemeriksaan pencarian di atas dijalankan.
- *Label negatif set uji v1* makin sering tidak berlaku pada indeks produksi; evaluasi pembanding tetap wajib lewat `archive/v1`.

Keputusan untuk Anda sebelum ini dibangun: apakah ingest boleh terjadwal atau tetap manual. Saya menyarankan manual, karena memori di mesin ini belum bisa diandalkan tanpa pengawas.

---

## Keputusan pemilik proyek (2026-10-03)

Rancangan di atas **disetujui**, dengan ketentuan berikut. Bagian ini mengalahkan usulan di atas
bila keduanya berbeda.

**Ingest tetap MANUAL.** Tidak dijadwalkan; pemilik proyek yang memulainya setelah memastikan
memori cukup.

**Enam tambahan.**

1. **Dua celah prasyarat dikerjakan lebih dulu, sebelum menyentuh penjadwalan**, lengkap dengan uji:
   (a) jalan yang selesai dengan kegagalan non-jaringan tidak boleh memajukan batas "sudah
   dimiliki"; (b) langkah coba-ulang dari `failed_ids.json`.
2. **Pemberitahuan.** Kegagalan harus sampai ke pemilik proyek tanpa membuka berkas status. Cara
   paling sederhana yang diusulkan (belum dibangun): notifikasi Windows saat jalan gagal, dan/atau
   ringkasan yang muncul saat proyek dibuka.
3. **Jadwal yang terlewat karena laptop tertidur dijalankan sekali begitu laptop menyala, bukan
   dilewati.** Ini menggantikan butir "tanpa 'jalankan ulang bila terlewat' yang menumpuk" pada
   usulan. Mode maju aman untuk itu karena berhenti di artikel pertama yang sudah dimiliki; yang
   dijaga hanya agar tidak ada dua jalan bersamaan (berkas kunci).
4. **Cadangan: simpan tiga yang terakhir saja**, dan laporkan perkiraan ukurannya.
5. **Catatan cakupan demo: angkanya JANGAN dihapus.** Angka recall adalah hasil pengukuran pada
   indeks tertentu, jadi ditulis bersama tanggal dan ukuran indeks saat diukur; jumlah artikel yang
   sedang dipakai ditampilkan otomatis dari indeks. Ini menggantikan pilihan "diubah menjadi kalimat
   yang tidak menyebut angka" pada usulan.
6. **Lapisan pengambilan data dibuat bisa diganti**, karena permintaan API key Yudistira masih
   menunggu jawaban. Integrasi API-nya TIDAK dibangun sekarang.

**Urutan pengerjaan yang ditetapkan:** (1) rancangan ini disimpan; (2) perbaikan `ef_search` di indeks
produksi dan alat pemeriksaan retriever lawan pencarian eksak; (3) dua celah prasyarat (butir 1);
laporan; baru kemudian penjadwalan.

---

## Kemajuan dan usulan lanjutan (2026-10-03)

**Butir 1 (dua celah prasyarat): SELESAI**, di `src/scraping/expand.py`, uji di `tests/test_expand.py`.

- *Jalan dengan kegagalan tidak memajukan batas "sudah dimiliki".* Selama masih ada kegagalan yang
  bisa dicoba lagi, jalan DITAHAN: berkas artikel tidak ditulis dan `state.json` tidak diubah, sehingga
  perintah yang sama mengulang seluruhnya (yang sudah berhasil terbaca dari cache). Berlaku untuk
  mode mundur dan mode maju. Aturannya:
  - kegagalan sistematis (>= 2 artikel gagal dan tingkat gagal > 5%): ditahan, kode keluar 3, sampai
    manusia turun tangan (memperbaiki penyebabnya, atau `--accept-failures`);
  - masih ada kegagalan yang bisa dicoba lagi: ditahan, kode keluar 5;
  - semua kegagalan permanen (HTTP 404/410, atau sudah gagal 3 kali antar-jalan): ditulis dan batas
    maju, kode keluar 6, artikelnya ditandai "perlu tinjauan".
- *Coba ulang dari `failed_ids.json`:* `python -m scraping.expand --retry-failed` mengambil ulang
  kegagalan terbuka langsung dari URL tersimpannya; hasil ke `data/expansion/retry_YYYY-MM-DD.json`
  (terhitung "dimiliki"); `--include-permanent` untuk yang perlu tinjauan, setelah penyebabnya
  diperbaiki. `--failed-status` kini memisahkan `id_bisa_dicoba_ulang` dari `id_perlu_tinjauan`.
- Kode keluar proses Python: 0 bersih | 3 ditahan (sistematis) | 4 jaringan putus | 5 ditahan (akan
  dicoba lagi) | 6 ditulis, ada yang perlu ditinjau. Pembungkus terjadwal cukup membaca kode ini.

**Butir 2 (pemberitahuan) -- usulan, belum dibangun.** Dua lapis, tanpa memasang apa pun:

1. *Berkas penanda di root proyek*, mis. `PERHATIAN_PEMBARUAN.txt`, ditulis pembungkus setiap kali
   jalan berakhir dengan kode selain 0 (isi: waktu, kode keluar dan artinya, jumlah gagal per jenis,
   jalur laporan), dan DIHAPUS pada jalan bersih berikutnya. Terlihat begitu proyek dibuka di IDE
   atau `git status` dijalankan (berkasnya di-gitignore). Ini lapis yang tidak bisa terlewat.
2. *Notifikasi Windows (toast)* dari pembungkus lewat PowerShell bawaan
   (`Windows.UI.Notifications`), hanya saat gagal dan saat ada artikel yang perlu ditinjau. Bisa
   terlewat bila laptop sedang tidak dipakai, karena itu bukan satu-satunya lapis.

Tambahan murah: setelah tiga jalan gagal beruntun, penanda menyebut bahwa pembaruan berhenti mencoba.

**Butir 4 (cadangan) -- perkiraan ukuran.** Satu cadangan = `data/chroma` + `articles.json`. Pada
indeks 1.532 artikel: sekitar 54 MB (indeks 49 MB, `articles.json` 5 MB). Tiga cadangan terakhir:
sekitar 160 MB sekarang; bertambah kira-kira 35 MB per 1.000 artikel per cadangan. Saat ini ada empat
cadangan (29 + 36 + 35 + 54 = 154 MB); belum ada yang dihapus -- aturan "tiga terakhir" berlaku
untuk cadangan otomatis yang akan dibangun, dan penghapusan cadangan lama menunggu perintah pemilik
proyek.

**Yang belum dikerjakan:** penjadwalan (Task Scheduler, jalankan sekali saat menyala bila terlewat),
pembungkus dan pemberitahuan, rotasi cadangan, catatan cakupan demo dengan jumlah artikel otomatis,
dan lapisan pengambilan data yang bisa diganti. Menunggu laporan ini ditinjau.

---

## Kemajuan 2026-10-03 (malam): pembungkus dibangun dan diuji manual; BELUM didaftarkan ke Task Scheduler

**Keputusan pemilik proyek atas laporan sebelumnya:** aturan menahan dan angka tiga percobaan disetujui,
dengan satu perubahan -- **kegagalan jaringan tidak dihitung** ke batas tiga kali antar-jalan (internet
mati beberapa hari tidak boleh membuat artikel sehat ditandai permanen); pemberitahuan dua lapis
disetujui; cadangan lama tidak dihapus tanpa keputusan pemilik proyek.

**Status keenam tambahan:**

| # | Tambahan | Status |
| --- | --- | --- |
| 1 | Dua celah prasyarat | Selesai (`expand.py`); hitungan percobaan hanya non-jaringan |
| 2 | Pemberitahuan dua lapis | Selesai (`scraping.scheduled`): `PERHATIAN_PEMBARUAN.txt` di root proyek + notifikasi Windows |
| 3 | Jadwal terlewat dijalankan sekali saat menyala | Didukung pembungkus (jalan kedua di hari yang sama tidak mengambil ulang); setelan Task Scheduler-nya (`StartWhenAvailable`) menunggu pendaftaran |
| 4 | Cadangan: simpan tiga terakhir | BELUM dibangun (cadangan hanya dibuat saat ingest, yang manual); cadangan yang ada tidak dihapus |
| 5 | Catatan cakupan demo | Selesai: tanggal dan ukuran indeks saat diukur tertulis; jumlah artikel dibaca dari indeks |
| 6 | Lapisan pengambilan data bisa diganti | Selesai (`scraping.source`, `ARTICLE_SOURCE`); integrasi API Yudistira tidak dibangun |

**Pembungkus `python -m scraping.scheduled`** (peluncur: `scripts/pembaruan_berkala.cmd`): kunci
satu-instans -> coba ulang kegagalan terbuka -> mode maju -> pemeriksaan kualitas SELURUH antrean yang
belum digabung -> `data/expansion/pembaruan_status.json` + `pembaruan_riwayat.jsonl` + log per jalan
-> penanda dan notifikasi bila tidak bersih. Label baru (di luar yang sudah diputuskan cara
menampilkannya), duplikat, dan tumpang tindih MENAHAN penggabungan dan terus memicu penanda sampai
ditinjau. Setelah tiga jalan beruntun ditahan sistematis pembungkus berhenti mencoba sampai
`--reset`; kegagalan jaringan tidak pernah memicu "berhenti mencoba". Kode keluar: 0 bersih | 3 | 4 |
5 | 6 (lihat `expand.py`) | 7 batas mode maju tak ditemukan | 8 galat tak terduga | 9 jalan lain
sedang berlangsung.

**Percobaan manual (tanpa Task Scheduler):**

- *Jalan nyata:* 16 artikel baru (27 Sep-2 Okt 2026; SALAH 8, PENIPUAN 6, **BELUM TERBUKTI 2** -- label
  baru: 36976, 36941), 0 gagal, 64 detik; kode 6, penanda ditulis, notifikasi terkirim. Antrean belum
  digabung: 16 artikel.
- *Simulasi jaringan mati sejak awal* (proxy rusak, direktori sementara): permintaan pertama (halaman
  daftar) gagal setelah 4 percobaan -> kode 4, penanda, notifikasi; tidak ada berkas artikel maupun
  `state.json` yang ditulis.
- *Simulasi putus di tengah jalan* (sumber tiruan): 3 artikel berhasil, lalu pemutus sirkuit aktif
  setelah 5 kegagalan jaringan beruntun -> kode 4, penanda, notifikasi; 5 kegagalan tercatat sebagai
  bisa dicoba ulang; tidak ada berkas artikel yang ditulis.
- *Cacat yang ditemukan dan diperbaiki lewat percobaan ini:* jalan kedua pada hari yang sama dianggap
  bersih dan menghapus penanda padahal artikel berlabel baru masih di antrean; pemeriksaan kualitas
  kini berlaku pada seluruh antrean.
- Notifikasi dilaporkan "terkirim" berdasarkan kode keluar PowerShell; apakah muncul di layar belum
  dikonfirmasi pemilik proyek.

**Menunggu pemilik proyek:** jam penjadwalan dan persetujuan pendaftaran ke Task Scheduler; keputusan
untuk label `BELUM TERBUKTI`; cadangan mana yang dihapus.
