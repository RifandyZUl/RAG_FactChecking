# src/evaluation/

Modul TIDAK dipindah ke subfolder (perintah `python -m evaluation.X` yang tercatat di dokumen tetap
berlaku). Pengelompokan menurut fungsi:

| Fungsi | Modul | LLM? |
| --- | --- | --- |
| Evaluasi set uji v1 | `testset_eval` (jalankan), `testset_analysis` (metrik), `metrics`, `results_store` | `testset_eval` ya |
| Evaluasi eksternal (Liputan6) | `external_eval` (jalankan), `external_analysis` (keandalan, label final, metrik) | `external_eval` ya |
| Set pengembangan dan diagnostik generasi | `devset`, `generation_eval`, `repeat_eval`, `comparison` | ya |
| Retrieval dan indeks | `retrieval_eval`, `retrieval_ablation`, `index_check`, `index_comparison`, `retriever_exactness` | tidak |
| Kesetaraan lingkungan (Tahap 2) | `embedding_proof` (embed ulang 200 chunk + top-3 64 kueri; venv vs container) | tidak |
| Kuota dan model | `probe_quota` (1 permintaan), `gemma_json_check` | ya |
| Perencanaan | `sample_size` | tidak |

Skrip yang memuat model memanggil `hf_env.prepare_hf_env()` di awal `main()`. Skrip "LIVE" memakai kuota
harian bersama demo (`data/quota_ledger.json`). Hasil yang di-commit ada di `testset/` (lihat
`testset/README.md`).
