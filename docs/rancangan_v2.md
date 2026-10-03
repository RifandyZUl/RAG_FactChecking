# Rancangan Versi 2

**Status: dokumen rancangan; belum ada kode Versi 2.** Disusun 2026-10-03 dari berkas di
repositori (daftar di bagian akhir); diperbarui pada hari yang sama dengan keputusan pemilik
proyek atas dua belas pertanyaan terbuka (bagian 0). Bila datanya tidak cukup untuk disimpulkan,
itu ditulis terus terang.

**Rancangan ini BELUM boleh dilanjutkan ke pembangunan.** Langkah pertama yang ditetapkan pemilik
proyek adalah mengukur apakah masalah pesan panjang memang terjadi pada pesan berantai ASLI
(bagian 10). Bila ternyata jarang, cakupan Versi 2 dipikir ulang.

Dokumen ini mengoreksi pemetaan lama di `testset/v1_temuan_untuk_v2.md` bagian 7 dan tabel
"Rencana Versi 2" di README: beberapa komponen di sana dicantumkan dengan bukti yang, setelah
diperiksa ulang, tidak mendukungnya.

---

## 0. Keputusan pemilik proyek (2026-10-03)

| # | Pertanyaan | Keputusan |
| --- | --- | --- |
| 1 | Cakupan | **Dipersempit: penanganan pesan panjang + pengukuran kebersihan rujukan.** Komponen lain tidak masuk, bahkan sebagai eksperimen (kuota terbatas, tidak ada bukti). |
| 2 | Grader | **Tidak masuk.** Generator sudah menilai kesamaan klaim; empat perbedaan yang mungkin dibawa grader tidak punya bukti. |
| 3 | "Mungkin terkait", verdict ketiga | **Tetap mati; verdict ketiga di luar cakupan** (perubahan produk, bukan perbaikan yang dijawab data). |
| 4 | Kerangka | **Pipeline Python biasa.** |
| 5 | Snapshot | **Disetujui, tidak dikerjakan sekarang.** Bila rancangan dilanjutkan: antrean digabung dan di-ingest dulu (ingest dimulai pemilik proyek), baru snapshot dibekukan, sebelum set uji v2 dibangun. Aturan Wajib #6 ditambah (CLAUDE.md). |
| 6 | Juri | **Tanpa juri LLM.** |
| 7 | Ukuran set uji | **140 butir terlalu berat. Dua tujuan dipisah:** uji kemunduran memakai set uji v1 di atas `archive/v1`; uji kemampuan baru memakai butir pesan panjang baru (bagian 6). |
| 8 | Sumber pesan panjang | **Positif: Liputan6 Cek Fakta** (sering mengutip pesan berantai utuh; `robots.txt`-nya mengizinkan), asalkan hoaksnya juga ada di basis data. **Negatif: arsip TurnBackHoax sebelum September 2025**, setelah diverifikasi tidak ada di basis data. Pemeriksaan data pribadi wajib untuk keduanya. |
| 9 | Mutu klarifikasi | **Di luar cakupan** (mengubah prompt mencampur efeknya dengan perbaikan pesan panjang). |
| 10 | Menghapus Penjelasan dari indeks | **Ditunda** (mengubah indeks dan snapshot; tidak berkaitan dengan masalah yang dijawab). |
| 11 | `retriever.py` | **Dikunci dengan hash sebelum evaluasi**, karena Versi 2 mengimpornya. |
| 12 | Pedoman anotasi | **Tambahan, bukan revisi: versi 1.1** untuk pesan berantai yang memuat beberapa klaim; dikunci sebelum pelabelan; aturan v1.0 lainnya tidak diubah (bagian 6.4). |

Ketentuan tambahan: **hipotesis Versi 2 beserta ambangnya dikunci sebelum pelabelan dimulai**,
seperti Versi 1; perhitungan ukuran sampel disimpan di repositori
(`src/evaluation/sample_size.py`, `testset/v2_ukuran_sampel.json`).

---

## 1. Masalah yang dijawab Versi 2, dan kekuatan buktinya

Untuk tiap masalah dibedakan **bukti bahwa masalahnya ada** dan **bukti bahwa solusi yang
diusulkan menyelesaikannya**. Skala: *kuat* = terukur, selisihnya jauh di atas kebetulan; *lemah* =
terukur tetapi sampel kecil, sintetis, atau tidak dapat dibedakan dari kebetulan; *tidak ada* =
belum pernah diukur.

| # | Masalah | Bukti masalah | Bukti solusi |
| --- | --- | --- | --- |
| M1 | Klaim di dalam pesan panjang tidak ikut dicari (terpotong 512 token) | **Kuat untuk mekanismenya**, lemah untuk besarnya pada pesan nyata | Tidak ada |
| M2 | Keputusan "klaim sama" generator kadang keliru atau tidak stabil antar-run | Lemah (2 kesalahan, 5 butir non-batas tidak bulat, dari 50) | Tidak ada |
| M3 | Fitur "Mungkin terkait" tidak dapat diwujudkan dengan ambang skor | **Kuat** | Tidak ada |
| M4 | Kebersihan dan kredibilitas RUJUKAN yang ditampilkan | **Kuat** (temuan data), tetapi tidak pernah diukur pada jawaban | Sebagian sudah diperbaiki di Versi 1; sisanya tidak ada |
| M5 | Klarifikasi sulit dibaca / terlalu tipis | Lemah (pengamatan, bukan pengukuran) | Tidak ada |
| -- | Retrieval gagal menemukan artikel yang benar pada klaim pendek | **Tidak ada bukti masalah** | -- |
| -- | Kredibilitas DOKUMEN hasil retrieval | **Tidak ada** (satu sumber) | -- |

### M1. Pesan panjang: klaim terdorong keluar dari jendela embedding

- **Bukti masalah (mekanisme): kuat.** Retrieval hanya meng-embed 512 token pertama kueri
  (`MAX_SEQ_LENGTH`). Pada 20 butir positif dengan pengganggu di depan dan belakang klaim,
  Recall@3 pada ~5.000 karakter adalah **2/20 pada arsip** (`testset/retrieval_ablation_report.txt`
  baris 115), **0/20 pada indeks 922** dan **0/20 pada indeks 1.532**
  (`retrieval_ablation_prod922_report.txt`, `retrieval_ablation_prod1532_report.txt` baris 115);
  klaim berada di luar 512 token pada 18/20. Kondisi pembanding (klaim di awal pesan, pengganggu
  di belakang) tetap **19/20** pada ketiga indeks (baris 121), jadi penyebabnya pemotongan token,
  bukan panjang itu sendiri. Pada ~1.500 dan ~3.000 karakter: 19/20.
- **Yang tidak diketahui: besar masalahnya pada pesan nyata.** Teks pengganggunya **sintetis**
  (sapaan, ajakan menyebarkan, tanda baca berlebihan; laporan ablasi menandainya "INDIKATIF"). Belum
  ada satu pun pesan berantai asli yang diukur: tidak diketahui seberapa sering pesan nyata
  melebihi 512 token, dan di mana klaimnya berada di dalam pesan. Set uji v1 tidak menguji rentang
  ini (klaim terpanjang 749 karakter / 152 token; `v1_temuan_untuk_v2.md` bagian 4.2).
- **Mitigasi yang sudah ada di Versi 1:** demo membatasi masukan 1.500 karakter dan memperingatkan
  sejak ~220 token (CLAUDE.md, "Keterbatasan yang Diketahui"). Jadi bagi pengguna demo masalah ini
  sekarang berbentuk "pesan panjang ditolak", bukan "pesan panjang dijawab keliru".
- **Bukti solusi: tidak ada.** Belum pernah diukur apakah ekstraksi klaim oleh LLM memulihkan
  recall, maupun apakah ekstraksi itu merusak klaim pendek.

### M2. Penilaian "klaim sama" oleh generator

- **Bukti masalah: lemah.** Pada set uji v1 (3 run x 54 butir; `testset/v1_analysis_report.txt`):
  akurasi non-batas modus **48/50**, Wilson95 [0,865; 0,989]. Kesalahan: `v1-020` (penolakan
  palsu, keliru di ketiga run) dan `v1-036` (kecocokan palsu, keliru di 2 dari 3 run). Enam butir
  tidak bulat antar-run (`v1-006`, `v1-010`, `v1-036`, `v1-039`, `v1-040`, dan `v1-053` yang
  berstatus batas); pada ketujuh butir unik itu artikel yang benar sudah ada di top-3
  (`v1_temuan_untuk_v2.md` bagian 2). Akurasi non-batas per run tunggal, dihitung dari
  `data/testset_v1_eval_gemini-3.5-flash-lite.jsonl`: **46/50, 47/50, 48/50**.
- **Mengapa "lemah":** 2 kesalahan dari 50 berada di dalam interval yang sama dengan 0 kesalahan;
  44% butir berbagi artikel jangkar (caveat 1 laporan analisis), sehingga interval itu pun terlalu
  percaya diri; dan subtipe `angka_waktu_beda` (tempat `v1-036`, `v1-039`, `v1-040` berada) 100%
  buatan model (caveat 3: confound sumber).
- **Bukti solusi: tidak ada.** Lihat bagian 2.2: belum ada bukti bahwa node grader terpisah
  menilai lebih baik daripada generator yang sudah menilai hal yang sama.

### M3. "Mungkin terkait" dengan ambang skor

- **Bukti masalah: kuat.** (a) Pada indeks 922 dan 1.532 tidak ada ambang yang memisahkan: kueri
  tak terkait "bumi datar" berskor 0,6385, di atas kandidat yang layak tampil (0,5739-0,63)
  (`config/related_threshold.json`; `testset/devset_retrieval_1532.json`). (b) Kegagalannya
  struktural: skor kandidat teratas sebuah kueri tidak bisa turun saat indeks diperbesar (chunk
  lama dan embedding-nya tetap), sehingga jarak antara "tak terkait" dan "layak tampil" hanya bisa
  menyempit. Terukur: skor top-1 tertinggi negatif mudah yang klaimnya tidak ada di basis data
  0,5351 (150 artikel) -> 0,5666 (922) -> 0,6308 (1.532, `v1-046`) (`v1_temuan_untuk_v2.md` bagian
  6.1). Fitur ini dimatikan sejak indeks 922.
- **Bukti solusi: tidak ada.** `v1_temuan_untuk_v2.md` bagian 6.1 mengusulkan grader sebagai
  pengganti. Itu **usulan, bukan temuan**: belum ada pengukuran apa pun bahwa LLM dapat memisahkan
  "topik sama, klaim berbeda" dari "tidak terkait" dengan andal. Yang ada hanyalah alasan di kolom
  `alasan` generator pada butir negatif sulit, yang tidak pernah dinilai benar-salahnya.
- **Ini fitur tampilan, bukan vonis.** Tidak ada temuan bahwa ketiadaan fitur ini merugikan
  pengguna; ia berkaitan dengan kandidat verdict ketiga "artikel terkait" (CLAUDE.md, "Status
  Pengembangan"), yang juga belum diputuskan.

### M4. Rujukan yang ditampilkan

Dua hal yang selama ini tercampur dalam "penilaian kredibilitas sumber" dipisahkan:

**(a) Kredibilitas dokumen hasil retrieval -- tidak ada temuan, dan tidak bisa ada.** Konsep
Corrective RAG menilai kredibilitas dokumen yang ditemukan. Di proyek ini semua dokumen berasal
dari satu sumber (artikel TurnBackHoax), jadi tidak ada variasi kredibilitas dokumen untuk dinilai.
`v1_temuan_untuk_v2.md` bagian 3 mencatat "tidak ada temuan kuantitatif"; itu benar untuk
pengertian ini.

**(b) Kredibilitas dan kebersihan RUJUKAN -- banyak temuan** (CLAUDE.md, "Temuan Aturan Wajib #1";
`v1_temuan_untuk_v2.md` bagian 9):

- Baris "Sumber:" di seksi Hasil Periksa Fakta bercampur: sumber hoaks dan situs pembanding yang
  sah. Dari 2.106 URL di baris itu, 1.987 berdomain daftar-blokir; pada 3 artikel (32110, 31532,
  33497) baris itu memuat situs resmi/media. Sebelum diperbaiki, URL "Sumber:" tampil sebagai
  rujukan pada 10 artikel (8 di indeks produksi).
- Pemendek URL: 13 rujukan tampil berpemendek pada 1.532 artikel; tujuannya tidak dapat
  diverifikasi sebelum diklik. Penyaringannya ikut membuang rujukan yang kemungkinan sah (36089).
- Pengecualian `*.go.id` berisiko: situs pemerintah dapat diretas (CLAUDE.md, "Keterbatasan").
- Daftar media/cek fakta tepercaya (`links.TRUSTED_SOURCE_DOMAINS`) disusun melingkar dari domain
  yang muncul sebagai rujukan di data.
- Media sosial disaring seluruhnya per domain, termasuk akun resmi instansi; 205 dari 1.532
  artikel tidak punya rujukan yang boleh ditampilkan.
- **Celah evaluasi:** evaluasi Versi 1 mengukur URL karangan LLM (0), tetapi tidak pernah mengukur
  kebersihan rujukan yang berasal dari data, dan berkas hasil tidak menyimpan rujukan jawaban.

**Bukti solusi:** perbaikan berbasis aturan (daftar domain, baris "Sumber:", penyaringan ulang saat
tampil) **sudah diterapkan di Versi 1** dan terverifikasi lewat parse ulang 1.532 artikel (0
rujukan tampil berdomain daftar-blokir, 0 yang juga `claim_sources`). Untuk penilaian kredibilitas
per-URL oleh LLM (mis. membedakan akun resmi dari akun penyebar hoaks) **tidak ada bukti sama
sekali**, dan percobaan meloloskan beranda akun pernah gagal diverifikasi (CLAUDE.md,
"Keterbatasan": 11 beranda akun tidak dapat diperiksa dari klien HTTP).

### M5. Mutu klarifikasi (di luar cakupan; keputusan 9)

- **Bukti masalah: lemah.** Tiga contoh keluaran untuk satu artikel (36730) yang dinilai padat dan
  sulit diikuti (`v1_temuan_untuk_v2.md` bagian 4.1) -- pengamatan pemilik proyek, bukan
  pengukuran. Ditambah temuan data: pada artikel Sep-Nov 2025 Kesimpulan hanya satu kalimat (median
  136-140 karakter vs 239), sehingga klarifikasi yang disusun darinya tipis (CLAUDE.md,
  "Keterbatasan").
- **Bukti solusi: tidak ada.** Mengubah prompt membatalkan baseline Versi 1 dan pengaruhnya pada
  akurasi belum diukur.

### Yang BUKAN masalah terbukti

- **"Retrieval gagal menemukan artikel yang benar."** Empat kegagalan Recall@3 Versi 1 (`v1-022`,
  `v1-024`, `v1-027`, `v1-033`) **semuanya butir negatif sulit** (`testset/v1.jsonl`:
  `expected_verdict = belum_ditemukan`); yang "gagal ditemukan" di sana adalah artikel TETANGGA,
  dan jawaban yang benar untuk keempatnya memang "belum ditemukan". Itu bukan bukti bahwa retrieval
  menggagalkan jawaban. Untuk butir positif, Recall@3 adalah **20/20** pada arsip, indeks 922, dan
  indeks 1.532 (ketiga laporan ablasi, eksperimen 1), baik pencarian eksak maupun retriever
  produksi. Akibat sebenarnya dari keempat butir itu adalah batas tafsir H1 (H1 hanya teruji pada
  17 dari 20 negatif sulit; `v1.meta.json`, `batas_tafsir_H1_recall_2026-09-23`), bukan kebutuhan
  akan penulis ulang kueri.
- **Parameter retrieval (top-k, agregasi).** Tidak ada yang dapat dibedakan dari kebetulan pada
  ketiga indeks (ablasi eksperimen 1 dan 2).

---

## 2. Komponen Versi 2 (setelah keputusan)

Hanya dua, sesuai keputusan 1.

### 2.1 Penanganan pesan panjang (menjawab M1)

- **Tugas:** bila pesan terkena pemotongan (definisi mekanistik di bagian 10), klaimnya tetap
  ikut dicari.
- **Dua kandidat, diukur dulu pada tahap retrieval (tanpa generator):**
  - *Pencarian per potongan pesan, tanpa LLM:* pesan dipecah menjadi jendela <= 512 token, tiap
    jendela di-embed dan dicari, skor artikel = maksimum antar-jendela. Nol panggilan LLM,
    deterministik, tidak bisa mengarang klaim. Yang perlu diukur: pengganggu ikut dicari sehingga
    bisa memunculkan artikel yang mirip pengganggunya.
  - *Ekstraksi klaim oleh LLM:* satu panggilan tambahan untuk pesan yang terkena. Yang perlu
    diukur: klaim yang berubah makna, dan biaya kuota.
- **Aturan pemilihan (V2-H3):** bila pencarian per potongan menyamai ekstraksi LLM (selisih <= 2
  butir), yang dipilih pencarian per potongan.
- **Hanya aktif pada pesan yang terkena.** Untuk klaim di bawah batas token, jalur Versi 2 harus
  identik dengan Versi 1 (kueri yang sama, kandidat yang sama). Ini yang diperiksa uji kemunduran.
- Belum ada bukti untuk solusi mana pun (bagian 1, M1).

### 2.2 Pengukuran kebersihan rujukan (menjawab M4)

Bukan komponen LLM. Berkas hasil evaluasi menyimpan daftar rujukan tiap jawaban "ditemukan", dan
metrik di bagian 5.4 dihitung untuk kedua versi. Kelemahan daftar domain (melingkar, `.go.id`)
tetap dicatat sebagai keterbatasan, tidak diselesaikan Versi 2.

### 2.3 Yang ditimbang lalu tidak dimasukkan

- **Grader** (keputusan 2). Generator Versi 1 sudah menilai "klaim sama": prompt sistemnya memuat
  definisi resmi (KIA, unsur inti, uji dua arah, uji Kesimpulan), ia membaca tiga kandidat
  sekaligus, dan mengeluarkan `klaim_sama` serta `alasan`. Yang secara konkret bisa berbeda pada
  grader hanya empat hal -- satu kandidat per panggilan, keluaran per unsur, kategori "topik sama,
  klaim berbeda", dan pemungutan suara -- dan tidak satu pun punya bukti. Satu-satunya data:
  modus 3 run 48/50 vs run tunggal 46-48/50, tetapi `v1-020` keliru di ketiga run dan selisih 0-2
  butir tidak dapat dibedakan dari kebetulan.
- **Penulis ulang kueri saat retrieval gagal, "Mungkin terkait" lewat grader, penilai kredibilitas
  per-URL, perubahan gaya klarifikasi:** lihat bagian 8.

### 2.4 Kerangka: pipeline Python biasa (keputusan 4)

Alur yang dibutuhkan:

```
klaim -> [bila terkena pemotongan: pencarian per potongan / ekstraksi] -> retrieval -> generator Versi 1 (tak berubah) -> jawaban
```

Linear dengan satu cabang bersyarat, tanpa putaran. `langgraph` tidak ada di `requirements.txt`;
lapisan `src/llm/` (throttle, kuota, pencatatan panggilan) dipakai apa adanya; komponen
dinyalakan/dimatikan untuk ablasi lewat parameter fungsi.

---

## 3. Pemisahan dari Versi 1

`src/generator.py` terkunci sejak tag `testset-v1`: `v1.meta.json` (`sidik_jari_generator_v1`)
menyimpan hash seluruh berkas, hash prompt+skema, model (`gemini-3.5-flash-lite`), dan
`thinking_level` (`medium`); `tests/test_testset_locks.py` gagal bila salah satunya berubah. Yang
di-hash saat ini hanya `generator.py`.

Karena cakupan dipersempit, **Versi 2 tidak punya prompt baru**: generator Versi 1 dipanggil apa
adanya. Struktur yang diusulkan (belum dibuat):

```
src/
  generator.py            # Versi 1 -- TIDAK disentuh; uji kunci tetap lolos
  retriever.py            # dipakai bersama; DIKUNCI dengan hash sebelum evaluasi (keputusan 11)
  v2/
    __init__.py
    long_message.py       # deteksi pesan terkena pemotongan; pencarian per potongan; (bila terpilih) ekstraksi LLM
    pipeline.py           # orkestrasi: klaim -> kandidat (v1 atau jalur pesan panjang) -> generator v1
  evaluation/
    testset_eval.py       # Versi 1 -- tidak diubah
    v2_eval.py            # menjalankan kondisi K0..K2 pada set uji; satu berkas hasil per kondisi, memuat rujukan jawaban
```

Ketentuan:

1. Versi 2 mengimpor dari Versi 1 (retriever, generator, lapisan `llm/`, `links`), tidak pernah
   sebaliknya, dan tidak mengubah berkas Versi 1.
2. Pengaman Versi 1 berlaku tanpa perubahan karena generatornya sama: status dari metadata,
   rujukan hanya dari metadata, `article_id` hanya dari kandidat, URL keluaran LLM dibuang.
3. Sebelum evaluasi: hash `retriever.py` ditambahkan ke sidik jari terkunci, dan `src/v2/` mendapat
   sidik jari serta uji kunci sendiri.
4. Demo memilih versi lewat setelan; bawaannya tetap Versi 1 sampai Versi 2 terukur.
5. Menyuntikkan kandidat tanpa mengubah `generator.py` dimungkinkan oleh kode yang ada:
   `AnswerGenerator` menerima `retrieve_fn(claim, top_k)` sebagai parameter konstruktor
   (`src/generator.py`), jadi Versi 2 cukup memberikan fungsi pencarian lain. Konsekuensinya:
   generator tetap menerima pesan UTUH sebagai `claim` (dipakai `build_user_prompt`), sehingga LLM
   membaca seluruh pesan panjang; pengaruhnya pada token masuk dan pada penilaian belum diukur.

---

## 4. Hipotesis yang dipra-registrasi (usulan; dikunci sebelum pelabelan)

Bentuknya mengikuti H1 dan H3 Versi 1 (`v1.meta.json`, `ambang`). "Komponen tidak memberi
perbaikan" adalah hasil yang sah. Aturan tafsir mengikuti ablasi Versi 1: selisih bermakna hanya
bila McNemar eksak dua sisi p < 0,05 **dan** selisih bersih >= 3 butir. McNemar memberi p < 0,05
paling sedikit pada 6 perbaikan tanpa kemunduran (`testset/v2_ukuran_sampel.json`).

| Kode | Hipotesis | Ukuran | Terdukung | Gugur |
| --- | --- | --- | --- | --- |
| V2-H1 | Pada pesan panjang ASLI yang terkena pemotongan, penanganan pesan panjang menaikkan Recall@3 butir positif | Recall@3 Versi 1 vs Versi 2 pada butir positif pesan panjang, berpasangan | p < 0,05 dan selisih bersih >= 6 butir | Selisih bersih <= 2 butir |
| V2-H2 | Versi 2 tidak lebih buruk pada klaim pendek | (a) deterministik: untuk 54 butir set uji v1 pada `archive/v1`, kueri dan top-3 Versi 2 identik dengan Versi 1; (b) akurasi modus 3 run non-batas | (a) 54/54 identik; (b) kemunduran bersih <= 2 butir terhadap 48/50 | (a) ada satu saja yang berbeda; (b) kemunduran bersih >= 3 butir |
| V2-H3 | Ekstraksi oleh LLM lebih baik daripada pencarian per potongan tanpa LLM | Recall@3 butir positif pesan panjang, dua kondisi | LLM unggul bersih >= 3 butir, p < 0,05 | Selisih <= 2 butir -> **dipilih yang tanpa LLM** |
| V2-H4 | Penanganan pesan panjang tidak menaikkan kecocokan palsu | Kecocokan palsu pada butir negatif pesan panjang, Versi 1 vs Versi 2 | Kenaikan bersih <= 1 butir | Kenaikan bersih >= 3 butir |
| V2-H5 | Rujukan yang ditampilkan bersih | Rujukan pada jawaban "ditemukan" yang melanggar kebijakan penyaringan atau termasuk sumber klaim | 0 pada kedua versi | >= 1 (dilaporkan per artikel; pemeriksaan sifat, bukan uji statistik) |
| V2-H6 | Biaya Versi 2 | Panggilan LLM dan latensi per kueri | Dilaporkan; tanpa ambang | -- |

**Batas tafsir V2-H2, ditulis eksplisit atas permintaan pemilik proyek:** set uji v1 **hanya sah
untuk menunjukkan Versi 2 tidak lebih buruk, tidak untuk mengklaim perbaikan**. Set itu sudah
dibedah berkali-kali; butir mana yang salah dan mengapa sudah diketahui, dan rancangan Versi 2
disusun dengan pengetahuan itu. Selain itu seluruh klaim di set uji v1 pendek (terpanjang 749
karakter / 152 token), jadi jalur pesan panjang tidak aktif di sana: yang diperiksa (a) adalah
bahwa jalur klaim pendek memang tidak berubah, dan selisih pada (b) hanyalah variasi acak LLM
(run tunggal Versi 1: 46, 47, 48 dari 50).

Urutan pengunci: hipotesis dan ambang ditulis ke `testset/v2.meta.json` -> pedoman 1.1 dikunci ->
baru pelabelan dimulai. Kode hipotesis lama H4 (Gemma sebagai juri) tidak dibawa (keputusan 6).

---

## 5. Rencana evaluasi

### 5.1 Dua tujuan, dua tempat

| Tujuan | Set uji | Indeks | Parameter retrieval |
| --- | --- | --- | --- |
| Uji kemunduran (V2-H2) | set uji v1 (54 butir, beku) | `archive/v1` (150 artikel) | milik arsip: `ef_search` 100 |
| Uji kemampuan baru (V2-H1, H3, H4, H5) | butir pesan panjang baru (set uji v2) | snapshot baru yang dibekukan | `ef_search` 2000 |

- **Kedua versi selalu dijalankan pada set, indeks, dan parameter yang sama** di tiap baris.
  `top_k` = 3, `CHUNK_FETCH` = 30, agregasi maksimum, model embedding dan `MAX_SEQ_LENGTH` tidak
  diubah.
- **Snapshot baru** (keputusan 5): belum dibuat. Urutannya bila rancangan dilanjutkan: antrean
  digabung dan di-ingest (dimulai pemilik proyek) -> `index_check` dan `retriever_exactness` ->
  indeks disalin sebagai snapshot beku dengan daftar id dan sidik jari isi -> set uji v2 dibangun
  dan diverifikasi terhadapnya. `evaluation.retriever_exactness` dijalankan juga pada kueri set
  uji v2; Recall dilaporkan dari retriever yang benar-benar dipakai dan dari pencarian eksak.
- **Aturan Wajib #6 ditambah** (CLAUDE.md): perbandingan Versi 1 dan Versi 2 pada kemampuan baru
  wajib memakai snapshot itu; angka asli Versi 1 (48/50, Recall@3 36/40, ablasi) tetap hanya lewat
  `archive/v1`.

### 5.2 Metrik retrieval dipisah dari metrik jawaban

- *Retrieval:* Recall@1/3/5 per tipe butir, peringkat artikel sasaran, dan keterbacaan klaim
  (utuh/terpotong).
- *Jawaban:* keputusan modus 3 run (verdict + `article_id`); kecocokan palsu, penolakan palsu,
  artikel salah, masing-masing dengan Wilson 95%; kesepakatan antar-run; pelanggaran format; URL di
  luar metadata -- sama dengan pra-registrasi Versi 1 (`v1.meta.json`, `evaluasi`).
- Butir tidak disaring berdasarkan hasil sistem.

### 5.3 Ablasi per komponen

| Kondisi | Penanganan pesan panjang |
| --- | --- |
| K0 = Versi 1 (terkunci) | -- |
| K1 | pencarian per potongan (tanpa LLM) |
| K2 | ekstraksi LLM |

K1 vs K2 diputuskan lebih dulu pada tahap retrieval saja (V2-H3). Hanya kondisi yang terpilih
dilanjutkan ke tahap jawaban; yang kalah tidak dijalankan generatornya.

### 5.4 Kebersihan rujukan

Per jawaban "ditemukan" dihitung: rujukan yang melanggar `links.blocked_reason` (kebijakan
terkini), rujukan yang termasuk `claim_sources` artikel itu (termasuk baris "Sumber:"), jawaban
tanpa rujukan, dan rujukan yang lolos hanya karena daftar tepercaya atau `.go.id`. Diukur untuk
kedua versi pada indeks yang sama; deterministik, tanpa LLM. Pada `archive/v1` hasil yang
diharapkan sudah diketahui sebagian: metadata 36089 masih memuat satu tautan pemendek
(`v1_temuan_untuk_v2.md` bagian 9), jadi pada indeks itu metrik ini mengukur keadaan arsip, bukan
mutu Versi 2.

### 5.5 Juri

Tidak dipakai (keputusan 6). Metrik utama objektif; juri hanya relevan untuk mutu klarifikasi,
yang di luar cakupan. Sebagai catatan dasar keputusan: Gemma belum pernah diuji sebagai juri,
latensinya 31-52 detik per panggilan, dan RAGAS belum pernah dipasang (CLAUDE.md, "Hipotesis dan
status").

---

## 6. Set uji

### 6.1 Uji kemunduran: set uji v1 pada `archive/v1`

Dipakai apa adanya (54 butir beku; label sah pada arsip). Batas tafsirnya ada di bagian 4
(V2-H2). Tidak ada butir baru, tidak ada pelabelan.

### 6.2 Uji kemampuan baru: butir pesan panjang (set uji v2)

Persyaratan, dikumpulkan dari catatan yang ada (`v1_temuan_untuk_v2.md` bagian 4, 5.2, 8, 9;
`v1.meta.json`; caveat laporan analisis; CLAUDE.md Aturan Wajib #5):

1. **Diberi versi bersama snapshot basis data**; hasil hanya sah pada snapshot itu. Dasar: enam
   butir negatif v1 gugur pada indeks yang lebih besar.
2. **Positif** dari Liputan6 Cek Fakta, hanya bila hoaksnya juga ada di basis data (artikel
   sasaran dipastikan manusia). **Negatif** dari arsip TurnBackHoax sebelum September 2025,
   **diverifikasi terhadap snapshot dengan top-3 retrieval**, bukan sekadar memeriksa keberadaan
   artikelnya. Butir dari situs cek fakta lain diperiksa ulang terhadap snapshot (bukti: `v1-050`).
3. **Pesan asli, tidak disunting panjangnya**, dengan posisi klaim apa adanya. Tidak ada
   pengganggu sintetis.
4. **Label final ditetapkan manusia**; pemakaian draf AI pada tahap mana pun dicatat (Aturan Wajib
   #5).
5. **Pemeriksaan data pribadi wajib** pada setiap teks (nomor, surel, akun, tautan), termasuk yang
   tertulis tanpa skema; pesan berantai lebih sering memuat nomor dan tautan daripada klaim
   pendek. Teks yang memuat kontak penipu tidak di-commit apa adanya.
6. **Confound sumber dicatat, tidak dapat dihindari:** positif seluruhnya dari Liputan6 dan negatif
   seluruhnya dari arsip TurnBackHoax, jadi tipe butir dan sumber tidak terpisah. Perbandingan
   kecocokan palsu vs penolakan palsu pada set ini wajib disertai catatan itu.
7. **Tidak boleh bocor** dari set uji v1 maupun set pengembangan.
8. Kepatuhan situs diperiksa ulang saat pengambilan (`robots.txt`), seperti pada v1.

### 6.3 Ukuran sampel

Sumber angka: `src/evaluation/sample_size.py` -> `testset/v2_ukuran_sampel.json` (rumus saja:
Wilson 95%, McNemar eksak dua sisi, binomial; uji `tests/test_sample_size.py`).

**(a) Mengapa set uji besar ditinggalkan.** Agar interval Wilson dua kondisi tidak tumpang tindih:
96% vs 99% butuh >= 413 butir per kondisi; 90% vs 96% butuh 276; 80% vs 95% butuh 68. Pada
perbandingan berpasangan, peluang 80% mengamati 6 perbaikan butuh 197 butir bila laju perbaikan
sejati 4% (kesalahan modus Versi 1: 2/50) dan 78 butir bila 10%. Jadi perbaikan akurasi pada klaim
pendek tidak dapat ditunjukkan dengan set yang sanggup dilabeli satu orang -- dan setelah cakupan
dipersempit, Versi 2 memang tidak mengklaimnya.

**(b) Berapa butir pesan panjang yang cukup.** V2-H1 terdukung bila ada >= 6 perbaikan bersih.
Laju perbaikan sejati = (bagian butir yang benar-benar terkena pemotongan) x (bagian yang
dipulihkan Versi 2). Butir positif yang dibutuhkan agar peluang mengamati >= 6 perbaikan mencapai
80%, tanpa kemunduran:

| Bagian butir yang terkena | dipulihkan 50% | dipulihkan 70% | dipulihkan 90% |
| --- | --- | --- | --- |
| 20% | 78 | 55 | 43 |
| 40% | 39 | 27 | 21 |
| 60% | 25 | 18 | 13 |
| 80% | 19 | 13 | 10 |
| 100% | 15 | 10 | 7 |

**Kedua faktor belum diketahui.** "Bagian yang terkena" adalah persis yang diukur di bagian 10;
"bagian yang dipulihkan" baru diketahui setelah komponen dibangun. Karena itu jumlah butir **tidak
dapat ditetapkan sekarang**. Yang dapat dikatakan: bila butir positif dipilih HANYA dari pesan
yang terbukti terkena (baris 100%), 15 butir cukup pada pemulihan 50% dan 10 pada 70%; bila
pengukuran menunjukkan pesan yang terkena sulit ditemukan, jumlah pesan yang harus disaring naik
sebanding.

**(c) Ketelitian yang didapat.** Batas bawah Wilson 95% bila semua butir benar: 0,722 (n = 10),
0,796 (15), 0,839 (20), 0,886 (30). Batas atas bila tidak ada kecocokan palsu pada butir negatif:
27,8% (10), 20,4% (15), 16,1% (20), 11,4% (30).

**(d) Usulan (ditetapkan setelah bagian 10):** 20 butir positif pesan panjang yang terkena + 20
butir negatif pesan panjang. Dengan 20 positif, V2-H1 berpeluang >= 80% terdukung bila Versi 2
memulihkan sedikitnya ~40% butir; dengan 20 negatif tanpa kecocokan palsu, batas atasnya 16%. Itu
40 butir baru (set uji v1: 54). Angka ini disesuaikan bila pengukuran bagian 10 mengubah
gambarannya.

### 6.4 Pedoman anotasi versi 1.1 (usulan tambahan; belum dikunci)

**Koreksi atas premis:** pedoman v1.0 **sudah** memuat satu baris untuk kasus ini
(`testset/ANNOTATION_GUIDE.md`, bagian 4): *"Pesan berantai berisi beberapa klaim -- SAMA bila KIA
adalah salah satu klaim utamanya dan tidak dibantah pesan itu sendiri -- catat di `catatan`"*. Yang
belum diatur adalah cara menentukan "klaim utama" dan apa yang dilakukan bila pesan cocok dengan
lebih dari satu artikel. Versi 1.1 mengoperasionalkan baris itu; aturan lain tidak diubah.

Usulan teks tambahan:

1. **Klaim utama sebuah pesan** adalah klaim yang (i) dinyatakan pesan itu sebagai fakta -- bukan
   dikutip untuk dibantah atau dipertanyakan -- **dan** (ii) menjadi pokok yang diminta dipercaya,
   diwaspadai, atau disebarkan, atau ditonjolkan pesan itu sendiri (judul, pengulangan, huruf
   besar).
2. **SAMA** bila ketiga unsur inti KIA muncul lengkap pada satu klaim utama, dan klaim itu lolos
   uji dua arah serta uji Kesimpulan. Klaim lain di dalam pesan diperlakukan seperti unsur
   perifer: jumlahnya dan letak klaim utama di dalam pesan (awal, tengah, akhir) tidak mengubah
   keputusan.
3. **TIDAK SAMA** bila KIA hanya disinggung sebagai latar atau contoh (setara `sebagian_perifer`),
   atau bila pesan itu sendiri membantahnya.
4. **Cocok dengan lebih dari satu artikel basis data** (pesan memuat beberapa klaim utama yang
   masing-masing punya artikel): butir TIDAK dikeluarkan; semua artikel yang sah dicatat di
   `expected_alt`, dan jawaban dinilai benar bila memilih salah satunya. (v1.0 untuk kasus `ambigu`
   pada klaim pendek tetap berlaku.)
5. **Unsur perifer tambahan untuk pesan berantai:** sapaan, ajakan menyebarkan, doa atau sumpah,
   daftar penerima, tanda baca dan emoji berlebihan.
6. **Kolom baru per butir:** `jumlah_klaim_utama`, dan posisi klaim yang cocok (token awal dan
   akhir menurut tokenizer bge-m3; lihat bagian 10).

Yang perlu diputuskan pemilik proyek sebelum dikunci: definisi (ii) pada butir 1 bersifat
penilaian, dan dengan satu anotator konsistensinya tidak terukur.

---

## 7. Kendala nyata

### 7.1 Kuota LLM

Angka tercatat (`src/llm/limits.py`, dari AI Studio 2026-09-21): `gemini-3.5-flash-lite` RPM 15,
TPM 250.000, **RPD 500**. Tier gratis **dapat berubah tanpa pemberitahuan**; `gemini-3.8-flash`
pernah dihentikan karena ketidakstabilan layanan. Setiap permintaan yang dikirim dihitung, termasuk
yang ditolak; demo berbagi kuota yang sama. Versi 1 memakai 1 panggilan per kueri (evaluasi v1: 162
panggilan untuk 162 baris; rata-rata 2.516 token masuk; latensi rata-rata 10-18 detik).

Panggilan untuk evaluasi 3 run dengan cakupan sekarang:

| Bagian | Butir | Kondisi | Panggilan |
| --- | --- | --- | --- |
| Uji kemunduran (b), set uji v1 | 54 | Versi 2 saja (hasil Versi 1 sudah tercatat) | 162 |
| Uji kemampuan baru | 40 (usulan) | K0 + kondisi terpilih | 240 bila tanpa LLM; 240 + 3 x (jumlah butir terkena) bila ekstraksi LLM |
| Pemilihan K1 vs K2 (retrieval saja) | butir positif | K2 saja yang memanggil LLM | 1 x jumlah butir positif |

Totalnya sekitar **400-480 panggilan**, yaitu satu hari kuota bila demo tidak dipakai, dua hari
bila ingin aman. Token masuk untuk pesan panjang lebih besar daripada 2.516 (pesan utuh ikut
dikirim ke generator); besarnya belum diukur, tetapi TPM 250.000 pada RPM 15 memberi ruang ~16.000
token per panggilan.

Bagi pengguna demo: pencarian per potongan tidak menambah panggilan; ekstraksi LLM menambah satu
panggilan hanya untuk pesan yang terkena.

### 7.2 Memori

Laptop pengembangan: 15,7 GB RAM, memori bebas teramati 2,3-3,4 GB; memuat model embedding menekan
memori tersedia sampai ~0,9-1,0 GB (`data/pending_2026-10-03.log`). Proses pernah dihentikan
sistem karena memori rendah: ingest 2026-09-27 dan ablasi 2026-10-03 tercatat di CLAUDE.md (pemilik
proyek menyebut tiga kejadian). Konsekuensi: tidak ada model lokal tambahan; satu proses pemuat
model pada satu waktu; pencarian per potongan meng-embed beberapa jendela per pesan dengan model
yang sama (tanpa tambahan memori, hanya waktu); evaluasi dapat dilanjutkan antar-hari.

### 7.3 Lain-lain

Satu anotator; satu sumber data; `generator.py` terkunci; pembaruan berkala terus mengubah indeks
produksi (karena itu perlu snapshot); ingest hanya dimulai pemilik proyek; permintaan API key
Yudistira belum dijawab.

---

## 8. Di luar cakupan

| Hal | Alasan |
| --- | --- |
| Grader / node penilai relevansi | Keputusan 2: generator sudah menilai kesamaan klaim; tidak ada bukti untuk perbedaan yang dibawa grader; kuota terbatas |
| Penulis ulang kueri saat retrieval gagal (putaran "cari lagi") | Tidak ada bukti masalah: empat kegagalan Recall@3 semuanya butir negatif; positif 20/20 di semua indeks |
| "Mungkin terkait" dan verdict ketiga "artikel terkait" | Keputusan 3: perubahan produk, bukan perbaikan yang dijawab data; ambang skor terbukti gagal dan tidak ada bukti untuk penggantinya |
| Mutu / gaya bahasa klarifikasi | Keputusan 9: mengubah prompt mencampur efeknya dengan perbaikan pesan panjang |
| Menghapus Penjelasan dari indeks | Keputusan 10: mengubah indeks dan snapshot; tidak berkaitan dengan masalah yang dijawab |
| Penilaian kredibilitas dokumen hasil retrieval | Satu sumber data; tidak ada yang dinilai |
| Penilai kredibilitas rujukan per-URL oleh LLM | Tidak ada bukti solusi; LLM tidak dapat membuka tautan; daftar eksplisit lebih mudah diaudit |
| Mengganti top-k atau agregasi | Tidak dapat dibedakan dari kebetulan pada tiga indeks |
| Model embedding lain, batas token indeks lain, skema chunking lain | Butuh pembangunan ulang indeks dan memori; tidak ada temuan yang menuntutnya |
| Juri LLM (RAGAS + Gemma) | Keputusan 6 |
| LangGraph | Keputusan 4 |
| Set uji umum v2 berukuran besar (140 butir) | Keputusan 7 |
| Mengubah `archive/v1`, `v1.jsonl`, `generator.py` | Baseline |
| Integrasi API Yudistira, penjadwalan ingest | Tahap lain |

---

## 9. Yang masih terbuka

1. **Hasil pengukuran bagian 10** -- menentukan apakah Versi 2 dilanjutkan dengan cakupan ini.
2. **Metode penentuan posisi klaim** (bagian 10.3) -- menunggu persetujuan pemilik proyek sebelum
   sampel diambil.
3. **Jumlah butir pesan panjang** (bagian 6.3 d) -- ditetapkan setelah pengukuran.
4. **Teks pedoman 1.1** (bagian 6.4) -- disetujui lalu dikunci sebelum pelabelan.
5. **Ambang hipotesis** (bagian 4) -- dikunci di `testset/v2.meta.json` sebelum pelabelan.
6. **Pengaruh pesan utuh pada generator** (bagian 3, butir 5): generator Versi 1 membaca seluruh
   pesan panjang; belum pernah diukur apakah penilaian "klaim sama"-nya tetap andal pada masukan
   sepanjang itu (set uji v1 tidak memuat pesan panjang).

---

## 10. Langkah pertama: apakah masalah pesan panjang terjadi pada pesan berantai asli?

Ditetapkan pemilik proyek. Bukti M1 berasal dari pengganggu sintetis yang sengaja menaruh klaim di
belakang separuh pengganggu. Belum diketahui apakah pesan berantai asli sering seperti itu. Bila
klaimnya hampir selalu di awal, Versi 1 sudah menanganinya (klaim di awal pesan: 19/20 pada ~5.000
karakter) dan Versi 2 memecahkan masalah yang jarang terjadi.

### 10.1 Yang diukur

1. Panjang tiap pesan dalam token bge-m3 (tokenizer yang sama dengan retrieval).
2. Posisi klaim inti relatif terhadap batas 512 token.
3. Persentase sampel yang benar-benar terkena masalah, menurut definisi mekanistik di 10.4.

### 10.2 Sampel

Diambil **acak**, bukan dipilih yang kebetulan panjang; ukuran sampel dan cara memilihnya
dilaporkan. Sumber sesuai keputusan 8: Liputan6 Cek Fakta (positif) dan arsip TurnBackHoax sebelum
September 2025 (negatif). Rincian kerangka sampel (populasi, benih acak, ukuran) diusulkan bersama
metode di 10.3 dan **menunggu persetujuan sebelum ada yang diambil**.

### 10.3 Metode penentuan posisi klaim

Diusulkan terpisah kepada pemilik proyek (lihat laporan 2026-10-03); **LLM tidak dipakai untuk
menentukannya tanpa persetujuan**. Metode yang disetujui dicatat di sini sebelum sampel diambil.

### 10.4 Definisi "pesan panjang" (mekanistik, bukan jumlah karakter)

Sebuah pesan **terkena** bila kedua syarat ini terpenuhi: (i) panjangnya melebihi 512 token
bge-m3, sehingga sebagian pesan tidak ikut di-embed; dan (ii) klaim intinya tidak terbaca utuh di
dalam 512 token pertama. Pesan yang panjang tetapi klaimnya utuh di dalam 512 token pertama
**tidak** terkena, berapa pun jumlah karakternya. Cara menetapkan syarat (ii) bergantung pada
metode di 10.3.

### 10.5 Aturan keputusan sesudahnya

Tidak ditetapkan angka ambang "jarang" di sini; pemilik proyek melihat hasilnya lebih dulu. Yang
dilaporkan: proporsi terkena beserta interval Wilson 95%, sebaran posisi klaim, dan berapa pesan
yang harus disaring untuk mendapat satu butir yang terkena (masukan langsung untuk bagian 6.3).

---

## Sumber

| Berkas | Dipakai untuk |
| --- | --- |
| `testset/v1_temuan_untuk_v2.md` | temuan per bagian (1, 2, 3, 4, 5, 6, 6.1, 8, 9, 10, 11) |
| `testset/v1_analysis_report.txt` | akurasi, jenis kesalahan, kesepakatan antar-run, caveat, latensi dan token |
| `testset/v1.meta.json` | ambang H1/H3, rancangan evaluasi, sidik jari generator, batas tafsir H1, butir negatif yang berubah status, keputusan `v1-046` |
| `testset/v1.jsonl` | tipe dan label empat butir gagal Recall@3; panjang klaim |
| `testset/ANNOTATION_GUIDE.md` | aturan v1.0 untuk pesan berantai berisi beberapa klaim |
| `data/testset_v1_eval_gemini-3.5-flash-lite.jsonl` | akurasi per run (46, 47, 48 dari 50); 1 panggilan per butir |
| `testset/retrieval_ablation_report.txt`, `_prod922_report.txt`, `_prod1532_report.txt` | Recall@k per indeks; pesan panjang (2/20, 0/20, 0/20; 19/20) |
| `testset/v1_perbandingan_indeks_1532.json`, `testset/devset_retrieval_1532.json` | recall positif pada indeks 1.532; skor set pengembangan |
| `config/related_threshold.json` | dasar keputusan mematikan "Mungkin terkait" |
| `src/evaluation/sample_size.py`, `testset/v2_ukuran_sampel.json`, `testset/v2_ukuran_sampel.txt` | seluruh angka ukuran sampel (bagian 4 dan 6.3) |
| `src/llm/limits.py` | kuota (RPM 15, TPM 250.000, RPD 500; 2026-09-21) |
| `src/generator.py`, `tests/test_testset_locks.py` | apa yang sudah dilakukan generator; apa yang terkunci |
| `CLAUDE.md` | keterbatasan, temuan Aturan Wajib #1, latensi Gemma, catatan memori |
