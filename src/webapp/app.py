"""
Demo Streamlit "Cek Pesan Hoaks": titik masuk. Jalankan dari root proyek (PowerShell):

    .\\.venv\\Scripts\\python.exe -m streamlit run src\\webapp\\app.py

(paket proyek dipasang ke venv dengan `pip install -e .`, jadi PYTHONPATH tidak perlu disetel).

Lapisan: `webapp/ui/` (render) -> `webapp/service.py` (validasi, batas laju, serialisasi) -> `generator.py`
+ `retriever.py` (TERKUNCI, persis seperti yang dievaluasi). `prepare_hf_env()` dipanggil pertama, sebelum
modul apa pun memuat transformers.
"""

from hf_env import prepare_hf_env

prepare_hf_env()

import logging

import streamlit as st

from webapp import resources, settings
from webapp.presentation import APP_NAME
from webapp.ui import beranda, components, tentang

# Log server (konsol): peringatan dari semua modul; pemuatan sumber daya dicatat sekali ("memuat <nama>")
# sebagai bukti tidak ada pemuatan ganda. Catatan aktivitas berkas menyusul di Tahap 3.
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("resources").setLevel(logging.INFO)

st.set_page_config(page_title=APP_NAME, page_icon=str(settings.FAVICON_PATH), layout="centered")
resources.start_warmup()  # sekali per proses (idempoten); memuat model di latar, TANPA memanggil LLM

pages = {
    "beranda": st.Page(beranda.render, title=APP_NAME, url_path="beranda", default=True),
    "tentang": st.Page(tentang.render, title=f"Tentang · {APP_NAME}", url_path="tentang"),
}
components.register_pages(pages)
navigation = st.navigation(list(pages.values()), position="hidden")
navigation.run()
