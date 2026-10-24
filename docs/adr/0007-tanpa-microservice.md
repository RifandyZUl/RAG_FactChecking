# ADR 0007: Satu proses, bukan microservice

## Konteks

Sistem ini terdiri dari retrieval (bge-m3 + ChromaDB), generasi (Gemini), dan antarmuka demo. Ketiganya bisa
saja dipisah menjadi layanan tersendiri. Pemilik proyek menetapkan aturan "jangan membangun untuk skala yang
tidak ada". Demo berjalan di satu laptop dan melayani sangat sedikit pengguna, dengan kuota LLM 500
permintaan per hari.

## Keputusan

- Demo berjalan sebagai **satu proses Python**: Streamlit, model embedding, indeks, dan penyedia LLM dimuat
  sekali di proses itu (ADR 0001, ADR 0005).
- Pemeriksaan diserialkan per proses dengan kunci layanan, ditambah pesan "menunggu giliran" dan batas tunggu
  150 detik.
- Batas laju dan buku besar kuota hidup di proses yang sama, dengan kunci berkas OS untuk berbagi dengan skrip
  evaluasi di host.

## Alternatif yang ditolak

- **Layanan retrieval, layanan generasi, dan frontend terpisah** (mis. API + antrean + antarmuka): ditolak.
  - Tidak ada beban yang membutuhkannya. Kuota Gemini (RPM 15, RPD 500) membatasi throughput jauh sebelum CPU.
  - Setiap layanan yang memuat bge-m3 menambah sekitar 2-3 GB memori; puncak satu proses saja sudah 3,39 GB.
  - Lebih banyak proses berarti lebih banyak permukaan serangan, konfigurasi, dan titik gagal untuk
    dipelihara satu orang.
- **Generator yang dipakai bersamaan dari banyak utas tanpa kunci**: ditolak. `generator.py` (terkunci, ADR
  0002) membaca `provider.records[n_before:]`, sehingga dua pemeriksaan serentak pada penyedia yang sama bisa
  saling tertukar catatan panggilannya.

## Konsekuensi

- Pemeriksaan berjalan satu per satu; pada saat Gemini lambat (sampai sekitar 97 detik saat 503), pengguna
  kedua menunggu.
- Skala horizontal tidak tersedia tanpa merancang ulang. Ini disengaja dan perlu ditinjau ulang hanya bila ada
  beban nyata yang membutuhkannya.
