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
2. **Beban penandaan** (bagian 10.3) -- setelah sampel diukur: berapa pesan di atas 512 token dan
   berapa pesan Liputan6 yang dikonfirmasi; diperkecil dengan sampel acak bila terlalu banyak.
3. **Jumlah butir pesan panjang** (bagian 6.3 d) -- ditetapkan setelah pengukuran.
4. **Teks pedoman 1.1** (bagian 6.4) -- disetujui lalu dikunci sebelum pelabelan.
5. **Ambang hipotesis** (bagian 4) -- dikunci di `testset/v2.meta.json` sebelum pelabelan.
6. **Pengaruh pesan utuh pada generator** (bagian 3, butir 5): generator Versi 1 membaca seluruh
   pesan panjang; belum pernah diukur apakah penilaian "klaim sama"-nya tetap andal pada masukan
   sepanjang itu (set uji v1 tidak memuat pesan panjang).
7. **Batas masukan demo** (bagian 10.6) bila Versi 2 menangani pesan panjang.

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

### 10.2 Sampel (disetujui 2026-10-03)

Diambil **acak berbenih** (benih 20261003, dicatat sebelum pengambilan), bukan dipilih yang
kebetulan panjang. Alat: `python -m candidates.chain_sample` (keluaran lokal di
`data/candidates/pesan_berantai/`, tidak di-commit). `robots.txt` kedua situs diperiksa
2026-10-03: liputan6.com tidak melarang `/cek-fakta` (daftar larangan tidak memuatnya, tidak ada
aturan khusus agen AI); turnbackhoax.id `Disallow:` kosong.

- **Liputan6 Cek Fakta, 100 artikel kasus tunggal** ("Cek Fakta: ...") terbit 30 Sep 2025-27 Sep
  2026 (rentang basis data). Pencacahan lewat halaman indeks per tanggal
  (`/cek-fakta/indeks/YYYY/MM/DD`): 60 tanggal dipilih acak, lalu 100 artikel dipilih acak dari
  gabungannya; artikel yang tanggal terbitnya di luar rentang dibuang.
- **Arsip TurnBackHoax sebelum September 2025, 100 artikel** di luar basis data: 30 halaman daftar
  dipilih acak dari halaman 175-1.558, lalu sampai 4 artikel acak per halaman; artikel bertanggal
  1 September 2025 atau sesudahnya dibuang.
- **"Pesan"** = kutipan terpanjang di artikel (Liputan6: halaman pertama; TurnBackHoax: seksi
  Narasi, atau teks setelah kata "narasi" bila tidak dikutip). **Kelemahan yang dicatat:** kutipan
  diambil otomatis dari tanda kutip, sehingga pesan yang memuat tanda kutip di dalamnya bisa
  terpotong (panjangnya terukur lebih pendek dari aslinya), dan artikel cek fakta bisa saja hanya
  mengutip sebagian pesan berantai.

### 10.3 Metode (disetujui 2026-10-03 dengan dua perubahan dari pemilik proyek)

Tanpa LLM. Tiga bagian:

- **C -- uji kegagalan, sebagai definisi.** Untuk tiap pesan positif (artikel sasarannya
  terkonfirmasi), pesan dicari dengan cara Versi 1 (512 token pertama). Hasil pencarian per
  jendela atas seluruh pesan **boleh dilaporkan sebagai pengamatan, tetapi BUKAN bagian dari
  definisi**: pencarian per jendela adalah salah satu kandidat solusi Versi 2, dan mendefinisikan
  "terkena" sebagai "yang bisa ditemukannya" akan membuat solusi itu tampak memulihkan semua butir
  secara melingkar.
- **A -- penandaan manual oleh pemilik proyek**, tanpa bantuan AI: kalimat pembawa klaim inti
  ditandai pada pesan di atas 512 token; posisi tokennya dihitung dari tanda itu. Dipakai untuk
  memisahkan penyebab kegagalan: klaimnya memang di luar 512 token pertama, atau gagal karena hal
  lain.
- **B -- pencocokan kata dengan judul artikel cek fakta**, dihitung untuk semua pesan sebagai
  pembanding; yang dilaporkan adalah seberapa sering ia sepakat dengan A.

**Artikel sasaran pesan Liputan6 dikonfirmasi pemilik proyek, tanpa bantuan AI.** Daftar kandidat
yang disodorkan **tidak dicari memakai pesan panjangnya**: bila dicari dengan pesan itu, pada
pesan yang memang gagal dicari -- persis kasus yang ingin dihitung -- artikel yang benar tidak
muncul, butirnya tersisih, dan prevalensinya terukur terlalu rendah. Kandidat dicari dari **judul
artikel Liputan6** (pendek) ditambah **pencarian kata kunci pada judul 1.532 artikel**, dan selalu
ada pilihan **"tidak ada yang cocok"**.

Urutan yang ditetapkan: sampel diambil dan diukur panjangnya lebih dulu; jumlah pesan di atas 512
token dan jumlah pesan Liputan6 yang perlu dikonfirmasi dilaporkan; bila terlalu banyak untuk
dikerjakan dengan teliti, diperkecil dengan **sampel acak**, bukan dengan bantuan AI; baru
kemudian berkas penandaan disiapkan.

### 10.4 Definisi (mekanistik, bukan jumlah karakter)

- **Pesan panjang** = pesan yang melebihi 512 token bge-m3, sehingga sebagian isinya tidak ikut
  di-embed.
- **Pesan terkena** = pesan panjang yang artikel sasarannya **tidak masuk tiga besar saat dicari
  dengan cara Versi 1**. Definisi ini hanya dari sisi kegagalan.
- **Penyebab** dipisahkan dengan penandaan manual: (i) klaim inti berada di luar 512 token pertama
  (seluruhnya atau sebagian); (ii) klaim inti utuh di dalam 512 token pertama tetapi tetap gagal
  (sebab lain).

### 10.5 Pelaporan: setiap angka dengan penyebutnya

Tidak ada angka "prevalensi" tanpa penyebut. Yang dilaporkan, masing-masing dengan interval Wilson
95%:

1. pesan di atas 512 token **dari seluruh sampel** (per sumber, dan dari sampel yang punya kutipan
   pesan);
2. pesan yang klaim intinya berada di luar 512 token pertama **dari pesan panjang**;
3. kegagalan Versi 1 (artikel sasaran di luar tiga besar) **dari butir positif yang artikel
   sasarannya terkonfirmasi**, dipisah untuk pesan panjang dan pesan pendek;
4. berapa pesan yang harus disaring untuk mendapat satu butir yang terkena (masukan untuk 6.3).

Tidak ditetapkan angka ambang "jarang"; pemilik proyek melihat hasilnya lebih dulu, lalu
memutuskan apakah cakupan Versi 2 dipikir ulang.

### 10.6 Dua hal yang ikut dicatat (2026-10-03)

- **Generator Versi 1 tetap membaca seluruh pesan panjang.** `AnswerGenerator` menerima pesan utuh
  sebagai `claim` dan mengirimkannya ke LLM; hanya pencariannya yang terpotong. Pengaruh masukan
  sepanjang itu pada penilaian "klaim sama" **belum pernah diukur** (set uji v1 tidak memuat pesan
  panjang). Ini **wajib ikut dievaluasi**: pada butir pesan panjang, kegagalan pencarian dan
  kegagalan penilaian dilaporkan terpisah, termasuk untuk butir yang artikelnya sudah masuk tiga
  besar.
- **Demo menolak pesan di atas 1.500 karakter**, sedangkan 512 token setara kira-kira 2.300-3.000
  karakter menurut rasio yang terukur (335 token pada 1.500 karakter; 998 token pada 5.000
  karakter; `presentation.py` dan `v1_temuan_untuk_v2.md` bagian 4.2). Artinya pesan yang terkena
  pemotongan saat ini **tidak bisa dimasukkan ke demo sama sekali**: bagi pengguna demo masalahnya
  berbentuk "pesan ditolak", bukan "pesan dijawab keliru". Bila Versi 2 menangani pesan panjang,
  **batas masukan demo harus ikut dipikirkan ulang** (dan peringatan 220 token), dengan batas baru
  yang diukur, bukan ditebak -- batas 5.000 karakter dulu ditetapkan tanpa pengukuran.

### 10.7 Hasil pengukuran panjang (2026-10-03) -- langkah sebelum penandaan

Sumber: `testset/v2_pesan_berantai_ringkasan.json` (hitungan saja; teks pesan tetap lokal). 200
artikel diambil, 0 gagal, 0 dibuang karena tanggal.

| Sumber | Sampel | Punya kutipan pesan | Di atas 512 token | Wilson 95% (dari sampel) | Token median / p90 / maks |
| --- | --- | --- | --- | --- | --- |
| Liputan6 Cek Fakta (terbit 2 Okt 2025-23 Sep 2026) | 100 | 99 | **0** | [0; 3,7%] | 66 / 162 / 312 |
| Arsip TurnBackHoax (terbit 2 Jan 2022-24 Nov 2024) | 100 | 100 | **0** | [0; 3,7%] | 34 / 69 / 297 |

- **Tidak ada satu pun pesan panjang menurut definisi 10.4.** Akibatnya angka 2 dan 3 pada 10.5
  tidak dapat dihitung: penyebutnya (pesan panjang) nol.
- **Hasilnya tahan terhadap cara pengukuran.** Untuk Liputan6: kutipan terpanjang di SEMUA halaman
  artikel maks 331 token (0 di atas 512); seluruh kutipan halaman pertama digabung maks 397 token
  (0 di atas 512). Baru bila seluruh kutipan di semua halaman digabung -- termasuk kutipan
  narasumber di bagian penelusuran, yang bukan pesan hoaks -- ada 3 dari 100 di atas 512. Untuk
  arsip TurnBackHoax: seksi Narasi PENUH (termasuk kalimat pengantar redaksi) maks 300 token.
- **Yang TIDAK dapat disimpulkan dari sini.** Yang diukur adalah pesan *sebagaimana dikutip artikel
  cek fakta*: artikel bisa saja hanya mengutip sebagian pesan berantai, dan sebagian besar yang
  dikutip adalah unggahan media sosial, bukan pesan yang diteruskan lewat aplikasi percakapan.
  Seberapa panjang pesan yang benar-benar akan ditempel pengguna ke demo tetap **tidak diketahui**
  (tidak ada data pemakaian). Arsip TurnBackHoax yang tersampel berasal dari 2022-2024, bukan dari
  rentang basis data.
- **Konsekuensi untuk rancangan.** Dengan sumber yang ditetapkan (keputusan 8), butir pesan panjang
  yang "terkena" tidak dapat dibangun: di 200 pesan acak tidak ada satu pun kandidatnya. Batas atas
  Wilson 3,7% per sumber berarti perlu menyaring puluhan sampai ratusan artikel untuk menemukan satu
  pesan di atas 512 token, bila ada. Rancangan Versi 2 dengan cakupan "penanganan pesan panjang"
  karenanya **menunggu keputusan pemilik proyek** (aturan yang ditetapkan sebelumnya: bila masalahnya
  jarang, cakupan dipikir ulang). Berkas penandaan TIDAK disiapkan.

---

## 11. Arah yang sedang ditimbang: klaim yang dijawab "belum ditemukan" (pengukuran pendahuluan)

**Status 2026-10-04: hanya pengukuran; belum ada rancangan dan belum ada yang dibangun.** Setelah
hasil 10.7, pemilik proyek menimbang arah lain yang mungkin lebih bernilai daripada penanganan
pesan panjang: klaim yang saat ini dijawab "belum ditemukan". Sebelum merancang apa pun, besar
celahnya diukur dulu.

### 11.1 Pertanyaan

Dari klaim yang diperiksa situs cek fakta lain (Liputan6 Cek Fakta), berapa bagian yang **tidak**
diperiksa TurnBackHoax, yaitu tidak ada di basis data 1.532 artikel?

### 11.2 Ambang keputusan (ditetapkan pemilik proyek SEBELUM melihat data)

> **Kalau lebih dari separuh klaim Liputan6 yang sah tidak ada di basis data TurnBackHoax, tahap
> berikutnya layak dikerjakan.**

Dicatat di sini pada 2026-10-04, sebelum berkas konfirmasi dibuat dan sebelum pemilik proyek
membukanya. Operasionalisasi (usulan Claude Code, ikut dicatat sebelum data dilihat):

- **Ukuran:** butir berkeputusan "tidak ada yang cocok" dibagi **butir yang sah**. Butir yang sah =
  butir tersampel dikurangi yang dinyatakan pemilik proyek "bukan putusan hoaks".
- **Keputusan** dibaca dari proporsi teramati: di atas 50% -> layak dikerjakan; 50% atau kurang ->
  tidak.
- **Dilaporkan bersama interval Wilson 95%.** Pemilik proyek menyatakan sampel diperluas bila
  hasilnya ambigu.

**Dikonfirmasi pemilik proyek 2026-10-04, sebelum berkas konfirmasi dibuka:**

- Ambangnya memang **"lebih dari separuh"** (kurung siku pada rumusan awal adalah sisa templat,
  bukan angka yang masih terbuka).
- **Hasil dianggap jelas** bila interval Wilson 95%-nya **seluruhnya di atas atau seluruhnya di
  bawah 50%**; **ambigu** bila interval itu melintasi 50% (pada 50 butir sah kira-kira proporsi
  teramati antara 37% dan 63%; batas persisnya dihitung dari jumlah butir sah yang sebenarnya).
- **Bila ambigu, sampel diperluas ke 100 butir** (seluruh sampel Liputan6 yang sah), lalu aturan
  yang sama diterapkan pada hasil 100 butir itu.
- Akibatnya aturan "proporsi teramati di atas 50%" di atas hanya memutuskan bila hasilnya jelas;
  hasil ambigu tidak diputuskan dari 50 butir.

### 11.3 Sampel dan aturan (ditetapkan 2026-10-04)

- **50 butir** dipilih acak berbenih (benih 20261004) dari 100 artikel Liputan6 pada sampel 10.2,
  **setelah** artikel yang bukan putusan hoaks dikeluarkan.
- **Dikeluarkan: 1 artikel** -- "Cek Fakta: Klarifikasi Polri soal Deretan Kabupaten Siap ke Jakarta
  27 Agustus 2026": penanda vonis Liputan6 sendiri adalah "klarifikasi" (judul dan label
  banner), dan Kesimpulannya hanya menyatakan postingan itu "telah diklarifikasi", bukan bahwa
  klaimnya tidak benar. Aturan (`candidates.gap_review.is_non_hoax_verdict`): dikeluarkan bila judul
  berkata vonis "klarifikasi", atau banner berlabel "klarifikasi" sementara judul tanpa kata vonis
  salah/hoaks dan Kesimpulan tidak menyatakan klaimnya keliru. **Dua artikel yang penandanya tidak
  tegas TIDAK dikeluarkan otomatis:** "Tidak Benar Maladewa Putus Hubungan Diplomatik dengan Israel
  ..." (banner "Klarifikasi", tetapi judul dan Kesimpulan menyatakan "tidak benar") dan "Video Sri
  Mulyani Diperiksa Bareskrim Polri Ini Terjadi pada 2015" (tanpa kata vonis dan tanpa banner;
  Kesimpulan: "video lama pada 2015"). Berkas konfirmasi menyediakan pilihan "BUKAN PUTUSAN HOAKS"
  agar pemilik proyek yang memutuskan butir seperti itu.
- **Berkas yang dihasilkan (2026-10-04):** `data/candidates/celah_liputan6/konfirmasi_50.csv` -- 50
  butir, 326 baris kandidat (5-8 per butir, median 7); 2 butir di ujung rentang (terbit 18 dan 23
  September 2026); 3 butir memuat kandidat dari antrean (16 artikel antrean, terbit 27 Sep-2 Okt
  2026); kolom KEPUTUSAN kosong. Skor kemiripan disimpan terpisah (`kunci_kandidat.json`).
- **Kandidat** dicari dari JUDUL artikel Liputan6 (kata vonis di awal dibuang), bukan dari pesan:
  5 teratas pencarian embedding pada indeks 1.532 artikel + 3 teratas pencocokan kata kunci pada
  judul 1.532 artikel. Skor kemiripan TIDAK ditampilkan di berkas, dan kandidat diurutkan menurut
  tanggal, bukan menurut skor.
- **Efek ujung rentang.** TurnBackHoax bisa memeriksa hoaks yang sama beberapa hari setelah Liputan6
  (bukti: `v1-050`). Karena itu judul artikel dari **antrean pembaruan terjadwal** (belum di-ingest;
  termasuk yang terbit setelah 27 September 2026) ikut dijadikan kandidat lewat pencocokan kata kunci
  pada judul, dan butir Liputan6 yang terbit pada dua minggu terakhir rentang (14-27 September 2026)
  ditandai agar hasilnya dapat dibandingkan.
- **Kesamaan klaim ditentukan pemilik proyek sendiri dengan pedoman anotasi v1.0, tanpa bantuan AI.**
  Berkas disiapkan kode (kandidat dan tata letak); keputusan diisi manusia (Aturan Wajib #5).
- Berkas dan teksnya lokal (`data/candidates/celah_liputan6/`, tidak di-commit).
- **Versi `.xlsx` (2026-10-04, permintaan pemilik proyek; inilah yang diisi dan dibaca):**
  `konfirmasi_50.xlsx`, dibuat `python -m candidates.gap_workbook --make` dari `konfirmasi_50.csv`
  tanpa mengambil ulang sampel (326 baris, 50 butir; isi dibaca ulang identik dengan CSV). Teks
  dibungkus, baris judul dibekukan, lebar kolom diatur, Kesimpulan tetap paling kanan, semua sel
  bertipe teks, tanpa skor.
- **Asal-usul berkas (Aturan Wajib #5).** Berkas buatan `openpyxl` ber-*creator* kode, persis tanda
  yang dipakai untuk mendeteksi kejadian 2026-09-22. Karena itu: (1) *creator*-nya ditulis
  eksplisit "tata letak dihasilkan kode, KEPUTUSAN diisi manusia"; (2) sidik jari templat kosong
  disimpan saat dibuat (`sidik_jari_templat_xlsx.json`): KEPUTUSAN terisi 0, catatan terisi 0,
  sidik jari isi selain kolom manusia `501df3816f509baa...`, SHA-256 berkas `387147e2edc768f4...`;
  (3) pembacaan (`--read`) menolak menghitung bila sel selain KEPUTUSAN/catatan berbeda dari
  templat, dan melaporkan apakah berkas terakhir disimpan aplikasi lain (`lastModifiedBy`).
  Pemeriksaan ini membuktikan berkas disimpan lewat Excel, **bukan** siapa yang mengetik; yang
  terakhir tetap pernyataan pemilik proyek.
- **Pembacaan tidak menebak.** Keputusan dibaca dari baris pertama tiap butir. Sel kosong, tulisan
  di luar tiga pilihan, id di luar daftar kandidat, dan keputusan yang diketik di baris kandidat
  hanya dilaporkan untuk ditanyakan; hasil tidak dihitung sampai semuanya jelas.

### 11.4 Batas tafsir

- Mengukur celah terhadap SATU situs cek fakta lain pada artikel kasus tunggal ("Cek Fakta: ...");
  artikel rangkuman tidak tersampel. Ini bukan ukuran celah terhadap klaim yang diketik pengguna.
- **Label Liputan6** (100 artikel sampel; koreksi 2026-10-04 atas laporan awal yang menyebut "tanpa
  banner 62" -- pola pembacaan banner waktu itu keliru): halaman Kesimpulan memuat **banner
  berlabel**, yaitu "Cek Fakta: Salah" 58, "Hoax" 39, "Klarifikasi" 2, tanpa banner 1. Kata vonis di
  awal judul: "Tidak Benar" 57, "Hoaks" 40, "Klarifikasi" 1, tanpa 2. Keduanya hampir selalu
  berpasangan (judul "Tidak Benar" dengan banner "Salah" 55; judul "Hoaks" dengan banner "Hoax" 37),
  jadi Liputan6 membedakan setidaknya tiga label: Salah, Hoax, Klarifikasi. **Pemetaannya ke label
  TurnBackHoax (SALAH, PENIPUAN, PARODI, ...) tidak diasumsikan**; hanya dilaporkan dari pasangan
  yang dikonfirmasi.

### 11.5 Hasil 50 butir (2026-10-08)

Alat: `python -m candidates.gap_result --hasil` lalu `--kunci` (uji `tests/test_gap_result.py`).
Keluaran lokal, tidak di-commit: `hasil_konfirmasi.json`, `perbandingan_kunci.json`.

**Asal-usul label (Aturan Wajib #5; dicatat apa adanya menurut pernyataan pemilik proyek).**

- Keputusan diisi pemilik proyek. **Butir 1-5 dibahas bersama Claude** sebagai contoh cara mengisi;
  **butir 6-50 dikerjakan pemilik proyek sendiri tanpa bantuan AI.** Ini berbeda dari rencana di 11.3
  ("tanpa bantuan AI" untuk seluruh butir).
- **Setelah selesai, Claude memeriksa berkas terisi** dan menunjukkan dua aturan yang diterapkan
  tidak konsisten (lihat sensitivitas). Pemilik proyek **mempertahankan semua keputusan apa adanya**
  dan melaporkan inkonsistensinya sebagai keterbatasan; tidak ada label yang direvisi setelah data
  dilihat. Pembahasan dan pemeriksaan itu terjadi di luar sesi Claude Code yang menghitung hasil ini;
  tidak ada catatannya di repositori.
- **Berkas yang dihitung bukan `konfirmasi_50.xlsx` (templat kode pada 11.3)**, melainkan
  `konfirmasi_50_terisi.csv`: pemilik proyek mengisi versi `.xlsx` lain
  (`konfirmasi_50_rapi_terisi.xlsx`) lalu mengonversinya kembali ke CSV dan menyeragamkan penulisan
  "Tidak Ada" menjadi "TIDAK ADA". Akibatnya pemeriksaan sidik jari templat `.xlsx`
  (`gap_workbook --read`) **tidak dijalankan**; penggantinya adalah pembandingan CSV terisi dengan
  `konfirmasi_50.csv`. `konfirmasi_50.xlsx` dan `konfirmasi_50.csv` tidak ditimpa (KEPUTUSAN tetap
  kosong). SHA-256 berkas terisi `f8e8909e8ae67753...`.
- `kunci_kandidat.json` dibuka kode baru setelah hasil utama, sensitivitas, dan rincian tersimpan.
  Label Liputan6 untuk tabel silang didapat tanpa kunci (butir dipetakan ke artikel sampel lewat
  judul; pemetaannya kemudian terbukti sama dengan urutan di kunci).

**Validasi: lolos.** 50 butir, 326 baris; setiap KEPUTUSAN adalah id kandidat butirnya atau TIDAK
ADA; tidak ada keputusan di baris bukan-pertama; kolom selain KEPUTUSAN/catatan identik dengan
`konfirmasi_50.csv`. Kolom catatan (terisi 50/50) tidak di-parse.

**Hasil utama (aturan 11.2 diterapkan apa adanya).**

| | TIDAK ADA / butir sah | Proporsi | Wilson 95% | Kategori 11.2 |
| --- | --- | --- | --- | --- |
| Label utama | 29 / 50 | 58,0% | [44,2%; 70,6%] | **AMBIGU** (interval melintasi 50%) |

Proporsi teramati di atas separuh, tetapi menurut 11.2 hasil ambigu **tidak diputuskan dari 50
butir**: sampel diperluas ke 100 butir, lalu aturan yang sama diterapkan. Jadi 50 butir ini **belum
mendukung dan belum menolak** arah "belum ditemukan". BUKAN PUTUSAN HOAKS: **0 butir**, sehingga
penyebutnya tetap 50; butir 44 (Maladewa, banner "Klarifikasi") diperlakukan pemilik proyek sebagai
butir sah dan diputuskan TIDAK ADA.

**Sensitivitas -- EKSPLORATIF, tidak dipra-registrasi.** Pemilik proyek menyatakan dua aturan
diterapkan tidak konsisten: (1) *selisih waktu/gelombang* -- kandidat butir 2 ditolak karena
tahun/periodenya berbeda, tetapi butir 8, 14, 28, 49 diterima walau selisih waktunya lebih jauh
(8 dan 28 sama-sama dicocokkan ke 36654); (2) *detail yang tidak disebut di judul TurnBackHoax* --
ditolak di butir 15, 20, 21, 22, 25, 29, 32; diterima di butir 24, 39, 40, 48. Label utama tidak
diubah; yang dihitung hanya batasnya.

| Batas | Butir dibalik | TIDAK ADA / sah | Proporsi | Wilson 95% | Kategori 11.2 |
| --- | --- | --- | --- | --- | --- |
| Atas | 8, 14, 24, 28, 39, 40, 48, 49 -> TIDAK ADA | 37 / 50 | 74,0% | [60,5%; 84,1%] | jelas di atas 50% |
| Bawah | 15, 20, 21, 22, 25, 29, 32 -> cocok | 22 / 50 | 44,0% | [31,2%; 57,7%] | ambigu |

**Kategori keputusan TIDAK sama di kedua batas: kesimpulan bergantung pada aturan pelabelan.**
Dengan aturan ketat hasilnya menjadi "layak dikerjakan"; dengan aturan longgar tetap ambigu dengan
proporsi teramati di bawah separuh. Pada tidak satu pun batas hasilnya "jelas di bawah 50%". Lima
belas dari 50 butir (30%) berada di daftar meragukan, lebih lebar daripada jarak hasil utama ke
ambang (4 butir).

**Rincian pendukung.**

- *Ujung rentang (n = 2; tidak ditarik kesimpulan):* butir 3 (18 Sep 2026) cocok dengan 36776;
  butir 21 (23 Sep 2026) TIDAK ADA.
- *Label banner Liputan6 pada 50 butir:* salah 26, hoax 22, hoaks 1 (ejaan banner apa adanya),
  klarifikasi 1. Pada 29 butir TIDAK ADA: salah 15, hoax 12, hoaks 1, klarifikasi 1.
- *Tabel silang, hanya 21 pasangan yang dikonfirmasi cocok:*

  | Banner Liputan6 | SALAH | PENIPUAN | PARODI | SATIR | Jumlah |
  | --- | --- | --- | --- | --- | --- |
  | salah | 3 | 7 | 1 | 0 | 11 |
  | hoax | 5 | 4 | 0 | 1 | 10 |

  Kedua label Liputan6 berpasangan dengan SALAH maupun PENIPUAN; pada 21 pasangan ini tidak tampak
  pemetaan satu-ke-satu (n kecil; tidak diuji).
- *Waktu terbit artikel TurnBackHoax terhadap artikel Liputan6 (21 pasangan):* sebelum 7, hari yang
  sama 1, sesudah 13. Tidak ada pasangan dari antrean (semua dari indeks). Di antara "sesudah" ada
  butir 28 (selisih ~11 bulan), butir 8 (~8 bulan), dan butir 49 (~5 bulan) -- ketiganya di daftar
  meragukan; 36654 dipilih dua kali.

**Keputusan vs pencarian otomatis (kunci dibuka setelah semua di atas tersimpan; TIDAK dipakai
untuk mengubah label).**

- Dari 21 pasangan cocok, id pilihan pemilik proyek adalah kandidat **teratas pencarian embedding
  pada 18** (ada di 5 teratas: 20) dan **teratas pencocokan kata kunci judul pada 20** (ada di 3
  teratas: 21). Teratas di keduanya: 18. Bukan teratas di keduanya: butir 3 (36776: di luar 5
  teratas embedding, peringkat 2 kata kunci). Embedding peringkat 2: butir 31 dan 49.
- **Skor tidak memisahkan cocok dari tidak cocok.** Skor embedding pilihan: 0,5733-0,7831 (median
  0,6903). Skor kandidat teratas pada 29 butir TIDAK ADA: 0,4833-0,7294 (median 0,6270); **22 dari
  29 berada di atas skor pilihan terendah.** Dua butir TIDAK ADA di atas median pilihan: butir 10
  (0,7294) dan butir 20 (0,7271).
- Butir TIDAK ADA dengan tumpang tindih kata kunci judul tertinggi: 21 (0,75), 20 (0,67), 15 (0,60),
  22 (0,50) -- keempatnya juga ada di daftar "ditolak secara meragukan". Ini pengamatan, bukan dasar
  untuk membalik label.
- Tafsir yang sah: bila ada pasangan, kandidat teratas hampir selalu pasangan itu; tetapi kandidat
  teratas selalu ada juga saat tidak ada pasangan, dan skornya tidak membedakan kedua keadaan
  (sejalan dengan temuan Versi 1). Catatan: kandidat hanya berasal dari kedua pencarian ini, jadi
  pasangan yang luput dari keduanya tidak mungkin dipilih -- angka di atas adalah kesepakatan
  **dengan syarat** pasangannya ada di daftar, bukan recall.

**Keterbatasan.**

- **Satu anotator**; kesepakatan antar-anotator tidak terukur.
- **Butir 1-5 dibahas bersama AI** (3 di antaranya cocok, 2 TIDAK ADA), dan berkas terisi diperiksa
  AI sebelum dihitung (tanpa revisi label).
- **Dua aturan diterapkan tidak konsisten** pada 15 butir, dan kategori keputusan berubah di batas
  atas. Daftar butir meragukan disusun setelah pelabelan, jadi sensitivitasnya eksploratif.
- **Perbandingan hanya berbasis judul dan Kesimpulan** artikel TurnBackHoax (Narasi tidak
  ditampilkan), dan kandidat dicari dari judul Liputan6.
- Pemeriksaan sidik jari templat `.xlsx` tidak berlaku untuk berkas yang dipakai (lihat asal-usul).
- Batas tafsir 11.4 tetap berlaku (satu situs pembanding; bukan klaim yang diketik pengguna).

**Langkah berikutnya (menurut 11.2 dan keputusan pemilik proyek 2026-10-08).** Sampel diperluas ke
100 butir. **Berkas 50 butir berikutnya BELUM dibuat:** dua aturan pelabelan tertulis (selisih
waktu/gelombang tautan penipuan; detail tidak disebut vs detail bertentangan) dikunci pemilik proyek
lebih dulu, sebelum data baru dilihat. Aturan itu hanya berlaku untuk butir baru; 50 butir di atas
tidak dilabel ulang.

### 11.6 Aturan untuk perluasan ke 99 butir (DIKUNCI pemilik proyek 2026-10-09, sebelum berkas butir baru dibuat)

Dikunci setelah hasil 50 butir pertama dilihat (11.5) dan **sebelum** berkas konfirmasi butir baru
dibuat, kandidatnya dicari, atau kuncinya ada. Berlaku **hanya untuk butir baru**; 50 butir lama
tidak dilabel ulang.

**Jumlah butir (dipastikan dari berkas sampel, bukan diasumsikan).** `sampel_liputan6.jsonl`: 100
artikel, 100 id unik; 1 dikeluarkan aturan `is_non_hoax_verdict` (11.3); 99 sah. Pengambilan
berbenih 20261004 direproduksi dan sama persis dengan 50 butir yang sudah dikonfirmasi; **sisanya 49
butir**. Total setelah perluasan: **99**, bukan 100 seperti tertulis di 11.2.

**Aturan A -- selisih waktu atau gelombang.** Unsur inti (subjek, tindakan, objek pembeda)
menentukan; **tanggal terbit tidak**. Untuk tautan penipuan berulang, lembaga dan jenis tawaran yang
sama berarti cocok walaupun gelombangnya berbeda. Tahun atau periode hanya menjadi pembeda bila
**disebut eksplisit di kedua sisi dan berbeda**.
*Keterbatasan yang diterima:* pada penipuan tahunan, tahun di judul sering hanya penanda gelombang,
sehingga aturan ini bisa memisahkan dua artikel yang sebenarnya gelombang dari penipuan yang sama.
Aturan ini dipilih karena **objektif**, bukan karena pasti benar.

**Aturan B -- detail tidak disebut versus detail bertentangan.** Detail yang tidak disebut **bukan**
alasan menolak; hanya detail yang **bertentangan pada unsur inti** yang menjadi alasan menolak.
Pembandingnya adalah **kutipan pesan Liputan6 dengan Narasi TurnBackHoax**, bukan hanya judul dan
Kesimpulan. Butir baru boleh ditandai ragu **hanya setelah Narasinya dibaca**. Tanda ragu disimpan
di kolom tersendiri `ragu` (`YA` atau kosong), bukan di catatan.

**Sensitivitas butir baru (ditetapkan di muka).** Dua arah: semua butir bertanda ragu dihitung
cocok (batas bawah proporsi TIDAK ADA), dan semua butir bertanda ragu dihitung TIDAK ADA (batas
atas). Label utama tidak diubah.

**Aturan berhenti.** Bila pada 99 butir interval Wilson 95% **masih mencakup 50%**, sampling
dihentikan dan **ambang dinyatakan tidak terpenuhi**: sumber kedua tidak diprioritaskan sekarang.
**Tidak ada perluasan ketiga.** Bila interval seluruhnya di atas 50%: layak dikerjakan; seluruhnya di
bawah 50%: tidak.

**Pelaporan.**

- **Hasil utama = 99 butir gabungan** (50 lama + 49 baru), sesuai pra-registrasi 11.2; butir BUKAN
  PUTUSAN HOAKS keluar dari penyebut.
- **Hasil sekunder = 49 butir baru saja**, yang dilabel dengan aturan terkunci di atas.
- Sensitivitas 50 butir lama tetap memakai batas 11.5 (37/50 dan 22/50); tidak dihitung ulang.
  Operasionalisasi untuk gabungan (usulan Claude Code, dicatat sebelum data baru ada; eksploratif):
  batas atas gabungan = batas atas lama + batas atas baru, begitu juga batas bawah.

**Berkas konfirmasi butir baru (rancangan; dibuat setelah bagian ini di-push).**

- Tata letak **blok per butir**: judul dan kutipan pesan Liputan6 di atas; sel masukan KEPUTUSAN,
  ragu, catatan; lalu tabel kandidat berkolom id, tanggal, label, asal, judul, **Narasi TurnBackHoax
  utuh**, Kesimpulan. Kandidat tanpa Narasi ditandai dan jumlahnya dilaporkan.
- Masukan **hanya** di sel blok. Lembar Rekap berisi rumus saja dan diproteksi (tanpa kata sandi):
  pada 50 butir pertama pemilik proyek sempat mengetik di lembar rekap karena tidak ada yang
  mencegahnya.
- Pembaca mengambil keputusan dari sel blok, menolak berkas yang kolom buktinya berubah dari
  templat, dan menyeragamkan huruf besar-kecil (`Tidak Ada` -> `TIDAK ADA`); selain itu tidak
  menafsirkan apa pun.
- Kandidat dicari dengan cara yang sama (11.3: dari judul Liputan6; 5 teratas embedding + 3 teratas
  kata kunci judul), diurutkan menurut tanggal, tanpa skor; kunci skor disimpan terpisah dan tidak
  dibuka sampai pemilik proyek selesai.

**Perbedaan antara 50 butir lama dan 49 butir baru yang ikut membatasi hasil gabungan** (dicatat di
muka): (1) aturan pelabelan berbeda (lama: pedoman v1.0 dengan dua inkonsistensi; baru: Aturan A dan
B); (2) bukti yang dilihat berbeda (lama: judul dan Kesimpulan; baru: juga Narasi utuh); (3) antrean
yang ikut dijadikan kandidat berbeda (lama: 16 artikel; baru: antrean pada saat berkas dibuat).

**Berkas dibuat 2026-10-09, setelah aturan di atas di-push (commit `c347e20`).**
`python -m candidates.gap_blocks --make` -> `konfirmasi_49.xlsx` (lokal, tidak di-commit): **49
butir**, 319 baris kandidat (5-8 per butir, median 7), 1 butir ujung rentang, antrean 32 artikel (6
butir memuat kandidat dari antrean), **kandidat tanpa Narasi: 0**, sel masukan terisi saat dibuat: 0.
Sidik jari bukti `932e756ae3a87d21...`; peta blok dan sidik jari di `sidik_jari_templat_49.json`;
skor di `kunci_kandidat_49.json` (ditulis, tidak dibaca alat ini). Lembar konfirmasi dan Rekap
diproteksi tanpa kata sandi; yang tidak terkunci hanya sel KEPUTUSAN, ragu, dan catatan di tiap blok
(proteksi lembar konfirmasi adalah tambahan Claude Code agar masukan memang hanya bisa di sel blok;
lebar kolom dan tinggi baris tetap bisa diubah). Pembacaan: `python -m candidates.gap_blocks --read`
(uji `tests/test_gap_blocks.py`); pada templat kosong ia menolak menghitung (49 butir kosong).
Isi berkas tidak dibuka atau diringkas Claude Code.

### 11.7 Selisih hari terbit pada 21 pasangan cocok (EKSPLORATIF; dari 50 butir pertama)

Selisih = tanggal terbit TurnBackHoax dikurangi tanggal terbit Liputan6 (positif = TurnBackHoax
belakangan). Hanya untuk menimbang apakah cakupan *saat hoaks beredar* perlu diukur terpisah nanti;
bukan dasar keputusan sekarang.

- Bertanda: minimum -197, kuartil bawah -5, **median +3**, kuartil atas +6, maksimum +323 hari.
- Nilai mutlak: kuartil bawah 3, median 6, kuartil atas 36 hari. **Dalam 14 hari: 15 dari 21;
  di atas 30 hari: 6 dari 21.**
- 13 pasangan "sesudah": **10 terpaut 1-14 hari** (1, 2, 3, 3, 4, 4, 5, 6, 8, 14) dan 3 terpaut jauh
  (159, 248, 323 hari: butir 49, 8, 28). 7 pasangan "sebelum": 4 terpaut 3-9 hari, 3 terpaut jauh
  (36, 42, 197 hari: butir 42, 48, 14). Satu pasangan terbit di hari yang sama.
- Jadi sebagian besar pasangan "sesudah" adalah TurnBackHoax terlambat beberapa hari, bukan
  gelombang lain. Lima dari enam pasangan yang terpaut lebih dari 30 hari ada di daftar "diterima
  secara meragukan" (8, 14, 28, 48, 49); yang keenam butir 42.
- Batas: n = 21, satu anotator, dan tanggal yang dibandingkan adalah tanggal terbit artikel cek
  fakta, bukan tanggal hoaks beredar.

### 11.8 Hasil 99 butir (2026-10-13): ambang TIDAK terpenuhi, sampling dihentikan

Alat: `python -m candidates.gap_blocks --read` (bawaan membaca `konfirmasi_49_terisi.xlsx`; uji
`tests/test_gap_blocks.py`). Keluaran lokal, tidak di-commit: `hasil_konfirmasi_49.json`. Bagian ini
(langkah 1-6) di-commit **sebelum** `kunci_kandidat_49.json` dibuka; perbandingan dengan kunci ada di
11.9.

**Asal-usul label (Aturan Wajib #5; dicatat apa adanya menurut pernyataan pemilik proyek).**

- Ke-49 butir dilabel pemilik proyek sendiri, tanpa bantuan AI, dengan Aturan A dan B (11.6).
- Claude (di luar sesi Claude Code yang menghitung hasil ini) **tidak membahas satu butir pun**.
  Bantuannya hanya teknis: cara keluar dari Protected View, letak sel isian, penjelasan umum Aturan
  A/B, dan pola penulisan catatan dengan contoh rekaan yang tidak diambil dari data.
- **Satu perubahan pada berkas oleh Claude:** templat menampilkan baris kandidat setinggi satu
  baris sehingga Narasi terpotong di layar, jadi tinggi baris diperbesar lewat openpyxl. Menurut
  pemilik proyek, isi sel, proteksi, sel terbuka, dan sel gabungan sudah dicek identik dengan
  templat. Diperiksa ulang di sesi ini pada berkas terisi: proteksi kedua lembar aktif; sel tak
  terkunci = tepat 245 sel masukan (49 blok x KEPUTUSAN, ragu, dan sel catatan gabungan F-H); 147
  sel gabungan sama dengan yang dibuat kode; tinggi baris kandidat 43,5-409,5 poin. Satu jejak kecil
  perubahan itu: *creator* berkas terisi kehilangan satu spasi (`openpyxl;tata letak ...`, templat
  `openpyxl; tata letak ...`).
- **Cacat alat yang diperbaiki:** `gap_blocks.write_workbook` dulu tidak menyetel tinggi baris
  kandidat. Kini disetel dari panjang teks dan lebar kolom (`wrapped_height`), dibatasi 409 poin
  (batas Excel; Narasi yang sangat panjang tetap terpotong di layar, isi sel utuh). Hanya berlaku
  untuk berkas yang dibuat kemudian; berkas 49 butir tidak dibuat ulang.
- **Templat tidak lagi kosong.** `konfirmasi_49.xlsx` disimpan Excel pada 2026-10-13 23.28 WIB
  dengan 45 KEPUTUSAN terisi (butir 2, 14, 18, 30 kosong) dan SHA-256-nya tidak lagi sama dengan
  sidik jari templat (`5c4ba627...` -> `d2a73ac6...`). Pembacaan pertama sesi ini (berkas terisi
  belum ada) berhenti dan melaporkannya; pemilik proyek lalu mengisi keempat butir dan menyimpan
  `konfirmasi_49_terisi.xlsx` (23.42 WIB), yang dihitung di sini. Bukti tidak terdampak: sidik
  jari sel bukti kedua berkas sama dengan templat (`932e756a...`).

**Langkah 1 -- validasi: lolos.** `konfirmasi_49_terisi.xlsx` (SHA-256 `b99e5bfef83e500b...`,
terakhir disimpan Microsoft Excel). Sidik jari seluruh sel selain KEPUTUSAN/ragu/catatan **sama**
dengan templat, jadi pemeriksaan tidak perlu dan tidak dilonggarkan: ia membandingkan nilai sel,
bukan format (tinggi baris tidak ikut). 49/49 KEPUTUSAN terisi dan sah (25 id kandidat butirnya, 24
TIDAK ADA, 0 BUKAN PUTUSAN HOAKS); kolom ragu hanya YA (butir 2, 14, 18, 30) atau kosong; catatan
terisi 46/49 (tidak di-parse).

**Langkah 2 -- hasil utama (11.2 dan 11.6 diterapkan apa adanya).**

| | TIDAK ADA / butir sah | Proporsi | Wilson 95% | Kategori |
| --- | --- | --- | --- | --- |
| **Gabungan 99 butir** | **53 / 99** | **53,5%** | **[43,8%; 63,0%]** | **AMBIGU** (interval mencakup 50%) |

BUKAN PUTUSAN HOAKS: 0 pada putaran lama dan 0 pada putaran baru, jadi penyebutnya 99. Menurut
aturan berhenti 11.6: **sampling selesai dan ambang dinyatakan TIDAK terpenuhi**; sumber kedua tidak
diprioritaskan sekarang. Proporsi teramati di atas separuh, tetapi ambang 11.2 menuntut interval
yang seluruhnya di atas 50%, dan itu tidak tercapai.

**Langkah 3 -- hasil sekunder dan sensitivitas (EKSPLORATIF selain baris "utama").**

| | TIDAK ADA / sah | Proporsi | Wilson 95% | Kategori |
| --- | --- | --- | --- | --- |
| 49 butir baru, label utama | 24 / 49 | 49,0% | [35,6%; 62,5%] | ambigu |
| Baru, butir ragu dihitung TIDAK ADA (butir 18 dibalik) | 25 / 49 | 51,0% | [37,5%; 64,4%] | ambigu |
| Baru, butir ragu dihitung cocok (butir 2, 14, 30 dibalik) | 21 / 49 | 42,9% | [30,0%; 56,7%] | ambigu |
| Gabungan, batas atas (37/50 + 25/49) | 62 / 99 | 62,6% | [52,8%; 71,5%] | **jelas di atas 50%** |
| Gabungan, batas bawah (22/50 + 21/49) | 43 / 99 | 43,4% | [34,1%; 53,3%] | ambigu |

**Kategori TIDAK sama di semua batas:** semuanya ambigu kecuali batas atas gabungan, yang jelas di
atas 50%. Batas atas itu sepenuhnya digerakkan oleh batas atas 50 butir lama (37/50; butir baru
hanya menambah satu). Pada putaran baru sendiri, keempat butir ragu tidak mengubah kategori.

**Langkah 4 -- dua putaran berdampingan (DESKRIPTIF, tanpa uji signifikansi).**

| Putaran | TIDAK ADA / sah | Proporsi | Wilson 95% |
| --- | --- | --- | --- |
| 50 butir pertama (11.5) | 29 / 50 | 58,0% | [44,2%; 70,6%] |
| 49 butir sisa | 24 / 49 | 49,0% | [35,6%; 62,5%] |

Selisih 9 poin persentase tidak diuji dan tidak ditafsirkan sebagai perbedaan populasi: ia tidak
dapat dipisahkan dari tiga perbedaan yang dicatat di muka pada 11.6 (aturan pelabelan, bukti yang
dilihat -- kini dengan Narasi utuh --, dan isi antrean kandidat).

**Langkah 5 -- rincian pendukung.**

- *BUKAN PUTUSAN HOAKS:* 0 butir (tidak ada alasan untuk dilaporkan).
- *Banner Liputan6 pada 49 butir baru:* salah 32, hoax 16, tanpa banner 1. Pada 24 butir TIDAK ADA:
  salah 15, hoax 8, tanpa banner 1.
- *Tabel silang banner Liputan6 x label TurnBackHoax, pasangan cocok:*

  | Banner Liputan6 | Pasangan | SALAH | PENIPUAN | PARODI | SATIR | Jumlah |
  | --- | --- | --- | --- | --- | --- | --- |
  | salah | baru (25) | 1 | 16 | 0 | 0 | 17 |
  | hoax | baru (25) | 3 | 5 | 0 | 0 | 8 |
  | salah | gabungan (46) | 4 | 23 | 1 | 0 | 28 |
  | hoax | gabungan (46) | 8 | 9 | 0 | 1 | 18 |

  Seperti pada 11.5, kedua label Liputan6 berpasangan dengan SALAH maupun PENIPUAN; tidak tampak
  pemetaan satu-ke-satu (tidak diuji). Pasangan baru didominasi PENIPUAN (21 dari 25; putaran lama
  11 dari 21).
- *Selisih hari terbit pasangan baru (TurnBackHoax dikurangi Liputan6; kuartil metode inklusif, sama
  dengan 11.7 -- diperiksa: metode ini memberi ulang angka 11.7 pada 21 pasangan lama):* bertanda
  min -212, kuartil bawah -134, **median -16**, kuartil atas +7, maks +95; mutlak kuartil bawah 7,
  **median 38**, kuartil atas 134 hari. Dalam 14 hari: 9 dari 25; **di atas 30 hari: 14 dari 25**
  (putaran lama: 6 dari 21). TurnBackHoax terbit sebelum Liputan6 pada 15 pasangan, sesudah pada 10.
  **Ke-14 pasangan yang terpaut lebih dari 30 hari semuanya PENIPUAN** -- sejalan dengan Aturan A
  (lembaga dan jenis tawaran sama = cocok walau gelombangnya berbeda). Artinya pada pasangan itu
  artikel TurnBackHoax membantah klaim yang sama dari gelombang sebelumnya/sesudahnya, bukan
  unggahan yang sama.
- *Pasangan yang artikel TurnBackHoax-nya hanya ada di antrean (belum di-ingest): 0 dari 25.*
  Seluruh 25 artikel pilihan ada di `data/articles.json` (1.532 artikel) dan indeks produksi. Enam
  butir memuat kandidat dari antrean (butir 3, 7, 17, 27, 28, 49); tidak satu pun kandidat antrean
  dipilih (butir 7 dan 28 cocok dengan artikel indeks; empat lainnya TIDAK ADA). Putaran lama juga
  0. Jadi pada 99 butir **tidak ada** pasangan yang ada di TurnBackHoax tetapi belum terjangkau
  sistem karena belum di-ingest.
- *Ujung rentang (n = 1, tanpa kesimpulan):* butir 49 TIDAK ADA.
- Tidak ada artikel TurnBackHoax yang dipilih dua kali pada putaran baru, dan tidak ada yang juga
  dipilih pada putaran lama.

**Langkah 6 -- catatan interpretasi (keterbatasan; kualitatif, tanpa melabel ulang).** 50 butir lama
dilabel dengan aturan yang berbeda dan, dalam satu hal, lebih ketat daripada aturan yang kini
dikunci. Arah pergeserannya, dinilai hanya dari uraian 11.5 (butirnya tidak dilihat ulang). **Semua
penilaian di butir-butir berikut adalah pembacaan agent (Claude Code) atas uraian itu, bukan label,
dan tidak mengubah hasil** (rumusan dirapikan 2026-10-17 atas permintaan pemilik proyek):

- *Diterima secara meragukan (8 butir: 8, 14, 24, 28, 39, 40, 48, 49).* Alasan keraguan 11.5 adalah
  selisih waktu yang jauh (8, 14, 28, 49; juga 48 menurut 11.7) atau detail yang tidak disebut
  judul TurnBackHoax (24, 39, 40, 48). Di bawah Aturan A dan B keduanya **bukan** alasan menolak,
  jadi penerimaan itu, **menurut pembacaan agent, konsisten dengan Aturan A/B; ini bukan label dan
  tidak mengubah hasil**. Bila pembacaan itu benar, batas atas lama (37/50), yang membalik kedelapan
  butir ini menjadi TIDAK ADA, kurang didukung aturan terkunci, padahal hanya batas itulah yang
  membuat gabungan "jelas di atas 50%". Sebagai ilustrasi aritmetika saja: tanpa
  empat butir selisih-waktu itu, batas atas gabungan menjadi 58/99 = 58,6% [48,7%; 67,8%] -- ambigu.
- *Ditolak secara meragukan (7 butir: 15, 20, 21, 22, 25, 29, 32)* karena detail "tidak disebut".
  Di bawah Aturan B itu bukan alasan menolak; sebagian bisa menjadi cocok, sebagian tetap ditolak
  bila Narasi (yang dulu tidak ditampilkan) memuat detail yang bertentangan. Jumlahnya tidak
  diketahui tanpa melabel ulang. Butir 2 (ditolak karena tahun/periode) hanya tetap ditolak bila
  tahunnya eksplisit dan berbeda di kedua sisi.
- *Arah bersih (pembacaan agent, bukan label):* bila aturan terkunci diterapkan seragam, TIDAK ADA pada 50 butir lama kemungkinan
  **berkurang atau tetap**, tidak bertambah. Jadi 53/99 kemungkinan **melebih-lebihkan** proporsi
  TIDAK ADA relatif terhadap aturan terkunci; dengan label utama butir baru, nilai seragamnya berada
  antara 46/99 (46,5% [37,0%; 56,2%], bila ketujuh butir menjadi cocok) dan 53/99.
  Pergeseran itu menjauh dari ambang, bukan mendekatinya, sehingga tidak mengubah kesimpulan
  "ambang tidak terpenuhi". Yang tidak dapat dinilai: arah pengaruh Narasi pada butir lama (bisa
  menambah maupun mengurangi kecocokan).
- Keterbatasan lain tetap berlaku: satu anotator, 1-5 butir lama dibahas bersama AI (11.5), kandidat
  hanya dari dua cara pencarian berbasis judul (pasangan yang luput dari keduanya tidak mungkin
  dipilih, jadi TIDAK ADA bisa sedikit melebih-lebihkan celah), dan batas tafsir 11.4.

### 11.9 Keputusan 49 butir baru vs pencarian otomatis (kunci dibuka 2026-10-17, setelah 11.8 di-commit `d6add92`)

`python -m candidates.gap_blocks --kunci` -> `perbandingan_kunci_49.json` (lokal). Fungsinya sama
dengan putaran pertama (`gap_result.compare_with_key`); urutan butir di kunci diperiksa sama dengan
peta blok templat. **Hanya untuk menilai pencarian otomatis; TIDAK dipakai untuk mengubah label.**

| Ukuran (pasangan cocok) | Putaran 1 (21) | Putaran 2 (25) |
| --- | --- | --- |
| Pilihan = teratas embedding | 18 | 17 |
| Pilihan di 5 teratas embedding | 20 | 25 |
| Pilihan = teratas kata kunci judul | 20 | 18 |
| Pilihan di 3 teratas kata kunci | 21 | 24 |
| Teratas di keduanya | 18 | 15 |
| Skor embedding pilihan, min / median / maks | 0,5733 / 0,6903 / 0,7831 | 0,5879 / 0,7046 / 0,7663 |

- Bukan teratas di keduanya: butir 1 (embedding peringkat 5, kata kunci 3), 4 (2, di luar 3 teratas
  kata kunci), 34, 42, 46 (embedding peringkat 2). Butir ragu yang cocok (18) teratas di keduanya.
- **Skor tetap tidak memisahkan cocok dari tidak cocok.** Skor embedding teratas pada 24 butir TIDAK
  ADA: 0,5850 / 0,6400 / 0,7582 (min / median / maks); **23 dari 24 di atas skor pilihan terendah**
  (putaran 1: 22 dari 29). Di atas median pilihan (0,7046): butir 8 (0,7582), 41 (0,7509), 17
  (0,7393), 30 (0,7083; butir ragu).
- Tumpang tindih kata kunci judul tertinggi pada butir TIDAK ADA: butir 2 (1,00; butir ragu), 8
  (0,90), 33 (0,71), 17 (0,56). Butir 8 dan 17 tinggi di kedua cara. Pengamatan, bukan dasar untuk
  membalik label: pada putaran ini pembanding manusia adalah Narasi utuh, sedangkan skor hanya
  membaca judul.
- Tafsir sama dengan 11.5: bila ada pasangan, ia hampir selalu ada di daftar dan sering teratas;
  kandidat berskor tinggi selalu ada juga saat tidak ada pasangan. Kesepakatan ini bersyarat pada
  pasangan ada di daftar, bukan recall.

### 11.10 Implikasi (ditulis 2026-10-17, setelah angka 11.8-11.9 keluar)

**Ambang yang ditetapkan sebelum data dilihat tidak terpenuhi:** pada 99 butir, 53,5% klaim Liputan6
tidak ada di basis data TurnBackHoax, dengan interval [43,8%; 63,0%] yang mencakup 50%. Menurut
aturan berhenti 11.6, sumber cek fakta kedua dan langkah korektif bergaya CRAG yang dibatasi ke situs
cek fakta **tidak diprioritaskan sekarang**, dan pengukuran ini tidak diperluas lagi. Itu bukan
bukti bahwa celahnya kecil: sekitar separuh klaim Liputan6 memang tidak diperiksa TurnBackHoax
(batas-batas eksploratif 43-63%), jadi "belum ditemukan" tetap akan sering menjadi jawaban yang sah
dan perlu dikomunikasikan di demo apa adanya. Yang tidak ditunjukkan data adalah bahwa celah itu
**jelas** melebihi separuh, dan menurut pembacaan agent pada 11.8 langkah 6 (bukan label) aturan terkunci kemungkinan
justru menurunkan angkanya. Dua temuan sampingan ikut membatasi rancangan apa pun di arah ini bila
kelak dibuka lagi: (1) skor kemiripan tidak memisahkan ada dari tidak ada pada kedua putaran (23/24
dan 22/29 butir TIDAK ADA berskor di atas pasangan sah terendah), jadi pemicu langkah korektif tidak
dapat berupa ambang skor -- ia membutuhkan penilai kesamaan klaim, yang sudah dikeluarkan dari
cakupan Versi 2; (2) 0 dari 46 pasangan hanya ada di antrean, jadi keterlambatan ingest bukan
penyebab celah pada sampel ini, dan sebagian besar pasangan baru adalah PENIPUAN berulang yang
cocok lintas gelombang (14 dari 25 terpaut lebih dari 30 hari), sehingga cakupan nyata untuk hoaks
semacam itu bergantung pada apakah generator menilai gelombang berbeda sebagai klaim yang sama
(pedoman v1.0 dan Aturan A tidak identik; belum diukur). Batas tafsir 11.4 tetap: ini celah terhadap
satu situs cek fakta, bukan terhadap klaim yang diketik pengguna.

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
| `src/candidates/chain_sample.py` | pengambilan sampel acak pesan berantai (bagian 10.2) |
| `src/evaluation/sample_size.py`, `testset/v2_ukuran_sampel.json`, `testset/v2_ukuran_sampel.txt` | seluruh angka ukuran sampel (bagian 4 dan 6.3) |
| `src/llm/limits.py` | kuota (RPM 15, TPM 250.000, RPD 500; 2026-09-21) |
| `src/generator.py`, `tests/test_testset_locks.py` | apa yang sudah dilakukan generator; apa yang terkunci |
| `CLAUDE.md` | keterbatasan, temuan Aturan Wajib #1, latensi Gemma, catatan memori |
