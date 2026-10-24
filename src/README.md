# src/

**Akar `src/` adalah alur inti RAG**, persis seperti yang dievaluasi:

| Modul | Peran |
| --- | --- |
| `chunker.py` | chunking per seksi (Narasi, Penjelasan, Kesimpulan) + metadata — **terkunci** |
| `ingest.py` | embedding bge-m3 (revisi dipatok) -> ChromaDB; perintah ingest |
| `retriever.py` | pencarian + agregasi per artikel — **terkunci** |
| `generator.py` | klaim -> retrieval -> LLM -> jawaban; prompt sistem — **terkunci** |
| `paths.py` | jalur proyek terpusat (`RAG_INDEX_DIR` memilih indeks baca) |
| `hf_env.py` | `prepare_hf_env()`: variabel Hugging Face (offline), dipanggil di awal setiap titik masuk |

"Terkunci" = hash-nya dijaga `tests/core/test_testset_locks.py` (bukti evaluasi); jangan diubah.

Subpaket:

| Paket | Isi |
| --- | --- |
| `llm/` | abstraksi penyedia LLM (Gemini), retry, pembatas laju, buku besar kuota |
| `scraping/` | pengambilan dan parsing artikel TurnBackHoax, perluasan, pembaruan berkala |
| `evaluation/` | evaluasi dan diagnostik (lihat `evaluation/README.md`) |
| `labeling/` | pembuatan kandidat set uji (`candidates/`), pengukuran celah (`gap/`), sesi pelabelan dan audit (`sessions/`) |
| `webapp/` | demo Streamlit: `app.py` (titik masuk), `settings`, `resources`, `service`, `presentation`, `evaluation_facts`, `ui/` |

Semua perintah dijalankan dari root proyek. Paket dipasang ke venv dengan `pip install -e .` (lihat README utama), jadi `PYTHONPATH=src` tidak diperlukan.
