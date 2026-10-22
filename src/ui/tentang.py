"""Halaman "Tentang sistem ini": cara kerja, angka evaluasi (dihitung dari berkas hasil), batasan, sumber data."""

import streamlit as st

import presentation as p
import settings
from evaluation_facts import external_evaluation
from ui import components as c


def render() -> None:
    c.load_css()
    st.page_link(c.page("beranda"), label=f"‹ {p.BACK_LABEL}")
    st.html(f'<h1 class="cp-h1">{c.esc(p.ABOUT_TITLE)}</h1>')
    st.html(f'<div class="cp-two"><div><div class="cp-overline">{c.esc(p.ABOUT_DOES_HEADING)}</div>'
            f'<div class="cp-text">{c.esc(p.ABOUT_DOES)}</div></div>'
            f'<div><div class="cp-overline">{c.esc(p.ABOUT_DOES_NOT_HEADING)}</div>'
            f'<div class="cp-text">{c.esc(p.ABOUT_DOES_NOT)}</div></div></div>')

    stats = c.cached_index_stats()
    current = p.format_count(stats.article_count) if stats.article_count else p.UNKNOWN_VALUE
    with st.container(key="kartu-tentang-cara"):
        steps = (p.ABOUT_STEPS[0].format(articles=current),) + p.ABOUT_STEPS[1:]
        st.html(f'<div class="cp-stack-12"><h2 class="cp-h2">{c.esc(p.HOW_IT_WORKS_HEADING)}</h2>'
                f'{c.numbered_steps_html(steps)}</div>')

    ev = external_evaluation()
    found, false = ev.found_correctly, ev.false_matches
    with st.container(key="kartu-tentang-andal"):
        st.html(
            f'<div class="cp-stack-12"><h2 class="cp-h2">{c.esc(p.RELIABILITY_HEADING)}</h2>'
            f'<p class="cp-small">{c.esc(p.RELIABILITY_INTRO.format(total=ev.total_items))}</p>'
            f'<div class="cp-figure"><div class="cp-number">{found.k} dari {found.n}</div>'
            f'<div class="cp-text">{c.esc(p.RELIABILITY_FOUND.format(pct=p.format_percent(found.rate), category=ev.positive_category.capitalize()))}</div></div>'
            f'<div class="cp-figure"><div class="cp-number">{false.k} dari {false.n}</div>'
            f'<div class="cp-text">{c.esc(p.RELIABILITY_FALSE.format(pct=p.format_percent(false.rate), category=ev.false_match_category.capitalize()))}</div></div>'
            f'<p class="cp-advice" style="font-size:14px">{c.esc(p.RELIABILITY_ADVICE)}</p>'
            f'<p class="cp-caption">{c.esc(p.RELIABILITY_FOOTNOTE.format(articles=p.format_count(ev.index_articles)))}</p></div>')

    with st.container(key="kartu-tentang-batas"):
        st.html(f'<div class="cp-stack-12"><h2 class="cp-h2">{c.esc(p.LIMITS_HEADING)}</h2>'
                f'{c.bullets_html(p.LIMITS)}</div>')

    st.html(f'<div class="cp-stack"><h2 class="cp-h2" style="font-size:14px">{c.esc(p.DATA_SOURCE_HEADING)}</h2>'
            f'<p class="cp-caption" style="font-size:13px">'
            f'{c.esc(p.DATA_SOURCE_BODY.format(date=p.format_date(stats.latest_date)))}</p>'
            f'<p class="cp-caption" style="font-size:13px;font-weight:600">'
            f'{c.link(settings.SOURCE_CODE_URL, p.SOURCE_CODE_LABEL)}</p></div>')
