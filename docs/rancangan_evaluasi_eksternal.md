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

### 7.7 Hasil keandalan label dan label final (2026-10-20, dihitung dan di-commit SEBELUM segel dibuka)

Alat: `python -m evaluation.external_analysis --keandalan` lalu `--label-final` (uji
`tests/test_external_analysis.py`; fungsi keduanya tidak membaca berkas hasil sistem, dijaga uji AST).
Masukan: `hasil_sesi_buta.json` (dari `--read` atas `sesi_buta_37_terisi.xlsx` `29b602f9...`, 2026-10-20
15:41 UTC; 37/37 terbaca sah) dan label awal `testset/eksternal_butir.json`. Sesi diisi pemilik
proyek sendiri, tanpa AI.

**Uji ulang 30 butir acak** (kappa Cohen; interval 95% bootstrap persentil, 10.000 ulangan, benih
20261027):

| Kelompok | n | Sepakat | Kappa biner [CI95] | Kappa id persis [CI95] | Berubah (arah) |
| --- | --- | --- | --- | --- | --- |
| Gabungan | 30 | 25 | **0,6341** [0,3077; 0,9112] | 0,7070 [0,4161; 0,9213] | 5: cocok -> TIDAK ADA 3, TIDAK ADA -> cocok 2, id lain 0 |
| Putaran 2 | 20 | 17 | 0,6809 [0,2857; 1,0] | 0,7479 [0,4059; 1,0] | 3: cocok -> TIDAK ADA 2 (P2-4, P2-46), TIDAK ADA -> cocok 1 (P2-3) |
| Putaran 1 | 10 | 8 | 0,5238 [-0,1538; 1,0] | 0,5918 [-0,0714; 1,0] | 2: cocok -> TIDAK ADA 1 (P1-31), TIDAK ADA -> cocok 1 (P1-16) |

- Putaran 1: 56 dari 10.000 ulangan bootstrap tidak terdefinisi (satu kategori saja) dan dibuang.
- **Tidak ada butir yang berpindah ke id lain**: kelima perubahan semuanya ada/tidaknya pasangan. Kappa
  id persis lebih tinggi dari kappa biner hanya karena kategori id lebih banyak (kesepakatan peluang
  lebih rendah), bukan karena pemilihan artikel lebih konsisten daripada keputusan ada/tidaknya.
- Butir yang ditandai ragu di sesi (uji ulang): P1-23, P2-3, P2-10, P2-46. Dua dari lima yang berubah
  (P2-3, P2-46) ditandai ragu.
- **Kappa putaran 1 bukan ukuran konsistensi murni**: ia mengukur gabungan pergantian aturan (v1.0 ->
  A/B) dan bukti yang lebih lengkap (Narasi utuh), lihat 7.2; dengan 10 butir intervalnya mencakup 0.
- **Ambang 7.4 diterapkan apa adanya:** dasar terkunci = estimasi titik kappa biner 30 butir = 0,6341 ->
  **kategori 0,60-0,79**: label final tetap dipakai, setiap metrik dilaporkan juga dengan kelima butir
  yang berubah dibalik ke dua arah, dan "lulus" hanya dinyatakan bila lulus pada kedua arah. Batas bawah
  interval kedua kappa di bawah 0,60, jadi kategori ini sendiri tidak pasti.
- **Ketidaksesuaian perintah dengan rancangan (dikoreksi pemilik proyek 2026-10-21, setelah hasil
  dilihat):** perintah pelaksanaan 2026-10-20 meminta ambang diterapkan pada "kappa putaran 2", padahal
  yang dikunci di 7.4 adalah estimasi titik kappa biner 30 butir. **Yang berlaku adalah 7.4 (30 butir,
  0,6341).** Kappa biner putaran 2 (0,6809) jatuh di kategori yang sama (0,60-0,79), jadi tindakan dan
  seluruh hasil di bagian 11 tidak berubah oleh ketidaksesuaian ini.
- Hasil uji ulang **tidak mengubah label** (7.5).

**Tujuh butir audit** (tidak ikut kappa; sinyal dibuka setelah keputusan sesi tercatat):

| Butir | Label awal | Sesi buta | Kandidat berjejak (7.1) | Sinyal | Sesi = kandidat berjejak |
| --- | --- | --- | --- | --- | --- |
| P1-10 | TIDAK ADA | 36546 | 36546 | 6 rangkaian 8 kata sama, domain 0 | ya |
| P1-20 | TIDAK ADA | 32039 | 32039 | 33 rangkaian, domain 0 | ya |
| P1-29 | TIDAK ADA | 35963 | 35963 | 45 rangkaian, domain 0 | ya |
| P1-30 | TIDAK ADA | TIDAK ADA | 31092 | 4 rangkaian, domain 0 | - |
| P1-38 | TIDAK ADA | 35849 | 35849 | 32 rangkaian, domain 0 | ya |
| P1-45 | TIDAK ADA | TIDAK ADA | 33308 | 3 rangkaian, domain 0 | - |
| P2-2 | TIDAK ADA (ragu) | TIDAK ADA (ragu) | 32765 | 4 rangkaian, domain 0 | - |

- **4 dari 7 berubah dari TIDAK ADA menjadi cocok, dan keempatnya memilih tepat artikel yang ditunjuk
  jejak identik.** Ketiga yang tetap TIDAK ADA adalah yang sinyalnya paling lemah (3-4 rangkaian).
  Ketujuhnya berjejak lewat rangkaian kata saja; sinyal domain 0 pada semuanya.
- Keempat yang berubah semuanya butir **putaran 1** (dulu dilabel tanpa Narasi; kini Narasi utuh
  ditampilkan). Jadi perubahan ini konsisten dengan "bukti yang lebih lengkap" -- pada P1 penyebabnya
  tidak dapat dipisahkan dari pergantian aturan. P1-20 dan P1-29 juga termasuk 15 butir P1 yang dulu
  ditandai tidak konsisten (kelompok "ditolak, diragukan").
- Bias yang disadari: butir audit dipilih justru karena berjejak, dan pemilik proyek tidak diberi tahu
  sinyalnya, tetapi tahu bahwa ada butir audit di sesi.

**Label final (7.5)** = label awal, kecuali **P1-10 -> 36546, P1-20 -> 32039, P1-29 -> 35963,
P1-38 -> 35849** (dari TIDAK ADA; selisih terbit 36, 2, 4, -2 hari: satu > 30 hari). Akibatnya butir
analisis menjadi **46 positif (P1 24, P2 22) dan 45 negatif (P1 23, P2 22)**, bukan 42/49. Label awal
disimpan berdampingan di berkas yang sama untuk sensitivitas.

- Berkas: `data/candidates/sesi_buta_eksternal/label_final.json` (lokal, di-gitignore), **SHA-256
  `c24008d1cea343c037889b76001e3eeffb6617a5cbc12d5dd9f98a15f7dd28da`**; ia mencatat hash
  `eksternal_butir.json` (`87e2ad83...`) dan `hasil_sesi_buta.json` (`fdfb2113...`). Hash ini juga
  ditulis di `external_analysis.FINAL_LABELS_SHA256`; `--metrik` menolak membuka segel bila berkas
  berbeda.
- **Ambang pada n yang baru (dihitung dari aturan Wilson 6.1/6.2 yang sama, sebelum segel dibuka):**
  positif 46 butir: memadai >= 35/46, buruk <= 21/46, tidak konklusif 22-34. Kecocokan palsu 45 butir:
  **lulus <= 3/45** (4/45 = 8,9% tetapi batas atas Wilson > 20%), **gugur >= 9/45**, tidak konklusif 4-8.
  Aturannya tidak berubah; hitungan "pada 49 butir" di 6.2 hanya contoh untuk n = 49.
- **Kode analisis metrik (bagian 6, sensitivitas, kemunduran, kepatuhan) ditulis dan di-commit
  bersama catatan ini, sebelum segel dibuka** (`external_analysis.py`).

### 7.8 Berkas adjudikasi buta (DIBUAT 2026-10-20 16:00 UTC, SEBELUM diisi; dibaca 2026-10-21, hasil di 11.9)

- Alat: `python -m candidates.adjudication_workbook --make` (uji `tests/test_adjudication_workbook.py`).
  Isi: **20 butir** = semua butir analisis yang keputusan modus sistemnya berbeda dari label final:
  9 penolakan palsu, 10 kecocokan palsu, 1 artikel salah; 21 baris artikel.
- Format dan proteksi sama dengan berkas sesi (`gap_blocks.write_workbook`: blok per butir, judul,
  tanggal, dan kutipan Liputan6, Narasi utuh, tinggi baris disetel, hanya sel masukan terbuka, Rekap
  rumus saja, petunjuk memuat aturan A dan B persis seperti sesi). Dua opsi per butir dalam urutan
  acak tanpa keterangan asal; opsi "tidak ada yang cocok" tidak berupa baris, jadi butir dengan satu
  artikel berarti opsi lainnya TIDAK ADA (berlaku sama untuk penolakan palsu dan kecocokan palsu, jadi
  jumlah artikel tidak membocorkan sisi sistem). Urutan butir dan artikel `SystemRandom`.
- Folder `data/candidates/adjudikasi_eksternal/` di-gitignore. Hash yang di-commit sebelum diisi
  (`--read` mencocokkannya, mengarsipkan berkas terisi ke `arsip_baca/` sebelum validasi apa pun, dan
  menolak nama yang sama dengan hash lain; koreksi = berkas baru `_v2`, ...):

  | Berkas | SHA-256 |
  | --- | --- |
  | `adjudikasi_buta.xlsx` (templat kosong) | `e721bd943d0abd64b1c14c947f5ddb03a99584272283dd1f6d4acb9e40b8b45b` |
  | `kunci_adjudikasi.json` (peta butir -> butir asli, opsi label/sistem) | `8f8cf5aaeccb1004ab86e6aae8fab809dbe49a1fbd17454072a93db3a2c65fd1` |
  | `sidik_jari_templat_adjudikasi.json` | `1d0a88dc5a57de2a2581de8d41f3203afd68558dc6f2940e346128f3af8e20ef` |

- Diisi pemilik proyek sendiri sebagai `adjudikasi_buta_terisi.xlsx`, lalu `--read`. Hasilnya
  (`hasil_adjudikasi.json`: memihak label / sistem / keduanya tidak) **dicatat terpisah dan tidak
  mengubah label final maupun metrik utama**. Bias yang disadari (7.6): hanya butir yang tidak sepakat
  yang ditinjau, jadi adjudikasi hanya bisa menggeser hasil ke arah sistem; dan pemilik proyek kini
  sudah tahu bahwa setiap butir di berkas ini adalah ketidaksesuaian.
- Judul dan tanggal Liputan6 tetap ditampilkan (keputusan pemilik proyek 2026-10-21): keduanya bagian
  dari bukti yang dilihat saat pelabelan. Berkas tidak diubah; hash di atas tetap berlaku.
- **Cara hasil adjudikasi dipakai (DITETAPKAN 2026-10-21, SEBELUM berkas diisi):**
  1. **Metrik utama tidak berubah** (bagian 11 tetap angka resmi, termasuk kategori GUGUR/MEMADAI/MUNDUR).
  2. Hasil hanya dilaporkan sebagai **sensitivitas "label setelah adjudikasi"**, berdampingan dengan
     metrik utama, tanpa uji beda:
     - jumlah **kecocokan palsu** (dari 10) yang menurut adjudikasi sebenarnya kesalahan label (pemilik
       proyek memilih artikel sistem) -- butir itu dihitung positif dengan sasaran artikel sistem;
     - jumlah **penolakan palsu** (dari 9) yang menurut adjudikasi sebenarnya kesalahan label (memilih
       TIDAK ADA) -- butir itu dihitung negatif;
     - **artikel salah** (1): memilih artikel sistem -> sasaran diganti; memilih TIDAK ADA -> negatif;
     - memilih opsi label -> label tetap.
     - Metrik yang disesuaikan: ketepatan positif dan kecocokan palsu dengan Wilson 95% dan kategori
       ambang 6.1/6.2 pada n hasil penyesuaian.
  3. Butir yang ditandai **ragu** saat adjudikasi dihitung dua arah (label tetap / pilihan adjudikasi),
     dan dilaporkan kategori terburuknya, seperti 6.2.
  4. Kecocokan palsu di luar daftar kandidat (P2-17) diperlakukan sama; hasilnya juga dicatat sebagai
     "cocok di luar daftar: sah / tidak sah" (bagian 3).
  5. Karena adjudikasi hanya bisa menggeser hasil ke arah sistem (7.6), angka yang disesuaikan adalah
     **batas yang menguntungkan sistem**, bukan perkiraan tak bias; laporan wajib menyebutnya begitu.
- **Pembacaan (2026-10-21), dicatat apa adanya:**
  1. *Versi pertama DITOLAK.* `adjudikasi_buta_terisi.xlsx`, sha256
     `839415be92e7e4537b2dbcc2fafe9e2e5b7d6379f48f36356a4ece666039625b` (disimpan Excel 14:46:46 UTC),
     diarsipkan `--read` 14:51:49 UTC sebelum validasi. Hash templat, kunci, dan sidik jari sama dengan tabel di
     atas; sel bukti sama dengan templat. Ditolak karena KEPUTUSAN butir **2, 3, 4, 6, 7, 13** berisi
     "Tidak sama" (butir 6: "tidak sama"), bukan id artikel atau TIDAK ADA. Hasil tidak dipetakan dan kunci
     tidak dibuka; isinya tidak ditafsirkan.
  2. *Versi kedua.* `adjudikasi_buta_terisi_v2.xlsx`, sha256
     `b25f1ff6f02580c3cc5106208d063294e673c64eeadad2f5824c2b9a99e89c82` (disimpan Excel 15:39:15 UTC), diarsipkan
     15:42:28 UTC sebelum dibandingkan dan lagi oleh `--read` 15:42:59 UTC. Pemilik proyek menyatakan ini
     **perbaikan format oleh dirinya sendiri, tanpa AI**: isian "Tidak sama" diganti nilai sah sesuai maksudnya saat
     mengerjakan, butir lain tidak diubah. **Perbandingan sel demi sel dengan salinan arsip versi pertama (ketiga
     lembar, dimensi, proteksi, sel gabungan): tepat 6 sel berbeda, semuanya KEPUTUSAN butir 2, 3, 4, 6, 7, 13**,
     masing-masing "Tidak sama" -> "Tidak ada" (butir 7: "Tidak Ada"; dibaca sebagai TIDAK ADA). Tidak ada sel lain
     yang berbeda. `--read`: lolos, 0 butir bermasalah.
  3. *Dua hal yang tidak sesuai pernyataan, dicatat tanpa diubah:* (a) pemilik proyek menyatakan perbaikannya
     dicatat di kolom catatan tiap butir, tetapi **kolom catatan keenam butir tidak berubah** dari versi pertama, jadi
     di berkas tidak ada jejak perbaikan; catatan ini satu-satunya rekamannya. (b) **Berkas versi pertama di disk ikut
     tersimpan ulang** (15:38:11 UTC, sha256 `3ce2d0136477365b61980050439917675171b4cf23d43a4d4bbfa3c7f07c1737`;
     selnya sama dengan v2), bertentangan dengan aturan "berkas yang sudah diserahkan tidak pernah ditimpa". Versi
     yang diserahkan utuh hanya di `arsip_baca/` (salinan berhash `839415be...`), dan itulah pembanding di butir 2.
     Pengarsipan sebelum validasi bekerja seperti yang dimaksudkan.
  4. Hasil: bagian 11.9.

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

---

## 11. Hasil (segel dibuka 2026-10-20, setelah label final terkunci di `bf82657`)

Urutan yang dijalankan: commit `9868b17` (hash templat sesi) sudah di origin sejak 05:53:52 UTC, sebelum
pengisian -> berkas terisi pertama ditolak dan dicatat (7.2, `e919a7e`) -> `--read` versi koreksi lolos
(ketiga hash sama, bukti sama dengan templat, 37/37 terbaca sah) -> keandalan dan label final dihitung,
di-commit dan di-push (7.7, `bf82657`) -> baru kemudian `python -m evaluation.external_analysis --metrik`
dan `--retrieval-pembanding`. Rincian lokal: `data/candidates/sesi_buta_eksternal/hasil_evaluasi_eksternal.json`
dan `retrieval_pembanding.json`; tabel per butir yang boleh dipublikasikan (bagian 8):
`testset/eksternal_hasil_per_butir.json`. Butir analisis: **91 = 46 positif + 45 negatif** (label final 7.7).

### 11.1 Keputusan modus

- 91 butir x 3 run = 273 rekam, semuanya `selesai`; **0 tak terjawab, 0 tanpa modus**.
- **Bulat 3/3: 82; pecah 2-1: 9** (P1-2, P1-8, P1-11, P1-22, P1-30, P1-31, P2-6, P2-17, P2-38).
- Top-3 retrieval identik di ketiga run pada 91/91 butir, dan identik dengan pencarian ulang tanpa LLM
  (46/46 positif diperiksa).

### 11.2 Positif (46 butir)

- **Ketepatan jawaban cocok: 36/46 = 78,3% [64,4%; 87,7%] -> MEMADAI** (batas bawah Wilson >= 60%;
  ambang pada 46 butir: >= 35/46). Per selisih terbit: **<= 30 hari 25/28 = 89,3% [72,8%; 96,3%]**;
  **> 30 hari 11/18 = 61,1% [38,6%; 79,7%]**. Per putaran (deskriptif, tanpa uji): P1 19/24 = 79,2%
  [59,5%; 90,8%], P2 17/22 = 77,3% [56,6%; 89,9%] -- keduanya tidak konklusif sendiri-sendiri.
- **Recall@3 bersyarat (pada pasangan yang terjangkau pencarian judul): 41/46 = 89,1% [77,0%; 95,3%].**
  *Recall@3 ini batas atas; Recall@3 sistem atas seluruh klaim yang memang ada di TurnBackHoax tidak
  dapat diukur dari set ini.* Per cara pasangan ditemukan: (a) teratas embedding judul 33/36; (b) 5
  teratas embedding, bukan teratas, 7/9; (c) hanya kata kunci 1/1.
- **Pembanding tanpa LLM:** kueri judul (tanpa kata vonis) **44/46 = 95,7% [85,5%; 98,8%]**, kueri
  kutipan **41/46 = 89,1%**. Per strata (judul / kutipan): (a) 36 / 33 dari 36, (b) 8 / 7 dari 9, (c)
  0 / 1 dari 1. Judul menemukan tetapi kutipan tidak: P1-8, P1-26, P1-28, P1-49, P2-37; sebaliknya:
  P1-3, P2-1. Jadi menempel pesan alih-alih parafrase pemeriksa fakta kehilangan 5 pasangan dan
  mendapat 2.
- **Kegagalan (10):**

  | Jenis | Butir | Sasaran di top-3? |
  | --- | --- | --- |
  | Penolakan pasangan lintas gelombang (> 30 hari) | **6**: P1-8, P1-28, P1-49, P2-37 / P2-15, P2-35 | tidak (4) / ya (2) |
  | Penolakan lain (<= 30 hari) | **3**: P1-26 / P1-31, P2-4 | tidak (1) / ya (2) |
  | Kecocokan ke artikel yang salah | **1**: P2-1 (memilih kandidat lain di daftarnya) | ya |

  Jadi 5 dari 10 kegagalan positif adalah kegagalan **retrieval** (sasaran tidak di top-3, sehingga
  generator tidak mungkin memilihnya) dan 5 kegagalan **penilaian**. Dari 4 penolakan dengan sasaran di
  top-3, 2 lintas gelombang (konsisten dengan prompt yang tidak mengenal Aturan A, bagian 3), dan 2
  (P1-31, P2-4) adalah butir yang **pada uji ulang 7.7 juga dilabel TIDAK ADA oleh pemilik proyek**.
  Label tidak diubah karenanya (7.5); hanya dicatat.

### 11.3 Negatif (45 butir) -- metrik utama untuk pemicu langkah korektif

- **Tingkat kecocokan palsu: 10/45 = 22,2% [12,5%; 36,3%] -> GUGUR** (batas bawah Wilson > 10%; ambang
  pada 45 butir: gugur >= 9/45). **Tingkat penolakan benar: 35/45 = 77,8% [63,7%; 87,5%].**
  Per putaran (deskriptif): P1 5/23 = 21,7% [9,7%; 41,9%] (tidak konklusif), P2 5/22 = 22,7% [10,1%;
  43,4%] (gugur). Menurut bagian 3 kategori yang berbeda antar-putaran dilaporkan "bergantung pada aturan
  pelabelan"; estimasi titiknya hampir sama, dan perbedaan kategori di sini datang dari n yang kecil
  (batas bawah 9,7% vs 10,1%).
- **Di dalam daftar kandidat 9, di luar daftar 1** (P2-17 -> 30409, peringkat 3 di top-3, pecah 2-1;
  didaftar untuk adjudikasi, tetap dihitung kecocokan palsu).
- **Pola kegagalan:** 9 dari 10 kecocokan palsu memilih **artikel peringkat 1 retrieval**, artikel yang
  dulu ditampilkan kepada pemilik proyek dan ditolaknya; 8 dari 10 bulat 3/3 (P2-17 dan P2-38 pecah 2-1).
  Jadi kesalahannya stabil, bukan acak: generator menerima tetangga terdekat yang pola klaimnya mirip
  tetapi menurut label berbeda unsur intinya. Empat dari sepuluh menyentuh ketidakpastian label: P1-16
  (pada uji ulang pemilik proyek memilih artikel yang sama dengan sistem), P1-15 (termasuk 15 butir P1
  yang ditandai tidak konsisten), P1-23 dan P2-2 (ditandai ragu di sesi). Kategori tetap GUGUR walau
  butir-butir seperti itu dihitung cocok (11.5).

### 11.4 Uji kemunduran testset-v1 (48 butir) dan kepatuhan

- **Kemunduran bersih 5 pada 44 butir non-batas -> MUNDUR** (ambang >= 3). Benar di arsip 42/44, benar
  di 1.532 37/44; benar -> salah 5, salah -> benar 0. Per butir:
  - v1-010, v1-019 (positif): sasaran tetap di top-3, tetapi kini dijawab "belum ditemukan" (bulat) --
    kegagalan penilaian.
  - v1-024, v1-026, v1-027 (negatif sulit): kini dicocokkan ke artikel yang tidak ada di indeks 150
    (36811, 31607, 36776; bulat) -- efek data. **Belum diperiksa apakah ketiga artikel itu memuat klaim
    yang sama** (seperti enam butir yang dikeluarkan); bila ya, labelnya tidak berlaku pada 1.532 dan
    itu bukan kecocokan palsu. Tanpa pemeriksaan itu kategori MUNDUR berlaku apa adanya.
  - Butir batas: v1-051 benar -> salah (kini dicocokkan ke 32314).
- **Kepatuhan:** pelanggaran format **0** pada 274 panggilan Liputan6 dan 162 panggilan testset-v1
  (ketiga run); id di luar kandidat 0. **URL yang tidak berasal dari metadata: 2 di Liputan6 (1 butir,
  P2-39, run 2) dan 2 di testset-v1 (1 butir, v1-026, run 1 dan 3)**, menurut
  `testset_analysis.urls_outside_metadata` pada keluaran mentah. Semuanya ada di bidang `klarifikasi`
  keluaran mentah, berdomain `.go.id`, dan tersalin dari teks seksi artikel kandidat (bukan karangan
  model); semuanya dibuang `strip_urls` sebelum disimpan dan tidak pernah tampil. Aturan Wajib #3 tetap
  terjaga di keluaran, tetapi prompt tidak mencegah model menyalin URL dari teks dokumen.

### 11.5 Sensitivitas

| Set label | Positif benar | Kategori | Kecocokan palsu | Kategori |
| --- | --- | --- | --- | --- |
| **Utama (label final)** | 36/46 = 78,3% [64,4; 87,7] | memadai | 10/45 = 22,2% [12,5; 36,3] | gugur |
| Label awal butir audit (tanpa perubahan sesi) | 32/42 = 76,2% [61,5; 86,5] | memadai | 14/49 = 28,6% [17,9; 42,4] | gugur |
| Butir ragu dihitung cocok | 37/49 = 75,5% [61,9; 85,4] | memadai | 9/42 = 21,4% [11,7; 35,9] | gugur |
| Butir ragu dihitung TIDAK ADA | 36/46 = 78,3% [64,4; 87,7] | memadai | 10/45 = 22,2% [12,5; 36,3] | gugur |
| 15 butir P1: yang diterima -> TIDAK ADA | 31/38 = 81,6% [66,6; 90,8] | memadai | 15/53 = 28,3% [18,0; 41,6] | gugur |
| 15 butir P1: yang ditolak -> cocok | 38/51 = 74,5% [61,1; 84,5] | memadai | 8/40 = 20,0% [10,5; 34,8] | gugur |
| Uji ulang berubah (5) -> cocok (kappa 0,60-0,79) | 37/48 = 77,1% [63,5; 86,7] | memadai | 9/43 = 20,9% [11,4; 35,2] | gugur |
| Uji ulang berubah (5) -> TIDAK ADA | 36/44 = 81,8% [68,0; 90,5] | memadai | 10/47 = 21,3% [12,0; 34,9] | gugur |
| Per putaran: P1 (deskriptif) | 19/24 | tidak konklusif | 5/23 | tidak konklusif |
| Per putaran: P2 (deskriptif) | 17/22 | tidak konklusif | 5/22 | gugur |

- "Butir ragu dihitung cocok" memakai kandidat yang dipilih sistem bila ada di daftar kandidat butir
  itu (bagian 3); ketiga butir ragu (P2-2, P2-14, P2-30) negatif. "Ditolak -> cocok" pada 15 butir P1
  memakai aturan yang sama. "Butir ragu dihitung TIDAK ADA" identik dengan utama (tidak ada positif
  ragu).
- **Kategori sama di semua sensitivitas: positif MEMADAI, kecocokan palsu GUGUR** (kategori terburuk
  menurut 6.2 dan 7.4 = kategori yang sama). Per putaran berbeda karena n kecil (lihat 11.3).
- Uji kemunduran tidak bergantung pada label Liputan6; kategorinya MUNDUR di semua sensitivitas.

### 11.6 Keterbatasan

- **Satu anotator.** Semua label, termasuk uji ulang dan audit, dari pemilik proyek sendiri; kappa
  mengukur konsistensi dalam-anotator (0,6341 [0,3077; 0,9112]), bukan kesepakatan antar-anotator.
  Batas bawah intervalnya di bawah 0,60.
- **Jeda uji ulang 7 hari** (penyimpangan 7.2), sehingga ingatan bisa menaikkan kappa P2; kappa P1
  mencampur pergantian aturan dan Narasi utuh.
- **Berkas terisi pertama tertimpa** (7.2): tidak berubahnya 36 butir lain antara kedua versi hanya
  bersandar pada pernyataan pemilik proyek.
- **Recall@3 bersyarat**: hanya pada pasangan yang terjangkau pencarian judul; batas atas.
- **Label negatif hanya berlaku terhadap daftar kandidat** (5-8 artikel per butir), bukan seluruh basis
  data; satu kecocokan palsu (P2-17) berada di luar daftar dan belum dinilai.
- **Kutipan pendek dikeluarkan** (K1/K2, 8 butir); pesan berisi tautan saja tidak terukur.
- **Prompt generator tidak mengenal aturan gelombang** (Aturan A); 6 dari 9 penolakan palsu terjadi pada
  pasangan > 30 hari, dan pada strata itu ketepatan 11/18.
- **n berubah setelah audit** (42/49 -> 46/45); ambang yang dikunci dinyatakan dengan aturan Wilson, jadi
  diterapkan pada n baru (7.7), tetapi hitungan contoh di 6.1/6.2 tidak lagi berlaku harfiah.
- **Audit mengubah label hanya ke satu arah** dan butirnya dipilih karena berjejak; dengan label awal
  kecocokan palsu lebih tinggi (14/49), jadi label final justru menurunkan angka kecocokan palsu.
- **Kemunduran testset-v1 mencampur efek data**; tiga butir negatif yang kini dicocokkan belum
  diverifikasi.
- Hasil adjudikasi (7.8) belum ada; ia tidak akan mengubah angka di atas.

### 11.7 Implikasi (ditulis setelah angka keluar)

Kemampuan sistem mengenali butir negatif **belum cukup** untuk menjadi pemicu langkah korektif bergaya
CRAG. Pemicunya adalah jawaban "belum ditemukan"; pada set ini ia menyala dengan benar pada 35 dari 45
klaim yang tidak punya pasangan, tetapi pada **10 dari 45 (22,2%, interval 12,5%-36,3%)** sistem justru
menampilkan artikel TurnBackHoax yang menurut label bukan klaim yang sama, sehingga klaim itu tidak
pernah sampai ke langkah korektif dan pengguna melihat klarifikasi serta rujukan dari artikel lain.
Kategori ini GUGUR di semua sensitivitas, termasuk ketika setiap butir yang labelnya diragukan dihitung
menguntungkan sistem (paling baik 8/40, batas bawah 10,5%). Sisi positif berlawanan: ketepatan 36/46
memadai, dan separuh kegagalannya berasal dari retrieval, bukan penilaian.

Yang perlu diperbaiki lebih dulu, berurutan:
1. **Penilaian kesamaan klaim pada tetangga terdekat.** Sembilan dari sepuluh kecocokan palsu adalah
   artikel peringkat 1 dengan pola klaim yang sama tetapi unsur inti berbeda menurut label, dan delapan
   di antaranya bulat 3/3. Ambang skor sudah terbukti tidak memisahkan (bagian 1), jadi yang dibutuhkan
   adalah pemeriksaan eksplisit unsur inti (lembaga/subjek, tindakan, objek pembeda) sebelum
   "ditemukan" -- langkah ini harus dirancang dan kriterianya dikunci sebelum diuji.
2. **Memutuskan kebijakan gelombang bersama butir 1.** Membuat generator menerima pasangan lintas
   gelombang (Aturan A) bisa memperbaiki sebagian dari 6 penolakan lintas gelombang (2 di antaranya
   sasarannya sudah di top-3; 4 lainnya gagal di retrieval), tetapi berisiko menambah kecocokan palsu
   pada penipuan berpola sama -- persis jenis kesalahan yang gugur di sini. Keduanya tidak boleh disetel
   terpisah.
3. **Memeriksa tiga butir negatif testset-v1 yang kini dicocokkan** (v1-024, v1-026, v1-027) sebelum
   kategori MUNDUR ditafsirkan sebagai kemunduran sistem. *(Selesai 2026-10-21: ketiganya SAMA; kemunduran
   bersih sensitivitas 2, tidak mundur; angka utama tetap MUNDUR -- 11.8.)*
4. **Uji pada sampel baru.** Set 99 butir ini kini **sekali pakai** (bagian 8): perbaikan apa pun pada
   generator, prompt, retriever, atau indeks tidak boleh dievaluasi ulang di set yang sama; uji akhirnya
   memerlukan sampel Liputan6 baru dari periode lain.

### 11.8 Verifikasi tiga butir negatif testset-v1 (berkas DIBUAT 2026-10-21 13:11 UTC, SEBELUM diisi; dibaca 2026-10-21)

- **Pertanyaan:** apakah artikel yang kini dicocokkan sistem pada indeks 1.532 (v1-024 -> 36811,
  v1-026 -> 31607, v1-027 -> 36776; modus 3 run, semuanya bulat) memuat klaim yang SAMA dengan kueri butir
  menurut pedoman v1.0? Ini keputusan label, dinilai pemilik proyek sendiri, tanpa AI.
- **Berkas:** `data/candidates/verifikasi_v1/verifikasi_v1_negatif.xlsx` (`python -m
  candidates.v1_verification --make`; uji `tests/test_v1_verification.py`). Format dan proteksi seperti
  berkas sesi: per butir kueri set uji v1 dan satu artikel (judul, tanggal, label, Narasi, Kesimpulan).
  **Keputusan dan penjelasan generator tidak ditampilkan**; nomor butir v1 hanya di kunci; urutan
  `SystemRandom`. KEPUTUSAN: SAMA | BEDA | RAGU, alasan di catatan. Folder di-gitignore. Hash yang
  di-commit sebelum diisi (`--read` mencocokkannya dan mengarsipkan berkas terisi sebelum validasi):

  | Berkas | SHA-256 |
  | --- | --- |
  | `verifikasi_v1_negatif.xlsx` (templat kosong) | `2a1cff46132444add6d9973bc5883c9bdd0cd41c48be4f4bbd0656bb66efea83` |
  | `kunci_verifikasi_v1.json` (peta butir -> id v1 dan artikel) | `f824f4fb293e3bdcd3db5d21b8a528aa36410fe4791abed344946dd906243244` |
  | `sidik_jari_templat_verifikasi_v1.json` | `829d7771a4eaf49f1c160d3486bb93531a3b3993ff825746efc3793341053f43` |

- **Aturan pemakaian (DITETAPKAN 2026-10-21, SEBELUM diisi):**
  1. **SAMA** -> butir itu dikeluarkan dari analisis kemunduran sebagai **perubahan status label**
     (seperti enam butir di 6.3), bukan kemunduran. **BEDA** -> tetap dihitung kemunduran. **RAGU** ->
     dihitung dua arah (tetap / dikeluarkan) dan dilaporkan keduanya.
  2. Kemunduran bersih dihitung ulang **hanya sebagai sensitivitas**; angka utama (5/44, MUNDUR) tidak
     diganti. Ambang tetap >= 3 (6.3), tidak disesuaikan dengan jumlah butir yang tersisa.
     Hasil yang mungkin: 0 SAMA -> 5 (mundur); 1 -> 4 (mundur); 2 -> 3 (mundur); 3 -> 2 (tidak mundur).
     Dua kemunduran pada butir positif (v1-010, v1-019) tidak tersentuh verifikasi ini.
  3. **`testset/v1.jsonl` yang beku tidak diubah** (uji kunci tetap lolos); status butir dicatat di
     rancangan ini dan, bila SAMA, di `testset/v1.meta.json` seperti butir yang statusnya berubah
     sebelumnya.
- **Hasil (dibaca 2026-10-21):** `verifikasi_v1_negatif_terisi.xlsx`, sha256
  `6e23979caba0b6fb8e23aad56e626c63a256a7f5171d639fea8dee40384b97f3` (disimpan Excel 14:50:05 UTC), diarsipkan
  `--read` 14:52:07 UTC sebelum validasi. Hash templat, kunci, dan sidik jari sama dengan tabel di atas; sel bukti
  sama dengan templat; 0 butir bermasalah. Diisi pemilik proyek sendiri, tanpa AI. Excel masih membuka berkas saat
  dibaca; pemilik proyek menyatakan menutupnya tanpa menyimpan ulang, jadi hash di atas yang berlaku.

  | Butir | Artikel yang dicocokkan sistem | Keputusan | Catatan pemilik proyek |
  | --- | --- | --- | --- |
  | v1-024 | 36811 | SAMA | Menyebut hal yang sama dan tanggal serta tahun yang sama |
  | v1-026 | 31607 | SAMA | Memiliki narasi yang sama |
  | v1-027 | 36776 | SAMA | Menyebut tokoh yang sama dan narasi yang sama |

  - **Sensitivitas kemunduran (aturan 1-2):** ketiganya dikeluarkan sebagai perubahan status label -> 41 butir
    non-batas; benar -> salah tinggal v1-010 dan v1-019 (keduanya positif); salah -> benar 0. **Kemunduran bersih 2
    -> TIDAK MUNDUR** (ambang >= 3, tidak disesuaikan). Tidak ada RAGU, jadi tidak ada arah kedua.
  - **Angka utama tidak diganti: 5/44, MUNDUR.** Yang dikatakan sensitivitas ini: dari lima kemunduran, tiga
    ternyata artikel yang baru masuk indeks memang memuat klaim butir itu, jadi label negatifnya yang tidak berlaku
    pada indeks 1.532; dua sisanya (penolakan pada butir positif yang artikelnya ada di top-3) tetap kemunduran
    penilaian generator.
  - **`testset/v1.jsonl` tidak diubah, dan label di `testset/v1.meta.json` juga tidak diubah.** Sesuai aturan 3,
    statusnya dicatat sebagai entri baru `butir_negatif_berubah_status_indeks_1532_verifikasi_2026-10-21` (status
    saja, seperti entri 2026-10-03); uji kunci lolos. Dengan ini butir negatif testset-v1 yang labelnya tidak berlaku
    pada indeks 1.532 menjadi sembilan.

### 11.9 Hasil adjudikasi buta (sensitivitas; aturan 7.8, dibaca 2026-10-21)

Berkas yang dihitung: `adjudikasi_buta_terisi_v2.xlsx` (`b25f1ff6...`; riwayat penolakan versi pertama di 7.8).
Alat: `python -m candidates.adjudication_workbook --read --berkas <v2>` lalu `--sensitivitas` (hasil lokal
`hasil_adjudikasi.json`, `sensitivitas_adjudikasi.json`). Diisi pemilik proyek sendiri, tanpa AI. **Metrik utama
(11.2-11.5) tidak berubah; semua angka di bawah adalah batas yang menguntungkan sistem, bukan perkiraan tak bias.**

| Jenis ketidaksesuaian | Butir | Menurut adjudikasi kesalahan label | Tetap kesalahan sistem |
| --- | --- | --- | --- |
| Kecocokan palsu | 10 | **7** (P1-15, P1-16, P1-17, P1-21, P1-23*, P2-2*, P2-41) | **3** (P2-17, P2-33, P2-38) |
| Penolakan palsu | 9 | **3** (P1-8, P1-28, P1-31) | **6** (P1-26, P1-49, P2-4, P2-15, P2-35, P2-37) |
| Artikel salah | 1 | 1 (P2-1: artikel sistem 29505) | 0 |

\* ditandai ragu saat adjudikasi (P1-23 tanpa catatan). Tidak ada pilihan "keduanya tidak".

| Set label | Positif benar | Kategori | Kecocokan palsu | Kategori |
| --- | --- | --- | --- | --- |
| Utama (label final, tidak berubah) | 36/46 = 78,3% [64,4; 87,7] | memadai | 10/45 = 22,2% [12,5; 36,3] | gugur |
| Adjudikasi, butir ragu ikut adjudikasi | 44/50 = 88,0% [76,2; 94,4] | memadai | 3/41 = 7,3% [2,5; 19,4] | lulus |
| Adjudikasi, butir ragu tetap berlabel lama | 42/48 = 87,5% [75,3; 94,1] | memadai | 5/43 = 11,6% [5,1; 24,5] | tidak konklusif |
| **Kategori terburuk yang dilaporkan (7.8 butir 3)** | | **memadai** | | **tidak konklusif** |

- **P2-17 (kecocokan ke artikel di luar daftar kandidat, 7.8 butir 4):** adjudikasi memilih TIDAK ADA, memihak
  label, tidak ragu (catatan: "Tokoh yang disebut berbeda") -> **cocok di luar daftar: tidak sah**; tetap
  kecocokan palsu.
- **Cara membaca.** Hanya 20 butir yang tidak sepakat yang ditinjau, dan pemilik proyek tahu setiap butir adalah
  ketidaksesuaian (7.6). Kesalahan label pada butir yang sistem dan label sepakat -- yang hanya bisa merugikan
  sistem -- tidak dicari. Jadi angka yang disesuaikan menggeser hasil sejauh mungkin ke arah sistem; kebenarannya
  berada di antara baris utama dan baris adjudikasi.
- **Bahkan di batas yang menguntungkan sistem, kecocokan palsu tidak lulus dengan kokoh:** kategori terburuk tidak
  konklusif (5/43, batas atas 24,5% > 20%), dan "lulus" hanya tercapai bila kedua butir ragu dihitung ke arah
  sistem, dengan batas atas 19,4% -- tepat di bawah 20%. Kesimpulan 11.7 (pemicu CRAG belum layak) tetap.
- **Yang lebih kuat dari angka itu: label pada butir yang sulit tidak stabil.** 11 dari 20 pilihan adjudikasi
  berbeda dari label final (7 dari 10 kecocokan palsu), padahal kappa uji ulang 0,63. P2-2 kini sudah dinilai tiga
  kali: TIDAK ADA (label awal), TIDAK ADA (sesi buta, audit), dan 31894 dengan ragu (adjudikasi). Ini sejalan dengan
  pola kegagalan utama (11.3): pada penipuan berpola sama, batas "klaim sama" kabur bagi anotator maupun sistem.
  Rancangan pemeriksaan unsur inti (11.7 butir 1) perlu kriteria yang cukup tegas untuk juga menstabilkan label.
- Penolakan palsu lebih tahan: 6 dari 9 tetap kesalahan sistem.
