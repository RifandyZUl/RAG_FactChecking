"""
Potongan render bersama untuk halaman demo.

Aturan keamanan di sini: SEMUA teks dinamis (pesan pengguna, judul, Kesimpulan, Penjelasan, label) lewat
`esc` (html.escape) sebelum masuk HTML, dan tautan hanya lewat `link`, yang menolak skema selain
http/https (`presentation.is_safe_url`). Fungsi `*_html` murni (mudah diuji tanpa Streamlit); fungsi
`render_*`/`load_css` menggambar.
"""

import base64
import html
import os
import re
import tomllib
from functools import cache
from typing import Any

import streamlit as st

from webapp import resources, settings
from webapp.presentation import FALLBACK_STATUS_COLOR, STATUS_STYLES, is_safe_url

# Ikon garis dari berkas acuan: digambar CSS (style.css, .cp-icon-*), karena sanitizer st.html membuang <svg>.
ICON_ALERT = '<span class="cp-icon cp-icon-alert" aria-hidden="true"></span>'
ICON_INFO = '<span class="cp-icon cp-icon-info" aria-hidden="true"></span>'


def esc(text: str) -> str:
    """Escape HTML (termasuk tanda kutip) untuk teks dinamis."""
    return html.escape(text, quote=True)


def link(url: str, label: str) -> str:
    """Tautan keluar aman; URL bukan http/https dirender sebagai teks biasa tanpa tautan."""
    if not is_safe_url(url):
        return esc(label)
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def pill_html(text: str, color: str) -> str:
    """Pil status: latar warna status (variabel CSS dari config.toml), teks putih."""
    return f'<span class="cp-pill" style="background: var(--status-{esc(color)})">{esc(text)}</span>'


def neutral_pill_html(text: str) -> str:
    """Pil netral berkas acuan untuk "belum ditemukan" (bukan status hasil pemeriksaan)."""
    return f'<span class="cp-pill cp-pill-neutral">{esc(text)}</span>'


def paragraphs_html(text: str, cls: str = "cp-body") -> str:
    """Teks multi-paragraf (baris kosong = paragraf baru), di-escape."""
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f'<p class="{cls}">{esc(p)}</p>' for p in parts)


@cache
def _theme() -> dict:
    return tomllib.loads(settings.STREAMLIT_CONFIG_PATH.read_text(encoding="utf-8"))["theme"]


def theme_variables_css() -> str:
    """Variabel CSS dari .streamlit/config.toml: satu sumber untuk warna tema dan warna status."""
    t = _theme()
    names = sorted({s.color for s in STATUS_STYLES.values()} | {FALLBACK_STATUS_COLOR})
    pairs = [("theme-bg", t["backgroundColor"]), ("theme-text", t["textColor"]),
             ("theme-primary", t["primaryColor"]), ("theme-border", t["borderColor"])]
    pairs += [(f"status-{n}", t[f"{n}Color"]) for n in names]
    # Spasi setelah "{" wajib: Markdown Streamlit membuang "{--...}" yang rapat (terlihat 2026-10-22).
    return ":root { " + " ".join(f"--{k}: {v};" for k, v in pairs) + " } "


@cache
def _css() -> str:
    """CSS satu baris tanpa komentar: Markdown memecah blok <style> pada baris kosong (terlihat 2026-10-22)."""
    raw = re.sub(r"/\*.*?\*/", "", settings.STYLE_PATH.read_text(encoding="utf-8"), flags=re.DOTALL)
    return theme_variables_css() + " ".join(raw.split())


def load_css() -> None:
    """
    Muat CSS (isi berkas di-cache per proses); dipanggil di awal fungsi setiap halaman.

    Satu-satunya pemakaian `unsafe_allow_html` di demo, dan isinya HANYA CSS statis (style.css + warna
    dari config.toml), tanpa teks dinamis apa pun. Alasannya (Streamlit 1.64, diperiksa 2026-10-22):
    mode aman st.html menyaring dengan profil HTML DOMPurify yang membuang <style>, termasuk jalur
    "hanya style" ke wadah event; menyalakan `unsafe_allow_javascript` justru mengizinkan <script>.
    Penanda `cp-css` dipakai CSS untuk menyembunyikan wadah elemen ini.
    """
    st.markdown(f'<span class="cp-css"></span><style>{_css()}</style>', unsafe_allow_html=True)


@cache
def logo_data_uri() -> str:
    return "data:image/png;base64," + base64.b64encode(settings.LOGO_HEADER_PATH.read_bytes()).decode("ascii")


def header_html(app_name: str) -> str:
    return f'<div class="cp-header"><img src="{logo_data_uri()}" alt=""><span>{esc(app_name)}</span></div>'


def numbered_steps_html(steps: tuple[str, ...]) -> str:
    items = "".join(f'<li><span class="cp-num">{i}</span><span>{esc(s)}</span></li>'
                    for i, s in enumerate(steps, start=1))
    return f'<ol class="cp-steps-list">{items}</ol>'


def bullets_html(items: tuple[str, ...] | list[str]) -> str:
    return '<ul class="cp-bullets">' + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


# -- Sumber daya ber-cache Streamlit (bermuara pada pemuat sekali-muat di resources.py) -----------


@st.cache_resource(show_spinner=False)
def cached_collection() -> object:
    return resources.collection.get()


@st.cache_resource(show_spinner=False)
def cached_model() -> object:
    return resources.embedding_model.get()


@st.cache_resource(show_spinner=False)
def cached_provider() -> object:
    return resources.provider.get()


@st.cache_data(ttl=600, show_spinner=False)
def cached_index_stats() -> resources.IndexStats:
    """Jumlah artikel dan tanggal data terakhir dari indeks yang SEDANG dipakai (dibaca ulang tiap 10 menit)."""
    return resources.index_stats()


def tester_mode_enabled() -> bool:
    """Mode penguji: variabel lingkungan diutamakan, lalu `.streamlit/secrets.toml`. Bawaan mati."""
    from streamlit.errors import StreamlitSecretNotFoundError

    env_value = os.environ.get(settings.TESTER_MODE_ENV)
    if env_value is not None:
        return settings.parse_flag(env_value)
    try:
        return settings.parse_flag(st.secrets.get(settings.TESTER_MODE_SECRET))
    except StreamlitSecretNotFoundError:  # tidak ada secrets.toml: mode penguji mati
        return False


# -- Halaman (didaftarkan app.py; dipakai st.page_link agar navigasi tetap di sesi yang sama) -------

_pages: dict[str, Any] = {}


def register_pages(pages: dict[str, Any]) -> None:
    _pages.update(pages)


def page(name: str) -> Any:
    return _pages[name]
