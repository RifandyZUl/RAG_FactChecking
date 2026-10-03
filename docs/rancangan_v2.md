# Rancangan Versi 2

**Status: dokumen rancangan, 2026-10-03. Belum ada kode Versi 2 dan belum ada keputusan.** Semua
angka di dokumen ini diambil dari berkas di repositori; sumbernya ditulis di samping tiap klaim
(daftar berkas di bagian akhir). Bila datanya tidak cukup untuk disimpulkan, itu ditulis terus
terang. Keputusan yang harus diambil pemilik proyek dikumpulkan di bagian 9.

Dokumen ini mengoreksi pemetaan lama di `testset/v1_temuan_untuk_v2.md` bagian 7 (dan tabel
"Rencana Versi 2" di README): beberapa komponen di sana dicantumkan dengan bukti yang, setelah
diperiksa ulang, tidak mendukungnya.

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

### M5. Mutu klarifikasi

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

## 2. Komponen yang diusulkan

Prinsip: komponen masuk hanya bila menjawab masalah di bagian 1, dan alternatif yang lebih
sederhana ditimbang lebih dulu.

### 2.1 Ekstraksi klaim dari pesan panjang (menjawab M1)

- **Tugas:** bila pesan melebihi ambang token, ambil klaim intinya lalu cari dengan klaim itu.
  Hanya tugas ini; "menulis ulang kueri saat retrieval gagal" **dicoret** (lihat bagian 8).
- **Alternatif yang lebih sederhana, tanpa LLM:** *pencarian per potongan pesan* -- pesan dipecah
  menjadi jendela <= 512 token, tiap jendela di-embed dan dicari, skor artikel = maksimum
  antar-jendela. Ini sudah disebut sebagai kemungkinan di `v1_temuan_untuk_v2.md` bagian 5.2.
  Kelebihan: nol panggilan LLM, deterministik, tidak bisa mengarang klaim. Kekurangan yang perlu
  diukur: pengganggu ikut dicari sehingga bisa memunculkan artikel yang mirip pengganggunya, dan
  LLM generator tetap membaca pesan utuh.
- **Belum diketahui mana yang lebih baik.** Keduanya belum pernah diukur. Rancangan ini mengusulkan
  keduanya diukur pada retrieval saja (tanpa generator, murah) sebelum memilih; bila pencarian per
  potongan menyamai ekstraksi LLM, yang dipilih pencarian per potongan.
- **Risiko yang wajib diukur:** kemunduran pada klaim pendek (karena itu hanya aktif di atas
  ambang token), dan klaim yang diubah maknanya oleh ekstraksi.

### 2.2 Grader (menjawab M2 dan mungkin M3)

**Apa yang bisa dilakukan grader yang belum dilakukan generator sekarang?** Generator Versi 1
sudah melakukan penilaian "klaim sama": prompt sistemnya memuat definisi resmi (KIA, unsur inti,
uji dua arah, uji Kesimpulan), ia membaca tiga kandidat sekaligus, dan mengeluarkan `klaim_sama`
serta `alasan` (CLAUDE.md, "Set uji Versi 1"; `src/generator.py`). Jadi grader **bukan kemampuan
baru**. Yang secara konkret berbeda hanya:

1. *Satu kandidat per panggilan* (bukan tiga sekaligus) -- dugaan: perhatian lebih terfokus.
2. *Keluaran terstruktur per unsur* (subjek, tindakan, objek/angka/waktu dibandingkan satu per satu)
   -- dugaan: menangkap selisih angka/waktu seperti `v1-036`, `v1-039`, `v1-040`.
3. *Kategori ketiga* "topik sama, klaim berbeda" -- yang dibutuhkan M3.
4. *Pemungutan suara* atas beberapa panggilan.

**Tidak satu pun dari keempatnya punya bukti.** Butir 1-2 adalah dugaan yang belum diuji. Butir 4
punya satu data: modus 3 run memberi 48/50 sedangkan run tunggal 46-48/50, tetapi `v1-020` keliru
di ketiga run (pemungutan suara tidak menolongnya) dan selisih 0-2 butir tidak dapat dibedakan
dari kebetulan.

**Alternatif yang lebih sederhana daripada node grader:**

- (a) *Tanpa grader.* Dasar: bukti M2 lemah, dan ukuran sampel yang layak tidak akan mampu
  menunjukkan perbaikan atas 2 kesalahan dari 50 (bagian 6.3).
- (b) *Pemungutan suara pada generator yang ada* (3 panggilan, modus) -- tanpa prompt baru, tetapi
  melipat-tigakan panggilan.
- (c) *Mengubah prompt generator* (keluaran per unsur) di salinan Versi 2 -- satu panggilan, tanpa
  node baru.

**Posisi rancangan:** grader **tidak direkomendasikan sebagai komponen wajib**. Bila M3 ("topik
sama, klaim berbeda") tetap diinginkan, bentuk paling sederhana adalah (c): menambah satu nilai
keluaran pada generator Versi 2, bukan node terpisah. Node grader terpisah hanya layak bila
ablasi menunjukkan (c) tidak cukup. Ini keputusan pemilik proyek (bagian 9, pertanyaan 2).

### 2.3 Rujukan (menjawab M4)

- **Yang diusulkan: pengukuran, bukan komponen LLM.** Menyimpan rujukan tiap jawaban di berkas
  hasil dan menghitung metrik kebersihan rujukan (bagian 5.4). Ini menutup celah evaluasi tanpa
  panggilan LLM tambahan.
- **Alternatif yang lebih berat:** penilai kredibilitas per-URL oleh LLM (membedakan akun resmi,
  menilai media). Tidak diusulkan: tidak ada bukti solusi, LLM tidak dapat membuka tautan, dan
  daftar domain eksplisit lebih mudah diaudit. Kelemahan daftar (melingkar, `.go.id`) dicatat
  sebagai keterbatasan, bukan diselesaikan Versi 2.

### 2.4 Mutu klarifikasi (menjawab M5)

Hanya instruksi gaya bahasa pada prompt salinan Versi 2 (kalimat aktif, subjek jelas), **bila**
pemilik proyek memutuskan M5 masuk cakupan. Catatan: ini mengubah dua hal sekaligus dengan
komponen lain bila dijalankan bersamaan, jadi perlu kondisi ablasi sendiri (bagian 5.3).

### 2.5 Kerangka: LangGraph atau pipeline Python biasa

Alur yang benar-benar dibutuhkan komponen di atas:

```
klaim -> [bila panjang: ekstraksi / pencarian per potongan] -> retrieval -> generator (dgn/tanpa perubahan prompt) -> jawaban
```

Alur ini linear dengan satu cabang bersyarat; tidak ada putaran. Satu-satunya putaran dalam
rencana awal ("tulis ulang kueri lalu cari lagi bila retrieval gagal") dicoret karena tidak ada
bukti masalahnya.

| | Pipeline Python biasa | LangGraph |
| --- | --- | --- |
| Kebutuhan alur ini | Fungsi berurutan + satu `if` | Graf dengan simpul dan tepi bersyarat |
| Dependensi baru | Tidak ada | Ya (`langgraph` tidak ada di `requirements.txt`) |
| Kendali kuota/throttle | Lapisan `src/llm/` yang ada dipakai apa adanya | Harus dijembatani ke lapisan itu |
| Pencatatan per langkah untuk ablasi | Ditulis sendiri (seperti `CallRecord` sekarang) | Tersedia, bentuknya ditentukan kerangka |
| Menyala-matikan komponen untuk ablasi | Parameter fungsi | Menyusun graf berbeda |

**Pilihan rancangan: pipeline Python biasa.** Alasannya hanya satu: alurnya tidak membutuhkan
lebih. LangGraph layak ditimbang ulang bila kelak ada putaran atau banyak cabang. Bila nilai
portofolio dari memakai kerangka itu dianggap penting, itu pertimbangan di luar bukti dan menjadi
keputusan pemilik proyek (pertanyaan 4).

---

## 3. Pemisahan dari Versi 1

`src/generator.py` terkunci sejak tag `testset-v1`: `v1.meta.json` (`sidik_jari_generator_v1`)
menyimpan hash seluruh berkas, hash prompt+skema, model (`gemini-3.5-flash-lite`), dan
`thinking_level` (`medium`), dan `tests/test_testset_locks.py` gagal bila salah satunya berubah.
Catatan: yang di-hash hanya `generator.py`; `retriever.py`, `chunker.py`, dan `ingest.py` tidak
dikunci dengan hash, hanya dengan kebiasaan "tidak disentuh".

Struktur yang diusulkan (belum dibuat):

```
src/
  generator.py            # Versi 1 -- TIDAK disentuh; uji kunci tetap lolos
  retriever.py            # dipakai bersama, tidak diubah
  v2/
    __init__.py
    pipeline.py           # orkestrasi Versi 2 (fungsi biasa); memanggil retriever yang sama
    extract.py            # ekstraksi klaim / pencarian per potongan (2.1)
    prompts.py            # prompt Versi 2 (salinan prompt v1 + perubahan); di-hash sendiri
    answer.py             # jawaban Versi 2: bidang yang sama dengan Answer v1 + catatan per langkah
  evaluation/
    testset_eval.py       # Versi 1 -- tidak diubah
    v2_eval.py            # menjalankan V1 dan V2 pada set uji v2; satu berkas hasil per kondisi
```

Ketentuan:

1. Versi 2 **mengimpor** dari Versi 1 (retriever, lapisan `llm/`, penyaringan URL), tidak pernah
   sebaliknya, dan tidak mengubah berkas Versi 1.
2. Pengaman Versi 1 dipertahankan apa adanya di Versi 2: status dari metadata, rujukan hanya dari
   metadata, `article_id` hanya dari kandidat, URL keluaran LLM dibuang (Aturan Wajib #3, #4).
3. Versi 2 punya sidik jari sendiri (hash `src/v2/` + prompt) yang dikunci sebelum evaluasi, dengan
   uji kunci terpisah.
4. Demo memilih versi lewat setelan; bawaannya tetap Versi 1 sampai Versi 2 terukur.
5. **Yang perlu diputuskan:** apakah `retriever.py` ikut dikunci dengan hash sebelum evaluasi
   Versi 2, supaya "retrieval yang sama" dijamin oleh uji, bukan oleh kebiasaan.

---

## 4. Hipotesis yang dipra-registrasi (usulan)

Bentuknya mengikuti H1 dan H3 Versi 1 (`v1.meta.json`, `ambang`): ukuran dan kriteria gugur
ditetapkan sebelum data dilihat. "Komponen tidak memberi perbaikan" adalah hasil yang sah dan
dilaporkan apa adanya. Aturan tafsir mengikuti ablasi Versi 1: selisih dianggap bermakna hanya
bila McNemar eksak p < 0,05 **dan** selisih bersih >= 3 butir. Angka `n` di bawah bergantung pada
ukuran set uji (bagian 6.3); ambang final ditulis ke `v2.meta.json` sebelum butir dibuat.

| Kode | Hipotesis | Ukuran | Terdukung | Gugur |
| --- | --- | --- | --- | --- |
| V2-H1 | Pada pesan panjang ASLI, penanganan pesan panjang menaikkan Recall@3 butir positif | Recall@3 Versi 1 vs Versi 2 pada strata pesan panjang, berpasangan | McNemar p < 0,05 dan selisih bersih >= 6 butir | Selisih bersih <= 2 butir, atau pesan panjang asli ternyata sudah terjangkau Versi 1 (masalahnya tidak ada pada pesan nyata) |
| V2-H2 | Penanganan pesan panjang tidak merusak klaim pendek | Recall@3 dan akurasi butir pendek, berpasangan | Kemunduran bersih <= 1 butir | Kemunduran bersih >= 3 butir |
| V2-H3 | Ekstraksi oleh LLM lebih baik daripada pencarian per potongan tanpa LLM | Recall@3 strata pesan panjang, dua kondisi | LLM unggul bersih >= 3 butir, p < 0,05 | Selisih <= 2 butir -> **pilih yang tanpa LLM** |
| V2-H4 | Perubahan penilaian klaim (2.2) menurunkan kesalahan tanpa memindahkannya | Kecocokan palsu dan penolakan palsu non-batas, dilaporkan terpisah | Kesalahan total turun bersih >= 3 butir, p < 0,05, dan tidak ada jenis kesalahan yang naik >= 3 butir | Tidak terdukung bila selisih <= 2 butir. **Perkiraan jujur: kemungkinan besar tidak terdukung** (bagian 6.3) |
| V2-H5 | Perubahan penilaian klaim menaikkan kestabilan antar-run | Jumlah butir non-batas yang keputusannya bulat di 3 run (Versi 1: 45/50) | Naik bersih >= 6 butir | Selisih <= 2 butir |
| V2-H6 | Rujukan yang ditampilkan bersih | Jumlah rujukan pada jawaban "ditemukan" yang melanggar kebijakan penyaringan atau termasuk sumber klaim | 0 pada kedua versi | >= 1 (dilaporkan per artikel; ini pemeriksaan sifat, bukan uji statistik) |
| V2-H7 | Versi 2 tidak lebih lambat/mahal secara tak wajar | Panggilan LLM dan latensi per kueri | Dilaporkan; tanpa ambang | -- |

H4 (Gemma sebagai juri) dari Versi 1 tidak dibawa; lihat 5.5.

---

## 5. Rencana evaluasi

### 5.1 Set uji, snapshot, dan parameter

Versi 1 dan Versi 2 dijalankan pada **set uji yang sama, snapshot indeks yang sama, dan parameter
retrieval yang sama**. Tiga hal yang perlu ditetapkan:

- **Set uji:** set uji v2 yang baru (bagian 6). Set uji v1 **tidak dapat menjadi bukti mutu Versi
  2**: komponen Versi 2 dirancang setelah melihat kesalahan pada set itu, dan aturan pembekuannya
  sendiri menyatakan perubahan sesudah pembekuan menuntut set uji baru. Set uji v1 tetap berguna
  sebagai pemeriksaan regresi pada `archive/v1`.
- **Snapshot:** *usulan* -- membekukan salinan indeks produksi pada satu tanggal sebagai
  `archive/v2_snapshot/` (daftar id + sidik jari isi, seperti `archive/v1`), setelah antrean 16
  artikel digabung atau diputuskan tidak digabung. Alasannya: (i) set uji v2 harus diverifikasi
  terhadap satu snapshot tertentu (bagian 6); (ii) indeks produksi terus bertambah lewat pembaruan
  berkala, jadi tidak bisa dijadikan acuan; (iii) arsip 150 artikel terlalu kecil dan tidak memuat
  kasus yang ingin diuji (mis. artikel tanpa Narasi, label baru). Arsip `archive/v1` tetap dipakai
  untuk mereproduksi baseline Versi 1 lama.
- **Parameter retrieval:** `ef_search` sekarang berbeda antara produksi (2000) dan arsip (100)
  (`v1_temuan_untuk_v2.md` bagian 10). *Usulan:* snapshot v2 dibekukan dengan `ef_search` 2000, dan
  **kedua versi** dijalankan pada snapshot itu dengan nilai tersebut; `evaluation.retriever_exactness`
  dijalankan pada kueri set uji v2 sebelum evaluasi, dan Recall dilaporkan dari retriever yang
  benar-benar dipakai serta dari pencarian eksak. `top_k` = 3, `CHUNK_FETCH` = 30, agregasi
  maksimum, model embedding dan `MAX_SEQ_LENGTH` tidak diubah.
- **Konsekuensi untuk Aturan Wajib #6.** Aturan itu mewajibkan pembandingan dengan *baseline
  Versi 1* lewat `archive/v1`. Rencana ini membandingkan *sistem* Versi 1 dengan *sistem* Versi 2
  pada snapshot baru, sehingga angka 48/50 tidak dipakai sebagai pembanding langsung. Itu perlu
  dinyatakan eksplisit dalam aturan (pertanyaan 5).

### 5.2 Metrik retrieval dipisah dari metrik jawaban

- *Retrieval (tanpa LLM, kecuali ekstraksi):* Recall@1/3/5 per tipe butir, peringkat artikel
  sasaran, dan untuk pesan panjang keterbacaan klaim (utuh/terpotong) seperti eksperimen 4.
- *Jawaban:* keputusan modus 3 run (verdict + `article_id`); kecocokan palsu, penolakan palsu,
  artikel salah, masing-masing dengan Wilson 95%, terpisah untuk batas dan non-batas; kesepakatan
  antar-run; pelanggaran format; URL di luar metadata. Sama dengan pra-registrasi Versi 1
  (`v1.meta.json`, `evaluasi`).
- Butir tidak disaring berdasarkan hasil sistem; kegagalan retrieval dan kegagalan jawaban
  dilaporkan sebagai dua hal.

### 5.3 Ablasi per komponen

Agar perbaikan bisa diatribusikan, tiap komponen dinyalakan sendiri:

| Kondisi | Penanganan pesan panjang | Perubahan penilaian klaim | Gaya bahasa |
| --- | --- | --- | --- |
| K0 = Versi 1 (terkunci) | -- | -- | -- |
| K1 | pencarian per potongan (tanpa LLM) | -- | -- |
| K2 | ekstraksi LLM | -- | -- |
| K3 | -- | ya | -- |
| K4 = Versi 2 lengkap | pilihan terbaik K1/K2 | ya | (bila masuk cakupan) |

K1 vs K2 pada retrieval saja dapat diputuskan lebih dulu tanpa menjalankan generator. Kondisi yang
tidak lolos tahap retrieval tidak dilanjutkan ke tahap jawaban (menghemat kuota; bagian 7).

### 5.4 Kebersihan rujukan (belum pernah diukur)

Berkas hasil menyimpan daftar rujukan tiap jawaban "ditemukan". Per jawaban dihitung: rujukan yang
melanggar `links.blocked_reason` (kebijakan terkini), rujukan yang termasuk `claim_sources` artikel
itu (termasuk baris "Sumber:"), jawaban tanpa rujukan, dan rujukan yang lolos hanya karena daftar
tepercaya atau `.go.id`. Diukur untuk kedua versi pada snapshot yang sama. Ini pemeriksaan
deterministik; tidak butuh LLM.

### 5.5 Juri (RAGAS + Gemma): tidak diperlukan untuk metrik utama

- Metrik utama (verdict dan `article_id` terhadap label emas manusia) bersifat objektif; juri LLM
  tidak menambah apa pun di sana.
- Juri hanya relevan untuk **mutu klarifikasi** (M5): kesetiaan pada Kesimpulan dan keterbacaan.
- Status H4 Versi 1: Gemma belum pernah diuji sebagai juri; yang diuji hanya format JSON (6/6
  berhasil), dengan latensi **31-52 detik per panggilan** (CLAUDE.md, "Hipotesis dan status").
  RAGAS belum dipasang; perkiraan 6-7 panggilan per sampel di CLAUDE.md adalah perkiraan yang tidak
  pernah diverifikasi.
- Hitungan kasar dengan angka itu: 150 butir x 3 run x 2 versi = 900 sampel; x 6-7 panggilan x
  31-52 detik = **46-91 jam** berurutan. Selain itu Gemma dan Gemini berasal dari pengembang yang
  sama (koreksi independensi 2026-09-22), jadi juri itu tidak independen.
- **Usulan:** tidak memakai juri LLM. Bila M5 masuk cakupan, mutu klarifikasi dinilai pemilik
  proyek pada sampel kecil dengan urutan diacak dan versi disamarkan, dan dilaporkan sebagai
  penilaian satu orang. Kesetiaan diperiksa dengan cara yang sudah ada (klarifikasi diganti
  Kesimpulan asli bila gagal; jumlahnya dilaporkan). Bila pemilik proyek tetap menginginkan juri,
  itu menambah kendala waktu di atas (pertanyaan 6).

---

## 6. Persyaratan set uji v2

Dikumpulkan dari catatan yang sudah ada (`v1_temuan_untuk_v2.md` bagian 4, 5.2, 8, 9;
`v1.meta.json`; caveat laporan analisis; CLAUDE.md Aturan Wajib #5).

### 6.1 Persyaratan

1. **Diberi versi bersama snapshot basis data.** Hasil hanya sah pada snapshot itu (daftar id +
   sidik jari isi). Dasar: enam butir negatif v1 gugur pada indeks yang lebih besar (`v1-021`,
   `v1-022`, `v1-029`, `v1-043`, `v1-049`, `v1-050`; `v1.meta.json`).
2. **Setiap butir negatif diverifikasi terhadap snapshot**, dengan top-3 retrieval, bukan sekadar
   memeriksa keberadaan artikel. Butir dari artikel arsip tidak dipakai bila artikelnya berpotensi
   masuk basis data.
3. **Butir dari situs cek fakta lain diperiksa ulang terhadap snapshot** (bukti: `v1-050`,
   Liputan6 17/9 -> TurnBackHoax 21/9).
4. **Label final ditetapkan manusia**; pemakaian draf AI pada tahap mana pun dicatat (Aturan Wajib
   #5). Pedoman anotasi v1.0 dipakai lagi atau direvisi sebelum butir dibuat, lalu dikunci.
5. **Pengendalian confound sumber.** Di v1, `angka_waktu_beda` 100% buatan model dan negatif mudah
   0% buatan model (caveat 3). Di v2 tiap sel tipe x subtipe sebaiknya memuat lebih dari satu
   sumber, atau perbandingannya tidak dibuat.
6. **Pesan panjang yang ASLI**, dengan posisi klaim beragam (awal, tengah, akhir), bukan pengganggu
   sintetis. **Datanya belum ada**: belum ada sumber pesan berantai asli yang dikumpulkan, dan
   kepatuhan pengumpulannya (izin situs, data pribadi) harus diperiksa seperti pada v1.
7. **Ketergantungan antar-butir dikurangi.** Di v1, 44% butir berbagi artikel jangkar (caveat 1).
8. **Contoh yang sudah dicatat:** pasangan `v1-046`/30652 sebagai negatif sulit (`v1.meta.json`,
   `keputusan_v1-046_2026-10-03`); artikel tanpa Narasi (29670); label baru (SATIR, KOMEDI, BELUM
   TERBUKTI).
9. **Butir tidak boleh bocor dari set uji v1 maupun set pengembangan**, karena keduanya sudah
   dipakai merancang Versi 2.

### 6.2 Yang tidak dapat ditetapkan dari data yang ada

- Berapa proporsi pesan panjang yang wajar: tidak ada data pemakaian nyata.
- Apakah satu anotator cukup: v1 hanya mengukur konsistensi dalam-anotator, dan hasil pengukuran
  itu tidak ditemukan tercatat di berkas yang dibaca untuk dokumen ini.

### 6.3 Ukuran sampel

Dihitung dengan interval Wilson 95% (z = 1,96) dan, untuk perbandingan berpasangan, McNemar eksak.

**(a) Akurasi keseluruhan tidak dapat dipakai untuk menunjukkan perbaikan.** Baseline 48/50
(96%). Agar interval Wilson dua kondisi tidak tumpang tindih:

| Perbandingan | Butir per kondisi |
| --- | --- |
| 96% vs 99% | >= 413 |
| 90% vs 96% | >= 276 |
| 86% vs 95% | >= 147 |
| 80% vs 95% | >= 68 |
| 10% vs 80% (pesan panjang, bila efeknya sebesar pada data sintetis) | >= 10 |

Empat ratus butir berlabel manusia di luar jangkauan satu anotator (v1: 54 butir). Jadi **klaim
"Versi 2 lebih akurat daripada Versi 1 pada klaim pendek" tidak akan dapat dibuktikan** dengan set
uji yang realistis; yang dapat ditunjukkan hanyalah tidak adanya kemunduran besar.

**(b) Perbandingan berpasangan lebih peka, tetapi tetap terbatas.** Kedua versi dijalankan pada
butir yang sama. McNemar eksak dua sisi memberi p < 0,05 hanya bila ada >= 6 butir yang berubah
searah tanpa satu pun kemunduran (6 vs 0: p = 0,031; 5 vs 0: p = 0,063; 8 vs 1: p = 0,039). Jumlah
butir agar peluang mengamati >= 6 perbaikan mencapai 80%:

| Laju perbaikan sejati | Butir yang dibutuhkan |
| --- | --- |
| 4% | 197 |
| 6% | 131 |
| 8% | 98 |
| 10% | 78 |

Kesalahan modus Versi 1 hanya 2/50 = 4%. Bahkan bila Versi 2 memperbaiki **semuanya** tanpa
kemunduran, dibutuhkan sekitar 197 butir non-batas. Untuk kestabilan (5 dari 50 butir non-batas
tidak bulat = 10%), memperbaiki semuanya membutuhkan sekitar 78 butir; memperbaiki separuhnya
sekitar 160.

**(c) Menunjukkan "tidak ada kejadian".** Batas atas Wilson 95% bila 0 kejadian: 16,1% (n = 20),
11,4% (30), 7,1% (50), 3,7% (100), 2,5% (150). Untuk menyatakan kecocokan palsu Versi 2 di bawah
~4% dibutuhkan >= 100 butir negatif tanpa satu pun kecocokan palsu.

**(d) Usulan ukuran** (keputusan pemilik proyek; pertanyaan 7):

| Strata | Butir | Yang bisa ditunjukkan |
| --- | --- | --- |
| Positif, pesan panjang asli | 30 | V2-H1 bila efeknya besar (>= 6 butir bersih); batas bawah Wilson bila semua benar 0,886 |
| Positif, klaim pendek | 30 | V2-H2 (tidak ada kemunduran besar) |
| Negatif sulit | 60 | batas atas kecocokan palsu ~6% bila 0 kejadian |
| Negatif mudah | 20 | -- |
| Batas | dilaporkan terpisah | -- |
| **Total non-batas** | **140** | perbaikan berpasangan hanya terdeteksi bila laju sejatinya >= ~6% |

Dengan 140 butir, V2-H4 (kesalahan turun) **hampir pasti tidak dapat didukung** kecuali kesalahan
Versi 1 pada set baru ternyata jauh lebih banyak daripada pada v1. Itu sebabnya rancangan ini
tidak menjadikan grader komponen wajib. Sebagai pembanding beban: 140 butir = 2,6 kali set uji v1.

---

## 7. Kendala nyata

### 7.1 Kuota LLM

Angka tercatat (`src/llm/limits.py`, diambil dari AI Studio 2026-09-21): `gemini-3.5-flash-lite`
RPM 15, TPM 250.000, **RPD 500**. Angka tier gratis **dapat berubah tanpa pemberitahuan** dan
"not guaranteed"; `gemini-3.8-flash` pernah dihentikan karena ketidakstabilan layanan (CLAUDE.md).
Setiap permintaan yang dikirim dihitung, termasuk yang ditolak. Demo berbagi kuota yang sama.

Versi 1 memakai 1 panggilan per kueri (evaluasi v1: 162 panggilan untuk 162 baris, 0 percobaan
ulang; rata-rata 2.516 token masuk, latensi rata-rata 10-18 detik per run;
`v1_analysis_report.txt` B.4). Panggilan per kueri untuk tiap kondisi (bagian 5.3):

| Kondisi | Panggilan per kueri | Catatan |
| --- | --- | --- |
| K0 Versi 1 | 1 | |
| K1 pencarian per potongan | 1 | tanpa LLM tambahan |
| K2 ekstraksi LLM | 1 + 1 hanya untuk pesan panjang | |
| K3 perubahan prompt | 1 | 3 bila pemungutan suara; 2-4 bila node grader terpisah (1 atau 3 kandidat per panggilan) |
| K4 lengkap | 1-2 | sampai ~4 dengan grader per kandidat (rata-rata ~4,2 bila 30 dari 150 butir pesan panjang) |

Evaluasi 3 run pada 140 butir non-batas + butir batas (dibulatkan 150 butir, 30 di antaranya pesan
panjang; 450 panggilan per kondisi satu-panggilan):

| Skenario | Panggilan | Hari pada RPD 500 (tanpa demo, tanpa percobaan ulang) |
| --- | --- | --- |
| Hanya K0 dan K4, tanpa grader (1 dan ~1,2 panggilan) | ~990 | 2 |
| K0 + K1 + K2 + K3 + K4, tanpa grader | ~2.400 | 5 |
| Sama, dengan node grader 1 panggilan (K3 = 2, K4 = ~2,2) | ~3.300 | 7 |
| Sama, dengan grader per kandidat (K3 = 4, K4 = ~4,2) | ~5.100 | 11 |

Menurut RPM 15, 500 panggilan butuh >= 34 menit; menurut latensi terukur (10-18 detik, berurutan)
sekitar 1,4-2,5 jam per hari. TPM bukan pembatas (2.516 token x 15 = ~38.000 per menit). Menekan
biaya: K1 vs K2 diputuskan pada tahap retrieval saja; kondisi yang gugur tidak dijalankan
generatornya; evaluasi dapat dilanjutkan antar-hari (`results_store` sudah mendukung).

**Bagi pengguna demo:** tiap komponen LLM tambahan mengurangi jumlah pemeriksaan per hari (500
dibagi panggilan per kueri) dan menambah latensi per pemeriksaan.

### 7.2 Memori

Laptop pengembangan: 15,7 GB RAM, memori bebas teramati 2,3-3,4 GB; memuat model embedding menekan
memori tersedia sampai ~0,9-1,0 GB (`data/pending_2026-10-03.log`). Proses pernah dihentikan
sistem karena memori rendah: ingest 2026-09-27 dan ablasi 2026-10-03 tercatat di CLAUDE.md (pemilik
proyek menyebut tiga kejadian). Konsekuensi untuk Versi 2: tidak ada model lokal tambahan (mis.
reranker atau model embedding kedua) tanpa pengukuran memori lebih dulu; satu proses pemuat model
pada satu waktu; evaluasi panjang memakai pemantau memori dan dapat dilanjutkan.

### 7.3 Lain-lain

Satu anotator; satu sumber data; `generator.py` terkunci; pembaruan berkala terus mengubah indeks
produksi (karena itu perlu snapshot); permintaan API key Yudistira belum dijawab.

---

## 8. Di luar cakupan

| Hal | Alasan |
| --- | --- |
| Penulis ulang kueri saat retrieval gagal (putaran "cari lagi") | Tidak ada bukti masalah: empat kegagalan Recall@3 semuanya butir negatif; positif 20/20 di semua indeks |
| Penilaian kredibilitas dokumen hasil retrieval | Satu sumber data; tidak ada yang dinilai |
| Penilai kredibilitas rujukan per-URL oleh LLM | Tidak ada bukti solusi; LLM tidak dapat membuka tautan; daftar eksplisit lebih mudah diaudit |
| Mengganti top-k atau agregasi | Tidak dapat dibedakan dari kebetulan pada tiga indeks |
| Model embedding lain, batas token indeks lain, skema chunking lain | Butuh pembangunan ulang indeks dan memori; tidak ada temuan yang menuntutnya. Pengecualian yang masih terbuka: menghapus Penjelasan dari indeks (pertanyaan 8) |
| Juri LLM (RAGAS + Gemma) | Lihat 5.5 |
| Verdict ketiga "artikel terkait" | Belum diputuskan; bergantung pada M3 (pertanyaan 3) |
| Mengubah `archive/v1`, `v1.jsonl`, `generator.py` | Baseline |
| Integrasi API Yudistira, penjadwalan ingest | Tahap lain |

---

## 9. Pertanyaan terbuka untuk pemilik proyek

Harus diputuskan sebelum ada kode ditulis.

1. **Cakupan Versi 2.** Menurut bukti, satu-satunya masalah dengan bukti kuat yang belum ditangani
   adalah pesan panjang (M1), dan itu pun baru terbukti pada data sintetis. Apakah Versi 2
   dipersempit menjadi "penanganan pesan panjang + pengukuran kebersihan rujukan", atau komponen
   lain tetap dimasukkan sebagai eksperimen yang hasilnya mungkin "tidak ada perbaikan"?
2. **Grader.** Dimasukkan atau tidak? Bila ya, dalam bentuk apa: perubahan prompt (satu
   panggilan), pemungutan suara, atau node terpisah? Rancangan ini tidak merekomendasikannya
   sebagai komponen wajib.
3. **"Mungkin terkait" dan verdict ketiga.** Tetap mati, atau dicoba lewat keluaran tambahan
   generator Versi 2 ("topik sama, klaim berbeda")? Bila dicoba, butir set uji v2 perlu label untuk
   kategori itu, dan pedoman anotasi harus direvisi.
4. **Kerangka.** Pipeline Python biasa (usulan), atau LangGraph demi nilai portofolio walau
   alurnya tidak membutuhkannya?
5. **Snapshot dan Aturan Wajib #6.** Setujukah membekukan snapshot baru (`archive/v2_snapshot/`,
   `ef_search` 2000) sebagai tempat Versi 1 dan Versi 2 dibandingkan, dan menyesuaikan bunyi
   Aturan Wajib #6? Kapan snapshot diambil, dan apakah antrean 16 artikel masuk?
6. **Juri.** Setujukah tanpa juri LLM, dengan penilaian manusia pada sampel kecil hanya bila M5
   masuk cakupan?
7. **Ukuran set uji v2.** 140 butir non-batas (usulan) sanggup dikerjakan satu anotator? Bila
   tidak, strata mana yang dikurangi -- dengan konsekuensi di bagian 6.3?
8. **Pesan panjang asli.** Dari mana sumbernya, dan bagaimana kepatuhan serta data pribadinya
   diperiksa? Tanpa ini V2-H1 tidak dapat diuji dan M1 tetap hanya terbukti pada data sintetis.
9. **Mutu klarifikasi (M5).** Masuk cakupan? Mengubah prompt berarti satu kondisi ablasi lagi.
10. **Menghapus Penjelasan dari indeks.** Agenda lama (`v1_temuan_untuk_v2.md` bagian 5.2):
    Penjelasan tidak menyumbang recall, tetapi pengaruhnya pada jawaban belum diuji dan menuntut
    indeks kedua. Dimasukkan sebagai kondisi ablasi atau ditunda?
11. **`retriever.py` dikunci dengan hash** sebelum evaluasi Versi 2?
12. **Pedoman anotasi.** Dipakai apa adanya (v1.0) atau direvisi dulu (mis. untuk kategori
    "topik sama, klaim berbeda" dan pesan panjang)?

---

## Sumber

| Berkas | Dipakai untuk |
| --- | --- |
| `testset/v1_temuan_untuk_v2.md` | temuan per bagian (1, 2, 3, 4, 5, 6, 6.1, 8, 9, 10, 11) |
| `testset/v1_analysis_report.txt` | akurasi, jenis kesalahan, kesepakatan antar-run, caveat, latensi dan token |
| `testset/v1.meta.json` | ambang H1/H3, rancangan evaluasi, sidik jari generator, batas tafsir H1, butir negatif yang berubah status, keputusan `v1-046` |
| `testset/v1.jsonl` | tipe dan label empat butir gagal Recall@3; komposisi sumber |
| `data/testset_v1_eval_gemini-3.5-flash-lite.jsonl` | akurasi per run (46, 47, 48 dari 50); 1 panggilan per butir |
| `testset/retrieval_ablation_report.txt`, `_prod922_report.txt`, `_prod1532_report.txt` | Recall@k per indeks; pesan panjang (2/20, 0/20, 0/20; 19/20) |
| `testset/v1_perbandingan_indeks_1532.json`, `testset/devset_retrieval_1532.json` | recall positif pada indeks 1.532; skor set pengembangan |
| `config/related_threshold.json` | dasar keputusan mematikan "Mungkin terkait" |
| `src/llm/limits.py` | kuota (RPM 15, TPM 250.000, RPD 500; 2026-09-21) |
| `src/generator.py`, `tests/test_testset_locks.py` | apa yang sudah dilakukan generator; apa yang terkunci |
| `CLAUDE.md` | keterbatasan, temuan Aturan Wajib #1, latensi Gemma, catatan memori |

Perhitungan ukuran sampel (bagian 6.3) memakai rumus interval Wilson dan McNemar eksak dua sisi;
angka-angkanya dihitung saat dokumen ini disusun dan tidak tersimpan sebagai berkas hasil.
