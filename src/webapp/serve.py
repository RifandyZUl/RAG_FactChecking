"""
Peluncur demo untuk container: `python -m webapp.serve [opsi streamlit run ...]`.

Sama dengan `streamlit run src/webapp/app.py`, dengan satu beda: pemanasan (`resources.start_warmup`)
dimulai saat server menyala, bukan saat halaman pertama kali dibuka. Server Streamlit berjalan di proses
yang SAMA, jadi `app.py` memakai pemuat sekali-muat yang sama (panggilan `start_warmup` di sana tidak
memulai apa-apa lagi) dan tidak ada model yang dimuat dua kali.

Begitu pemanasan selesai tanpa galat, berkas penanda di `RAG_READY_FILE` (bila disetel) ditulis;
HEALTHCHECK container baru sehat setelah berkas itu ada. Pemanasan yang gagal (mis. indeks tidak ada atau
`GEMINI_API_KEY` kosong) tidak pernah menulis penanda, sehingga container tetap tidak sehat. Pemanasan
tidak memanggil LLM.

Di Windows, demo tetap dijalankan dengan `streamlit run src\\webapp\\app.py` (README).
"""

import os
import time
from collections.abc import Callable
from pathlib import Path

from hf_env import prepare_hf_env

READY_FILE_ENV = "RAG_READY_FILE"
APP_PATH = Path(__file__).resolve().parent / "app.py"


def wait_and_mark_ready(state: Callable[[], object], ready: object, failed: object, ready_file: Path,
                        poll_s: float = 1.0) -> bool:
    """Tunggu pemanasan selesai; tulis `ready_file` hanya bila berhasil. True bila penanda ditulis."""
    while True:
        current = state()
        if current is ready:
            ready_file.write_text(time.strftime("%Y-%m-%dT%H:%M:%S%z"), encoding="utf-8")
            return True
        if current is failed:
            return False
        time.sleep(poll_s)


def main() -> int:
    prepare_hf_env()
    import logging
    import sys
    import threading

    from streamlit.web import cli as streamlit_cli

    from webapp import resources

    # Sama dengan app.py, agar baris "memuat <nama>" dari pemanasan awal ikut tercatat.
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("resources").setLevel(logging.INFO)

    ready_path = os.environ.get(READY_FILE_ENV, "").strip()
    if ready_path:
        ready_file = Path(ready_path)
        ready_file.unlink(missing_ok=True)  # penanda dari jalan sebelumnya tidak boleh terbawa
    resources.start_warmup()
    if ready_path:
        threading.Thread(target=wait_and_mark_ready, name="penanda-siap", daemon=True,
                         args=(resources.warmup_state, resources.WarmupState.READY, resources.WarmupState.FAILED,
                               ready_file)).start()

    sys.argv = ["streamlit", "run", str(APP_PATH), *sys.argv[1:]]
    return streamlit_cli.main()


if __name__ == "__main__":
    raise SystemExit(main())
