# Pemetaan jalur lama ke jalur baru (Tahap 1b, 2026-10-24)

Dokumen riwayat (rancangan, audit, laporan, `testset/v1.meta.json`, catatan di `data/`) **tidak ditulis
ulang**: jalur di dalamnya adalah jalur saat dokumen itu ditulis. Tabel ini menerjemahkannya. Dihasilkan
dari `git diff -M --name-status` (pemindahan dengan `git mv`; isi tidak berubah selain jalur impor dan
jalur berkas).

## Berkas

| Jalur lama | Jalur baru |
| --- | --- |
| `config/related_threshold.json` | `archive/fitur_mati/related_threshold.json` |
| `docs/audit_tahap0.md` | `docs/audit/audit_tahap0.md` |
| `docs/draf_readme_evaluasi.md` | `docs/riwayat/draf_readme_evaluasi.md` |
| `docs/laporan_tahap1.md` | `docs/audit/laporan_tahap1.md` |
| `docs/rancangan_evaluasi_eksternal.md` | `docs/rancangan/rancangan_evaluasi_eksternal.md` |
| `docs/rancangan_pembaruan_berkala.md` | `docs/rancangan/rancangan_pembaruan_berkala.md` |
| `docs/rancangan_v2.md` | `docs/rancangan/rancangan_v2.md` |
| `src/app.py` | `src/webapp/app.py` |
| `src/candidates/adjudication_workbook.py` | `src/labeling/sessions/adjudication_workbook.py` |
| `src/candidates/archive.py` | `src/labeling/candidates/archive.py` |
| `src/candidates/blind_session.py` | `src/labeling/sessions/blind_session.py` |
| `src/candidates/blind_workbook.py` | `src/labeling/sessions/blind_workbook.py` |
| `src/candidates/chain_sample.py` | `src/labeling/candidates/chain_sample.py` |
| `src/candidates/crosssite.py` | `src/labeling/candidates/crosssite.py` |
| `src/candidates/gap_blocks.py` | `src/labeling/gap/gap_blocks.py` |
| `src/candidates/gap_result.py` | `src/labeling/gap/gap_result.py` |
| `src/candidates/gap_review.py` | `src/labeling/gap/gap_review.py` |
| `src/candidates/gap_workbook.py` | `src/labeling/gap/gap_workbook.py` |
| `src/candidates/gemma_generate.py` | `src/labeling/candidates/gemma_generate.py` |
| `src/candidates/screen.py` | `src/labeling/candidates/screen.py` |
| `src/candidates/targets.py` | `src/labeling/candidates/targets.py` |
| `src/candidates/trace_audit.py` | `src/labeling/sessions/trace_audit.py` |
| `src/candidates/v1_verification.py` | `src/labeling/sessions/v1_verification.py` |
| `src/evaluation_facts.py` | `src/webapp/evaluation_facts.py` |
| `src/presentation.py` | `src/webapp/presentation.py` |
| `src/resources.py` | `src/webapp/resources.py` |
| `src/service.py` | `src/webapp/service.py` |
| `src/settings.py` | `src/webapp/settings.py` |
| `src/ui/__init__.py` | `src/webapp/ui/__init__.py` |
| `src/ui/beranda.py` | `src/webapp/ui/beranda.py` |
| `src/ui/components.py` | `src/webapp/ui/components.py` |
| `src/ui/style.css` | `src/webapp/ui/style.css` |
| `src/ui/tentang.py` | `src/webapp/ui/tentang.py` |
| `tests/anonymize_fixtures.py` | `scripts/anonymize_fixtures.py` |
| `tests/test_adjudication_workbook.py` | `tests/labeling/test_adjudication_workbook.py` |
| `tests/test_blind_session.py` | `tests/labeling/test_blind_session.py` |
| `tests/test_blind_workbook.py` | `tests/labeling/test_blind_workbook.py` |
| `tests/test_candidates.py` | `tests/labeling/test_candidates.py` |
| `tests/test_client.py` | `tests/scraping/test_client.py` |
| `tests/test_comparison.py` | `tests/evaluation/test_comparison.py` |
| `tests/test_crosssite.py` | `tests/labeling/test_crosssite.py` |
| `tests/test_devset.py` | `tests/evaluation/test_devset.py` |
| `tests/test_discovery.py` | `tests/scraping/test_discovery.py` |
| `tests/test_evaluation_facts.py` | `tests/webapp/test_evaluation_facts.py` |
| `tests/test_expand.py` | `tests/scraping/test_expand.py` |
| `tests/test_external_analysis.py` | `tests/evaluation/test_external_analysis.py` |
| `tests/test_external_eval.py` | `tests/evaluation/test_external_eval.py` |
| `tests/test_gap_blocks.py` | `tests/labeling/test_gap_blocks.py` |
| `tests/test_gap_result.py` | `tests/labeling/test_gap_result.py` |
| `tests/test_gap_review.py` | `tests/labeling/test_gap_review.py` |
| `tests/test_gap_workbook.py` | `tests/labeling/test_gap_workbook.py` |
| `tests/test_gemini.py` | `tests/llm/test_gemini.py` |
| `tests/test_gemma_generate.py` | `tests/labeling/test_gemma_generate.py` |
| `tests/test_generator.py` | `tests/core/test_generator.py` |
| `tests/test_index_check.py` | `tests/evaluation/test_index_check.py` |
| `tests/test_index_comparison.py` | `tests/evaluation/test_index_comparison.py` |
| `tests/test_ledger.py` | `tests/llm/test_ledger.py` |
| `tests/test_links.py` | `tests/scraping/test_links.py` |
| `tests/test_metrics.py` | `tests/evaluation/test_metrics.py` |
| `tests/test_parser.py` | `tests/scraping/test_parser.py` |
| `tests/test_paths.py` | `tests/core/test_paths.py` |
| `tests/test_pipeline.py` | `tests/scraping/test_pipeline.py` |
| `tests/test_presentation.py` | `tests/webapp/test_presentation.py` |
| `tests/test_prompt.py` | `tests/core/test_prompt.py` |
| `tests/test_reparse.py` | `tests/scraping/test_reparse.py` |
| `tests/test_resources.py` | `tests/webapp/test_resources.py` |
| `tests/test_restore.py` | `tests/scraping/test_restore.py` |
| `tests/test_results_store.py` | `tests/evaluation/test_results_store.py` |
| `tests/test_retrieval_ablation.py` | `tests/evaluation/test_retrieval_ablation.py` |
| `tests/test_retriever.py` | `tests/core/test_retriever.py` |
| `tests/test_retriever_exactness.py` | `tests/evaluation/test_retriever_exactness.py` |
| `tests/test_sample_size.py` | `tests/evaluation/test_sample_size.py` |
| `tests/test_scheduled.py` | `tests/scraping/test_scheduled.py` |
| `tests/test_screen.py` | `tests/labeling/test_screen.py` |
| `tests/test_service.py` | `tests/webapp/test_service.py` |
| `tests/test_testset_analysis.py` | `tests/evaluation/test_testset_analysis.py` |
| `tests/test_testset_eval.py` | `tests/evaluation/test_testset_eval.py` |
| `tests/test_testset_locks.py` | `tests/core/test_testset_locks.py` |
| `tests/test_theme.py` | `tests/webapp/test_theme.py` |
| `tests/test_throttle.py` | `tests/llm/test_throttle.py` |
| `tests/test_trace_audit.py` | `tests/labeling/test_trace_audit.py` |
| `tests/test_ui.py` | `tests/webapp/test_ui.py` |
| `tests/test_v1_verification.py` | `tests/labeling/test_v1_verification.py` |

## Modul (perintah `python -m`, `PYTHONPATH=src`)

| Lama | Baru |
| --- | --- |
| `python -m candidates.adjudication_workbook` | `python -m labeling.sessions.adjudication_workbook` |
| `python -m candidates.archive` | `python -m labeling.candidates.archive` |
| `python -m candidates.blind_session` | `python -m labeling.sessions.blind_session` |
| `python -m candidates.blind_workbook` | `python -m labeling.sessions.blind_workbook` |
| `python -m candidates.chain_sample` | `python -m labeling.candidates.chain_sample` |
| `python -m candidates.crosssite` | `python -m labeling.candidates.crosssite` |
| `python -m candidates.gap_blocks` | `python -m labeling.gap.gap_blocks` |
| `python -m candidates.gap_result` | `python -m labeling.gap.gap_result` |
| `python -m candidates.gap_review` | `python -m labeling.gap.gap_review` |
| `python -m candidates.gap_workbook` | `python -m labeling.gap.gap_workbook` |
| `python -m candidates.gemma_generate` | `python -m labeling.candidates.gemma_generate` |
| `python -m candidates.screen` | `python -m labeling.candidates.screen` |
| `python -m candidates.targets` | `python -m labeling.candidates.targets` |
| `python -m candidates.trace_audit` | `python -m labeling.sessions.trace_audit` |
| `python -m candidates.v1_verification` | `python -m labeling.sessions.v1_verification` |
| `python -m streamlit run src\app.py` | `$env:PYTHONPATH="src"; python -m streamlit run src\webapp\app.py` |
| `import settings`, `resources`, `service`, `presentation`, `evaluation_facts`, `ui` | `from webapp import ...` |

**Tidak dipindah:** `src/chunker.py`, `ingest.py`, `retriever.py`, `generator.py`, `paths.py`,
`src/evaluation/`, `src/llm/`, `src/scraping/`, `scripts/pembaruan_berkala.*`, `manifests/`, `archive/v1/`,
`data/`, dan **seluruh `testset/`** (keputusan pemilik proyek 2026-10-24).

**Sengaja tidak diubah walau menyebut nama modul lama:** teks yang ikut tertulis ke berkas tinjauan `.xlsx`
dan berkas petunjuknya (konstanta `GENERATED_BY`, kalimat "disiapkan kode (candidates.X)", perintah di
petunjuk berkas sesi). Itu isi artefak bukti, bukan jalur.
