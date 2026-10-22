# Tahap 0: audit dan rencana demo portofolio

Disusun 2026-10-22 di branch `tahap-0-audit`. Tidak ada kode yang diubah: isi branch ini hanya berkas
ini. Semua angka di bawah diukur pada hari itu, kecuali yang ditandai "riwayat" beserta sumbernya.

Garis dasar saat audit (commit `a704d5b`): `pytest` 530 lolos (65,8 dtk); `ruff check src tests`
29 temuan lama, dua di antaranya di berkas terkunci (lihat 5.3).

---

## Koreksi atas spesifikasi (dicatat atas permintaan pemilik proyek, 2026-10-22)

Tiga hal di spesifikasi awal ternyata keliru setelah dicocokkan dengan kode. Yang berlaku adalah
koreksinya.

1. **Rujukan diambil dari `references`, bukan `references_filtered`.** `references_filtered` berisi
   tautan yang dibuang (`scraping/links.py` `filter_references`). Verifikasi data: lihat 8.1.
2. **Warna status di berkas acuan tidak mengikuti skema status yang ada, dan hijau tidak boleh
   dipakai.** Skema di `.streamlit/config.toml` tetap berlaku, termasuk kuning zaitun untuk
   PARODI/SATIRE/SATIR/KOMEDI. Berkas acuan tidak diubah; setiap penyimpangan dicatat di laporan
   Tahap 1.
3. **Uji kunci selama ini hanya menjaga `generator.py` dan prompt/skema**
   (`tests/test_testset_locks.py`), bukan `retriever.py` dan `chunker.py`. Hash keduanya hanya
   tercatat di dokumen dan `testset/eksternal_butir.json` (lihat 8.2).

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
| 9 | Dependensi usang: `requests` 2.31.0. Terverifikasi lewat GitHub Security Advisory (`gh api /advisories?ecosystem=pip&affects=requests@2.31.0`, 2026-10-22): [GHSA-9wx4-h78v-vm56](https://github.com/advisories/GHSA-9wx4-h78v-vm56) (CVE-2024-35195, sedang, diperbaiki 2.32.0), [GHSA-9hjg-9r4m-mvj7](https://github.com/advisories/GHSA-9hjg-9r4m-mvj7) (CVE-2024-47081, sedang, 2.32.4), [GHSA-gc5v-m9x4-r6x2](https://github.com/advisories/GHSA-gc5v-m9x4-r6x2) (CVE-2026-25645, sedang, 2.33.0) | requirements.txt | naik ke 2.34.2, menutup ketiganya (disetujui, T2); audit penuh butuh `pip-audit` = dependensi baru, perlu izin |
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

---

## 8. Lanjutan Tahap 0: verifikasi atas keputusan pemilik proyek (2026-10-22)

### 8.1 `references` tidak memuat `claim_sources` maupun tautan yang dibuang

- **Kode:** `filter_references` (`scraping/links.py:153-185`) memasukkan setiap URL ke tepat satu
  daftar. URL yang cocok dengan `claim_sources` atau terkena `blocked_reason` masuk
  `references_filtered`; sisanya masuk `references`. `chunker.py:146` melarang `claim_sources`,
  `references_filtered`, dan `references_raw` masuk metadata, sehingga yang sampai ke indeks hanya
  `references`. `presentation.display_references` menyaringnya sekali lagi saat tampil.
- **CLAUDE.md** (butir (e) dan (f), 2026-10-03) mencatat "0 rujukan tampil berdomain daftar-blokir,
  0 rujukan tampil yang juga `claim_sources`".
- **Diperiksa ulang hari ini** (baca-saja, pencocokan string persis):

  | Sumber | refs ∩ `claim_sources` | refs ∩ `references_filtered` | terblokir kebijakan kini | beda dari `articles.json` |
  | --- | --- | --- | --- | --- |
  | `articles.json`, 1.532 artikel | 0 | 0 | 0 | - |
  | metadata indeks, 4.593 chunk | 0 | 0 | 0 | 0 |

- **Pengecualian yang disengaja:** URL "Sumber:" berdomain `*.go.id` atau ada di
  `TRUSTED_SOURCE_DOMAINS` tidak dimasukkan ke `claim_sources` (keputusan 2026-10-03; 32110, 31532,
  33497), jadi URL itu boleh tampil sebagai rujukan. Uji Tahap 1 menjaga aturan apa adanya:
  tidak ada URL dari `claim_sources` atau `references_filtered` yang pernah tampil.

### 8.2 Hash berkas terkunci: COCOK, boleh dikunci

`testset/eksternal_butir.json`, `hash_berkas_terkunci` (dibekukan 2026-10-17, commit `fa7464c`;
juga dikutip singkat di `docs/rancangan_evaluasi_eksternal.md` bagian 8):

| Berkas | Tercatat saat pembekuan | Saat ini (sha256, CRLF→LF) |
| --- | --- | --- |
| `src/retriever.py` | `68321aeda8cc46dadd4faa6eaa506a989077ad5fdc5b0e4675c5d16169065ab8` | sama |
| `src/chunker.py` | `6d9de5ced2e487a9b972877863109fc552c7de958dbf55b77a069dc01aaef475` | sama |
| `src/generator.py` (pembanding) | `e5a5ba5a72c0a3c14db37a3aee646ef5b3b7e34e036718947493955cf6df651a` | sama |

`git diff fa7464c HEAD -- src/retriever.py src/chunker.py src/generator.py` kosong. Commit terakhir
yang menyentuh keduanya: `623f300` (2026-09-21) dan `927649d` (2026-09-25). Uji kunci Tahap 1
membaca nilai yang diharapkan dari `testset/eksternal_butir.json`, bukan dari salinan baru, sehingga
tetap ada satu sumber.

### 8.3 Revisi bge-m3: terbukti `5617a9f61b028005a4858fdac845db406aefb181`

1. Cache HF lokal hanya punya **satu** snapshot, `snapshots/5617a9f…`, berkasnya bertanggal
   2026-09-19/20 (`pytorch_model.bin` 2.271.145.830 byte). `refs/main` berisi hash yang sama dan
   tidak berubah sejak 2026-09-19 23:37. Indeks 1.532 dibangun 2026-10-03
   (`data/ingest_batch04-06_2026-10-03.log`), jadi semua pemuatan sejak 19 Sep, termasuk ingest itu,
   memakai snapshot ini.
2. Hugging Face Hub (`/api/models/BAAI/bge-m3/revision/main`, 2026-10-22): `main` = `5617a9f…`,
   commit 2024-07-03. `main` tidak bergerak sejak sebelum proyek dimulai.
3. `index_check` lengkap 2026-10-03: 8 sampel di-embed ulang, kosinus 1,000000 terhadap vektor
   tersimpan, termasuk chunk dari kelompok tertua (450 chunk basis) dan terbaru.
4. Catatan riwayat: 450 chunk basis sempat dibuat dari safetensors PR #130 saat torch 2.5.1, lalu
   seluruh indeks dibangun ulang (`--rebuild`, 2026-09-21) dengan `.bin` dari `main`. Bobot PR #130
   terbukti identik bit-per-bit dengan `main` (CLAUDE.md).

Log ingest sendiri tidak mencatat hash revisi; buktinya dari (1)-(3). Pematokan
`revision="5617a9f61b028005a4858fdac845db406aefb181"` karenanya tidak mengubah bobot.

### 8.4 `showErrorDetails`

`streamlit config show` dari paket terpasang (streamlit 1.64.0) mencantumkan nilai sah `"full"`,
`"stacktrace"`, `"type"`, `"none"`, plus `True`/`False` yang sudah usang; bawaannya `"full"`. Yang paling
ketat adalah `"none"`: browser hanya menampilkan pesan galat umum, sedangkan jenis galat, pesan
lengkap, dan traceback hanya ke konsol.

### 8.5 Playwright (dependensi pengembangan saja)

Versi terbaru 1.64.0 (`requires_python >=3.10`; dependensi `pyee`, `greenlet`). Wheel `win_amd64`
**38,7 MB**, `manylinux1_x86_64` **48,3 MB** (PyPI). Browser Chromium diunduh terpisah dengan
`playwright install chromium`; ukurannya baru saya laporkan setelah terpasang, tidak saya tebak.
Rencananya hanya di `requirements-dev.txt`, tidak masuk image (dijamin daftar-putih
`.dockerignore`) dan tidak diimpor `src/`.

### 8.6 Logo (`docs/desain_tampilan/logo.jpg`)

| Sifat | Nilai |
| --- | --- |
| Format | JPEG, RGB, 445.770 byte |
| Ukuran | 1024 × 1024 px |
| Latar transparan | **Tidak.** JPEG tidak punya kanal alfa; latarnya putih (`#FFFFFF`-`#FBF9FA` di tepi) |
| Di latar `#F6F7F9` | Kotak putih logo **terlihat** sebagai persegi yang sedikit lebih terang. Ilustrasi bunglon (gelap) tetap terbaca di 32 px ke atas; di 16 px tinggal gumpalan; jaring garis biru muda dan teks kecil di dalamnya hilang di bawah ~64 px. Diperiksa dengan pratinjau pengecilan di scratchpad, bukan berkas proyek. |

Usulan:
- **Struktur:** `assets/brand/logo.jpg` sebagai salinan byte-identik, dengan sha256 dicatat di
  `assets/brand/README.md`. Turunannya diletakkan berdampingan: `favicon-32.png` (32×32) dan
  `logo-96.png` (96×96, untuk header 48 px di layar 2×). Keduanya dibuat dengan Pillow (sudah
  terpasang sebagai dependensi Streamlit, bukan dependensi baru), hanya diskalakan dengan LANCZOS:
  persegi ke persegi, tanpa potong, tanpa pewarnaan ulang.
- **Docker:** `!assets/brand/` di daftar-putih `.dockerignore`.
- **Tampilan:** karena latarnya tidak bisa dibuang tanpa mengubah logo, logo diletakkan di petak putih
  bersudut membulat dengan garis `#EAECF0`. Dengan begitu kotak putihnya tampak disengaja.
  Logonya sendiri tidak diubah.
- **Catatan desain:** logo memuat efek pendar dan gradasi, sedangkan aturan tampilan melarang
  gradien. Saya anggap aturan itu berlaku untuk elemen antarmuka, bukan aset merek Anda.
- **Pemindahan dilakukan di awal Tahap 1** (di branch tahap 1), bukan di main, karena commit ini
  hanya dokumentasi.

---

## 9. Bagian C (menunggu persetujuan)

### 9.1 Matriks versi Python

Dasar: versi terpasang (`pip freeze`, 124 paket) dan PyPI (bagian 4).
- **Semua paket biner yang terpasang punya wheel Linux x86_64** untuk cp312, cp313, dan cp314
  (atau abi3), pada versi yang sama dengan sekarang.
- **Kenaikan `requests` 2.31.0 → 2.34.2** (minor) sudah disetujui untuk semua pilihan.
- **`openpyxl` 3.1.5** (dev) tidak mencantumkan versi di atas 3.11 di versi mana pun.

| Python | Paket yang harus naik | Mayor? | torch / transformers / sentence-transformers |
| --- | --- | --- | --- |
| 3.12 | tidak ada (selain `requests`) | - | tetap 2.14.0 / 5.17.0 / 6.1.0 |
| 3.13 | tidak ada (selain `requests`) | - | tetap 2.14.0 / 5.17.0 / 6.1.0 (classifier tertinggi 6.1.0 = 3.13) |
| 3.14 | `sentence-transformers` 6.1.0 → **6.2.0** | tidak (minor) | torch dan transformers tetap; ST naik minor. Persyaratan 6.2.0 sama dengan 6.1.0 kecuali `huggingface-hub <3` (sebelumnya `<2`); yang terpasang 1.32.0, jadi tidak dipaksa naik |

- **Menurut kriteria Anda** (terbaru tanpa kenaikan mayor pada ketiganya), pilihannya **3.14**.
- **Catatan risiko:** `sentence-transformers` 6.2.0 diunggah **2026-10-21, sehari sebelum
  pengecekan ini**, dan paket ini ada di jalur embedding.
- **Usulan saya:** pakai 3.14 bila saat Tahap 2 dimulai versi 6.2.0 sudah berumur ≥ 2 minggu
  (sejak 2026-11-04) dan lolos pembuktian di bawah. Kalau belum, pakai 3.13: tumpukan embedding
  tidak berubah sama sekali, dan naik ke 3.14 bisa dilakukan kemudian.

**Rencana pembuktian embedding.** Berlaku juga untuk 3.11 di dalam container, karena Linux, wheel
Linux, dan pustaka BLAS sudah berbeda dari venv Windows.

1. **Sebelum pindah** (lingkungan sekarang): pada **salinan** indeks produksi, pilih 200 id chunk
   dengan `random.Random(20261022).sample(sorted(ids), 200)`. Simpan id-nya. Simpan juga top-3
   (id + skor) dari 64 kueri tetap milik `evaluation.retriever_exactness`, dihitung dengan model di
   lingkungan sekarang.
2. **Di lingkungan baru:** embed ulang teks 200 chunk itu dengan `ingest.load_model()` (revisi
   dipatok, normalisasi sama). Hitung kosinus terhadap vektor tersimpan: minimum, rata-rata,
   persentil-1.
3. Jalankan `evaluation.retriever_exactness` (HNSW vs eksak di lingkungan baru) dan hitung ulang
   top-3 64 kueri tadi. Bandingkan dengan langkah 1: jumlah kueri dengan top-3 berbeda dan
   maks |Δskor|.
4. **Ambang, ditetapkan sebelum mengukur:**
   - **SAMA:** kosinus minimum ≥ 0,99999, rata-rata ≥ 0,999999, `retriever_exactness` kode
     keluar 0, dan top-3 identik pada 64/64 kueri.
   - **BEDA KECIL:** kosinus minimum di [0,999; 0,99999), top-3 tetap identik 64/64, dan
     `retriever_exactness` 0. Dilaporkan; pemilik proyek memutuskan.
   - **BEDA:** kosinus minimum < 0,999, atau ada top-3 yang berbeda, atau `retriever_exactness`
     ≠ 0. Berhenti dan laporkan; tidak ada penggabungan.
   - Dasar ambang: `index_check` pada lingkungan yang sama selalu memberi 1,000000 (6 desimal).
     Perbedaan antarplatform yang hanya akibat urutan operasi floating point seharusnya tetap di
     atas 0,99999. Angka di bawah itu menandakan perbedaan model atau tokenizer, bukan derau.
5. Angka evaluasi di README tetap merujuk lingkungan saat evaluasi (Windows, Python 3.11.4); hasil
   pembuktian dicatat berdampingan.

Pembuktian ini juga menuntut **pematokan semua dependensi tak langsung** untuk image. Sekarang
`requirements.txt` hanya mematok dependensi langsung, sehingga image yang dibangun bulan depan bisa
mendapat numpy, tokenizers, atau huggingface-hub yang berbeda. Usulan: berkas constraints hasil
`pip freeze` lingkungan yang sudah dibuktikan. Ini bukan dependensi baru.

### 9.2 Pengukuran bge-m3: TIDAK dijalankan

Memori bebas saat dicek: **741 MB**, lalu **854 MB**. Pemakai terbesar (working set per nama
proses): chrome 2.740 MB, Antigravity IDE 2.724 MB, Memory Compression 2.123 MB, node 1.939 MB,
svchost 1.213 MB. Di bawah ambang 3 GB, jadi tidak dipaksakan.

Skrip yang akan dipakai: muat model, lalu 20 kueri rekaan 1-3 kalimat yang ditulis baru dan bukan
dari set evaluasi. Hasilnya waktu muat, median dan p95 embedding per kueri, dan puncak memori proses
(`PeakWorkingSetSize` via `ctypes`, tanpa dependensi baru). Skrip menolak berjalan sendiri bila
memori bebas < 3 GB.

### 9.3 Struktur modul final Tahap 1

**Berkas baru**

| Berkas | Tanggung jawab |
| --- | --- |
| `src/settings.py` | Semua setelan dari env dan nilai bawaan: batas masukan, ambang peringatan token, batas laju, jalur log, nama env mode penguji, `HF_HUB_OFFLINE`, `DISABLE_SAFETENSORS_CONVERSION`, revisi model. Konstanta milik berkas terkunci (`TOP_K`, `MAX_SEQ_LENGTH`) dirujuk, tidak disalin. |
| `src/resources.py` | Tanpa Streamlit. Koleksi baca-saja + cek `ef_search`, model, tokenizer, statistik indeks (jumlah artikel, tanggal terakhir dari metadata `date` dd/mm/yyyy yang diurai, bukan dibandingkan sebagai string), dan **pemanasan** (9.4). Setiap sumber daya dimuat sekali per proses dengan kunci. |
| `src/service.py` | Tanpa Streamlit. `check(text, session) -> CheckOutcome`: validasi, batas laju (T3), **kunci proses yang menserialkan pemeriksaan** (alasan di bawah), panggil `AnswerGenerator(provider, retrieve)`, ambil Kesimpulan/Penjelasan dari koleksi, waktu per tahap, galat bertipe. |
| `src/evaluation_facts.py` | Angka 36/46, 10/45 (dari `testset/eksternal_hasil_per_butir.json`) dan 48/50 (dari `testset/v1_analysis.json`), dibaca dan dihitung, tidak diketik. |
| `src/ui/beranda.py`, `src/ui/tentang.py` | Render halaman saja. |
| `src/ui/components.py` | Potongan render bersama; semua teks dinamis lewat `html.escape`, tautan lewat satu fungsi yang hanya menerima `http`/`https`. |
| `src/ui/style.css` | Satu-satunya CSS kustom, dimuat sekali per rerun lewat satu `st.html`. |
| `assets/brand/` | Logo + turunan (8.6). |
| Uji: `test_service.py`, `test_resources.py`, `test_evaluation_facts.py` (termasuk kesesuaian dengan README), `test_ui_safety.py` (escape, skema tautan, tidak ada `claim_sources`/`references_filtered` yang tampil), uji konkurensi di `test_ledger.py`/`test_throttle.py`, uji kunci retriever/chunker di `test_testset_locks.py`. |

**Berkas yang berubah**
- `src/app.py`: titik masuk + `st.navigation`, membungkus `resources` dengan `st.cache_resource` dan
  statistik dengan `st.cache_data`.
- `src/presentation.py`: buang rantai "mungkin terkait", `count_indexed_articles`, catatan cakupan;
  tambah tabel judul/saran per label dan Kesimpulan apa adanya.
- `src/llm/ledger.py`, `src/llm/throttle.py`: `threading.Lock`.
- `src/ingest.py`: `revision=` di `load_model`.
- `.streamlit/config.toml`: `showErrorDetails = "none"`, aksen `#1F4E9E`.
- `ruff.toml`: pengecualian per berkas per aturan untuk `generator.py` ISC004 dan `chunker.py` I001;
  pengecualian `app.py` I001 dihapus.
- 27 berkas dengan temuan ruff, `tests/test_testset_eval.py` (folder sementara),
  `requirements-dev.txt` (Playwright).

**Dihapus**
- Di jalur demo: `RelatedThreshold`, `RELATED_DISABLED_NO_CONFIG`, `RELATED_THRESHOLD_CONFIG`,
  `RELATED_HEADING`, `RELATED_NOTE`, `RelatedArticle`, `index_key`, `load_related_threshold_config`,
  `resolve_related_threshold`, `related_articles`, bidang `ResultView.related` dan
  `Diagnostics.related_threshold`/`related_status`, `app.load_related_threshold`,
  `app.render_related`, serta uji-ujinya di `test_presentation.py`. Daftar final dicek ulang dengan
  `grep` saat dikerjakan.
- Juga: `app.count_query_tokens`, `READING_CSS`, dan `escape_markdown`/`markdown_link` bila tidak lagi
  dipakai.
- **Dipertahankan:** semua skrip/artefak di `src/evaluation/` dan `testset/`, serta
  `config/related_threshold.json`. Hasil `grep` 2026-10-22: berkas itu hanya dibaca `app.py`,
  `presentation.py`, dan `test_presentation.py`, tidak oleh skrip evaluasi mana pun. Isinya catatan
  kalibrasi (ambang `null` + alasannya per ukuran indeks). Setelah kode dihapus, berkas itu tidak
  dibaca kode lagi, tetapi tetap disimpan sebagai artefak kalibrasi; berkas ini juga diberi
  keterangan bahwa fiturnya dihapus dari demo.

**Alur pemanggilan**

```
ui/beranda.py  --(teks, id sesi)-->  service.check()
   service: validasi -> batas laju -> [kunci proses] ->
            AnswerGenerator(provider, retrieve_fn).answer(teks)      # generator.py, terkunci
               retrieve_fn = lambda q, k: retriever.retrieve(q, model, koleksi, top_k=k)  # terkunci
            -> ambil Kesimpulan + Penjelasan artikel terpilih dari koleksi (metadata/dokumen)
            -> CheckOutcome(answer, hits, waktu per tahap, jenis galat)
ui/beranda.py  <--  presentation.build_view(outcome)  ->  ui/components (HTML ber-escape)
```

**Mengapa pemeriksaan diserialkan per proses.** Generator mengambil catatan panggilannya dengan
`self.provider.records[n_before:]` (`generator.py`, `AnswerGenerator.answer`), sedangkan provider
dibagi semua sesi. Tanpa serialisasi, dua pemeriksaan serentak bisa saling mencampur `calls`, dan
`classify_failure` membaca `ans.calls`, sehingga jenis galat satu pengguna bisa berasal dari
pengguna lain. Karena generator terkunci, perbaikannya ada di lapisan layanan: satu kunci di sekitar
`answer()`. Biayanya kecil, karena throttle sudah menahan jeda 4 dtk antar-panggilan. Di bawah kunci
yang sama, `provider.records` dipangkas setelah tiap pemeriksaan, sehingga kebocoran memori 1.3 butir
8 tertutup tanpa menyentuh `llm/base.py`.

**Kunci buku besar.** `threading.Lock` di `DailyLedger` menutup balapan antar-utas di satu proses.
Demo dan skrip evaluasi adalah **proses berbeda** yang berbagi `data/quota_ledger.json`, dan kunci
utas tidak melindunginya. Usulan tambahan: kunci berkas dengan stdlib (berkas `.lock` lewat
`os.open(O_CREAT|O_EXCL)` dengan batas waktu). Bila tidak disetujui, aturannya didokumentasikan:
jangan menjalankan evaluasi dan demo bersamaan.

### 9.4 Pemanasan (warm-up)

Batasan Streamlit: `app.py` dieksekusi ulang di setiap rerun, sedangkan modul lain diimpor sekali per
proses (`sys.modules`). Tidak ada kait "server sudah mulai".

- `resources.start_warmup()` dipanggil dari `app.py` di setiap rerun, tetapi idempoten: kunci +
  penanda modul. Pada panggilan pertama ia menyalakan **satu utas daemon** yang memuat koleksi,
  tokenizer, dan model, serta membuat klien LLM.
- Fungsi `st.cache_resource` di `app.py` memanggil `resources.get_model()` dan sejenisnya, yang
  menunggu kunci yang sama. Pengguna yang datang saat pemanasan berjalan tidak memicu pemuatan
  kedua; ia menunggu yang sedang berjalan. Pengguna setelahnya tidak menunggu sama sekali.
- **UI:** selama pemanasan, kotak input tetap aktif dan tombol Periksa menampilkan "Menyiapkan
  sistem…". Statusnya diambil dari `resources.warmup_state()` (belum/berjalan/siap/gagal), tanpa
  angka teknis.
- **Docker:** HEALTHCHECK baru "sehat" bila `/_stcore/health` membalas **dan** pemanasan siap
  (berkas `/tmp/ready` ditulis utas pemanasan). `start_period` diatur sesuai waktu muat terukur.
  Pemanasan baru dimulai saat halaman pertama kali dibuka, jadi `docker compose up` menyertakan
  satu permintaan pembuka dari HEALTHCHECK ke halaman utama.
- Lokal tanpa Docker: pengguna pertama yang membuka halaman memicu pemanasan saat ia masih membaca
  dan mengetik. Waktu itu tumpang tindih dengan waktu muat, tidak lagi ditambahkan sesudah klik.
- Risikonya: memanggil `st.cache_resource` dari utas non-skrip memicu peringatan "missing
  ScriptRunContext". Karena itu utas pemanasan memanggil `resources` langsung, bukan fungsi
  ber-cache Streamlit.

### 9.5 Batas laju (usulan, Tahap 3)

| Batas | Nilai | Alasan |
| --- | --- | --- |
| Cadangan harian | demo berhenti di **400 dari 500** permintaan menurut buku besar | RPD 500 per proyek dibagi dengan evaluasi; 100 cukup untuk uji asap dan pemeriksaan kecil. Satu run evaluasi penuh (91 + 54 butir) tetap butuh hari tersendiri. |
| Global per jam | **60** pemeriksaan per proses | 400 tersebar minimal ~7 jam, jadi satu lonjakan tidak menghabiskan kuota sehari dalam satu jam. Masih jauh di bawah RPM 15 yang sudah dijaga `RateLimiter`. |
| Per sesi, jeda | **15 dtk** antar-pemeriksaan | Membaca satu hasil butuh lebih dari 15 dtk; klik ganda atau mengulang terus-menerus tertahan. |
| Per sesi, per jam | **10** pemeriksaan | Penggunaan wajar perorangan; mencegah satu tab memakai 1/6 jatah global per jam. |

Sesi Streamlit dibuat ulang setiap kali halaman dimuat ulang, jadi batas per sesi bisa dilewati.
Perlindungan yang sesungguhnya adalah batas global dan cadangan harian. Semua angka ada di
`settings.py`, dan pesannya ditulis dalam bahasa awam ("Coba lagi dalam N detik").

### 9.6 Status sembilan keputusan

| # | Keputusan | Status |
| --- | --- | --- |
| K1 | Rujukan dari `references` | **Diputuskan (A).** Diverifikasi di 8.1 |
| K2 | Warna status tetap seperti `config.toml`, termasuk kuning zaitun | **Diputuskan (A)** |
| K3 | Tanpa hijau; kotak 36/46 dan 10/45 netral, kategori sebagai teks | **Diputuskan (A)** |
| K4 | 1280px: satu kolom tengah | **Diputuskan (A).** Angka diusulkan: lebar isi maksimum **640px**. Itu ~70-80 karakter per baris pada 15px dan cukup untuk dua kolom "Pesan Anda / Yang diperiksa" (masing-masing ~300px) |
| K5 | Tampilkan Kesimpulan apa adanya; parafrase LLM hanya di panel penguji | **Menunggu konfirmasi.** Sesuai spesifikasi awal Anda, tetapi efek sampingnya belum Anda tanggapi |
| K6 | Hapus "Mungkin terkait" dari jalur demo | **Diputuskan (A).** Daftar di 9.3 |
| K7 | Versi Python dan kenaikan dependensi | **Sebagian.** `requests` disetujui (T2); versi Python menunggu (9.1) |
| K8 | Uji kunci retriever/chunker | **Diputuskan (A).** Hash cocok (8.2) |
| K9 | Pengukuran bge-m3 | **Menunggu.** Memori bebas < 3 GB (9.2) |

### 9.7 Perkiraan Tahap 1 (diperbarui)

**3-4 sesi kerja** (sebelumnya 2-3), karena bertambah: kunci + uji konkurensi, serialisasi di
layanan, pemanasan, perbaikan 27 temuan ruff, uji di folder sementara, logo + turunan, pemasangan
Playwright dan tangkapan layar 8 halaman, serta uji keamanan rujukan.

Risiko tambahan:
- tata letak Streamlit (CSS pada kelas internal yang bisa berubah antarversi);
- memori sempit saat menjalankan demo, model, dan Chromium bersamaan;
- pemilihan 3 contoh klaim butuh 3-6 panggilan Gemini.


---

## 10. Keputusan pemilik proyek atas bagian C (2026-10-22)

1. **K9:** pengukuran bge-m3 dijalankan setelah aplikasi lain ditutup (memori bebas 3,2-3,4 GB); hasil
   di `docs/laporan_tahap1.md` bagian 1.
2. **Python 3.13, tidak bersyarat.** Alasan: tidak menuntut kenaikan paket selain `requests` (torch,
   transformers, sentence-transformers tetap) dan masih didukung lama (EOL 2029-10). Python 3.14 bisa
   dipertimbangkan nanti, setelah sentence-transformers 6.2.0 cukup berumur.
3. **Pembuktian embedding:** ambang 9.1 disetujui, dengan dua tambahan yang ditetapkan sebelum mengukur:
   hasil di antara 0,999 dan ambang "SAMA" berarti lapor dan tunggu keputusan (tidak lanjut otomatis);
   pembuktian dijalankan di dalam container Linux yang akan dipakai (hasil Windows hanya pembanding).
4. **K5:** ya. Pengguna melihat Kesimpulan TurnBackHoax apa adanya; parafrase LLM hanya di panel penguji.
5. **Struktur modul** 9.3 disetujui; tidak menambah lapisan lain tanpa persetujuan.
6. **Konkurensi:** kunci layanan disetujui (pesan menunggu giliran + batas waktu tunggu + uji catatan
   tidak tercampur); kunci berkas antar-proses dengan stdlib disetujui (Windows dan Linux, kunci
   tertinggal tertangani). Aturan "jangan jalankan demo di container dan evaluasi di host bersamaan" ditulis
   di README dan CLAUDE.md.
7. **Pemanasan** disetujui: tanpa pemuatan ganda (dibuktikan uji dan log) dan tanpa panggilan LLM.
8. **Batas laju** disetujui: 15 dtk, 10/jam per sesi, 60/jam per proses, berhenti di 400 permintaan harian
   (buku besar yang sama dengan evaluasi). Batas per sesi bisa dilewati dengan memuat ulang halaman;
   perlindungan sebenarnya ada di batas global.
9. **Logo:** versi berlatar transparan dari pemilik proyek (`logo2.png`, 500×500) dipakai sebagai berkas
   asli di `assets/brand/`, tanpa petak putih, dengan turunan 32 dan 96 px.
10. **Pembagian ulang tahap:** Tahap 1 = tampilan, struktur modul, perbaikan (kunci, `showErrorDetails`,
    tokenizer, uji tanpa `data/`, ruff), uji kunci, pemanasan, escape, validasi, batas laju. Tahap 2 =
    Docker, Python 3.13, pembuktian embedding, requests 2.34.2, CI. Tahap 3 = catatan aktivitas,
    ringkasan, pola galat.
