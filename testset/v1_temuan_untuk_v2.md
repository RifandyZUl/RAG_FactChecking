# Temuan Versi 1 untuk rancangan Versi 2

Disusun 2026-09-23 dari hasil evaluasi set uji v1 (3 run x 54 butir, `testset/v1_analysis.json`
dan `testset/v1_analysis_report.txt`). Ini daftar **temuan terukur**, bukan rancangan Versi 2 --
komponen yang disebut di tiap bagian hanya menandai target, implementasinya belum dirancang.

Latar (lihat CLAUDE.md, "Versi 2 — Corrective RAG"): komponen kandidat Versi 2 adalah (a) node
**penulis ulang kueri** (query rewriter), (b) node **penilai relevansi dokumen** (grader), dan
(c) **penilaian kredibilitas sumber**. Pemetaan temuan ke komponen yang terbaru ada di
**bagian 7**.

> **KETERBATASAN UTAMA VERSI 1 (terukur 2026-09-25, bagian 5.2):** sistem hanya andal untuk
> klaim di bawah **512 token pada sisi kueri**. Pada pesan panjang, klaim terdorong keluar dari
> jendela embedding sehingga tidak ikut dicari: Recall@3 **19/20** pada ~1.500 dan ~3.000
> karakter, runtuh ke **2/20** pada ~5.000 karakter (klaim di luar 512 token pada 18/20). Kondisi
> pembanding klaim-di-awal-pesan tetap **19/20** pada ~5.000 karakter. Teks pengganggu sintetis,
> hasil indikatif.

---

## 1. Kegagalan retrieval (4 butir)

Artikel yang seharusnya terjangkau (`expected_retrieval_article`) tidak masuk top-3 hasil
retrieval. Peringkat sebenarnya dicari dengan retrieval top_k=20 (kueri lokal, bukan panggilan
API) pada indeks yang sama.

| Butir | Subtipe | Artikel diharapkan | Top-3 aktual (skor) | Peringkat sebenarnya | Skor sebenarnya | Selisih skor ke posisi #3 |
|---|---|---|---|---|---|---|
| `v1-024` | pola_sama_entitas_beda | 36576 | 36043(0,584), 36042(0,575), **36737(0,564)** | **#4** (nyaris) | 0,556 | **0,008** |
| `v1-027` | pola_sama_entitas_beda | 36191 | 36613(0,614), 36576(0,598), **36571(0,589)** | **#4** (nyaris) | 0,568 | 0,020 |
| `v1-033` | entitas_sama_klaim_beda | 36191 | 36596(0,460), 36380(0,447), 36476(0,424) | #6 (jauh) | 0,417 | 0,027 (ke #3) |
| `v1-022` | pola_sama_entitas_beda | 36648 | 36672(0,632), 36612(0,610), 36054(0,590) | #19 (jauh) | 0,531 | 0,059 (ke #3) |

**Catatan ketepatan angka:** dua kasus "nyaris masuk" (peringkat 4) punya selisih skor yang
BERBEDA -- `v1-024` selisihnya ~0,008 (sangat tipis), `v1-027` ~0,020 (masih dekat tapi tidak
setipis `v1-024`). Keduanya tetap dikelompokkan "nyaris" karena sama-sama peringkat 4, tapi
besar selisihnya tidak identik.

Ketiga butir `v1-022`/`v1-024`/`v1-027` (subtipe pola_sama_entitas_beda) berakibat pada batas
tafsir H1 -- lihat `testset/v1.meta.json.hasil_evaluasi_v1_2026-09-23.batas_tafsir_H1_recall_2026-09-23`:
generator tidak pernah benar-benar diuji membedakan klaim dari artikel tetangga pada ketiganya,
karena artikelnya tidak sampai menjadi kandidat.

**Target Versi 2: node penulis ulang kueri (query rewriter).** Dua kasus nyaris (peringkat 4)
adalah kandidat paling langsung untuk perbaikan lewat penulisan ulang kueri -- pergeseran skor
kecil (~0,008–0,02) masuk akal diatasi dengan reformulasi kueri yang lebih dekat dengan bahasa
artikel. Dua kasus jauh (peringkat 6 dan 19) kemungkinan butuh lebih dari sekadar penulisan ulang
kueri satu langkah; implementasinya (mis. berapa kali menulis ulang, kapan menyerah) adalah
keputusan rancangan Versi 2, tidak ditentukan di sini.

---

## 2. Kegagalan penilaian generator (2 kesalahan + 6 ketidakbulatan antar-run)

Pada kedua kesalahan (`v1-020`, `v1-036`) dan keenam butir yang keputusannya tidak bulat antar-
run (`v1-006`, `v1-010`, `v1-036`, `v1-039`, `v1-040`, `v1-053`; `v1-036` muncul di kedua daftar),
**artikel yang benar SELALU tersedia di top-3** (recall_at_3=True untuk ketujuh butir unik).
Kegagalan/variasi ini murni penilaian LLM terhadap kandidat yang sudah benar, bukan retrieval.

| Butir | Jenis | Keterangan singkat |
|---|---|---|
| `v1-020` | kesalahan (penolakan palsu) | Klaim positif dijawab tidak ditemukan padahal artikel tersedia di top-3 |
| `v1-036` | kesalahan (kecocokan palsu) + tidak bulat | Magnitudo gempa 8,2 vs 7,7 asli -- 2 dari 3 run menganggap sama |
| `v1-006` | tidak bulat, modus benar | 1 dari 3 run keliru menjawab "ditemukan" |
| `v1-010` | tidak bulat, modus benar | 1 dari 3 run keliru menjawab "tidak ditemukan" |
| `v1-039` | tidak bulat, modus benar | 1 dari 3 run keliru menjawab "ditemukan" (HUT ke-80 vs ke-81 asli) |
| `v1-040` | tidak bulat, modus benar | 1 dari 3 run keliru menjawab "ditemukan" ("tiap tahun" vs "tiap bulan" asli) |
| `v1-053` | kesalahan batas (kecocokan palsu, dilaporkan terpisah) | 2 dari 3 run menganggap klaim peringkat kemiskinan sama dengan artikel |

**Target Versi 2: node penilai relevansi dokumen (grader).** Karena artikel yang benar selalu
tersedia sebagai kandidat, masalahnya bukan menemukan dokumen -- melainkan menilai apakah
dokumen itu benar-benar menjawab klaim yang sama. Node grader terpisah (menilai relevansi/
kesamaan klaim secara eksplisit, sebelum menyusun jawaban akhir) menargetkan persis pola
kegagalan ini. Ketidakbulatan antar-run (6 dari 7 kasus di atas) juga mengindikasikan keputusan
klaim-sama/tidak berada di titik yang sensitif terhadap variasi acak LLM -- relevan untuk
menimbang apakah grader perlu memakai pemungutan suara atau penalaran terstruktur tambahan,
tanpa merancang mekanismenya di sini.

---

## 3. Tidak tercakup oleh temuan sesi ini

**Penilaian kredibilitas sumber** -- tidak ada temuan dari evaluasi set uji v1 yang secara
langsung mengindikasikan kebutuhan ini (set uji v1 tidak menguji kredibilitas rujukan). Kebutuhan
komponen ini berasal dari keterbatasan yang sudah dicatat sebelumnya (lihat CLAUDE.md,
"Keterbatasan yang Diketahui" -- penyaringan `references` berbasis domain, bukan mengevaluasi
kredibilitas akun/sumber individual), bukan dari temuan analisis kuantitatif di atas.

---

## 4. Temuan dari demo lokal (2026-09-25)

Bukan hasil evaluasi set uji; diamati pemilik proyek saat mencoba demo (`src/app.py`) di
browser, lalu dicatat di sini sebagai bahan Versi 2. Tidak ada perubahan prompt atau generator
berdasarkan temuan ini (generator terkunci sejak tag `testset-v1`).

### 4.1 Klarifikasi padat dan sulit diikuti pembaca awam

Teks `klarifikasi` keluaran generator cenderung memadatkan beberapa hal ke satu kalimat panjang.
Contoh nyata dari artikel **36730** ("Ojol Dilarang Beli Pertalite"): satu kalimat memuat
sekaligus **wacana** (pernyataan yang sempat beredar), **ralat pejabat**, dan **kesimpulan**.
Dua keluaran tercatat untuk artikel yang sama (set pengembangan, kueri "katanya ojol nggak boleh
isi pertalite lagi ya?"):

- `data/generation_repeat_gemini-3.5-flash-lite.jsonl`: "Meskipun pernyataan tersebut sempat
  diungkapkan, pejabat berwenang kemudian meralatnya sehingga informasi mengenai larangan ojol
  membeli Pertalite merupakan hal yang menyesatkan."
- `data/generation_eval_gemini-3.5-flash-lite.jsonl`: "Meskipun sempat ada pernyataan terkait,
  pihak berwenang menegaskan bahwa pengemudi ojek online dikecualikan dari kebijakan pembatasan
  Pertalite, sehingga klaim larangan tersebut tidak benar."

Keduanya juga merujuk "pernyataan tersebut"/"pernyataan terkait" tanpa menyebut siapa yang
menyatakan apa, sehingga pembaca awam tidak tahu wacana mana yang diralat.

**Contoh ketiga, dari pengujian demo oleh pemilik proyek (artikel 36730, tidak tersimpan di berkas
hasil):** "Pihak berwenang memang pernah menyatakan wacana tersebut, namun belakangan telah
meralatnya." Frasa "namun belakangan telah meralatnya" terasa kaku, dan subjek-objeknya tidak
jelas bagi pembaca awam: tidak terbaca siapa yang meralat dan apa yang diralat. Bahasa yang lebih
wajar misalnya "tapi pernyataan itu kemudian diluruskan kembali".

**Variasi antar-panggilan.** Tiga keluaran di atas berasal dari panggilan berbeda dengan prompt
yang sama untuk artikel yang sama, dan mutu penyajiannya berbeda-beda (dua menyebut
"menyesatkan"/"tidak benar" sebagai kesimpulan, satu tidak). Ini konsisten dengan temuan 6 dari
54 butir set uji yang keputusannya tidak bulat antar-run (bagian 2): keluaran generator
bervariasi antar-panggilan, bukan hanya pada keputusan tetapi juga pada gaya bahasa. Karena itu
perbaikan gaya bahasa di Versi 2 **wajib dievaluasi pada beberapa kali pemanggilan per butir,
bukan satu kali**, misalnya dengan menilai sebaran mutu dari 3 run seperti evaluasi v1.

**Sasaran Versi 2 (gaya bahasa):** tambahkan instruksi gaya bahasa pada prompt agar klarifikasi
memakai **kalimat aktif, subjek yang jelas, dan diksi sehari-hari**. Pengaruhnya pada akurasi
**wajib diukur ulang**, karena mengubah prompt membatalkan keabsahan baseline Versi 1 (sidik jari
prompt dikunci di `v1.meta.json.sidik_jari_generator_v1`); pengukurannya pada set uji baru, dengan
indeks arsip Versi 1 (`archive/v1`) agar perbedaan hasil murni karena prompt, bukan data.

- **Target:** instruksi bidang `klarifikasi` pada prompt Versi 2 (mis. kalimat pendek,
  urutan fakta -> konteks, subjek eksplisit). Perubahan prompt wajib diukur pada set uji baru,
  bukan set uji v1 yang beku.
- **Yang sudah dilakukan di Versi 1 (hanya penyajian, teks tidak diubah):** kolom baca
  dipersempit (560 px), jarak baris 1,75, dan klarifikasi dipisah jarak dari blok status serta
  dipisah garis dari rujukan.

### 4.2 Klaim panjang melebihi batas token embedding (dari kode + tokenizer; frekuensi di pemakaian nyata belum diukur)

Batas masukan demo sempat dinaikkan ke 5.000 karakter (pesan berantai nyata sering panjang) tanpa
pengukuran; setelah ablasi (bagian 5.2) diturunkan ke 1.500 karakter. Retrieval
meng-embed klaim dengan batas `MAX_SEQ_LENGTH` = 512 token, sehingga **bagian klaim di atas
~512 token tidak ikut dicari** (LLM tetap membaca klaim utuh). Terukur dengan tokenizer bge-m3:
satu contoh teks 5.000 karakter berbahasa Indonesia = 998 token. **Set uji v1 tidak menguji rentang ini**:
klaim terpanjang 749 karakter / 152 token, 0 dari 54 butir di atas 512 token. Demo
menampilkan jumlah token klaim di panel penguji.

- **Target:** penulis ulang kueri (rewriter) Versi 2 -- mengekstrak klaim inti dari pesan
  panjang sebelum retrieval. Set uji Versi 2 sebaiknya memuat pesan berantai panjang.

Pembaruan 2026-09-25: dampaknya kini **terukur** -- lihat bagian 5.2, eksperimen 4.

---

## 5. Parameter retrieval yang ditetapkan tanpa pengukuran (dan ablasi 2026-09-25)

Eksperimen: `src/evaluation/retrieval_ablation.py` (uji offline:
`tests/test_retrieval_ablation.py`); hasil `testset/retrieval_ablation.json` dan
`testset/retrieval_ablation_report.txt`. **Hanya retrieval, tanpa panggilan LLM**, pada 54 butir
set uji beku dengan `expected_retrieval_article` sebagai kebenaran dasar (40 non-batas + 4 batas
punya artikel sasaran). Skor kosinus eksak terhadap seluruh 450 chunk; kesetiaan tervalidasi:
top-3 eksak = `retriever.retrieve` produksi 54/54 dan = top-3 tercatat evaluasi v1 54/54.
**Pengukuran, bukan penyetelan -- tidak ada parameter produksi yang diubah.** Pengaruh pada
akurasi akhir belum terukur (butuh menjalankan generator, dan itu membatalkan keabsahan baseline
Versi 1; harus diuji pada set uji baru).

Aturan tafsir: selisih dianggap bermakna hanya bila McNemar eksak p < 0,05 **dan** selisih bersih
>= 3 butir. Selisih 1-2 butir tidak disimpulkan sebagai keunggulan. 44% butir berbagi artikel
jangkar, jadi p dan interval Wilson cenderung terlalu percaya diri.

### 5.1 Status tiap parameter

| Parameter | Nilai Versi 1 | Status pengukuran |
|---|---|---|
| `top_k` kandidat ke LLM | 3 | **Diuji (retrieval saja)**, eksperimen 1. Efek pada kecocokan palsu dan ukuran konteks LLM **belum** diukur. |
| Agregasi skor per artikel | maksimum antar-chunk | **Diuji**, eksperimen 2 (maks vs rata-rata vs rata-rata dua teratas). |
| Chunking per seksi | Narasi / Penjelasan / Kesimpulan | **Sebagian diuji**, eksperimen 3: subset seksi yang ikut dicari (setara indeks tanpa seksi itu, karena tiap chunk di-embed sendiri). **Belum diuji**: skema chunking lain (per paragraf, seluruh artikel, jendela token) karena **butuh pembangunan ulang indeks**. |
| Batas 512 token (`MAX_SEQ_LENGTH`) | 512 | **Sisi kueri diuji**, eksperimen 4 (klaim panjang). **Sisi indeks belum diuji** (embedding chunk dengan batas lain) karena **butuh pembangunan ulang indeks**; dampaknya kecil pada data sekarang (hanya 3/450 chunk terpotong). |
| Model embedding | BGE-M3 | **Belum diuji**: pembanding model lain **butuh pembangunan ulang indeks**. |
| `CHUNK_FETCH` (chunk diambil sebelum agregasi) | 30 | Tidak diuji terpisah; pada k=3 hasilnya identik dengan pencarian eksak penuh (54/54). |

Parameter yang butuh pembangunan ulang indeks (chunking lain, batas token indeks, model
embedding) adalah **agenda eksperimen Versi 2**, dengan indeks Versi 1 diarsipkan lebih dulu agar
baseline tetap dapat direproduksi.

### 5.2 Hasil ablasi

**Eksperimen 1 -- top-k** (agregasi maks, seluruh seksi), non-batas n=40:

| k | 1 | 3 | 5 | 10 | 20 |
|---|---|---|---|---|---|
| Recall@k | 33/40 | **36/40** | 38/40 | 39/40 | 40/40 |

Positif 20/20 sejak k=3; seluruh kegagalan ada di negatif sulit. Terhadap k=3: k=5 +2 (p=0,50),
k=10 +3 (p=0,25), k=20 +4 (p=0,125) -- **tidak ada yang dapat dibedakan dari kebetulan**. Empat
kegagalan Recall@3 Versi 1: `v1-024` dan `v1-027` masuk mulai k=5 (peringkat 4), `v1-033` mulai
k=10 (peringkat 6), `v1-022` mulai k=20 (peringkat 19). Menaikkan k juga menambah konteks LLM dan
dapat menaikkan kecocokan palsu (tidak diukur), jadi k yang memaksimalkan recall belum tentu k
terbaik.

**Eksperimen 2 -- agregasi**: maks 36/40 (@3), 38/40 (@5); rata-rata 35/40, 38/40; rata-rata dua
teratas 35/40, 36/40. Selisih maksimal 2 butir, **tidak dapat dibedakan dari kebetulan**. Tidak ada
bukti untuk mengganti agregasi maksimum.

**Eksperimen 3 -- seksi**:

| Kondisi | Recall@3 non-batas | vs seluruh seksi |
|---|---|---|
| Seluruh seksi (produksi) | 36/40 | -- |
| Hanya Narasi | 36/40 | identik (0 butir berpindah) |
| Narasi + Kesimpulan (tanpa Penjelasan) | 36/40 | identik (0 butir berpindah) |
| Hanya Kesimpulan | 30/40 | **-6, p=0,031: selisih bermakna** |

- Pada artikel yang BENAR, chunk berskor tertinggi berasal dari **Narasi 35/40**, Kesimpulan 3,
  Penjelasan 2 (positif: Narasi 17/20; negatif sulit: Narasi 18/20).
- **Penjelasan tidak menyumbang recall** pada set ini: membuangnya tidak mengubah satu butir pun,
  pada @3 maupun @5.
- **Menilai ulang asumsi Narasi.** Asumsi awal "klaim pengguna paling cocok dengan Narasi"
  sempat dinyatakan tidak terbukti (CLAUDE.md, 10 kueri set pengembangan). Ukuran di sana
  berbeda: seksi chunk teratas SECARA KESELURUHAN, artikel apa pun (Penjelasan 7/10). Dengan 44
  butir, **untuk artikel yang benar Narasi-lah yang paling cocok (35/40)**, dan Narasi saja sudah
  menyamai recall seluruh seksi. Kemenangan Penjelasan pada ukuran lama kemungkinan besar terjadi
  di artikel lain (tetangga), bukan pada artikel yang benar. Ini belum diuji langsung di sini.
- **Agenda eksperimen Versi 2 (bukan keputusan): menghapus seksi Penjelasan dari indeks.**
  Penjelasan tidak memberi kontribusi pada retrieval (0 butir berpindah saat dihilangkan, @3
  maupun @5). Menghapusnya akan memangkas sepertiga chunk (150 dari 450) dan mempercepat
  ingestion. Tetapi **wajib diuji dulu** apakah kehadirannya berpengaruh pada kualitas jawaban
  generator, lewat kandidat yang terpilih atau kecocokan palsu. Generator tidak membaca teks
  Penjelasan (konteksnya hanya judul, label, tanggal, Narasi, Kesimpulan, rujukan), tetapi
  Penjelasan dapat mengubah artikel mana yang masuk top-3. Dugaan bahwa Penjelasan lebih sering
  memunculkan artikel tetangga juga belum diuji. Pengujiannya butuh set uji baru.

**Eksperimen 4 -- panjang klaim** (20 butir positif non-batas; teks pengganggu **sintetis**,
hasil indikatif):

| Panjang | Pengganggu di kedua sisi | Klaim di awal (pengganggu di belakang) |
|---|---|---|
| Asli (48-582 karakter) | 20/20 | 20/20 |
| ~1.500 karakter | 19/20 | 19/20 |
| ~3.000 karakter | 19/20 | 19/20 |
| ~5.000 karakter | **2/20** (klaim di luar 512 token pada 18/20) | 19/20 |

- **Penurunan besar disebabkan pemotongan token, bukan pengenceran:** pada 5.000 karakter
  (median 1.112 token), separuh pengganggu di depan mendorong klaim melewati token ke-512 dan
  model embedding tidak melihatnya sama sekali (artikel benar jatuh ke peringkat 10-149). Bila klaim
  di awal pesan, recall tetap 19/20.
- Pengenceran murni hanya menjatuhkan satu butir (`v1-002`, peringkat 2 -> 4; skornya memang
  tipis sejak awal) dan menurunkan skor artikel benar secara bertahap (median: kedua sisi
  0,746 / 0,705 / 0,511 pada 1.500 / 3.000 / 5.000 karakter; klaim di awal 0,782 / 0,774 / 0,765).
- Artinya batas 5.000 karakter yang sempat dipakai demo **melampaui wilayah yang bekerja**. Pesan
  berantai dengan pembuka panjang (>~2.000 karakter sebelum klaim) praktis tidak akan menemukan
  artikelnya. **Tindak lanjut:** batas demo diturunkan ke 1.500 karakter (19/20 terukur), dengan
  peringatan sebelum pemeriksaan sejak ~220 token.
- **Target Versi 2:** rewriter yang mengekstrak klaim inti sebelum retrieval, atau embedding
  per potongan pesan. Set uji Versi 2 wajib memuat pesan berantai panjang yang ASLI (bukan
  sintetis) dengan posisi klaim beragam.

---

## 6. Keterbatasan ambang "mungkin terkait" 0,57 (demo)

Ambang tampilan `RELATED_SCORE_THRESHOLD = 0,57` di `src/presentation.py` **rapuh**:

- **Marginnya hanya 0,002** di atas skor kandidat tertinggi negatif mudah (0,5680).
- Ambang ini **disetel dari data set uji v1 itu sendiri** (dicek silang pada 10 kueri set
  pengembangan), bukan dari data terpisah.
- Skor kosinus bergantung pada isi basis data. Menambah artikel mengubah tetangga terdekat dan
  sebaran skor, sehingga **ambang ini tidak berlaku otomatis setelah basis data diperluas.**
- **Agenda Versi 2:** setel ulang ambang dari data terpisah (bukan set uji mana pun) setelah
  basis data diperluas, dan laporkan margin serta sebarannya. Karena ambang ini hanya
  memengaruhi tampilan, bukan vonis, ia tidak memengaruhi hasil evaluasi Versi 1.

**Pembaruan 2026-09-28 (indeks 922 artikel):** ambang kini dibaca per indeks dari
`config/related_threshold.json` beserta jumlah chunk tempat ia dikalibrasi; bila indeks berubah
ukuran, fitur mati sampai dikalibrasi ulang. Pada indeks 922 fitur **dimatikan** untuk indeks
`data` (arsip `archive/v1` tetap 0,57). **Alasannya:** pada set pengembangan tidak ada ambang yang
memisahkan -- kueri tak terkait "NASA ngaku bumi datar" (0,6385) berskor lebih tinggi daripada
kandidat yang layak tampil (0,5739-0,63), dan ambang 0,64 yang menyingkirkannya hanya bermargin
0,0015. **Bukan** karena artikel bertopik jauh lolos pada set uji v1 (lihat butir pertama).

- Negatif mudah v1 yang lolos 0,57: 4 dari 10 (40%), tetapi keempatnya bukan topik jauh (v1-043
  dan v1-049: artikel asalnya kini di basis data; v1-050: klaim yang sama kini ada, 36775; v1-044:
  topik dekat, Pigai soal HAM). Enam sisanya yang benar-benar tak terkait: maks 0,5666 (arsip:
  0,5351) -- skor tak terkait naik seiring basis data membesar.
- Set pengembangan: "NASA ngaku bumi datar" (tak terkait) kini 0,6385 ke "Gravitasi Bumi Berhenti
  7 Detik", di atas kandidat yang layak tampil (36729 0,5739; Pigai 0,5781; tetangga negatif
  sulit di peringkat 1: 0,62-0,63). Rentangnya tumpang tindih.
- Ambang 0,64 menyingkirkan 9 dari 9 tak terkait yang teramati (margin 0,0015) tetapi juga
  seluruh kandidat layak di atas; sampel tak terkait hanya 9. Rincian: `config/related_threshold.json`.
- Implikasi Versi 2: skor kosinus saja tidak cukup untuk daftar ini pada basis data besar;
  kandidat yang lebih pantas adalah keluaran grader (topik sama, klaim berbeda).

---

## 7. Pemetaan komponen Versi 2 (diperbarui 2026-09-25)

| Komponen | Tugas | Bukti dari Versi 1 | Keterukuran dampak |
|---|---|---|---|
| **Rewriter** (tugas 1) | Mengekstrak inti klaim dari pesan panjang **sebelum** retrieval | 18 dari 20 butir positif gagal Recall@3 pada pesan ~5.000 karakter karena klaim di luar jendela 512 token (bagian 5.2, eksperimen 4) | **Paling terukur**: selisih -18/20, jauh di atas kebetulan |
| **Rewriter** (tugas 2) | Menulis ulang kueri saat retrieval gagal | 4 butir dengan artikel benar di luar top-3: 2 nyaris (peringkat 4), 2 jauh (6 dan 19) (bagian 1) | Kecil: 4 butir |
| **Grader** | Menilai apakah kandidat benar-benar klaim yang sama | 2 kesalahan + 6 ketidakbulatan, semua dengan artikel benar di top-3 (bagian 2) | 7 butir unik; murni penilaian LLM |
| **Kredibilitas sumber** | Menyaring rujukan lebih cerdas dari per domain | Tidak ada temuan kuantitatif dari set uji v1 (bagian 3) | Belum terukur |

Agenda eksperimen terkait (bagian 5): menghapus seksi Penjelasan dari indeks; skema chunking,
batas token indeks, dan model embedding lain (butuh pembangunan ulang indeks); penyetelan ulang
ambang tampilan 0,57 dari data terpisah (bagian 6; pada indeks 922 fitur dimatikan). Persyaratan
set uji Versi 2 terkait snapshot basis data: bagian 8.

---

## 8. Keterikatan set uji pada snapshot basis data (dicatat 2026-09-28)

**Empat butir negatif berubah status pada indeks produksi 922 artikel.** v1-021, v1-022
(negatif_sulit, pola_sama_entitas_beda), v1-043, dan v1-049 (negatif_mudah) dibuat dari artikel
arsip TurnBackHoax (35310, 35850, 32490, 35833) yang kini ada di basis data produksi; artikel
asalnya muncul di **peringkat 1** (skor 0,8713; 0,7732; 0,8488; 0,8266). **Label negatif keempat
butir itu tidak berlaku pada indeks 922.** `v1.jsonl` tidak diubah: set uji v1 tetap beku dan hanya
sah pada `archive/v1/` (Aturan Wajib #6). Rincian: `v1.meta.json`
(`butir_negatif_berubah_status_indeks_922_2026-09-28`).

**Butir kelima: v1-050 (terverifikasi 2026-09-28).** Label negatifnya juga **tidak berlaku pada
indeks 922**, tetapi jalurnya berbeda dari empat butir di atas:

- **Tipe:** negatif_mudah (subtipe null, kekhususan "jauh"), `v1.jsonl` baris 50, sumber Liputan6
  (kandidat `liputan6-8293491`; semula cadangan strata negatif_mudah_teks_nyata, lalu dipakai
  mengisi kekurangan negatif_mudah -- tidak pernah terkait subtipe pola_sama_entitas_beda).
- **Asal 36775 di indeks produksi:** mode maju 2026-09-27 (`forward_2026-09-27.json`, 21/9/2026),
  bukan kelompok mundur.
- **Top-3:** 36775 di **peringkat 1** retriever produksi (top_k = `generator.TOP_K` = 3): 0,6330;
  berikutnya 33076 (0,5232) dan 32952 (0,4910). Tidak ada di `archive/v1`.
- **Bukti teks:** Narasi 36775 mengutip unggahan TikTok: "MenKeu Suhasasil Terlibat Korupsi 500
  Triliun"; teks butir: "Menkeu Suhasasil Terlibat Korupsi 500 Triliun" -- identik termasuk salah
  ketik "Suhasasil".
- **Mengapa berbeda:** empat butir lain dibuat dari artikel arsip TurnBackHoax. v1-050 bersumber
  Liputan6, yang diutamakan justru sebagai sumber independen (bukan arsip Mafindo/TurnBackHoax),
  namun TurnBackHoax memeriksa hoaks yang sama 4 hari kemudian. **Butir negatif dari situs cek
  fakta lain pun tidak aman dari perubahan status.**
- **Linimasa:** unggahan 16/9; Liputan6 17/9/2026; basis data 150 artikel berakhir 18/9/2026;
  TurnBackHoax 36775 21/9/2026. **Verifikasi awal benar pada saatnya:** 36775 belum ada di basis
  data 150 artikel. Ini bukan kesalahan prosedur, melainkan konsekuensi jeda waktu antar-situs cek
  fakta. (Catatan: saat halaman Liputan6 di-cache, 22/9, 36775 sudah terbit di situs TurnBackHoax;
  prosedur memang memeriksa terhadap basis data, bukan situs.)
- `v1.jsonl` tidak diubah; set uji tetap sah hanya pada `archive/v1/`.

**Rekap (2026-09-28): lima butir negatif tidak berlaku pada indeks 922** -- v1-021, v1-022,
v1-043, v1-049, dan v1-050. Kelimanya diverifikasi dengan top-3 retrieval (artikel berisi klaim
yang sama di peringkat 1), bukan sekadar keberadaan artikel di basis data.

- **v1-029 (berikutnya diperiksa):** artikel asalnya (30089, 16 Nov 2025, negatif_sulit)
  berpotensi masuk pada kelompok perluasan berikutnya (mundur ke akhir September 2025). Setelah
  masuk, **verifikasi dulu apakah 30089 benar-benar masuk top-3 retrieval untuk klaim v1-029**
  sebelum menyimpulkan labelnya gugur -- prosedur yang sama dengan v1-050. Artikel asal v1-042
  (28638, 27 Agu 2025) tepat di luar batas akhir September 2025. Sumber arsip lain (23531, 23544,
  26646, 26669, 26671) bertanggal Okt 2024-Apr 2025.
- **Pengamatan (bukan kesimpulan):** jumlah label negatif yang gugur tampak bertambah seiring basis
  data membesar (0 pada 150 artikel, 5 pada 922). Lima kasus belum cukup untuk disimpulkan sebagai
  pola yang terukur; jumlahnya juga bergantung pada cara butir dibuat (4 dari 5 berasal dari arsip
  TurnBackHoax), bukan hanya pada ukuran basis data.

**Persyaratan set uji Versi 2:**

1. Setiap butir negatif **wajib diverifikasi terhadap snapshot basis data yang dipakai** (daftar id
   artikel + sidik jari isi).
2. Set uji **wajib diberi versi bersama snapshot itu**; hasilnya hanya sah pada snapshot tersebut.
3. Butir negatif yang berasal dari artikel arsip **tidak boleh dipakai** bila artikel itu
   berpotensi masuk basis data (mis. berada dalam rentang tanggal perluasan yang direncanakan).
4. **Wajib:** butir negatif dari hoaks nyata yang diperiksa situs cek fakta **lain** juga
   diperiksa ulang terhadap snapshot. Bukti konkret: v1-050 (Liputan6 17/9 -> TurnBackHoax 36775
   21/9, peringkat 1 pada indeks 922). Persyaratan set uji Versi 2, bukan pekerjaan sekarang.

---

## 9. Kebersihan rujukan dari DATA tidak diukur pada evaluasi Versi 1 (dicatat 2026-10-03)

Evaluasi Versi 1 mengukur **URL karangan LLM** (URL pada keluaran LLM di luar metadata: 0), tetapi
**tidak pernah mengukur apakah rujukan yang berasal dari metadata itu sendiri layak ditampilkan**.
Itu celah yang tidak terukur waktu itu, bukan temuan tentang perilaku LLM.

- **Arsip indeks Versi 1 (`archive/v1`, 150 artikel):** satu artikel, **36089** (PENIPUAN, "Tautan
  Lowongan Kerja untuk Lansia 2026"), menyimpan tautan pemendek `bit.ly` di metadata `references`.
  Menurut Kesimpulan artikel itu, tautan tersebut adalah tautan pendaftaran program Kemnaker (jadi
  kemungkinan rujukan sah), tetapi tujuannya **tidak diperiksa** dan tidak dapat diverifikasi
  pengguna sebelum diklik. Dengan kebijakan penyaringan per 2026-10-03 (pemendek URL, seluruh domain
  arsip, baris "Sumber:") hanya artikel ini yang rujukan tersimpannya berubah di arsip; 14 artikel
  arsip lain hanya berubah pada `claim_sources`/`references_filtered`, yang tidak ada di indeks.
- **Apakah tautan itu pernah tampil pada evaluasi:** pada `data/testset_v1_eval_gemini-3.5-flash-lite.jsonl`
  (162 baris, 3 run), 36089 hanya muncul sebagai kandidat top-3 retrieval untuk v1-026 dan v1-029
  (6 baris, semuanya dijawab "tidak ditemukan"); ia **tidak pernah menjadi artikel jawaban**. Jadi
  tautan itu tidak pernah menjadi rujukan sebuah jawaban di evaluasi, tetapi ikut terkirim ke LLM
  sebagai bagian konteks kandidat (konteks memuat rujukan). Berkas hasil evaluasi tidak menyimpan
  daftar rujukan jawaban, sehingga kebersihan rujukan memang tidak dapat diaudit dari sana.
- **`archive/v1/` tidak diubah** (Aturan Wajib #6); angka baseline tidak terpengaruh. Bila demo
  diarahkan ke arsip, lapisan tampilan (`presentation.display_references`) menyaring tautan itu.
- **Pada indeks produksi (922 artikel) celahnya lebih besar:** 20 artikel menyimpan rujukan yang
  kini disaring (pemendek URL dan arsip di luar daftar lama), termasuk URL baris "Sumber:" -- sumber
  hoaks -- pada 7 artikel; diperbaiki 2026-10-03 (lihat CLAUDE.md, "Temuan Aturan Wajib #1").
- **Persyaratan untuk evaluasi Versi 2:** tambahkan metrik kebersihan rujukan DATA -- untuk setiap
  jawaban "ditemukan", rujukan yang ditampilkan diperiksa terhadap kebijakan penyaringan terkini
  dan terhadap sumber klaim artikel (`claim_sources`, termasuk baris "Sumber:") -- dan simpan daftar
  rujukan jawaban di berkas hasil agar dapat diaudit. Ini juga masukan langsung untuk komponen
  penilaian kredibilitas sumber.

## Ringkasan angka

- Recall@3 non-batas: 36/40 (90%) -- tapi hanya 17/20 butir negatif_sulit yang benar-benar
  "teruji" generatornya (lihat batas tafsir H1 di atas).
- Dari 4 kegagalan retrieval: 2 nyaris (peringkat 4), 2 jauh (peringkat 6 dan 19).
- Dari 7 butir bermasalah di sisi generator (kesalahan + tidak bulat): 0 di antaranya
  disebabkan retrieval -- 100% murni penilaian LLM.
