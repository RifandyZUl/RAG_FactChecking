"""Uji lapisan tampilan dengan streamlit.testing (offline: pemanasan dimatikan, hasil disuntikkan ke sesi).

Yang dijaga: teks dinamis (pesan, judul, Kesimpulan, Penjelasan, label) selalu di-escape, tautan hanya
http/https, dan mode penguji tidak bisa dinyalakan dari luar (parameter URL).
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import presentation as p
import resources
from ui import components as c

APP = str(Path(__file__).resolve().parent.parent / "src" / "app.py")
XSS = '<script>alert("x")</script><img src=x onerror=alert(1)>'


@pytest.fixture(autouse=True)
def _no_warmup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resources, "start_warmup", lambda *a, **k: False)
    monkeypatch.delenv("DEMO_TESTER_MODE", raising=False)


def _found_view(**kw: object) -> p.ResultView:
    base: dict = {"kind": "found", "status_color": "red", "pill_text": f"PENIPUAN{XSS}", "headline": "Judul tetap.",
                  "kesimpulan": f"Kesimpulan {XSS}", "advice": "Saran.", "message_excerpt": f"pesan {XSS}",
                  "article_title": f"Judul {XSS}", "article_url": "https://turnbackhoax.id/articles/1-x",
                  "article_date": "1 Januari 2026", "penjelasan": f"Penjelasan {XSS}",
                  "references": ["https://www.kemkes.go.id/a", "javascript:alert(1)"]}
    base.update(kw)
    return p.ResultView(**base)


def _bodies(at: AppTest) -> str:
    """Isi HTML mentah semua blok st.html di halaman (sebelum disanitasi browser)."""
    return "\n".join(el.proto.body for el in at.get("html"))


def _run(view: p.ResultView | None = None, query: dict | None = None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    if view is not None:
        at.session_state["hasil"] = view
    for key, value in (query or {}).items():
        at.query_params[key] = value
    return at.run()


def test_found_page_escapes_every_dynamic_text() -> None:
    at = _run(_found_view())
    assert not at.exception
    html = _bodies(at)
    assert "<script>" not in html and "<img src=x" not in html
    assert "&lt;script&gt;" in html, "teks dinamis tampil sebagai teks, bukan dieksekusi"


def test_only_http_links_are_rendered() -> None:
    html = _bodies(_run(_found_view()))
    assert 'href="javascript:' not in html
    assert 'href="https://www.kemkes.go.id/a"' in html


def test_link_helper_refuses_unsafe_schemes() -> None:
    assert c.link("javascript:alert(1)", "klik") == "klik"
    assert c.link('https://x.org/"><script>', "a").count("<script>") == 0


def test_tester_panel_cannot_be_enabled_from_the_url() -> None:
    at = _run(_found_view(), query={"demo_tester_mode": "1", "DEMO_TESTER_MODE": "1"})
    assert not [e for e in at.expander if e.label == p.DIAGNOSTICS_LABEL]


def test_tester_panel_appears_only_with_the_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_TESTER_MODE", "1")
    at = _run(_found_view())
    assert [e for e in at.expander if e.label == p.DIAGNOSTICS_LABEL]


def test_home_renders_without_calling_the_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Memuat (dan memuat ulang) beranda tidak pernah membuat penyedia LLM, apalagi memanggilnya."""
    def boom() -> None:
        raise AssertionError("LLM tidak boleh disentuh saat halaman dimuat")

    monkeypatch.setattr(c, "cached_provider", boom)
    at = _run()
    at.run()
    assert not at.exception
    assert any(b.label == p.SUBMIT_LABEL for b in at.button)


def test_example_button_fills_the_input() -> None:
    at = _run()
    at.button(key="contoh-0").click().run()
    assert at.text_area(key="pesan").value == p.EXAMPLE_CLAIMS[0]
