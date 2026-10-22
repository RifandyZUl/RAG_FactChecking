# Tahap 0: audit dan rencana demo portofolio

Disusun 2026-10-22 di branch `tahap-0-audit`. Tidak ada kode yang diubah: isi branch ini hanya berkas
ini. Semua angka di bawah diukur pada hari itu, kecuali yang ditandai "riwayat" beserta sumbernya.

Garis dasar saat audit (commit `a704d5b`): `pytest` 530 lolos (65,8 dtk); `ruff check src tests`
29 temuan lama, dua di antaranya di berkas terkunci (lihat 5.3).

---

## 0. Yang perlu Anda putuskan sebelum Tahap 1

| # | Keputusan | Usulan saya |
| --- | --- | --- |
| K1 | **Prompt meminta rujukan dari `references_filtered`. Di proyek ini `references_filtered` justru tautan yang DIBUANG** (sumber hoaks, media sosial, arsip, pemendek URL; `scraping/links.py:153` `filter_references`, `parser.py:272`). Rujukan yang sah ada di `references`. `chunker.py:146` bahkan melarang `references_filtered` masuk metadata. | Pakai `references` (lewat `presentation.display_references`, yang menyaringnya ulang). Mengikuti prompt apa adanya akan melanggar Aturan Wajib #1. |
| K2 | Warna status di berkas acuan berbeda dari skema yang ada. Acuan: merah `#B42318`, jingga `#C2410C`, ungu `#6A3A9A`, abu `#475467`, dan tidak ada kuning PARODI. Yang ada (`.streamlit/config.toml`): `#8F1D1D`, `#9A4A0B`, kuning `#6E5A12`, `#6A3A9A`, `#5B6168`. Prompt menyebut keduanya: "warna status yang sudah ada" dan "berkas acuan sebagai sumber kebenaran warna". | Pertahankan warna status yang ada (sudah diuji kontras di `tests/test_theme.py`). Untuk palet netral dan aksen, ikuti acuan (`#1F4E9E`, bukan `#1F4E79`). |
| K3 | `Tentang.dc.html` memakai **hijau** `#0F6B3E` untuk "36 dari 46" dan "YANG DILAKUKAN", serta latar merah muda/hijau muda. Hijau tidak ada di palet prompt, dan proyek ini sengaja menghindari hijau karena terkesan "benar" (`config.toml`, komentar violet). Angka 36/46 berwarna hijau juga terbaca sebagai prestasi, padahal aturan nada README menuntut angka disajikan bersama set, indeks, dan interval. | Pakai warna teks utama/aksen, tanpa hijau, dan tulis angka lengkap dengan interval. |
| K4 | Acuan hanya selebar 390px (ponsel). Tidak ada acuan 1280px. | Kolom tengah dengan lebar maksimum (~640px) di desktop, urutan sama dengan ponsel; perbedaan dicatat di laporan Tahap 1. |
| K5 | Hasil "ditemukan" diminta menampilkan **Kesimpulan TurnBackHoax apa adanya**. Sekarang yang tampil adalah parafrase LLM (`Answer.klarifikasi`). Generator tetap memanggil LLM dan tetap menulis parafrase (prompt terkunci); tampilan hanya berhenti memakainya. Keputusan dan angka evaluasi tidak berubah. Efek samping: teks bebas dari LLM tidak lagi tampil ke pengguna umum, sehingga permukaan prompt injection berkurang. | Setuju. Parafrase tetap terlihat di panel penguji. |
| K6 | Fitur "Mungkin terkait" mati permanen di indeks 1.532 (`config/related_threshold.json`, `ambang: null`), tetapi seluruh rantainya masih ada di jalur demo: `RelatedThreshold`, `resolve_related_threshold`, `related_articles`, `render_related`, `load_related_threshold`, 3 konstanta, 2 bidang diagnostik, dan ujinya. Itu kode mati di jalur produksi. | Hapus dari kode demo. Riwayat kalibrasinya tetap tercatat di CLAUDE.md dan `v1_temuan_untuk_v2.md` 6.1. Berkas `config/related_threshold.json` juga dihapus, atau dipindah ke `docs/` sebagai catatan. Fitur tetap mati, hanya kodenya hilang. |
| K7 | Versi Python dan dua kenaikan dependensi (bagian 4). | Python 3.14 dengan `sentence-transformers` 6.1.0 → 6.2.0 dan `requests` 2.31.0 → 2.34.2. Keduanya kenaikan dependensi yang ada, bukan dependensi baru, tetapi tetap butuh izin Anda. |
| K8 | `retriever.py` dan `chunker.py` disebut "hash-nya bukti evaluasi", tetapi **tidak ada uji yang menguncinya**. Yang dikunci `tests/test_testset_locks.py` hanya `generator.py`, prompt, dan skema. | Tahap 1 menambah uji kunci hash untuk keduanya, dengan nilai saat ini: `retriever.py` `68321aed…5ab8`, `chunker.py` `6d9de5ce…f475` (sha256 ternormalisasi LF). |
| K9 | Pengukuran model embedding belum bisa dilakukan hari ini (bagian 2.3). | Ukur ulang saat memori bebas ≥ 3 GB; Anda cukup menutup aplikasi lain lalu memberi tahu saya. |

---

## 1. Peta arsitektur saat ini

### 1.1 Modul yang dipakai demo

| Modul | Tanggung jawab | Status |
| --- | --- | --- |
| `src/app.py` (444 baris) | Adapter Streamlit: memuat sumber daya (`st.cache_resource`), `check_claim` (satu-satunya pemanggil pipeline), fungsi `render_*`, `main` | dapat diubah |
| `src/presentation.py` (795 baris) | Salinan teks UI, gaya status, klasifikasi galat, `Answer` → `ResultView`, validasi masukan, escape Markdown, **plus** jumlah artikel via sqlite, catatan cakupan evaluasi, dan ambang "mungkin terkait" | dapat diubah |
| `src/generator.py` | `AnswerGenerator.answer`: retrieval → prompt → LLM → `Answer`; pengaman URL/id | **terkunci** |
| `src/retriever.py` | `retrieve`: embed → `collection.query` (30 chunk) → `aggregate_by_article` → ambil Narasi/Kesimpulan | **terkunci** (belum ada uji kunci, K8) |
| `src/chunker.py` | `MAX_SEQ_LENGTH`, `decode_references` (dipakai retriever) | **terkunci** (belum ada uji kunci, K8) |
| `src/ingest.py` | `load_model`, `MODEL_NAME`, `COLLECTION_NAME`, `CHROMA_DIR`, `get_collection` (ingest), efek samping env `DISABLE_SAFETENSORS_CONVERSION` | dapat diubah (hati-hati: ingest/evaluasi) |
| `src/llm/` | `get_provider` → `GeminiProvider` (retry, throttle RPM/TPM, buku besar RPD, `redact`) | dapat diubah |
| `src/scraping/links.py` | `blocked_reason` (penyaringan ulang rujukan saat tampil) | dapat diubah |
| `src/paths.py` | `INDEX_DIR` (`RAG_INDEX_DIR`), `PROJECT_ROOT` | dapat diubah |
| `.streamlit/config.toml` | tema, satu-satunya tempat kode warna | dapat diubah |
| `config/related_threshold.json` | ambang "mungkin terkait" per indeks (mati) | K6 |

### 1.2 Alur satu pemeriksaan

```
main() [app.py]
 ├─ render_header → load_article_count → presentation.count_indexed_articles (sqlite baca-saja)
 │                 → presentation.evaluation_scope_note (angka diketik tetap)
 ├─ st.text_area → count_claim_tokens → load_tokenizer (AutoTokenizer terpisah) → is_long_claim
 ├─ st.button "Periksa" → presentation.validate_claim
 └─ run_check → check_claim(text)
      ├─ load_collection   (PersistentClient.get_collection, tanpa get_or_create)
      ├─ load_provider     (llm.get_provider → GeminiProvider, cache per PROSES)
      ├─ load_embedder     (ingest.load_model → SentenceTransformer bge-m3, CPU)
      ├─ AnswerGenerator(provider, retrieve_and_keep).answer(claim)      [terkunci]
      │    ├─ retrieve(query, embedder, collection, top_k=3)             [terkunci]
      │    │    ├─ model.encode (≤512 token)
      │    │    ├─ collection.query(n_results=30)  → aggregate_by_article
      │    │    └─ collection.get(ids=Narasi+Kesimpulan top-3)
      │    ├─ build_user_prompt → provider.generate (≤2 panggilan bila format gagal)
      │    └─ parse_llm_output → status/rujukan dari METADATA, bukan LLM
      └─ presentation.build_view(ans, …) → ResultView → st.session_state → render_result
```

### 1.3 Redundansi dan ketergantungan yang tidak perlu (dengan bukti)

1. **Dua tokenizer untuk hal yang sama.** `app.count_claim_tokens` memuat `AutoTokenizer` sendiri lewat
   `load_tokenizer`, sedangkan `app.count_query_tokens` memakai `embedder.tokenizer`. Hasilnya sama,
   tetapi tokenizer dimuat dua kali di memori. Satu fungsi cukup. Tokenizer terpisah tetap dipakai
   karena ringan dan dibutuhkan sebelum model dimuat.
2. **Pembukaan koleksi ganda dan tidak diperiksa.** `app.load_collection` menyalin logika
   `ingest.get_collection` tanpa `get_or_create`. Itu sengaja, agar demo tidak membuat koleksi,
   tetapi `ef_search` tidak pernah diperiksa. Kalau demo diarahkan ke indeks dengan `ef_search` 100,
   tidak ada yang memberi tahu (`ingest.collection_ef_search` sudah ada, tidak dipakai).
3. **`import ingest` di app hanya demi efek samping.** Impor itu menyetel
   `DISABLE_SAFETENSORS_CONVERSION` sebelum transformers dimuat, sampai butuh pengecualian ruff
   `I001` (`ruff.toml`). Akibatnya demo mengimpor seluruh modul ingest, termasuk chromadb,
   saat start. Setelan env sebaiknya pindah ke modul konfigurasi yang diimpor pertama.
4. **`presentation.py` memegang empat tanggung jawab:** salinan teks, pemetaan tampilan,
   akses sqlite indeks (`count_indexed_articles`), dan konfigurasi ambang (`load_related_threshold_config`,
   `resolve_related_threshold`). Akses indeks bukan urusan lapisan tampilan.
5. **Angka evaluasi diketik tetap** di `presentation.evaluation_scope_note`
   (`48 dari 50`, `BASELINE_ARTICLES`, `RETRIEVAL_MEASUREMENT`), terpisah dari README. Sumber tunggal
   untuk 36/46 dan 10/45 sudah ada: `testset/eksternal_hasil_per_butir.json` (di-commit, 91 butir,
   `label_final` + `keputusan_modus`). Dari berkas itu negatif = 45 (`TIDAK ADA`), dan yang dijawab
   "ditemukan" = 10.
6. **Kode mati di jalur demo:** rantai "mungkin terkait" (K6).
7. **Provider bersama tanpa kunci antar-utas.** `load_provider` di-cache per proses, jadi semua sesi
   Streamlit (masing-masing utas) berbagi satu `GeminiProvider`. `DailyLedger._save` menulis ke berkas
   `.tmp` yang sama lalu `os.replace` (`llm/ledger.py:75-79`), dan `RateLimiter` juga tanpa kunci.
   `grep Lock src/llm` = 0 hasil. Dua pemeriksaan serentak bisa saling menimpa hitungan kuota.
8. **`provider.records` tumbuh tanpa batas.** `llm/base.py:90` menambah satu `CallRecord` per
   panggilan, dan karena provider hidup seumur proses, daftarnya tidak pernah dipangkas. Kecil, tapi
   tetap kebocoran memori.
9. **Jeda 4 detik global.** `GeminiProvider.min_interval_s` bawaan 4 dtk (`LLM_MIN_INTERVAL_S`).
   Karena provider dibagi, dua pengguna yang memeriksa hampir bersamaan saling menunggu.
   Ini wajar untuk kuota, tetapi pengguna kedua tidak diberi tahu.
10. **`generator.render()`** (teks CLI) tidak dipakai demo. Ia dipakai CLI/evaluasi dan berada di berkas
    terkunci, jadi tidak disentuh.

---

## 2. Profil kinerja

### 2.1 Kondisi pengukuran

Laptop i5-1235U, RAM 16 GB, tetapi **memori bebas hanya 0,9-1,5 GB** saat mengukur (IDE, pyrefly,
Chrome terbuka). Angka di bawah karenanya cenderung lebih lambat dan berderau. Indeks diukur pada
**salinan** `data/chroma` di scratchpad (produksi tidak dibuka), tanpa memanggil API.

### 2.2 Terukur hari ini

| Langkah | Waktu | Catatan |
| --- | --- | --- |
| `import ingest` (chromadb, chunker) | 24,3 dtk | impor dingin, terjadi di setiap start server |
| `import streamlit` | 4,0 dtk | |
| `import transformers` | 10,8-19,6 dtk | dipicu saat tokenizer pertama dimuat |
| Muat tokenizer bge-m3 dari cache | 2,7 dtk (`HF_HUB_OFFLINE=1`) / 4,4 dtk (online) / **101,9 dtk sekali** | online = cek ke Hugging Face Hub di setiap pemuatan; pencilan 102 dtk terjadi di jalan pertama |
| `count_indexed_articles` (sqlite) | 0,77 dtk | sekali per proses (di-cache) |
| Buka koleksi + `count()` (4.593 chunk) | 3,5 dtk | sekali per proses |
| `collection.query` (ef_search 2000, 40 kueri) | median 28 ms, maks 93 ms | 2026-10-03 terukur median 9,8 ms dengan memori lebih lega |
| `collection.get` Narasi/Kesimpulan | median 7 ms | |
| Hitung token ~1.300 karakter | 0,8 ms | dijalankan di setiap rerun bila kotak teks berisi |

### 2.3 Belum terukur hari ini (K9)

- **Muat model bge-m3** dan **embedding satu kueri.** Model butuh sekitar 2,2 GB (cache HF
  `models--BAAI--bge-m3` 2,2 GB), sedangkan memori bebas hanya 1,5 GB. Kalau dimuat dalam keadaan ini,
  Windows akan mem-*page* dan angkanya tidak bermakna. Proses juga bisa dihentikan, seperti kejadian
  ingest 2026-09-27.
  Riwayat: model siap dalam **10 dtk** (`data/ingest_batch04-06_2026-10-03.log`, baris 13) dan
  **~67 dtk** pada pemeriksaan pertama demo (komentar `presentation.py`, `STEP_LOAD_MODEL`).
  Waktu embedding per kueri tidak tercatat di mana pun, jadi saya tidak menebaknya.

### 2.4 LLM (dari hasil evaluasi yang sudah ada; hanya bidang waktu, isi butir tidak dibaca)

`CallRecord.latency_s` mencakup jeda `_pace` (4 dtk antar-panggilan), throttling, dan retry
(`llm/gemini.py`, `t_start` sebelum `_before_call`).

| Sumber | n percobaan | median | p95 | maks |
| --- | --- | --- | --- | --- |
| `external_eval_liputan6_…jsonl` | 273 | 6,67 dtk | 67,9 dtk | 166,6 dtk |
| `external_eval_v1_idx1532_…jsonl` | 162 | 7,05 dtk | 28,0 dtk | 44,4 dtk |

Token masuk median ~2.500 per panggilan. Tidak ada percobaan yang butuh panggilan format ulang.

### 2.5 Yang dimuat ulang setiap kali halaman berinteraksi

Streamlit menjalankan ulang seluruh `main()` pada setiap interaksi.

- Setiap rerun menjalankan `set_page_config`, `st.html(READING_CSS)`, `render_header` (jumlah artikel
  dari cache, catatan cakupan dihitung ulang, murah), dan `tester_mode_enabled()` (membaca env dan
  secrets).
- Kalau kotak teks berisi: `count_claim_tokens` (tokenizer dari cache, <1 ms).
- **LLM tidak pernah dipanggil saat rerun.** Hanya `run_check` di cabang `if clicked:` yang
  memanggilnya, dan hasilnya disimpan di `st.session_state`. Ini sudah benar.
- Yang mahal hanya terjadi sekali per proses, tetapi semuanya **pada pengguna pertama**: impor (~28 dtk),
  tokenizer (3-102 dtk) saat pertama mengetik, lalu koleksi (3,5 dtk) dan model (10-67 dtk) saat
  pertama menekan Periksa.

Usulan: (a) `HF_HUB_OFFLINE=1` setelah model terunduh, yang menghapus pencilan 102 dtk dan cek
jaringan; (b) siapkan sumber daya saat start, misalnya dimuat di halaman pertama dengan pesan
"Menyiapkan…", atau pemanasan di container sebelum HEALTHCHECK menyatakan sehat, sehingga pengguna
pertama tidak menanggungnya; (c) satu tokenizer.

---

## 3. Usulan struktur baru

Prinsip: hanya tiga lapisan yang punya fungsi nyata. Berkas terkunci tidak dipindah.

```
src/
  app.py            # titik masuk: st.navigation([beranda, tentang]); setelan halaman; muat CSS sekali
  ui/
    beranda.py      # halaman beranda + hasil (render saja)
    tentang.py      # halaman Tentang (render saja)
    components.py   # potongan render bersama (kartu, pil status, kotak cek); semua teks di-escape
    style.css       # SATU-SATUNYA CSS kustom
  presentation.py   # TETAP: Answer/hasil layanan -> ResultView; salinan teks; gaya status; tabel saran
  service.py        # BARU, tanpa Streamlit: validasi masukan, batas laju per sesi, jalankan
                    #   retrieve + AnswerGenerator, waktu per tahap, galat bertipe, catatan aktivitas
  resources.py      # BARU, tanpa Streamlit: buka koleksi baca-saja + cek ef_search, muat model,
                    #   tokenizer, statistik indeks (jumlah artikel, tanggal terakhir dari metadata)
  settings.py       # BARU: konfigurasi terpusat (env var, batas masukan, batas laju, jalur log,
                    #   HF offline). Konstanta milik berkas terkunci (TOP_K, MAX_SEQ_LENGTH) DIRUJUK,
                    #   tidak disalin.
  evaluation_facts.py  # BARU, kecil: angka 36/46, 10/45, 48/50 dibaca dari berkas hasil yang
                    #   di-commit; dipakai halaman Tentang dan uji kesesuaian dengan README
  activity_log.py   # Tahap 3: JSON per baris + rotasi, tanpa isi pesan
  generator.py, retriever.py, chunker.py   # TIDAK DISENTUH
```

**Yang dipindah:**
- `count_indexed_articles` dari `presentation.py` ke `resources.py`;
- `load_collection` dari `app.py` ke `resources.py`;
- `check_claim` dari `app.py` ke `service.py`;
- angka evaluasi dari `presentation.evaluation_scope_note` ke `evaluation_facts.py`;
- setelan env `DISABLE_SAFETENSORS_CONVERSION` dari efek samping `import ingest` ke `settings.py`
  (ingest tetap menyetelnya sendiri untuk CLI). Pengecualian `I001` di `ruff.toml` untuk app.py lalu
  bisa dihapus.

**Yang dihapus:**
- rantai "mungkin terkait" (K6);
- `count_query_tokens`, karena tokenizer cukup satu;
- `escape_markdown`/`markdown_link`, bila semua render beralih ke HTML ber-escape. Kalau ada yang
  tetap Markdown, satu fungsi dipertahankan;
- `READING_CSS` inline, pindah ke `style.css`.

**Yang sengaja tidak dibuat:** antrean, worker, API HTTP terpisah, basis data log, atau kelas abstrak
baru. `service.py` adalah fungsi biasa yang menerima sumber daya sebagai argumen, sehingga bisa diuji
dengan objek palsu dari `tests/_fakes.py`. `app.py` hanya membungkus `resources` dengan
`st.cache_resource` dan statistik indeks dengan `st.cache_data`.

---

## 4. Versi Python

Sumber: PyPI JSON API (`https://pypi.org/pypi/<paket>/<versi>/json`: `requires_python`,
classifier, dan nama berkas wheel `manylinux…x86_64`), indeks `https://download.pytorch.org/whl/cpu/torch/`,
dan siklus rilis resmi `https://peps.python.org/api/release-cycle.json`. Semuanya diambil 2026-10-22.

- **Dipakai sekarang:** Python **3.11.4** (`.venv`). 3.11 berstatus *security*, EOL 2027-10.
- **Python terbaru:** **3.15** (rilis pertama 2026-10-09).

| Paket (versi terpatok) | Classifier tertinggi | Wheel Linux x86_64 |
| --- | --- | --- |
| torch 2.14.0 | 3.14 | cp310-cp314 (PyPI); indeks CPU juga cp315 |
| transformers 5.17.0 | 3.14 | murni Python |
| sentence-transformers **6.1.0** | **3.13** (6.2.0: 3.14) | murni Python |
| chromadb 1.5.9 | tidak ada classifier; `>=3.9` | cp39-abi3 (berlaku untuk versi lebih baru) |
| google-genai 2.24.0 | 3.14 | murni Python |
| streamlit 1.64.0 | 3.14 | murni Python |
| requests **2.31.0** | **3.11** (2.34.2: 3.14) | murni Python |
| beautifulsoup4 4.12.2 | tidak ada | murni Python |
| tzdata 2026.4 | tidak ada | data |
| pytest 9.1.1 / ruff 0.16.9 | 3.15 / 3.14 | |
| openpyxl 3.1.5 (dev; sudah versi terbaru) | 3.11 | murni Python |
| Dependensi biner tak langsung yang terpasang (numpy 2.4.6, scipy 1.17.1, onnxruntime 1.30.0, pyarrow 25.0.1, tokenizers 0.23.2, safetensors 0.8.0, pydantic_core, grpcio, …; 29 paket) | | **semuanya punya wheel cp314 atau abi3**; numpy 2.4.6, scipy 1.17.1, onnxruntime 1.30.0, pyarrow 25.0.1 **tidak punya cp315** |

**Kesimpulan:**
- **3.15 tidak didukung:** transformers, streamlit, dan google-genai belum mencantumkannya, dan beberapa
  paket biner tak punya wheel cp315.
- **3.14 adalah versi tertinggi yang didukung**, dengan dua syarat: `sentence-transformers` naik ke
  6.2.0 dan `requests` naik ke 2.34.2 (K7). Kenaikan `requests` juga menutup celah keamanan versi lama
  (bagian 6, butir 9).
- `openpyxl` (dev, untuk berkas tinjauan manusia) tidak mencantumkan versi di atas 3.11 sama sekali,
  bahkan di versi terbarunya. Tidak ada versi lain untuk dipilih, jadi dicatat sebagai pengecualian.
- Tanpa kenaikan apa pun, pembacaan classifier yang ketat hanya memberi **3.11** (karena
  `requests` 2.31.0).
- Image `python:3.14-slim-trixie` tersedia (Docker Hub; tag terbaru yang terlihat 3.14.8).

**Risiko pindah versi:** `sentence-transformers` ada di jalur embedding. Setelah pindah, wajib dijalankan
`evaluation.retriever_exactness`, `index_check` lengkap (termasuk embedding ulang sampel, target kosinus
1,000000), dan pembandingan top-3 64 kueri tetap dengan lingkungan lama. Semua selisih dilaporkan.

---

## 5. Rancangan Docker dan CI

### 5.1 Docker

- **Dockerfile multi-stage.**
  - Tahap *builder*: `python:3.14-slim-trixie@sha256:<digest>`, venv di `/opt/venv`, torch
    `2.14.0+cpu` dari indeks CPU PyTorch (tanpa CUDA, jauh lebih kecil), lalu `requirements.txt`
    terpatok.
  - Tahap *runtime*: base yang sama, menyalin hanya venv, `src/`, `.streamlit/config.toml`, dan
    `testset/eksternal_hasil_per_butir.json` (sumber angka halaman Tentang, sudah publik).
    `config/` ikut hanya bila K6 tidak disetujui.
  - Berjalan sebagai pengguna `app` (uid 10001).
  - Env: `PYTHONPATH=src`, `HF_HOME=/models`, `HF_HUB_OFFLINE=1`,
    `DISABLE_SAFETENSORS_CONVERSION=1`, `PYTHONDONTWRITEBYTECODE=1`.
- **HEALTHCHECK:** `python -c "urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"`.
  Image slim tidak punya curl, dan saya tidak menambah paket.
- **`.dockerignore` daftar-putih:** `*` lalu `!src/`, `!requirements*.txt`, `!.streamlit/config.toml`,
  `!testset/eksternal_hasil_per_butir.json`; `**/__pycache__` tetap dikecualikan. Dengan begitu
  `.env`, `data/`, `archive/`, log, `.streamlit/secrets.toml`, dan cache model tidak mungkin terbawa.
- **`docker-compose.yml`:**
  - Layanan `demo`: `ports: "127.0.0.1:8501:8501"` (hanya mesin ini), `env_file: .env`,
    `read_only: true` + `tmpfs: /tmp`. Volume: `./data/chroma` → `/app/data/chroma` (**baca-tulis**:
    ChromaDB menulis ulang berkas saat koleksi dibuka, lihat CLAUDE.md), `hf-cache` → `/models`,
    `./logs` → `/app/logs`.
  - Layanan `tools` (profil `tools`, tidak ikut `up`) untuk:
    - `docker compose run --rm tools python src/ingest.py`
    - `docker compose run --rm tools python -m evaluation.index_check`
    - `docker compose run --rm tools python -m evaluation.retriever_exactness`
    - unduh model pertama kali dengan `HF_HUB_OFFLINE=0`.
  - `articles.json` dipasang hanya ke `tools`.
- **Aturan operasi:** hentikan `demo` sebelum ingest. Dua proses yang membuka indeks bersamaan berisiko
  merusak sqlite.
- **RAM:** model ~2,2 GB + torch + Streamlit → batas container ≥ 4 GB, saran `.wslconfig`
  `memory=6GB`. Di laptop ini, dengan IDE terbuka, memori bebas hanya 1-1,5 GB, jadi Docker Desktop
  dan IDE berbarengan akan sesak. Ini dicatat di README.
- **Risiko Windows:** bind mount dari drive Windows ke WSL2 lambat untuk sqlite dan bisa bermasalah
  dengan penguncian berkas. Alternatifnya named volume yang diisi sekali. Perlu diuji di Tahap 2
  sebelum dipilih.
- **Pembaruan terjadwal:** tetap Task Scheduler. Nanti bisa dipindah dengan meminta Task Scheduler
  menjalankan `docker compose run --rm tools python -m scraping.scheduled`. Catatannya: notifikasi
  Windows dan berkas `PERHATIAN_PEMBARUAN.txt` perlu jalur yang terlihat dari host, dan jaringan
  container perlu diizinkan.

### 5.2 CI (GitHub Actions; remote `origin` = GitHub)

- Pemicu: `push` dan `pull_request`; `permissions: contents: read`; aksi dipatok ke SHA; tanpa
  rahasia.
- Langkah:
  - `actions/checkout` dengan `fetch-depth: 0` dan tag. Ini wajib: `test_v1_jsonl_unchanged_since_tag`
    membandingkan dengan tag `testset-v1` dan akan **dilewati diam-diam** (`pytest.skip`) bila tag
    tidak ada, sehingga uji kunci melemah tanpa ketahuan.
  - setup-python 3.14 (sama dengan container); torch CPU dari indeks CPU; `pip install -r
    requirements-dev.txt`.
  - `ruff check src tests`.
  - `pytest`, dengan `HF_HUB_OFFLINE=1` dan `HF_HOME` kosong sebagai jaminan tidak ada model
    yang diunduh.
  - Uji kunci dijalankan sebagai langkah tersendiri agar terlihat jelas.
- **Simulasi sudah dijalankan:** checkout bersih (worktree tanpa `data/`, tanpa `.env`, `HF_HOME`
  kosong, `HF_HUB_OFFLINE=1`) menghasilkan **525 lolos, 5 gagal**. Kelimanya
  `tests/test_testset_eval.py` (`test_main_*`, `test_circuit_breaker_*`, `test_run_flag_*`) karena
  `evaluation.testset_eval` menulis log ke `data/llm_calls.log` dan folder `data/` tidak ada. Perbaikan
  di sisi uji: arahkan jalur log ke `tmp_path`. Tidak ada uji yang memanggil Gemini atau mengunduh
  model.
- **Ruff saat ini 29 temuan**, dua di berkas terkunci: `generator.py:316` ISC004 dan `chunker.py:17`
  I001. Keduanya ditangani lewat `per-file-ignores` di `ruff.toml` dengan alasan "berkas terkunci",
  bukan dengan menyunting berkasnya. Sisanya (27) dirapikan di Tahap 2, karena CI menuntut ruff bersih.

---

## 6. Risiko keamanan

| # | Risiko | Bukti | Penanganan (tahap) |
| --- | --- | --- | --- |
| 1 | **Rujukan dari `references_filtered`** akan menampilkan sumber hoaks | K1 | pakai `references` + `display_references` (T1) |
| 2 | **XSS** saat beralih ke HTML kustom. Sekarang aman karena semua lewat `escape_markdown`; desain baru butuh `st.html`/HTML | `presentation.py:784` | `html.escape` semua teks dinamis; tautan hanya `http/https` dari metadata (`urlparse` + daftar skema); uji dengan `<script>`, `<img onerror>`, `javascript:` (T1, diuji ulang T3) |
| 3 | **Traceback tampil di browser:** `client.showErrorDetails` bawaan `"full"` (`streamlit config show`) | config.toml tidak menyetelnya | `showErrorDetails = "none"` (T1) |
| 4 | **Satu pengguna bisa menghabiskan kuota** (RPD 500, dibagi dengan evaluasi); tidak ada batas per sesi | `app.run_check` | usulan angka di bawah (T3) |
| 5 | **Buku besar kuota tidak aman antar-utas** | 1.3 butir 7 | kunci `threading.Lock` di `DailyLedger.add/_save` dan `RateLimiter.acquire` (`llm/`, tidak terkunci) (T3) |
| 6 | Kunci API bocor | `llm/secrets.redact` (pola `AIza…`) dipakai di galat provider dan app | kunci hanya dari env (compose `env_file`); log aktivitas tanpa teks galat bebas; uji bahwa `redact` diterapkan pada semua jalur galat layanan (T3) |
| 7 | Mode penguji aktif dari luar | hanya `DEMO_TESTER_MODE` atau `secrets.toml`; tidak ada query param | `secrets.toml` tidak masuk image; uji bahwa query param tidak berpengaruh (T3) |
| 8 | XSRF/CORS dimatikan | bawaan `enableXsrfProtection = true`, `enableCORS = true` | tidak diubah; uji konfigurasi yang gagal bila keduanya dimatikan (T2) |
| 9 | Dependensi usang: `requests` 2.31.0 (2023) punya celah yang diperbaiki di 2.32.x. Saya ingat CVE-2024-35195 dan CVE-2024-47081 tetapi **belum memverifikasinya** | requirements.txt | naik ke 2.34.2 (K7); audit penuh butuh `pip-audit` = dependensi baru, perlu izin (T2) |
| 10 | Revisi model tidak dipatok: `SentenceTransformer("BAAI/bge-m3")` memuat cabang `main`; bila BAAI mengubahnya, embedding kueri berubah tanpa ketahuan | `ingest.load_model`; cache lokal = commit `5617a9f61b028005a4858fdac845db406aefb181` | patok `revision=` ke commit itu (ingest.py tidak terkunci; bobot sama, jadi angka tidak berubah). Perlu persetujuan karena menyentuh jalur embedding (T2) |
| 11 | Prompt injection | prompt aturan 8; URL dibuang (`strip_urls`); status dan tautan dari metadata | dengan K5, teks bebas LLM tidak tampil ke umum; uji injeksi dengan provider palsu (keluaran berisi URL/instruksi) tanpa mengubah prompt (T3) |
| 12 | Privasi isi pesan | demo tidak menulis log berkas; Gemini tier gratis memakai konten untuk perbaikan produk (CLAUDE.md, "Privasi data") | log aktivitas tanpa isi pesan (T3); kalimat privasi di halaman Tentang dan di bawah kotak input ("Tanpa nomor telepon atau data pribadi", dari acuan) (T1) |
| 13 | Container berjalan sebagai root atau port terbuka ke LAN | | non-root, `read_only`, port 127.0.0.1 (T2) |
| 14 | Indeks rusak bila ingest dan demo membuka bersamaan | perilaku ChromaDB (CLAUDE.md) | dokumentasi + layanan `tools` terpisah; hentikan demo sebelum ingest (T2) |

**Usulan batas laju** (bisa disetel di `settings.py`):
- per sesi: jeda minimum 15 dtk antar-pemeriksaan dan maksimum 10 pemeriksaan per jam;
- global: maksimum 60 pemeriksaan per jam per proses;
- **cadangan harian 100 permintaan** untuk evaluasi: demo berhenti di 400 dari 500 menurut buku besar.

Keterbatasan yang jujur: sesi Streamlit dibuat ulang setiap kali halaman dimuat ulang, jadi batas per
sesi bisa dilewati. Yang benar-benar melindungi kuota adalah batas global dan cadangan harian.

---

## 7. Pembagian kerja dan perkiraan

Perkiraan waktu adalah waktu kerja saya, belum termasuk waktu tinjauan Anda.

| Tahap | Isi | Perkiraan | Risiko utama |
| --- | --- | --- | --- |
| **1. Tampilan** | uji kunci retriever/chunker (K8); `settings.py`, `resources.py`, `service.py` (alur saja; batas laju dan log di T3); `ui/` + `style.css`; dua halaman via `st.navigation`; tabel judul/saran per label; 3 contoh klaim (diusulkan, ditunjukkan, dijalankan = maksimal 3-6 panggilan Gemini); `evaluation_facts.py` + uji kesesuaian README; penghapusan K6; tangkapan layar | 2-3 sesi | Streamlit membatasi tata letak (kontrol `st.checkbox`/`st.expander`/`st.text_area` tidak bisa ditata persis seperti HTML acuan, sehingga butuh CSS pada kelas internal Streamlit yang bisa berubah antarversi); **tangkapan layar otomatis butuh alat** (Playwright = dependensi baru, perlu izin, atau Anda yang mengambil; sesi browser Claude in Chrome bisa menjadi alternatif bila Anda izinkan); memori sempit saat menjalankan demo dan LLM |
| **2. Docker, Python, CI** | Python 3.14 + kenaikan K7; Dockerfile, compose, `.dockerignore`; patok revisi model; CI; ruff bersih; perbaikan 5 uji CI; README cara menjalankan; pengukuran ulang retrieval di lingkungan baru | 2 sesi | pembangunan image butuh RAM dan unduhan ~1 GB; bind mount Windows/WSL2; perubahan numerik embedding di versi baru (harus dilaporkan, tidak bisa dijamin nol); waktu CI karena torch |
| **3. Keamanan, log, galat** | validasi di layanan; escape + uji XSS; batas laju; kunci antar-utas buku besar; `activity_log.py` (JSON per baris, `RotatingFileHandler`, tanpa isi pesan) + ringkasan CLI untuk Anda; galat bertipe → pesan awam; uji injeksi; ADR; diagram README | 2 sesi | uji injeksi yang bermakna butuh panggilan Gemini sungguhan (kuota) selain provider palsu; ringkasan log harus tetap tidak bisa menautkan sesi ke isi pesan |

Waktu sebelum dan sesudah diukur di Tahap 1 dan 3 dengan skrip yang sama
(`perf_light` + pengukuran model, bila memori memungkinkan).
