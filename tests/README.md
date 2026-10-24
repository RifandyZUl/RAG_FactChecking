# tests/

**`tests/` BUKAN `testset/`.**
- `tests/` berisi **kode uji otomatis** (pytest) yang berjalan **offline**: tanpa API, tanpa model, tanpa
  `data/`.
- `testset/` berisi **data** set uji dan hasil evaluasi (tidak dijalankan).

| Folder | Menguji |
| --- | --- |
| `core/` | inti RAG (`generator`, `retriever`, prompt, `paths`), **uji kunci** (hash berkas terkunci, pedoman, set uji v1, hash byte data beku), `hf_env` |
| `scraping/` | `src/scraping/` |
| `llm/` | `src/llm/` (termasuk uji konkurensi buku besar kuota) |
| `evaluation/` | `src/evaluation/` |
| `labeling/` | `src/labeling/` |
| `webapp/` | `src/webapp/` (layanan, sumber daya, tampilan, tema, halaman lewat `streamlit.testing`) |

Di akar: `conftest.py`, `_fakes.py` (objek palsu bersama; `pyproject.toml` menaruh `tests/` di `pythonpath`),
`fixtures/` (HTML nyata yang **disamarkan** lewat `scripts/anonymize_fixtures.py`).

```powershell
.\.venv\Scripts\python.exe -m pytest                         # semua
.\.venv\Scripts\python.exe -m pytest tests/core/test_testset_locks.py   # uji kunci saja
```
