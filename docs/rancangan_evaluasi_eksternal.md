# Rancangan evaluasi eksternal: 99 butir Liputan6 pada indeks produksi 1.532 artikel

**Status (2026-10-17): RANCANGAN DAN USULAN PRA-REGISTRASI; BELUM DISETUJUI DAN BELUM DIJALANKAN.**
Belum ada panggilan LLM, belum ada ingest, dan sistem tidak diubah. Satu-satunya yang sudah
dijalankan adalah **audit jejak identik** (bagian 7.1), yang tidak memakai LLM maupun embedding dan
parameternya di-commit sebelum dijalankan (`e7504fc`). Angka ambang di bawah adalah **usulan**:
baru mengikat setelah pemilik proyek menyetujuinya dan persetujuan itu di-commit, sebelum evaluasi
pertama dijalankan.

Asal butir dan labelnya: `docs/rancangan_v2.md` bagian 11 (11.3-11.8). Teks Liputan6 dan TurnBackHoax
tetap lokal (`data/candidates/`, tidak di-commit).

---

## 1. Mengapa evaluasi ini

1. **Akurasi sistem pada indeks produksi belum pernah diukur.** Angka Versi 1 (48/50, Recall@3
   36/40) berasal dari indeks 150 artikel (`archive/v1`). Pada indeks 1.532 artikel yang dipakai demo
   hanya retrieval yang terukur (positif Recall@1/3 = 18/20 dan 20/20). Ke-99 butir celah adalah
   klaim **nyata** dari situs cek fakta lain dengan label emas manusia: 46 positif dengan id artikel
   sasaran dan 53 negatif.
2. **Prasyarat langkah korektif bergaya CRAG yang dibatasi ke situs cek fakta.** Bagian tersulit
   CRAG adalah penilai retrieval, dan proyek ini sudah tiga kali menunjukkan bahwa ambang skor tidak
   memisahkan cocok dari tidak cocok (set pengembangan 2026-09-21; ablasi dan "mungkin terkait"
   2026-10-03; kunci celah 11.5 dan 11.9). Di sistem ini, pemicu langkah korektif adalah generator
   yang menjawab "belum ditemukan". Karena itu **ketepatan sistem pada butir negatif adalah ukuran
   mutu pemicu itu dan dilaporkan paling menonjol** (bagian 6.2).

Membangun langkah korektif kelak adalah **keputusan baru dengan alasan baru** (celah sekitar separuh
tetap besar), **bukan** klaim bahwa ambang di `rancangan_v2.md` bagian 11 terpenuhi. Ambang itu tidak
terpenuhi (11.8).

---

## 2. Butir dan kueri

### 2.1 Kueri = kutipan pesan Liputan6 apa adanya

Kueri adalah kutipan pesan yang diambil dari artikel Liputan6 (`sampel_liputan6.jsonl`, kolom
`pesan`), dikirim tanpa diubah, seperti yang akan ditempel pengguna. Judul Liputan6 **tidak** dipakai
sebagai kueri: judul adalah parafrase pemeriksa fakta, memuat kata vonis, dan justru menjadi kueri
yang menghasilkan daftar kandidat (bias ke atas yang paling besar, lihat bagian 4).

### 2.2 Aturan kutipan yang tidak memuat klaim (usulan; ditetapkan sebelum hasil apa pun dilihat)

Dihitung dengan `candidates.trace_audit.words` (NFKC, huruf kecil, tautan berskema/`www.` dibuang,
tanda baca menjadi pemisah):

- **K1 -- kutipan kurang dari 5 kata setelah tautan dibuang:** 7 butir. Rinciannya: hanya tautan 5
  (P1-4, P1-19, P2-10, P2-11, P1-5), kosong 1 (P2-18; artikelnya tidak mengutip pesan), satu salam
  saja 1 (P2-46). **Ambang ini tidak peka:** ambang 3, 5, atau 8 kata menghasilkan 7 butir yang sama;
  butir berikutnya baru muncul pada 9 kata.
- **K2 -- kutipan berupa kalimat pengantar redaksi** (diakhiri titik dua, mis. "... berikut
  isinya:"): 1 butir (P2-34). Hanya satu butir di 99 yang diakhiri titik dua.
- **Perlakuan yang diusulkan: DIKELUARKAN dari analisis utama, tanpa diganti judul.** Alasannya:
  tautan saja atau salam tidak memuat klaim yang dapat dibandingkan, dan mengganti dengan judul
  menambah bias (2.1). Butir ini juga tidak dijalankan (hemat 24 panggilan). Jumlahnya dilaporkan per
  label: **positif 4** (P1-5, P2-18, P2-34, P2-46) dan **negatif 4** (P1-4, P1-19, P2-10, P2-11).
  *Catatan:* pengguna sungguhan memang bisa menempel tautan saja; sistem tidak dirancang untuk itu
  (tidak mengambil isi tautan), dan itu dicatat sebagai keterbatasan, bukan diukur di sini.
- **Butir analisis: 91** = **42 positif** (P1 20, P2 22) dan **49 negatif** (P1 27, P2 22).

### 2.3 Panjang

Token bge-m3 tercatat di sampel (bagian 10.7): **0 dari 99 di atas 512 token** (maks 312); **0 di
atas 1.500 karakter** (batas masukan demo; maks 1.032); 4 butir di atas 220 token (P1-21, P1-39, P2-1,
P2-25), yang di demo memunculkan peringatan tetapi tetap diperiksa. Jadi tidak ada butir yang
terpotong jendela embedding atau ditolak demo; aturan tambahan tidak diperlukan.

---

## 3. Label emas dan keterbatasannya

- **Positif** = butir yang KEPUTUSAN-nya id artikel TurnBackHoax (sasaran = id itu). **Negatif** =
  butir berkeputusan TIDAK ADA.
- **Negatif hanya berarti "tidak ada yang cocok di daftar kandidat" (5-8 artikel per butir), BUKAN
  "tidak ada di basis data".** Kandidat dicari dari judul Liputan6 (5 teratas embedding + 3 teratas
  kata kunci judul); pasangan yang luput dari keduanya tidak pernah dilihat pemilik proyek.
- **Protokol bila sistem mencocokkan butir negatif dengan artikel:**
  1. Pada analisis utama, setiap jawaban "ditemukan" pada butir negatif dihitung **kecocokan palsu**,
     baik artikelnya ada di daftar kandidat maupun tidak. Label awal tidak pernah ditimpa.
  2. Bila artikelnya **di luar daftar kandidat**, pemilik proyek menilainya dengan Aturan A/B lewat
     adjudikasi buta (7.3). Hasilnya dicatat terpisah sebagai "cocok di luar daftar: sah / tidak
     sah" dan dilaporkan sebagai sensitivitas, bukan sebagai pengganti label.
  3. Bila artikelnya **di dalam daftar**, pemilik proyek sudah pernah menolaknya; ia tetap masuk
     adjudikasi buta (7.3) agar perlakuannya sama.
- **Empat butir ragu (P2-2, P2-14, P2-30 TIDAK ADA; P2-18 cocok).** P2-18 dikeluarkan oleh K1. Tiga
  sisanya: label utama dipakai apa adanya; sensitivitas dua arah seperti 11.6 (dihitung cocok /
  dihitung TIDAK ADA). Karena "cocok" pada butir ragu tidak menyebut artikel, pada arah "dihitung
  cocok" sasarannya adalah kandidat yang dipilih sistem bila ada di daftar kandidat butir itu.
- **Perbedaan aturan antar-putaran.** P1 dilabel dengan pedoman v1.0 (dua inkonsistensi tercatat,
  tanpa Narasi); P2 dengan Aturan A/B dan Narasi utuh.
  - **Hasil utama = gabungan 91 butir** dengan label utama (ukuran sampel terbesar; sesuai cara
    11.6 menjadikan gabungan hasil utama).
  - **Hasil sekunder = per putaran** (P1: 20 positif / 27 negatif; P2: 22 / 22), selalu disajikan
    berdampingan dan **tanpa uji beda** (sama seperti 11.8 langkah 4).
  - **Sensitivitas P1:** 15 butir yang ditandai tidak konsisten (11.5) dibalik ke dua arah, dengan
    cara 11.5.
  - Bila kesimpulan sebuah metrik berbeda antara P1 dan P2, kesimpulan itu dilaporkan **bergantung
    pada aturan pelabelan**, bukan dirata-ratakan.
- **Ketidakselarasan label dengan generator (temuan saat menyusun rancangan).** Label P2 mengikuti
  Aturan A ("lembaga dan jenis tawaran sama = cocok walau gelombangnya berbeda"), sedangkan prompt
  generator yang terkunci mengikuti pedoman v1.0, yang tidak punya aturan gelombang. 14 dari 25
  pasangan P2 terpaut lebih dari 30 hari, dan semuanya PENIPUAN. Generator yang menolak pasangan
  lintas gelombang akan tercatat **penolakan palsu** walau ia konsisten dengan pedomannya sendiri.
  Karena itu metrik positif juga dilaporkan per strata **selisih terbit <= 30 hari vs > 30 hari**.

---

## 4. Bias yang sudah diketahui: Recall@3 positif bias ke atas

Daftar kandidat dibuat oleh retriever produksi (dengan judul sebagai kueri) dan pencarian kata kunci
judul. Positif ada **hanya** bila pasangannya muncul di daftar itu, jadi Recall@3 dihitung pada
pasangan yang sudah terbukti dapat ditemukan oleh retriever yang sama. Pasangan yang tidak dapat
ditemukan retriever tidak pernah menjadi positif. Cara melaporkannya:

1. Recall@3 selalu disebut **"Recall@3 bersyarat (pada pasangan yang terjangkau pencarian
   judul)"**, tidak pernah disandingkan langsung dengan Recall@3 Versi 1 tanpa catatan ini.
2. **Strata menurut cara pasangan ditemukan** (dari kunci yang sudah dibuka, 11.5 dan 11.9): (a)
   teratas embedding judul, (b) di 5 teratas embedding tetapi bukan teratas, (c) hanya dari kata
   kunci. Strata (b) dan (c) lebih dekat ke kondisi tanpa bias.
3. **Pembanding pemisah efek kueri:** Recall@3 dengan kueri judul (tanpa kata vonis) dan dengan kueri
   kutipan, keduanya tanpa LLM. Selisihnya menunjukkan berapa banyak yang hilang karena pengguna
   menempel pesan, bukan parafrase pemeriksa fakta.
4. Kalimat wajib di laporan: *Recall@3 ini batas atas; Recall@3 sistem atas seluruh klaim yang
   memang ada di TurnBackHoax tidak dapat diukur dari set ini.*

Bias yang sama menyentuh negatif dari arah sebaliknya: negatif "sulit" karena kandidatnya sudah yang
paling mirip menurut retriever, jadi kecocokan palsu di sini lebih mungkin daripada pada klaim acak
yang tidak ada di basis data.

---

## 5. Pembekuan indeks

- Evaluasi dijalankan pada **indeks produksi 1.532 artikel yang sekarang**, sebelum antrean
  di-ingest: artikel baru bisa mengubah butir negatif menjadi positif. **Ingest antrean dijalankan
  pemilik proyek setelah evaluasi selesai** (termasuk adjudikasi).
- **Sidik jari indeks yang dibekukan** (`python -m evaluation.index_check --fingerprint
  --embed-sample 0`, 2026-10-17; kode keluar 0, "INDEKS SEGAR", `ef_search` 2000):

  | Kunci | Nilai |
  | --- | --- |
  | jumlah_artikel / jumlah_chunk | 1.532 / 4.593 |
  | sha256_daftar_artikel | `1a1a4f198c22b98b12b60f83717e5e1a88147cafcc7d80acb8c6147d4c789d5b` |
  | sha256_teks_metadata | `6283f0f6c8db894360116a7487ccf93dd15ded7d9fac33e5d6970c3a05530330` |
  | sha256_embedding_float32 | `9851a6dcba0c84c1216e7067f27484aa25b3cc81f3c4a3bb4ae0eeca0b79de94` |
  | sha256_articles_json_isi | `cc7f1989ad1bf6c6ae7a055b8985ac1800722eb12415e8c2090aee346c77fb28` |

- Sebelum **setiap** hari evaluasi: sidik jari dicocokkan (berhenti bila beda), dan
  `python -m evaluation.retriever_exactness` wajib kode keluar 0 (top-3 HNSW = pencarian eksak).
- Pembaruan berkala terjadwal hanya mengambil artikel ke antrean dan tidak meng-ingest, jadi tidak
  mengubah indeks; antrean tetap tidak boleh digabung selama evaluasi.

---

## 6. Metrik dan ambang (usulan; dikunci sebelum dijalankan)

Semua proporsi dengan interval Wilson 95%. Keputusan per butir = **modus 3 run** (seperti Versi 1);
ketidakbulatan antar-run dilaporkan terpisah. Butir "tak terjawab" (galat API setelah semua
percobaan) dilaporkan sendiri dan tidak dihitung benar maupun salah.

### 6.1 Metrik positif (42 butir)

- **Recall@3 bersyarat** (retrieval saja; bagian 4).
- **Ketepatan jawaban cocok** = modus "ditemukan" dengan id sasaran.
- Dipecah: penolakan palsu (modus "belum ditemukan") dan artikel salah (ditemukan, id lain).
- **Ambang (usulan):** memadai bila batas bawah Wilson >= 60% (pada 42 butir: >= 32/42); buruk bila
  batas atas < 60% (<= 18/42); di antaranya tidak konklusif. Ambang positif ini **tidak** menjadi
  gerbang langkah korektif; ia menilai apakah demo layak diklaim menemukan klaim yang ada.

### 6.2 Metrik negatif (49 butir) -- dilaporkan paling menonjol

- **Tingkat kecocokan palsu** = modus "ditemukan" (artikel apa pun) / 49. Dipecah: artikel di dalam
  daftar kandidat vs di luar (3).
- **Tingkat penolakan benar** = modus "belum ditemukan" / 49 (= 1 - kecocokan palsu bila tidak ada
  yang tak terjawab).
- **Ambang kecocokan palsu (usulan; gerbang pemicu CRAG):**

  | Kategori | Syarat | Pada 49 butir |
  | --- | --- | --- |
  | **Lulus** | proporsi <= 10% DAN batas atas Wilson <= 20% | <= 4/49 (8,2% [3,2%; 19,2%]) |
  | **Gugur** | batas bawah Wilson > 10% | >= 10/49 (20,4% [11,5%; 33,6%]) |
  | Tidak konklusif | di antaranya | 5-9/49 |

  *Dasar pemilihan.* Versi 1 mencatat kecocokan palsu 1/30 pada negatif non-batas (3,3% [0,6%;
  16,7%]). Set ini lebih sulit: negatifnya klaim nyata yang tetangga terdekatnya dipilih retriever
  yang sama (bagian 4), dan banyak berupa penipuan berpola sama dengan lembaga berbeda. Ambang 10%
  memberi ruang sekitar tiga kali angka Versi 1, tetapi batas atas 20% menjaga agar "lulus" tidak
  bisa dicapai dengan hasil yang intervalnya masih memuat satu dari lima klaim tercap keliru.
  *Makna bahayanya di set ini:* ke-49 klaim negatif sudah dinyatakan hoaks oleh Liputan6, jadi
  kecocokan palsu di sini tidak membalik nilai kebenaran; yang salah adalah artikel, klarifikasi,
  dan rujukan yang ditampilkan. Pada klaim pengguna yang benar, kecocokan palsu bisa mencap klaim
  benar sebagai hoaks. Ambang ini mengukur disiplin pencocokan, bukan besarnya kerugian.
- Bila kategori berbeda antara label utama dan sensitivitas (butir ragu, 15 butir P1), yang
  dilaporkan adalah kategori terburuk di antara keduanya, dengan penjelasan.

### 6.3 Uji kemunduran: testset-v1 pada indeks 1.532

- Seluruh 54 butir dijalankan 3 run dengan prosedur Versi 1 (`evaluation.testset_eval`, tanpa
  mengubah kode; `RAG_INDEX_DIR` tidak diset).
- **Dianalisis pada 48 butir:** enam butir negatif yang statusnya berubah pada indeks 1.532 (v1-021,
  v1-022, v1-029, v1-043, v1-049, v1-050; `v1.meta.json`) dikeluarkan karena labelnya tidak lagi
  berlaku. Tersisa 44 non-batas dan 4 batas.
- **Pembanding:** keputusan modus Versi 1 pada butir yang sama di `archive/v1`
  (`data/testset_v1_eval_gemini-3.5-flash-lite.jsonl`).
- **Ambang (usulan):** "mundur" bila kemunduran bersih pada 44 butir non-batas >= 3, yaitu (benar di
  arsip -> salah di 1.532) dikurangi (salah -> benar). Setiap perpindahan dilaporkan per butir dengan
  penyebab yang terlihat (retrieval vs penilaian). Selisih di sini mencampur efek data dan bukan uji
  arsitektur (Aturan Wajib #6 tetap berlaku untuk angka asli Versi 1).

---

## 7. Keandalan label tanpa anotator kedua

**Yang diukur adalah konsistensi satu anotator, bukan kesepakatan antar-anotator.** Anotator kedua
belum tersedia dan dapat ditambahkan belakangan dengan berkas yang sama. **LLM tidak dipakai sebagai
anotator pengganti.** Hasil ketiga langkah di bawah **tidak pernah mengganti label utama**.

### 7.1 Audit jejak identik (tanpa LLM, tanpa embedding) -- SUDAH DIJALANKAN

- **Alat:** `python -m candidates.trace_audit` (uji `tests/test_trace_audit.py`). Parameter
  di-commit sebelum dijalankan (`e7504fc`).
- **Sinyal (a), domain tautan hoaks yang sama:** host tautan di kutipan vs host di `claim_sources`
  dan tautan di Narasi setiap kandidat. Tidak dihitung: domain daftar-blokir (`links.blocked_reason`:
  media sosial, arsip, hosting gambar, pemendek URL), sumber tepercaya (`links.is_trusted_source`:
  `.go.id`, media, cek fakta), dan `turnbackhoax.id`/`liputan6.com`. Yang dicocokkan host persis
  (tanpa `www.`), bukan domain terdaftar, karena akhiran seperti `my.id`/`biz.id` dipakai bersama
  banyak pemilik. Hanya tautan berskema `http(s)` atau `www.`.
- **Sinyal (b), rangkaian kata identik:** minimal **8 kata** berurutan sama antara kutipan dan
  Narasi kandidat setelah normalisasi (NFKC, huruf kecil, tautan dibuang, tanda baca menjadi
  pemisah). Alasan 8: cukup panjang untuk menyingkirkan frasa umum (salam, "klik link berikut"),
  tetapi masih menangkap kutipan sebagian.
- **Hasil awal (2026-10-17):**
  - **Butir terdeteksi: 20 dari 99.**
  - Positif (46): jejak hanya pada artikel pilihan 11, pada pilihan dan kandidat lain 1, hanya pada
    kandidat lain 1, tanpa jejak 33.
  - **Presisi pada butir berlabel cocok** (satu-satunya tempat kebenarannya diketahui): 12 dari 14
    pasangan (butir, kandidat) berjejak adalah artikel pilihan pemilik proyek.
  - **Negatif (53): 7 berjejak, untuk ditinjau ulang secara buta: P1-10, P1-20, P1-29, P1-30, P1-38,
    P1-45, P2-2.** Sinyal per butir **sengaja tidak ditulis di sini**; ada di berkas lokal
    `audit_jejak_identik.json`, yang tidak boleh dibuka pemilik proyek sebelum tinjauan buta
    selesai. Rincian per sinyal dilaporkan sesudahnya.
  - Butir tanpa jejak sama sekali tidak berarti tidak cocok: 33 dari 46 positif tanpa jejak, karena
    pesan penipuan berganti tautan dan kalimat antar-gelombang (bagian 3).
- **Tinjauan buta tujuh butir itu** digabung ke berkas uji ulang 7.2, diacak bersama butir lain,
  tanpa keterangan mana yang berasal dari audit. Hasilnya dilaporkan sebagai "berubah / tetap" per
  butir, sebagai sensitivitas, dan tidak dihitung dalam kappa kecuali butirnya juga terambil acak.

### 7.2 Uji ulang buta oleh pemilik proyek sendiri

- **Waktu:** paling cepat **27 Oktober 2026** (dua minggu setelah pelabelan terakhir 13 Oktober).
- **Butir:** 30, diambil acak berbenih **20261027**:
  - **20 dari P2** (49 butir; termasuk butir ragu): ukuran **konsistensi** (aturan sama).
  - **10 dari P1**, dari 30 butir yang memenuhi syarat: butir 1-5 (dibahas bersama AI) dan 15 butir
    yang pernah ditandai tidak konsisten **dikeluarkan**. Butir P1 dilabel ulang dengan **Aturan
    A/B**, jadi hasilnya diukur sebagai **efek pergantian aturan**, bukan konsistensi.
  - Ditambah butir dari 7.1 yang belum terambil (tidak masuk kappa).
- **Berkas:** tata letak blok `gap_blocks` (Narasi utuh, kini dengan tinggi baris yang benar);
  urutan butir dan urutan kandidat diacak; label lama, catatan, dan tanda ragu disembunyikan;
  butir dinomori ulang. Peta nomor baru -> butir asli disimpan terpisah dan tidak dibuka sampai
  pemilik proyek selesai.
- **Ukuran:** Cohen's kappa pada keputusan biner (cocok vs TIDAK ADA), interval 95% bootstrap
  persentil (10.000 ulangan, benih 20261027), dilaporkan untuk P2 (konsistensi; dipakai ambang
  7.4), P1 (efek aturan), dan gabungan 30 (deskriptif). Juga dilaporkan: kesepakatan persis
  termasuk id artikel, dan perpindahan per arah (cocok -> TIDAK ADA dan sebaliknya).
- **Keterbatasan yang diterima:** dengan 20 butir, interval kappa lebar (kira-kira +-0,25); butir P1
  pernah dilihat sebelumnya, jadi ingatan bisa menaikkan kesepakatan.

### 7.3 Adjudikasi buta setelah evaluasi

- **Hanya butir yang keputusan modus sistemnya berbeda dari label** (penolakan palsu, artikel salah,
  kecocokan palsu).
- Disajikan sebagai **dua opsi dalam urutan acak**, tanpa keterangan mana dari sistem: opsi label
  (id artikel atau TIDAK ADA) dan opsi sistem. Untuk opsi yang berupa artikel ditampilkan judul,
  Narasi utuh, dan Kesimpulan, seperti di berkas konfirmasi. Aturan A/B berlaku.
- **Dilaporkan:** berapa yang berubah, per arah dan per jenis. Hasil utama tetap memakai label awal;
  hasil dengan label adjudikasi hanya sensitivitas. **Bias yang disadari:** adjudikasi hanya meninjau
  ulang butir yang tidak sepakat dengan sistem, jadi ia hanya bisa menggeser hasil ke arah sistem.

### 7.4 Ambang kappa (ditetapkan sebelum uji ulang)

Diterapkan pada kappa titik P2 (n = 20):

| Kappa P2 | Tindakan |
| --- | --- |
| >= 0,80 | Label dipakai apa adanya. |
| 0,60-0,79 | Hasil tetap memakai label utama, tetapi setiap metrik dilaporkan juga dengan butir yang berubah pada uji ulang dibalik ke dua arah. Kategori "lulus" hanya dinyatakan bila lulus pada kedua arah. |
| < 0,60 | Set ini **tidak dipakai sebagai gerbang** apa pun (termasuk pemicu CRAG); hasil evaluasi hanya deskriptif, dan pedoman perlu diperjelas sebelum set baru dibuat. |

Bila kappa P1 (efek aturan) < 0,60, hasil per putaran P1 diberi catatan bahwa labelnya tidak sebanding
dengan P2, tetapi gabungan tetap dihitung seperti 3.

---

## 8. Pelaksanaan

- **Generator, prompt, dan retriever terkunci.** `src/generator.py` = sidik jari terkunci
  `e5a5ba5a...` (sudah dicek sama, 2026-10-17); model `gemini-3.5-flash-lite`, thinking `medium`,
  tanpa override `.env`. Hash `src/retriever.py` dicatat sekarang dan diperiksa sebelum setiap hari
  evaluasi: `68321aed...` (normalisasi CRLF->LF, UTF-8). Juga `src/chunker.py` `6d9de5ce...`. Uji
  kunci (`tests/test_testset_locks.py`) wajib lolos sebelum setiap hari evaluasi.
- **3 run, keputusan modus**, urutan butir diacak per run dengan benih **2026101701-03**.
- **Skrip baru** `evaluation.external_eval` (belum ditulis), meniru `testset_eval`: hasil mentah
  per (run, butir) ke `data/external_eval_<model>.jsonl` (lokal), lanjut dari yang terakhir per
  (run, butir), berhenti bila kuota harian habis atau 2 butir beruntun tak terjawab. Analisis di
  skrip terpisah tanpa panggilan API.
- **Kuota (RPD 500, berbagi dengan demo):**

  | | Butir | Panggilan minimum (3 run) | Terburuk dengan ulang format |
  | --- | --- | --- | --- |
  | Liputan6 | 91 | 273 | 546 |
  | testset-v1 | 54 | 162 | 324 |
  | **Jumlah** | | **435** | 870 |

  **Usulan: 3 hari, satu run kedua set per hari** (145 panggilan minimum, 290 terburuk dengan ulang
  format), menyisakan >= 210 per hari untuk ulang butir dan demo. Catatan: pemeriksaan anggaran
  `testset_eval` memakai kasus terburuk 6 panggilan per butir; untuk 91 butir itu 546 > 500, jadi
  skrip baru memeriksa anggaran dengan 2 panggilan per butir (ulang format), dan buku besar kuota
  tetap menjadi penghenti keras saat sisa habis.
- **Yang boleh dipublikasikan (di-commit):** metrik agregat dan intervalnya; tabel per butir berisi
  nomor butir, id artikel Liputan6 (angka), label emas (id TurnBackHoax / TIDAK ADA), keputusan modus
  sistem, dan id artikel jawaban. **Tidak** dipublikasikan: kutipan pesan, judul Liputan6, Narasi,
  keluaran mentah dan alasan LLM (bisa mengutip pesan), dan sinyal audit per butir.
- **Set ini sekali pakai.** Setelah hasil evaluasi dilihat, setiap perubahan pada generator, prompt,
  retriever, parameter retrieval, chunking, atau indeks membuat ke-99 butir ini **data
  pengembangan**: tidak boleh lagi dipakai sebagai bukti mutu. Uji ulang dan adjudikasi harus selesai
  sebelum ada perubahan sistem.
- **Urutan yang diusulkan:**
  1. Pemilik proyek menyetujui atau mengubah rancangan ini; ambang di-commit.
  2. Tinjauan buta 7.1 dan uji ulang 7.2 (>= 27 Oktober), **sebelum** pemilik proyek melihat keluaran
     sistem per butir, agar uji ulang tidak terpengaruh jawaban sistem.
  3. Evaluasi 3 hari (bagian 5 dan 8).
  4. Adjudikasi 7.3.
  5. Laporan, lalu ingest antrean oleh pemilik proyek.

  *Alternatif:* evaluasi dijalankan sebelum 27 Oktober tetapi hasil per butir disegel (hanya agregat
  dilaporkan) sampai uji ulang selesai.

---

## 9. Garis besar langkah korektif (BELUM dibangun; hanya untuk menunjukkan cara memakai 49 negatif)

**Langkah korektif** = bila generator menjawab "belum ditemukan", sistem mencari ke situs cek fakta
lain, lalu menjawab hanya bila menemukan putusan eksplisit atas klaim yang sama.

- **Pencarian hanya lewat API pencarian web resmi** (judul, cuplikan, tautan), dibatasi ke daftar
  domain situs cek fakta. **Tidak mengambil isi halaman** dari situs yang menolak agen AI di
  robots.txt (Kompas, Tempo, Antara, Komdigi). *Ketegangan yang perlu diputuskan:* keputusan
  2026-09-21 untuk set uji v1 menyatakan judul dan URL hasil pencarian dari Kompas, Tempo, dan
  Komdigi pun tidak dipakai. Apakah cuplikan API pencarian dari situs-situs itu boleh dipakai di
  produk perlu keputusan tersendiri.
- **Hanya artikel dengan putusan eksplisit** (label vonis di judul atau cuplikan, mis. "[HOAKS]",
  "Cek Fakta: Tidak Benar ..."; dikenali dengan aturan, bukan LLM). Bila yang ditemukan hanya berita
  tanpa putusan, jawabannya tetap "belum ditemukan".
- **Tautan selalu dari metadata hasil pencarian**, tidak pernah dari LLM (Aturan Wajib #3); LLM hanya
  memilih indeks hasil, seperti generator memilih `article_id`.
- **Penilai kesamaan klaim** membandingkan pesan dengan judul dan cuplikan. Ini bagian tersulit, dan
  skor kemiripan tidak boleh menjadi penentunya (bagian 1).
- **Uji pada 49 butir negatif, dua kondisi:**
  1. **Tanpa Liputan6** di daftar domain: kondisi yang jujur. Ukuran: proporsi butir yang mendapat
     putusan eksplisit atas klaim yang sama (dinilai pemilik proyek secara buta dengan Aturan A/B),
     dan kecocokan palsu langkah korektif.
  2. **Dengan Liputan6**: pemeriksaan kewarasan saja. Sistem semestinya menemukan artikel sumbernya
     sendiri; bila tidak, pencarian atau penilainya rusak. Angkanya tidak boleh dilaporkan sebagai
     mutu.
- Positif yang sistemnya menolak secara palsu (6.1) juga melewati langkah korektif. Dicatat apakah
  langkah itu menghasilkan jawaban yang bertentangan dengan artikel TurnBackHoax sasaran.
- **Kuota pencarian dan kebijakan layanan API** diperiksa sebelum rancangan rinci, karena tier
  gratis bisa berubah seperti kuota LLM.
- Kriteria keberhasilan langkah korektif dikunci terpisah sebelum dibangun. Bila set 99 butir sudah
  terpakai untuk mengembangkannya, ia tidak sah lagi sebagai bukti (bagian 8), jadi uji akhirnya
  memerlukan sampel Liputan6 baru dari periode lain.

---

## 10. Yang menunggu keputusan pemilik proyek

1. Aturan kutipan K1/K2 dan perlakuan "dikeluarkan" (2.2).
2. Hasil utama gabungan 91 butir; per putaran sekunder (3).
3. Ambang positif (6.1), ambang kecocokan palsu (6.2), dan ambang kemunduran testset-v1 (6.3).
4. Rancangan uji ulang 20 P2 + 10 P1, tanggal paling cepat 27 Oktober, dan ambang kappa (7.2, 7.4).
5. Urutan langkah (8): uji ulang sebelum evaluasi, atau evaluasi dengan hasil disegel.
6. Pembagian 3 hari kuota (8).
7. Pemakaian cuplikan pencarian dari situs yang menolak agen AI (9).
