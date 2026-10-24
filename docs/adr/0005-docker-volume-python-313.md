# ADR 0005: Docker dengan volume minimal dan Python 3.13; venv lokal tetap 3.11

## Konteks

Demo perlu bisa dijalankan orang lain tanpa menyiapkan venv Windows. Data yang dipakai demo (indeks berisi
teks pihak ketiga, buku besar kuota, `.env`, model 2,2 GB) tidak boleh masuk image maupun repositori. Semua
angka evaluasi diukur di venv Windows dengan Python 3.11. Laptop pengembangan punya RAM 16 GB, sebagian besar
sudah dipakai aplikasi lain.

## Keputusan

- **Peran**: venv Windows adalah cara utama untuk pengembangan, evaluasi, dan demo harian. Docker adalah cara
  resmi untuk lingkungan yang dapat direproduksi, pembuktian kesetaraan lingkungan, dan dasar deployment di
  masa depan. CI membangun image di setiap push (job `docker-build`, tanpa menjalankan container).
- **Python 3.13 di container dan CI** (keputusan pemilik proyek 2026-10-22). Python 3.14 menunggu
  `sentence-transformers` 6.2.0 cukup berumur.
- **Venv lokal tetap Python 3.11**, karena itulah lingkungan tempat evaluasi dijalankan. Keduanya menjalankan
  seluruh uji. Kesetaraan embedding dibuktikan dengan ambang yang ditetapkan sebelum mengukur
  (`evaluation.embedding_proof`): kedua lingkungan **SAMA**. Kosinus minimum 0,9999999999985 (Windows) dan
  0,9999999999987 (container) pada 200 chunk, dan top-3 identik 64/64 di dalam masing-masing lingkungan
  maupun antar-lingkungan.
- **Image**: `python:3.13.16-slim-trixie` dipatok ke digest, multi-stage, torch build CPU, versi dari
  `requirements.txt`, pengguna non-root, sistem berkas baca-saja, `.dockerignore` daftar-putih. Isinya hanya
  kode, konfigurasi tampilan, logo, dan dua berkas angka publik.
- **Container tidak pernah menulis ke `data/` produksi.** Volume dibatasi pada yang dibutuhkan demo:
  - salinan indeks khusus container (`data/container/chroma/`, baca-tulis);
  - buku besar kuota di subfolder tersendiri (`data/container/kuota/`, baca-tulis, lewat `RAG_LEDGER_DIR`);
  - log (`data/container/logs/`, baca-tulis);
  - `.env` sebagai berkas baca-saja (bukan `env_file`, supaya kunci tidak terlihat di `docker inspect`);
  - cache Hugging Face host, baca-saja.
- **`mem_limit: 5g`**. Puncak terukur 3,39 GB (`memory.peak`).
- **Berhenti dengan bersih: `stop_grace_period: 30s` dan `init: true`** (2026-10-24). Container yang dihentikan
  dulu keluar dengan kode 137 (SIGKILL). Diagnosis awal (Python sebagai PID 1 mengabaikan SIGTERM) ternyata
  keliru. Penyebab yang terukur lewat `docker events`: daemon Docker di mesin pengembangan memberi
  `StopTimeout` **1 detik** ke setiap container (juga pada `docker run` polos), sehingga SIGKILL datang sekitar
  1 detik setelah SIGTERM. Streamlit polos sempat berhenti dalam 0,8 detik, sedangkan Streamlit dengan model
  termuat butuh 1,5-2,5 detik. Dengan `stop_grace_period: 30s`, `docker compose stop` selesai dalam 2,5 detik
  dengan kode keluar 0, hanya SIGTERM yang dikirim, buku besar kuota tidak berubah, dan kuncinya bisa langsung
  diambil proses baru. Tanpa `init` hasilnya sama (2,2 detik, kode 0). `init: true` dipertahankan sebagai
  praktik baku (tini meneruskan sinyal dan membereskan proses anak), bukan sebagai perbaikan kode 137.
- **Kesehatan**: `python -m webapp.serve` memulai pemanasan di proses yang sama dengan Streamlit. HEALTHCHECK
  baru sehat setelah pemanasan berhasil. Terukur: sehat dalam 26 detik; model dimuat sekali (3,3 detik, pid 1).

## Alternatif yang ditolak

- **Memasang seluruh `data/`** (rancangan awal Tahap 2): ditolak. Container jadi bisa menulis indeks produksi
  dan SQLite lewat folder bersama Windows/WSL2, yang rawan rusak.
- **Memasang indeks produksi hanya-baca**: diuji dan gagal; ChromaDB menulis ke SQLite saat klien dibuat.
  Karena itu dipakai salinan, yang harus disalin ulang setiap kali indeks produksi berubah.
- **Memasang berkas buku besar host langsung**: tidak bisa, karena buku besar diganti lewat `os.replace`
  sehingga butuh folder, dan kunci berkas tidak andal lewat bind mount Windows/WSL2.
- **Volume Docker untuk model, diisi sekali**: tidak dibutuhkan. Waktu muat model dari cache host baca-saja
  3,3 detik, lebih cepat daripada venv (15,2 detik).
- **`mem_limit: 4g`** (rancangan awal): ditolak karena berisiko OOM saat model dimuat.
- **Python 3.11 di container** atau **3.14 sekarang**: ditolak. Lihat keputusan di atas.
- **Pemanasan dipicu permintaan HTTP dari HEALTHCHECK** (rancangan Tahap 0): tidak bekerja. Streamlit baru
  menjalankan skrip ketika ada sesi WebSocket, bukan pada permintaan HTTP biasa.

## Konsekuensi

- Buku besar kuota container terpisah dari host, padahal kuota Gemini berlaku per proyek Google. **Demo di
  container dan skrip di host tidak boleh dijalankan bersamaan.**
- Salinan indeks container bisa basi; README mencantumkan langkah menyalin ulang setelah ingest di host.
- Ingest dan evaluasi untuk indeks produksi tetap dijalankan di venv host.
- Image berukuran 2,93 GB di disk (venv 2,17 GB); build tanpa cache sekitar 5,5 menit.
- Kebutuhan memori: WSL2 minimal `memory=6GB`, dan sekitar 4-5 GB RAM bebas di Windows sebelum build atau
  menjalankan container (laptop 16 GB). Langkah memperbarui salinan indeks ada di README, "Docker".
- Build dan jalan container butuh memori yang cukup di Windows. Pada percobaan pertama build dihentikan
  karena RAM bebas Windows turun di bawah 0,7 GB.
