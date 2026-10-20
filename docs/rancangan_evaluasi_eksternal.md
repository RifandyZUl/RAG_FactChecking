# Rancangan evaluasi eksternal: 99 butir Liputan6 pada indeks produksi 1.532 artikel

**Status (2026-10-17): DISETUJUI PEMILIK PROYEK (bagian 10) DAN DIKUNCI SEBELUM PANGGILAN LLM PERTAMA.**
Rancangan disusun dan diusulkan Claude Code; keputusan dan dua penegasan ambang berasal dari pemilik
proyek. Audit jejak identik (bagian 7.1) dijalankan lebih dulu tanpa LLM maupun embedding, dengan
parameter yang di-commit sebelum dijalankan (`e7504fc`). Pemilihan butir sesi buta dan pembekuan
daftar butir di-commit sebelum evaluasi dimulai (bagian 8). **Hasil per butir tersegel sampai sesi
buta selesai.**

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

### 2.2 Aturan kutipan yang tidak memuat klaim (ditetapkan sebelum hasil apa pun dilihat; DISETUJUI 2026-10-17)

Dihitung dengan `candidates.trace_audit.words` (NFKC, huruf kecil, tautan berskema/`www.` dibuang,
tanda baca menjadi pemisah):

- **K1 -- kutipan kurang dari 5 kata setelah tautan dibuang:** 7 butir. Rinciannya: hanya tautan 5
  (P1-4, P1-19, P2-10, P2-11, P1-5), kosong 1 (P2-18; artikelnya tidak mengutip pesan), satu salam
  saja 1 (P2-46). **Ambang ini tidak peka:** ambang 3, 5, atau 8 kata menghasilkan 7 butir yang sama;
  butir berikutnya baru muncul pada 9 kata.
- **K2 -- kutipan berupa kalimat pengantar redaksi** (diakhiri titik dua, mis. "... berikut
  isinya:"): 1 butir (P2-34). Hanya satu butir di 99 yang diakhiri titik dua.
- **Perlakuan (DISETUJUI 2026-10-17): DIKELUARKAN dari analisis utama, tanpa diganti judul.** Alasannya:
  tautan saja atau salam tidak memuat klaim yang dapat dibandingkan, dan mengganti dengan judul
  menambah bias (2.1). Butir ini juga tidak dijalankan (hemat 24 panggilan). Jumlahnya dilaporkan per
  label: **positif 4** (P1-5, P2-18, P2-34, P2-46) dan **negatif 4** (P1-4, P1-19, P2-10, P2-11).
  **Keterbatasan:** pesan yang hanya berisi tautan adalah masukan pengguna yang nyata (5 dari 99
  kutipan di sampel ini); sistem tidak dirancang untuk itu (tidak mengambil isi tautan dan meng-embed
  teks URL apa adanya), dan evaluasi ini tidak mengukurnya. **Fitur masa depan (dicatat, BELUM
  dibangun):** pencocokan URL/domain deterministik dari pesan ke `claim_sources` artikel, tanpa LLM,
  dengan penyaringan domain yang sama seperti audit 7.1.
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
     adjudikasi buta (7.6). Hasilnya dicatat terpisah sebagai "cocok di luar daftar: sah / tidak
     sah" dan dilaporkan sebagai sensitivitas, bukan sebagai pengganti label.
  3. Bila artikelnya **di dalam daftar**, pemilik proyek sudah pernah menolaknya; ia tetap masuk
     adjudikasi buta (7.6) agar perlakuannya sama.
- **Empat butir ragu (P2-2, P2-14, P2-30 TIDAK ADA; P2-18 cocok).** P2-18 dikeluarkan oleh K1. Tiga
  sisanya: label utama dipakai apa adanya; sensitivitas dua arah seperti 11.6 (dihitung cocok /
  dihitung TIDAK ADA). Karena "cocok" pada butir ragu tidak menyebut artikel, pada arah "dihitung
  cocok" sasarannya adalah kandidat yang dipilih sistem bila ada di daftar kandidat butir itu.
- **Perbedaan aturan antar-putaran.** P1 dilabel dengan pedoman v1.0 (dua inkonsistensi tercatat,
  tanpa Narasi); P2 dengan Aturan A/B dan Narasi utuh.
  - **Hasil utama = gabungan 91 butir** (DISETUJUI 2026-10-17), dengan label final menurut 7.5.
  - **Pecahan wajib:** per putaran (P1: 20 positif / 27 negatif; P2: 22 / 22) dan, untuk positif,
    per selisih terbit **<= 30 hari (25 butir) vs > 30 hari (17 butir)**. Disajikan berdampingan dan
    **tanpa uji beda** (sama seperti 11.8 langkah 4).
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

## 6. Metrik dan ambang (DISETUJUI 2026-10-17; dikunci sebelum dijalankan)

Semua proporsi dengan interval Wilson 95%. Keputusan per butir = **modus 3 run** (seperti Versi 1);
ketidakbulatan antar-run dilaporkan terpisah. Butir "tak terjawab" (galat API setelah semua
percobaan) dilaporkan sendiri dan tidak dihitung benar maupun salah.

### 6.1 Metrik positif (42 butir)

- **Recall@3 bersyarat** (retrieval saja; bagian 4).
- **Ketepatan jawaban cocok** = modus "ditemukan" dengan id sasaran.
- Dipecah: penolakan palsu (modus "belum ditemukan") dan artikel salah (ditemukan, id lain).
- **Ambang (DISETUJUI 2026-10-17). Patokan: 60% pada batas Wilson 95%.** Memadai bila batas
  **bawah** Wilson >= 60% (pada 42 butir: >= 32/42); buruk bila batas **atas** < 60% (<= 18/42); di
  antaranya (19-31/42) tidak konklusif. Ambang berlaku pada **ke-42 butir sesuai label emas**,
  termasuk pasangan lintas gelombang. Ambang positif ini **tidak** menjadi gerbang langkah korektif;
  ia menilai apakah demo layak diklaim menemukan klaim yang ada.
- **Laporan wajib memisahkan kegagalan yang berupa penolakan pasangan lintas gelombang** (strata
  > 30 hari, bagian 3), karena prompt generator yang terkunci tidak mengenal Aturan A: penolakan itu
  dilaporkan sebagai jumlah tersendiri di samping kegagalan lain, tanpa mengubah hitungan ambang.

### 6.2 Metrik negatif (49 butir) -- dilaporkan paling menonjol

- **Tingkat kecocokan palsu** = modus "ditemukan" (artikel apa pun) / 49. Dipecah: artikel di dalam
  daftar kandidat vs di luar (3).
- **Tingkat penolakan benar** = modus "belum ditemukan" / 49 (= 1 - kecocokan palsu bila tidak ada
  yang tak terjawab).
- **Ambang kecocokan palsu (DISETUJUI 2026-10-17; gerbang pemicu CRAG).** **"Lulus" berarti tidak
  terbukti buruk, BUKAN terbukti aman:** pada batas lulus, batas atas Wilson masih sekitar 19%, jadi
  data tetap sejalan dengan hampir satu dari lima klaim negatif tercocokkan palsu.

  | Kategori | Syarat | Pada 49 butir |
  | --- | --- | --- |
  | **Lulus** (= tidak terbukti buruk) | proporsi <= 10% DAN batas atas Wilson <= 20% | <= 4/49 (8,2% [3,2%; 19,2%]) |
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
- **Ambang (DISETUJUI 2026-10-17):** "mundur" bila kemunduran bersih pada 44 butir non-batas >= 3, yaitu (benar di
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
- **Ketujuh butir ini ditinjau ulang dalam sesi buta gabungan (7.2)**, tanpa penanda dan tanpa
  diberi tahu sinyalnya. Hasilnya dilaporkan terpisah sebagai hasil audit (berubah / tetap per butir,
  lalu rincian sinyal dan presisi per sinyal setelah sesi buta selesai) dan **tidak** ikut kappa,
  karena butirnya dipilih tidak acak.

### 7.2 Sesi buta gabungan (DISETUJUI 2026-10-17)

- **Isi: 37 butir dalam satu berkas** = 30 butir uji ulang acak + 7 butir audit (P1-10, P1-20, P1-29,
  P1-30, P1-38, P1-45, P2-2), dicampur acak **tanpa penanda** mana butir audit dan mana butir uji
  ulang.
- **Pemilihan uji ulang** (dikunci dan di-commit sebelum panggilan LLM pertama, tidak bergantung pada
  hasil evaluasi): `python -m candidates.blind_session --select` -> `testset/eksternal_sesi_buta_pilihan.json`.
  Benih **20261027**; **20 butir P2** (konsistensi, aturan sama) lalu **10 butir P1** (dilabel ulang
  dengan Aturan A/B; efek pergantian aturan). Dikecualikan dari kolam acak: butir 1-5 P1, 15 butir
  P1 yang pernah ditandai tidak konsisten, dan ketujuh butir audit. Kolam: P1 26, P2 48.
- **Berkas:** dibuat **paling cepat 27 Oktober 2026** (dua minggu setelah pelabelan terakhir 13
  Oktober; **diubah menjadi 20 Oktober, lihat penyimpangan di bawah**). Format sama dengan `konfirmasi_49` (blok per butir, Narasi utuh, tinggi baris disetel,
  hanya sel masukan terbuka). Label lama, catatan, dan tanda ragu disembunyikan; urutan butir dan
  urutan kandidat diacak; butir dinomori ulang; peta nomor -> butir asli disimpan terpisah dan tidak
  dibuka sampai pemilik proyek selesai.
- **Keterbatasan yang diterima:** butir P1 pernah dilihat sebelumnya (ingatan bisa menaikkan
  kesepakatan), dan dengan 30 butir interval kappa lebar. **Tambahan karena penyimpangan di bawah:**
  jeda 7 hari untuk butir P2 menambah risiko pemilik proyek masih ingat label lama, sehingga kappa
  (terutama kappa P2, ukuran konsistensi) bisa terlalu tinggi; jeda untuk butir P1 di atas 11 hari
  (pelabelan P1 selesai paling lambat 8 Oktober). **Tambahan 2026-10-20 (dicatat sebelum sesi
  diisi):** butir P1 di sesi ini ditampilkan dengan **Narasi TurnBackHoax utuh**, padahal pada
  pelabelan pertama (`konfirmasi_50`) pemilik proyek melabelnya hanya dari judul dan Kesimpulan. Jadi
  kesepakatan pada butir P1 mengukur **gabungan** efek pergantian aturan (A/B) dan bukti yang lebih
  lengkap, bukan konsistensi murni; kedua efek itu tidak dapat dipisahkan dengan rancangan ini.
- **PENYIMPANGAN RANCANGAN (diputuskan pemilik proyek 2026-10-19, dicatat SEBELUM berkas sesi buta
  dibuat; hasil evaluasi MASIH TERSEGEL saat keputusan diambil -- belum ada metrik atau hasil per butir
  yang dilihat siapa pun):**
  - *Parameter lama:* jeda uji ulang minimal **dua minggu** setelah pelabelan terakhir (13 Oktober) ->
    berkas sesi buta dibuat paling cepat **27 Oktober 2026**.
  - *Parameter baru:* jeda minimal **7 hari** setelah pelabelan terakhir -> berkas sesi buta dibuat
    **20 Oktober 2026**.
  - *Alasan:* murni jadwal; pemilik proyek ingin proyek ini selesai sebagai portofolio sebelum akhir
    Oktober. Tidak ada alasan yang berasal dari hasil evaluasi.
  - *Yang tidak berubah:* pemilihan butir tetap yang sudah di-commit di `fa7464c`
    (`testset/eksternal_sesi_buta_pilihan.json`, benih 20261027; catatan "paling cepat 2026-10-27" di
    berkas itu adalah riwayat dan digantikan penyimpangan ini), isi 37 butir, format, dan ambang kappa
    7.4.
- **Berkas sesi buta DIBUAT 2026-10-20 05:31 UTC, SEBELUM diisi** (`python -m
  candidates.blind_workbook --make`; folder `data/candidates/sesi_buta_eksternal/` di-gitignore, jadi
  hash ini, yang ikut di-commit, adalah bukti bertanggal bahwa templat dan pemetaan butir tidak berubah
  setelah pengisian). 37 butir, 243 baris kandidat; pilihan = blob `a0bfd101...` di `fa7464c`.
  `--read` mencocokkan ulang ketiga hash ini dan BERHENTI bila ada yang berbeda.

  | Berkas | SHA-256 |
  | --- | --- |
  | `sesi_buta_37.xlsx` (templat kosong) | `ba5f6f8a7886f6b880c340132e510053346c54551c41409628a5a0ef5b3ca6c1` |
  | `kunci_sesi_buta.json` (peta nomor sesi -> butir asli) | `75263881065e111f5d9430046620060c30a88fe5e6e5816e4d94dc6937bd9d17` |
  | `sidik_jari_templat_sesi_buta.json` | `3efbfa953f888bc8412d56e967abbd4ff03e11aa12a00ee1dd52ae3e791b45c4` |

- **Kejadian 2026-10-20: berkas terisi pertama ditolak, dikoreksi, dan versi pertamanya tertimpa
  (dicatat SEBELUM segel dibuka; tidak ada hasil sistem yang dilihat siapa pun).**
  - *Penyerahan pertama:* `sesi_buta_37_terisi.xlsx`, SHA-256
    `63ed18c7dc1862480bede3c99b3af877c70beeb790678142f696a76cca8bf5f6` (disimpan Microsoft Excel
    13:35:36 UTC; commit `9868b17` sudah di origin sejak 05:53:52 UTC). `--read` menolaknya (kode keluar
    1, tidak ada yang dipetakan): **id `32218` tidak ada di daftar kandidat butir sesi 30**
    (kandidatnya `32118`, `29971`, `32111`, `29477`, `32092`, `32007`). Pemeriksaan lain pada jalan itu:
    sel di luar sel masukan sama dengan templat, kunci tidak berubah, templat masih seperti saat
    dibuat; butir 30 satu-satunya masalah.
  - *Koreksi:* nilai lama `32218`, nilai baru `32118`. Menurut pernyataan pemilik proyek ini **koreksi
    salah ketik yang ia lakukan sendiri, bukan penilaian ulang**, dan butir lain tidak diubah atau
    dinilai ulang. Pernyataan itu **tidak dapat dibuktikan dari berkas**.
  - *Versi pertama tertimpa:* koreksi disimpan ke nama yang sama, mengikuti instruksi yang diterima
    pemilik proyek; instruksi itu keliru karena bertentangan dengan permintaan perbandingan sel demi
    sel. `--read` saat itu tidak menyalin berkas, Claude Code tidak membuat salinan, dan Previous
    Versions Windows tidak menyediakan versi lama. **Versi pertama tidak dapat dipulihkan.**
  - *Versi koreksi:* `sesi_buta_37_terisi.xlsx`, SHA-256
    `29b602f946ad401f353611c4f75b21da5942bb33d9f4b8da32f9f2d1d2d85961` (98.023 byte, disimpan 14:51:53
    UTC); salinan byte di `arsip_baca/20261020T153235684685Z_29b602f946ad_sesi_buta_37_terisi.xlsx`
    (hash sama).
  - *Catatan butir 30* di berkas berbunyi "Lembaga dan tokoh yang disebut sama" dan **tidak menyebut
    koreksi**. Pemilik proyek sempat menyatakan koreksinya dicatat di kolom catatan; pemeriksaan
    berkas (kolom catatan dan seluruh sel) menunjukkan tidak, dan pemilik proyek membenarkannya. Jejak
    koreksi hanya ada di bagian ini.
  - **Terbukti:** dari `--read` pertama, sel di luar sel masukan sama dengan templat dan satu-satunya
    masalah adalah butir 30 = `32218`; dari versi koreksi, butir 30 = `32118`. **Tidak terbukti:**
    bahwa KEPUTUSAN, ragu, dan catatan 36 butir lain tidak berubah antara kedua versi; itu hanya
    bersandar pada pernyataan pemilik proyek.
  - Koreksi dilakukan saat segel masih tertutup, jadi perubahan apa pun tidak mungkin dipengaruhi hasil
    sistem.
  - **Aturan sejak kejadian ini:** berkas yang sudah diserahkan tidak pernah ditimpa; koreksi disimpan
    sebagai berkas baru berakhiran `_v2`, `_v3`, dan seterusnya (`--read --berkas ...`). `--read` kini
    menyalin berkas terisi beserta hash-nya ke `arsip_baca/` (log `arsip_baca.jsonl`) **sebelum
    validasi apa pun**, dan berhenti bila nama yang sama pernah dibaca dengan hash lain.

### 7.3 Kappa uji ulang

- Dihitung **hanya dari 30 butir acak**. Ketujuh butir audit tidak ikut.
- **Dua tingkat**, masing-masing dengan interval 95% bootstrap persentil (10.000 ulangan, benih
  20261027): (1) **biner** (cocok vs TIDAK ADA); (2) **kesamaan id persis** (kategori = id artikel
  atau TIDAK ADA).
- Dilaporkan juga (deskriptif): kappa P2 saja (konsistensi) dan P1 saja (efek aturan), dan
  perpindahan per arah.

### 7.4 Ambang kappa (DISETUJUI 2026-10-17; dibaca dari estimasi titik kappa biner 30 butir, interval dilaporkan)

| Kappa | Tindakan |
| --- | --- |
| >= 0,80 | Label dipakai apa adanya. |
| 0,60-0,79 | Hasil tetap memakai label final (7.5), tetapi setiap metrik dilaporkan juga dengan butir yang berubah pada uji ulang dibalik ke dua arah. Kategori "lulus" hanya dinyatakan bila lulus pada kedua arah. |
| < 0,60 | Set ini **tidak dipakai sebagai gerbang** apa pun (termasuk pemicu CRAG); hasil evaluasi hanya deskriptif, dan pedoman perlu diperjelas sebelum set baru dibuat. |

Kappa id persis dilaporkan berdampingan; bila ia jauh di bawah kappa biner, laporan menyebut bahwa
ketidakkonsistenan terletak pada pemilihan artikel, bukan pada ada/tidaknya pasangan.

### 7.5 Label final untuk metrik utama

- **Label final = label awal, KECUALI butir audit yang labelnya berubah di sesi buta**: untuk butir
  itu dipakai label sesi buta, karena perubahannya dipicu mekanisme yang tidak melihat jawaban
  sistem.
- **Metrik dengan label awal** dilaporkan sebagai sensitivitas.
- Hasil uji ulang 30 butir **tidak** mengganti label; ia hanya mengukur konsistensi (7.3-7.4).

### 7.6 Adjudikasi buta setelah buka segel

- **Hanya butir yang keputusan modus sistemnya berbeda dari label final** (penolakan palsu, artikel
  salah, kecocokan palsu).
- Disajikan sebagai **dua opsi dalam urutan acak**, tanpa keterangan mana dari sistem: opsi label dan
  opsi sistem, masing-masing dengan judul, Narasi utuh, dan Kesimpulan. Aturan A/B berlaku.
- **Perubahan dari adjudikasi dicatat terpisah dan TIDAK masuk metrik utama.** Bias yang disadari:
  adjudikasi hanya meninjau ulang butir yang tidak sepakat dengan sistem, jadi ia hanya bisa menggeser
  hasil ke arah sistem.

---

## 8. Pelaksanaan

- **Generator, prompt, dan retriever terkunci.** `src/generator.py` = sidik jari terkunci
  `e5a5ba5a...` (sudah dicek sama, 2026-10-17); model `gemini-3.5-flash-lite`, thinking `medium`,
  tanpa override `.env`. Hash `src/retriever.py` dicatat sekarang dan diperiksa sebelum setiap hari
  evaluasi: `68321aed...` (normalisasi CRLF->LF, UTF-8). Juga `src/chunker.py` `6d9de5ce...`. Uji
  kunci (`tests/test_testset_locks.py`) wajib lolos sebelum setiap hari evaluasi.
- **3 run, keputusan modus**, urutan butir diacak per run dengan benih **2026101701-03**.
- **Skrip** `evaluation.external_eval` (uji `tests/test_external_eval.py`): `--freeze` membekukan
  daftar 99 butir (label awal, alasan dikeluarkan, hash kutipan; tanpa teks), sidik jari indeks, dan
  hash berkas ke `testset/eksternal_butir.json`; `--set liputan6|v1 --run N` menjalankan satu run;
  hasil mentah per (run, butir) ke `data/external_eval_<set>_<model>.jsonl` (lokal), lanjut dari yang
  terakhir, berhenti bila kuota habis atau 2 butir beruntun tak terjawab. Sebelum panggilan pertama
  setiap run ia memeriksa daftar butir, sidik jari indeks, `ef_search`, hash berkas, dan
  model/thinking; satu saja berbeda -> tidak dimulai. testset-v1 memakai benih run Versi 1 dan berkas
  keluaran sendiri (tidak menyentuh hasil arsip). Analisis di skrip terpisah, ditulis sebelum segel
  dibuka, tanpa panggilan API.
- **Segel.** Layar dan `--status` hanya menampilkan status teknis (jumlah panggilan, galat, 429, butir
  yang diulang). Selama segel, yang dilaporkan kepada pemilik proyek hanya status teknis, sidik jari
  indeks, dan hasil `retriever_exactness`; **tidak ada angka metrik dan tidak ada hasil per butir**
  sampai sesi buta selesai. Claude Code juga tidak membaca keputusan per butir dari berkas hasil
  selama segel.
- **Kuota (RPD 500, berbagi dengan demo):**

  | | Butir | Panggilan minimum (3 run) | Terburuk dengan ulang format |
  | --- | --- | --- | --- |
  | Liputan6 | 91 | 273 | 546 |
  | testset-v1 | 54 | 162 | 324 |
  | **Jumlah** | | **435** | 870 |

  **DISETUJUI: 3 hari, satu run kedua set per hari** (145 panggilan minimum, 290 terburuk dengan ulang
  format), menyisakan >= 210 per hari untuk ulang butir dan demo. Pemeriksaan anggaran membandingkan
  kebutuhan minimum (1 panggilan per butir) dengan sisa kuota; kasus terburuk hanya dilaporkan, dan
  buku besar kuota tetap menjadi penghenti keras saat sisa habis (proses berhenti dan dilanjutkan
  setelah reset). *Koreksi atas versi pertama rancangan ini:* versi itu keliru menyebut bahwa
  pemeriksaan anggaran `testset_eval` menolak berdasarkan kasus terburuk.
- **Rekonsiliasi buku besar hari 1 (2026-10-17): 152 = 98 + 54, selisih 6 dari percobaan ulang
  koneksi di dalam penyedia.** Buku besar (`data/quota_ledger.json`) hanya menyimpan hitungan per
  hari, tanpa asal, tetapi ia bertambah satu pada **setiap percobaan** permintaan
  (`GeminiProvider._before_call`, dipanggil di tiap putaran `MAX_ATTEMPTS` = 4), sedangkan "panggilan"
  di berkas hasil adalah satu `CallRecord` per panggilan generator, dengan bidang `attempts`. Dari
  bidang teknis berkas hasil (tanpa membaca keputusan): Liputan6 92 panggilan dengan jumlah
  `attempts` **98** (tiga panggilan berulang: 2, 4, dan 3 percobaan; yang 4 percobaan gagal
  `APIConnectionError` lalu butirnya diulang dan selesai); testset-v1 54 panggilan, `attempts` 54.
  98 + 54 = 152, sama persis dengan buku besar. Enam peringatan `[retry i/3] APIConnectionError` di
  `data/llm_calls.log` (15.09.47, 15.15.25, 15.15.41, 15.15.46, 15.16.43, 15.18.13 WIB) cocok dengan
  1 + 3 + 2 percobaan ulang itu, semuanya selama run Liputan6 (proses testset-v1 baru mulai 15.24).
  **Uji kunci dan pemeriksaan sebelum run tidak memanggil API** (`tests/test_testset_locks.py` hanya
  mengimpor konstanta `DEFAULT_GEMINI_MODEL`; `index_check`, `retriever_exactness`, dan pemeriksaan
  awal `external_eval` tanpa LLM), jadi biayanya 0 panggilan per hari. Karena asal selisih dapat
  dipastikan dari data yang ada, penanda asal **tidak** ditambahkan ke buku besar di tengah evaluasi.
- **Perkiraan kuota run 2 dan run 3:** minimum 145 permintaan per hari (91 + 54). Hari 1 butuh 152
  (beban percobaan ulang ~4%). Batas atas praktis bila setiap butir gagal format sekali: 290, ditambah
  percobaan ulang koneksi yang tidak dapat diperkirakan (maksimal 4 percobaan per panggilan). Sisa
  kuota per hari tanpa pemakaian demo: ~348 pada beban seperti hari 1, >= 210 pada batas atas
  ulang format; demo berbagi kuota yang sama.
- **Status pelaksanaan (dicatat 2026-10-19; status teknis saja, hasil tetap tersegel):**
  - **Run 1 dan run 2 lengkap untuk kedua set** (Liputan6 91/91, testset-v1 54/54 per run). Run 2 tidak
    dijalankan 18 Oktober; ia dijalankan 2026-10-19 pukul 12.58-13.24 WIB, seluruhnya di jendela kuota
    yang dimulai 18 Oktober 14.00 WIB (tidak ada butir yang menyeberang jendela). Buku besar run 2:
    148 = 91 (Liputan6) + 57 (testset-v1); selisih 3 terhadap 145 panggilan = tiga percobaan ulang karena
    503 "high demand" dari server (13.12, 13.16, 13.17 WIB), masing-masing berhasil pada percobaan kedua;
    0 galat butir, 0 429, 0 butir diulang.
  - **Run 3 terhenti setelah 2 butir Liputan6** (mulai 14.02 WIB, setelah pemeriksaan sebelum run lolos)
    karena Claude Code menghentikan proses latarnya saat memori sistem rendah -- **bukan galat
    evaluasi**. Butir ke-3 sempat dikirim ke model (14.05.58 WIB, tercatat di buku besar: 3 percobaan vs 2
    hasil), tetapi jawabannya tidak tersimpan dan tidak pernah dilihat; berkas hasil berakhir utuh pada
    butir ke-2. Butir itu dipanggil ulang saat run dilanjutkan (lanjut-dari-terakhir). Run 3 diselesaikan
    di luar Claude Code.
  - **Run 3 DISELESAIKAN 2026-10-19 malam di luar Claude Code** (PowerShell terpisah, dijalankan pemilik
    proyek; log `data/external_eval_run3_lanjut_20261019_1920.log`; keenam langkah kode keluar 0): uji kunci
    6/6, `retriever_exactness` 0/64 kueri berbeda, anggaran kedua set, lalu run 3 Liputan6 (19.22-19.58 WIB,
    89 butir sisa) dan run 3 testset-v1 (19.58-20.07 WIB). Pemeriksaan awal di dalam run (daftar butir,
    sidik jari indeks, `ef_search`, hash berkas terkunci, model/thinking) **lolos untuk kedua set**.
    - Run 3 Liputan6: 91/91 butir (2 dari proses siang + 89 dari proses malam), 91 panggilan, 92 percobaan
      (satu percobaan ulang `APIConnectionError` pukul 19.54.58 WIB, berhasil pada percobaan kedua), 0
      galat butir, 0 429, 0 butir diulang. Run 3 testset-v1: 54/54, 54 panggilan, 54 percobaan, 0 galat,
      0 429, 0 butir diulang.
    - **Buku besar jendela 19 Okt: 147 = 93 (Liputan6) + 54 (testset-v1).** Menurut penanda asal per
      proses: proses siang (pid 9824) 3 percobaan pertama, 14.05.33-14.05.58 WIB = 2 butir tersimpan + 1
      permintaan butir ke-3 yang jawabannya tidak tersimpan; proses malam (pid 14844) 90 = 89 percobaan
      pertama + 1 percobaan ulang; testset-v1 (pid 12424) 54. Jadi 93 - 92 percobaan di berkas hasil = 1 =
      permintaan butir ke-3 yang terputus, yang dipanggil ulang oleh proses malam. Tidak ada selisih lain.
  - **Ketiga run lengkap untuk kedua set** (Liputan6 91 butir unik per run, testset-v1 54 per run, semua
    berstatus selesai); tidak ada butir yang hasilnya hilang di run mana pun.
  - **Rincian "gagal 1" di laporan hari pertama:** satu panggilan generator gagal setelah 4 percobaan
    (`APIConnectionError`); butirnya diulang dan selesai. Seluruhnya ada **6 percobaan ulang karena galat
    koneksi** pada run Liputan6 (1 + 3 + 2), semuanya tercatat di buku besar; **tidak ada butir yang
    kehilangan jawaban**.
  - **Penanda asal buku besar ditambahkan sebelum run 2** (commit `cde7ce7`): setiap penambahan juga
    ditulis ke `data/quota_ledger_events.jsonl` (waktu UTC, proses asal, pid, nomor percobaan). Hanya
    `src/llm/ledger.py` dan satu baris di `src/llm/gemini.py`; berkas terkunci (generator, retriever,
    chunker) dan prompt tidak tersentuh, hash terkunci tetap lolos pemeriksaan awal run 2 dan run 3.
    (Ini menggantikan keputusan hari 1 untuk tidak menambah penanda di tengah evaluasi.)
- **Yang boleh dipublikasikan (di-commit):** metrik agregat dan intervalnya; tabel per butir berisi
  nomor butir, id artikel Liputan6 (angka), label emas (id TurnBackHoax / TIDAK ADA), keputusan modus
  sistem, dan id artikel jawaban. **Tidak** dipublikasikan: kutipan pesan, judul Liputan6, Narasi,
  keluaran mentah dan alasan LLM (bisa mengutip pesan), dan sinyal audit per butir.
- **Set ini sekali pakai.** Setelah hasil evaluasi dilihat, setiap perubahan pada generator, prompt,
  retriever, parameter retrieval, chunking, atau indeks membuat ke-99 butir ini **data
  pengembangan**: tidak boleh lagi dipakai sebagai bukti mutu. Uji ulang dan adjudikasi harus selesai
  sebelum ada perubahan sistem.
- **Urutan (DISETUJUI 2026-10-17):**
  1. Rancangan diperbarui, pemilihan sesi buta (`--select`) dan pembekuan butir (`--freeze`)
     di-commit **sebelum panggilan LLM pertama**.
  2. Evaluasi 3 hari dengan hasil tersegel (hari pertama: 2026-10-17).
  3. Sesi buta gabungan (7.2), berkas dibuat paling cepat 27 Oktober 2026 (**penyimpangan 2026-10-19:
     20 Oktober**, lihat 7.2).
  4. Kappa (7.3-7.4) dan label final (7.5), lalu **buka segel** dan hitung metrik.
  5. Adjudikasi buta (7.6), laporan, lalu ingest antrean oleh pemilik proyek.

---

## 9. Garis besar langkah korektif (BELUM dibangun; hanya untuk menunjukkan cara memakai 49 negatif)

**Langkah korektif** = bila generator menjawab "belum ditemukan", sistem mencari ke situs cek fakta
lain, lalu menjawab hanya bila menemukan putusan eksplisit atas klaim yang sama.

- **Pencarian hanya lewat API pencarian web resmi** (judul, cuplikan, tautan), dibatasi ke daftar
  domain situs cek fakta. **Kompas, Tempo, Antara, dan Komdigi tidak dipakai sama sekali**: judul,
  URL, dan cuplikannya tidak dipakai walaupun berasal dari API pencarian, dan isi halamannya tidak
  diambil (keputusan 2026-09-21 tetap berlaku; ditegaskan pemilik proyek 2026-10-17). Domain itu
  dikeluarkan dari daftar pencarian **dan** hasil yang berdomain itu dibuang sebelum sampai ke LLM.
  Keputusan ini **dapat ditinjau ulang saat langkah korektif benar-benar dibangun**.
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

## 10. Keputusan pemilik proyek (2026-10-17)

1. **Kutipan pendek:** K1 dan K2 disetujui; delapan butir dikeluarkan tanpa diganti judul; tersisa 91
   butir (42 positif, 49 negatif). Keterbatasan pesan berisi tautan saja dan fitur masa depan
   pencocokan URL/domain deterministik dicatat (2.2).
2. **Hasil utama:** gabungan 91 butir, dengan pecahan per putaran dan per selisih terbit <= 30 / > 30
   hari (3).
3. **Ambang disetujui** dengan dua penegasan: "lulus" kecocokan palsu = tidak terbukti buruk, bukan
   terbukti aman (6.2); ambang positif berlaku pada 42 butir sesuai label emas, dengan kegagalan
   berupa penolakan pasangan lintas gelombang dipisahkan di laporan (6.1). Patokan ambang positif =
   60% pada batas Wilson.
4. **Urutan:** evaluasi sekarang dengan hasil tersegel, lalu satu sesi buta gabungan, lalu buka segel
   (7.2-7.6, 8). Kappa dari 30 butir acak saja, dua tingkat, ambang dari estimasi titik. Label final
   = label sesi buta hanya untuk butir audit yang berubah; label awal sebagai sensitivitas; adjudikasi
   dicatat terpisah.
5. **Kuota 3 hari disetujui.**
6. **Langkah korektif:** Kompas, Tempo, Antara, dan Komdigi tidak dipakai sama sekali, termasuk
   lewat API pencarian; dapat ditinjau ulang saat dibangun (9).
