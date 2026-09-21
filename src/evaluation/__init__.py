"""
Evaluasi dan alat diagnostik LIVE (memanggil LLM sungguhan) serta pustaka pendukungnya.

  results_store     simpan/lanjutkan hasil evaluasi (JSONL per kueri)
  comparison        perbandingan keputusan antarmodel (informasi, bukan kriteria H3)
  generation_eval   evaluasi lapisan generasi (CLI)
  retrieval_eval    verifikasi retrieval (CLI)
  gemma_json_check  uji format JSON Gemma 4 (CLI)
  probe_quota       probe tunggal ke server (CLI)

Semua CLI dijalankan dari root proyek: PYTHONPATH=src python -m evaluation.<modul>
Nama modul sengaja TIDAK berawalan `test_` agar pytest tidak mengumpulkannya.
"""
