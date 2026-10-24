# data/

Data lokal, **tidak di-commit** (lihat `.gitignore`): `articles.json` (teks artikel), `raw_html/` (cache),
`chroma/` (indeks), `expansion/` (hasil perluasan), `candidates/` (berkas pelabelan, kunci), `backups/`,
hasil dan log evaluasi (`*.jsonl`, `*.log`), buku besar kuota (`quota_ledger.json`, `*.lock`).

Alasannya: berisi teks pihak ketiga, tautan sumber hoaks, dan kontak penipu. Yang di-commit hanya berkas
ini. Membangun ulang: README utama, "Membangun basis pengetahuan".
