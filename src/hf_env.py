"""
Persiapan lingkungan Hugging Face untuk program yang memuat model atau tokenizer bge-m3.

Dipanggil EKSPLISIT di awal titik masuk program (perintah ingest, `--update-metadata`, skrip evaluasi dan
pelabelan yang memuat model, dan demo), bukan sebagai efek samping impor: mengimpor modul proyek mana pun
tidak mengubah `os.environ` (diuji `tests/core/test_hf_env.py`).

Harus dipanggil SEBELUM `huggingface_hub`/`transformers` diimpor, karena keduanya membaca variabel ini saat
diimpor. Bila sudah terlambat, fungsi ini melempar galat alih-alih diam-diam tidak berlaku.
"""

import os
import sys

# Nilai bawaan; `setdefault` agar pengguna tetap bisa menimpa (mis. HF_HUB_OFFLINE=0 untuk unduhan pertama).
HF_ENV_DEFAULTS: dict[str, str] = {
    # Model DAN tokenizer hanya dari cache lokal. Wajib untuk ingest: tokenizer `chunker.make_token_counter`
    # (berkas terkunci) tidak dipatok revisinya, jadi tanpa ini ia bisa mengambil `main` terbaru dari Hub.
    # Untuk demo juga mempercepat muat model (82,7 -> 15,2 dtk, terukur 2026-10-22).
    "HF_HUB_OFFLINE": "1",
    # Repo BAAI/bge-m3 hanya punya .bin; tanpa ini transformers mengunduh varian safetensors 2,3 GB di utas
    # latar non-daemon dan proses menggantung (CLAUDE.md, "Jebakan").
    "DISABLE_SAFETENSORS_CONVERSION": "1",
    "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
}
_TOO_LATE_MODULES = ("huggingface_hub", "transformers", "sentence_transformers")
_prepared = False


def prepare_hf_env() -> None:
    """
    Setel variabel lingkungan Hugging Face; RuntimeError bila pustakanya sudah terlanjur diimpor.

    Aman dipanggil berulang (Streamlit menjalankan ulang skrip demo di setiap interaksi): panggilan setelah
    yang pertama tidak melakukan apa pun.
    """
    global _prepared
    if _prepared:
        return
    loaded = [m for m in _TOO_LATE_MODULES if m in sys.modules]
    if loaded:
        raise RuntimeError(
            f"prepare_hf_env() dipanggil setelah {', '.join(loaded)} diimpor: variabel lingkungan tidak akan "
            "berlaku. Panggil di awal titik masuk, sebelum memuat model atau tokenizer."
        )
    for key, value in HF_ENV_DEFAULTS.items():
        os.environ.setdefault(key, value)
    _prepared = True
