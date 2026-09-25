"""
Demo Streamlit pemeriksa klaim: adapter tipis di atas pipeline Versi 1.

Jalankan dari root proyek:  .\\.venv\\Scripts\\python.exe -m streamlit run src\\app.py

Tidak ada logika retrieval atau penyusunan jawaban di sini: semuanya lewat
`retriever.retrieve` dan `generator.AnswerGenerator`, persis seperti yang
dievaluasi. Data tampilan disiapkan di `presentation.py` (tanpa Streamlit);
fungsi `render_*` di sini hanya menggambar `ResultView` dan tidak memanggil API.

Indeks ChromaDB hanya DIBACA: koleksi dibuka tanpa `get_or_create`, sehingga
demo tidak pernah membuat koleksi. (ChromaDB sendiri menulis ulang berkas indeks
setiap kali koleksi dibuka, juga saat evaluasi; isinya tetap sama. Lihat CLAUDE.md.)
"""

import logging
import os
from collections.abc import Callable
from typing import Any

# ingest diimpor lebih dulu: ia men-set DISABLE_SAFETENSORS_CONVERSION sebelum
# transformers dimuat (lihat CLAUDE.md, "Jebakan"). Pengecualian I001 di ruff.toml.
from ingest import CHROMA_DIR, COLLECTION_NAME, load_model

import chromadb
import chromadb.errors
import streamlit as st
from chromadb.config import Settings
from streamlit.errors import StreamlitSecretNotFoundError

from chunker import MAX_SEQ_LENGTH
from generator import AnswerGenerator
from llm import LLMConfigError, LLMProvider, get_provider
from llm.secrets import redact
from presentation import (
    ADVICE_HEADING,
    ARTICLE_LINK_PREFIX,
    CLARIFICATION_HEADING,
    CLARIFICATION_LINE_HEIGHT,
    DIAGNOSTICS_LABEL,
    INPUT_LABEL,
    INPUT_PLACEHOLDER,
    LIMITATION_NOTE,
    PAGE_SUBTITLE,
    PAGE_TITLE,
    PROGRESS_DONE,
    PROGRESS_FAILED,
    PROGRESS_RUNNING,
    READING_WIDTH_PX,
    REFERENCES_HEADING,
    RELATED_HEADING,
    RELATED_NOTE,
    STEP_COMPARE,
    STEP_LOAD_MODEL,
    STEP_OPEN_INDEX,
    STEP_SEARCH,
    SUBMIT_LABEL,
    TESTER_MODE_ENV,
    TESTER_MODE_SECRET,
    Diagnostics,
    FailureKind,
    ResultView,
    build_view,
    escape_markdown,
    failure_view,
    markdown_link,
    parse_flag,
    validate_claim,
)
from retriever import ArticleHit, retrieve

logger = logging.getLogger("app")

RESULT_STATE_KEY = "result_view"
CLARIFICATION_KEY = "clarification"

# Satu-satunya CSS: jarak baris klarifikasi (tidak bisa diatur lewat config.toml).
# Warna tidak diatur di sini; semuanya di .streamlit/config.toml.
READING_CSS = (
    f"<style>.st-key-{CLARIFICATION_KEY} p {{ line-height: {CLARIFICATION_LINE_HEIGHT}; }}</style>"
)


class IndexUnavailableError(Exception):
    """Indeks vektor tidak ada atau kosong; demo tidak membuatnya sendiri."""


# --------------------------------------------------------------------------
# Setelan dan sumber daya (dimuat sekali per proses server lewat cache Streamlit)
# --------------------------------------------------------------------------


def tester_mode_enabled() -> bool:
    """Mode penguji: variabel lingkungan diutamakan, lalu `.streamlit/secrets.toml`. Bawaan mati."""
    env_value = os.environ.get(TESTER_MODE_ENV)
    if env_value is not None:
        return parse_flag(env_value)
    try:
        return parse_flag(st.secrets.get(TESTER_MODE_SECRET))
    except StreamlitSecretNotFoundError:  # tidak ada secrets.toml: mode penguji mati
        return False


@st.cache_resource(show_spinner=False)
def load_collection() -> Any:
    """
    Buka koleksi ChromaDB yang SUDAH ada, tanpa membuat koleksi baru.

    Melempar `IndexUnavailableError` bila berkas basis data, koleksi, atau isinya
    tidak ada. Galat tidak di-cache, jadi setelah indeks dibangun cukup muat ulang.
    """
    if not (CHROMA_DIR / "chroma.sqlite3").is_file():
        raise IndexUnavailableError(f"berkas basis data tidak ditemukan di {CHROMA_DIR}")
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False)
    )
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except chromadb.errors.NotFoundError as e:
        raise IndexUnavailableError(f"koleksi '{COLLECTION_NAME}' tidak ada") from e
    if collection.count() == 0:
        raise IndexUnavailableError(f"koleksi '{COLLECTION_NAME}' kosong")
    return collection


@st.cache_resource(show_spinner=False)
def load_embedder() -> Any:
    """Muat model embedding bge-m3 sekali per proses (fungsi yang sama dengan evaluasi)."""
    return load_model()


@st.cache_resource(show_spinner=False)
def load_provider() -> LLMProvider:
    """Buat penyedia LLM dari `.env`; `LLMConfigError` tidak di-cache."""
    return get_provider()


def count_query_tokens(embedder: Any, claim: str) -> int | None:
    """Panjang klaim dalam token model embedding (diagnostik saja; tidak memengaruhi pencarian)."""
    tokenizer = getattr(embedder, "tokenizer", None)
    if tokenizer is None:
        return None
    return len(tokenizer(claim)["input_ids"])


# --------------------------------------------------------------------------
# Satu-satunya fungsi yang memanggil pipeline (dan karena itu API)
# --------------------------------------------------------------------------


def check_claim(claim: str, on_step: Callable[[str], None]) -> ResultView:
    """
    Jalankan pipeline Versi 1 untuk satu klaim dan kembalikan data tampilannya.

    `on_step` menerima teks langkah yang sedang berjalan (untuk indikator proses);
    fungsi ini sendiri tidak menggambar apa pun.
    """
    on_step(STEP_OPEN_INDEX)
    try:
        collection = load_collection()
    except IndexUnavailableError as e:
        logger.error("indeks tidak tersedia: %s", e)
        return failure_view(FailureKind.NO_INDEX, Diagnostics(error_detail=str(e)))
    try:
        provider = load_provider()
    except LLMConfigError as e:  # pesannya tidak memuat kunci; tetap disamarkan
        logger.error("konfigurasi LLM: %s", redact(str(e)))
        return failure_view(FailureKind.CONFIG, Diagnostics(error_detail=redact(str(e))))

    on_step(STEP_LOAD_MODEL)
    embedder = load_embedder()

    # Retrieval tetap `retriever.retrieve` apa adanya; pembungkus ini hanya melaporkan
    # langkah dan menyimpan hasilnya (URL artikel untuk daftar "mungkin terkait").
    hits: list[ArticleHit] = []

    def retrieve_and_keep(query: str, k: int) -> list[ArticleHit]:
        on_step(STEP_SEARCH)
        hits[:] = retrieve(query, embedder, collection, top_k=k)
        on_step(STEP_COMPARE)
        return hits

    gen = AnswerGenerator(provider, retrieve_and_keep)
    try:
        ans = gen.answer(claim)
    except Exception as e:
        # Galat LLM sudah ditangani generator; ini galat lain (mis. retrieval).
        # Dicatat lengkap di konsol server dan ditampilkan sebagai kegagalan umum.
        logger.exception("pemeriksaan klaim gagal di luar lapisan LLM")
        detail = redact(f"{type(e).__name__}: {e}")
        return failure_view(
            FailureKind.OTHER, Diagnostics(model=provider.model, error_detail=detail)
        )
    if ans.error:
        logger.warning("pemeriksaan gagal: %s", ans.error)  # sudah disamarkan penyedia
    return build_view(
        ans,
        model=provider.model,
        article_urls={h.article_id: h.url for h in hits},
        query_tokens=count_query_tokens(embedder, claim),
        query_token_limit=MAX_SEQ_LENGTH,
    )


# --------------------------------------------------------------------------
# Render: hanya menggambar ResultView, tidak memanggil API
# --------------------------------------------------------------------------


def render_header() -> None:
    """Judul, satu kalimat pengantar, dan catatan keterbatasan yang selalu terlihat."""
    st.title(PAGE_TITLE, anchor=False)
    st.markdown(PAGE_SUBTITLE)
    st.caption(LIMITATION_NOTE)


def render_status(view: ResultView) -> None:
    """Blok status: elemen paling menonjol; saran umum PENIPUAN dipisah garis."""
    with st.container(border=True):
        heading = f"{view.status_icon} {escape_markdown(view.status_label)}"
        st.markdown(f"## :{view.status_color}[{heading}]", anchors=False)
        st.markdown(escape_markdown(view.summary), width=READING_WIDTH_PX)
        if view.article_url:
            link = markdown_link(view.article_title, view.article_url)
            st.markdown(f"{ARTICLE_LINK_PREFIX} {link}", width=READING_WIDTH_PX)
        if view.advice:
            st.divider()
            st.markdown(
                f"**{ADVICE_HEADING}**  \n{escape_markdown(view.advice)}",
                width=READING_WIDTH_PX,
            )


def render_clarification(view: ResultView) -> None:
    """Klarifikasi sebagai teks baca: kolom sempit, jarak baris lega, terpisah dari status."""
    if not view.clarification:
        return
    st.space("medium")
    with st.container(key=CLARIFICATION_KEY):
        st.markdown(f"### {CLARIFICATION_HEADING}", anchors=False)
        st.markdown(escape_markdown(view.clarification), width=READING_WIDTH_PX)


def render_references(view: ResultView) -> None:
    """Rujukan sahih dari metadata; paling akhir dan paling tenang. Tanpa rujukan: dihilangkan."""
    if not view.references:
        return
    st.divider()
    st.markdown(f"### {REFERENCES_HEADING}", anchors=False)
    st.caption("\n".join(f"- {markdown_link(url, url)}" for url in view.references))


def render_related(view: ResultView) -> None:
    """Artikel bertopik dekat untuk "belum ditemukan": judul + tautan, tanpa skor."""
    if not view.related:
        return
    st.space("medium")
    st.markdown(f"### {RELATED_HEADING}", anchors=False)
    st.caption(escape_markdown(RELATED_NOTE))
    st.markdown(
        "\n".join(f"- {markdown_link(a.title, a.url)}" for a in view.related),
        width=READING_WIDTH_PX,
    )


def _fmt_number(value: float, digits: int = 2) -> str:
    """Angka desimal dengan koma (gaya Indonesia)."""
    return f"{value:.{digits}f}".replace(".", ",")


def render_diagnostics(diag: Diagnostics) -> None:
    """Panel untuk penguji (hanya di mode penguji), tertutup. Istilah teknis hanya di sini."""
    with st.expander(DIAGNOSTICS_LABEL, expanded=False):
        tokens = (
            f"{diag.input_tokens if diag.input_tokens is not None else '-'} masuk / "
            f"{diag.output_tokens if diag.output_tokens is not None else '-'} keluar"
        )
        lines = [
            f"- Model: `{diag.model or '-'}`",
            f"- Panggilan LLM: {diag.llm_calls} (percobaan HTTP: {diag.attempts})",
            f"- Latensi LLM: {_fmt_number(diag.latency_s, 1)} dtk",
            f"- Token LLM: {tokens}",
        ]
        if diag.query_tokens is not None:
            cut = (
                " -- MELEBIHI batas, sisanya tidak ikut dicari (LLM tetap membaca utuh)"
                if diag.query_token_limit and diag.query_tokens > diag.query_token_limit
                else ""
            )
            lines.append(
                f"- Token klaim untuk retrieval: {diag.query_tokens} "
                f"(batas {diag.query_token_limit}){cut}"
            )
        lines.append(f"- Ambang \"mungkin terkait\": {_fmt_number(diag.related_threshold)}")
        st.markdown("\n".join(lines))
        if diag.candidates:
            rows = [
                "| # | ID | Judul | Label | Skor kemiripan |",
                "| --- | --- | --- | --- | --- |",
            ] + [
                f"| {i} | {escape_markdown(c.article_id)} | {escape_markdown(c.title)} "
                f"| {escape_markdown(c.label)} | {_fmt_number(c.score, 4)} |"
                for i, c in enumerate(diag.candidates, start=1)
            ]
            st.markdown("**Kandidat retrieval (top-3)**\n\n" + "\n".join(rows))
        if diag.llm_reason:
            st.markdown(f"**Alasan LLM**\n\n{escape_markdown(diag.llm_reason)}")
        flags = [
            ("Jenis kegagalan", diag.failure_kind),
            ("Galat", diag.error_detail),
            ("Keluaran gagal di-parse", str(diag.parse_failures) if diag.parse_failures else ""),
            ("ID artikel tidak sah dari LLM", "ya" if diag.invalid_id else ""),
            ("URL pada keluaran LLM yang dibuang",
             str(diag.llm_urls_removed) if diag.llm_urls_removed else ""),
            ("Klarifikasi diganti Kesimpulan asli", "ya" if diag.clarification_fallback else ""),
        ]
        shown = [f"- {name}: {escape_markdown(value)}" for name, value in flags if value]
        if shown:
            st.markdown("\n".join(shown))


def render_result(view: ResultView, show_diagnostics: bool) -> None:
    """Urutan hierarki: status -> klarifikasi -> rujukan / artikel terkait -> diagnostik."""
    render_status(view)
    render_clarification(view)
    render_references(view)
    render_related(view)
    if show_diagnostics:
        render_diagnostics(view.diagnostics)


def main() -> None:
    """Susun halaman: kepala, formulir, indikator proses, lalu hasil terakhir (bila ada)."""
    st.set_page_config(page_title=PAGE_TITLE, page_icon=":material/fact_check:", layout="centered")
    st.html(READING_CSS)
    render_header()

    with st.form("claim_form", border=False):
        # Sengaja tanpa `max_chars`: widget akan memotong teks tempelan diam-diam.
        # Panjang diperiksa `validate_claim` dan pengguna diberi tahu.
        claim = st.text_area(INPUT_LABEL, placeholder=INPUT_PLACEHOLDER, height=140)
        submitted = st.form_submit_button(SUBMIT_LABEL, type="primary")

    if submitted:
        text = (claim or "").strip()
        problem = validate_claim(text)
        if problem is not None:
            st.session_state.pop(RESULT_STATE_KEY, None)
            st.markdown(f":gray[{escape_markdown(problem)}]")
        else:
            with st.status(PROGRESS_RUNNING, expanded=True) as progress:
                view = check_claim(text, on_step=progress.write)
                # Selalu "complete": status "error" berwarna merah, sedangkan kegagalan
                # teknis sengaja ditampilkan netral (abu), bukan dengan warna peringatan.
                progress.update(
                    label=PROGRESS_FAILED if view.kind == "failed" else PROGRESS_DONE,
                    state="complete",
                    expanded=False,
                )
            st.session_state[RESULT_STATE_KEY] = view

    view = st.session_state.get(RESULT_STATE_KEY)
    if view is not None:
        render_result(view, show_diagnostics=tester_mode_enabled())


main()
