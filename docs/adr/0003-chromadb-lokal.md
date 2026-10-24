# ADR 0003: ChromaDB lokal sebagai basis vektor

## Konteks

Basis pengetahuan berukuran kecil (Versi 1: 150 artikel / 450 chunk; kini 1.532 artikel / 4.593 chunk) dan
dijalankan di satu laptop dengan CPU saja, tanpa anggaran layanan berbayar. Alasan memilih ChromaDB pada awal
proyek **tidak tercatat** di repositori. Yang tercatat adalah perilakunya dan keputusan lanjutan.

## Keputusan

- ChromaDB 1.5.9 sebagai `PersistentClient` lokal (SQLite + segmen HNSW di `data/chroma/`), satu koleksi,
  ruang kosinus. Indeks tidak di-commit karena berisi teks pihak ketiga.
- Kesetaraan indeks dibuktikan dari **isi**, bukan byte berkas (`evaluation.index_check`), karena ChromaDB
  menulis ulang berkas indeks setiap kali koleksi dibuka.
- `ef_search` produksi 2000 (2026-10-03), karena HNSW dengan nilai bawaan 100 mulai berbeda dari pencarian
  eksak pada 1.532 artikel. `evaluation.retriever_exactness` wajib dijalankan setiap kali indeks bertambah.
  Arsip `archive/v1` sengaja tetap 100.
- Arsip dan bukti tidak pernah dibuka langsung; yang dibuka selalu salinan byte.

## Alternatif yang ditolak

- **Pencarian eksak (brute-force) sebagai retriever produksi**: tidak diterapkan. `ef_search` 2000 terukur
  sama dengan pencarian eksak (0 dari 1.920 chunk terlewat pada 64 kueri) dengan latensi kueri sekitar 10 ms.
  Pencarian eksak tetap dipakai sebagai pembanding di alat evaluasi.
- **Memasang indeks hanya-baca di container** (2026-10-24): ditolak karena terbukti tidak bisa. ChromaDB
  sudah menulis ke SQLite saat klien dibuat (`attempt to write a readonly database`). Lihat ADR 0005.

## Konsekuensi

- Hash byte berkas indeks tidak bisa dipakai sebagai bukti; yang dipakai selalu sidik jari isi.
- Retrieval adalah pencarian perkiraan. Ketepatannya hanya terukur pada ukuran indeks saat pengukuran.
- Dua proses tidak boleh membuka indeks yang sama sementara salah satunya menulis (mis. ingest saat demo
  berjalan).
