"""
Halaman beranda: masukan pesan, lalu hasil (ditemukan / belum ditemukan / gagal) di halaman yang sama.

Render saja. Pemeriksaan lewat `service.check_message`; teks dan pemetaan lewat `presentation`.
LLM hanya dipanggil di cabang tombol "Periksa pesan" ditekan, tidak pernah saat halaman dimuat ulang:
hasilnya disimpan di `st.session_state` dan rerun berikutnya hanya menggambar ulang.
"""

import streamlit as st

import presentation as p
import resources
import service
import settings
from ui import components as c

TEXT_KEY = "pesan"
RESULT_KEY = "hasil"
USAGE_KEY = "pemakaian_sesi"
WARNED_KEY = "peringatan_panjang_untuk"
NOTICE_KEY = "pemberitahuan_masukan"
SHOW_ALL_KEY = "kesimpulan_lengkap"
RESULT_COUNTER_KEY = "nomor_hasil"  # kunci checkbox per hasil, agar centang lama tidak terbawa


def _service_resources() -> service.Resources:
    return service.Resources(get_collection=c.cached_collection, get_model=c.cached_model,
                             get_provider=c.cached_provider, count_tokens=resources.count_tokens)


def _usage() -> service.SessionUsage:
    return st.session_state.setdefault(USAGE_KEY, service.SessionUsage())


def _use_example(text: str) -> None:
    st.session_state[TEXT_KEY] = text
    st.session_state.pop(NOTICE_KEY, None)


def _clear_result(keep_text: bool) -> None:
    st.session_state.pop(RESULT_KEY, None)
    st.session_state.pop(SHOW_ALL_KEY, None)
    if not keep_text:
        st.session_state[TEXT_KEY] = ""


def _run_check(text: str) -> None:
    """Jalankan pemeriksaan dengan pesan proses yang jelas, lalu simpan hasil di sesi."""
    preparing = resources.warmup_state() is not resources.WarmupState.READY
    queue_note = st.empty()
    with st.spinner(p.PROGRESS_PREPARING if preparing else p.PROGRESS_CHECKING):
        outcome = service.check_message(
            text, _usage(), _service_resources(),
            on_wait=lambda: queue_note.html(f'<p class="cp-note">{c.esc(p.PROGRESS_QUEUED)}</p>'))
    queue_note.empty()
    notice = p.input_problem_message(outcome.error, outcome.message) if outcome.error else None
    if notice is not None:
        st.session_state[NOTICE_KEY] = notice
        return
    st.session_state[RESULT_KEY] = p.build_view(outcome)
    st.session_state[RESULT_COUNTER_KEY] = st.session_state.get(RESULT_COUNTER_KEY, 0) + 1
    st.rerun()


# -- Beranda --------------------------------------------------------------------------------------


def _render_home() -> None:
    st.html(c.header_html(p.APP_NAME))
    st.html(f'<div class="cp-stack"><h1 class="cp-h1">{c.esc(p.HOME_TITLE)}</h1>'
            f'<p class="cp-lead">{c.esc(p.HOME_SUBTITLE)}</p></div>')

    with st.container(key="kartu-input"):
        # Sengaja tanpa `max_chars`: widget memotong teks tempelan diam-diam. Nilai masuk saat pengguna
        # keluar dari kotak (atau Ctrl+Enter), jadi penghitung dan peringatan diperbarui saat itu.
        raw = st.text_area(p.INPUT_LABEL, key=TEXT_KEY, placeholder=p.INPUT_PLACEHOLDER, height=150)
        text = service.clean_message(raw or "")
        over = len(text) > settings.MAX_INPUT_CHARS
        counter_cls = "cp-counter-over" if over else ""
        st.html(f'<div class="cp-counter"><span>{c.esc(p.INPUT_PRIVACY_HINT)}</span>'
                f'<span class="{counter_cls}">{p.format_count(len(text))} / '
                f'{p.format_count(settings.MAX_INPUT_CHARS)}</span></div>')
        long_message = bool(text) and not over and service.is_long_message(text, resources.count_tokens(text))
        if over:
            st.html(f'<p class="cp-note-warn">{c.esc(p.input_problem_message(service.CheckError.TOO_LONG, text) or "")}</p>')
        elif long_message:
            st.html(f'<p class="cp-note-warn">{c.esc(p.LONG_CLAIM_WARNING)}</p>')
        clicked = st.button(p.SUBMIT_LABEL, type="primary", use_container_width=True, icon=":material/search:")
        if resources.warmup_state() is resources.WarmupState.RUNNING:
            st.html(f'<p class="cp-note">{c.esc(p.WARMUP_NOTE)}</p>')

    if long_message and not clicked:
        st.session_state[WARNED_KEY] = text  # peringatan sudah terlihat untuk teks ini
    if clicked:
        st.session_state.pop(NOTICE_KEY, None)
        if long_message and st.session_state.get(WARNED_KEY) != text:
            # Teks panjang masuk bersamaan dengan klik: peringatan baru muncul, jadi pemeriksaan ditunda
            # satu klik agar peringatan terbaca dulu.
            st.session_state[WARNED_KEY] = text
            st.session_state[NOTICE_KEY] = p.LONG_CLAIM_CONFIRM.format(button=p.SUBMIT_LABEL)
        else:
            _run_check(raw or "")
    notice = st.session_state.get(NOTICE_KEY)
    if notice and not over:
        st.html(f'<p class="cp-note-warn">{c.esc(notice)}</p>')

    if p.EXAMPLE_CLAIMS:
        st.html(f'<div class="cp-overline" style="font-size:13px;letter-spacing:0">{c.esc(p.EXAMPLES_HEADING)}</div>')
        with st.container(key="contoh", horizontal=True, wrap=True, gap="small"):  # berjajar bila muat, terbungkus bila tidak
            for i, example in enumerate(p.EXAMPLE_CLAIMS):
                st.button(example, key=f"contoh-{i}", on_click=_use_example, args=(example,), width="content",
                          wrap=True)  # label panjang terbungkus, bukan terpotong elipsis

    steps = "".join(f'<div><span class="cp-num">{i}</span>{c.esc(s)}</div>'
                    for i, s in enumerate(p.HOW_IT_WORKS_STEPS, start=1))
    st.html(f'<div class="cp-stack-12"><div class="cp-overline" style="font-size:13px;letter-spacing:0">'
            f'{c.esc(p.HOW_IT_WORKS_HEADING)}</div><div class="cp-steps-grid">{steps}</div></div>')
    _render_footer()


def _render_footer() -> None:
    stats = c.cached_index_stats()
    st.html(f'<div class="cp-footer"><p class="cp-caption">'
            f'{c.esc(p.footer_archive(stats.article_count, stats.latest_date))}</p></div>')
    st.page_link(c.page("tentang"), label=p.ABOUT_LINK_LABEL)


# -- Hasil ----------------------------------------------------------------------------------------


def _back_button(label: str, keep_text: bool, key: str) -> None:
    st.button(f"‹ {label}", key=key, type="tertiary", on_click=_clear_result, args=(keep_text,))


def _render_found(view: p.ResultView) -> None:
    _back_button(p.CHECK_ANOTHER_LABEL, keep_text=False, key="kembali-atas")
    with st.container(key="kartu-status"):
        show_all = st.session_state.get(SHOW_ALL_KEY, False)
        preview, truncated = p.kesimpulan_preview(view.kesimpulan)
        body = view.kesimpulan if show_all else preview
        st.html(f'<div class="cp-stack-12"><div class="cp-pill-row">{c.pill_html(view.pill_text, view.status_color)}'
                f'<span class="cp-pill-suffix">{c.esc(p.SOURCE_SUFFIX)}</span></div>'
                f'<h1 class="cp-h1-result">{c.esc(view.headline)}</h1>{c.paragraphs_html(body)}</div>')
        if truncated:
            st.button(p.SHOW_LESS_LABEL if show_all else p.SHOW_ALL_LABEL, type="tertiary", key="tampilkan-semua",
                      on_click=lambda: st.session_state.update({SHOW_ALL_KEY: not show_all}))
        if view.advice:
            st.html(f'<p class="cp-advice">{c.esc(view.advice)}</p>')

    with st.container(key="kartu-cek"):
        st.html(f'<div class="cp-stack-12"><div class="cp-warn-title">{c.ICON_ALERT}'
                f'<h2>{c.esc(p.MATCH_CHECK_HEADING)}</h2></div>'
                f'<p class="cp-warn-text">{c.esc(p.MATCH_CHECK_INTRO)}</p><div class="cp-compare">'
                f'<div><div class="cp-overline">{c.esc(p.MATCH_CHECK_YOURS)}</div>'
                f'<div class="cp-quote">“{c.esc(view.message_excerpt)}”</div></div>'
                f'<div><div class="cp-overline">{c.esc(p.MATCH_CHECK_CHECKED)}</div>'
                f'<div class="cp-quote">{c.esc(view.article_title)}</div></div></div></div>')
        n = st.session_state.get(RESULT_COUNTER_KEY, 0)
        with st.container(key="cek-daftar"):  # jarak antar-checkbox dirapatkan (style.css)
            for i, question in enumerate(p.MATCH_CHECK_QUESTIONS):
                st.checkbox(question, key=f"cek-{n}-{i}")  # hanya membantu pengguna; tidak memengaruhi apa pun
        st.html(f'<p class="cp-warn-note">{c.esc(p.MATCH_CHECK_CLOSING)}</p>')

    with st.container(key="kartu-artikel"):
        meta = p.ARTICLE_SOURCE + (f" · {view.article_date}" if view.article_date else "")
        st.html(f'<div class="cp-stack"><div class="cp-overline">{c.esc(p.ARTICLE_HEADING)}</div>'
                f'<div class="cp-article-title">{c.esc(view.article_title)}</div>'
                f'<div class="cp-meta">{c.esc(meta)}</div></div>')
        if view.article_url:
            st.link_button(f"{p.READ_ARTICLE_LABEL} ↗", view.article_url, use_container_width=True)

    if view.penjelasan or view.references:
        with st.container(key="kartu-perluas"):
            if view.penjelasan:
                with st.expander(p.EXPLANATION_LABEL):
                    st.html(c.paragraphs_html(view.penjelasan, "cp-small"))
            if view.references:
                with st.expander(p.REFERENCES_LABEL.format(n=len(view.references))):
                    items = "".join(f"<li>{c.link(url, url)}</li>" for url in view.references)
                    st.html(f'<ol class="cp-refs">{items}</ol>')

    st.html(f'<p class="cp-caption">{c.esc(p.PROVENANCE_NOTE)}</p>')
    st.page_link(c.page("tentang"), label=p.PROVENANCE_LINK_LABEL)


def _render_not_found(view: p.ResultView) -> None:
    _back_button(p.CHECK_ANOTHER_LABEL, keep_text=False, key="kembali-atas")
    with st.container(key="kartu-status"):
        st.html(f'<div class="cp-stack-12"><div class="cp-pill-row">{c.neutral_pill_html(view.pill_text)}</div>'
                f'<h1 class="cp-h1-result">{c.esc(view.headline)}</h1>'
                f'<div class="cp-callout">{c.ICON_INFO}<p>{c.esc(p.NOT_FOUND_CALLOUT)}</p></div>'
                f'<p class="cp-small">{c.esc(p.NOT_FOUND_BODY)}</p></div>')
    with st.container(key="kartu-langkah"):
        st.html(f'<div class="cp-stack-12"><h2 class="cp-h2">{c.esc(p.NEXT_STEPS_HEADING)}</h2>'
                f'{c.numbered_steps_html(p.NEXT_STEPS)}</div>')
        with st.container(key="situs-cek-fakta"):
            for name, url in p.FACT_CHECK_SITES:
                st.link_button(f"{name} ↗", url, use_container_width=True)
    with st.container(key="kartu-tanda"):
        signs = "".join(f"<div>{c.esc(s)}</div>" for s in p.SCAM_SIGNS)
        st.html(f'<div class="cp-stack-12"><h2 class="cp-h2">{c.esc(p.SCAM_SIGNS_HEADING)}</h2>'
                f'<div class="cp-signs">{signs}</div></div>')
    st.button(p.CHECK_ANOTHER_LABEL, type="primary", use_container_width=True, key="kembali-bawah",
              on_click=_clear_result, args=(False,))


def _render_failed(view: p.ResultView) -> None:
    _back_button(p.BACK_LABEL, keep_text=True, key="kembali-atas")
    with st.container(key="kartu-gagal"):
        st.html(f'<div class="cp-stack-12"><h1 class="cp-h1-result">{c.esc(view.failure_title)}</h1>'
                f'<p class="cp-small">{c.esc(view.failure_body)}</p></div>')
    st.button(p.BACK_LABEL, type="primary", use_container_width=True, key="kembali-bawah",
              on_click=_clear_result, args=(True,))


def _render_diagnostics(diag: p.Diagnostics) -> None:
    """Panel penguji (hanya bila mode penguji aktif), tertutup. Istilah teknis hanya di sini."""
    with st.expander(p.DIAGNOSTICS_LABEL, expanded=False):
        st.json({
            "model": diag.model, "waktu_dtk": {k: round(v, 3) for k, v in diag.timings.items()},
            "panggilan_llm": diag.llm_calls, "percobaan_http": diag.attempts,
            "token_llm": {"masuk": diag.input_tokens, "keluar": diag.output_tokens},
            "token_klaim_retrieval": diag.query_tokens, "batas_token": diag.query_token_limit,
            "kandidat": [vars(row) for row in diag.candidates],
            "alasan_llm": diag.llm_reason, "parafrase_llm": diag.llm_paraphrase,
            "jenis_kegagalan": diag.failure_kind, "galat": diag.error_detail,
            "gagal_parse": diag.parse_failures, "id_tidak_sah": diag.invalid_id,
            "url_llm_dibuang": diag.llm_urls_removed,
        })


def render() -> None:
    """Gambar beranda atau hasil terakhir sesi ini."""
    c.load_css()
    view: p.ResultView | None = st.session_state.get(RESULT_KEY)
    if view is None:
        _render_home()
        return
    {"found": _render_found, "not_found": _render_not_found, "failed": _render_failed}[view.kind](view)
    if c.tester_mode_enabled():
        _render_diagnostics(view.diagnostics)

