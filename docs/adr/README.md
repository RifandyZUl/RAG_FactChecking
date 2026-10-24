# docs/adr/

Catatan keputusan arsitektur (ADR). Setiap ADR memakai format yang sama: **konteks, keputusan, alternatif
yang ditolak, konsekuensi**. ADR ditulis dari keputusan yang memang sudah diambil dan tercatat (CLAUDE.md,
`docs/audit/`, `docs/rancangan/`, riwayat commit). Bila alasan awal sebuah keputusan tidak pernah dicatat,
ADR menyatakannya, alih-alih menyusun alasan sesudahnya.

| No. | Keputusan | Status |
| --- | --- | --- |
| [0001](0001-streamlit-untuk-demo.md) | Streamlit untuk demo | berlaku |
| [0002](0002-berkas-terkunci.md) | Berkas inti dikunci dengan hash | berlaku |
| [0003](0003-chromadb-lokal.md) | ChromaDB lokal sebagai basis vektor | berlaku |
| [0004](0004-gemini-tier-gratis.md) | Gemini tier gratis sebagai LLM generator | berlaku |
| [0005](0005-docker-volume-python-313.md) | Docker dengan volume minimal dan Python 3.13; venv lokal tetap 3.11 | berlaku |
| [0006](0006-catatan-aktivitas-tanpa-isi-pesan.md) | Catatan aktivitas tanpa isi pesan | diputuskan, dibangun di Tahap 3 |
| [0007](0007-tanpa-microservice.md) | Satu proses, bukan microservice | berlaku |
