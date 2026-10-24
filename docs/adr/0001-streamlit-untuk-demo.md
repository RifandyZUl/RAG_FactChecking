# ADR 0001: Streamlit untuk demo

## Konteks

Proyek ini adalah portofolio pembelajaran; nilainya ada pada arsitektur dan evaluasi, bukan kelengkapan fitur.
Demo dibutuhkan untuk memperlihatkan pipeline yang **sama persis** dengan yang dievaluasi. Demo pertama dibuat
2026-09-25 sebagai adapter tipis di atas `generator` dan `retriever`. Tampilannya lalu dibangun ulang di
Tahap 1 (2026-10-23) dari berkas acuan desain, tetap di Streamlit.

Alasan memilih Streamlit pada demo pertama **tidak tercatat** di repositori. Yang tercatat adalah keputusan
Tahap 0/Tahap 1 untuk mempertahankannya (`docs/audit/audit_tahap0.md`).

## Keputusan

- Demo memakai Streamlit (versi dipatok, kini 1.64.0), dua halaman lewat `st.navigation`.
- Streamlit hanya lapisan tampilan. Logika berada di modul tanpa Streamlit yang diuji offline:
  `webapp/service.py` (validasi, batas laju, serialisasi), `webapp/resources.py` (sumber daya sekali-muat,
  pemanasan), dan `webapp/presentation.py` (data tampilan). `app.py` tidak punya logika retrieval atau generasi.
- Semua teks dinamis di-escape, `client.showErrorDetails = "none"`, dan pemantau berkas dimatikan.

## Alternatif yang ditolak

- **Menulis ulang antarmuka sebagai aplikasi web terpisah** (backend API + frontend) pada Tahap 1: ditolak.
  Tampilan yang diinginkan bisa dicapai di Streamlit dengan CSS, sedangkan memisahkan backend menambah proses
  dan permukaan serangan tanpa kebutuhan (lihat ADR 0007).

## Konsekuensi

- Skrip halaman dijalankan ulang di setiap interaksi. Karena itu sumber daya berat wajib dimuat lewat pemuat
  sekali-muat (`resources._Once` + `st.cache_resource`), dan dibuktikan dengan log "memuat <nama>" yang muncul
  sekali.
- Ada kekhasan yang harus diakali: sanitizer `st.html` membuang `<style>` dan `<svg>`, CSS dimuat sekali lewat
  `st.markdown`, dan ikon dipasang sebagai data-URI. CSS bergantung pada kelas internal yang bisa berubah
  antarversi, jadi menaikkan versi Streamlit berarti menguji ulang tampilannya (`scripts/screenshots.py`).
- Batas laju per sesi bisa dilewati dengan memuat ulang halaman. Perlindungan sesungguhnya ada di batas per
  proses dan batas harian.
- Di container, pemanasan dimulai saat server menyala lewat `webapp.serve` (ADR 0005), karena Streamlit baru
  menjalankan skrip ketika ada sesi.
