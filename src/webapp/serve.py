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

Setiap baris log memuat PID, dan bila `RAG_LOG_DIR` disetel log server juga ditulis ke berkas di folder
itu. Itu bukti bahwa pemanasan dan sesi halaman memakai proses (dan pemuat sekali-muat) yang sama.

Di Windows, demo tetap dijalankan dengan `streamlit run src\\webapp\\app.py` (README).
"""

import os
import time
from collections.abc import Callable
from pathlib import Path

from hf_env import prepare_hf_env

READY_FILE_ENV = "RAG_READY_FILE"
LOG_DIR_ENV = "RAG_LOG_DIR"  # bila disetel, log server juga ditulis ke <folder>/demo_server.log
LOG_FILE_NAME = "demo_server.log"
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

    # Seperti app.py, ditambah PID: baris "memuat <nama>" dari pemanasan dan dari sesi halaman harus
    # ber-PID sama (satu proses, model dimuat sekali). basicConfig di app.py tidak berbuat apa-apa lagi
    # karena logger akar sudah punya handler.
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    log_dir = os.environ.get(LOG_DIR_ENV, "").strip()
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(Path(log_dir) / LOG_FILE_NAME, encoding="utf-8"))
    logging.basicConfig(level=logging.WARNING, handlers=handlers,
                        format="%(asctime)s pid=%(process)d %(levelname)s %(name)s: %(message)s")
    logging.getLogger("resources").setLevel(logging.INFO)
    logging.getLogger("serve").warning("server Streamlit dan pemanasan berjalan di proses pid=%d", os.getpid())

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
