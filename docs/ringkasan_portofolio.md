# Ringkasan untuk website portofolio

Bahan siap salin. Semua angka sama dengan [README](../README.md) dan berasal dari
`testset/eksternal_hasil_per_butir.json` serta `testset/eksternal_butir.json`.

## Judul

Cek Pesan Hoaks: RAG Verifikasi Klaim

## Deskripsi satu kalimat

Sistem yang mencari apakah klaim dalam sebuah pesan sudah pernah diperiksa TurnBackHoax.id, lalu menampilkan
label, kesimpulan, dan rujukan dari artikel cek fakta itu apa adanya.

## Deskripsi satu paragraf

Banyak hoaks yang beredar sebenarnya sudah pernah diperiksa pemeriksa fakta, tetapi artikelnya susah dicari
karena kata-kata di pesan berbeda dengan judul artikel. Saya membangun sistem RAG yang mencari tiga artikel
TurnBackHoax.id yang paling mirip dengan pesan pengguna, lalu meminta Gemini memutuskan apakah salah satunya
membahas klaim yang sama. Label, kesimpulan, dan tautan selalu diambil dari artikel, tidak pernah ditulis oleh
model. Sistem ini saya uji dengan 91 klaim nyata dari Liputan6 Cek Fakta, dengan batas lulus yang saya
tentukan sebelum pengujian. Untuk klaim yang ada di arsip, artikel yang benar ditemukan pada 36 dari 46 klaim
(78,3%, interval 95% 64,4%-87,7%), dan hasil ini memadai. Untuk klaim yang tidak ada di arsip, sistem masih
keliru mencocokkan 10 dari 45 klaim (22,2%, interval 95% 12,5%-36,3%), terutama pada penipuan yang polanya
sama tetapi lembaganya berbeda. Hasil ini gugur menurut batas yang sudah saya tetapkan, jadi demo selalu
meminta pengguna mengecek sendiri apakah klaimnya benar-benar sama.

## Teknologi

- Python 3.11 (lingkungan evaluasi) dan 3.13 (Docker, CI)
- BGE-M3 lewat sentence-transformers dan PyTorch (CPU) untuk embedding
- ChromaDB 1.5.9 sebagai basis vektor lokal
- Gemini 3.5 Flash Lite lewat google-genai, tier gratis
- Streamlit 1.64.0 untuk demo
- requests dan BeautifulSoup untuk scraping
- pytest, ruff, dan GitHub Actions untuk uji otomatis
- Docker dan Docker Compose
- Playwright untuk tangkapan layar demo

## Keputusan teknis yang paling penting

1. **Model hanya memilih, tidak menulis jawaban.** Gemini cukup memilih satu dari tiga artikel atau menolak.
   Label, kesimpulan, dan tautan diambil langsung dari artikel, dan URL apa pun yang ditulis model dibuang.
2. **"Belum ditemukan" dianggap jawaban yang benar.** Evaluasi sengaja memuat klaim yang mirip topiknya
   tetapi bukan klaim yang sama, karena di dunia nyata banyak klaim memang belum pernah diperiksa.
3. **Batas lulus ditentukan sebelum pengujian.** Set uji dibekukan, dan kode generator, retriever, serta
   chunker dikunci dengan hash. Dengan begitu hasil yang kurang baik, seperti kecocokan palsu yang gugur,
   tetap dilaporkan apa adanya.
4. **Chunking mengikuti seksi artikel.** Setiap artikel dipotong per seksi (Narasi, Penjelasan, Kesimpulan),
   bukan per jumlah karakter, supaya klaim yang beredar dan fakta yang sebenarnya tidak tercampur.
5. **Tautan sumber hoaks dipisah dari rujukan yang sah.** Tautan ke unggahan hoaks tidak pernah ditampilkan
   sebagai rujukan, dan tautan pendek atau arsip ikut disaring karena tujuannya tidak bisa dicek pengguna.
