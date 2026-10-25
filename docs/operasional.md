# Operasional

Detail menjalankan dan merawat sistem yang dipindah dari [README](../README.md) agar README tetap ringkas.
Isinya sama dengan bagian README sebelumnya (dipindah 2026-10-25), ditambah ringkasan pembaruan berkala.
Semua perintah dijalankan dari root repositori di venv lokal Windows, kecuali bagian Docker.

- [Pembaruan berkala](#pembaruan-berkala)
- [Ingest antrean (pembaruan berkala)](#ingest-antrean-pembaruan-berkala), termasuk pemulihan dan perekaman
- [Mode offline Hugging Face](#mode-offline-hugging-face)
- [Menjalankan demo](#menjalankan-demo)
- [Arsip indeks Versi 1](#arsip-indeks-versi-1)
- [Docker](#docker)

## Pembaruan berkala

Tugas Task Scheduler "RAG_FactChecking - pembaruan berkala" berjalan setiap hari pukul 13.00 (hanya saat
pengguna login, tanpa jendela, lewat `.venv\Scripts\pythonw.exe scripts\pembaruan_berkala.pyw`). Jadwal yang
terlewat dijalankan sekali saat laptop menyala, hanya satu instans boleh berjalan, dan batas waktunya satu
jam. Tugas ini **hanya mengambil artikel baru ke antrean** (`data/expansion/forward_*.json`); penggabungan
dan ingest selalu manual (bagian berikut). Rancangan dan riwayat keputusannya:
[`rancangan/rancangan_pembaruan_berkala.md`](rancangan/rancangan_pembaruan_berkala.md).

Setiap jalan menulis `data/expansion/pembaruan_status.json`, menambah satu baris ke
`data/expansion/pembaruan_riwayat.jsonl`, dan menyimpan log di `data/expansion/logs/`. Bila jalannya tidak
bersih, berkas penanda `PERHATIAN_PEMBARUAN.txt` muncul di root proyek (dihapus otomatis pada jalan bersih
berikutnya) dan notifikasi Windows dikirim. Kode keluar: 0 bersih, 3 ditahan (kegagalan sistematis),
4 jaringan putus, 5 ditahan (akan dicoba lagi), 6 ada yang perlu ditinjau, 7 batas mode maju tidak
ditemukan, 8 galat tak terduga, 9 jalan lain sedang berlangsung.

Menjalankan ulang secara manual dengan setelan yang sama, lalu memeriksa hasilnya:

```powershell
Start-ScheduledTask -TaskName "RAG_FactChecking - pembaruan berkala"
Get-ScheduledTaskInfo -TaskName "RAG_FactChecking - pembaruan berkala" | Select-Object LastRunTime, LastTaskResult
Get-Content data\expansion\pembaruan_status.json
```

Perluasan ke belakang (artikel lebih tua dari yang dimiliki) memakai `python -m scraping.expand --batch-size N`
dan juga hanya menulis ke `data/expansion/`.

## Ingest antrean (pembaruan berkala)

Pembaruan berkala hanya mengambil artikel baru ke **antrean** (`data/expansion/forward_*.json`); penggabungan
ke `articles.json` dan ingest selalu dijalankan **manual oleh pemilik proyek**, di venv Windows. Jangan
menjalankannya bersamaan dengan demo atau evaluasi, dan hindari jam jalan terjadwal (13.00).

```powershell
# 0. Hentikan demo (lokal dan container) lalu laporan antrean, tanpa menulis apa pun
docker compose stop demo
.\.venv\Scripts\python.exe scripts\gabung_antrean.py

# 1. Cadangan indeks (articles.json dicadangkan otomatis oleh langkah 2). Tanggal WIB, sama dengan nama
#    folder yang dipakai gabung_antrean.py. Menolak bila cadangan sudah ada: Copy-Item ke folder yang
#    sudah ada akan menaruh salinan baru DI DALAMNYA (chroma\chroma).
$tgl = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'SE Asia Standard Time').ToString('yyyy-MM-dd')
if (Test-Path "data\backups\pre_antrean_$tgl") { throw "cadangan pre_antrean_$tgl sudah ada; jangan ditimpa" }
Copy-Item -Recurse data\chroma "data\backups\pre_antrean_$tgl\chroma"

# 2. Gabungkan antrean di akhir articles.json, cadangan articles.json ke folder $tgl yang SAMA dengan langkah 1
#    (menolak bila kualitas antrean menahan penggabungan atau cadangan indeks belum ada di folder itu)
.\.venv\Scripts\python.exe scripts\gabung_antrean.py --tulis --folder-cadangan "data\backups\pre_antrean_$tgl"

# 3. Parse ulang seluruh articles.json dari cache HTML (tanpa jaringan; parser yang berlaku sekarang)
.\.venv\Scripts\python.exe -m scraping.reparse
#    periksa: artikel lama harus identik dan berurutan sama (harus mencetak "True")
.\.venv\Scripts\python.exe -c "import json; a=json.load(open('data/backups/pre_antrean_$tgl/articles.json',encoding='utf-8')); b=json.load(open('data/articles.json',encoding='utf-8')); print(len(a), len(b), a==b[:len(a)])"

# 4. Ingest INKREMENTAL (bukan --rebuild); HF_HUB_OFFLINE=1 disetel prepare_hf_env() di awal ingest
.\.venv\Scripts\python.exe src\ingest.py

# 5. Pemeriksaan wajib setelah indeks bertambah
.\.venv\Scripts\python.exe -m evaluation.index_check            # kode 0 = indeks segar
.\.venv\Scripts\python.exe -m evaluation.retriever_exactness   # kode 0 = HNSW = eksak

# 6. Perbarui salinan indeks container (lihat "Docker"); container harus berhenti lebih dulu
Remove-Item -Recurse -Force data\container\chroma
if (Test-Path data\container\chroma) { throw "salinan lama belum terhapus; hentikan container lalu ulangi" }
Copy-Item -Recurse data\chroma data\container\chroma
#    periksa: harus mencetak "salinan = produksi: True"
$h = { param($d) Get-ChildItem $d -Recurse -File | Sort-Object FullName | ForEach-Object { $_.FullName.Substring((Resolve-Path $d).Path.Length) + '|' + (Get-FileHash $_.FullName).Hash } }
"salinan = produksi: " + (-not (Compare-Object (& $h data\chroma) (& $h data\container\chroma)))
```

Setelah `reparse`, artikel lama harus tetap identik (yang berubah hanya bila parser berubah sejak artikel
itu diambil). `ingest.py` mencetak jumlah chunk terpotong 512 token per seksi di awal: catat angkanya.

**Pemulihan.** Cadangan dari langkah 1 dan 2 ada di `data\backups\pre_antrean_$tgl\` (`chroma\` dan
`articles.json`); jangan dihapus sampai hasil ingest diverifikasi. Bila jendela PowerShell sempat tertutup,
cari foldernya lalu isi ulang `$tgl` dengan tanggal pada nama folder itu:

```powershell
Get-ChildItem data\backups -Directory -Filter "pre_antrean_*" | Select-Object -ExpandProperty Name
$tgl = '2026-10-25'   # contoh: sesuaikan dengan nama folder di atas

# A. Gagal SEBELUM langkah 4 (indeks belum tersentuh): pulihkan articles.json saja
Copy-Item -Force "data\backups\pre_antrean_$tgl\articles.json" data\articles.json

# B. Gagal SAAT atau SETELAH langkah 4: pulihkan indeks DAN articles.json (hentikan demo/evaluasi dulu)
Remove-Item -Recurse -Force data\chroma
if (Test-Path data\chroma) { throw "indeks rusak belum terhapus; tutup proses yang membukanya lalu ulangi" }
Copy-Item -Recurse "data\backups\pre_antrean_$tgl\chroma" data\chroma
Copy-Item -Force "data\backups\pre_antrean_$tgl\articles.json" data\articles.json
.\.venv\Scripts\python.exe -m evaluation.index_check --embed-sample 0   # harus INDEKS SEGAR, kode 0
```

Setelah pemulihan, antrean kembali belum digabung, jadi langkah 0-6 bisa diulang. Jangan memakai
`ingest.py --rebuild` sebagai jalan pintas. Bila ingest hanya terhenti di tengah (mis. memori habis) tanpa
galat SQLite/ChromaDB, cukup jalankan ulang langkah 4: chunk tersimpan bertahap.

**Merekam keluaran.** Di Windows PowerShell 5.1, `Start-Transcript` **tidak merekam keluaran program
native** (`python.exe`, `docker`) yang diketik langsung di prompt: rekaman ingest 2026-10-25 hanya memuat
baris perintah dan keluaran cmdlet PowerShell (mis. `salinan = produksi: True`), tanpa satu baris pun dari
Python. Dalam skrip `.ps1` atau `powershell -Command` keluaran itu ikut terekam (diuji 2026-10-25), jadi
gejalanya khusus perintah yang diketik interaktif. Untuk lain kali, alirkan setiap perintah Python lewat
`Tee-Object` (keluaran tetap tampil di layar):

```powershell
$env:PYTHONIOENCODING = "utf-8"   # tanpa ini Python yang keluarannya dialirkan memakai cp1252 dan gagal pada karakter seperti "→"
$env:PYTHONUNBUFFERED = "1"       # keluaran tampil saat itu juga, bukan saat program selesai
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8   # PowerShell membaca keluaran Python sebagai UTF-8
function Rekam { process { "$_" } }   # baris stderr (ErrorRecord di 5.1) menjadi teks biasa
$log = "data\ingest_antrean_" + [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'SE Asia Standard Time').ToString('yyyy-MM-dd') + ".log"

# pola untuk SETIAP perintah Python di langkah 0-6:
.\.venv\Scripts\python.exe src\ingest.py 2>&1 | Rekam | Tee-Object -FilePath $log -Append
"kode keluar: $LASTEXITCODE" | Tee-Object -FilePath $log -Append
```

Diuji 2026-10-25 di folder sementara (PowerShell 5.1.26100, jendela konsol sungguhan): stdout dan stderr
terekam, karakter non-ASCII utuh, `$LASTEXITCODE` tetap kode keluar Python (3 pada program uji), dan
perintah `python -c "..."` langkah 3 berjalan tanpa perubahan kutip. Catatan: berkasnya UTF-16 (bawaan
`Tee-Object` di 5.1; terbaca Notepad dan `Get-Content`), dan urutan baris stderr terhadap stdout bisa
bergeser karena keduanya pipa terpisah. Jangan memakai pola ini bila `$ErrorActionPreference = 'Stop'`:
baris stderr akan menghentikan perintah.

## Mode offline Hugging Face

Ingest, `--update-metadata`, `index_check`, skrip evaluasi dan pelabelan yang memuat model, serta demo
berjalan dengan **`HF_HUB_OFFLINE=1`**, disetel `hf_env.prepare_hf_env()` di awal setiap titik masuk (bukan
saat modul diimpor): model dan tokenizer hanya dibaca dari cache lokal. Ini wajib karena tokenizer di
`chunker.py` (berkas terkunci) tidak memakai revisi yang dipatok, sehingga tanpa mode offline ia bisa
mengambil versi terbaru dari Hugging Face Hub. Di mesin baru, unduh model sekali dengan
`HF_HUB_OFFLINE=0` (perintah di bawah).

**Model dibaca dari cache lokal tanpa cek ke Hugging Face Hub** (`HF_HUB_OFFLINE=1`, disetel
`hf_env.prepare_hf_env()` di awal setiap titik masuk; revisi bge-m3 dipatok di `ingest.MODEL_REVISION`). Di mesin baru, unduh sekali dengan Hub menyala:

```powershell
$env:HF_HUB_OFFLINE = "0"
.\.venv\Scripts\python.exe -c "import ingest; ingest.load_model()"
Remove-Item Env:HF_HUB_OFFLINE
```

## Menjalankan demo

Antarmuka Streamlit dua halaman (beranda + "Tentang sistem ini") di atas pipeline yang sama dengan yang
dievaluasi. Lapisannya: `src/webapp/ui/` (tampilan) -> `src/webapp/service.py` (validasi, batas laju, serialisasi) ->
`generator.py` + `retriever.py` (terkunci). Butuh indeks di `data/chroma/` (lihat
[README, "Membangun basis pengetahuan"](../README.md#membangun-basis-pengetahuan)) dan `GEMINI_API_KEY` di `.env`.

```powershell
.\.venv\Scripts\python.exe -m streamlit run src\webapp\app.py   # dari root repositori
```

Di Command Prompt (cmd): perintah yang sama tanpa `.\` di depan. Browser terbuka ke
`http://localhost:8501`; hentikan dengan Ctrl+C. Pemantau berkas Streamlit dimatikan
(`.streamlit/config.toml`), jadi **jalankan ulang server setelah mengubah kode**.

**Pemanasan:** saat halaman pertama kali dibuka, satu utas latar memuat tokenizer, indeks, dan model
embedding (tanpa memanggil LLM), sementara pengguna masih mengetik. Setiap sumber daya dimuat sekali per
proses (log server: satu baris `memuat <nama>` per sumber daya). Terukur 2026-10-22, laptop 16 GB:
pemanasan 21 dtk saat memori lega, 40-60 dtk saat memori sesak; setelah itu embedding kueri 0,1-0,3 dtk
dan pencarian di bawah 0,05 dtk per pemeriksaan. Waktu selebihnya adalah panggilan Gemini (median ~7 dtk
pada evaluasi; bisa puluhan detik saat layanan membalas 503).

Masukan dibatasi **1.500 karakter** (wilayah yang terukur bekerja; lihat [README, "Keterbatasan"](../README.md#keterbatasan)); validasinya di
lapisan layanan, termasuk pembuangan karakter kontrol. Sejak ~220 token demo menampilkan peringatan
**sebelum** pemeriksaan; kalau teks panjang ditempel lalu tombol langsung ditekan, klik pertama hanya
menampilkan peringatan.

**Batas laju** (`src/webapp/settings.py`): jeda 15 detik dan 10 pemeriksaan per jam per sesi, 60 per jam per
proses, dan demo berhenti di **400 permintaan per hari** menurut buku besar kuota yang sama dengan skrip
evaluasi (panggilan evaluasi ikut terhitung). Batas per sesi bisa dilewati dengan memuat ulang halaman
(sesi Streamlit baru); perlindungan sebenarnya ada di batas per proses dan batas harian. Pemeriksaan
diserialkan per proses: pengguna kedua melihat pesan "menunggu giliran", dan setelah 150 detik menunggu
diberi pesan untuk mencoba lagi.

**Mode penguji** (bawaan mati) menampilkan panel "Detail untuk penguji": kandidat retrieval beserta skor,
alasan dan parafrase LLM, waktu per tahap, token, dan jenis galat. Hanya bisa dinyalakan dari sisi server,
tidak dari URL:

```powershell
$env:DEMO_TESTER_MODE = "1"          # variabel lingkungan (diutamakan), sesi PowerShell ini saja
```

atau buat `.streamlit/secrets.toml` (di-gitignore) berisi `demo_tester_mode = true`. Nilai
`1`/`true`/`ya`/`yes`/`on` menyalakan; nilai lain atau tidak diatur berarti mati.

> **Jangan menjalankan demo di container Docker dan skrip di host secara bersamaan.** Di host, buku besar kuota
> (`data/quota_ledger.json`) dilindungi kunci antar-utas dan kunci berkas OS, jadi demo dan skrip evaluasi di
> host aman berjalan bersamaan. Container memakai buku besarnya sendiri (lihat "Docker"), sehingga
> hitungan kuota container dan host tidak saling terlihat.

> **Kuota bersama dengan evaluasi.** Demo dan evaluasi berbagi kuota harian
> yang sama: 500 permintaan per hari untuk `gemini-3.5-flash-lite`, tercatat di
> `data/quota_ledger.json`, satu permintaan per pemeriksaan. Bila keduanya
> diperlukan di hari yang sama, **jalankan evaluasi lebih dulu**, agar evaluasi
> tidak berhenti di tengah karena kuota sudah terpakai demo.

## Arsip indeks Versi 1

`archive/v1/` berisi salinan indeks ChromaDB dan `articles.json` (150 artikel,
450 chunk, ~9,5 MB) persis seperti saat Versi 1 dievaluasi. Tujuannya agar
evaluasi Versi 1 tetap dapat direproduksi setelah basis data diperluas, dan agar
Versi 2 dapat dievaluasi pada data yang sama, sehingga perbedaan hasil murni
karena arsitektur. Arsip **tidak di-commit**: isinya teks artikel pihak ketiga,
dan ChromaDB menulis ulang berkasnya setiap kali dibuka. Sidik jari **isinya**
(bukan hash berkas) tercatat di `testset/v1.meta.json`
(`arsip_indeks_v1_2026-09-25`).

Memakai arsip, tanpa mengubah kode:

```powershell
$env:RAG_INDEX_DIR = "archive/v1"
.\.venv\Scripts\python.exe -m evaluation.index_check --expect-v1-archive   # wajib lolos (kode 0)
.\.venv\Scripts\python.exe -m evaluation.testset_eval                      # atau skrip lain
Remove-Item Env:RAG_INDEX_DIR                                              # kembali ke data/
```

**Bila arsip hilang, bangun ulang dari daftar artikel.** Yang ter-commit hanya
`archive/v1/article_ids.json`: id, URL, judul, label, kategori, dan tanggal ke-150
artikel, dalam urutan arsip. `articles.json` sengaja tidak di-commit karena memuat
teks hoaks apa adanya, termasuk nomor dan tautan penipuan.

1. Pulihkan `archive/v1/articles.json` lewat scraping ulang berdasarkan daftar
   URL itu. Artikel diambil dari cache `data/raw_html/` bila ada, dan dari situs
   sumber bila tidak (timeout 45 dtk, retry, jeda 1,5 dtk). Proses gagal tanpa
   menulis berkas bila ada artikel yang tidak dapat dipulihkan:

   ```powershell
   .\.venv\Scripts\python.exe -m scraping.restore archive\v1\article_ids.json --out archive\v1\articles.json
   ```

2. Bangun ulang indeksnya. `ingest` menolak menulis ke `archive/` tanpa
   `--allow-archive`:

   ```powershell
   .\.venv\Scripts\python.exe src\ingest.py --rebuild --articles archive\v1\articles.json --chroma-dir archive\v1\chroma --allow-archive
   ```

3. Verifikasi:

   ```powershell
   $env:RAG_INDEX_DIR = "archive/v1"
   .\.venv\Scripts\python.exe -m evaluation.index_check --expect-v1-archive
   .\.venv\Scripts\python.exe -m evaluation.retrieval_ablation --out-json cek.json --out-report cek.txt
   ```

   `sha256_teks_metadata` dan `sha256_articles_json_isi` harus cocok persis, dan
   `cek.json` harus identik dengan `testset/retrieval_ablation.json` (selain
   tanggal). Prosedur ini sudah diuji (2026-09-25, mesin
   pengembangan, ke direktori sementara): keenam sidik jari cocok, **termasuk byte
   embedding**, dalam ~8 menit di CPU. Pada mesin atau versi pustaka lain,
   `sha256_embedding_float32` bisa berbeda di digit presisi. Dalam kasus itu,
   kesetaraan dibuktikan lewat kosinus `index_check` dan ablasi yang identik.

Pemulihan dari cache sudah diuji (2026-09-26): `scraping.restore` menghasilkan
`articles.json` dengan `sha256_articles_json_isi` identik dengan yang tercatat.
Jalur jaringan belum diuji.

**Keterbatasan pemulihan lewat scraping ulang:**

- Bergantung pada artikel yang **masih tersedia** di situs sumber. Artikel yang
  dihapus atau dipindahkan penerbit membuat pemulihan gagal.
- Artikel yang **diperbarui penerbitnya** setelah diambil (September 2026) menghasilkan teks
  berbeda, sehingga sidik jari (`sha256_articles_json_isi`, `sha256_teks_metadata`)
  tidak cocok lagi. Arsip seperti itu **bukan** arsip Versi 1 dan tidak sah
  untuk dibandingkan dengan baseline.
- Hasil parse juga bergantung pada parser. Selama parser berubah, pemulihan hanya
  setara bila dijalankan dengan kode pada tag atau commit yang sama.

## Docker

**Peran Docker.** Venv Windows (Python 3.11) adalah **cara utama** untuk pengembangan, evaluasi, dan demo
harian; semua angka evaluasi diukur di sana. Docker (Python 3.13) adalah **cara resmi untuk lingkungan yang
dapat direproduksi**: menjalankan demo di mesin lain tanpa menyiapkan venv, membuktikan kesetaraan lingkungan
(pembuktian embedding di bawah), dan menjadi dasar deployment di masa depan. CI membangun image di setiap push
(job `docker-build`, tanpa menjalankan container) untuk membuktikan Dockerfile masih bisa dibangun.

**Kebutuhan memori (terukur 2026-10-24):** container memuncak di 3,39 GB, jadi `mem_limit` 5 GB dan WSL2
minimal `memory=6GB` (`%USERPROFILE%\.wslconfig`, berlaku setelah `wsl --shutdown`). Di laptop 16 GB, sediakan
**sekitar 4-5 GB RAM bebas di Windows** sebelum build atau `docker compose up`: build pertama turun dari 4,8 GB
ke di bawah 0,6 GB RAM bebas Windows dan dihentikan. Tutup peramban, aplikasi obrolan, dan IDE lebih dulu.

`docker compose up --build` menjalankan demo di http://127.0.0.1:8501 (hanya dapat diakses dari mesin ini).
Image hanya berisi kode, konfigurasi tampilan, logo, dan dua berkas angka publik untuk halaman "Tentang"
(`.dockerignore` berupa daftar-putih). **Container tidak pernah menulis ke `data/` produksi**: semua
keadaannya ada di `data/container/` (di-gitignore).

| Di host | Di container | Mode | Untuk |
| --- | --- | --- | --- |
| `data/container/chroma/` | `/app/data/chroma` | baca-tulis | SALINAN indeks khusus container |
| `data/container/kuota/` | `/app/data/kuota` | baca-tulis | buku besar kuota container (`RAG_LEDGER_DIR`) |
| `data/container/logs/` | `/app/logs` | baca-tulis | log server (`RAG_LOG_DIR`) |
| `.env` | `/app/.env` | baca-saja | kunci API; wajib ada |
| cache Hugging Face host (`HF_CACHE_DIR`, bawaan `%USERPROFILE%\.cache\huggingface`) | `/home/app/.cache/huggingface` | baca-saja | bge-m3, revisi dipatok |
| `data/container/hasil/` (hanya `tools`) | `/app/data/hasil` | baca-tulis | keluaran alat |
| `testset/` (hanya `tools`) | `/app/testset` | baca-saja | kueri tetap, set uji |

**Mengapa salinan indeks, bukan pemasangan hanya-baca:** ChromaDB 1.5.9 tidak bisa membuka indeks yang
dipasang hanya-baca (diuji 2026-10-24: `attempt to write a readonly database` saat klien dibuat), dan menulis
SQLite lewat folder bersama Windows/WSL2 berisiko merusaknya. Salinan dibuat sekali, dan **dibuat ulang
setiap kali indeks produksi berubah** (setelah ingest di host):

```powershell
docker compose stop demo
Remove-Item -Recurse -Force data\container\chroma
Copy-Item -Recurse data\chroma data\container\chroma
New-Item -ItemType Directory -Force data\container\kuota, data\container\logs, data\container\hasil
docker compose up -d demo
```

- **Image:** Python 3.13 slim (dipatok ke digest), torch build CPU, versi dari `requirements.txt`,
  multi-stage, berjalan sebagai pengguna non-root `app`, sistem berkas container baca-saja.
- **Kesehatan:** container dijalankan lewat `python -m webapp.serve`, yang memulai pemanasan saat server
  menyala, di proses yang sama dengan Streamlit (setiap baris log memuat PID). Status `healthy` baru muncul
  setelah pemanasan selesai tanpa galat. Bila indeks tidak ada atau `GEMINI_API_KEY` kosong, container
  tetap tidak sehat.
- **Memori:** `mem_limit: 5g`.

**Terukur 2026-10-24** (laptop 16 GB, WSL2 `memory=6GB`):

| Ukuran | Nilai |
| --- | --- |
| Image | 2,93 GB di disk (lapisan venv 2,17 GB), 626 MB terkompresi |
| Build | ~5,5 menit tanpa cache (`pip install` 194 dtk), 39 dtk dengan cache |
| Sampai `healthy` | 26 dtk |
| Muat model / tokenizer / indeks | 3,3 / 10,0 / 1,5 dtk, masing-masing sekali, satu proses (pid 1) |
| Puncak memori container | 3,39 GB (`memory.peak`); 1,29 GiB setelah pemanasan dan satu pemeriksaan |
| Pemeriksaan dari peramban Windows | berhasil, 1 panggilan Gemini |

Waktu muat model di container (3,3 dtk) lebih cepat daripada di venv (15,2 dtk), jadi cache host yang
dipasang baca-saja dipertahankan.

**Kesetaraan embedding** (`python -m evaluation.embedding_proof`; 200 chunk acak benih 20261022 di-embed ulang
dan dibandingkan dengan vektor tersimpan, ditambah top-3 untuk 64 kueri tetap; ambang ditetapkan sebelum
mengukur; masing-masing pada salinan indeks yang belum pernah dibuka):

| Lingkungan | Kosinus min / rata-rata | Top-3 HNSW = eksak | Top-3 sama antar-lingkungan | Putusan |
| --- | --- | --- | --- | --- |
| venv Windows, Python 3.11.4 | 0,9999999999985 / 0,9999999999997 | 64/64 | (pembanding) | SAMA |
| container Linux, Python 3.13.16 | 0,9999999999987 / 0,9999999999996 | 64/64 | 64/64 | SAMA |

Bukti: `docs/evaluasi/tahap2_bukti_embedding_{windows,container}.json`.

Alat di container berjalan lewat layanan `tools` (tidak ikut `up`), juga hanya pada salinan indeks container.
**Ingest dan evaluasi untuk indeks produksi tetap dijalankan di venv host**, tempat angka evaluasi diukur:

```powershell
docker compose run --rm tools python -m evaluation.retriever_exactness --out-json /app/data/hasil/exactness.json
```

> **Jangan menjalankan demo di container dan skrip (evaluasi, ingest, atau demo) di host secara bersamaan.**
> Kuota Gemini dihitung per proyek Google, sedangkan container mencatat ke buku besarnya sendiri
> (`data/container/kuota/`). Keduanya tidak saling melihat hitungan, jadi batas harian demo (400) dan
> pemeriksaan anggaran evaluasi bisa meleset tanpa ketahuan.
