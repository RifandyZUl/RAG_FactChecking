# Pemetaan hash commit: riwayat asli ke riwayat yang ditulis ulang

Riwayat git repositori ini ditulis ulang pada 25 Oktober 2026 dengan `git filter-repo` 2.47.0. Hanya dua hal
yang diubah:

1. **Baris atribusi asisten AI di pesan commit dihapus**, yaitu 175 baris `Co-Authored-By: Claude …`
   (Claude Opus 5.5 dan Claude Sonnet 5). Baris `Claude-Session` dan "Generated with Claude Code" tidak pernah
   ada. Dua judul commit yang menyebut "Claude Code" sebagai keterangan kejadian dibiarkan apa adanya.
2. **Identitas author, committer, dan pembuat tag diseragamkan** menjadi `RifandyZul <rzultiandra@gmail.com>`.
   Sebelumnya 172 commit dan kedua tag memakai `rzultiandra@gmail.comm` (salah ketik), dan satu commit memakai
   identitas editor web GitHub (lihat catatan commit `4fdadd4` di bawah).

Isi berkas tidak berubah. Ini diperiksa sebelum riwayat baru dipakai:

- jumlah commit sama (177 lama, 177 baru);
- untuk setiap pasangan di `commit-map` filter-repo, hash tree (isi seluruh berkas) dan tanggal author sama,
  177 dari 177;
- kedua tag beranotasi (`testset-v1`, `annotation-guide-v1.0`) tetap tag beranotasi, menunjuk commit dengan
  tree yang sama seperti tag lama, dan pesan tagnya sama;
- 0 baris `Co-Authored-By` tersisa, dan semua identitas hanya `RifandyZul <rzultiandra@gmail.com>`;
- seluruh uji otomatis, termasuk uji kunci, lolos di clone hasil penulisan ulang.

Karena pesan dan identitas ikut membentuk hash, **semua hash commit berubah**. Dokumen beku dan dokumen sejarah
(`testset/`, `docs/rancangan/`, `docs/adr/`, `docs/audit/`, dan `CLAUDE.md`) sengaja tidak diubah, jadi hash di
sana tetap hash riwayat asli. Pakai tabel di bawah untuk menemukan commit yang sama di riwayat ini. Uji yang
membaca git (`tests/core/test_testset_locks.py`) memakai nama tag `testset-v1`, bukan hash, jadi tidak terpengaruh.

## Riwayat asli

- **Repo arsip:** repositori lama diganti namanya menjadi `RAG_FactChecking-lama` dan dijadikan private oleh
  pemilik proyek. Di sana tersimpan riwayat asli dengan hash lama, catatan push asli, dan jalannya CI GitHub
  Actions yang asli.
- **Bundle cadangan:** `riwayat_asli_2026-10-25.bundle` (tidak di-commit; disimpan lokal dan di penyimpanan
  eksternal pemilik proyek), SHA-256 `db83fad310e6e9ae0b604979f27ce3256cdee3aad09a3519cadda13b9ba7e5a5`, berisi
  176 commit dan kedua tag. Bundle dibuat sebelum commit persiapan terakhir (`7968e3e`, baris 177 di tabel);
  commit itu ada di repo arsip.

## Tag

| Tag | Objek tag lama | Objek tag baru | Commit lama | Commit baru |
| --- | --- | --- | --- | --- |
| `testset-v1` | `dc02d45135210f9ff0be4447e0acb258e2ddadc1` | `4498e8bb5cb2af32ac1a063ac4c6dd880147248e` | `028bea71d631cb40d56111aa7643ef98bd98d5d9` | `b021cdcfdd0265e47b21a6af4477c4944b9d5809` |
| `annotation-guide-v1.0` | `9e5f48a1c58d6e85823ffc1e22dea698fe2fdf45` | `cb5d9701a227a2aeb6e839e19ef0fe215d4d6a99` | `25000134ceef6979c04cdd96c64dced66b46bad7` | `979a2cf6a7a71087af1b1a9746ba806df6f963ef` |

## Catatan commit `4fdadd4` ("Create README.md")

Commit ini aslinya dibuat lewat editor web GitHub, dengan author `Zul Tiandra Rifandy
<129819015+RifandyZUl@users.noreply.github.com>`, committer `GitHub <noreply@github.com>`, dan tanda tangan
GPG dari GitHub. Penulisan ulang menyeragamkan kedua identitas itu, dan **tanda tangan GitHub-nya hilang**.
Tanda tangan itu tidak bisa dipertahankan, karena hash induk commit ini ikut berubah. Isi commit (tree) tetap sama.

## Tabel commit

Urutan dari commit pertama ke terakhir. Kolom terakhir menandai 38 commit yang hash lamanya dirujuk berkas di
repositori.

| No | Hash lama | Hash baru | Tanggal | Judul | Dirujuk dokumen |
| --- | --- | --- | --- | --- | --- |
| 1 | `1ae7a49c8340ff27821f56cae87bb4d610de6fd7` | `6d3dfc56357bfed194cf149ecda431cb6a42282f` | 2026-09-19 | Inisialisasi proyek RAG cek fakta TurnBackHoax (Versi 1) |  |
| 2 | `39c5ba2f389ea45b13ddd5d92bfc0b7f0c10f666` | `81daca892f26ac4b69abe79f3d8f32456cae17df` | 2026-09-19 | Tambah Session, retry backoff, dan cache HTML mentah pada scraper |  |
| 3 | `4e23ebcbe67d1c2277f7c3d560d6d59e45bfba18` | `123ac36a95afb07c1c3b5a03e7ab335c72ee3be6` | 2026-09-19 | Perbaiki pemilihan kontainer artikel dan saring tautan hoaks dari referensi |  |
| 4 | `4dc227839dd5bd6950a8799c1d8ac9b7851f98f6` | `fdbaea733f4009017621275ae88acb1b30065d3b` | 2026-09-19 | Validasi HTML sebelum cache dan perketat penyaringan referensi |  |
| 5 | `c7c62ed3bb202b9472d29b7756b876a8f95383c1` | `feef1012436b5b71bd97d10005c5ce8a5f717aa9` | 2026-09-19 | Kembalikan penyaringan references ke penyaringan penuh per domain |  |
| 6 | `8baa9606e082266e31f534b131aa5f8b626dd52d` | `fd75686a2ef312f3a4b0921c77998c75dca1e0e3` | 2026-09-20 | Tambah modul ingestion Versi 1: chunking, embedding bge-m3, retrieval per artikel |  |
| 7 | `febf2c1c05a2b5ba2f5e8c54f566379323490712` | `868455e19715dec151945cf453f604b909878263` | 2026-09-20 | Pindah ke venv dengan torch 2.14, muat bge-m3 dari .bin resmi, tambah uji kueri negatif |  |
| 8 | `623f300de1493175a2ae24b1dcaa7fbfc83bf30e` | `34eeeafd875b998a5fd37e2c8e80971be5a09faf` | 2026-09-21 | Tambah lapisan generasi Versi 1 dan perbaiki infrastruktur evaluasi | **ya**: `docs/audit/audit_tahap0.md` |
| 9 | `2ca03a9210e76d72d38977d379b3925fc3ce199e` | `f688c986f379c9aeaa1f7f620caa5d39d753ae0d` | 2026-09-21 | Tambah throttling proaktif, anggaran kuota harian, dan perbandingan model |  |
| 10 | `0b150213672d5aec57ddc9b0ab80c17c18da4431` | `b017341b382f6f50cd7a237bbb3b9d1a4e25ecfd` | 2026-09-21 | Catat isi galat API di log, tambah pemutus beruntun dan uji JSON Gemma |  |
| 11 | `6dc240e649407ff8f4cb825c21a11e1d457e6e7e` | `5162e7c98e104cd6519fc0c92d745b1c64f19533` | 2026-09-21 | Catat hasil live 2026-09-21 dan koreksi waktu reset di CLAUDE.md |  |
| 12 | `596784f0972a1a6ef9586987f9000a628d7e93b8` | `37df98d6fedc110a944e2e16ae9e441e5e15bd9d` | 2026-09-21 | Tetapkan Flash Lite sebagai generator Versi 1 dan rumuskan ulang H3 |  |
| 13 | `eb2bbf84cda1f25a091efc0b47010e0d19a1c751` | `d9b0761a3ce78dc06ffdbb03a66e0506aa0f2427` | 2026-09-21 | Tandai hasil yang diukur pada data terduplikasi di CLAUDE.md |  |
| 14 | `c41962195539e47defba210e1de968b054c2ad42` | `0813eaa90de53bd141f3e65e127cd2982671aa88` | 2026-09-21 | Refaktor tanpa perubahan perilaku: paths.py dan paket scraping/ |  |
| 15 | `ee447a0a57267a7785d10997dc6c3c2e8cd8fec2` | `811e427c21a63d66210e9d2757e82a54f51e54d6` | 2026-09-21 | Refaktor tanpa perubahan perilaku: paket llm/ |  |
| 16 | `58a4924c43bfdd3b9efceabadb740413a47a381f` | `70aca5efbbaf1d636cb15bed0fdf4eef4ed338b3` | 2026-09-21 | Refaktor tanpa perubahan perilaku: evaluation/ dan tests/ (pytest) |  |
| 17 | `fe4b90808ee22e7f9d4825525e00fd69cb93f501` | `3e390a50468e972355d27aeb5aa90e6c0942c517` | 2026-09-21 | Perbaiki 2 galat tipe di tests/test_gemini.py |  |
| 18 | `46394e432aee60fa3582b9a5622251ffb5faf6f0` | `58c0da83c7ab72555241713c2e2b78834b225f0f` | 2026-09-21 | Perbaiki uji tautologis: nilai harapan literal, bukan dari konstanta yang diuji |  |
| 19 | `486af27869822d24d115e388777ed923eefa9164` | `0e309e7bdb4d902fdeb4d9673a3098bcc30702ca` | 2026-09-21 | Perbaiki jalur keluaran bawaan scraper.main: dijangkar ke root proyek |  |
| 20 | `cf59ab2ca1244fdb30d99e8d9ebbd0e5f63ad975` | `f2160fa170b82371c1bac019750168b40febd8fe` | 2026-09-21 | Tambah scraping.reparse: parse ulang dari cache HTML tanpa jaringan |  |
| 21 | `b29d91cc48cba25e1d6951bbd5984a0731b071c9` | `3dac6a8a9c83cba86314fe2f05dd7dbfe1e01112` | 2026-09-21 | Perbaiki duplikasi teks Narasi/Penjelasan pada extract_sections | **ya**: `CLAUDE.md` |
| 22 | `c6c3dddb4561ba9801aed4427d481a80f0a82bc3` | `eee3f1437c3ceaf8f1a5dee12c2a423bf6e8f6f2` | 2026-09-21 | Tambah ingest --rebuild dan evaluation.index_check (indeks basi harus terdeteksi) |  |
| 23 | `301e539a937b346bfe10a8770efe8e87facc9ceb` | `da35e86a7028b56a043cfef6e45226b0e8b66d9b` | 2026-09-21 | Catat pengukuran ulang setelah perbaikan duplikasi; perbarui delapan tanda di CLAUDE.md |  |
| 24 | `f61f9df327e51e45ee6d0d23c904eb97df1f63e0` | `a7e318fc8090c93592ec593a8a14f58c780de3ae` | 2026-09-21 | Rapikan tipe dan lint tests/test_gemini.py (dan _fakes.py) |  |
| 25 | `0cdb73d66d1eff3cbe235951245ba9886c03ba69` | `7035b3c593f025523c23a89cd260cedcb29cf032` | 2026-09-21 | Tambah evaluation.repeat_eval: ulangan diagnostik keputusan generator |  |
| 26 | `9031646f2620f7767b50420be34321c2b4616552` | `28497527689a8e3bd02f18ad6a2a17ae1351256e` | 2026-09-21 | Catat hasil ulangan Flash Lite, setelan sampling, dan daftar pekerjaan sebelum portofolio |  |
| 27 | `37fcac980d3c255ace1fd6d926ace6a9cb40ee9c` | `a46e911c6568e546813d9c2a12bf74ce35211503` | 2026-09-21 | Selaraskan prompt sistem dengan pedoman "klaim sama" (definisi tertulis di dalam sistem) | **ya**: `CLAUDE.md`, `testset/v1.meta.json` |
| 28 | `25000134ceef6979c04cdd96c64dced66b46bad7` | `979a2cf6a7a71087af1b1a9746ba806df6f963ef` | 2026-09-21 | Kunci pedoman anotasi v1.0 dan pra-registrasi set uji v1 (sebelum butir dibuat) | **ya**: `CLAUDE.md`, `testset/README.md` |
| 29 | `20827c36d3225644855ac5f693f3ad19a15e8783` | `e9f6f4393a6b5063eab983b8d0fc15f12d6f0ecf` | 2026-09-21 | Catat prompt selaras pedoman, pelabelan ulang kueri 3, pra-registrasi, dan regresi di CLAUDE.md |  |
| 30 | `57db5776bd8839b0c403ece77765ac062e8ea8c2` | `6bab614cca10047b353bdff03c298bfa992f8277` | 2026-09-21 | Pisahkan dua label pada evaluasi: artikel terjangkau retrieval vs keputusan akhir |  |
| 31 | `89d6ef5556bc956fb392eb3492d13f3836db34b9` | `355a3f27f60e6a42a1b1fce7ba7671889dc760e0` | 2026-09-21 | Pra-registrasi dua label dan dua jenis kesalahan di v1.meta.json; catat kueri 2 = batas |  |
| 32 | `82493d55341aec09083afd4847d544897f89efba` | `4b3106e05222bd8197b478fd53b57e6e934e67e3` | 2026-09-21 | Tambah pengumpul kandidat set uji (arsip TurnBackHoax) dan penyaring; catat temuan kepatuhan situs |  |
| 33 | `f579d9bc7055829af791bed5952e91a00465029f` | `51ed6132e5ecbee5f3d9e9e18d60e36a1a0accbd` | 2026-09-21 | Terapkan keputusan sumber: lintas situs otomatis dilepas, confound dicatat, kelas usulan dipisah |  |
| 34 | `c2d7edfaa24762a3c5508b234b375bc86e6df6d9` | `88893dacf236798f6f36521c09abc83709573940` | 2026-09-21 | Pra-registrasi pemilihan 20 artikel target positif (benih tetap, hanya id) |  |
| 35 | `a67d472fa8778b9a32eda221ad8c03deac385abc` | `5dc10ddaa6d6e65a5548af442e97045ffd815d5c` | 2026-09-22 | Tambah pengumpul kandidat Liputan6 Cek Fakta; lepas cekfakta.com; koreksi independensi Gemma | **ya**: `testset/README.md` |
| 36 | `b6be23cd9d7bf6d0315b9b393bfc73046dc196d7` | `2b721bd8f11c2fd771194dfe305cff6d31fdaa99` | 2026-09-22 | Perbaiki ekstraktor kutipan Liputan6: pasangkan tanda kutip berurutan, bukan regex kelas karakter |  |
| 37 | `3c2bd29f8472484f149fef912a1b327833eb986b` | `ab0fdedc830f16a50aeacd4653b01c0c5d00d6d4` | 2026-09-22 | Perbaiki claim_candidate() arsip: cari setelah kata 'narasi' pertama, bukan hanya pola berkutip |  |
| 38 | `0bfad9ec1ae00cbede8ded74da39a8799704d662` | `b843f3297f926aab561c354ba9c2cbe82a6dc60e` | 2026-09-22 | Catat audit kebocoran set uji v1: ganti 3 target bocor, sampel arsip, penukaran bersyarat Liputan6 |  |
| 39 | `22eda9cf55dca2679fe8e55edc03f306c1db5584` | `7d6f2fa9f96a16d73b6fe263ea661afae97dea30` | 2026-09-22 | Catat prosedur klaim manusia: sumber Kompas/Tempo saja, verifikasi independensi pasca-klaim |  |
| 40 | `1f6db42e1441c90bc390d80593ae0047544e54b5` | `5671ca0f0c9a83f26a495675372495556bacbba4` | 2026-09-22 | Tambah metadata versi model di tingkat LLMProvider |  |
| 41 | `7d4d827c517fa28292ba7be6690323812e724238` | `918b79deeeff0e8d0560ebff5110fa63332b0218` | 2026-09-22 | Tambah candidates.gemma_generate: penghasil kandidat set uji v1 sumber Gemma |  |
| 42 | `922d4e67bf59ba285f7af603747004c7ace296c4` | `b1f91f490829bf9598489155edcfe68f9d1a7362` | 2026-09-22 | Kunci label emas tahap 1/2, keputusan 36700, dan jatah final Gemma | **ya**: `testset/README.md` |
| 43 | `7617265c2c964b4b9eccc8cdf2b39482b259c52d` | `9d2b9ac72370dcd62800b586b3b6aad3d1bd6a7d` | 2026-09-23 | Tambah slot negatif_entitas_sama; perbaiki bug kemiripan judul; jalankan generasi Gemma |  |
| 44 | `b2b03a3ccfc5b4d18c4ad4a0b94df6c3248e4c6c` | `9618e60ecea2c3257e8f1e2c11e2514a14940b95` | 2026-09-23 | Catat hasil tinjauan tahap 3 (58 kandidat Gemma): reduksi seeded, temuan PII/pedoman |  |
| 45 | `4e684722dc09f0381d4412dbe7fe1a58a5a1afdd` | `8dbdb2a726d6845233ca2c35adcb8dd64c78f747` | 2026-09-23 | Susun testset/v1.jsonl (54 butir): tiga keputusan pemilik proyek + perbaikan PII | **ya**: `testset/v1.meta.json` |
| 46 | `61cffe79b18f4d008f4ace6c314e1ddfda917dbb` | `480b5cc1a1948f7063d42fc7c5b164b2a3842729` | 2026-09-23 | Perbaiki kolom subtipe (hilang dari pra-registrasi) dan koreksi laporan pasangan minimal |  |
| 47 | `028bea71d631cb40d56111aa7643ef98bd98d5d9` | `b021cdcfdd0265e47b21a6af4477c4944b9d5809` | 2026-09-23 | Bekukan set uji v1: catat 3 catatan pemilik proyek, kunci sidik jari generator | **ya**: `testset/README.md` |
| 48 | `44e5ae6cb425baab53c6477a0ed3213f093913ac` | `e2e4922e67ee7a657c911ccae4efbd7c7d4555ae` | 2026-09-23 | Tulis evaluation.testset_eval (runner set uji v1): offline, belum dijalankan |  |
| 49 | `0122400124f7138a5637816d0efa88b07e804605` | `d7d91474f873ddba6bc011547e73553a01a497d4` | 2026-09-23 | Tambah --run ke testset_eval; turunkan sirkuit pemutus ke 2 butir beruntun |  |
| 50 | `2f54dc4c08333cebbe29a9410f783085df464ede` | `33b55c08c559c3dd53dcd307b2846fc5ccfca5e8` | 2026-09-23 | Tulis evaluation.testset_analysis: hitung metrik dari hasil mentah, offline |  |
| 51 | `b0ee4fd1c2ca2f28fd2001f55b7bb2350c283741` | `18cff5eafe088462e32a9e1d3b0de74668b71ce1` | 2026-09-23 | Hasil evaluasi set uji v1: 3 run, akurasi 48/50 non-batas, H1 dan H3 terdukung | **ya**: `testset/README.md` |
| 52 | `15bfd9849859b86bdb4f849863ba0dbfa21f550c` | `cda538c07f09561208f52268bcfdab3cbf4fcc61` | 2026-09-23 | Tutup Versi 1: batas tafsir H1, temuan untuk Versi 2, ringkasan di CLAUDE.md |  |
| 53 | `4fdadd49b1a275ef6337b56b6660569c187043d0` | `fce58f5adfa0b2a24a19af98e940e96809c7656a` | 2026-09-23 | Create README.md |  |
| 54 | `4de092e4aa9701ee9c00b8a856f05cb169a47eb1` | `402be508805b51ba382cb85bd07d4ac2c640b89c` | 2026-09-23 | Simpan dan koreksi README.md: perintah PowerShell, struktur, angka, rujukan |  |
| 55 | `329f41fd95c1445910f6117607b9b5f349ee31ae` | `f511ef83d36a2c31ee93fdf6e86f74bce9a58f3b` | 2026-09-25 | Tambah demo Streamlit pemeriksa klaim beserta uji offline |  |
| 56 | `80447e6a3096bd758fc993430dccc786e8bc645f` | `e5ee71a18bcdab82b1969688e13a75bc37b9fba6` | 2026-09-25 | Dokumentasi penutupan demo: temuan ChromaDB, temuan untuk Versi 2, status |  |
| 57 | `036189e102d2c14a6e8268dd015733e06afd8b58` | `0a9beafc65df840b6e07cbc8ffcc6bca2702536e` | 2026-09-25 | Eksperimen ablasi retrieval pada set uji v1 beku (tanpa LLM, tanpa rebuild) | **ya**: `testset/README.md` |
| 58 | `8e1799265b1648bdad96bffa28c2a36861cd7944` | `55a01c83f9d7538426208a19edb575bc0f18c8b5` | 2026-09-25 | Demo: batas masukan 1.500 karakter dan peringatan pesan panjang |  |
| 59 | `c0693936f2dc24982bed0430dcd5983e12559db3` | `129a9a5f255645fbe089cea9fe5f89468a2ab727` | 2026-09-25 | Dokumentasi: keterbatasan 512 token, peta rewriter Versi 2, koreksi Narasi |  |
| 60 | `927649df48b29fd98189bdf5524640c5367113d9` | `00e1b20a103d529f95092fa8b38628d270f2863b` | 2026-09-25 | Tahap 2: arsip indeks Versi 1 (archive/v1) dengan sidik jari isi terverifikasi | **ya**: `docs/audit/audit_tahap0.md` |
| 61 | `28dc2711c71a919496a1faf7832f7285fe6fc697` | `3dbd5f1874e3a145a3725de1cf9cd97fcb43b6ec` | 2026-09-25 | Temuan v2 §4.1: contoh gaya bahasa klarifikasi 36730 dan variasi antar-panggilan |  |
| 62 | `9b65af5ae88a5d4509bebd6c4671da15d0f81f23` | `b9aee89554b809df563e902a2f95eab349ccdd18` | 2026-09-26 | Samarkan fixture HTML uji: hapus teks artikel dan tautan akun penyebar hoaks |  |
| 63 | `e3b53e9752fc614cf48236af743361bc13324dfc` | `7d06bcba84e21baac9763978a74878501f2e2fba` | 2026-09-26 | PII: ganti nomor penipu di catatan meta, jadikan pemeriksaan PII Gemma tetap |  |
| 64 | `f5f490cfe13207726304f0897b090780073cb012` | `17779a0763ff1487cc61c394224cfa95507f10af` | 2026-09-26 | Daftar artikel arsip v1, pemulihan lewat scraping.restore, dokumentasi tahap 2 |  |
| 65 | `a7e614fb5fa1b11077c6956241877d3ee2305401` | `e0a439f0e77b1dff9b15b5fb936bd752540e09df` | 2026-09-27 | Tahap perluasan: scraping.expand (mode mundur per kelompok) dan status kelompok 1 |  |
| 66 | `d1fbf20f1957167d308202842aefc42dfe8c90de` | `d46204e711aa12dfd104dbaaddf11fd1c763187a` | 2026-09-27 | scraping.expand: mode maju (--forward) untuk artikel lebih baru dari basis |  |
| 67 | `383197f522fc862dfaed0751360d77dbb0bed05e` | `db8ccf92e2e0f8530b551a581f5e71327e5b2ec0` | 2026-09-27 | Status Terkini: kelompok 2 perluasan basis data |  |
| 68 | `385ba707fe46910ccbddefbf8e2470d1ce9be85e` | `498db8fc3c873324bf1bbbac15200c0a9426ebed` | 2026-09-27 | Aturan Wajib #7 (label dari judul), parse_title toleran kurung rusak, manifest perluasan |  |
| 69 | `cf1dce9b0672ffe17ccb954200edba0249b9cf2a` | `ca8df496cdf4f64de392df5b3119a46cdf7ab6f7` | 2026-09-27 | Buku artikel gagal + hitungan retry di expand; normalisasi baris baru; catatan celah penyegaran |  |
| 70 | `58216c1644bf69c8c7246c37e6048bf0ead2b5b6` | `bdffc3d95f21939146f077fb248e5f1e92d45f0e` | 2026-09-27 | Status Terkini: kelompok 3 perluasan basis data (scraping saja) |  |
| 71 | `176ded740ea04443dfee623f2cb6447cfbf75377` | `070cfc05151f0abe20ed911facb79478f5107d2e` | 2026-09-27 | Gabung kelompok 3 (922 artikel, ingest inkremental 750 chunk); agenda sub-chunk dan coba ulang |  |
| 72 | `3a356fccebff30b298ee4a75493c9b0757a024bb` | `3b488cd20a5bef8861ff45b4783679d65cd0988c` | 2026-09-27 | Manifest perluasan: 772 artikel (kelompok 1-3 + mode maju), pemeriksaan PII judul |  |
| 73 | `9bee0aff8ca1ae942cfb9396182a781f37ec8435` | `a21ffb5e9e9caf9629174d0737a5855218de7079` | 2026-09-27 | Ablasi retrieval pada indeks 922 vs arsip v1; keterikatan set uji v1 pada 150 artikel | **ya**: `testset/README.md` |
| 74 | `28152a0c43bb62ed8c73d141efc7faff866680ee` | `566874649299c50a66aa423c58ea98804cbc9261` | 2026-09-28 | Ambang "mungkin terkait" per indeks (dimatikan pada 922); status butir negatif pada snapshot |  |
| 75 | `db9e5566ccc4569271564d95fabe1b0aafe0a6b7` | `123ef191451a75fb661f756e0916cae1ce57c7ed` | 2026-09-28 | v1-050 terverifikasi (butir kelima); SATIRE/SATIR tampil sebagai PARODI; kelompok 4 (scraping) |  |
| 76 | `de853e7fcca3bd9786db416a4213ae6191b6dfd2` | `959653b7247e9de413b853c84bb4d5b2e7ee9b88` | 2026-09-28 | Catatan cakupan evaluasi (README + demo); rekap lima butir negatif gugur pada indeks 922 |  |
| 77 | `a9c19fcc69f514e1055f5ac1124ed9f9d6f5dac4` | `bd2f5bd823a102d0c791209129bdf65a25b1b487` | 2026-10-02 | Status terkini: kelompok 5 gagal sebagian besar (40/250), state.json sudah maju |  |
| 78 | `3882f74c71828dff60c99178fa377be00011bb41` | `abba28a4bac7fc6688b16957cf0d141d436cb50f` | 2026-10-02 | Pemutus sirkuit expand.py, status turunan failed_ids, tampilan netral label tak dikenal |  |
| 79 | `1b14801513cc9e25c29c629389c879757c2bd8d5` | `2d2820bf776e2b96efa4b173231337e9cbf70065` | 2026-10-02 | Status terkini: kelompok 5 lengkap setelah jalan ulang (250/250), 30089 masuk |  |
| 80 | `0ad0e90f25894c0baed5120752d153526ce0014d` | `373efcdb1c5501fca030dd7ef996699ed5a3a598` | 2026-10-02 | parse_title: buang karakter tak terlihat dari judul, terima penutup "}" untuk label dikenal |  |
| 81 | `00c4fb5f94e403052f321157fd46b3dd159e04f0` | `def3f77576e9444b6198148b9260388651eee8de` | 2026-10-02 | Status terkini: kelompok 6 berhenti di artikel 29437 (URL referensi cacat di sumber) | **ya**: `CLAUDE.md` |
| 82 | `b101bd2bc16a8e62976b298bc9608dd7ad04e1fe` | `7035c38e025f21400f73ddac077fa6ddaf71e6f1` | 2026-10-03 | URL referensi tidak sah disaring; exception per artikel jadi kegagalan berjenis galat_kode |  |
| 83 | `89ad36a70feee08dcca1269a6ceb98c92ed76d1e` | `e66d63849ed82c6f73f5819a300376567c49abec` | 2026-10-03 | Status terkini: kelompok 6 lengkap (110/110, 30 Sep-23 Okt 2025); temuan URL "Sumber:" | **ya**: `CLAUDE.md` |
| 84 | `11742a73f3c1e7585b91d17020193374b72d79c4` | `317ec49baf148c8324fef797ed4e313ad91eac90` | 2026-10-03 | Aturan Wajib #1: pemendek URL disaring; rujukan disaring ulang di lapisan tampilan | **ya**: `CLAUDE.md` |
| 85 | `ed1214e0c8f0e9c90cf11bd77bc74d86d45396e0` | `458e90c1c61470403463d763d36b596aecdf7c9f` | 2026-10-03 | Aturan Wajib #1: baris "Sumber:" masuk claim_sources; lima domain arsip disaring |  |
| 86 | `02425e1fa97e520466f26f829ccdd96a8ec83e2f` | `407155333c44069967828063b641f053dc900cf2` | 2026-10-03 | ingest: --update-metadata (pembaruan metadata terarah tanpa embedding ulang) + uji |  |
| 87 | `aedcdc534ecb0d92ff3aab4b6bff8c4582955c38` | `2b6c3a4e89149cef4aea50ac64b78a8681a1043a` | 2026-10-03 | Catatan: aturan "Sumber:", pembaruan metadata 922 artikel, penggabungan kelompok 4-6 |  |
| 88 | `c8b7afdcabba843c2fe1fe6a35000deb7fd7b841` | `11f060a38e0cc597a86b3858ff3ddbd7dd1c2e8a` | 2026-10-03 | Manifest perluasan: kelompok 4-6 (1.382 artikel, pemeriksaan PII judul); keterbatasan daftar tepercaya, .go.id, dan pemendek URL |  |
| 89 | `d0e1e74c7b848ba6e52235ef611513e524976050` | `e0d9f8744e22ddec27f4ccabd0fcd4aeef9c99b3` | 2026-10-03 | Perbandingan retrieval set uji v1: arsip 150 vs indeks final 1.532 artikel (tanpa LLM) | **ya**: `testset/README.md` |
| 90 | `cae7979acd04111261101ef03239e9b8be947ea9` | `77193dc691c8367d9c23d1ac9892df0dd1d833be` | 2026-10-03 | Ambang 'Mungkin terkait' tetap dimatikan pada indeks 1.532; catatan cakupan demo diperbarui |  |
| 91 | `b597c990652ff5757fa34d5bb83740de0f315060` | `51376c822d6f5440a8489e283643bfd9d7bd4abe` | 2026-10-03 | README dan Status Terkini: indeks produksi 1.532 artikel (30 Sep 2025-27 Sep 2026), belum dievaluasi dengan generator |  |
| 92 | `145d9f1c01a4bb7866e5d578b98617eebc6d7769` | `9534660000c431e289034204eb2bd70be77be293` | 2026-10-03 | Uji batas domain daftar tepercaya; catatan cakupan demo memisahkan pencarian dari akurasi jawaban |  |
| 93 | `cdb303b852c923e9cc86e2cc949d2b7b0cc2a1b1` | `82ad534a68e1450c8005fbb254a35d096d7a3804` | 2026-10-03 | v1.meta.json: v1-029 butir negatif keenam yang berubah status (indeks 1.532; 30089 peringkat 1) |  |
| 94 | `c84e44ac330389bfbf333e3f9e65ae1be3186e06` | `9fa2332c218655bbd433392532927152360e41fd` | 2026-10-03 | Set pengembangan diukur ulang pada indeks 1.532 (retrieval saja); dasar keputusan ambang diperbarui | **ya**: `testset/README.md` |
| 95 | `acc75e606b4e3fb36d6e924efe7acc547edc2884` | `0a8db3fa31014a75c91813b03f79d11ca2af7edd` | 2026-10-03 | Ablasi retrieval lengkap pada indeks 1.532; Status Terkini: tahap perluasan selesai | **ya**: `testset/README.md` |
| 96 | `f801a7ef2d42e3560995783c14053e358450fd07` | `bf5305b8221abecb53a5e29ef719afb78e9f668d` | 2026-10-03 | v1-046 tetap negatif (keputusan pemilik proyek); temuan HNSW dan artikel ber-chunk Kesimpulan saja |  |
| 97 | `f3c0d628717d9a9bed92464035090be414d17ab6` | `6af6a72201f2e9ef4c1e320d4e20515aacdde1f8` | 2026-10-03 | docs: rancangan pembaruan berkala (usulan 2026-10-03, salinan persis) |  |
| 98 | `61fdb8c41727d04904225dd30f47fdc34785e234` | `4bd76bee425e340f201e288c62643a71c8133448` | 2026-10-03 | docs: rancangan pembaruan berkala versi yang disetujui (ingest manual + enam tambahan) |  |
| 99 | `c6cb45b62648c73ab57cbb4b4bf9aca4c0251614` | `fb12066e8fafe5bec78d5890e98c70f78ff4eed5` | 2026-10-03 | ef_search indeks produksi 100 -> 2000; alat evaluation.retriever_exactness; arsip tetap 100 | **ya**: `testset/README.md` |
| 100 | `1024172e6549b440f651c50d3c95d34666be8a64` | `92321b5392002576f4be1caa2bfbfe84509a918c` | 2026-10-03 | expand: jalan dengan kegagalan ditahan (batas tidak maju); --retry-failed dari failed_ids.json |  |
| 101 | `48feee108f4db3dacf1174026ee35f07a72f0e73` | `91fcbf6d608279d8e8457b6a3e9a69c6e4ab1abd` | 2026-10-03 | expand: kegagalan jaringan tidak dihitung ke batas tiga percobaan antar-jalan |  |
| 102 | `27e381091629cbc20c12459e650b79df1e503774` | `e5276182814cbf35bfb0601b2033d818c12699ff` | 2026-10-03 | Demo: catatan cakupan memuat tanggal dan ukuran indeks saat diukur; jumlah artikel dibaca dari indeks |  |
| 103 | `3fc1868664df4087f24895d976d5f002480fe0f9` | `3103ed7dc3311f04139d3ecf6bc93eae5445ecc0` | 2026-10-03 | scraping.source: lapisan pengambilan data yang bisa diganti (bawaan HTML; API Yudistira belum dibangun) |  |
| 104 | `6084f341f3762208b4ee47b8a3295afbd66d6a51` | `c73e1337905efd59c085b7bf20281d9ebb2c0a62` | 2026-10-03 | scraping.scheduled: pembungkus pembaruan berkala (scraping saja), penanda, notifikasi Windows |  |
| 105 | `ee76a54a6d046ca10f3838ee83f310226541439e` | `d7ab44759d954931dd3c1bcc2d049bdc5d3844a6` | 2026-10-03 | Pembaruan berkala: kualitas seluruh antrean, peluncur .cmd, catatan percobaan manual |  |
| 106 | `e65dce4e385cbccaee600931fb2f585dd9ad5637` | `3670cf21aa98073c0a949313714fa41d58007b26` | 2026-10-03 | Status Terkini: koreksi jumlah cadangan (empat) |  |
| 107 | `cce7ca8432fd4bd23cb769693d5be2431fe47728` | `ae9b9847896b9e16f4ea34b79670bd78fe47fd70` | 2026-10-03 | Label BELUM TERBUKTI: gaya ungu sendiri (slot violet di config.toml), uji kontras AA |  |
| 108 | `e3a84b40f8aa73ade9f5f8987d66f215e71cae12` | `47dc4be506ac291609b71d5b777e26c5c01c0b39` | 2026-10-03 | Catatan: dua cadangan lama dihapus, BELUM TERBUKTI diputuskan, penanda = pemberitahuan utama |  |
| 109 | `273b278fb23bda9d190283c2d09b988e96a777ca` | `aef08a607f35653384c50200d14651cd63e66810` | 2026-10-03 | Peluncur pembaruan berkala tanpa jendela (pythonw); notifikasi tanpa jendela konsol |  |
| 110 | `17597a6e594461441b38abe8f11b57c70b250286` | `f21f67fad4bb696c14b364b71c0dc3bbcf572f33` | 2026-10-03 | Catatan: tugas pembaruan berkala terdaftar di Task Scheduler (harian 13.00) dan dipicu sekali |  |
| 111 | `7c5bd2b80d83e3b3e28b56fbbdf4898b9a420ba8` | `d40302ecaa88d946a19545fc4702b81b0436bdda` | 2026-10-03 | docs: rancangan Versi 2 (tanpa kode); koreksi pemetaan temuan | **ya**: `testset/README.md` |
| 112 | `66004c4c1945c0044182b2537f7db64704906707` | `745c22d6d98f82efaa791a82a04e80a2f4ff4496` | 2026-10-03 | Rancangan Versi 2: keputusan pemilik proyek, cakupan dipersempit; README; ukuran sampel tersimpan | **ya**: `testset/README.md` |
| 113 | `5d44e248ae417767bd1ebf1f56db9d82bf9132cf` | `c6da84b71d6c14bc19d949f1bbaee88ca942d667` | 2026-10-03 | Rancangan v2 bagian 10: metode pengukuran pesan asli yang disetujui; alat pengambilan sampel acak |  |
| 114 | `2ce166511d9b9a943fd3aa28d5e6bae080b8d872` | `a75aae5c032030d339e436516afa6c23d1e3d5e5` | 2026-10-03 | Pengukuran pesan berantai asli: 0 dari 200 pesan melebihi 512 token | **ya**: `testset/README.md` |
| 115 | `d11939960d9011539466aa73bcbc8b3529f1d8e9` | `277873a9104927308ea0aa207d99607425648336` | 2026-10-03 | Status: pengukuran celah 'belum ditemukan' (Liputan6 vs basis data) menunggu konfirmasi pemilik proyek |  |
| 116 | `f9ecd0f8fe7e7f2f5433d26a2c9412ce2baece94` | `69e920ea8e8627ae799eaef75199784445a74849` | 2026-10-04 | Rancangan v2 bagian 11: ambang keputusan celah 'belum ditemukan' dicatat sebelum data dilihat | **ya**: `CLAUDE.md` |
| 117 | `eba32f9cc89066322f414c4c5f250df3cb04fab7` | `d5800baf7701002b4a9ccbeeee0720e09a4ace2f` | 2026-10-04 | candidates.gap_review: berkas konfirmasi manusia untuk celah 'belum ditemukan' (50 butir) |  |
| 118 | `a1459a2d204ef00f2467e84fa5b040f024747020` | `c2f9a9cdee182c35534a59bea144f775968956fb` | 2026-10-04 | Rancangan v2 bagian 11.2: tafsiran 'ambigu' dan perluasan ke 100 butir dikonfirmasi pemilik proyek sebelum berkas dibuka | **ya**: `CLAUDE.md` |
| 119 | `82f3c6f2f241f6b2e505675dd89ed07f99dcd5e1` | `0b2c1ee6a3e7b9bbd6b2cc7d73d1489dc6e97c5f` | 2026-10-04 | candidates.gap_workbook: berkas konfirmasi .xlsx (openpyxl 3.1.5) dan pembacaan keputusan tanpa menebak |  |
| 120 | `9b17b354e603956eb88d8054a69ed294cb53f3f9` | `7fae7d7b6998e4131d30268a35fbd517ca062f70` | 2026-10-08 | candidates.gap_result: hasil 50 butir celah 'belum ditemukan' (29/50, ambigu menurut 11.2) dan sensitivitas |  |
| 121 | `c347e2062b83fb031146b7d5e375930e4cab9672` | `5eed721d4d1ecdd58a22fe4d77e362a3450fbd0d` | 2026-10-09 | Rancangan v2 bagian 11.6: aturan pelabelan A/B, aturan berhenti, dan pelaporan dikunci sebelum berkas 49 butir dibuat | **ya**: `CLAUDE.md`, `docs/rancangan/rancangan_v2.md` |
| 122 | `d1298e330d20ebe80abc8941bae7569cc2c2066f` | `6733463fad1793a14fdebe9d3681545ef08a1c42` | 2026-10-09 | candidates.gap_blocks: berkas konfirmasi 49 butir (blok per butir, Narasi utuh, Rekap terkunci) dan pembacanya; isolasi ChromaDB antar-uji |  |
| 123 | `6b5a4aa198015b072f2261e0a9191ee639661242` | `0a40a62a1c860f55d1c010850e87c0e488b66f03` | 2026-10-09 | Status: koreksi jumlah jalan uji pada catatan penyelidikan test_index_check (26, bukan 28) |  |
| 124 | `d6add92166809dccf831129f368dfb0626968d00` | `dc6cca15b29c4fb815f5d34d8a24a08a75f448cc` | 2026-10-17 | Rancangan v2 bagian 11.8: hasil 99 butir (53/99, ambigu -> ambang tidak terpenuhi, sampling berhenti) | **ya**: `docs/rancangan/rancangan_v2.md` |
| 125 | `cbb24b16367ae34113024c4c3373511b0d329d2a` | `d0b9e23446329462cdaed378d86f308bca74b830` | 2026-10-17 | Rancangan v2 bagian 11.9-11.10: kunci 49 butir dibuka setelah hasil di-commit, dan implikasinya |  |
| 126 | `e7504fcd0e8363747135a56acaeb92c5edafb8af` | `adfcbf367808a09526210daff5c30624681ee6d7` | 2026-10-17 | candidates.trace_audit: audit jejak identik 99 butir (domain tautan hoaks, rangkaian 8 kata), parameter dikunci sebelum dijalankan | **ya**: `CLAUDE.md`, `docs/rancangan/rancangan_evaluasi_eksternal.md` |
| 127 | `972658bdabf17412cfca59e51e7c8d87c1a750d1` | `b6cc85558ffa8d416a99b17ab02aad5aaed2268d` | 2026-10-17 | Rancangan evaluasi eksternal 99 butir Liputan6 pada indeks 1.532 (usulan, belum dijalankan); perapian bagian 11 dan README |  |
| 128 | `b9484e9bedcfa61b4df3b6f848d8c3734caa97b0` | `8e81f7201c723789c7facc1f68619bd3a49ed100` | 2026-10-17 | Evaluasi eksternal: keputusan pemilik proyek dicatat; alat evaluasi tersegel dan pemilih sesi buta |  |
| 129 | `fa7464cbd79964eb09b117358e4b738dc1b00488` | `05fda901d0992b6c86c5e9dc69757c5dc6a633e4` | 2026-10-17 | Evaluasi eksternal: pemilihan sesi buta (benih 20261027) dan pembekuan 91 butir, sebelum panggilan LLM pertama | **ya**: `CLAUDE.md`, `docs/adr/0002-berkas-terkunci.md`, `docs/audit/audit_tahap0.md`, `docs/rancangan/rancangan_evaluasi_eksternal.md`, `src/labeling/sessions/blind_workbook.py`, `tests/core/test_testset_locks.py`, `testset/README.md` |
| 130 | `c43005d825d9c673239e90c8b9ddcff835e0cc32` | `8da837230b7111bbc48157f2ad3e645846806cdc` | 2026-10-17 | Status: evaluasi eksternal hari 1 selesai (hasil tersegel) |  |
| 131 | `34a754f60475c12318b09995b4fe41f3ba2bdf3d` | `dbc6da4fc2d333e892bb4f7beccfc04796078347` | 2026-10-17 | Evaluasi eksternal: rekonsiliasi buku besar hari 1 (152 = 98 + 54 percobaan; selisih 6 = percobaan ulang koneksi) |  |
| 132 | `cde7ce7b07aee7556b9bb8b0dae1ea88bb1aed94` | `62b8a7d2679b49c9e6d9fdcf51bb141a980c0b6b` | 2026-10-19 | Buku besar kuota: catat asal tiap penambahan (waktu UTC, proses, pid, nomor percobaan) ke quota_ledger_events.jsonl | **ya**: `CLAUDE.md`, `docs/rancangan/rancangan_evaluasi_eksternal.md` |
| 133 | `3004c5c729a3666f9da19d1d6d7ac021918e981b` | `3fd0693f8c8f9b1dd7e1428e4a86cbe5665701cc` | 2026-10-19 | Status evaluasi eksternal: run 1-2 lengkap, run 3 terhenti (proses dihentikan Claude Code karena memori rendah) |  |
| 134 | `cd44b53ed5a72e5c19891404531973aa53021922` | `9b8352ddca350bb8adf9b3207c16e5b9513181d0` | 2026-10-19 | Penyimpangan rancangan: jeda uji ulang buta 2 minggu -> 7 hari (berkas sesi buta 20 Okt, bukan 27 Okt) |  |
| 135 | `aad53134a4099f15dfbbf5268c212dac5e4ade96` | `b3e255bdea870786e1be231b001ebd61435db0c4` | 2026-10-19 | Status evaluasi eksternal: run 3 selesai di luar Claude Code; ketiga run lengkap kedua set |  |
| 136 | `9868b17648882b19e83790a35eb1ec9486878df4` | `2005f1f73215b68a13e881b25e430d0fb1f658c0` | 2026-10-20 | Sesi buta gabungan: berkas 37 butir dibuat (sebelum diisi), hash templat/kunci/sidik jari dicatat di 7.2 | **ya**: `docs/rancangan/rancangan_evaluasi_eksternal.md` |
| 137 | `e919a7eef5969cdd7ce41c360eaa892a5d229b35` | `c6296afa0ef44ad590f28fe3d72168f409a28dd7` | 2026-10-20 | Sesi buta: catat berkas terisi pertama yang tertimpa (7.2); --read mengarsipkan sebelum validasi | **ya**: `docs/rancangan/rancangan_evaluasi_eksternal.md` |
| 138 | `bf8265720a675b13516370310a3c650c0001c00e` | `17881b826fde7206ad0d0409f0c92d28a27e5c36` | 2026-10-20 | Keandalan label dan label final evaluasi eksternal dikunci SEBELUM segel dibuka (7.7) | **ya**: `CLAUDE.md`, `docs/rancangan/rancangan_evaluasi_eksternal.md` |
| 139 | `a56cac4766ce53ab94482f05ed982eaa40024a47` | `bacad69329c787a0cfdba73d1cfbb064a35f8e36` | 2026-10-20 | Evaluasi eksternal: segel dibuka, hasil dan adjudikasi buta disiapkan (rancangan 7.8, 11) | **ya**: `testset/README.md` |
| 140 | `1e2b31b447740a4c40d3adbdce248d0d27ea01ca` | `26c37ecc283e3ae619254ff6bdafea593346fbfe` | 2026-10-21 | Rancangan 7.7/7.8: dasar ambang kappa = 7.4 (30 butir); aturan pemakaian adjudikasi ditetapkan sebelum diisi |  |
| 141 | `04cae4a4c731e775f0256938928ae4dd84abed09` | `98da03940514257203107959132abe377bfea57f` | 2026-10-21 | Verifikasi 3 negatif testset-v1 disiapkan (11.8), peringatan pencocokan di demo, draf README Evaluasi |  |
| 142 | `ddcbf5c3f9e4aff1de885503bb107f03b5909c7e` | `b8694b6a2278420db3fb8c5f4b79f49c45bbc9de` | 2026-10-21 | Adjudikasi buta dan verifikasi testset-v1 dibaca: sensitivitas 7.8/11.8, draf README lengkap | **ya**: `testset/README.md` |
| 143 | `ca602296cea8aef628cb557d483699f3d5144e5e` | `d2cda5025387c4ed95ca692f18721e7623b6497a` | 2026-10-21 | README: Hasil Evaluasi diganti (baseline Versi 1 + evaluasi eksternal 1.532), status, Rencana Versi 2, Keterbatasan |  |
| 144 | `a704d5b4a92970e24ee509e3d5df4b7a7a79752c` | `cb58fcbfb3ddc0bd10a849cfe05846cf36e1d4ab` | 2026-10-21 | README: ringkasan pembaca cepat, asal-usul label, catatan sidik jari indeks, rumusan rentang adjudikasi | **ya**: `docs/audit/audit_tahap0.md` |
| 145 | `4b7fb96874831c9a5a0c7f6bac761492c3638957` | `966f5730d0a70f7b4ce73ec02190c9fcbf3b4dcf` | 2026-10-22 | Tahap 0: audit arsitektur, kinerja, versi Python, rancangan Docker/CI, risiko keamanan |  |
| 146 | `6b5aab60b430d09a7cc5d9c9bab46c21148fe1f4` | `4b8b7abf4bcfd3ba76b9a4d25aa916394654617d` | 2026-10-22 | Tahap 0 lanjutan: koreksi spesifikasi, verifikasi rujukan/hash/revisi model, CVE terverifikasi, logo, bagian C |  |
| 147 | `ecf3b010483b43186c559db5643392fc30611996` | `c01b1923c53e7da396d3ed903874f68ec65dbd57` | 2026-10-22 | Tahap 1 (1/n): kunci buku besar antar-utas dan antar-proses, kunci throttle, uji kunci retriever/chunker, uji evaluasi tanpa data/, ruff bersih |  |
| 148 | `3a4fe4c977578df22e34158fd9bb8f74f353a1be` | `39a18cf6972b794b764ac261a77c2d0ad32dca09` | 2026-10-23 | Tahap 1: tampilan baru (beranda, hasil, Tentang), lapisan layanan/sumber daya/setelan, pemanasan, batas laju, escape, serialisasi pemeriksaan |  |
| 149 | `d47950da2d36f4e09e601639b9da55c671199886` | `c93956a3a3c6b56ddba3449b702ebfbb2f51dfe6` | 2026-10-23 | Tahap 1 Bagian A: contoh 2 diganti (35133), contoh konsisten 3/3, judul label seragam, teks waktu proses, artikel terbaru, kotak cek rapat, antrean 150 dtk, ingest offline |  |
| 150 | `29514c08c748535f80a2fa110ec0cecd40135a1b` | `d9a5f425430241a587d854d554cd7d839eae8958` | 2026-10-23 | Tangkapan layar diambil ulang dari kode d47950d; skrip memuat bobot font IBM Plex secara eksplisit || **ya** (dulu): `docs/audit/rencana_tahap1b.md`, dihapus 2026-10-25 |
| 151 | `06e89c0aa4076bf8afadc5374f5a12a9a7540439` | `15bddc7af35170498e5bb086c6a284e3c3185aeb` | 2026-10-23 | Rencana Tahap 1b (belum ada pemindahan) |  |
| 152 | `b3721dff3928adb754f89af105f33005113e67ac` | `279a785bc42f2b5d561342f1d1f9703158dc832e` | 2026-10-24 | .gitattributes: LF untuk teks, CRLF untuk *.cmd dan data beku testset/, biner untuk gambar |  |
| 153 | `fba5604f7cb4677296a7993f4003b51fae4aa474` | `ed5c3c7926ee7a1bd710944533d8d89fb069fa9e` | 2026-10-24 | Tahap 1b: perapian struktur dengan git mv (webapp/, labeling/, tests/<kelompok>/, docs/<kelompok>/), hf_env, README per folder, LICENSE MIT |  |
| 154 | `9015f76f94502581c6fc1166772cdbf82b576ad8` | `51764a5d323d38c17fe10c8bd470ed56ad714412` | 2026-10-24 | CLAUDE.md: Tahap 1b digabung; skrip pembaruan berkala baru diuji --help, bukti sebenarnya jalan terjadwal berikutnya |  |
| 155 | `393e5c012dc9f8a83b6d0aee68ba6d02e78366df` | `250a9e913e35413f19e23c1c73539fd70750b30a` | 2026-10-24 | Tahap 2b: pyproject.toml (pip install -e .), tanpa PYTHONPATH=src |  |
| 156 | `d0a078bb10dec10b1dd34ba1c1b7c22ffbb41092` | `4887acb4108064b03c58bcff47012105e416fecf` | 2026-10-24 | Tahap 2c: requests 2.31.0 -> 2.34.2 (perbaikan keamanan) |  |
| 157 | `19eb89c8b843cb560c81ae1d811431cae7f35cd7` | `9479a07f6a9cf585722f7f5bfc9ce9f00565952f` | 2026-10-24 | Tahap 2f: CI GitHub Actions (Ubuntu 24.04, Python 3.13) |  |
| 158 | `ccd5e09559597820ef8992f589d8c8b07a9c206a` | `f8692bbbccba288d974dbe8a9fad8544f430f741` | 2026-10-24 | Tahap 2d/e (sebagian): Dockerfile, compose, peluncur webapp.serve, alat embedding_proof |  |
| 159 | `6df015edf007845ce54d25f537bd092dfd4a3a80` | `54953eac0d608e6e6c81fe25683ee79cf8152b75` | 2026-10-24 | Tahap 2 langkah 2: rancangan Docker diperbaiki sebelum build |  |
| 160 | `bfb38a0e0e9054822fdfa93465c7f0f4d3b5e049` | `4d3467757edc86cd76dfef54062e7700632ccbce` | 2026-10-24 | Tahap 2 langkah 3, 4, 7: Docker dibangun dan diukur, pembuktian embedding di container, ADR |  |
| 161 | `b1a1957c1aa53afff756e1704864d4c84e8a211d` | `0c1a23018c50630bbe628d769c63d95489f8eb36` | 2026-10-24 | CI: job docker-build (membangun image saja, tanpa menjalankan container dan tanpa model) |  |
| 162 | `a87ae6a81a96bb7602a44b57914ba0fa6e3d302a` | `57e6fd6a3964b1d938e2c4185b62b5f0d09004b8` | 2026-10-24 | Docs: peran Docker dan kebutuhan memori di README dan ADR 0005 |  |
| 163 | `1259b9f6dbafeb3b648f9abbf455e452c3c1e6bb` | `d900ff29e12227ffa1adc8f6688d83287960db49` | 2026-10-24 | Tahap 2 penutup: jadwal tanpa syarat jaringan dicatat; compose init + stop_grace_period |  |
| 164 | `d38bbb3bd4f383472b7033f3e9657423e7876c43` | `0e55662fa46b8b3dd47b756754b5cbc7efe93a0e` | 2026-10-24 | Ingest antrean: skrip penggabungan teruji dan urutan perintah di README (BELUM dijalankan) |  |
| 165 | `de4c4adc58dc35d8133b0a9ba7006087a7ebaf92` | `03c921f186496ac2d1c8f27096a6c13dcb59b6b8` | 2026-10-24 | README "Ingest antrean": cadangan tidak bisa bersarang, tanggal WIB, cek salinan container |  |
| 166 | `cdae5ce85744fd3e3d4e0779e5e38cf8214df2c5` | `ebbe1c860bb1c1a3f84696c1abf580ca7e03290d` | 2026-10-24 | gabung_antrean: folder cadangan diberikan pemanggil (sama dengan langkah cadangan indeks) |  |
| 167 | `2a4765ddaa0c6ffdb607313fcb218abb5a7490d0` | `46453719225a2b7381dfdf2b73bab5015a3ce87a` | 2026-10-24 | README "Ingest antrean": bagian Pemulihan (diuji di folder sementara) |  |
| 168 | `ae22081cf13afad10d924319ccbd87818bf526cb` | `f7e89bc5acbf141756f9f74194eb045ace8924a8` | 2026-10-24 | CLAUDE.md: rencana ingest antrean 2026-10-25 setelah jalan 13.00; log riwayat Task Scheduler aktif |  |
| 169 | `74d4be2e5e360cf12795feae41a8ad4efc36def3` | `abb7d02a1ec6b0e67497aa54eade9b2ca488f07a` | 2026-10-25 | Pasca-ingest 2026-10-25: indeks demo 1.611 artikel terverifikasi, manifest, tangkapan layar, perekaman |  |
| 170 | `5715e15f07c1bed8d00018070db961e9b250da86` | `49e70b3a4e86e2201f7773c7ab667aa2ba15b528` | 2026-10-25 | index_check: sampel embedding ulang selalu mencakup chunk terakhir; catatan cadangan indeks evaluasi |  |
| 171 | `195b1610ad1108e43c9280655fb7e5342cf03aa4` | `3a10a6745900609ffa64d0c522edfd8ea472797c` | 2026-10-25 | README akhir: layar pertama untuk perekrut; detail operasional ke docs/operasional.md |  |
| 172 | `4d5e5356a8f2e8ebc234ac3926119fd11b99d0ee` | `a5028e245d575027ce89150627679403951c704d` | 2026-10-25 | README: bahasa sederhana, potongan tangkapan layar, istilah "gugur", .env aman, angka rujukan tertelusur |  |
| 173 | `d53c719089ba336c600138a424bf56665dd22b7a` | `7a66523f1fb2646c2bfc66992b6e004b3500e4b3` | 2026-10-25 | reference_gaps: tulis keluaran dengan LF (bukan CRLF Windows) | **ya**: `CLAUDE.md` |
| 174 | `09336a9cba7813437270284e03b58acaf4a0a559` | `c42d29f22cd885c8d4907cbf247b37941b6379bb` | 2026-10-25 | Email git benar dicatat; "16 dari 150" hanya di catatan sejarah Versi 1; kuota Gemini di skrip tangkapan layar |  |
| 175 | `87020e2c33148771376b0374461b0b6d1bb68f39` | `448eaf2e9d84b9a7cdfc0c6c5da9c259f122e8eb` | 2026-10-25 | Gabung readme-akhir: README dokumentasi portofolio, docs/operasional.md, ringkasan portofolio, angka rujukan tertelusur | **ya**: `CLAUDE.md` |
| 176 | `4c29da8a37a7d9b1c340a785582c7ecc4da0fc4a` | `e65c3c7ff17a55d67c8000fa1ee8948e0dacb983` | 2026-10-25 | CLAUDE.md: README akhir selesai (87020e2), proyek siap ditampilkan; daftar pekerjaan pasca-tenggat; cek jalan terjadwal 26 Okt oleh pemilik proyek |  |
| 177 | `7968e3e4461ecf550cf2f906553e4119a0a645a8` | `1b083a17074b4b3bb0b1b91b449f61b7ee9fc387` | 2026-10-25 | Persiapan penulisan ulang riwayat: aturan tanpa atribusi, pembersihan berkas |  |
