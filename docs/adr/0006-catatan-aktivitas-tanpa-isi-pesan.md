# ADR 0006: Catatan aktivitas tanpa isi pesan

Status: **diputuskan**; dibangun di Tahap 3, belum ada kodenya.

## Konteks

Pemilik proyek perlu tahu apakah demo dipakai dan di mana ia gagal (galat, kuota, waktu proses). Pesan yang
ditempel pengguna bisa memuat nomor telepon, nama, atau isi percakapan pribadi. Saat ini demo tidak menulis
log berkas apa pun selain log server; isi pesan hanya terkirim ke Gemini (ADR 0004). Temuan ini tercatat di
audit Tahap 0 (`docs/audit/audit_tahap0.md`, tabel keamanan butir 12).

## Keputusan

- Tahap 3 menambahkan catatan aktivitas berupa JSON per baris dengan rotasi berkas, **tanpa isi pesan**.
- Teks pesan dan potongannya tidak pernah dicatat. Pemilik proyek mendapat ringkasan lewat perintah CLI.
- Rincian bidang belum diputuskan dan akan ditetapkan di Tahap 3. Usulan (belum disetujui): waktu, jenis hasil
  (ditemukan / belum ditemukan / galat dan jenisnya), panjang pesan, waktu per tahap, dan status kuota; tanpa
  hash pesan, karena hash pesan pendek bisa dicocokkan balik ke teksnya.
- Di container, catatan ditulis ke volume log (`data/container/logs/`, ADR 0005).

## Alternatif yang ditolak

- **Mencatat isi pesan untuk analisis kegagalan**: ditolak. Risiko privasinya lebih besar daripada manfaatnya
  bagi demo portofolio. Analisis kegagalan memakai set uji yang disusun dengan sengaja.
- **Tidak mencatat apa pun**: ditolak, karena pola galat (503, kuota habis, antrean penuh) tidak terlihat.

## Konsekuensi

- Kegagalan pada pesan tertentu tidak bisa direproduksi dari log; yang terlihat hanya jenis dan pola.
- Halaman Tentang dan README harus menyatakan apa yang dicatat dan apa yang tidak.
- Uji Tahap 3 wajib memastikan teks masukan tidak pernah muncul di berkas log.
