# CLAUDE.md

Panduan konteks proyek untuk Claude Code. Baca berkas ini sebelum
mengerjakan tugas apa pun di repositori ini.

---

## Status Terkini

**Diperbarui setiap kali satu tahap selesai. Baca bagian ini LEBIH DULU saat memulihkan
sesi** (mis. setelah sesi terputus) -- sebelum bagian lain di berkas ini.

*(2026-10-03)*

> **KEADAAN (2026-10-03 malam): PERLUASAN BASIS DATA SELESAI. INDEKS PRODUKSI = 1.532 ARTIKEL /
> 4.593 CHUNK, SATU TAHUN PENUH: 2025-09-30 s.d. 2026-09-27** (SALAH 1.057, PENIPUAN 456, PARODI 15,
> SATIR 2, SATIRE 1, KOMEDI 1). `index_check` LENGKAP (termasuk 8 sampel embedding ulang, kosinus
> 1,000000): SEGAR. **Demo berjalan di indeks ini, yang BELUM PERNAH dievaluasi dengan generator;
> yang terukur hanya retrieval (positif Recall@1/3 = 18/20, 20/20).** Akurasi 48/50 tetap hanya
> berlaku pada `archive/v1` (150 artikel). **TAHAP PERLUASAN ("tahap 3") DINYATAKAN SELESAI oleh
> pemilik proyek setelah penutupan 2026-10-03; berikutnya Versi 2 (belum dimulai).** Ablasi lengkap
> pada indeks 1.532, konfirmasi v1-029 lewat retriever produksi, dan pengukuran ulang set
> pengembangan SUDAH dijalankan (butir (l) di bawah; jalan pertama ablasi sempat dihentikan karena
> memori rendah). **v1-046 diputuskan pemilik proyek: TETAP NEGATIF**
> (bertetangga topik dengan 30652, bukan klaim sama; `v1.meta.json`). **Tahap berikutnya = pembaruan
> berkala (`docs/rancangan_pembaruan_berkala.md`; ingest tetap manual): pembungkus SCRAPING sudah
> dibangun dan diuji manual (butir (o)) dan **TERDAFTAR di Task Scheduler sejak 2026-10-03 (atas
> persetujuan pemilik proyek): tugas "RAG_FactChecking - pembaruan berkala", setiap hari 13.00**,
> `pythonw.exe` + `scripts/pembaruan_berkala.pyw` (tanpa jendela), boleh mulai dan terus berjalan
> saat memakai baterai, `StartWhenAvailable` (jadwal terlewat dijalankan sekali saat menyala), hanya
> bila jaringan tersedia, satu instans, batas 1 jam, hanya saat pengguna login (Interactive). Dipicu
> sekali lewat Task Scheduler pukul 20.35: kode keluar 0, `pembaruan_status.json` dan log tertulis --
> TETAPI jalan itu melewati mode maju (sudah berjalan hari itu), jadi **pengambilan dari jaringan di
> bawah Task Scheduler baru pertama kali teruji pada jalan terjadwal 2026-10-04 13.00; periksa
> `data/expansion/pembaruan_status.json` sesudahnya.** Setelan tugas JANGAN diubah tanpa persetujuan
> pemilik proyek (mengubah pengaturan sistem). Menghapus: `Unregister-ScheduledTask -TaskName
> "RAG_FactChecking - pembaruan berkala"`. Berkas penanda `PERHATIAN_PEMBARUAN.txt` adalah
> pemberitahuan UTAMA (notifikasi Windows masuk diam-diam ke panel karena Do not disturb). ANTREAN BELUM DIGABUNG: 16 artikel
> (`data/expansion/forward_2026-10-03.json`, 27 Sep-2 Okt 2026; SALAH 8, PENIPUAN 6, BELUM TERBUKTI
> 2) -- penggabungan dan ingest-nya dijalankan MANUAL oleh pemilik proyek, jangan dikerjakan
> sendiri. Label baru `BELUM TERBUKTI` sudah diputuskan (gaya ungu sendiri, butir (p)), jadi antrean
> tidak lagi menahan dan `PERHATIAN_PEMBARUAN.txt` sudah terhapus.** `ef_search` produksi kini 2000
> (butir (m)). Cadangan yang ada (dua yang lebih lama DIHAPUS 2026-10-03 atas perintah pemilik
> proyek): `data/backups/pre_batch04-06_2026-10-03/` (indeks 922 dengan rujukan bersih +
> `articles.json` 1.532, sebelum ingest) dan `data/backups/pre_ef_search_2026-10-03/` (indeks 1.532,
> `ef_search` 100). Manifest `manifests/expansion_article_ids.json` SUDAH memuat
> kelompok 4-6 (1.382 artikel; pemeriksaan PII judul 2026-10-03: 0 temuan). **Aturan Wajib #1 (butir "Temuan Aturan
> Wajib #1" di bawah): SELESAI untuk data dan indeks produksi -- pemendek URL dan
> seluruh domain arsip disaring, baris "Sumber:" dibaca sebagai sumber klaim (kecuali pemerintah/
> media tepercaya), rujukan disaring ulang saat tampil, metadata 922 artikel terindeks sudah
> diperbarui terarah dan `index_check` lolos sebelum penggabungan.**

**VERSI 1 SELESAI, TERUKUR, DAN PUNYA DEMO LOKAL. Tahap: (1) pengarsipan indeks Versi 1 --
SELESAI 2026-09-25, ditutup 2026-09-26 (pemeriksaan data terpublikasi); (2) perluasan basis
data -- SELESAI 2026-10-03 (1.532 artikel, 30 Sep 2025-27 Sep 2026; disebut "tahap 3" di prompt
pemilik proyek); lalu (3) Versi 2 -- BELUM DIMULAI.**

- **Perluasan basis data (sejak 2026-09-26): scraping HTML**, keputusan pemilik proyek -- API key
  Yudistira belum diberikan; tetap scraping sampai key ada. Alat: `src/scraping/expand.py`
  (`PYTHONPATH=src python -m scraping.expand --batch-size 250`; uji offline `tests/test_expand.py`).
  Mode mundur: kelompok artikel LEBIH TUA dari artikel tertua yang dimiliki, dicari lewat URL
  jangkar (halaman daftar bergeser dan id tidak monoton). Keluaran di `data/expansion/`
  (`batch_NN.json`, `batch_NN_report.json`, `state.json`; **di-gitignore** karena berisi teks
  artikel dan kontak penipu -- lihat "Cara Kerja"). HTML mentah tetap di-cache di `data/raw_html/`.
  **Ketentuan:** JANGAN gabungkan ke `data/articles.json` dan JANGAN ingest kelompok BARU sampai seluruh kelompok
  selesai dan lolos pemeriksaan kualitas; `archive/v1/` tidak disentuh. Ambang berhenti tingkat
  gagal 5% (`MAX_FAILURE_RATE`, pilihan pemilik proyek, bukan berbasis data).
  - **Kelompok 1 (2026-09-26):** 250/250 berhasil, 0 seksi kosong, tanggal 2026-05-26 s.d.
    2026-08-05 (bersambung dengan basis 5 Agu-18 Sep 2026). Label: SALAH 127, PENIPUAN 119,
    PARODI 2, TIDAK DIKETAHUI 2. Dua yang terakhir (34929, 35383) karena kurung siku judul di
    SUMBER tidak lengkap (`[SALAH Purbaya ...`, `PENIPUAN] Tautan ...`), bukan label baru;
    `parse_title` tidak diubah (menunggu keputusan).
  - **Kelompok 2 (2026-09-27):** 250/250 berhasil, 0 seksi kosong, 2026-03-31 s.d. 2026-05-26
    (halaman daftar 43-68; 0 id tumpang tindih dengan kelompok 1). Label: SALAH 159, PENIPUAN 88,
    TIDAK DIKETAHUI 2 (33422, 33355: sama-sama `[SALAH` tanpa `]` di sumber), PARODI 1.
    Laju ~4,5 artikel/hari (56 hari), lebih cepat dari kelompok 1.
  - **Penggabungan kelompok 3 (2026-09-27, atas izin pemilik proyek):** reparse kelompok 3 dari
    cache (6 artikel berubah, hanya Kesimpulan; selisihnya persis efek CR CR LF di cache lama, sama
    dengan 10 artikel sebelumnya), digabung di akhir `articles.json` -> **922 artikel**; 672 lama
    identik; reparse penuh 922 dari cache identik. Cadangan sebelum ingest:
    `data/backups/pre_batch03_2026-09-27/` (29 MB: `chroma/` + `articles.json`; di-gitignore, terpisah
    dari arsip; **DIHAPUS 2026-10-03** atas perintah pemilik proyek -- memuat metadata rujukan lama). Ingest INKREMENTAL (bukan `--rebuild`): 750 chunk baru, 2016 dilewati, 10 mnt 13 dtk
    (0,8 dtk/chunk), tidak terhenti. `index_check` produksi: SEGAR, 2766 chunk. Arsip v1 diperiksa pada
    SALINAN byte (agar arsip tidak dibuka; lihat temuan ChromaDB): `--expect-v1-archive` SIDIK JARI
    COCOK, SEGAR; hash byte 11 berkas `archive/v1/` sebelum = sesudah. Chunk terpotong kini 10/2766
    (Penjelasan 9, **Narasi 1 -- pertama kali ada Narasi terpotong**, 532 token).
    **Cakupan: 922 artikel, 2766 chunk, 2026-02-02 s.d. 2026-09-27** (SALAH 562, PENIPUAN 353,
    PARODI 7). Menuju ~1.000: kurang 78 -> 1 kelompok lagi (`--batch-size 78`, atau 250 bila target
    dinaikkan).
  - **Kelompok 4 (2026-09-28; scraping SAJA, belum digabung/di-ingest -- menunggu memori dibebaskan):**
    250/250 berhasil, 0 seksi kosong, 2025-12-17 s.d. 2026-02-02 (halaman daftar s.d. 118; id 30876-32104;
    0 id tumpang tindih dengan 922 artikel). Label: SALAH 199, PENIPUAN 48, PARODI 1, **SATIRE 1 (31118),
    SATIR 1 (30924)** -- label BARU berkurung lengkap, diterima apa adanya (Aturan Wajib #7); cara
    menampilkan: **diputuskan 2026-09-28** -- SATIRE dan SATIR = satu kategori, ditampilkan dengan gaya
    PARODI (`STATUS_ALIASES` di `presentation.py`, lapisan tampilan saja; label tersimpan tidak diubah). Retry: artikel 1 (halaman galat, berhasil),
    halaman daftar 0; `failed_ids.json` tidak dibuat. 0 artikel memuat `\r`. Laju ~5,3 artikel/hari
    (47 hari). **30089 (artikel asal v1-029, 16 Nov 2025) BELUM masuk** (di luar rentang kelompok ini);
    sisa ke akhir Sep 2025 = 78 hari -> **perkiraan ~400 artikel lagi (2 kelompok), total ~1.570
    artikel** pada laju 5,3/hari (bukan ~486/1.408). Laju bervariasi antar-periode (kelompok 1: ~3,5/hari;
    kelompok 2: ~4,5; kelompok 4: ~5,3), jadi angka ini perkiraan.
  - **Kelompok 6, JALAN ULANG (2026-10-03 ~00:07 WIB, `--batch-size 110`; scraping SAJA): 110/110
    berhasil, 0 gagal, 0 retry, 0 seksi kosong, kode keluar Python 0** (baris terakhir
    `batch_06.log`). Jangkar 29646 di halaman daftar 144; halaman daftar s.d. 155; id 29324-29645;
    80 artikel pertama sama dengan jalan yang gugur (terbaca dari cache). **2025-09-30 s.d.
    2025-10-23** (23 hari, ~4,8 artikel/hari; Sep 2025: 8 artikel, semuanya 30 Sep; Okt: 102). Tiga
    artikel terakhir dalam urutan daftar bertanggal 30 Sep, jadi **30 Sep 2025 mungkin belum
    lengkap** (belum diperiksa apakah ada artikel 30 Sep lain setelah jangkar baru 29324). Label:
    SALAH 91, PENIPUAN 16, PARODI 3; tidak ada label baru, `TIDAK DIKETAHUI` 0, 0 judul berkarakter
    tak terlihat. 0 duplikat, 0 tumpang tindih dengan 1.422 artikel lain, 0 memuat `\r`; 110 cache
    lolos validasi, 0 teks galat, reparse dari cache identik 110/110; total cache 1.532.
    **29437 MASUK** (PENIPUAN, 07/10/2025): `http://kemenag.go.id]` tersaring dengan alasan "URL tidak
    sah" dan tetap di `references_raw`; `http://kemenag.go.id` yang sah menjadi satu-satunya rujukan.
    `state.json`: `batch` 6, jangkar 29324, `start_page` 155, 1.510 `known_ids`. `failed_ids.json`
    tetap 210 entri; status turunan 210 teratasi / 0 terbuka. `references` kosong 20/110.
    **`claim_sources` kosong 110/110** -- lihat butir "Temuan Aturan Wajib #1". Kesimpulan median 136
    karakter, hanya 4/110 diawali "Faktanya" (keterbatasan klarifikasi tipis berlaku juga di sini).
    **Label 1.532 artikel setelah reparse:** SALAH 1.057, PENIPUAN 456, PARODI 15, SATIR 2, SATIRE 1,
    KOMEDI 1. Log jalan yang gugur disimpan sebagai `batch_06_gugur_2026-10-02.log`.
  - **Temuan Aturan Wajib #1 (2026-10-03; DILAPORKAN, BELUM DIPERBAIKI -- menunggu keputusan pemilik
    proyek; ditemukan saat memeriksa `claim_sources` kelompok 6):**
    (1) *Sumber hoaks sebelum ~akhir Okt 2025 tidak ada di Narasi.* Pada artikel lama, Narasi di
    sumber berupa teks polos tanpa tautan; tautan unggahan hoaks hanya ada di seksi **Hasil Periksa
    Fakta, baris "Sumber:"**, yang TIDAK dibaca `extract_claim_sources`. `claim_sources` kosong per
    bulan: Sep 2025 8/8, **Okt 2025 115/156**, Nov 9/126, lalu 1-13 per bulan. Akibatnya kriteria (a)
    penyaringan `references` ("cocok dengan `claim_sources`") tidak bekerja untuk artikel itu; yang
    menjaga hanya daftar domain.
    (2) *Baris "Sumber:" ada di SEMUA 1.532 artikel* dan pada artikel baru umumnya sama dengan tautan
    Narasi (ada di `claim_sources` pada 807/922, 212/250, 218/250, 0/110).
    (3) **URL "Sumber:" yang TAMPIL di `references`: 11 URL pada 10 artikel** (pencocokan string
    ternormalisasi): 9 URL / 8 artikel di **indeks produksi 922** (35161 `arsip.cekfakta.com`; 34994,
    34980, 34647 `short-url.org`; 33802 `tinyurl.com`; 33794, 33308 `shorturl.at`; 33497 dua tautan
    media arus utama), 1 di kelompok 4 (31532 `cekbansos.kemensos.go.id`), 1 di kelompok 5 (29858
    `tinyurl.com`), 0 di kelompok 6. Tujuh di antaranya pemendek URL pada artikel PENIPUAN/SALAH:
    **ke mana pemendek itu mengarah TIDAK diperiksa** (tidak dibuka; bisa arsip, bisa tautan penipuan).
    Tautan media/pemerintah (33497, 31532) kemungkinan sah (sumber yang dikutip keliru oleh hoaks),
    belum diverifikasi. Usulan (belum dikerjakan): baca baris "Sumber:" sebagai sumber `claim_sources`
    kedua sehingga kriteria (a) menyaringnya -- ini perubahan logika parsing yang mengubah
    `claim_sources`/`references` banyak artikel (metadata chunk), jadi perlu bukti reparse dan
    keputusan soal ingest ulang.
  - **Tindak lanjut temuan Aturan Wajib #1 (2026-10-03, keputusan pemilik proyek; tanpa membuka
    tautan apa pun):**
    (a) *Pemendek URL masuk `ALWAYS_BLOCKED_DOMAINS`* (`links.py`): `tinyurl.com`, `shorturl.at`,
    `short-url.org`, `bit.ly`, `s.id`, `cutt.ly` (ditetapkan pemilik proyek) + `surl.li`, `g.co`, dan
    `fb.me` (pemendek Facebook, kelompok media sosial) yang ditemukan di data. Alasan: tujuan tautan
    pendek tidak bisa diverifikasi pengguna sebelum diklik, bahkan bila rujukannya sah. **Bukti
    (parse ulang 1.532 artikel dari cache, kode `89ad36a` vs baru): 1.507 identik, 25 berubah, hanya
    bidang `references_filtered` (25) dan `references` (13)**; `references_raw`/`claim_sources` tidak
    berubah; tidak ada rujukan yang bertambah. 13 URL tersaring: bit.ly 4, short-url.org 3,
    tinyurl.com 2, shorturl.at 2, g.co 2. Per sumber: 922 = 18 artikel (8 di antaranya kehilangan
    rujukan tampil: 36089, 35112, 34994, 34980, 34647, 33802, 33794, 33308), kelompok 4 = 4, 5 = 1,
    6 = 2. Rujukan menjadi kosong: 34994, 32091. **Arsip v1: 36089 terdampak (bit.ly di
    `references`); `archive/v1/` TIDAK disentuh** -- lapisan tampilan menyaringnya bila demo
    diarahkan ke arsip.
    (b) *Penyaringan ulang di lapisan tampilan* (`presentation.display_references`, dipanggil
    `build_view`): rujukan dari metadata indeks disaring lagi dengan `links.blocked_reason` tepat
    sebelum ditampilkan, dan tiap rujukan terbuang dicatat `logger.warning` (alasan + id artikel,
    bukan tautannya). Dasar: ingest inkremental hanya membandingkan TEKS chunk, jadi metadata
    `references` yang basi tidak pernah diperbarui olehnya. Lapisan ini tidak mengenal
    `claim_sources` (tidak dibawa ke metadata), jadi hanya menutup kebocoran berbasis domain.
    `generator.py` tidak disentuh (uji kunci lolos): keluaran teks `generator` (CLI/evaluasi) dan
    konteks LLM masih memuat rujukan dari metadata apa adanya.
    (c) *`index_check` sudah mendeteksi metadata basi:* `compare_index` membandingkan `references`
    tiap chunk dengan hasil chunking `articles.json` (uji baru: teks sama, rujukan beda -> dilaporkan).
    Saat ini indeks MASIH cocok dengan `articles.json` karena `articles.json` belum di-reparse;
    setelah reparse, `index_check` akan gagal pada chunk 18 artikel itu sampai metadata diperbarui.
    (e) **Keputusan pemilik proyek atas (d), diterapkan 2026-10-03:** BAWAAN = SARING. Semua URL di
    baris "Sumber:" masuk `claim_sources` (dan karenanya tersaring dari `references`), KECUALI
    domain pemerintah (`*.go.id`) atau media/cek fakta pada daftar eksplisit
    `links.TRUSTED_SOURCE_DOMAINS` (`is_trusted_source`). **Daftar itu disusun 2026-10-03 dari media
    arus utama dan pemeriksa fakta yang muncul sebagai rujukan di data; "klasifikasi domain"
    2026-09-26 tidak pernah disimpan sebagai daftar di repositori, jadi daftar ini BARU dan perlu
    ditinjau pemilik proyek.** Pada data saat ini hanya 4 URL yang bergantung padanya (2 `.go.id`, 2
    media). Ekstraksi (`parser.extract_factcheck_sources`) memecah per URL karena satu `<a href>` di
    sumber bisa memuat beberapa URL (136/1.532 artikel). Lima domain arsip ditambahkan ke daftar
    saring: `arsip.cekfakta.com`, `archive.fo`, `megalodon.jp`, `perma.cc`, `archive.cob.web.id`.
    *Pemecahan 119 URL "Sumber:" di luar daftar lama:* arsip 88, pemendek 20, pemerintah 2 (32110,
    31532), media 2 (33497), `turnbackhoax.id` 3 (dilewati parser), **domain lain 4**: 34525
    (`*.emgy.top`, laman penipuan), 32772 (Google Drive), 33554 (Google Docs), 36622
    (`videotourl.com`) -- keempatnya kini di `claim_sources`; tidak satu pun sebelumnya tampil sebagai
    rujukan. Tiga artikel berujukan resmi (32110, 31532, 33497) tetap menampilkan rujukannya.
    **Bukti (parse ulang 1.532 artikel, `11742a7` vs baru): 1.176 identik, 356 berubah, HANYA
    `claim_sources` (268), `references_filtered` (309), `references` (25); `references_raw` tidak
    berubah; tidak ada rujukan bertambah.** 27 rujukan tampil tersaring (megalodon.jp 15,
    arsip.cekfakta.com 9, archive.fo 2, perma.cc 1); `claim_sources` kosong 206 -> 1 artikel (29505,
    "Sumber:"-nya hanya PDF di turnbackhoax.id); artikel tanpa rujukan 200 -> 205. Setelah semua
    perubahan: 0 rujukan tampil berdomain daftar-blokir, 0 rujukan tampil yang juga `claim_sources`.
    (f) **Metadata 922 artikel terindeks diperbarui TERARAH (2026-10-03):** alat baru
    `python src/ingest.py --update-metadata` (`ingest.update_metadata`: menulis ulang metadata chunk
    yang teksnya sama; tanpa embedding, tanpa memuat model; chunk berteks beda/belum ada hanya
    dilaporkan; uji dengan ChromaDB sementara). Urutan yang dijalankan: cadangan
    (`data/backups/pre_metadata_update_2026-10-03/`, DIHAPUS 2026-10-03 atas perintah pemilik proyek
    karena memuat metadata rujukan yang bermasalah; salinan byte 10
    berkas indeks cocok) -> `index_check` SEGAR -> `scraping.reparse` (922: 729 identik, 193 berubah,
    hanya tiga bidang itu) -> `index_check` **BASI, 60 masalah, semuanya "metadata 'references'
    beda"** (20 artikel x 3 chunk: bukti nyata bahwa ia memeriksa metadata, bukan hanya teks) ->
    `--update-metadata` (60 chunk, kunci `references` saja, 0 teks berbeda) -> `index_check` SEGAR.
    Sidik jari: `sha256_embedding_float32` SAMA sebelum/sesudah (`6a49aca4...`); `sha256_teks_metadata`
    berubah. Semua `index_check` dijalankan dengan `--embed-sample 0` (model tidak dimuat; memori
    bebas 2,3 GB). 20 artikel: 32314, 32378, 32772, 32827, 32861, 33308, 33426, 33461, 33651, 33653,
    33658, 33794, 33802, 34471, 34647, 34980, 34994, 35112, 35161, 36089.
    (g) **Arsip v1:** `archive/v1/` tidak disentuh. Hanya 36089 yang rujukan tersimpannya terdampak
    (bit.ly); ia tidak pernah menjadi artikel jawaban pada evaluasi v1 (hanya kandidat top-3 untuk
    v1-026 dan v1-029). Celah pengukuran dicatat di `testset/v1_temuan_untuk_v2.md` bagian 9.
    (h) **Penggabungan kelompok 4-6 (2026-10-03):** masing-masing di-reparse dari cache (kelompok 4:
    31 artikel berubah; 5: 39, termasuk `title`/`label` tiga judul yang diperbaiki; 6: 109 -- hanya
    bidang `claim_sources`/`references`/`references_filtered` selain tiga judul itu), digabung di
    akhir `articles.json` -> 1.532; 922 pertama identik; reparse penuh dari cache identik; 0
    duplikat id; skema sama; 0 `\r`. Label: SALAH 1.057, PENIPUAN 456, PARODI 15, SATIR 2, SATIRE 1,
    KOMEDI 1. Seksi kosong hanya 29670 (Narasi, Penjelasan) dan 29687 (Penjelasan) -> 4.593 chunk
    (bukan 4.596). Chunk terpotong 512 token yang AKAN berlaku setelah ingest: **Narasi 4 /
    Penjelasan 9 / Kesimpulan 0 dari 4.593** (922: 1/9/0 dari 2.766). Berkas `batch_0N.json` di
    disk dibiarkan seperti hasil scraping (belum memuat perubahan reparse).
    (i) **Ingest kelompok 4-6 (2026-10-03, INKREMENTAL, bukan `--rebuild`):** cadangan
    `data/backups/pre_batch04-06_2026-10-03/` (35 MB; salinan byte cocok, 2.766 chunk, integritas
    sqlite ok). 2.766 chunk dilewati, **1.827 chunk baru di-embed dalam 35 mnt 22 dtk (1,2 dtk/chunk)**,
    tidak terhenti, kode keluar Python 0 (log `data/ingest_batch04-06_2026-10-03.log`). `index_check`
    lengkap (`data/index_check_batch04-06_2026-10-03.log`): SEGAR, 4.593 chunk, 8 sampel kosinus
    1,000000 (termasuk 31975, 30987, 29913 dari kelompok baru). **Arsip v1:** hash byte 11 berkas
    `archive/v1/` sebelum = sesudah; pada SALINAN byte, `--expect-v1-archive`: SIDIK JARI COCOK, SEGAR.
    **Chunk terpotong 512 token: Narasi 4 / Penjelasan 9 / Kesimpulan 0 dari 4.593** (riwayat:
    0/3/0 dari 450; 0/8/0 dari 2.016; 1/9/0 dari 2.766). Maks token: Narasi 547, Penjelasan 591,
    Kesimpulan 132.
    (j) **v1-029 dan perbandingan indeks (2026-10-03; `evaluation.index_comparison`, kosinus eksak,
    tanpa LLM; `testset/v1_perbandingan_indeks_1532.json`):** **30089 berada di PERINGKAT 1 untuk
    v1-029 (0,8992)**; top-3: 30089, 32614 (0,7815), 29732 (0,7070); sasaran lama 36161 turun dari
    peringkat 1 (arsip) -> 3 (922) -> 5 (1.532). Jadi v1-029 = butir negatif KEENAM yang klaimnya
    kini ada di basis data (artikel asalnya sendiri); belum dicatat di `v1.meta.json`. Recall@1/3/5/
    10/20 arsip -> 922 -> 1.532: **positif 19,20,20,20,20 -> 18,20,20,20,20 -> 18,20,20,20,20** (tidak
    berubah sejak 922; v1-002 peringkat 3, v1-019 peringkat 2); negatif sulit (sasaran = artikel
    tetangga; PENGAMATAN, bukan mutu) 14,16,18,19,20 -> 9,11,13,15,18 -> 9,9,11,14,16; negatif dengan
    kandidat top-3 > 0,5739: 16 -> 23 -> 24 dari 30 (bertambah v1-046, 0,6308 ke 30652, topik pelatih
    timnas, klaim berbeda). Artikel asal butir negatif yang kini ada di indeks: v1-021, v1-022,
    v1-029, v1-043, v1-049 (+ v1-050 lewat artikel lain).
    (k) **"Mungkin terkait" pada indeks 1.532: TETAP DIMATIKAN** (`config/related_threshold.json`,
    entri `data` kini 1.532 artikel / 4.593 chunk, `ambang: null`). Skor kandidat teratas tidak bisa
    turun saat indeks diperbesar (chunk lama dan embedding-nya tetap), jadi kueri tak terkait "bumi
    datar" tetap >= 0,6385, di atas kandidat layak tampil (0,5739-0,63); selain itu v1-046 kini
    0,6308. Set pengembangan tidak diukur ulang (memori).
    (l) **Penutupan 2026-10-03 (satu jalan, memori dipantau; log `data/pending_2026-10-03.log`):**
    *Ablasi lengkap pada indeks 1.532* (`testset/retrieval_ablation_prod1532.json`/`_report.txt`, ~7
    menit, kode keluar 0): Recall@1/3/5/10/20 non-batas 27,29,31,34,36 dari 40 (positif
    18,20,20,20,20; negatif sulit 9,9,11,14,16) -- sama dengan `index_comparison`. Agregasi dan top-k:
    tetap tidak dapat dibedakan dari kebetulan. Seksi (@3 non-batas): seluruh seksi 29/40, hanya
    Narasi 28/40, Narasi+Kesimpulan 29/40 (identik dengan seluruh seksi, 0 butir berpindah), hanya
    Kesimpulan 21/40 (turun bermakna, -8, p 0,008; positif 15/20) -- jadi 29670, yang hanya punya
    chunk Kesimpulan, berada di jalur retrieval terlemah. Panjang klaim: ~1.500 dan ~3.000 karakter
    19/20; ~5.000 karakter dengan pengganggu di kedua sisi **0/20** (klaim di luar 512 token pada
    18/20; pada arsip 2/20); klaim di awal pesan tetap 19/20. **Validasi kesetiaan: top-3 eksak =
    `retriever.retrieve` produksi pada 53/54 butir; berbeda pada v1-048** (pada 922: 54/54) --
    pertama kalinya retriever produksi tidak sama dengan pencarian eksak; penyebabnya (aproksimasi
    HNSW atau batas `CHUNK_FETCH`) BELUM diselidiki.
    *v1-029 lewat retriever produksi:* 30089 peringkat 1 (0,8992), lalu 32614 (0,7815), 29732
    (0,7070); identik dengan pencarian eksak. Dicatat di `v1.meta.json`
    (`butir_negatif_berubah_status_indeks_1532_2026-10-03`) sebagai butir negatif KEENAM. **v1-046
    TIDAK dicatat** (menunggu keputusan pemilik proyek; top-1 30652 0,6308).
    *Set pengembangan pada indeks 1.532* (`testset/devset_retrieval_1532.json`): sasaran di peringkat
    1 untuk 36730, 36738, 36731, 36729; **kueri batas "bantuan buat orang tua" tidak lagi memuat 36737
    di top-3** (32625 0,6514; 35849 0,6408; 32117 0,6355). Negatif: bumi datar 0,6385 (tetap), vaksin
    flu 36214 0,6671 (tetap), megathrust 0,5963 (tetap), daun sirsak 0,5715, gas melon 0,6225 (naik
    dari 0,5377; kini ada artikel bantuan untuk pemilik LPG 3 kg). "Mungkin terkait" tetap mati; bahwa
    ambang skor gagal secara STRUKTURAL saat basis data membesar dicatat di
    `v1_temuan_untuk_v2.md` bagian 6.1 (usulan: ganti dengan penilaian grader di Versi 2).
    *Daftar tepercaya* disetujui pemilik proyek (2026-10-03); pencocokan pada batas domain, diuji
    dengan tiruan nama media. *Catatan cakupan demo* memisahkan hasil pencarian (18 dan 20 dari 20
    butir uji) dari akurasi jawaban, yang belum terukur pada indeks ini.
    (m) **Retriever produksi = pencarian PERKIRAAN (HNSW), diselidiki 2026-10-03 pada SALINAN indeks
    (produksi tidak diubah; hash byte sama):** parameter bawaan ChromaDB 1.5.9 `ef_search` 100,
    `ef_construction` 100, `max_neighbors` 16. v1-048: artikel 31975 (eksak peringkat 2, 0,5546)
    hilang dari hasil produksi karena chunk Narasi-nya tidak dikembalikan; 34690 naik ke peringkat 2,
    36776 masuk peringkat 3. 64 kueri, 30 chunk teratas: chunk terlewat 20/1.920 pada 922 artikel
    (0 top-3 berbeda) -> 35/1.920 pada 1.532 (1 top-3 berbeda); pada salinan dengan `ef_search` 200:
    10; 500: 1; 2.000: 0. Jadi selisihnya aproksimasi HNSW dan membesar bersama indeks. Konsekuensi
    demo: artikel yang benar kadang bisa tidak terambil (penolakan palsu dari indeks); pada 20 butir
    positif tidak terjadi.
    **DIPERBAIKI di indeks produksi 2026-10-03 (keputusan pemilik proyek; perbaikan ketepatan, tanpa
    embedding ulang): `ef_search` produksi 100 -> 2000** (`ingest.PRODUCTION_EF_SEARCH`; diterapkan
    dengan `python src/ingest.py --apply-search-config`; cadangan
    `data/backups/pre_ef_search_2026-10-03/`, 54 MB). Dipilih 2000 = nilai terkecil yang terukur tanpa
    meleset (500 menyisakan 1 chunk); bukan "setara eksak" karena jumlah chunk terus bertambah.
    Sebelum -> sesudah pada indeks produksi (64 kueri, proses baru): chunk terlewat 33/1.920 -> 0;
    top-3 berbeda 1 (v1-048) -> 0; latensi `collection.query` median 4,1 -> 9,8 ms (p95 5,6 -> 11,9).
    Isi indeks tidak berubah (sidik jari sama; `index_check` lengkap SEGAR).
    **INDEKS PRODUKSI DAN ARSIP KINI SENGAJA MEMAKAI PARAMETER PENCARIAN BERBEDA: produksi
    `ef_search` 2000, `archive/v1` tetap 100** (arsip tidak disentuh; hash byte sama). Alasan: arsip
    adalah baseline yang dibangun dan dievaluasi dengan nilai bawaan; pada 450 chunk HNSW identik
    dengan pencarian eksak, jadi pembandingan lewat arsip (Aturan Wajib #6) tidak terpengaruh.
    `get_collection` hanya memakai konfigurasi saat koleksi DIBUAT (koleksi baru di luar `archive/`
    langsung 2000, mis. setelah `--rebuild`); `index_check` gagal bila `ef_search` tersimpan tidak
    sesuai (produksi 2000; arsip atau salinannya lewat `--expect-v1-archive` 100). **Alat pemeriksaan
    rutin: `python -m evaluation.retriever_exactness`** (kode keluar 1 bila top-3 retriever berbeda
    dari pencarian eksak; hasil terakhir `testset/retriever_exactness_1532.json`) -- WAJIB dijalankan
    setiap kali indeks bertambah. Catatan: `ef_search` baru berlaku pada proses yang membuka indeks
    SETELAH diubah (segmen di-cache per proses); demo yang sedang berjalan perlu dijalankan ulang.
    (n) **Dua celah prasyarat pembaruan berkala DITUTUP (2026-10-03; `expand.py`, uji di
    `tests/test_expand.py`, tiga mutasi kontrol menggagalkan uji yang sesuai):**
    *(1) Jalan dengan kegagalan tidak memajukan batas "sudah dimiliki".* Dulu jalan yang selesai
    dengan kegagalan tetap menulis hasil dan memajukan `state.json` (mundur) atau titik henti (maju),
    sehingga artikel gagal tak pernah terjangkau lagi. Sekarang (`hold_decision`): kegagalan sistematis
    (>= 2 gagal dan > 5%) -> DITAHAN, kode keluar 3, sampai manusia turun tangan (`--accept-failures`
    untuk menulis apa adanya); masih ada kegagalan yang bisa dicoba lagi -> DITAHAN, kode 5; semua
    kegagalan permanen (HTTP 404/410 atau sudah `MAX_ATTEMPTS` = 3 kali gagal antar-jalan) -> ditulis,
    batas maju, kode 6, artikel ditandai "perlu tinjauan". Jalan yang ditahan tidak menulis berkas
    artikel dan tidak mengubah `state.json`; yang ditulis hanya `<jalan>_tertahan_<waktu UTC>_report.json`
    dan entri `failed_ids.json`. Perubahan perilaku: ambang 5% kini MENAHAN, bukan lagi "tulis lalu
    kode 3".
    *(2) Coba ulang (agenda (b)):* `python -m scraping.expand --retry-failed` mengambil ulang
    kegagalan TERBUKA dari URL tersimpan di `failed_ids.json` (bukan lewat penelusuran daftar) ->
    `data/expansion/retry_YYYY-MM-DD.json` + `retry_<waktu UTC>_report.json`; hasil sebagian tetap
    disimpan bila jaringan putus; `--include-permanent` untuk yang perlu tinjauan. `owned_ids` dan
    `forward_known_ids` menghitung `retry_*.json`. `--failed-status` memisahkan
    `id_bisa_dicoba_ulang` dan `id_perlu_tinjauan`. **Penggabungan ke `articles.json` tetap manual:
    berkas `retry_*.json` harus ikut digabung seperti kelompok lain.**
    Kode keluar `expand`: 0 bersih | 3 ditahan sistematis | 4 jaringan putus | 5 ditahan, akan dicoba
    lagi | 6 ditulis, ada yang perlu ditinjau. Data nyata saat ini: 210 entri, 0 terbuka.
    (o) **Pembaruan berkala, tahap scraping (2026-10-03 malam; BELUM dijadwalkan):**
    *Hitungan percobaan:* kegagalan JARINGAN tidak dihitung ke `MAX_ATTEMPTS` (keputusan pemilik
    proyek: internet mati beberapa hari tidak boleh menandai artikel sehat permanen;
    `attempts_by_id`). Konsekuensi: artikel yang terus gagal karena jaringan menahan jalan (kode 5)
    sampai berhasil atau `--accept-failures`.
    *Lapisan sumber data* (`src/scraping/source.py`): `expand` memakai `SOURCE` (dipilih
    `ARTICLE_SOURCE`, bawaan `html`); artikel dari sumber mana pun diperiksa skemanya
    (`ARTICLE_KEYS`); `yudistira` dikenali tetapi BELUM dibangun (NotImplementedError).
    *Catatan cakupan demo:* `presentation.evaluation_scope_note(n)`; angka pencarian terikat
    `RETRIEVAL_MEASUREMENT` (3 Oktober 2026, 1.532 artikel) dan jumlah artikel saat ini dibaca dari
    indeks lewat sqlite baca-saja (`count_indexed_articles`); bila berbeda, catatan menyebut angka
    itu belum tentu berlaku. **Bila pengukuran diulang, perbarui `RETRIEVAL_MEASUREMENT`.**
    *Pembungkus* `python -m scraping.scheduled` (peluncur `scripts/pembaruan_berkala.cmd`; uji
    `tests/test_scheduled.py`): kunci satu-instans, coba ulang kegagalan terbuka, mode maju,
    kualitas SELURUH antrean belum digabung (label di luar `REVIEWED_LABELS`, duplikat, tumpang tindih
    menahan penggabungan), status `data/expansion/pembaruan_status.json` + `pembaruan_riwayat.jsonl` +
    `logs/`, penanda `PERHATIAN_PEMBARUAN.txt` (di-gitignore; dihapus pada jalan bersih) dan notifikasi
    Windows. Kode keluar tambahan: 7 batas mode maju tak ditemukan, 8 galat tak terduga, 9 terkunci.
    Tiga kali beruntun ditahan sistematis -> berhenti mencoba sampai `--reset`.
    *Percobaan manual:* jalan nyata = 16 artikel baru, 0 gagal, kode 6 karena label baru `BELUM
    TERBUKTI`; simulasi jaringan mati sejak awal (halaman daftar gagal) dan putus di tengah (pemutus
    sirkuit) = kode 4, penanda dan notifikasi bekerja, tidak ada berkas artikel/`state.json` yang
    ditulis. Cacat yang ditemukan dan diperbaiki: jalan susulan menghapus penanda padahal antrean
    masih menahan. **Meninjau label baru = memutuskan tampilannya di `presentation.STATUS_ALIASES`
    (atau `STATUS_STYLES`) DAN menambahkannya ke `scheduled.REVIEWED_LABELS` (uji menjaga keduanya
    sama).** Rotasi cadangan "tiga terakhir" BELUM dibangun; dari empat cadangan, dua yang
    lebih lama dihapus 2026-10-03 atas perintah pemilik proyek (tersisa `pre_batch04-06_2026-10-03`
    dan `pre_ef_search_2026-10-03`, 89 MB).
    (p) **Label `BELUM TERBUKTI` (2026-10-03; keputusan pemilik proyek):** gaya SENDIRI, bukan alias:
    `STATUS_STYLES["BELUM TERBUKTI"]` = judul "Belum terbukti", warna `violet` (slot `violetColor`/
    `violetTextColor`/`violetBackgroundColor` di `.streamlit/config.toml`, `#6A3A9A`; kontras teks pada
    latar halaman 7,5:1), ikon `help`, kalimat persis: "Klaim ini sudah diperiksa TurnBackHoax.id dan
    belum ada bukti yang mendukungnya, sehingga belum dapat dianggap benar." -- TANPA saran medis atau
    kalimat lain. Alasan ungu: merah/jingga/kuning = skala bahaya, abu-abu = "belum ditemukan", hijau
    terkesan "benar", biru = aksen. `tests/test_theme.py` (baru) memastikan setiap warna status punya
    slot tema dan lolos kontras AA (4,5:1) pada latar halaman, latar sekunder, dan latar sendiri; uji
    presentasi memastikan tampilannya berbeda dari "belum ditemukan". Label ini masuk
    `scheduled.REVIEWED_LABELS`; pemeriksaan antrean dijalankan ulang tanpa scraping -> kode 0, penanda
    terhapus. Tampilan ungu di halaman demo belum dilihat langsung (hanya diuji lewat data tampilan
    dan konfigurasi).
    (d) **Baris "Sumber:" -- temuan awal (riwayat; keputusannya di butir (e)).** Letak: seksi Hasil Periksa Fakta
    (`section.article-factcheck`) pada 1.532/1.532 artikel (2 artikel juga memuat kata "Sumber:" di
    Narasi); 2.106 URL, 39 domain, 1.987 URL berdomain daftar-blokir. Keputusan pemilik proyek: baris
    itu dibaca sebagai sumber klaim, KECUALI bila ada artikel yang "Sumber:"-nya jelas bukan unggahan
    hoaks -> lapor dan berhenti. **Itu terjadi pada 3 artikel:** 32110 (`bpjs-kesehatan.go.id`, situs
    resmi yang juga satu-satunya rujukan tampil), 31532 (`cekbansos.kemensos.go.id`, situs resmi,
    satu-satunya rujukan tampil), 33497 (dua berita media arus utama, keduanya rujukan tampil).
    Menyaring semua URL "Sumber:" akan membuang rujukan sah itu. Lainnya di luar daftar-blokir:
    arsip (`arsip.cekfakta.com` 76, `megalodon.jp` 7, `perma.cc` 4, `archive.cob.web.id` 1), pemendek,
    `turnbackhoax.id` (3, tangkapan layar; sudah dikecualikan parser), Google Docs/Drive (33554,
    32772), satu domain penipuan (34525, sudah di `claim_sources`), `videotourl.com` (36622).
    **Masih tampil sebagai rujukan setelah (a)-(b):** arsip di luar daftar-blokir (`arsip.cekfakta.com`
    9 URL termasuk 35161 yang merupakan "Sumber:", `archive.fo` 2, `perma.cc` 1) -- belum diputuskan.
  - **Kelompok 6, JALAN PERTAMA (2026-10-02 ~23:30 WIB; riwayat): jalan berhenti dengan
    galat parse (kode keluar Python 1), BUKAN galat jaringan.** Jangkar 29646 ditemukan di halaman
    daftar 144; 110 URL terkumpul (s.d. halaman 155); 80 artikel berhasil (0 retry), lalu artikel
    ke-81, **29437**, melempar `ValueError: Invalid IPv6 URL` dari `urlparse` di
    `links.blocked_reason`: seksi Referensi di sumber memuat tautan cacat `http://kemenag.go.id]`
    (kurung siku nyasar). Galat di dalam `parse_article` tidak tertangkap sebagai kegagalan per
    artikel, jadi seluruh jalan gugur. **Tidak ada yang rusak:** `state.json` tidak maju (masih `batch`
    5, jangkar 29646), `batch_06.json` tidak ditulis, `failed_ids.json` tidak berubah; 81 HTML
    (termasuk 29437) sudah di cache (total 1.503), jadi jalan ulang hanya mengambil 29 artikel dari
    jaringan. **Diperbaiki 2026-10-03 (disetujui pemilik proyek):**
    (1) *URL tidak dapat diurai* (`links.py`): `blocked_reason` mengembalikan alasan `"URL tidak sah"`
    (`INVALID_URL_REASON`) sehingga URL itu disaring ke `references_filtered` dan tetap apa adanya di
    `references_raw` -- TIDAK diperbaiki (itu menebak isi sumber). Titik pengurai URL lain diperiksa:
    `normalize_url` (`urldefrag` melempar galat yang sama bila URL cacat memuat `#`) kini
    mengembalikan URL apa adanya; `discovery.find_article_urls` (`urljoin`) hanya memproses jalur
    `/articles/...` dan tidak melempar (diuji). Tidak ada pengurai URL lain di `src/`.
    (2) *Exception tak terduga saat mengambil/mem-parse satu artikel* (`expand.scrape_with_reason`):
    menjadi kegagalan artikel itu, jalan berlanjut; alasan `galat tak terduga: <Jenis>: <pesan>
    (<berkas>:<baris> <fungsi>)` dan jejak lengkap tercetak di log. **Setiap kegagalan kini berbidang
    `jenis`** di `failed_ids.json` dan laporan: `jaringan` | `galat_kode` (+ bidang `exception`) |
    `halaman_galat` | `parse_kosong` | `http_atau_lain`; laporan memuat `gagal_per_jenis` dan
    `exception_galat_kode`, `--failed-status` memuat `terbuka_per_jenis`, log menulis
    `GAGAL [jenis]: ...`. `galat_kode` tidak dihitung pemutus sirkuit. **Celah yang tetap ada:** jalan
    yang selesai dengan kegagalan non-jaringan tetap memajukan `state.json`, jadi artikel `galat_kode`
    tidak dicoba ulang mode mundur (HTML-nya ada di cache; terlihat sebagai "terbuka" di
    `--failed-status`).
    **Bukti (parse ulang 1.422 artikel dari cache, kode `00c4fb5` vs kode baru): 1.422/1.422 identik
    (hash keluaran sama); 0 artikel memuat URL tidak sah.** Indeks tidak perlu dibangun ulang.
  - **Kelompok 5, JALAN ULANG (2026-10-02 ~17:45-17:59 WIB; scraping SAJA, belum digabung/di-ingest):
    250/250 berhasil, 0 gagal, 0 retry (artikel 0, halaman daftar 0), kode keluar Python 0** (dicatat
    di baris terakhir `batch_05.log`, diperiksa dari berkas). Sebelumnya: catatan kejadian disalin ke
    `data/expansion/insiden_2026-09-28_batch05/` (salinan byte `state.json`, `batch_05.json`,
    `batch_05_report.json`, `batch_05.log`, `failed_ids.json`; jangan diubah), `state.json`
    dikembalikan ke keadaan setelah kelompok 4 (`batch` 4, jangkar 30876, `start_page` 118, 1.150
    `known_ids`), koneksi diuji (200, 2,2 dtk), dijalankan dengan `--start-page 116`.
    - Jangkar 30876 ditemukan di halaman daftar **119** (28 Sep: 118); halaman daftar s.d. 144. Himpunan
      250 id sama persis dengan jalan 28 Sep (id 29646-30875); 40 artikel yang dulu berhasil terbaca
      dari cache dan identik. 0 duplikat; 0 tumpang tindih dengan 922 artikel dan kelompok 4.
    - **2025-10-23 s.d. 2025-12-17** (55 hari, ~4,5 artikel/hari). Label: SALAH 202, PENIPUAN 39,
      PARODI 4, KOMEDI 1 (30793), SATIR 1 (30644), TIDAK DIKETAHUI 3 di `batch_05.json`/laporan jalan:
      29847 `[SALAH} ...` (penutup kurung kurawal), 29812 dan 29787 `[SALAH] ...` berkurung lengkap
      tetapi diawali U+200B (spasi lebar-nol). **Diperbaiki 2026-10-02 di `parse_title` (keputusan
      pemilik proyek; Aturan Wajib #7):** karakter tak terlihat dibuang dari JUDUL sebelum dicocokkan
      (isi seksi TIDAK dinormalkan; `title_raw` tetap asli), dan pola kurung rusak menerima penutup
      `}` tepat setelah label yang dikenal. **Bukti (parse ulang 1.422 artikel dari cache, parser lama
      vs baru): 1.419 identik, 3 berubah, hanya bidang `title` dan `label` (ketiganya -> SALAH);
      data tersimpan == parser lama 1.422/1.422.** Jadi `articles.json` (922) dan indeks TIDAK
      berubah -- tidak perlu `--rebuild`. `batch_05.json` di disk BELUM ditulis ulang (masih memuat 3
      `TIDAK DIKETAHUI`); `scraping.reparse` sebelum penggabungan akan menerapkannya. Label kelompok
      5 setelah reparse: SALAH 205, PENIPUAN 39, PARODI 4, KOMEDI 1, SATIR 1.
    - **Seksi kosong: 2 artikel, kosong DI SUMBER (bukan galat parse/halaman galat):** 29687
      (Penjelasan hanya judul seksi) dan 29670 (PARODI; Narasi DAN Penjelasan hanya judul seksi, yang
      ada Kesimpulan saja). **Keputusan pemilik proyek 2026-10-02: keduanya IKUT DIGABUNG apa
      adanya** (data sah; PARODI sudah sangat sedikit). `chunker` melewati seksi kosong, jadi 29687
      punya 2 chunk dan **29670 hanya punya chunk Kesimpulan -- hanya terjangkau retrieval lewat
      Kesimpulan** (seksi yang pada ablasi v1 paling lemah untuk pencocokan klaim), dan konteks LLM
      untuknya tanpa Narasi. Saat ingest, pemeriksaan "0 seksi kosong" akan melaporkan 2 artikel ini:
      itu diharapkan.
    - Halaman galat lolos validasi: tidak ditemukan (250 cache lolos validasi, 0 teks galat, ukuran
      35-50 KB, reparse dari cache identik 250/250, 0 artikel memuat `\r`, 0 `.tmp`; total cache 1.422).
      Kesimpulan lebih pendek pada Okt-Nov 2025 (median 140/137 karakter; Des 243; acuan 239): gaya
      redaksi periode itu (satu kalimat "Unggahan berisi klaim ... merupakan konten palsu", tanpa
      kalimat "Faktanya"), 18 Kesimpulan di bawah minimum acuan 114 (terpendek 91). `references` kosong
      33/250, `claim_sources` kosong 23/250 (acuan 145 dan 73 dari 1.172).
    - **30089 MASUK** (SALAH, 16/11/2025; Narasi 1.027 / Penjelasan 519 / Kesimpulan 244 karakter;
      `references` kosong setelah penyaringan). Verifikasi top-3 v1-029 menunggu ingest.
    - `state.json`: `batch` 5, jangkar 29646, `start_page` 144, 1.400 `known_ids`. `failed_ids.json`
      tidak berubah (210 entri kejadian 28 Sep); status turunan: **210 teratasi, 0 terbuka**;
      `gagal_terbuka` di laporan `[]`. Dimiliki total 1.422 artikel (922 + 250 + 250).
    - Di bilah samping situs terlihat label `[BELUM TERBUKTI]` (belum ada di data kita); bila kelak
      masuk, ia akan jatuh ke tampilan netral dan tercatat di log.
    - Sisa menuju akhir Sep 2025: ~23 hari (23 Okt -> 30 Sep) -> ~100 artikel pada 4,5/hari (perkiraan).
  - **Kelompok 5, JALAN PERTAMA / KEJADIAN (2026-09-28 ~19:00-20:40 WIB; diperiksa 2026-10-02 dari
    berkas; butir di bawah ini riwayat -- keadaan `state.json` dan 30089 sudah digantikan jalan ulang
    di atas): 40/250 berhasil, 210 GAGAL (84%).** Log
    berakhir `BERHENTI: tingkat gagal 84.0% > 5%`; menurut kode jalur itu mengembalikan kode keluar
    **3**, bukan 0 (kode keluar 0 yang teramati pemilik proyek tidak dapat diverifikasi dari berkas;
    dugaan: yang terbaca adalah kode keluar pipa/pengalihan log, belum diuji). Ambang 5% hanya
    diperiksa SETELAH seluruh 250 dicoba, jadi jalan tidak berhenti lebih awal.
    - *Yang berhasil (40):* urutan 1-38, 40, 41; id 30595-30875; 2025-12-08 s.d. 2025-12-17
      (bersambung dengan kelompok 4); 0 seksi kosong; 0 duplikat; 0 tumpang tindih dengan 922 artikel
      maupun kelompok 4; 0 memuat `\r`. Label: SALAH 30, PENIPUAN 6, PARODI 2, SATIR 1 (30644),
      **KOMEDI 1 (30793) -- label BARU berkurung lengkap** (`[KOMEDI] ...` di `<h1>` cache), diterima
      apa adanya (Aturan Wajib #7); **diputuskan 2026-10-02:** ditampilkan dengan gaya PARODI
      (`STATUS_ALIASES`, bersama SATIRE/SATIR).
    - *Yang gagal (210):* id 29646-30600; ConnectionError 209, ReadTimeout 1, semuanya setelah 4
      percobaan (retry artikel 630 = 210 x 3; halaman daftar 0). Waktu di `failed_ids.json`:
      2026-09-28 12:10:09 s.d. 13:40:16 UTC (19:10-20:40 WIB), beruntun dari urutan 42 sampai 250
      tanpa satu pun keberhasilan -> jaringan putus total, bukan putus-nyambung. `failed_ids.json`
      (210 entri, semuanya `batch_05`, id unik 210) sama persis dengan `id_gagal` di laporan.
      **30089 (artikel asal v1-029) termasuk yang GAGAL** (12:52:36 UTC, ConnectionError); tidak ada
      di cache. Verifikasi top-3 v1-029 belum dapat dilakukan.
    - *Halaman galat lolos validasi: tidak ditemukan.* 40 cache lolos `is_valid_article_html`, 0
      memuat teks "Terjadi kesalahan saat mengambil data" (juga 0 pada seluruh 1.212 berkas cache),
      ukuran terkecil 37 KB, median 42,6 KB (median seluruh cache 42,8 KB), reparse dari cache identik dengan
      `batch_05.json` (40/40). Tidak ada artikel gagal yang punya cache; tidak ada `.tmp` tersisa.
      Panjang seksi dibanding 1.172 artikel acuan (922 + kelompok 4): tidak ada yang di bawah
      minimum acuan; satu di bawah persentil-1: 30875 Penjelasan 364 karakter (p1 acuan 430, minimum
      acuan 226) -- pendek tetapi artikel sah. `references` kosong 8/40 (penyaringan domain, perilaku
      yang sudah dikenal).
    - **`state.json` SUDAH MAJU:** `batch` 5, jangkar 29646, `start_page` 143, `known_ids` 1.400
      (memuat 210 id gagal). Ini celah yang sudah dicatat di "Perilaku gagal": mode mundur tidak
      pernah mencoba ulang id di `known_ids`. **Menunggu keputusan pemilik proyek**, dua jalan:
      (1) kembalikan `state.json` ke keadaan setelah kelompok 4 (`batch` 4, jangkar 30876,
      `start_page` 118, `known_ids` dikurangi 250 id kelompok 5 -> 1.150) lalu jalankan ulang
      kelompok 5 (40 artikel terbaca dari cache, 210 dari jaringan; `batch_05.*` tertimpa,
      `failed_ids.json` hanya bertambah); atau (2) bangun langkah coba-ulang agenda (b) yang membaca
      `failed_ids.json`. Belum ada yang dikerjakan; `state.json` tidak diubah.
    - Cakupan tanggal 210 artikel gagal tidak diketahui (tidak terambil), jadi perkiraan sisa
      artikel pada butir kelompok 4 belum dapat diperbarui.
  - **Pemutus sirkuit di `expand.py` (2026-10-02, setelah kejadian kelompok 5):** jalan berhenti
    (kode keluar **4**) setelah `MAX_CONSECUTIVE_NETWORK_FAILURES` artikel BERUNTUN gagal karena
    jaringan (alasan `<Timeout|ConnectionError|SSLError|ProxyError> setelah N percobaan`). 404,
    halaman galat, dan gagal parse TIDAK dihitung dan justru mengembalikan hitungan ke nol bila
    berasal dari jaringan (server terbukti terjangkau), begitu juga artikel yang berhasil diambil
    dari jaringan; artikel dari cache tidak mengubah hitungan. **Nilai 5 disetujui pemilik
    proyek 2026-10-02** (5 artikel = 20 permintaan gagal beruntun, ~2 menit pada laju
    kelompok 5; dapat ditimpa `--max-network-failures`). Jalan yang terputus TIDAK menulis
    `batch_NN.json`/`forward_*.json` dan TIDAK memajukan `state.json` (perintah yang sama dapat
    dijalankan ulang; yang sudah berhasil terbaca dari cache); yang ditulis hanya
    `<jalan>_terputus_<waktu UTC>_report.json` dan entri `failed_ids.json`. Jalur lama tidak berubah:
    ambang 5% tetap diperiksa di akhir dan pada jalur itu `state.json` TETAP maju (celah lama untuk
    kegagalan non-jaringan, belum diperbaiki). Uji: `tests/test_expand.py` (putus total berbentuk
    kelompok 5, artikel rusak beruntun pada jaringan normal, putus-nyambung, cache, `main`, mode
    maju); dua mutasi kontrol menggagalkan uji yang sesuai.
    **`failed_ids.json` adalah catatan KEJADIAN, bukan status:** entri tidak dihapus saat artikelnya
    kemudian berhasil. Statusnya DITURUNKAN, tidak disimpan (disetujui 2026-10-02): "terbuka" = pernah
    gagal dan tidak ada di `articles.json`/`batch_*.json`/`forward_*.json`; "teratasi" = pernah gagal
    tetapi kini dimiliki. Lihat dengan `python -m scraping.expand --failed-status` (tanpa jaringan);
    setiap laporan kelompok/maju memuat `gagal_terbuka`. Ini BUKAN alat coba-ulang agenda (b).
  - **Tampilan label tak dikenal kini NETRAL (2026-10-02, keputusan pemilik proyek):** label di luar
    SALAH/PENIPUAN/PARODI dan aliasnya tampil abu-abu, ikon `label`, judul "Sudah diperiksa", dengan
    kalimat yang hanya menyatakan klaim sudah diperiksa dan diberi label aslinya (dikutip apa
    adanya) -- tidak lagi bergaya atau berkalimat SALAH. Label kosong/`TIDAK DIKETAHUI` memakai
    kalimat "label ... tidak terbaca". Setiap kemunculan dicatat `logger.warning` (logger
    `presentation`, dengan label dan id artikel). KOMEDI -> gaya PARODI; ringkasan PARODI diubah
    menjadi "konten humor (parodi, satire, atau komedi), bukan berita sungguhan" agar pas untuk
    ketiga alias (judul status tetap "Parodi"). **Label unik seluruh data (1.212 artikel: 922 +
    kelompok 4 + 40 kelompok 5):** SALAH 791, PENIPUAN 407, PARODI 10, SATIR 2, SATIRE 1, KOMEDI 1;
    0 `TIDAK DIKETAHUI`; tidak ada label yang jatuh ke tampilan netral saat ini.
  - **Kelompok 3 (2026-09-27; scraping):** 250/250
    berhasil, 0 seksi kosong, 2026-02-02 s.d. 2026-03-31 (halaman daftar 68-93; 0 id tumpang tindih
    dengan 672 artikel). Label: SALAH 175, PENIPUAN 73, PARODI 2, TIDAK DIKETAHUI 0. Retry: artikel
    0, halaman daftar 1 (halaman galat, berhasil pada percobaan ke-2). `failed_ids.json` tidak
    dibuat (0 gagal). 6 artikel masih memuat `\r` (diambil dengan parser lama) -> wajib reparse
    sebelum digabung.
  - **Metrik dipantau: chunk terpotong 512 token per seksi** -- laporkan SETIAP kali indeks
    ditambah atau dibangun ulang (`ingest.py` mencetaknya di awal lewat `truncation_report`).
    Riwayat (Narasi / Penjelasan / Kesimpulan dari total chunk): 150 artikel 0/3/0 dari 450; 672
    artikel 0/8/0 dari 2016; **922 artikel 1/9/0 dari 2766** (Narasi pertama yang terpotong: 532
    token). Pemecahan sub-chunk TIDAK diterapkan; diputuskan di Versi 2 bersama agenda penghapusan
    Penjelasan (agenda (a) di bawah).
  - **Dampak perluasan pada retrieval set uji v1 (2026-09-27; tanpa API):** ablasi pada salinan
    arsip identik dengan `testset/retrieval_ablation.json` (pembanding sah). Produksi 922:
    `testset/retrieval_ablation_prod922.json`/`_report.txt`; per butir:
    `testset/v1_perbandingan_indeks_922.json` (`evaluation.index_comparison`). Recall@1/3/5/10/20
    arsip -> produksi: **positif 19,20,20,20,20 -> 18,20,20,20,20 (dari 20)**; negatif sulit (sasaran
    = artikel tetangga) 14,16,18,19,20 -> 9,11,13,15,18; non-batas 33,36,38,39,40 -> 27,31,33,35,38
    (dari 40). Negatif: 16 -> 23 dari 30 punya kandidat top-3 > 0,5739; **artikel asal 4 butir negatif
    (v1-021, v1-022, v1-043, v1-049) kini ADA di basis data** (peringkat 1). Label negatif set uji v1
    tidak otomatis berlaku pada indeks besar (`v1.meta.json`, `keterikatan_basis_data_150_2026-09-27`).
    Kelompok 4 MENUNGGU keputusan pemilik proyek setelah melihat hasil ini.
    **2026-09-28:** status 4 butir itu dicatat (`v1.meta.json`
    `butir_negatif_berubah_status_indeks_922_2026-09-28`, `v1_temuan_untuk_v2.md` bagian 8, termasuk
    persyaratan set uji Versi 2: butir negatif diverifikasi dan diberi versi bersama snapshot basis
    data). **v1-050 = butir kelima (terverifikasi):** 36775 (mode maju, 21 Sep) di peringkat 1 top-3
    retriever produksi (0,6330); Narasinya mengutip teks butir persis ("Suhasasil"). Bersumber Liputan6
    (17 Sep), bukan arsip -> butir dari situs cek fakta lain pun bisa berubah status; pemeriksaannya kini
    WAJIB untuk set uji Versi 2. Artikel asal v1-029 (30089, Nov 2025) akan masuk saat perluasan ke Sep 2025.
  - **Agenda (dicatat 2026-09-27, JANGAN diterapkan terpisah; keputusan pemilik proyek):**
    (a) *Chunk terpotong 512 token:* yang terpotong hanya INPUT embedding (`model.max_seq_length`);
    teks chunk tersimpan utuh. Usulan: pecah seksi > 510 token di batas paragraf menjadi
    `{id}_{seksi}_1`, `_2`, ... (metadata `section` sama + nomor bagian, tumpang tindih satu kalimat;
    agregasi per artikel tidak berubah). Mengubah id chunk -> wajib `--rebuild`, dan agenda Versi 2
    masih menimbang menghapus Penjelasan dari indeks, jadi **keduanya diputuskan bersama**.
    (b) *Coba ulang artikel gagal:* langkah terpisah yang membaca `failed_ids.json` dan mengambil
    ulang dari URL tersimpan (bukan lewat penelusuran daftar); "terbuka" = gagal dan belum pernah
    berhasil; batas 3 percobaan antar-jalan, 404 langsung permanen (tinjau manusia); hasil ke
    `retry_YYYY-MM-DD.json`. `state.json.known_ids` tetap berarti "sudah dicoba" (kursor mode
    mundur); "dimiliki = berhasil" dihitung dari `articles.json` + berkas hasil. Titik henti mode maju
    tidak berubah; tanpa langkah ini artikel gagal di mode maju tak pernah terjangkau lagi.
  - **Mode maju (`--forward`, 2026-09-27):** dari halaman daftar 1 ke belakang, berhenti pada
    artikel pertama yang sudah dimiliki; keluaran `forward_YYYY-MM-DD[_report].json` (tanggal WIB),
    `state.json` tidak diubah. **Dasar pembaruan berkala nanti** -- logikanya sama, hanya perlu
    dijadwalkan (penjadwalan BELUM dibangun, sengaja). Jalan pertama: 22/22 berhasil, 0 seksi
    kosong, 2026-09-19 s.d. 2026-09-27, SALAH 11 / PENIPUAN 11; titik henti 36738 (artikel terbaru
    basis, halaman daftar 3). Cakupan kini bersambung 26 Mei-27 Sep 2026.
  - **Validasi ujung-ke-ujung (2026-09-27, atas permintaan pemilik proyek, SEBELUM kelompok 3):**
    672 artikel (mode maju 22 + basis 150 + kelompok 1-2 500) digabung ke `data/articles.json`
    (urutan: maju, basis, kelompok 1, kelompok 2), di-parse ulang dari cache (`scraping.reparse`,
    menerapkan Aturan Wajib #7), lalu di-ingest inkremental (1566 chunk baru; 26 mnt CPU). 0 artikel
    gagal, 0 tidak sesuai skema (kunci/tipe sama dengan basis), 0 duplikat id. `index_check`: INDEKS
    SEGAR, 2016 chunk, kosinus sampel 1,000000. Chunk terpotong 512 token: 8 (semua Penjelasan).
    Label: SALAH 387, PENIPUAN 280, PARODI 5, TIDAK DIKETAHUI 0. Uji retrieval 4 kueri (lama dan
    baru): artikel benar di peringkat 1 semua. Proses ingest sempat dihentikan Claude Code (memori
    sistem rendah) SETELAH semua chunk tersimpan; hanya ringkasan akhir yang hilang. **Demo kini
    memakai indeks 672 artikel**; pembandingan baseline tetap wajib lewat `archive/v1` (#6).
    - Reparse mengubah 10 artikel kelompok baru hanya pada `\r` -> `\n` (teks dari jaringan memuat
      `\r`, dari cache tidak). **Hasil scraping wajib lewat `scraping.reparse` sebelum digabung.**
    - Cadangan metadata: `manifests/expansion_article_ids.json` (522 artikel: id, url, tanggal,
      label, kelompok; di-commit). Pemulihan dari cache diuji: 522/522 identik dengan `articles.json`.
  - **Perilaku gagal (diperiksa 2026-09-27):** retry (`scraping.client`: 3x, backoff 2/4/8 dtk,
    hanya timeout/connection error/halaman galat) TERCETAK di log (`[retry i/3]`), tidak
    tersembunyi; log kelompok 1-2 dan mode maju: 0 retry, 0 gagal. Tetapi laporan kelompok tidak
    menghitung retry. **Celah:** artikel yang gagal TIDAK dicoba ulang di jalan berikutnya (mode
    mundur memasukkannya ke `known_ids`; mode maju berhenti di artikel dimiliki yang lebih baru).
    Halaman daftar gagal -> RuntimeError (keras). Belum diperbaiki.
    **Sejak 2026-09-27:** setiap artikel gagal (kedua mode) langsung ditambahkan ke
    `data/expansion/failed_ids.json` (hanya ditambah, tidak pernah ditimpa; id, url, alasan, retry,
    jalan, waktu UTC), dan laporan kelompok/maju memuat `retry` (artikel, halaman_daftar) serta
    `id_gagal`. Semantik `state.json` tidak diubah. Percobaan ulang otomatis BELUM ada (rancangan:
    langkah coba-ulang terpisah yang membaca `failed_ids.json`, bukan lewat penelusuran daftar).
  - **Baris baru (diperbaiki 2026-09-27):** cache ditulis dengan `newline=""` (sebelumnya mode teks
    Windows mengubah CRLF server menjadi CR CR LF, terbaca sebagai baris kosong palsu; 14 berkas cache
    lama tetap begitu, sengaja tidak diubah agar `articles.json` tidak berubah) dan `parse_article`
    menormalkan CRLF/CR -> LF. Hasil parse jaringan kini identik dengan hasil parse cache (diuji);
    672 artikel yang ada tidak berubah (reparse identik). Reparse sebelum penggabungan tetap dianjurkan
    untuk hasil kelompok yang diambil dengan kode lama (termasuk kelompok 3).
  - **Cakupan waktu (koreksi 2026-09-27):** kelompok 1 = ~71 hari untuk 250 artikel (~3,5 artikel/
    hari), jadi 1.000 artikel ~9-10 bulan ke belakang, bukan ~13 bulan seperti perkiraan awal.
    Laju bisa berbeda di periode lain.

- **Demo lokal (2026-09-25):** `src/app.py` (Streamlit, adapter tipis; tidak ada logika
  retrieval/generasi sendiri) + `src/presentation.py` (data tampilan, tanpa Streamlit, diuji
  offline di `tests/test_presentation.py`) + `.streamlit/config.toml` (satu-satunya tempat kode
  warna). Jalankan: `.\.venv\Scripts\python.exe -m streamlit run src\app.py`. Panel diagnostik
  hanya di mode penguji (`DEMO_TESTER_MODE=1` atau `demo_tester_mode = true` di
  `.streamlit/secrets.toml`, di-gitignore; bawaan mati). Hasil "belum ditemukan" menampilkan
  artikel "mungkin terkait" (skor >= 0,57; dasar ambang di komentar `RELATED_SCORE_THRESHOLD`)
  TANPA mengubah vonis. Demo berbagi kuota harian (RPD 500) dengan evaluasi.
  **Sejak 2026-09-28 ambang dibaca per indeks dari `config/related_threshold.json`** (dengan jumlah
  chunk saat kalibrasi; ukuran berbeda -> fitur mati sampai dikalibrasi ulang). Indeks `data` (922):
  **DIMATIKAN** -- pada set pengembangan tak ada ambang pemisah (kueri tak terkait "bumi datar"
  0,6385 di atas kandidat layak 0,5739-0,63; ambang 0,64 bermargin 0,0015), BUKAN karena topik jauh
  lolos pada set uji v1 (6 negatif mudah tak terkait tetap < 0,57);
  `archive/v1`: 0,57.
  `generator.py`, prompt, `retriever.py`, dan `v1.jsonl` tidak disentuh (uji kunci lolos).
- **Eksperimen ablasi retrieval (2026-09-25; pengukuran, BUKAN penyetelan -- parameter produksi
  tidak diubah):** `src/evaluation/retrieval_ablation.py`, hasil `testset/retrieval_ablation.json`
  dan `_report.txt`, ringkasan + status tiap parameter di `testset/v1_temuan_untuk_v2.md` bagian
  5-6. Inti: top-k dan agregasi tidak menunjukkan selisih bermakna; Narasi saja = seluruh seksi
  (Penjelasan tidak menyumbang recall), Kesimpulan saja turun bermakna (-6/40); klaim ~5.000
  karakter dengan pembuka panjang jatuh ke Recall@3 2/20 karena klaim terpotong di luar 512 token.
- **Tindak lanjut ablasi (2026-09-25):** batas masukan demo diturunkan 5.000 -> **1.500**
  karakter dan ada peringatan pesan panjang (token bge-m3, ambang 220) SEBELUM pemeriksaan.
  Keterbatasan 512 token dicatat sebagai **keterbatasan utama** (lihat "Keterbatasan yang
  Diketahui", README, `v1_temuan_untuk_v2.md`). Rasional Aturan Wajib #2 dikoreksi: peran
  Narasi kembali didukung data. Parameter produksi lain tidak berubah.
- **Jalur data resmi untuk tahap 3 (dicatat 2026-09-26, belum dipakai):** Mafindo menyediakan API
  publik (host `https://yudistira.turnbackhoax.id/api/`, "Yudistira"); dokumentasi
  https://mafindodocs.netlify.app/ (terakhir diperbarui Agustus 2022, mungkin usang); API key lewat
  halaman kontak TurnBackHoax -- pemilik proyek sudah mengajukan permintaan. Dokumentasi mengundang
  pengembang memakai ulang basis datanya. Menurut dokumentasi v2, objek News punya bidang terpisah
  `content`, `fact`, `conclusion`, `references`, `source_link` (pemetaan ke Narasi/Penjelasan/
  Kesimpulan/Referensi/sumber hoaks BELUM diverifikasi). **Implikasi tahap 3:** bila key diberikan dan
  respons memisahkan seksi setara HTML, perluasan basis data sebaiknya lewat API, bukan scraping; bila
  tidak memisahkan seksi, chunking per seksi (Aturan Wajib #2) tidak dapat diterapkan dan wajib
  dievaluasi dulu. **Sumber data Versi 1 dan indeks arsip `archive/v1` tidak boleh diganti dalam keadaan
  apa pun.** Rincian: `v1.meta.json` (`jalur_data_resmi_yudistira_2026-09-26`).
- **Penutupan tahap 2 (2026-09-26): pemeriksaan data terpublikasi.** Rincian di `v1.meta.json`
  (`pemeriksaan_data_terpublikasi_2026-09-26`). (1) `tests/fixtures/` DISAMARKAN lewat
  `tests/anonymize_fixtures.py` (teks isi -> kata semu sepanjang aslinya, tautan sumber hoaks ->
  jalur fiktif di domain sama, nomor/surel -> fiktif); jumlah assert sama (90) dan 14 mutasi kontrol
  negatif memberi himpunan uji gagal identik dengan fixture asli. (2) Nomor di catatan PII Gemma
  diganti `0800-0000-0000` -- ternyata BUKAN karangan model, melainkan nomor penipu dari Narasi
  36191 yang disalin Gemma. (3) Pemeriksaan PII Gemma kini tetap: `pii_flags` diperluas (URL tanpa
  skema, en-dash, wa.me), keluaran mentah diperiksa, `assert_pii_checked` sebelum menulis.
  (4) Riwayat git TIDAK ditulis ulang (keputusan pemilik proyek). (5) `archive/v1/article_ids.json`
  (metadata saja) di-commit; pemulihan arsip lewat `python -m scraping.restore` (lihat README).
  `articles.json` TIDAK di-commit: 12/150 artikel (semuanya PENIPUAN) memuat nomor telepon/wa.me dan
  62/150 memuat domain di luar daftar media/pemerintah/cek fakta/platform sosial (klasifikasi
  heuristik; di dalamnya domain yang tampak phishing, mis. subdomain vercel.app dan bit.ly).
- **Tahap 2 SELESAI: arsip indeks Versi 1 (2026-09-25).** `archive/v1/` = salinan `data/chroma` +
  `articles.json` (9,51 MB, di-gitignore). Sidik jari isi di `v1.meta.json`
  (`arsip_indeks_v1_2026-09-25`); diverifikasi: sama dengan indeks utama, `index_check` lolos,
  ablasi retrieval pada arsip identik dengan yang tercatat. Pemilihan indeks: `RAG_INDEX_DIR`.
  **Aturan Wajib #6: pembandingan dengan baseline Versi 1 wajib memakai arsip.** Tahap berikutnya:
  perluasan basis data (indeks utama `data/`), lalu Versi 2.
- **Temuan ChromaDB (2026-09-25):** berkas indeks ditulis ulang setiap kali koleksi dibuka,
  juga oleh evaluasi -- lihat "Berkas indeks ChromaDB ditulis ulang setiap kali dibuka" di
  "Temuan Ingestion dan Retrieval". Relevan untuk tahap pengarsipan indeks: arsipkan berkas
  SEKALI lalu jangan buka arsipnya langsung (buka salinannya), dan verifikasi dengan isi, bukan
  hash byte.

- Set uji v1 beku (tag `testset-v1`, sidik jari generator dikunci di
  `v1.meta.json.sidik_jari_generator_v1`, ditegakkan `tests/test_testset_locks.py`), dievaluasi
  3 run x 54 butir, dianalisis (`src/evaluation/testset_eval.py` + `testset_analysis.py`, hasil
  di `testset/v1_analysis.json`/`.txt`). **Angka utama dan status H1/H3 ada di "Status
  Pengembangan" di atas** -- jangan diulang manual di sini, itu satu-satunya sumber ringkas.
- Temuan untuk Versi 2 (kegagalan retrieval vs kegagalan generator, dipetakan ke komponen
  target) ada di `testset/v1_temuan_untuk_v2.md`. Batas tafsir H1 (3 dari 4 kegagalan recall@3
  membuat subtipe pola_sama_entitas_beda sebenarnya hanya teruji pada 17/20, bukan 20/20) ada di
  `v1.meta.json.hasil_evaluasi_v1_2026-09-23.batas_tafsir_H1_recall_2026-09-23`.
  `v1.jsonl`/prompt/generator TIDAK diubah oleh analisis lanjutan ini (diverifikasi tetap lolos
  uji kunci).
- **Riwayat penyusunan set uji v1** (label emas, keputusan 36700, gap PII, kolom `subtipe`,
  pasangan minimal, ketergantungan antar-butir, dll.) ada lengkap di `v1.meta.json` -- tidak
  diringkas ulang di sini karena sudah tidak berubah (bagian dari sejarah pembekuan, bukan
  status yang sedang berjalan).
- **Sudah di-commit & push:** seluruh pekerjaan Versi 1 termasuk tag `testset-v1`, lalu demo
  (2026-09-25; dua commit: demo + uji, dokumentasi), di `origin`. `.env` terverifikasi tidak
  ter-track.
- **Belum dimulai:** pengarsipan indeks Versi 1, perluasan basis data, dan Versi 2 (Corrective
  RAG) -- lihat "Status Pengembangan" di atas dan `testset/v1_temuan_untuk_v2.md` untuk pemetaan
  temuan ke komponen; rancangan implementasi belum ada.

---

## Ringkasan Proyek

Sistem RAG (Retrieval-Augmented Generation) untuk verifikasi klaim
berbahasa Indonesia. Pengguna memasukkan sebuah klaim atau pesan yang
ingin dicek, sistem mencari kecocokan pada basis pengetahuan artikel cek
fakta TurnBackHoax.id, lalu mengembalikan status verifikasi, klarifikasi
fakta yang sebenarnya, dan tautan rujukan yang sahih.

Proyek ini adalah proyek portofolio dengan tujuan pembelajaran. Nilai
utamanya ada pada kejelasan arsitektur dan kualitas evaluasi, bukan pada
kelengkapan fitur.

## Status Pengembangan

Proyek dibangun bertahap dalam dua versi:

- **Versi 1 — RAG dasar (SELESAI DAN TERUKUR, 2026-09-23).** Pipeline linear:
  scraping, chunking, embedding, penyimpanan vektor, retrieval berbasis
  kemiripan, generasi jawaban (`gemini-3.5-flash-lite`, thinking medium).
  Dievaluasi pada set uji v1 beku (tag `testset-v1`, 54 butir: 50 utama + 4
  batas), 3 run, 0 kegagalan panggilan. **Angka utama** (keputusan modus,
  metrik pra-registrasi; rincian dan caveat wajib di
  `testset/v1_analysis_report.txt` dan `v1.meta.json.hasil_evaluasi_v1_2026-09-23`):
  - Akurasi non-batas: **48/50**, Wilson95 [0,865; 0,989].
  - H1 (LLM membedakan klaim identik dari bertetangga topik): **TERDUKUNG**,
    tapi lihat catatan basis-teruji di bawah.
  - H3 (model kelas Flash cukup untuk tugas ini): **TERDUKUNG** pada sampel ini.
  - Recall@3: 36/40 non-batas -- 3 dari 4 kegagalan recall membuat H1 pada
    subtipe *pola_sama_entitas_beda* sebenarnya hanya teruji pada 17 dari 20
    butir negatif sulit (kecocokan palsu 1/17, bukan hanya 1/20 basis penuh).
  - Diagnostik penting: **seluruh** kesalahan dan ketidakbulatan antar-run
    generator (7 butir) terjadi ketika artikel yang benar SUDAH tersedia di
    top-3 -- kegagalan itu murni penilaian LLM, bukan retrieval.
  - Temuan lengkap untuk rancangan Versi 2 (kegagalan retrieval vs generator,
    dipetakan ke komponen target): `testset/v1_temuan_untuk_v2.md`.
- **Versi 2 — RANCANGAN DISUSUN 2026-10-03, BELUM ADA KODE: `docs/rancangan_v2.md`.** Dua belas
  pertanyaan sudah dijawab pemilik proyek (bagian 0 dokumen itu): **cakupan dipersempit menjadi
  penanganan pesan panjang + pengukuran kebersihan rujukan**; grader, "Mungkin terkait"/verdict
  ketiga, gaya klarifikasi, penghapusan Penjelasan, juri LLM, dan LangGraph TIDAK masuk; pipeline
  Python biasa; uji kemunduran = set uji v1 pada `archive/v1` (hanya sah untuk "tidak lebih buruk"),
  uji kemampuan baru = butir pesan panjang baru pada snapshot baru; `retriever.py` dikunci dengan
  hash sebelum evaluasi; pedoman anotasi 1.1 (tambahan) dan hipotesis dikunci sebelum pelabelan.
  **RANCANGAN BELUM BOLEH DILANJUTKAN: langkah pertama adalah mengukur pada pesan berantai ASLI
  apakah klaim memang sering berada di luar 512 token (dokumen bagian 10); metode penentuan posisi
  klaim dan kerangka sampelnya MENUNGGU persetujuan pemilik proyek -- jangan mengambil sampel
  sebelum itu, dan jangan memakai LLM untuk menentukan posisi klaim tanpa persetujuan.**
  Perhitungan ukuran sampel: `python -m evaluation.sample_size` -> `testset/v2_ukuran_sampel.json`.
  **HASIL PENGUKURAN PANJANG (2026-10-03; `testset/v2_pesan_berantai_ringkasan.json`, dokumen bagian
  10.7): 0 dari 100 pesan Liputan6 dan 0 dari 100 pesan arsip TurnBackHoax melebihi 512 token**
  (maks 312 dan 297 token; Wilson95 [0; 3,7%] per sumber; tahan terhadap cara pengukuran). Yang
  diukur adalah pesan sebagaimana DIKUTIP artikel cek fakta, bukan pesan yang ditempel pengguna.
  Metode yang disetujui: "terkena" didefinisikan dari sisi kegagalan Versi 1 saja; kandidat artikel
  sasaran dicari dari judul, bukan dari pesan panjang; penandaan posisi klaim dan konfirmasi artikel
  sasaran dikerjakan pemilik proyek TANPA bantuan AI. **Berkas penandaan TIDAK disiapkan; cakupan
  Versi 2 MENUNGGU keputusan pemilik proyek atas hasil ini.**
  **Arah yang sedang ditimbang pemilik proyek (2026-10-03, BELUM ada rancangan, belum ada yang
  dibangun): menangani klaim yang kini dijawab "belum ditemukan".** Langkah ukur: mencocokkan 100
  artikel Liputan6 dari sampel di atas dengan 1.532 artikel basis data untuk mengetahui berapa yang
  juga diperiksa TurnBackHoax. Kandidat dicari dari JUDUL Liputan6 (embedding top-5 + kata kunci pada
  judul), bukan dari pesannya; **kecocokan dikonfirmasi pemilik proyek sendiri, dengan pilihan "tidak
  ada yang cocok"**. Pengelompokan otomatis terbukti tidak dapat dipercaya ke dua arah, jadi keseratus
  butir perlu dikonfirmasi. **Keputusan pemilik proyek 2026-10-04: 50 butir acak berbenih
  (20261004); AMBANG ditetapkan sebelum data dilihat dan dicatat di `docs/rancangan_v2.md` bagian
  11.2 (commit `f9ecd0f`): "kalau lebih dari separuh klaim Liputan6 yang sah tidak ada di basis data
  TurnBackHoax, tahap berikutnya layak dikerjakan".** Berkas konfirmasi SUDAH disiapkan:
  `data/candidates/celah_liputan6/konfirmasi_50.csv` (50 butir, 326 baris kandidat; lokal, tidak
  di-commit; alat `python -m candidates.gap_review`, yang menolak menimpa berkas yang sudah ada).
  **KEPUTUSAN di berkas itu diisi pemilik proyek SENDIRI dengan pedoman v1.0, tanpa bantuan AI --
  jangan mengisi, mengusulkan, atau "memeriksa" keputusannya, dan jangan membuka
  `kunci_kandidat.json` untuknya.** Satu artikel dikeluarkan (Klarifikasi Polri). Label Liputan6:
  banner "Salah" 58, "Hoax" 39, "Klarifikasi" 2, tanpa 1 (dari 100) -- TIDAK dipetakan ke label
  TurnBackHoax tanpa pasangan terkonfirmasi. Sesudah berkas diisi: hitung proporsi "TIDAK ADA" dari
  butir sah dengan Wilson 95%, bandingkan butir ujung rentang, dan laporkan tabel silang label.
  **Dikonfirmasi pemilik proyek 2026-10-04 (bagian 11.2, commit `a1459a2`, sebelum berkas dibuka):**
  ambang "lebih dari separuh"; hasil JELAS bila interval Wilson 95% seluruhnya di atas atau di bawah
  50%, AMBIGU bila melintasi 50%; bila ambigu, perluas ke 100 butir.
  **Yang diisi pemilik proyek adalah `konfirmasi_50.xlsx`** (dibuat `python -m candidates.gap_workbook
  --make` dari CSV yang sama, tanpa mengambil ulang sampel; `openpyxl==3.1.5` di
  `requirements-dev.txt`; uji `tests/test_gap_workbook.py`). Berkas ini ber-creator kode (lihat
  Aturan Wajib #5): templat keluar dengan KEPUTUSAN kosong, buktinya `sidik_jari_templat_xlsx.json`.
  **Setelah pemilik proyek menyatakan selesai: `python -m candidates.gap_workbook --read`** -- ia
  menolak menghitung bila sel selain KEPUTUSAN/catatan berubah dari templat atau ada butir yang
  kosong/tidak terbaca (dilaporkan untuk ditanyakan, TIDAK ditebak), dan baru saat itu membuka
  `kunci_kandidat.json` untuk tabel silang label. **Belum dijalankan; keputusan belum diisi.** **Rancangan itu
  MENGOREKSI butir di bawah ini:** (i) empat kegagalan Recall@3 (v1-022, v1-024, v1-027, v1-033)
  semuanya butir NEGATIF sulit, jadi bukan dasar untuk "menulis ulang kueri saat retrieval gagal"
  (tugas rewriter kedua dicoret; positif 20/20 di semua indeks); (ii) bukti pesan panjang kuat untuk
  mekanismenya (2/20 arsip, 0/20 indeks 922 dan 1.532) tetapi pengganggunya sintetis; (iii) untuk
  grader dan "Mungkin terkait" ada bukti masalah tetapi TIDAK ada bukti solusi; (iv) kredibilitas
  DOKUMEN (tidak ada temuan) dipisah dari kredibilitas RUJUKAN (banyak temuan). Teks lama di bawah
  dipertahankan sebagai riwayat.
- **Versi 2 — Corrective RAG (rencana awal, lihat koreksi di atas).** Menambahkan
  node penilai relevansi dokumen (grader), penulis ulang kueri (query
  rewriter), dan penilaian kredibilitas sumber -- lihat
  `testset/v1_temuan_untuk_v2.md` untuk pemetaan temuan Versi 1 ke masing-
  masing komponen. **Rewriter punya dua tugas berbasis bukti:** (1) mengekstrak
  inti klaim dari pesan panjang sebelum retrieval -- dampak paling terukur, 18
  dari 20 butir positif gagal Recall@3 pada pesan ~5.000 karakter; (2) menulis
  ulang kueri saat retrieval gagal (4 butir). Grader menargetkan 7 butir
  kegagalan/ketidakbulatan penilaian; kredibilitas sumber tidak punya temuan
  kuantitatif langsung dari set uji v1. **Agenda eksperimen (dicatat, belum
  diputuskan):** menghapus seksi Penjelasan dari indeks (0 butir Recall@3
  berpindah saat dihilangkan; memangkas sepertiga chunk) -- wajib diuji dulu
  pengaruhnya pada kualitas jawaban generator. **Kandidat fitur
  (dicatat, belum diputuskan):** verdict ketiga "artikel terkait" untuk klaim
  yang lebih umum daripada artikel (mis. "Malaysia marah soal asap" vs artikel
  "Malaysia Laporkan Indonesia ke PBB"). Di Versi 1 klaim seperti itu
  menghasilkan "belum ditemukan" (Aturan Wajib #4); sengaja tidak ditambahkan
  sebelum set uji v1 dibekukan.

---

## Struktur Data Sumber

Setiap artikel TurnBackHoax memiliki seksi baku berikut:

| Seksi | Isi |
| --- | --- |
| **Narasi** | Klaim/narasi hoaks yang beredar, beserta tautan ke unggahan aslinya |
| **Penjelasan** | Proses penelusuran yang dilakukan tim pemeriksa fakta |
| **Kesimpulan** | Fakta yang sebenarnya, umumnya diawali kata "Faktanya..." |
| **Hasil Periksa Fakta** | Label kebenaran (Salah, Penipuan, dsb.) |
| **Referensi** | Daftar tautan rujukan sahih yang dipakai untuk verifikasi |

Label kebenaran juga tertanam di judul dalam kurung siku, misalnya
`[SALAH] Malaysia Laporkan Indonesia ke PBB soal Karhutla`.

Pola URL artikel: `https://turnbackhoax.id/articles/{id}-{slug}`

---

## Aturan Wajib

Aturan berikut bersifat mengikat. Jangan melanggarnya tanpa persetujuan
eksplisit dari pemilik proyek.

### 1. Pemisahan tautan sumber hoaks dan rujukan sahih

Tautan pada seksi **Narasi** adalah sumber hoaks itu sendiri (unggahan
media sosial asli). Tautan ini **tidak boleh** ditampilkan kepada
pengguna sebagai rujukan yang sahih. Hanya tautan dari seksi
**Referensi** yang boleh disajikan sebagai rujukan.

Keduanya tetap disimpan, tetapi pada medan terpisah: `references` untuk
rujukan sahih, `claim_sources` untuk sumber hoaks.

### 2. Chunking berbasis seksi, bukan jumlah karakter

Pemotongan dokumen dilakukan per seksi (Narasi, Penjelasan, Kesimpulan),
**bukan** dengan pemotongan buta berdasarkan jumlah karakter.

Alasannya: chunk per seksi memisahkan peran tiap seksi. Narasi memuat
klaim yang beredar, Penjelasan memuat proses penelusuran, dan
**Kesimpulan** memuat fakta yang ditampilkan sebagai jawaban dari artikel
yang sama. Pemotongan berbasis karakter merusak pemisahan ini karena satu
chunk dapat berisi campuran akhir Narasi dan awal Penjelasan.

> **Riwayat rasional.** Rumusan awal aturan ini menyatakan bahwa klaim
> pengguna paling cocok dengan chunk Narasi. Pengujian awal (10 kueri set
> pengembangan) sempat menyatakannya **tidak terbukti** karena chunk
> Penjelasan unggul 7/10. **Koreksi 2026-09-25:** pengukuran itu menghitung
> chunk teratas dari **artikel mana pun**. Ablasi retrieval pada set uji v1
> mengukur chunk terbaik dari **artikel yang benar**: Narasi unggul **35/40**,
> dan retrieval dengan Narasi saja menyamai seluruh seksi (Recall@3 36/40,
> 0 butir berpindah). Jadi **rasional chunking per seksi, termasuk peran
> Narasi sebagai pencocok klaim, kembali didukung data.** Dugaan bahwa
> Penjelasan lebih sering memunculkan artikel tetangga (penjelasan atas 7/10
> itu) **belum diuji**. Aturannya sendiri tidak berubah. Rincian:
> `testset/v1_temuan_untuk_v2.md` bagian 5.2.

### 3. Jangan biarkan LLM mengarang tautan

Tautan rujukan diambil dari metadata dokumen hasil retrieval, tidak
pernah dihasilkan oleh LLM. LLM yang diminta menuliskan URL dari
ingatannya cenderung berhalusinasi.

### 4. Jawaban wajib berbasis dokumen

Prompt sistem harus menegaskan bahwa LLM hanya boleh menjawab
berdasarkan potongan dokumen yang diberikan. Bila tidak ada dokumen yang
cukup relevan, jawaban yang benar adalah menyatakan klaim tersebut belum
ditemukan dalam basis data — bukan memaksakan kesimpulan.

### 5. Label emas set uji: tinjauan manusia wajib, label final selalu manusia

Setiap kandidat yang akan masuk set uji — termasuk kandidat buatan Gemma —
**wajib** melalui tinjauan pemilik proyek sendiri sebelum dipakai sebagai
butir set uji. **Label final selalu ditetapkan manusia** (pemilik proyek),
tidak pernah oleh AI. Bila draf AI (ChatGPT, Gemma, Claude, atau lainnya)
dipakai pada tahap mana pun — draf awal label, draf teks klaim, atau
pendapat yang dibaca sebelum memutuskan — **penggunaannya wajib dicatat**
secara eksplisit (model/alat, tahap, dan sejauh mana dipakai), sekalipun
draf itu sendiri kemudian tidak disimpan.

Alasan: kejadian 2026-09-22 — sebuah berkas draf label tahap 1 yang
dihasilkan `openpyxl` (bukan diketik manusia di Excel) sempat berisiko
dianggap sebagai label emas karena nama berkasnya mirip dengan berkas
label emas yang sebenarnya. Berkas draf itu sudah dihapus pemilik proyek
setelah label final ditetapkan (`data/candidates/` tidak di-commit, jadi
ini bukan operasi git); **catatan riwayat kejadian ini dipertahankan**
di `kebijakan_label_emas_2026-09-22` pada `testset/v1.meta.json` meski
berkasnya sudah tidak ada — termasuk cara mendeteksi kejadian serupa
(periksa `docProps/core.xml` suatu `.xlsx`: creator `openpyxl` atau nama
aplikasi lain berarti dihasilkan kode, bukan diketik manusia).

### 6. Pembandingan dengan baseline Versi 1 wajib memakai indeks arsip

Evaluasi yang **dimaksudkan untuk dibandingkan dengan baseline Versi 1** (akurasi 48/50,
Recall@3 36/40, ablasi retrieval, dan evaluasi Versi 2 terhadap Versi 1) **wajib dijalankan pada
indeks arsip `archive/v1`, bukan indeks utama `data/`**. Indeks utama akan diperluas; kalau
datanya berbeda, selisih hasil tidak lagi murni karena arsitektur. Sidik jari isi arsip dicatat
di `testset/v1.meta.json` (`arsip_indeks_v1_2026-09-25`) dan **wajib dicocokkan lebih dulu**:

```powershell
$env:PYTHONPATH = "src"
$env:RAG_INDEX_DIR = "archive/v1"          # arahkan SEMUA pembacaan indeks ke arsip
.\.venv\Scripts\python.exe -m evaluation.index_check --expect-v1-archive   # wajib kode keluar 0
.\.venv\Scripts\python.exe -m evaluation.testset_eval       # atau skrip evaluasi lain, tanpa ubah kode
.\.venv\Scripts\python.exe -m evaluation.retrieval_ablation --out-json X.json --out-report X.txt
Remove-Item Env:RAG_INDEX_DIR               # kembali ke indeks utama
```

**Tambahan 2026-10-03 (keputusan pemilik proyek; berlaku bila Versi 2 dilanjutkan):** aturan di atas
menjaga **angka asli Versi 1** (48/50, Recall@3 36/40, ablasi) dan uji kemunduran Versi 2 pada set
uji v1 -- semuanya tetap hanya lewat `archive/v1` (`ef_search` 100). **Perbandingan Versi 1 dan
Versi 2 pada KEMAMPUAN BARU (butir pesan panjang) wajib memakai snapshot beku yang baru**
(`archive/v2_snapshot/`, `ef_search` 2000), dengan kedua versi dijalankan pada snapshot, set uji,
dan parameter retrieval yang sama. Snapshot itu BELUM dibuat: urutannya antrean digabung dan
di-ingest (ingest dimulai pemilik proyek) -> snapshot dibekukan (daftar id + sidik jari isi) -> set
uji v2 dibangun dan diverifikasi terhadapnya. Hasil pada snapshot tidak boleh dibandingkan dengan
angka pada `archive/v1`, dan sebaliknya. Rincian: `docs/rancangan_v2.md` bagian 5.1.

`RAG_INDEX_DIR` hanya mengubah jalur BACA (`paths.INDEX_DIR`); scraping tetap menulis ke `data/`,
dan `ingest` menolak menulis ke `archive/` kecuali `--allow-archive`. Nilai yang tidak berisi
indeks lengkap langsung gagal (tidak membuat indeks kosong). Jangan jalankan `ingest` dengan
`--allow-archive` kecuali untuk membangun ulang arsip yang hilang (README, "Arsip indeks Versi 1").

### 7. Sumber label kebenaran: judul artikel otoritatif (ditetapkan 2026-09-27)

**Label diambil dari judul** (`[SALAH] ...`, `[PENIPUAN] ...`, `[PARODI] ...`), bukan dari seksi
**Hasil Periksa Fakta** di isi artikel. Seksi itu dibaca hanya sebagai pemeriksaan silang dan dicatat
bila janggal; ia tidak pernah menimpa label judul.

Dasar (672 artikel: basis + kelompok 1-2 + mode maju, diperiksa dari cache HTML 2026-09-27): seksi
Hasil Periksa Fakta berbunyi "Salah" pada **670/672**, termasuk **280/280 PENIPUAN dan 5/5 PARODI**
(dua sisanya, 36224 dan 35176, berlabel SALAH; angka 279 di catatan awal menghitung 35383 sebagai
TIDAK DIKETAHUI, sebelum aturan ini diterapkan).
Jadi seksi itu adalah nilai kebenaran kasar, bukan kategori, dan PENIPUAN/PARODI adalah jenis
"Salah". Kasus seperti 35383 (judul PENIPUAN, isi "Salah") karenanya **tidak bertentangan**. Dua
kejanggalan sejati: 36224 (basis; isi "Benar") dan 35176 (kelompok 1; isi "Dalam Proses"). Pada
keduanya Kesimpulan menyatakan klaimnya keliru, sehingga judul (SALAH) yang benar dan isian seksi
itulah yang keliru.

Kurung siku rusak di judul sumber (`[SALAH Judul`, `PENIPUAN] Judul`; 4 kasus: 34929, 35383,
33422, 33355) diterima **hanya bila kata labelnya salah satu label yang sudah dikenal**
(`KNOWN_LABELS` di `scraping/parser.py`, huruf besar, tepat satu kurung). **Perluasan 2026-10-02:**
penutup salah ketik `[SALAH} Judul` (29847) diterima dengan syarat yang sama, dan HANYA untuk `}`
(penutup lain seperti `)` atau `>`, serta pembuka salah seperti `{SALAH]`, tetap `TIDAK DIKETAHUI`);
pola ini baru dicoba setelah pola kurung lengkap gagal, sehingga judul yang sudah terbaca benar tidak
terpengaruh. Karakter tak terlihat (U+200B-U+200F, U+2060, U+FEFF, U+00AD) dibuang dari **judul**
sebelum dicocokkan (29812, 29787); isi seksi sengaja tidak dinormalkan agar teks chunk yang sudah
di-embed tidak berubah. Label di luar daftar itu
tetap `TIDAK DIKETAHUI` dan wajib dilaporkan untuk ditinjau manusia, **bukan** ditebak dari isi
artikel. Label baru yang muncul dengan kurung lengkap (`[X] ...`) tetap diterima apa adanya (perilaku
lama), lalu diputuskan terpisah cara menampilkannya (`presentation.py` memakai tampilan NETRAL
untuk label tak dikenal dan mencatatnya ke log, sejak 2026-10-02 -- sebelumnya gaya SALAH;
SATIRE/SATIR/KOMEDI ditampilkan sebagai PARODI lewat `STATUS_ALIASES`).

---

## Lingkungan Pengembangan

- **Sistem operasi:** Windows
- **Shell:** PowerShell
- **Python:** 3.11.4 (64-bit)
- **IDE:** Antigravity (turunan VS Code)

### Virtual environment (wajib)

Proyek ini memakai virtual environment di `.venv/` (di-gitignore). Semua
perintah Python **harus dijalankan dari venv ini**, bukan dari Python
global, agar dependensi terisolasi. Python global mesin dev juga dipakai
proyek lain (mis. TensorFlow), dan memasang paket proyek ini ke sana
pernah menimbulkan konflik `protobuf`.

```powershell
python -m venv .venv                          # sekali saja
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt   # requirements.txt + pytest
.\.venv\Scripts\python.exe -m pytest                # uji offline di tests/ (tanpa jaringan/API)
.\.venv\Scripts\Activate.ps1                        # atau aktifkan dulu
```

Paket di `src/` (mis. `scraping`) dijalankan dari **root proyek** dengan
`PYTHONPATH=src`, sehingga jalur relatif tetap berbasis root:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m scraping     # menggantikan `python src\scraper.py`
.\.venv\Scripts\python.exe -m evaluation.generation_eval --check-budget   # skrip evaluasi LIVE
```

Skrip evaluasi (`evaluation.generation_eval`, `retrieval_eval`, `gemma_json_check`,
`probe_quota`) sengaja **tidak** berawalan `test_`: pytest hanya mengumpulkan
`tests/` (lihat `pytest.ini`) dan tidak pernah memanggil LLM. Uji `tests/`
memakai objek palsu dan aman dijalankan kapan saja.

`requirements.txt` mengunci versi (`torch==2.14.0`, build CPU dari PyPI).
torch harus >= 2.6 agar `transformers` 5.x mau memuat
`pytorch_model.bin` bge-m3 (CVE-2025-32434).

### Catatan PowerShell

Di PowerShell, `curl` adalah alias untuk `Invoke-WebRequest`, bukan curl
asli. Flag gaya Unix seperti `-I` tidak bekerja dan dapat membuat
perintah menggantung. Gunakan `curl.exe` bila benar-benar memerlukan
curl, atau `Invoke-WebRequest -Method Head` sebagai gantinya.

### Catatan jaringan

Server `turnbackhoax.id` berlatensi tinggi dan kerap lambat mengirimkan
respons pertama. **Setiap permintaan jaringan wajib memiliki timeout
eksplisit.** Perintah tanpa batas waktu pernah menggantung lebih dari 40
menit pada proyek ini.

Ketentuan yang berlaku:

- Timeout: 45 detik
- Retry: maksimal 3 kali dengan *exponential backoff*, hanya untuk read
  timeout dan connection error — jangan retry untuk galat 404
- Jeda antar-permintaan: minimal 1,5 detik agar tidak membebani server
- HTML mentah di-cache ke `data/raw_html/` agar pengembangan logika
  parsing tidak perlu memanggil server berulang kali

---

## Struktur Direktori

```
RAG_FactChecking/
├── src/
│   ├── paths.py          # Jalur proyek terpusat; RAG_INDEX_DIR memilih indeks BACA (bawaan data/)
│   ├── scraping/         # Pengambilan & parsing artikel TurnBackHoax
│   │   ├── links.py      #   normalisasi URL + daftar domain diblokir (Aturan #1)
│   │   ├── client.py     #   sesi HTTP, timeout/retry, cache HTML
│   │   ├── discovery.py  #   pengumpulan URL dari halaman daftar
│   │   ├── parser.py     #   parsing HTML artikel -> dict terstruktur
│   │   ├── pipeline.py   #   orkestrasi + CLI (python -m scraping)
│   │   ├── reparse.py    #   parse ulang dari cache TANPA jaringan (python -m scraping.reparse)
│   │   ├── restore.py    #   pulihkan articles.json arsip dari daftar artikel (cache/jaringan)
│   │   ├── expand.py     #   perluasan basis data per kelompok -> data/expansion/ (python -m scraping.expand)
│   │   ├── source.py     #   sumber artikel yang bisa diganti (bawaan HTML; ARTICLE_SOURCE)
│   │   └── scheduled.py  #   pembungkus pembaruan berkala: scraping saja, penanda + notifikasi
│   ├── chunker.py        # Chunking per seksi + metadata (Aturan Wajib #2)
│   ├── ingest.py         # Embedding bge-m3 -> ChromaDB (idempoten)
│   ├── retriever.py      # Retrieval, diagregasi per article_id
│   ├── llm/              # Abstraksi penyedia LLM (Gemini), retry, throttling, kuota
│   │   ├── errors.py, base.py, secrets.py   # galat; LLMProvider + CallRecord; .env + samarkan kunci
│   │   ├── gemini.py, gemini_errors.py      # GeminiProvider; penafsiran galat HTTP Gemini
│   │   └── limits.py, throttle.py, ledger.py # angka kuota; jendela geser RPM/TPM; buku besar + anggaran
│   ├── generator.py      # Klaim -> retrieval -> LLM -> jawaban terstruktur
│   ├── presentation.py   # Data tampilan demo (tanpa Streamlit): status, salinan teks, galat
│   ├── app.py            # Demo Streamlit (streamlit run src\app.py); adapter tipis
│   └── evaluation/       # Evaluasi & diagnostik LIVE (bukan uji otomatis)
│       ├── generation_eval.py  #   evaluasi generasi (--check-budget, --compare)
│       ├── retrieval_eval.py   #   verifikasi retrieval pada kueri sehari-hari
│       ├── gemma_json_check.py #   uji format JSON Gemma 4
│       ├── probe_quota.py      #   probe tunggal ke server (1 permintaan)
│       ├── retriever_exactness.py  # retriever (HNSW) vs pencarian eksak; wajib tiap indeks bertambah
│       └── results_store.py, comparison.py  # simpan/lanjutkan hasil; perbandingan model
├── tests/                # Uji offline (pytest), satu berkas per modul
│   ├── fixtures/         #   HTML nyata yang DISAMARKAN (di-commit); dibuat lewat anonymize_fixtures.py
│   └── _fakes.py         #   objek palsu bersama (bukan uji)
├── archive/v1/           # Arsip indeks Versi 1 (chroma/ + articles.json di-gitignore; Aturan Wajib #6)
│   └── article_ids.json  #   daftar 150 artikel (metadata saja) -- SATU-SATUNYA berkas arsip yang di-commit
├── data/
│   ├── raw_html/         # Cache HTML mentah (tidak di-commit)
│   ├── articles.json     # Hasil scraping terstruktur (tidak di-commit)
│   └── chroma/           # Basis vektor ChromaDB (tidak di-commit)
├── .streamlit/config.toml  # Tema demo (satu-satunya tempat kode warna); secrets.toml di-gitignore
├── requirements.txt, requirements-dev.txt   # dependensi (+ streamlit); + pytest, ruff
├── pytest.ini            # testpaths = tests, pythonpath = src
├── ruff.toml             # hanya pengecualian disengaja (I001 di src/app.py)
└── CLAUDE.md
```

---

## Konvensi Kode

- Bahasa komentar dan docstring: **Indonesia**
- Nama variabel dan fungsi: **Inggris**
- Sertakan *type hint* pada tanda tangan fungsi
- Tangani galat secara eksplisit; jangan menelan *exception* diam-diam
- Setiap perubahan pada logika parsing wajib diikuti menjalankan `pytest`
  (khususnya `tests/test_parser.py`, `test_links.py`, `test_client.py`)
- **Setiap perubahan logika parsing atau chunking mewajibkan pembangunan ulang
  indeks vektor**, berurutan: `python -m scraping.reparse` (offline, dari cache)
  -> `python src/ingest.py --rebuild` (hapus koleksi lama, embed semua chunk
  dari nol) -> `python -m evaluation.index_check` (kode keluar 0 = indeks segar).
  Indeks basi tidak menimbulkan galat: retriever tetap mengembalikan hasil,
  hanya dari teks dan embedding lama. Ingestion **inkremental** (tanpa
  `--rebuild`) hanya aman bila isi teks chunk tidak berubah: ia membandingkan
  teks tersimpan dengan teks baru dan meng-embed ulang yang berbeda
  (`select_chunks_to_embed`), tetapi TIDAK mendeteksi perubahan tokenizer,
  batas token (`MAX_SEQ_LENGTH`), model, atau metadata pada chunk yang teksnya
  sama, dan hanya melaporkan (tidak menghapus) chunk usang. Contoh terukur:
  setelah perbaikan duplikasi, ingest inkremental akan meng-embed 300 chunk
  yang berubah (Narasi dan Penjelasan) dan melewati 150 Kesimpulan yang
  teksnya identik.

---

## Cara Kerja yang Diharapkan

- **Tidak ada teks artikel, tautan sumber hoaks, atau kontak di berkas ter-commit.** Fixture HTML
  baru WAJIB disamarkan dulu (`PYTHONPATH=src python tests/anonymize_fixtures.py <asli> <keluaran>`),
  dan literal uji diambil dari hasil tersamar. `articles.json` dan HTML mentah tetap lokal.

Proyek ini bertujuan pembelajaran, sehingga cara mengerjakannya penting,
bukan hanya hasil akhirnya.

- **Laporkan temuan sebelum mengubah kode.** Bila diminta menyelidiki
  sesuatu, sampaikan hasil penyelidikan lebih dulu dan tunggu
  persetujuan sebelum menulis ulang apa pun.
- **Tunjukkan bukti mentah.** Saat melaporkan hasil pemeriksaan
  jaringan atau struktur HTML, sertakan status code dan potongan
  keluaran aslinya. Jangan menyajikan dugaan seolah-olah hasil
  pemeriksaan langsung.
- **Ubah seperlunya.** Jangan merefaktor bagian yang tidak diminta.
  Logika parsing pada `extract_sections`, `extract_references`, dan
  `extract_claim_sources` sudah tervalidasi — jangan diubah tanpa alasan
  kuat. (Pengecualian yang disetujui 2026-09-21: `extract_sections`
  diperbaiki karena menduplikasi teks; lihat "Masalah terbuka" dan
  `tests/test_parser.py`, yang kini gagal bila rasio panjang hasil parse
  terhadap teks HTML asli melebihi 1,1.)
- **Jelaskan keputusan desain.** Bila ada beberapa pendekatan, sebutkan
  pilihan yang diambil beserta alasan dan konsekuensinya.
- **Sampaikan ketidakpastian secara jujur.** Bila sesuatu belum
  terverifikasi, katakan demikian alih-alih menyajikannya sebagai fakta.

---

## Temuan Ingestion dan Retrieval (Versi 1)

> **CATATAN (2026-09-21): seluruh angka bertanda `[DIUKUR ULANG 2026-09-21]` semula diukur
> pada teks Narasi/Penjelasan yang terduplikasi (150 dari 150 artikel). Duplikasi itu sudah
> diperbaiki (`extract_sections`), `articles.json` di-parse ulang dari cache, indeks vektor
> dibangun ulang dari nol dan diverifikasi segar (`evaluation.index_check`), lalu semuanya
> diukur ulang. Angka lama dan baru ada berdampingan di "Pengukuran ulang setelah perbaikan
> duplikasi" (di bawah), dengan penanda mana temuan yang bertahan dan mana yang berubah.**
> Angka lama yang masih tertulis di teks tiap bagian dipertahankan sebagai riwayat.

Hasil pengujian pertama terhadap 450 chunk (150 artikel), memakai 5 kueri
berbahasa sehari-hari (`src/evaluation/retrieval_eval.py`). **Sampelnya baru 5
kueri**: cukup untuk sanity check dan menemukan masalah, bukan evaluasi
statistik.

### Penjelasan menang atas Narasi [DIUKUR ULANG 2026-09-21] — BERTAHAN (arah), angka berubah; ukuran "artikel mana pun", lihat koreksi 2026-09-25 di bawah

Diukur ulang pada 10 kueri (bukan 5): chunk Penjelasan tetap paling sering menang.
Peringkat satu: Penjelasan 7, Narasi 2, Kesimpulan 1 (data lama pada 10 kueri yang sama:
6/2/2). Seluruh top-5 chunk (50 hasil): Penjelasan 22, Kesimpulan 14, Narasi 14 (lama:
20/12/18). Angka di paragraf berikut (5 kueri) adalah riwayat pengukuran pertama; jangan
dibandingkan langsung dengan angka 10 kueri.

Asumsi awal bahwa klaim pengguna paling cocok dengan chunk Narasi
**tidak terbukti**. Pada peringkat satu, chunk Penjelasan menang pada 3
dari 5 kueri, Narasi 1, Kesimpulan 1. Pada seluruh top-5 chunk (25 hasil):
Penjelasan 11, Kesimpulan 7, Narasi 7. Chunk Penjelasan yang terpotong
pada 512 token pun tetap cocok kuat. Chunking per seksi dipertahankan
karena jawaban diambil dari Kesimpulan artikel yang sama, tetapi
rasionalnya adalah pemisahan peran seksi, bukan pencocokan lewat Narasi
(lihat koreksi pada Aturan Wajib #2).

**Dinilai ulang 2026-09-25 dengan 44 butir set uji (ablasi retrieval):** ukuran di atas menghitung
seksi chunk teratas secara KESELURUHAN (artikel apa pun). Bila yang dihitung adalah chunk terbaik
pada artikel yang BENAR, Narasi menang 35 dari 40 butir non-batas, dan retrieval dengan Narasi saja
menyamai seluruh seksi (Recall@3 36/40, 0 butir berpindah). Jadi untuk menemukan artikel yang
benar, asumsi awal tentang Narasi ternyata didukung; kemenangan Penjelasan pada ukuran lama
kemungkinan terjadi di artikel tetangga (belum diuji langsung). Rincian:
`testset/v1_temuan_untuk_v2.md` bagian 5.2.

### Retrieval diagregasi per `article_id`

Skor sebuah artikel adalah skor tertinggi di antara chunk-chunknya, apa
pun seksinya (`src/retriever.py`, `aggregate_by_article`). Tanpa agregasi,
satu artikel bisa mengisi beberapa peringkat teratas. Jawaban tetap
diambil dari chunk Kesimpulan artikel pemenang, dan tautan dari metadata
(Aturan Wajib #3).

### Skor kemiripan berdaya pisah rendah [DIUKUR ULANG 2026-09-21] — BERTAHAN, angka berubah sedikit

Semua skor di paragraf berikut berasal dari embedding teks terduplikasi (riwayat). Diukur
ulang pada data diperbaiki: skor kasus "vaksin flu bikin mandul" **0,6508 -> 0,6671**
(artikel teratas tetap 36214); positif terendah 0,5669 -> 0,5739; negatif tertinggi
0,6508 -> 0,6671; celah (positif terendah dikurangi negatif tertinggi) -0,0839 ->
-0,0932. Tiga dari lima skor positif tetap di bawah skor kasus vaksin flu. **Kesimpulan bahwa
skor kemiripan tidak dapat memisahkan klaim yang ada dari yang tidak ada bertahan** (semua
skor naik tipis; urutannya hampir tidak berubah: artikel teratas sama pada 9 dari 10 kueri).

Pada level artikel: kueri 2 memberi artikel benar 0,6227 dan artikel lain
0,6213 (selisih ≈ 0,001); kueri 5 memberi artikel lain 0,6877 melawan
artikel benar 0,6922. Skor artikel benar berkisar 0,567 sampai 0,692,
sedangkan tetangga yang salah bisa mencapai 0,688.

Uji kueri negatif (5 klaim yang tidak ada di basis data; ketiadaan
kata kunci diperiksa otomatis di `evaluation/retrieval_eval.py`) menambah bukti.
Skor artikel teratas tiap kueri negatif: 0,5204 (kebijakan subsidi, gas
melon), **0,6508** (vaksin flu bikin mandul; tetangga dekat artikel vaksin
HPV bikin impoten), 0,4825 (gempa megathrust), 0,4813 (daun sirsak), 0,5037
(bumi datar). Skor positif: 0,5669 sampai 0,6922. Klaim "vaksin flu bikin
mandul" sengaja dipertahankan sebagai kueri negatif: itu kasus tersulit
sekaligus paling realistis, karena hoaks nyata sering bervariasi di sekitar
tema yang sama, dan menguji hanya dengan klaim yang jauh dari topik akan
memberi gambaran yang terlalu optimistis. Hasilnya:

- Negatif yang jauh dari topik basis data (0,48 sampai 0,52) masih
  terpisah dari positif terendah (0,5669), tetapi celahnya hanya ≈ 0,05
  dan dihitung dari sampel 5 lawan 5.
- Klaim yang **serupa bentuknya** dengan klaim yang ada (vaksin flu vs
  vaksin HPV) mencetak 0,6508, di atas 3 dari 5 skor positif. Ambang skor
  tidak bisa memisahkannya, karena embedding menilai kemiripan topik, bukan
  apakah klaimnya sama.

**Kesimpulan:** hasil kueri negatif membuktikan, pada sampel ini, bahwa
skor kemiripan tidak dapat memisahkan klaim yang ada dari yang tidak ada.
Klaim negatif "vaksin flu bikin mandul" mencetak 0,6508, di atas 3 dari 5
skor positif, sehingga ambang skor apa pun akan menerima klaim itu atau
menolak tiga klaim yang memang ada di basis data. Karena itu **Aturan Wajib
#4 (menyatakan klaim belum ditemukan) tidak akan diwujudkan dengan ambang
skor di Versi 1.** Ini justifikasi empiris bahwa node penilai relevansi
(grader) di Versi 2, yang menilai apakah klaim pengguna sama dengan klaim
pada artikel hasil retrieval, adalah jawabannya.

**Ukuran sampel: baru 5 positif dan 5 negatif.** Angka-angka di atas
(termasuk celah ≈ 0,05 untuk negatif yang jauh dari topik) adalah indikasi
yang kuat untuk arah keputusan, bukan evaluasi statistik.

### Berkas indeks ChromaDB ditulis ulang setiap kali dibuka (ditemukan 2026-09-25)

Ditemukan saat menguji demo: `data/chroma/chroma.sqlite3` serta `data_level0.bin` dan
`length.bin` di folder segmen HNSW **berubah secara byte setiap kali koleksi dibuka dan dikueri**
(chromadb 1.5.9). **Ini bukan akibat demo:** jalur yang dipakai evaluasi
(`ingest.get_collection`, dipakai `testset_eval`/`generation_eval`) mengubah byte yang sama,
bahkan pada dua pembukaan berturut-turut, dan demo sendiri tidak membuat koleksi (memakai
`get_collection`, bukan `get_or_create`). Jadi evaluasi Versi 1 pun berjalan dengan perilaku ini.

**Konsekuensi: reproduksibilitas evaluasi Versi 1 dijamin oleh kesamaan ISI indeks, bukan
kesamaan byte berkas.** Isi diverifikasi 2026-09-25 setelah perubahan byte:
`evaluation.index_check` lolos (450 chunk, id/teks/metadata identik dengan `articles.json`,
kosinus sampel embedding ulang 1,000000), dan **200 kueri acak** (vektor tersimpan + derau
kecil) memberi top-30 HNSW **identik** dengan pencarian eksak brute-force atas seluruh vektor
tersimpan (0 selisih). Hash byte berkas indeks karenanya **tidak** boleh dipakai sebagai bukti
bahwa indeks tidak berubah; pakai `index_check` dan perbandingan hasil kueri. Penyebab pastinya
(kemungkinan HNSW di-persist ulang saat dimuat) tidak diselidiki lebih jauh. Keadaan byte
sebelum pembukaan pertama pada 2026-09-25 tidak tercadang. Tercatat juga di
`testset/v1.meta.json` (`temuan_chromadb_penulisan_ulang_indeks_2026-09-25`).

### Pemuatan model: riwayat safetensors PR #130

`transformers` 5.x menolak memuat `pytorch_model.bin` bila torch < 2.6
(CVE-2025-32434). Saat torch global masih 2.5.1, embedding 450 chunk
dibuat dari varian safetensors milik PR konversi #130 di repo
`BAAI/bge-m3` (pembuat: `SFconvertbot`, akun konversi otomatis Hugging
Face; commit `9a0624b8…`). PR itu belum di-review atau di-merge BAAI,
sehingga sempat menjadi ketergantungan yang belum terverifikasi.

**Sudah dibuktikan:** bobot safetensors tersebut identik bit-per-bit dengan
`pytorch_model.bin` resmi di branch `main` (391 dari 391 tensor, tanpa
selisih nama, dibandingkan dengan `torch.load(mmap=True, weights_only=True)`
di dalam venv). Karena itu embedding yang tersimpan tetap valid tanpa
diulang, dan skor retrieval sebelum dan sesudah peralihan identik.

**Keadaan sekarang:** venv memakai torch >= 2.6, sehingga `src/ingest.py`
memuat `.bin` resmi dari branch `main` dan tidak lagi bergantung pada PR.

**Jebakan:** setiap kali `transformers` memuat `.bin` dari repo tanpa
safetensors, ia menjalankan `Thread` non-daemon yang mengunduh varian
safetensors dari PR konversi (2,3 GB) di latar belakang, sehingga proses
Python tidak berhenti sampai unduhan selesai. Skripnya tampak selesai
(hasil tercetak) tetapi proses menggantung. `use_safetensors=False` tidak
mencegahnya; yang efektif adalah variabel lingkungan
`DISABLE_SAFETENSORS_CONVERSION=1`, yang di-set di bagian atas
`src/ingest.py`. Jangan dihapus.

---

## Lapisan Generasi Jawaban (Versi 1)

Kode: `src/llm/` (abstraksi penyedia), `src/generator.py`
(alur klaim -> retrieval 3 artikel -> LLM -> jawaban), `src/evaluation/generation_eval.py`
(evaluasi live 5 positif + 5 negatif). Kunci API dibaca dari `.env`
(`GEMINI_API_KEY`; contoh di `.env.example`) dan tidak pernah dicetak:
semua log dan pesan galat melewati `redact()`.

### Keputusan jalur: API gratis (Gemini), bukan Claude API atau model lokal

- **Claude API dibatalkan** karena berbayar (estimasi ±$0,25 sampai $0,65
  per 10 kueri pada Opus 5; harga dari tabel cache skill bertanggal
  2026-06-24, tidak diverifikasi ulang).
- **Model lokal dibatalkan**: RAM tersedia ±3,9 GB dan CPU-only membuat
  model 3B memakan ±2,5-3,5 menit per kueri (perkiraan dari benchmark CPU,
  tidak diukur langsung).
- **Gemini tier gratis** dipilih sebagai implementasi pertama.

### Desain provider-agnostic

Pipeline hanya bergantung pada `LLMProvider.generate(system_prompt,
user_prompt, json_schema=None) -> str`; penyedia dipilih lewat `LLM_PROVIDER`
di `.env`. Alasan: tier gratis dapat memperketat batas tanpa pemberitahuan
atau berhenti total tanpa kompensasi, dan tahap evaluasi perlu membandingkan
beberapa model tanpa menulis ulang pipeline. Setiap panggilan dicatat
(model, token bila tersedia, latensi, keberhasilan, jumlah 429).

Penanganan 429 (diperbaiki setelah percobaan live pertama): 429 dibedakan
menurut `quotaId` pada rincian galat (`classify_429`). **Kuota harian** ->
`LLMQuotaExhaustedError`, tanpa retry, dan evaluasi berhenti dengan pesan
jelas. **Per menit / tidak diketahui** -> maksimal 3 retry, menunggu sesuai
saran server (`Retry-After` / `retryDelay`); saran > 120 dtk dianggap kuota
habis. Format `quotaId` dikenal dari galat Gemini API umumnya dan diuji dengan
transport palsu; **belum diamati pada 429 asli akun ini**.

**Jebakan SDK:** klien Interactions di `google-genai` 2.24 mengulang 429/5xx
sendiri (3 retry, menunggu `Retry-After` tanpa batas atas) tanpa log. Di
percobaan live pertama itu menjelaskan mengapa satu "percobaan" memakan 2-3
menit padahal log menulis "menunggu 2,3 dtk" (terukur dengan transport palsu:
4 permintaan per panggilan; bahwa itulah yang terjadi pada server nyata adalah
kesimpulan, bukan pengamatan langsung). `disable_sdk_retry()` mematikannya
lewat konfigurasi internal SDK (opsi publik `retry_options.attempts` tidak bisa
di bawah 1 retry); `test_provider_with_real_sdk_errors` akan gagal bila SDK
berubah dan retry internal kembali aktif. Uji lama memakai galat palsu
berbentuk lain (body `str`, header di `err.headers`), sehingga tidak
menangkap bahwa saran server tidak pernah terbaca.

`evaluation/generation_eval.py` menulis hasil ke `data/generation_eval_<model>.jsonl` per
kueri, dapat dilanjutkan (kueri yang sudah punya hasil dilewati; `--force` untuk
mengulang), dan berhenti bila kuota harian habis. Opsi: `--model ID`,
`--check-budget` (hanya laporan anggaran, tanpa panggilan LLM), dan
`--compare DASAR KANDIDAT` (tabel keputusan berdampingan antarmodel, tanpa
panggilan LLM; hanya informasi kesetaraan keputusan dan BUKAN kriteria H3,
lihat "Hipotesis dan status").

**Throttling proaktif dan anggaran harian** (`src/llm/limits.py`, `throttle.py`, `ledger.py`): batas
RPM/TPM/RPD per model dibaca dari `DEFAULT_LIMITS` (dapat ditimpa `LLM_RPM`,
`LLM_TPM`, `LLM_RPD`). Jendela geser 60 dtk menjaga RPM dan TPM tidak pernah
tersentuh (setiap percobaan, termasuk retry, melewatinya); retry 429 tinggal
jaring pengaman. RPD dicatat di `data/quota_ledger.json` per hari **Pasifik**
(reset tengah malam Pasifik menurut dokumentasi) dan **setiap permintaan yang
dikirim dihitung, termasuk yang ditolak 429**, karena dokumentasi tidak
menyatakan apakah 429 ikut terhitung. Sebelum evaluasi dimulai, kebutuhan
(minimal 1 panggilan/kueri; terburuk 1 + `MAX_FORMAT_RETRIES`) dibandingkan
dengan sisa; bila tidak cukup, evaluasi tidak dimulai (kode keluar 4) dan saat
anggaran habis di tengah jalan permintaan tidak dikirim. **Buku besar hanya
tahu permintaan dari kode ini.** Koreksi logika pengisian awal: buku besar
sempat diisi (`seed(21)`) dari kolom "penggunaan puncak 28 hari" di dashboard AI
Studio, padahal angka itu puncak historis, bukan pemakaian hari berjalan, jadi
tidak sah sebagai nilai awal; entri keliru itu sudah dihapus. Nilai awal hanya
boleh berasal dari hitungan yang dapat ditelusuri (mis. log panggilan kita
sendiri); bila pemakaian hari itu tidak diketahui, buktinya adalah probe tunggal
(`src/evaluation/probe_quota.py`, 1 permintaan), bukan dashboard.

### Model dan kuota (diverifikasi dari dokumentasi resmi pada 2026-09-20)

- **Model bawaan (keputusan 2026-09-21): `gemini-3.5-flash-lite`**, generator
  Versi 1. `gemini-3.8-flash` (sebelumnya bawaan) **dihentikan** karena
  ketidakstabilan layanan (lihat "Hipotesis dan status"). Sumber daftar model:
  https://ai.google.dev/gemini-api/docs/models (halaman diperbarui
  2026-09-17 UTC); Flash stabil lain di halaman itu: 3.8, 3.7, 3.6, 3.5,
  3.1-flash-lite, 2.5-flash, 2.5-flash-lite. Ganti lewat `LLM_MODEL`.
  `gemini-2.0-flash` dan `-lite` tercatat sudah dimatikan.
- **Tier gratis:** halaman harga (https://ai.google.dev/gemini-api/docs/pricing)
  mencantumkan `gemini-3.8-flash` "Free of charge" pada Free tier.
- **Batas kuota: angka konkret TIDAK dipublikasikan di dokumentasi**, hanya
  di AI Studio (https://aistudio.google.com/rate-limit; dokumentasi:
  https://ai.google.dev/gemini-api/docs/rate-limits, yang juga menyatakan
  batas "not guaranteed"). **Angka akun ini, diambil dari AI Studio pada
  2026-09-21 (kolom penggunaan puncak 28 hari / batas; tier gratis dapat
  berubah tanpa pemberitahuan, ambil ulang berkala):**

  | Model | RPM | TPM (input) | RPD |
  | --- | --- | --- | --- |
  | `gemini-3.8-flash` | 5 (puncak 7) | 250K (puncak 15,19K) | 20 (puncak 21) |
  | `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite` | 15 | 250K | 500 |
  | `gemma-4-26b-a4b-it`, `gemma-4-31b-it` | 30 | 16K | 14,4K |

  **Kolom "puncak" adalah puncak 28 hari terakhir, BUKAN penggunaan hari
  ini**: angka 21/20 RPD dan 7/5 RPM menunjukkan bahwa batas pernah
  terlampaui, tetapi tidak menunjukkan kapan, oleh apa, atau apakah kuota hari
  ini sudah habis/direset. Untuk itu satu-satunya bukti adalah probe tunggal
  (`src/evaluation/probe_quota.py`). (Buku besar lokal sempat di-seed 21 dari angka ini;
  itu keliru, karena puncak bukan pemakaian hari itu.) Nama di AI Studio
  ("gemma-4-26b", "gemma-4-31b") dipetakan ke ID API di atas; pemetaan itu
  asumsi.
- **Reset kuota harian:** dokumentasi rate-limits: "Requests per day (RPD)
  quotas reset at midnight Pacific time"; batas berlaku **per proyek**, bukan
  per kunci. Tidak dinyatakan: apakah 429 ikut terhitung, dan apakah TPM Gemma
  dihitung sama. Waktu Pasifik ber-DST (AS): **September-awal November = PDT
  (UTC-7): reset 07:00 UTC = 14:00 WIB (UTC+7)**; sejak 1 Nov 2026 = PST
  (UTC-8): 08:00 UTC = 15:00 WIB; DST AS mulai lagi 14 Mar 2027. Indonesia
  tidak ber-DST, jadi jam reset dalam WIB bergeser satu jam dua kali setahun.
  Selalu hitung dari UTC: zona jam mesin dev ini berubah pada sesi yang sama
  (tercatat +08:00 Singapore Standard Time, lalu +07:00 SE Asia Standard
  Time), sehingga jam lokal tidak boleh dipakai untuk memutuskan "sudah
  reset"; jam sistem UTC cocok dengan header `Date` server Google. Kode
  menghitungnya dari `America/Los_Angeles` (uji: 06:59 UTC
  masih hari lama, 07:01 UTC hari baru; sebaliknya 07:59/08:01 UTC pada PST).
- **ID model diverifikasi dari dokumentasi resmi pada 2026-09-21:**
  `gemini-3.5-flash-lite` dan `gemini-3.1-flash-lite` (halaman models, diperbarui
  2026-09-17 UTC); Gemma 4 lewat Gemini API: `gemma-4-31b-it` dan
  `gemma-4-26b-a4b-it` (https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api;
  tidak tercantum di halaman models). Semuanya "Free of charge" pada halaman
  harga, dengan konten Free tier dipakai untuk meningkatkan produk Google.
- **`thinking_level` yang didukung** (https://ai.google.dev/gemini-api/docs/thinking,
  2026-09-21): `gemini-3.8-flash` low/medium/high (bawaan medium; **tidak ada
  minimal**); Flash Lite minimal/low/medium/high (bawaan **minimal**); Gemma 4
  hanya `high` (aktif) atau `minimal` (nonaktif). Kode menolak nilai tak
  didukung sebelum mengirim (`supported_thinking_levels`). Proyek ini memakai
  `medium` eksplisit untuk semua model Gemini agar perbandingan model tidak
  bercampur dengan perbedaan thinking; bawaan Flash Lite sendiri `minimal`.
- **SDK:** `google-genai` 2.24.0, memakai Interactions API
  (`client.interactions.create`) sesuai quickstart resmi; bentuk permintaan
  dan tipe respons (`output_text`, `status`, `usage.total_*_tokens`, galat
  `GenAiError`) diverifikasi terhadap paket terpasang. Klien Interactions di
  SDK itu berlabel versi preview (`2.4.1-preview.5`, v1beta). Terhadap
  server nyata: 5 panggilan pertama (kueri positif 1-5) berhasil pada
  percobaan pertama dengan skema terstruktur dan token tercatat, jadi
  integrasi dasarnya bekerja; kueri 6-8 kena 429 (lihat penanganan 429).

### Privasi data

Halaman harga menyatakan konten pada **Free tier digunakan untuk
meningkatkan produk Google** ("Used to improve our products": Yes; Paid: No).
Dapat diterima di proyek ini karena sumber datanya publik (artikel cek fakta),
tetapi klaim yang diketik pengguna juga terkirim. Perlu dipertimbangkan ulang
bila proyek ini kelak menangani data sensitif. Permintaan memakai
`store=False`; bila `store` dibiarkan bawaan, dokumentasi menyatakan
interaksi Free tier disimpan 1 hari.

### Retry internal SDK dan kuota harian

Retry internal SDK (3 retry per panggilan, tanpa log) **kemungkinan besar ikut
menghabiskan kuota harian**: percobaan live pertama mencatat 5 panggilan
sukses, sedangkan AI Studio menampilkan puncak 28 hari 21 dari 20 RPD dan 7
dari 5 RPM. Itu sesuai dengan permintaan tertolak (dan retry tersembunyi) yang
ikut terhitung, tetapi belum terbukti: puncak 28 hari tidak dapat dikaitkan ke
percobaan itu, dan dokumentasi tidak menyatakan apakah 429 terhitung. Jadi menonaktifkan retry internal (`disable_sdk_retry`) bukan hanya
soal kejujuran log, melainkan juga **anggaran kuota**: dengan RPD 20, satu
kueri yang gagal dulu bisa memakan 24 permintaan.

### Pengaman di kode (bukan di prompt)

Status verifikasi diambil dari label metadata, bukan dari LLM. Tautan rujukan
hanya dari metadata `references` (Aturan Wajib #3); URL apa pun pada keluaran
LLM dibuang dan dihitung. LLM hanya memilih `article_id` dari 3 kandidat; id
di luar kandidat ditolak dan dianggap "tidak cocok". Artikel tanpa `references`
tetap dijawab tanpa bagian rujukan. Konteks per artikel: judul, label,
tanggal, Narasi, Kesimpulan, rujukan; Penjelasan tidak dikirim.

### Hipotesis dan status

- **H1** (LLM yang membaca Narasi dapat membedakan klaim identik dari klaim
  bertetangga topik; gugur bila pada "vaksin flu bikin mandul" LLM
  merujuk artikel 36214): **dukungan awal pada `gemini-3.5-flash-lite` untuk
  satu kasus inti** (kueri itu dijawab tidak ditemukan; alasan: berbeda dari
  artikel vaksin HPV dan cacar air) [DIUKUR ULANG 2026-09-21] — **BERTAHAN**: pada data diperbaiki
  (skor retrieval 0,6671, kandidat 36214, 36577, 36053) LLM kembali menjawab tidak
  ditemukan dan alasannya sama (vaksin flu berbeda dari vaksin HPV, cacar air, dan
  vaksinasi-autisme). **Belum konklusif sampai diuji pada set uji** (satu kasus, pada set
  pengembangan); jangan digeneralisasi.
- **H3** (model kelas Flash cukup untuk tugas ini; gugur bila format terstruktur
  dilanggar berulang atau keliru pada >= 2 dari 10 kueri). **Kriteria dinilai
  terhadap ground truth (label yang ditetapkan manusia), bukan terhadap model
  lain.** Sempat dirumuskan ulang secara relatif ("Flash Lite cukup bila
  keputusannya sama dengan 3.8 Flash"); itu **kesalahan desain hipotesis**:
  kesetaraan dengan model pembanding bukan kebenaran (kesalahan yang sama tampak
  "setara"), dan hasilnya bergantung pada ketersediaan layanan pembanding.
  Status pada 10 kueri [DIUKUR ULANG 2026-09-21] — **BERUBAH sedikit**: pada data lama 10/10 benar; pada
  data diperbaiki **9/10 benar** (positif 4/5, negatif 5/5, 0 pelanggaran format). Kueri 3
  ("malaysia marah ke indonesia soal asap", skor retrieval 0,5739, rumusan paling samar)
  kini dijawab "tidak ditemukan"; sebelumnya benar (36729), dan 3.8 Flash juga menolaknya
  pada data lama. **Penyebabnya tidak dapat dipastikan**: satu proses per kondisi, jadi
  variasi acak LLM tidak terpisah dari efek data. Satu kesalahan dari 10 masih di bawah
  ambang H3 (gugur bila >= 2), tetap **terdukung terhadap ground truth**, **dengan catatan bahwa
  10 kueri itu adalah set pengembangan yang sudah dipakai berulang** (menyusun
  uji retrieval, uji generasi, dan keputusan desain), sehingga **tidak sah
  sebagai bukti mutu**. Bukti mutu hanya dari set uji yang dibekukan (lihat
  "Set uji Versi 1").
- **`gemini-3.8-flash` dihentikan (keputusan 2026-09-21)** karena
  ketidakstabilan layanan: 503 dan `APITimeoutError` di server, serta 429 yang
  muncul saat hitungan permintaan lokal masih di bawah batas harian 20 (penyebab
  429 tidak didiagnosis; diagnosis dihentikan atas keputusan). Baseline 3.8
  Flash tidak selesai (1 dari 10 kueri valid) dan perbandingan mutu tidak
  pernah terjadi: **hasil itu tidak boleh ditafsirkan sebagai 3.8 Flash lebih
  buruk dari Flash Lite.** `--compare` dipertahankan hanya sebagai alat
  informasi.
- **H4** (Gemma 4 dapat menjadi model juri RAGAS): **belum diuji sebagai
  juri**. Uji format JSON (`src/evaluation/gemma_json_check.py`, `gemma-4-31b-it`,
  thinking `minimal`, 3 prompt x 2 mode, 2026-09-21): 6/6 panggilan berhasil;
  mode skema server berfungsi (dokumentasi tidak menyebutnya) dan
  mengembalikan JSON murni 3/3 dengan bentuk sesuai 3/3; mode teks
  (tanpa skema, cara RAGAS) selalu dibungkus pagar ```json (0/3 JSON murni)
  tetapi valid setelah pagar dibuang 3/3 dan bentuk sesuai 3/3. Yang belum
  diketahui: apakah pengurai RAGAS menerima pagar itu, dan mutu penilaian
  (satu alasan mengandung salah ketik "dilarat"; bentuk verdict wajar).
  **Latensi 31-52 dtk per panggilan** walau prompt kecil (121-2521 token
  masuk, tanpa throttling), jauh lebih lambat daripada Gemini (Flash Lite
  ~4-10 dtk). Cukup TPM 16K per panggilan, tetapi waktu jam-dinding menjadi
  kendala (lihat "Perencanaan kapasitas"). Karena mode skema berfungsi, risiko
  format untuk H4 sebagian besar gugur; yang tersisa adalah latensi dan mutu
  penilaian. **RAGAS belum dipasang: menunggu set uji selesai.**
- Eksperimen thinking ditunda sampai set uji dibekukan dan generator final
  ditetapkan (jangan ubah dua variabel sekaligus). Selama ini semua hasil
  Gemini memakai `thinking_level=medium` eksplisit, bukan bawaan Flash Lite
  (`minimal`).
- **Hasil live 2026-09-21** (bukan evaluasi statistik; 10 kueri) [DIUKUR ULANG 2026-09-21]: bagian di
  bawah ini adalah hasil pada data LAMA (terduplikasi); hasil pada data diperbaiki ada di
  "Pengukuran ulang setelah perbaikan duplikasi".
  - `gemini-3.5-flash-lite` (thinking medium): 10/10 selesai tanpa 429/503,
    positif 5/5 (artikel dan label benar), negatif 5/5 "tidak ditemukan",
    0 pelanggaran format, 0 URL di luar metadata, latensi rata-rata 6,9 dtk.
    Kueri 3 ("malaysia marah ke indonesia soal asap", skor 0,5669) dijawab
    benar (36729).
  - `gemini-3.8-flash` (thinking medium): probe OK (6,8 dtk); baseline
    **hanya 1/10 valid** (kueri 1: 36730, benar). Kueri 2-5 gagal di API:
    `APITimeoutError` 90 dtk, lalu 503 (saran tunggu 30 dtk), lalu 429 berulang
    dengan saran tunggu 54-59 dtk yang klasifikasinya "tidak_diketahui" (isi
    galat tidak memuat quotaId per `classify_429`; **isi aslinya belum tercatat**
    karena log baru menyertakannya setelah kejadian). Kueri 6 tidak dikirim:
    buku besar lokal mencapai 20/20 (menghitung SEMUA percobaan, termasuk
    503/timeout/429, jadi mungkin melebihi hitungan server). Penyebabnya belum
    diketahui: bukan RPM dari sisi kita (percobaan berjarak >= 30 dtk) dan 429
    muncul saat hitungan lokal baru ~8-19 dari 20, tetapi apakah ini beban/
    kapasitas server ("actual capacity may vary") atau batas lain belum dapat
    dibedakan. Dihentikan (lihat di atas); `data/generation_eval_gemini-3.8-flash.jsonl`
    hanya memuat 1 kueri valid dan tidak dipakai.
  - Pemutus baru: evaluasi berhenti setelah 2 kueri beruntun gagal di API.
- **Ulangan diagnostik 2026-09-21** (`evaluation.repeat_eval`; murni diagnostik, tidak boleh dipakai
  untuk menyetel apa pun): 10 kueri set pengembangan x 5 run = 50 panggilan `gemini-3.5-flash-lite`
  (thinking medium) pada data diperbaiki. **Keputusan (verdict + artikel) identik pada semua 5 run
  untuk 10 dari 10 kueri** (0 gagal, 0 pelanggaran format); kueri 3 ditolak 5 dari 5 kali dengan
  alasan yang sama ("klaim pengguna hanya menyatakan kemarahan Malaysia soal asap secara umum,
  sedangkan artikel membahas klaim spesifik pelaporan ke PBB"). Yang bervariasi hanya redaksi
  alasan. Kandidat retrieval sama di semua run. Jadi selisih kueri 3 antara proses lama (diterima) dan
  proses baru (ditolak) kemungkinan besar efek data, bukan variasi acak; ini belum terbukti karena data
  lama tidak dapat dijalankan ulang. Batas atas 95% laju pembalikan keputusan (0 dari 50): ~6%, hanya
  untuk jenis kueri yang jelas; kueri batas belum terwakili.
  **Setelan sampling generator** (tidak diubah): `generation_config` hanya berisi `thinking_level`
  (medium) dan `max_output_tokens` (8192); temperature, top-p, top-k, dan seed TIDAK diatur, jadi
  default server. Dokumentasi Gemini 3 (https://ai.google.dev/gemini-api/docs/gemini-3): default
  temperature 1,0 dan "sangat disarankan" tidak diubah; menurunkannya dapat menyebabkan looping atau
  penurunan mutu pada tugas penalaran. Field `generation_config` klien Interactions terpasang
  (google-genai 2.24) tidak memuat temperature/top_p/top_k; ada `seed` (tidak dipakai; apakah server
  menghormatinya belum diverifikasi).
- Sampel evaluasi hanya 5 positif dan 5 negatif dan berstatus set
  pengembangan: indikasi, bukan bukti statistik.

### Perencanaan kapasitas (evaluasi 50 kueri)

Perkiraan, bukan pengukuran; angka kuota per 2026-09-21. Perkiraan token
per panggilan (generator) [DIUKUR ULANG 2026-09-21]: 2,2-3,6K token masuk pada data lama -> 1,7-2,1K pada
data diperbaiki (terukur pada 10 kueri; sekitar 20-40% lebih kecil). Perkiraan RAGAS di
bawah dibuat dari angka lama dan belum dihitung ulang (RAGAS belum dipasang); anggap terlalu
besar.

- **Generator Flash Lite** (RPD 500, RPM 15): 50 panggilan (terburuk 100 dengan
  percobaan ulang format) = **1 hari**, >= 3,4 menit menurut RPM (terukur:
  ~6,9 dtk per kueri). Ini generator Versi 1.
- (Dihentikan) generator 3.8 Flash: RPD 20 akan membutuhkan 3 hari; tidak
  ditempuh.
- **Juri Gemma 4** (TPM 16K, RPM 30, RPD 14,4K), bila H4 layak: RAGAS ~6-7
  panggilan/sampel, ~8-14K token masuk/sampel (perkiraan dari struktur metrik
  dan konteks kita; RAGAS belum terpasang dan tidak diperiksa), prompt
  terbesar ~3-4K << 16K. **Koreksi setelah pengukuran:** latensi Gemma 31-52
  dtk per panggilan (terukur, 6 panggilan) sehingga ~350 panggilan berurutan
  ~3-5 jam; TPM (~1-2 sampel/menit) bukan lagi pembatas, latensi yang
  membatasi. Dengan konkurensi ~4 (RPM 30 dan TPM 16K masih cukup) sekitar
  ~1 jam; keduanya masih perkiraan. Tetap **1 hari**, kuotanya terpisah dari
  generator.
- **Skenario realistis:** Flash Lite + juri Gemma = 1 hari. RAGAS belum
  dipasang; menunggu set uji selesai.

### Set uji Versi 1 (pedoman dikunci; butir belum dibuat)

Set uji 50 kueri untuk bukti mutu, terpisah dari 10 kueri pengembangan. Prinsip yang ditetapkan pemilik proyek:
10 kueri pengembangan tidak boleh masuk; setelah set uji dibekukan, prompt sistem dan logika generator tidak boleh
diubah berdasarkan hasilnya (bila perlu diubah, dibuat set uji baru); komposisi 20 positif + 20 negatif sulit + 10
negatif mudah (tetangga topik seperti "vaksin flu bikin mandul" lebih penting daripada negatif mudah); sebaran
positif mengikuti label dan kategori 150 artikel (dengan PARODI di-oversample); ragam gaya bahasa; setiap butir
ditinjau manual; enam artikel dikecualikan sebagai target (36730, 36737, 36729, 36738, 36731, 36214); sumber butir:
buatan model (Gemma 4 dari Narasi), buatan manusia, dan teks nyata (negatif dari arsip TurnBackHoax di luar 150
artikel, positif dari situs cek fakta lain, dengan URL asal dan data pribadi dibersihkan).

- **Pedoman anotasi** `testset/ANNOTATION_GUIDE.md` **v1.0, DIKUNCI 2026-09-21** (commit `2500013`, tag
  `annotation-guide-v1.0`), sebelum satu butir pun dibuat. Definisi "klaim sama": klaim inti artikel (KIA = judul;
  123 dari 150 artikel mengutipnya di Kesimpulan) dengan unsur inti (subjek, tindakan, objek pembeda), uji dua arah
  dan uji Kesimpulan, serta aturan kasus khusus (lebih umum, lebih spesifik, sebagian, sinonim, pertanyaan, ambigu).
  `tests/test_testset_locks.py` gagal bila pedoman atau prompt/skema berubah diam-diam. **Aturan: pedoman tidak
  boleh direvisi selama pembuatan set uji v1**; kasus tak tercakup dicatat di `testset/kasus_terbuka.md` dan
  diputuskan dengan aturan terdekat.
- **Pra-registrasi** `testset/v1.meta.json` (ditulis sebelum data): metrik utama = **keputusan modus dari 3 run**;
  kesepakatan antar-run dilaporkan per nilai `kekhususan`; **seed tidak dipakai sebagai jaminan determinisme**
  (efeknya belum diverifikasi); interval Wilson 95% di seluruh laporan; ambang H1 (negatif sulit "ditemukan"
  pada keputusan modus: <= 1 dari 20 terdukung, 2 tidak konklusif, >= 3 gugur) dan H3 (>= 5 kesalahan dari 50 atau
  pelanggaran format >= 2 gugur); laporan wajib: akurasi per tipe/kekhususan/sumber (buatan model vs teks nyata),
  Recall@3 retrieval terpisah, analisis per pasangan minimal termasuk jumlah pasangan yang DUA-DUANYA benar (ukuran
  paling langsung untuk H1).
- **Keterbatasan:** pelabelan dilakukan **satu anotator manusia**, sehingga kesepakatan antar-anotator tidak
  terukur (hanya konsistensi dalam-anotator: 10 butir acak dianotasi ulang setelah satu minggu). Pedoman ditulis
  setelah melihat keluaran model pada set pengembangan (risiko rasionalisasi; dibatasi oleh jangkar KIA yang sudah
  ada dan pengunciannya sebelum butir dibuat).
- **Prompt sistem diselaraskan dengan pedoman sebelum pembekuan** (commit `37fcac9`; keputusan pemilik proyek).
  Definisi resmi "klaim sama" kini tertulis di dalam sistem: bahan pembanding utama adalah KIA (Judul) dan unsur
  inti, Narasi hanya rujukan pendukung; uji dua arah, uji Kesimpulan, dan aturan kasus khusus; contoh baru
  (tingkat kekhususan) hanya dari enam artikel yang dikecualikan dan tanpa memakai teks 10 kueri pengembangan
  (diuji `tests/test_prompt.py`). Tidak ada verdict ketiga. Skema tetap empat bidang (deskripsi `klaim_sama`
  disesuaikan).
- **Pelabelan ulang kueri 3 pada set pengembangan** (disetujui pemilik proyek): "malaysia marah ke indonesia soal
  asap" diubah dari positif (target 36729) menjadi **negatif sulit dengan `kekhususan=umum`**. **Perubahan ini
  dilakukan SETELAH melihat keluaran model** (yang menolaknya 5 dari 5 kali dengan alasan "terlalu umum"), dengan
  dasar pedoman yang berjangkar pada KIA (tindakan inti "melaporkan ke PBB" tidak ada pada klaim pengguna; uji dua
  arah dan uji Kesimpulan gagal). **Hanya berlaku untuk set pengembangan**, bukan bukti mutu.
  Kode kini memisahkan **dua label** per kueri (`evaluation/devset.py`): `expected_retrieval_article` (artikel yang
  seharusnya terjangkau retrieval, untuk Recall@3) dan `expected_verdict` (`ditemukan` | `belum_ditemukan`,
  keputusan akhir yang seharusnya). Kueri 3: `expected_retrieval_article=36729`, `expected_verdict=belum_ditemukan`,
  `kekhususan=umum`. Format butir set uji v1 memakai struktur dua label yang sama.
- **Kueri 2 = `kekhususan=batas`** (keputusan pemilik proyek): "orang tua" ambigu terhadap "lansia" (lebih sering
  berarti ayah-ibu) dan **tidak diputuskan secara umum**, karena menetapkannya untuk seluruh set uji sama dengan
  merevisi pedoman yang terkunci. Butir serupa di set uji v1 diputuskan **per butir lewat uji Kesimpulan**. Butir
  batas dilaporkan terpisah dan tidak masuk hitungan utama (ringkasan `generation_eval` kini memisahkannya).
- **Dua jenis kesalahan dilaporkan terpisah** (`evaluation/metrics.py`, dipra-registrasi di `v1.meta.json`):
  **kecocokan palsu** (expected `belum_ditemukan` dijawab ditemukan), **penolakan palsu** (expected `ditemukan`
  dijawab belum ditemukan), dan **artikel salah**, masing-masing dengan interval Wilson 95%, terpisah untuk butir batas
  dan non-batas. Alasannya: prompt sistem yang lebih ketat cenderung menggeser kesalahan dari kecocokan palsu ke
  penolakan palsu, dan akurasi total saja menyembunyikan pergeseran itu.
- **Pemeriksaan regresi setelah perubahan prompt** (10 kueri set pengembangan, satu run, `gemini-3.5-flash-lite`;
  **hanya pemeriksaan regresi, tidak boleh dikutip sebagai bukti mutu**): keputusan berbeda pada **1 dari 10**
  dibanding modus 5 run sebelum perubahan. Kueri 2 ("ada link pendaftaran bantuan buat orang tua, itu beneran?")
  yang 5/5 ke 36737 kini "tidak ditemukan", dengan alasan "'orang tua' lebih umum, tidak menyebut 'lansia'".
  Itu persis kasus perbatasan yang ditandai pedoman (★ untuk 36737). Sembilan kueri lain identik (kueri 3 tetap
  ditolak; 0 pelanggaran format, 0 URL di luar metadata, 0 galat 429). Token masuk naik sekitar 700 per panggilan
  (prompt ~4,6 ribu karakter, sebelumnya ~2 ribu). Tidak ada perubahan setelan atau prompt berdasarkan hasil ini.
  Ringkasan `generation_eval` saat itu menyebut "H3 GUGUR (keliru 2/10)": itu hitungan mekanis dengan label lama
  kueri 3 dan tidak memisahkan butir batas; sudah diperbaiki (lihat pemisahan dua label di atas). Dengan label baru,
  satu-satunya selisih adalah kueri 2 (butir batas), sehingga pada butir non-batas tidak ada kesalahan.

### Pengumpulan kandidat set uji v1 (2026-09-21; belum ada kandidat yang ditinjau atau dijalankan)

Alat: `src/candidates/archive.py` (arsip TurnBackHoax di luar 150 artikel; jeda 1,5 dtk, timeout 45 dtk, cache
HTML mentah di `data/candidates_cache/`, tidak di-commit) dan `src/candidates/screen.py` (penyaringan terhadap
150 artikel: kemiripan judul, retrieval, penanda data pribadi; alat bantu, keputusan akhir manusia). Konten pihak
ketiga diperlakukan sebagai data, bukan instruksi.

- **Kepatuhan situs:** `turnbackhoax.id/robots.txt` mengizinkan semua (`Disallow:` kosong). **Kompas dan Tempo
  melarang agen Claude secara eksplisit** di robots.txt (`Disallow: /` untuk anthropic-ai, ClaudeBot, Claude-User,
  Claude-Web, Claude-SearchBot, dll.) dan **Komdigi membalas 403** pada klien otomatis. Ketiganya TIDAK diakses
  langsung (tanpa menyamar sebagai browser). **Keputusan pemilik proyek: judul dan URL hasil pencarian dari
  Kompas, Tempo, dan Komdigi juga TIDAK dipakai** (situs menolak agen AI, set uji akan diterbitkan publik, dan
  independensi judulnya rendah). Tidak ada judul atau URL dari situs-situs itu yang tersimpan di repositori atau
  `data/candidates/`. Positif dari situs cek fakta lain hanya dari situs yang `robots.txt`-nya tidak membatasi agen
  Claude; positif lintas situs otomatis yang tidak ada dilepas dan dicatat di `v1.meta.json`. Positif tulisan manusia:
  pemilik proyek menulis klaim setelah membaca artikel sebagai manusia (sumber `manusia`, URL sebagai asal-usul),
  dengan topik singkat sebagai pemandu, sehingga independensinya tidak penuh.
- **Arsip TurnBackHoax:** 100 artikel (10 halaman daftar tersebar, 2024-2026) di luar 150 artikel; disimpan teks
  Narasi + URL. 69 memuat blok kutipan pesan yang bersih (>= 25 karakter); 66 tanpa penanda data pribadi pada
  teks klaim (3 memuat URL yang harus dibersihkan). **Tidak ada satu pun yang klaimnya sama dengan artikel basis
  data** (kemiripan judul tertinggi 0,86; 0 di atas 0,90), jadi arsip tidak menghasilkan calon positif; ia menghasilkan
  calon NEGATIF: 18 dengan pola judul dan label sama dengan artikel basis data tetapi entitas berbeda (calon negatif
  sulit "pola sama, entitas beda", mis. "Lowongan Kerja SPX Express" vs "Puskesmas"), dan 16 dengan skor retrieval
  < 0,60 (calon negatif mudah). **Kelas otomatis tidak dapat dipercaya**: 20 kandidat ditandai
  "kemungkinan_sama" ternyata keluarga tautan penipuan dengan entitas berbeda, bukan klaim yang sama.
- **Uji awal lintas situs (dilepas):** dari 10 artikel basis yang dicoba lewat pencarian, kecocokan jelas 4, ambigu
  3, tidak ada 3, dan judulnya mirip judul basis data (kemiripan karakter 0,61-0,94): independensi rendah. Hasil itu
  tidak dipakai dan tidak disimpan.
- **Kelas usulan otomatis** penyaring disimpan di berkas terpisah (`archive_screen_class.jsonl`) dan tidak
  ditampilkan pada berkas tinjauan (bias anchoring); setelah tinjauan selesai dibandingkan dan kesepakatannya
  dilaporkan sebagai keandalan penyaring.
- **Data pribadi:** nama akun hanya pada kalimat pembuka Narasi (bukan pada teks klaim yang dikutip), jadi
  butir memakai teks klaim yang dikutip, bukan seluruh Narasi.

### Catatan untuk tahap evaluasi (RAGAS)

Model juri sebaiknya **berbeda** dari model generator agar penilaian tidak
bias terhadap keluarannya sendiri. Abstraksi penyedia membuat ini mudah:
cukup instansiasi penyedia kedua dengan `LLM_MODEL` lain.

**Koreksi independensi (2026-09-22):** Gemma dan Gemini bukan "keluarga
berbeda" dari generator, melainkan **model berbeda dari pengembang yang
sama** — keduanya dikembangkan Google dari riset yang berkaitan. Pemisahan
pembuat butir (Gemma), generator (Gemini Flash Lite), dan juri (kandidat:
Gemma) hanya **mengurangi**, bukan menghilangkan, risiko bias bersama (mis.
kecenderungan gaya jawaban atau kesalahan sistematis yang sama-sama
diwariskan dari data/RLHF Google). Berlaku juga untuk H4 di atas dan
untuk pembuat butir buatan_model di set uji v1.

### Duplikasi teks seksi (TERSELESAIKAN 2026-09-21)

Ditemukan saat menyusun generator: teks **Narasi dan Penjelasan di `articles.json`
terduplikasi** pada 150 dari 150 artikel (panjang JSON / panjang teks seksi HTML asli:
median 2,00; Kesimpulan 1,00). Penyebabnya `extract_sections()` mengiterasi elemen bersarang
(induk `div` dan anak `p`/`strong`) sehingga isinya tercatat dua kali.

Perbaikan (commit `b29d91c`): pohon HTML ditelusuri sekali secara berurutan, bukan membuang
duplikat sesudahnya. Artikel 36590 (Penjelasan bersarang di dalam Narasi) dan 36483 (Kesimpulan
bersarang di dalam Penjelasan) kini terpisah benar; 36603 diuji sebagai regresi (seksinya
memang normal setelah duplikasi hilang). Uji `tests/test_parser.py` kini gagal bila rasio
panjang hasil parse terhadap teks HTML asli melebihi 1,1 (atau di bawah 0,9). Hasil pada 150
artikel: rasio Narasi/Penjelasan median 1,00 (maks 1,00); 148 dari 150 artikel dalam 0,5% dari
1,0 (dua sisanya, 36590 dan 36483, wajar karena seksi HTML-nya memuat seksi bersarang);
Kesimpulan, `references`, dan kolom lain tidak berubah. `articles.json` di-parse ulang dari
cache (`python -m scraping.reparse`), indeks dibangun ulang dengan `ingest.py --rebuild` dan
diverifikasi segar (`evaluation.index_check`: id, teks, metadata identik; vektor sampel di-embed
ulang, kosinus 1,000000). Retriever kini membaca teks baru (panjang Narasi ~50% dari sebelumnya,
sama dengan `articles.json`).

### Pengukuran ulang setelah perbaikan duplikasi (2026-09-21)

Data lama = `articles.json` dan indeks sebelum perbaikan; data baru = sesudah perbaikan dan
`--rebuild`. Kolom terakhir menandai apakah temuan **bertahan** atau **berubah**.

| Ukuran | Lama | Baru | Temuan |
| --- | --- | --- | --- |
| Rasio panjang seksi (parse / HTML asli), median Narasi | 2,00 (1,62-2,29) | 1,00 (0,41-1,00) | berubah (cacat hilang) |
| idem, Penjelasan | 2,00 (1,62-2,74) | 1,00 (0,83-1,00) | berubah (cacat hilang) |
| idem, Kesimpulan | 1,00 | 1,00 | bertahan |
| Artikel dengan rasio > 1,1 | 150 (Narasi), 149 (Penjelasan) | 0 | berubah |
| Token median Narasi / Penjelasan / Kesimpulan | 270 / 450 / 61 | 137 / 225 / 61 | berubah (Kesimpulan bertahan) |
| Token p90 Narasi / Penjelasan | 454 / 807 | 228 / 369 | berubah |
| Token maks Narasi / Penjelasan | 1442 / 1187 | 422 / 573 | berubah |
| Chunk terpotong 512 token (Narasi / Penjelasan / Kesimpulan) | 11 / 58 / 0 (69 dari 450, 15,3%) | 0 / 3 / 0 (3 dari 450, 0,7%) | berubah |
| Seksi pemenang, top-1 chunk, 10 kueri (P / N / K) | 6 / 2 / 2 | 7 / 2 / 1 | bertahan (Penjelasan tetap teratas) |
| Seksi pemenang, top-5 chunk, 50 hasil (P / N / K) | 20 / 18 / 12 | 22 / 14 / 14 | bertahan (arah) |
| Artikel top-1 sama dengan sebelumnya | - | 9 dari 10 kueri | bertahan |
| Skor kasus vaksin flu (artikel teratas 36214) | 0,6508 | 0,6671 | bertahan (tetap di atas 3 dari 5 positif) |
| Positif terendah / negatif tertinggi | 0,5669 / 0,6508 | 0,5739 / 0,6671 | bertahan (skor tak memisahkan) |
| Flash Lite, 10 kueri (benar terhadap ground truth) | 10/10 | 9/10 (kueri 3 kini "tidak ditemukan") | berubah (penyebab tak terpastikan) |
| Flash Lite, kasus vaksin flu | tidak ditemukan | tidak ditemukan | bertahan |
| Flash Lite, token masuk per panggilan | 2,2-3,6K | 1,7-2,1K | berubah |
| Flash Lite, pelanggaran format / URL di luar metadata / 429 | 0 / 0 / 0 | 0 / 0 / 0 | bertahan |

Catatan: (1) "Seksi pemenang" pada 10 kueri (5 positif dan 5 negatif, set pengembangan) tidak
sebanding dengan angka 5 kueri di riwayat. (2) Pada data baru, kriteria 4 evaluasi generasi
menandai `36730.` pada kueri 1: LLM menyebut id artikel di kolom alasan; itu penanda heuristik,
bukan klaim tak berdasar. (3) Selisih kueri 3 berasal dari satu proses per kondisi; ulangan
akan memisahkan variasi acak dari efek data (belum dilakukan).

---

## Daftar Pekerjaan Sebelum Portofolio

Tidak mendesak dan tidak memengaruhi evaluasi, tetapi harus beres sebelum repositori ditampilkan:
IDE akan menampilkan garis merah pada siapa pun yang membukanya.

- **22 galat tipe pyright (mode standar) di `tests/`** (per 2026-09-21): `test_generator.py` 11 (mis.
  `ScriptedProvider` bukan turunan `LLMProvider`), `test_client.py` 7, `test_discovery.py` 3,
  `test_reparse.py` 1. Periksa dengan `npx pyright tests` (atau Pylance). `test_gemini.py` dan
  `_fakes.py` sudah bersih (pyright standar dan strict, mypy, ruff).
- **Gaya kode:** dengan `ruff==0.16.9` (dikunci di `requirements-dev.txt`; aturan bawaannya lebih
  luas dari versi sebelumnya), `ruff check src tests` masih menandai **29 temuan lama** (per
  2026-09-25) di luar berkas demo: 14 I001 (mis. `src/llm/limits.py`), 3 ISC004, dan 12 lain-lain.
  Berkas demo (`src/app.py`, `src/presentation.py`, `tests/test_presentation.py`) bersih; I001
  di `src/app.py` dikecualikan secara sengaja di `ruff.toml` (urutan impor `ingest` lebih dulu).
- **Konfigurasi alat statis** (saran, belum dikerjakan): satu `pyproject.toml` untuk pyright/ruff agar
  IDE dan CI konsisten, termasuk jalur `src` dan `tests`.

---

## Keterbatasan yang Diketahui

Batasan berikut sudah disadari dan diterima. Jangan memperlakukannya
sebagai cacat yang perlu diperbaiki tanpa diminta.

- **KETERBATASAN UTAMA: sistem hanya andal untuk klaim di bawah 512 token
  pada sisi kueri.** Retrieval hanya meng-embed 512 token pertama pesan
  (`MAX_SEQ_LENGTH`). Pada pesan panjang, klaim terdorong keluar dari jendela
  embedding sehingga tidak ikut dicari. Terukur (ablasi 2026-09-25, 20 butir
  positif, pengganggu sintetis di depan dan belakang klaim): Recall@3 **19/20**
  pada ~1.500 dan ~3.000 karakter, runtuh ke **2/20** pada ~5.000 karakter
  (klaim di luar 512 token pada 18/20). Pembanding klaim-di-awal (pengganggu
  hanya di belakang) tetap **19/20** pada ~5.000 karakter, jadi penyebabnya
  pemotongan token, bukan panjang itu sendiri. Mitigasi di demo: batas masukan
  1.500 karakter dan peringatan sebelum pemeriksaan sejak ~220 token (batas
  5.000 sebelumnya ditetapkan tanpa pengukuran). Perbaikan sebenarnya adalah
  agenda Versi 2 (rewriter tugas 1).

- **Klarifikasi lebih tipis untuk hoaks Oktober-November 2025** (dicatat 2026-10-02). Klarifikasi
  disusun dari seksi Kesimpulan, dan pada periode itu Kesimpulan TurnBackHoax umumnya hanya satu
  kalimat ("Unggahan berisi klaim ... merupakan konten palsu (fabricated content)") tanpa kalimat
  "Faktanya ..." yang memuat fakta sebenarnya. Terukur pada kelompok 5: median Kesimpulan 140
  karakter (Okt 2025, 54 artikel) dan 137 (Nov 2025, 126 artikel), dibanding 243 (Des 2025) dan 239
  pada 1.172 artikel acuan; 18 Kesimpulan lebih pendek dari yang terpendek di acuan (114), terpendek
  91 karakter. Faktanya sendiri ada di Penjelasan, yang tidak dikirim ke LLM. **Masukan Versi 2:**
  penyusunan/gaya bahasa klarifikasi perlu sumber selain Kesimpulan untuk artikel seperti ini (ikut
  ditimbang bersama agenda menghapus Penjelasan dari indeks). Kelompok 6 (30 Sep-23 Okt 2025) sama: median
  136 karakter, hanya 4/110 Kesimpulan diawali "Faktanya". Periode sebelum 30 Sep 2025 belum diketahui.
- **Dua artikel berseksi kosong di sumber** (kelompok 5; digabung apa adanya, keputusan 2026-10-03):
  29687 tanpa Penjelasan; 29670 (PARODI) tanpa Narasi dan Penjelasan, sehingga hanya terjangkau
  lewat chunk Kesimpulan. **Itu jalur pencarian terlemah:** pada ablasi, retrieval dengan Kesimpulan
  saja turun bermakna (Recall@3 non-batas 21/40 vs 29/40 pada indeks 1.532, p 0,008; positif 15/20
  vs 20/20), jadi klaim yang cocok dengan 29670 lebih mungkin tidak terambil
  (`v1_temuan_untuk_v2.md` bagian 11).
- **Retriever produksi memakai pencarian perkiraan (HNSW).** Dengan `ef_search` bawaan (100), sejak
  indeks 1.532 artikel hasilnya tidak lagi selalu sama dengan pencarian eksak (1 dari 64 kueri
  berbeda di top-3). Sejak 2026-10-03 indeks produksi memakai `ef_search` 2000 dan sama dengan
  pencarian eksak pada 64 kueri tetap, tetapi itu **hanya terukur pada 4.593 chunk**: saat basis data
  bertambah bisa meleset lagi, jadi `evaluation.retriever_exactness` wajib dijalankan setiap kali
  indeks bertambah. Arsip tetap 100 (`v1_temuan_untuk_v2.md` bagian 10).
- **Tidak ada mekanisme untuk menyegarkan artikel lama yang isinya berubah di sumber** (dicatat
  2026-09-27). Artikel yang sudah ada di cache `data/raw_html/` tidak pernah diambil ulang (mode maju
  berhenti pada artikel pertama yang sudah dimiliki; cache dipakai tanpa memeriksa perubahan), jadi
  koreksi, pembaruan Kesimpulan, atau perubahan label oleh TurnBackHoax tidak akan terlihat. Contoh
  kasus yang perlu diwaspadai: 35176 berseksi Hasil Periksa Fakta "Dalam Proses" (judul SALAH,
  Kesimpulan menyatakan klaimnya keliru) -- artikel semacam ini bisa saja diperbarui kemudian. Ini
  **bukan** bukti bahwa putusannya berubah; hanya contoh artikel yang isinya mungkin belum final.
- Basis pengetahuan hanya memuat hoaks yang **sudah** diverifikasi
  Mafindo. Klaim yang baru viral belum tentu ada di dalamnya, sehingga
  jawaban "belum ditemukan" adalah keluaran yang sah dan benar.
- Situs sumber diperbarui secara berkala, bukan real-time. Diperlukan
  scraping ulang secara terjadwal agar basis pengetahuan tetap mutakhir.
- Total artikel di situs sumber sekitar 15.000 (1.558 halaman × 10
  artikel). Scraping penuh memakan waktu berjam-jam karena latensi
  server. Tahap awal dibatasi 100–200 artikel terbaru.
- Jalur retry dan backoff belum teruji pada beban nyata. Selama scraping
  150 artikel server merespons stabil: tidak ada read timeout maupun
  connection error, sehingga tidak satu pun retry terpicu (hanya satu
  `ConnectionError` yang di-retry, pada pengambilan ulang satu artikel
  sesudahnya). Selebihnya jalur ini hanya diuji dengan session palsu di
  `tests/` (`test_client.py`). Server juga pernah membalas 200 OK dengan halaman
  galat ("Terjadi kesalahan saat mengambil data"); kasus ini ditangani
  validasi HTML sebelum caching, yang juga baru diuji dengan fixture.
- Embedding dibatasi ke **512 token** (`MAX_SEQ_LENGTH` di
  `src/chunker.py`) meski bge-m3 mendukung 8192. Alasan: mesin dev
  hanya berCPU dengan RAM bebas ~2,5 GB, sehingga batas pendek menekan
  memori dan waktu embedding; dan target pencocokan utama adalah seksi
  Narasi (median 270 token) yang mayoritas muat utuh. Terukur pada 450
  chunk (150 artikel) [DIUKUR ULANG 2026-09-21] — **BERUBAH**: pada data lama Narasi terpotong 11/150
  (7,3%), Penjelasan 58/150 (38,7%), Kesimpulan 0/150 (median Narasi 270 token); pada data
  diperbaiki Narasi **0/150**, Penjelasan **3/150 (2,0%)**, Kesimpulan 0/150 (median Narasi
  137, Penjelasan 225, Kesimpulan 61 token). Angka lama menghitung teks ~2x; alasan
  "mayoritas Narasi muat utuh" justru makin kuat. Chunk terpotong ditandai `truncated` pada
  metadata untuk audit. Bagian ekor Narasi/Penjelasan yang terpotong tidak
  ikut terindeks; keputusan ini perlu ditinjau ulang di Versi 2 (mengubah
  batas berarti embedding ulang semua chunk: `python src/ingest.py --rebuild`).
- Penyaringan `references` bersifat konservatif dan berbasis domain:
  semua tautan ke media sosial (Instagram, Facebook, TikTok, X/Twitter,
  Threads, YouTube), arsip, hosting gambar, dan (sejak 2026-10-03) pemendek URL dibuang, tanpa membedakan
  postingan dari beranda akun. Akibatnya sebagian artikel (16 dari 150
  pada scraping awal) berakhir dengan `references` kosong padahal
  Referensi aslinya berisi tautan. Tautan yang dibuang tetap tersimpan di
  `references_raw` dan `references_filtered`.
- **Pengecualian baris "Sumber:" bertumpu pada daftar yang belum ditinjau dan pada `*.go.id`**
  (dicatat 2026-10-03). (1) `links.TRUSTED_SOURCE_DOMAINS` (media dan cek fakta) disusun Claude Code
  pada 2026-10-03 dari domain yang muncul sebagai rujukan di data -- **melingkar**, karena justru
  kebersihan rujukan itulah yang sedang diperiksa; "klasifikasi domain" 2026-09-26 tidak pernah ada
  sebagai daftar. **Isi daftar sudah dibaca dan disetujui pemilik proyek (2026-10-03)**; cara
  penyusunannya tetap melingkar. Pada data saat ini hanya dua URL (33497) yang bergantung padanya.
  Pencocokan pada batas domain (host persis atau subdomain sejati), diuji dengan tiruan nama media. (2) Pengecualian `*.go.id` berisiko: situs pemerintah di Indonesia
  cukup sering diretas dan disisipi halaman judi atau penipuan, sehingga URL `.go.id` di baris
  "Sumber:" bisa saja memang halaman berbahaya. Tidak diubah sekarang (keputusan pemilik proyek);
  pada data saat ini hanya dua URL (32110, 31532), keduanya beranda/layanan resmi yang disebut
  Kesimpulan artikelnya. Penilaian kredibilitas per-URL adalah lingkup Versi 2.
- **Penyaringan pemendek URL dan arsip ikut membuang sebagian rujukan yang benar -- harga yang
  diterima dengan sadar** (keputusan pemilik proyek 2026-10-03). Contoh: 36089, yang tautan `bit.ly`-nya
  menurut Kesimpulan adalah tautan pendaftaran resmi Kemnaker (tujuannya tidak diperiksa). Alasannya:
  tujuan tautan pendek tidak dapat diverifikasi pengguna sebelum diklik, dan aturan pencegah tautan
  hoaks berbawaan "saring kecuali terbukti sah". Terukur pada 1.532 artikel: 13 rujukan berpemendek
  dan 27 rujukan arsip tersaring; artikel tanpa rujukan 200 -> 205. Tautan itu tetap ada di
  `references_raw`/`references_filtered`.
- **Ditunda ke Versi 2:** penyaringan berbasis kredibilitas sumber yang
  lebih cerdas, termasuk membedakan akun resmi instansi (mis.
  `instagram.com/kemensetneg.ri/`) dari akun penyebar hoaks. Alasan
  keputusan: (1) percobaan meloloskan beranda akun ("Opsi 2") tidak
  menyelamatkan satu pun dari 16 artikel yang `references`-nya kosong,
  karena artikel-artikel itu hanya berisi postingan dan arsip; (2) 11
  beranda akun yang lolos tidak bisa diverifikasi dari sini (Instagram dan
  TikTok menyajikan halaman kosong/login untuk klien HTTP biasa), sehingga
  sebagian bisa saja akun penyebar hoaks, yang melanggar Aturan Wajib #1.
  Trade-off-nya dinilai merugikan, jadi dipilih penyaringan penuh per
  domain. Penilaian kredibilitas sumber memang bagian dari lingkup
  Corrective RAG.
