"""Uji penyiapan data tampilan demo (offline: `Answer` tiruan, tanpa API, tanpa model)."""

import re
from pathlib import Path

import pytest

from generator import MAX_FORMAT_RETRIES, Answer
from llm import CallRecord
from presentation import (
    EMPTY_INPUT_MESSAGE,
    FAILURE_MESSAGES,
    MAX_INPUT_CHARS,
    NOT_FOUND_STYLE,
    RELATED_NOTE,
    RELATED_SCORE_THRESHOLD,
    SCAM_ADVICE,
    STATUS_STYLES,
    FailureKind,
    RelatedArticle,
    build_view,
    classify_call_error,
    classify_failure,
    display_title,
    escape_markdown,
    failure_view,
    markdown_link,
    parse_flag,
    related_articles,
    validate_claim,
)

ROOT = Path(__file__).resolve().parent.parent

REFS = ["https://www.kemkes.go.id/rilis", "https://cekfakta.example.org/a"]
CANDIDATES = [
    {"article_id": "36214", "title": "[SALAH] Vaksin HPV Bikin Impoten", "label": "SALAH", "score": 0.6671},
    {"article_id": "36577", "title": "[SALAH] Cacar Air", "label": "SALAH", "score": 0.61},
    {"article_id": "36053", "title": "[PENIPUAN] Link Bantuan", "label": "PENIPUAN", "score": 0.59},
]


def _ok_call(latency: float = 3.0, tokens_in: int | None = 1800, tokens_out: int | None = 120) -> CallRecord:
    return CallRecord("gemini", "gemini-3.5-flash-lite", latency, True, 1,
                      input_tokens=tokens_in, output_tokens=tokens_out)


def _failed_call(error: str) -> CallRecord:
    return CallRecord("gemini", "gemini-3.5-flash-lite", 90.0, False, 3, error=error)


def _found(label: str = "SALAH", **kw: object) -> Answer:
    base: dict = {
        "claim": "klaim", "verdict": "ditemukan", "status_label": label, "article_id": "36214",
        "title": f"[{label}] Judul Artikel",
        "article_url": "https://turnbackhoax.id/articles/36214-judul",
        "klarifikasi": "Faktanya, klaim itu tidak benar.", "alasan": "Klaim sama dengan judul.",
        "references": list(REFS), "candidates": list(CANDIDATES), "calls": [_ok_call()],
    }
    base.update(kw)
    return Answer(**base)


def _failed(**kw: object) -> Answer:
    base: dict = {"claim": "klaim", "verdict": "gagal", "candidates": list(CANDIDATES)}
    base.update(kw)
    return Answer(**base)


# -- status ditemukan -------------------------------------------------------

@pytest.mark.parametrize("label", ["SALAH", "PENIPUAN", "PARODI"])
def test_found_uses_status_style_from_metadata_label(label: str) -> None:
    view = build_view(_found(label), model="m")
    style = STATUS_STYLES[label]
    assert view.kind == "found"
    assert (view.status_label, view.status_color, view.status_icon, view.summary) == (
        style.label, style.color, style.icon, style.summary)
    assert view.article_title == "Judul Artikel"  # label dalam kurung siku dibuang
    assert view.clarification == "Faktanya, klaim itu tidak benar."
    assert view.references == REFS


def test_status_colors_are_distinct_and_never_success_green() -> None:
    colors = [s.color for s in STATUS_STYLES.values()] + [NOT_FOUND_STYLE.color]
    assert len(set(colors)) == len(colors)
    assert "green" not in colors and "blue" not in colors
    assert NOT_FOUND_STYLE.color == "gray"


def test_scam_advice_only_for_penipuan_and_always_identical() -> None:
    a = build_view(_found("PENIPUAN", klarifikasi="Faktanya A", title="[PENIPUAN] Link X"))
    b = build_view(_found("PENIPUAN", klarifikasi="Faktanya B", title="[PENIPUAN] Link Y"))
    assert a.advice == b.advice == SCAM_ADVICE
    assert SCAM_ADVICE not in a.clarification  # terpisah dari klarifikasi
    assert build_view(_found("SALAH")).advice == ""
    assert build_view(_found("PARODI")).advice == ""


def test_unknown_label_falls_back_without_crashing() -> None:
    view = build_view(_found("MENYESATKAN"))
    assert view.kind == "found"
    assert view.status_label == "Menyesatkan"
    assert view.status_color == STATUS_STYLES["SALAH"].color
    assert "MENYESATKAN" in view.summary
    assert view.advice == ""


def test_article_without_references_has_empty_reference_list() -> None:
    assert build_view(_found(references=[])).references == []


def test_claim_sources_never_leak_into_view() -> None:
    """Aturan Wajib #1: hanya `references` yang tampil; tautan hoaks tidak ada di Answer maupun view."""
    hoax_link = "https://www.facebook.com/penyebar/posts/1"
    view = build_view(_found())
    assert hoax_link not in repr(view)
    assert set(view.references) == set(REFS)


# -- belum ditemukan --------------------------------------------------------

def test_not_found_is_neutral_and_llm_reason_only_in_diagnostics() -> None:
    ans = Answer(claim="vaksin flu bikin mandul", verdict="tidak_ditemukan",
                 alasan="Berbeda dari artikel vaksin HPV 36214.",
                 candidates=list(CANDIDATES), calls=[_ok_call()])
    view = build_view(ans)
    assert view.kind == "not_found"
    assert view.status_color == "gray"
    assert "tidak berarti klaimnya benar" in view.summary
    assert "36214" not in view.summary and view.clarification == "" and view.references == []
    assert view.diagnostics.llm_reason == "Berbeda dari artikel vaksin HPV 36214."


def test_main_copy_has_no_technical_terms() -> None:
    views = [build_view(_found(label)) for label in STATUS_STYLES] + [
        build_view(Answer(claim="x", verdict="tidak_ditemukan"))]
    texts = [v.summary for v in views] + [body for _, body in FAILURE_MESSAGES.values()]
    for text in texts:
        for term in ("retrieval", "chunk", "skor", "embedding", "LLM", "API", "token"):
            assert term.lower() not in text.lower(), (term, text)


# -- klasifikasi galat ------------------------------------------------------

@pytest.mark.parametrize(("error", "expected"), [
    ("APITimeoutError status=None", FailureKind.TIMEOUT),
    ("ReadTimeout status=None", FailureKind.TIMEOUT),
    ("ServerError status=503", FailureKind.UNAVAILABLE),
    ("ServerError status=500", FailureKind.UNAVAILABLE),
    ("ClientError status=429 jenis=per_menit", FailureKind.UNAVAILABLE),
    ("APIConnectionError status=None", FailureKind.UNAVAILABLE),
    ("ClientError status=403", None),
    ("status=incomplete teks_kosong=True", None),
    ("anggaran-lokal-habis", None),
    ("format baru yang tidak dikenal", None),
])
def test_classify_call_error(error: str, expected: FailureKind | None) -> None:
    assert classify_call_error(error) is expected


def test_quota_flag_wins_over_call_error() -> None:
    ans = _failed(quota_exhausted=True, error="Kuota habis",
                  calls=[_failed_call("ClientError status=429 jenis=harian kuota-habis")])
    assert classify_failure(ans) is FailureKind.QUOTA


def test_timeout_and_unavailable_from_last_failed_call() -> None:
    timeout = _failed(error="x", calls=[_failed_call("APITimeoutError status=None")])
    down = _failed(error="x", calls=[_failed_call("ServerError status=503")])
    assert classify_failure(timeout) is FailureKind.TIMEOUT
    assert classify_failure(down) is FailureKind.UNAVAILABLE


def test_parse_failure_when_all_format_attempts_fail_without_call_error() -> None:
    ans = _failed(error="Keluaran LLM tidak sesuai format terstruktur setelah percobaan ulang.",
                  parse_failures=1 + MAX_FORMAT_RETRIES,
                  calls=[_ok_call() for _ in range(1 + MAX_FORMAT_RETRIES)])
    assert classify_failure(ans) is FailureKind.PARSE


def test_changed_error_format_falls_back_to_general_message() -> None:
    ans = _failed(error="x", calls=[_failed_call("TimeoutBaru: kode 503")])
    assert classify_failure(ans) is FailureKind.OTHER
    assert classify_failure(_failed(error="tak dikenal")) is FailureKind.OTHER


def test_non_failures_have_no_failure_kind() -> None:
    assert classify_failure(_found()) is None
    assert classify_failure(Answer(claim="x", verdict="tidak_ditemukan")) is None


def test_provider_error_format_still_matches_classifier() -> None:
    """Pengunci: bila format CallRecord.error di gemini.py berubah, uji ini mengingatkan."""
    source = (ROOT / "src" / "llm" / "gemini.py").read_text(encoding="utf-8")
    assert 'f"{type(e).__name__} status={status}"' in source
    assert "Timeout" in source and "_RETRYABLE_STATUS = {429, 500, 502, 503, 504}" in source


@pytest.mark.parametrize("kind", list(FailureKind))
def test_every_failure_kind_has_message_with_action(kind: FailureKind) -> None:
    title, body = FAILURE_MESSAGES[kind]
    view = failure_view(kind)
    assert view.kind == "failed" and view.status_color == "gray"
    assert (view.status_label, view.summary) == (title, body)
    assert view.diagnostics.failure_kind == kind.value
    assert re.search(r"coba|perlu", body), "pesan wajib menyebut apa yang bisa dilakukan"


def test_failed_answer_view_carries_redacted_error_only_in_diagnostics() -> None:
    ans = _failed(error="Panggilan gemini gagal ([KUNCI-DISAMARKAN])",
                  calls=[_failed_call("ServerError status=503")])
    view = build_view(ans, model="gemini-3.5-flash-lite")
    assert view.kind == "failed"
    assert "KUNCI" not in view.summary
    assert view.diagnostics.error_detail.startswith("Panggilan gemini gagal")
    assert view.diagnostics.model == "gemini-3.5-flash-lite"


# -- diagnostik ---------------------------------------------------------------

def test_diagnostics_aggregate_calls_and_candidates() -> None:
    ans = _found(calls=[_ok_call(2.0, 1000, 50), _ok_call(1.5, None, 30)],
                 parse_failures=1, llm_urls_found=["http://x.id"], klarifikasi_fallback=True)
    d = build_view(ans, model="m").diagnostics
    assert d.latency_s == pytest.approx(3.5)
    assert (d.llm_calls, d.attempts, d.input_tokens, d.output_tokens) == (2, 2, 1000, 80)
    assert [c.article_id for c in d.candidates] == ["36214", "36577", "36053"]
    assert d.candidates[0].score == pytest.approx(0.6671)
    assert (d.parse_failures, d.llm_urls_removed, d.clarification_fallback) == (1, 1, True)


def test_tokens_none_when_not_recorded() -> None:
    d = build_view(_found(calls=[_ok_call(tokens_in=None, tokens_out=None)])).diagnostics
    assert d.input_tokens is None and d.output_tokens is None


# -- Markdown ---------------------------------------------------------------

def test_display_title_strips_label_prefix() -> None:
    assert display_title("[SALAH] Malaysia Laporkan Indonesia ke PBB") == "Malaysia Laporkan Indonesia ke PBB"
    assert display_title("Tanpa label") == "Tanpa label"
    assert display_title("[SALAH]") == "[SALAH]"


def test_escape_markdown_neutralizes_latex_links_and_directives() -> None:
    text = "Harga $5 dan $10 *murah* [klik](http://x) :red[a] :material/home:"
    escaped = escape_markdown(text)
    assert not re.search(r"(?<!\\)[$*\[\]():]", escaped)
    assert escaped.replace("\\", "") == text


def test_markdown_link_escapes_text_and_encodes_url() -> None:
    link = markdown_link("Judul [x]", "https://a.id/p (1)")
    assert link == r"[Judul \[x\]](https://a.id/p%20%281%29)"


# -- "belum ditemukan": artikel mungkin terkait ------------------------------

URLS = {
    "36214": "https://turnbackhoax.id/articles/36214-salah-vaksin-hpv",
    "36577": "https://turnbackhoax.id/articles/36577-salah-cacar-air",
    "36053": "https://turnbackhoax.id/articles/36053-link-bantuan",
}


def test_related_articles_filtered_by_threshold_sorted_and_without_scores() -> None:
    cands = [
        {"article_id": "36577", "title": "[SALAH] Cacar Air", "label": "SALAH", "score": 0.61},
        {"article_id": "36053", "title": "Link", "label": "PENIPUAN", "score": RELATED_SCORE_THRESHOLD - 0.001},
        {"article_id": "36214", "title": "[SALAH] Vaksin HPV", "label": "SALAH", "score": 0.6671},
    ]
    related = related_articles(cands, URLS)
    assert related == [
        RelatedArticle("Vaksin HPV", URLS["36214"]),
        RelatedArticle("Cacar Air", URLS["36577"]),
    ]
    assert "0.6" not in repr(related)  # skor tidak dibawa ke tampilan


def test_threshold_is_inclusive_and_candidates_without_url_are_skipped() -> None:
    cands = [{"article_id": "1", "title": "A", "label": "SALAH", "score": RELATED_SCORE_THRESHOLD},
             {"article_id": "2", "title": "B", "label": "SALAH", "score": 0.9}]
    assert related_articles(cands, {"1": "https://turnbackhoax.id/articles/1-a"}) == [
        RelatedArticle("A", "https://turnbackhoax.id/articles/1-a")]


def test_threshold_value_documented_basis() -> None:
    """Ambang 0,57 dari sebaran skor evaluasi v1 (lihat komentar di presentation.py)."""
    assert RELATED_SCORE_THRESHOLD == 0.57
    assert RELATED_SCORE_THRESHOLD > 0.5680  # skor kandidat tertinggi negatif mudah v1
    assert RELATED_SCORE_THRESHOLD < 0.5739  # 36729 pada "malaysia marah soal asap" (set pengembangan)


def test_not_found_view_lists_related_but_keeps_neutral_verdict() -> None:
    ans = Answer(claim="vaksin flu bikin mandul", verdict="tidak_ditemukan",
                 candidates=list(CANDIDATES), calls=[_ok_call()])
    view = build_view(ans, article_urls=URLS)
    assert view.kind == "not_found" and view.status_color == "gray"
    assert [a.url for a in view.related] == [URLS["36214"], URLS["36577"], URLS["36053"]]
    assert view.references == [] and view.clarification == ""
    assert "tidak sama" in RELATED_NOTE


def test_related_only_for_not_found() -> None:
    assert build_view(_found(), article_urls=URLS).related == []
    failed = _failed(error="x", calls=[_failed_call("ServerError status=503")])
    assert build_view(failed, article_urls=URLS).related == []


def test_not_found_without_urls_shows_no_related() -> None:
    ans = Answer(claim="x", verdict="tidak_ditemukan", candidates=list(CANDIDATES))
    assert build_view(ans).related == []


# -- masukan dan setelan -----------------------------------------------------

def test_validate_claim_limits() -> None:
    assert MAX_INPUT_CHARS == 5000
    assert validate_claim("   ") == EMPTY_INPUT_MESSAGE
    assert validate_claim("a" * MAX_INPUT_CHARS) is None
    message = validate_claim("a" * (MAX_INPUT_CHARS + 1))
    assert message is not None
    assert "5.001" in message and "5.000" in message and "tidak ada bagian yang dipotong" in message


def test_validate_claim_counts_after_trimming_whitespace() -> None:
    assert validate_claim("  " + "a" * MAX_INPUT_CHARS + "  ") is None


@pytest.mark.parametrize(("value", "expected"), [
    (None, False), ("", False), ("0", False), ("false", False), ("tidak", False),
    ("1", True), ("true", True), ("TRUE", True), (" ya ", True), ("on", True),
    (True, True), (False, False), (1, True), (0, False),
])
def test_parse_flag(value: object, expected: bool) -> None:
    assert parse_flag(value) is expected


def test_query_token_diagnostics_passed_through() -> None:
    d = build_view(_found(), query_tokens=700, query_token_limit=512).diagnostics
    assert (d.query_tokens, d.query_token_limit) == (700, 512)
    assert d.related_threshold == RELATED_SCORE_THRESHOLD
