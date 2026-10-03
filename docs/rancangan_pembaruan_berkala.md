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
