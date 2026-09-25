# Temuan Versi 1 untuk rancangan Versi 2

Disusun 2026-09-23 dari hasil evaluasi set uji v1 (3 run x 54 butir, `testset/v1_analysis.json`
dan `testset/v1_analysis_report.txt`). Ini daftar **temuan terukur**, bukan rancangan Versi 2 --
komponen yang disebut di tiap bagian hanya menandai target, implementasinya belum dirancang.

Latar (lihat CLAUDE.md, "Versi 2 — Corrective RAG"): komponen kandidat Versi 2 adalah (a) node
**penulis ulang kueri** (query rewriter), (b) node **penilai relevansi dokumen** (grader), dan
(c) **penilaian kredibilitas sumber**.

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

- **Target:** instruksi bidang `klarifikasi` pada prompt Versi 2 (mis. kalimat pendek,
  urutan fakta -> konteks, subjek eksplisit). Perubahan prompt wajib diukur pada set uji baru,
  bukan set uji v1 yang beku.
- **Yang sudah dilakukan di Versi 1 (hanya penyajian, teks tidak diubah):** kolom baca
  dipersempit (560 px), jarak baris 1,75, dan klarifikasi dipisah jarak dari blok status serta
  dipisah garis dari rujukan.

### 4.2 Klaim panjang melebihi batas token embedding (dari kode + tokenizer; frekuensi di pemakaian nyata belum diukur)

Batas masukan demo dinaikkan ke 5.000 karakter (pesan berantai nyata sering panjang). Retrieval
meng-embed klaim dengan batas `MAX_SEQ_LENGTH` = 512 token, sehingga **bagian klaim di atas
~512 token tidak ikut dicari** (LLM tetap membaca klaim utuh). Terukur dengan tokenizer bge-m3:
satu contoh teks 5.000 karakter berbahasa Indonesia = 998 token. **Set uji v1 tidak menguji rentang ini**:
klaim terpanjang 749 karakter / 152 token, 0 dari 54 butir di atas 512 token. Demo
menampilkan jumlah token klaim di panel penguji.

- **Target:** penulis ulang kueri (rewriter) Versi 2 -- mengekstrak klaim inti dari pesan
  panjang sebelum retrieval. Set uji Versi 2 sebaiknya memuat pesan berantai panjang.

---

## Ringkasan angka

- Recall@3 non-batas: 36/40 (90%) -- tapi hanya 17/20 butir negatif_sulit yang benar-benar
  "teruji" generatornya (lihat batas tafsir H1 di atas).
- Dari 4 kegagalan retrieval: 2 nyaris (peringkat 4), 2 jauh (peringkat 6 dan 19).
- Dari 7 butir bermasalah di sisi generator (kesalahan + tidak bulat): 0 di antaranya
  disebabkan retrieval -- 100% murni penilaian LLM.
