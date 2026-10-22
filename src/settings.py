"""
Setelan demo terpusat: semua batas, jalur, dan nama variabel lingkungan yang dipakai lapisan layanan
dan tampilan ada di sini, satu kali.

Modul ini WAJIB diimpor sebelum transformers/huggingface_hub (`app.py` mengimpornya pertama): dua
variabel lingkungan di bawah dibaca pustaka itu saat diimpor.

Konstanta milik berkas TERKUNCI (`generator.TOP_K`, `chunker.MAX_SEQ_LENGTH`) tidak disalin ke sini;
pemakainya merujuk modul aslinya.
"""

import os

# -- Lingkungan pustaka (sebelum transformers diimpor) ------------------------------------------
# Repo BAAI/bge-m3 hanya punya .bin; tanpa ini transformers mengunduh varian safetensors 2,3 GB di
# utas latar dan proses menggantung (CLAUDE.md, "Jebakan"). Sebelumnya dipasang lewat efek samping
# `import ingest` di app.py.
os.environ.setdefault("DISABLE_SAFETENSORS_CONVERSION", "1")
# Model dan tokenizer dibaca dari cache lokal tanpa cek ke Hugging Face Hub. Terukur 2026-10-22:
# muat model 82,7 dtk (online) vs 15,2 dtk (offline); muat tokenizer sekali tercatat 101,9 dtk karena
# cek Hub. Unduhan pertama: jalankan sekali dengan HF_HUB_OFFLINE=0 (README).
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from paths import PROJECT_ROOT

# -- Masukan ------------------------------------------------------------------------------------
# 1.500 karakter: wilayah yang TERUKUR bekerja pada ablasi retrieval (Recall@3 19/20 pada ~1.500
# karakter, 2/20 pada ~5.000 karena klaim terdorong keluar dari 512 token embedding;
# testset/retrieval_ablation_report.txt, eksperimen 4). Teks lebih panjang TIDAK dipotong.
MAX_INPUT_CHARS = 1500
# Peringatan pesan panjang SEBELUM pemeriksaan, dalam token model embedding. 220 token ~ 1.000
# karakter (rasio terukur ~4,5 karakter/token). Pilihan konservatif pemilik proyek, bukan titik runtuh.
LONG_CLAIM_WARN_TOKENS = 220
LONG_CLAIM_WARN_CHARS = 1000  # cadangan bila tokenizer belum siap

# -- Batas laju (keputusan pemilik proyek 2026-10-22; docs/audit_tahap0.md 9.5) -------------------
# Batas per sesi bisa dilewati dengan memuat ulang halaman (sesi Streamlit baru). Perlindungan kuota
# yang sesungguhnya adalah batas global per proses dan berhenti harian, yang membaca buku besar yang
# sama dengan skrip evaluasi (data/quota_ledger.json), sehingga panggilan evaluasi ikut terhitung.
SESSION_MIN_INTERVAL_S = 15
SESSION_MAX_PER_HOUR = 10
GLOBAL_MAX_PER_HOUR = 60
DAILY_STOP_REQUESTS = 400  # dari RPD 500; 100 dicadangkan untuk evaluasi dan uji

# Pemeriksaan diserialkan per proses (service.py). Pengguna yang menunggu giliran lebih lama dari ini
# diberi pesan "coba lagi" alih-alih menunggu tanpa batas.
QUEUE_TIMEOUT_S = 90

# -- Mode penguji (panel diagnostik). Bawaan MATI; hanya dari variabel lingkungan atau
# .streamlit/secrets.toml (tidak pernah dari URL atau masukan pengguna). -------------------------
TESTER_MODE_ENV = "DEMO_TESTER_MODE"
TESTER_MODE_SECRET = "demo_tester_mode"

# -- Tampilan -----------------------------------------------------------------------------------
ASSETS_DIR = PROJECT_ROOT / "assets" / "brand"
LOGO_HEADER_PATH = ASSETS_DIR / "logo-96.png"  # tampil 32 px (96 px untuk layar 3x)
FAVICON_PATH = ASSETS_DIR / "logo-32.png"
STYLE_PATH = PROJECT_ROOT / "src" / "ui" / "style.css"
STREAMLIT_CONFIG_PATH = PROJECT_ROOT / ".streamlit" / "config.toml"
KESIMPULAN_PREVIEW_CHARS = 320  # Kesimpulan lebih panjang dipotong rapi dengan opsi "Tampilkan semua"
MESSAGE_EXCERPT_CHARS = 160  # potongan awal pesan pengguna di kotak "Pastikan klaimnya sama"

# Tautan keluar tetap (bukan dari LLM). Halaman utama resmi, diperiksa membalas 200 pada 2026-10-22.
TURNBACKHOAX_URL = "https://turnbackhoax.id/"
LIPUTAN6_CEK_FAKTA_URL = "https://www.liputan6.com/cek-fakta"
SOURCE_CODE_URL = "https://github.com/RifandyZUl/RAG_FactChecking"

_TRUE_VALUES = {"1", "true", "ya", "yes", "on"}


def parse_flag(value: object) -> bool:
    """Tafsirkan nilai setelan sebagai boolean; hanya nilai "hidup" yang eksplisit yang benar."""
    if isinstance(value, bool):
        return value
    return value is not None and str(value).strip().lower() in _TRUE_VALUES
