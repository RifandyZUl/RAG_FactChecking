"""Uji penyiapan data tampilan demo (offline: hasil layanan tiruan, tanpa API, tanpa model)."""

import logging
import re

import pytest

from generator import MAX_FORMAT_RETRIES, Answer
from llm import CallRecord
from retriever import ArticleHit
from webapp import settings
from webapp.presentation import (
    EMPTY_INPUT_MESSAGE,
    FAILURE_MESSAGES,
    NOT_FOUND_PILL,
    STATUS_STYLES,
    FailureKind,
    build_view,
    classify_call_error,
    classify_failure,
    display_references,
    display_title,
    excerpt,
    format_date,
    format_metadata_date,
    input_problem_message,
    is_safe_url,
    kesimpulan_preview,
    status_style_key,
)
from webapp.service import CheckError, CheckOutcome

REFS = ["https://www.kemkes.go.id/rilis", "https://cekfakta.example.org/a"]
CANDIDATES = [
    {"article_id": "36214", "title": "[SALAH] Vaksin HPV Bikin Impoten", "label": "SALAH", "score": 0.6671},
    {"article_id": "36577", "title": "[SALAH] Cacar Air", "label": "SALAH", "score": 0.61},
]
KESIMPULAN = "Faktanya, klaim vaksin HPV bikin impoten tidak benar menurut Kemenkes."


def _ok_call() -> CallRecord:
    return CallRecord("gemini", "gemini-3.5-flash-lite", 3.0, True, 1, input_tokens=1800, output_tokens=120)


def _hit(article_id: str = "36214", kesimpulan: str = KESIMPULAN, date: str = "14/08/2026") -> ArticleHit:
    return ArticleHit(article_id=article_id, title="[SALAH] Vaksin HPV Bikin Impoten",
                      url=f"https://turnbackhoax.id/articles/{article_id}-x", label="SALAH", score=0.66,
                      best_section="narasi", references=list(REFS), date=date, kesimpulan=kesimpulan)


def _found_answer(label: str = "SALAH", **kw: object) -> Answer:
    base: dict = {
        "claim": "klaim", "verdict": "ditemukan", "status_label": label, "article_id": "36214",
        "title": f"[{label}] Vaksin HPV Bikin Impoten",
        "article_url": "https://turnbackhoax.id/articles/36214-x",
        "klarifikasi": "PARAFRASE LLM yang tidak boleh tampil ke pengguna umum.", "alasan": "Klaim sama.",
        "references": list(REFS), "candidates": list(CANDIDATES), "calls": [_ok_call()],
    }
    base.update(kw)
    return Answer(**base)


def _outcome(answer: Answer | None = None, **kw: object) -> CheckOutcome:
    base: dict = {"message": "vaksin hpv bikin anak cowok impoten katanya", "answer": answer,
                  "hits": [_hit()], "penjelasan": "Penelusuran tim.\n\nParagraf kedua.", "model": "m"}
    base.update(kw)
    return CheckOutcome(**base)


# -- ditemukan -----------------------------------------------------------------


@pytest.mark.parametrize("label", ["PENIPUAN", "SALAH", "PARODI", "BELUM TERBUKTI"])
def test_found_uses_label_from_metadata_with_fixed_headline_and_advice(label: str) -> None:
    view = build_view(_outcome(_found_answer(label)))
    style = STATUS_STYLES[label]
    assert view.kind == "found" and view.pill_text == label
    assert (view.status_color, view.headline, view.advice) == (style.color, style.headline, style.advice)


def test_found_shows_turnbackhoax_kesimpulan_as_is_and_llm_paraphrase_only_in_diagnostics() -> None:
    view = build_view(_outcome(_found_answer()))
    assert view.kesimpulan == KESIMPULAN
    assert "PARAFRASE" not in view.kesimpulan + view.headline + view.advice
    assert view.diagnostics.llm_paraphrase.startswith("PARAFRASE")


def test_penipuan_advice_is_the_sentence_set_by_the_owner() -> None:
    assert STATUS_STYLES["PENIPUAN"].advice == "Jangan klik tautannya, jangan isi formulirnya, dan jangan teruskan pesannya."


def test_belum_terbukti_keeps_the_exact_sentence_from_2026_10_03() -> None:
    assert STATUS_STYLES["BELUM TERBUKTI"].advice == (
        "Klaim ini sudah diperiksa TurnBackHoax.id dan belum ada bukti yang mendukungnya, "
        "sehingga belum dapat dianggap benar.")
    assert STATUS_STYLES["BELUM TERBUKTI"].color == "violet"


@pytest.mark.parametrize("label", ["SATIRE", "SATIR", "KOMEDI", "parodi"])
def test_humor_labels_use_parodi_style_but_pill_shows_original_label(label: str) -> None:
    view = build_view(_outcome(_found_answer(label)))
    assert status_style_key(label) == "PARODI"
    assert view.status_color == "yellow" and view.pill_text == label.upper()


def test_status_colors_are_distinct_and_never_green() -> None:
    colors = [s.color for s in STATUS_STYLES.values()]
    assert len(set(colors)) == len(colors) and "green" not in colors


def test_unknown_label_is_neutral_quoted_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="presentation"):
        view = build_view(_outcome(_found_answer("HOAKS BARU")))
    assert view.status_color == "gray" and view.pill_text == "HOAKS BARU"
    assert "“HOAKS BARU”" in view.headline and "salah" not in view.headline.lower()
    assert "HOAKS BARU" in caplog.text and "36214" in caplog.text


@pytest.mark.parametrize("label", ["", "TIDAK DIKETAHUI"])
def test_unreadable_label_is_not_quoted(label: str) -> None:
    view = build_view(_outcome(_found_answer(label)))
    assert view.pill_text == "SUDAH DIPERIKSA" and "TIDAK DIKETAHUI" not in view.headline


def test_found_carries_article_card_fields_from_metadata() -> None:
    view = build_view(_outcome(_found_answer()))
    assert view.article_title == "Vaksin HPV Bikin Impoten"
    assert view.article_url == "https://turnbackhoax.id/articles/36214-x"
    assert view.article_date == "14 Agustus 2026"
    assert view.penjelasan.startswith("Penelusuran tim.")
    assert view.message_excerpt == "vaksin hpv bikin anak cowok impoten katanya"


def test_references_come_only_from_metadata_and_never_from_llm_output() -> None:
    ans = _found_answer(klarifikasi="lihat https://jahat.example/x", alasan="www.jahat.example")
    view = build_view(_outcome(ans))
    assert view.references == REFS


def test_claim_sources_and_filtered_links_never_reach_the_view() -> None:
    """Metadata indeks hanya membawa `references`; tautan terblokir yang lolos ke metadata tetap disaring."""
    blocked = ["https://www.facebook.com/hoaks/posts/1", "https://bit.ly/abc", "https://archive.fo/x"]
    view = build_view(_outcome(_found_answer(references=[*REFS, *blocked])))
    assert view.references == REFS


@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,<b>x</b>", "file:///etc/passwd", "//x.org"])
def test_unsafe_url_schemes_are_never_linked(url: str) -> None:
    assert not is_safe_url(url)
    assert display_references([url]) == []
    assert build_view(_outcome(_found_answer(article_url=url))).article_url == ""


def test_display_filter_uses_the_same_policy_as_the_parser(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="presentation"):
        assert display_references(["https://tinyurl.com/kode-rahasia", REFS[0]], "1") == [REFS[0]]
    assert "kode-rahasia" not in caplog.text, "log mencatat alasan (domain) dan id artikel, bukan tautan lengkapnya"


# -- belum ditemukan dan kegagalan ----------------------------------------------


def test_not_found_is_neutral_and_llm_reason_only_in_diagnostics() -> None:
    ans = Answer(claim="k", verdict="tidak_ditemukan", alasan="Unsur inti berbeda.", candidates=list(CANDIDATES),
                 calls=[_ok_call()])
    view = build_view(_outcome(ans))
    assert view.kind == "not_found" and view.pill_text == NOT_FOUND_PILL
    assert "Unsur inti" not in view.headline and view.diagnostics.llm_reason == "Unsur inti berbeda."
    assert view.references == [] and view.kesimpulan == ""


@pytest.mark.parametrize(("error", "kind"), [
    (CheckError.SESSION_INTERVAL, FailureKind.RATE_LIMITED), (CheckError.SESSION_HOURLY, FailureKind.RATE_LIMITED),
    (CheckError.GLOBAL_HOURLY, FailureKind.RATE_LIMITED), (CheckError.DAILY_STOP, FailureKind.QUOTA),
    (CheckError.BUSY, FailureKind.BUSY), (CheckError.NO_INDEX, FailureKind.NO_INDEX),
    (CheckError.CONFIG, FailureKind.CONFIG), (CheckError.UNEXPECTED, FailureKind.OTHER),
])
def test_service_errors_map_to_plain_language_failures(error: CheckError, kind: FailureKind) -> None:
    view = build_view(_outcome(None, error=error, retry_after_s=42, error_detail="RuntimeError: rinci"))
    assert view.kind == "failed" and view.failure_title == FAILURE_MESSAGES[kind][0]
    assert "RuntimeError" not in view.failure_body and "{wait}" not in view.failure_body
    assert view.diagnostics.error_detail == "RuntimeError: rinci"


def test_rate_limit_message_states_the_wait_in_plain_words() -> None:
    assert "42 detik" in build_view(_outcome(None, error=CheckError.SESSION_INTERVAL, retry_after_s=42)).failure_body
    assert "3 menit" in build_view(_outcome(None, error=CheckError.GLOBAL_HOURLY, retry_after_s=150)).failure_body


@pytest.mark.parametrize("kind", list(FailureKind))
def test_every_failure_message_says_what_to_do_without_technical_terms(kind: FailureKind) -> None:
    title, body = FAILURE_MESSAGES[kind]
    assert title and body
    words = set(re.findall(r"[\w=]+", (title + body).lower()))
    assert not words & {"http", "api", "exception", "traceback", "status=", "error", "galat"}


@pytest.mark.parametrize(("error", "expected"), [
    ("APITimeoutError status=None", FailureKind.TIMEOUT), ("InternalServerError status=503", FailureKind.UNAVAILABLE),
    ("APIConnectionError status=None", FailureKind.UNAVAILABLE), ("BadRequest status=400", None), ("format baru", None),
])
def test_classify_call_error(error: str, expected: FailureKind | None) -> None:
    assert classify_call_error(error) == expected


def test_classify_failure_order() -> None:
    failed = CallRecord("gemini", "m", 1.0, False, 3, error="InternalServerError status=503")
    assert classify_failure(Answer(claim="k", verdict="gagal", quota_exhausted=True, calls=[failed])) is FailureKind.QUOTA
    assert classify_failure(Answer(claim="k", verdict="gagal", calls=[failed])) is FailureKind.UNAVAILABLE
    assert classify_failure(Answer(claim="k", verdict="gagal", parse_failures=1 + MAX_FORMAT_RETRIES)) is FailureKind.PARSE
    assert classify_failure(_found_answer()) is None


def test_input_problem_messages() -> None:
    assert input_problem_message(CheckError.EMPTY, "") == EMPTY_INPUT_MESSAGE
    msg = input_problem_message(CheckError.TOO_LONG, "x" * 2001)
    assert msg is not None and "2.001" in msg and "1.500" in msg
    assert input_problem_message(CheckError.BUSY, "x") is None


# -- format ---------------------------------------------------------------------


def test_display_title_strips_label_prefix() -> None:
    assert display_title("[SALAH] Judul") == "Judul" and display_title("Tanpa label") == "Tanpa label"


def test_kesimpulan_preview_cuts_at_sentence_or_word() -> None:
    short = "Satu kalimat."
    assert kesimpulan_preview(short) == (short, False)
    long_text = "Kalimat pertama cukup panjang. " * 20
    preview, cut = kesimpulan_preview(long_text)
    assert cut and preview.endswith(".") and len(preview) <= settings.KESIMPULAN_PREVIEW_CHARS


def test_excerpt_flattens_whitespace_and_cuts_on_word_boundary() -> None:
    assert excerpt("a  b\n\nc", 50) == "a b c"
    assert excerpt("satu dua tiga empat", 10) == "satu dua…"


def test_dates_in_indonesian() -> None:
    assert format_metadata_date("09/09/2026") == "9 September 2026"
    assert format_metadata_date("bukan tanggal") == "bukan tanggal"
    assert format_date(None) == "(tidak terbaca)"


def test_every_headline_follows_one_pattern() -> None:
    from webapp.presentation import FALLBACK_HEADLINE, UNREADABLE_HEADLINE

    headlines = [s.headline for s in STATUS_STYLES.values()] + [FALLBACK_HEADLINE, UNREADABLE_HEADLINE]
    assert all(h.startswith("Klaim serupa pernah diperiksa dan ") for h in headlines)
    assert "humor, bukan berita sungguhan" not in STATUS_STYLES["PARODI"].headline
    assert "bukan berita sungguhan" in STATUS_STYLES["PARODI"].advice


def test_about_numbers_are_not_swapped() -> None:
    from webapp.presentation import about_steps, footer_archive, reliability_footnote

    assert "2.000 artikel" in about_steps(2000)[0] and "1.532" not in about_steps(2000)[0]
    assert reliability_footnote(1532).startswith("Angka berlaku untuk arsip 1.532 artikel")
    assert "artikel terbaru" in footer_archive(2000, None) and "diperbarui" not in footer_archive(2000, None)
