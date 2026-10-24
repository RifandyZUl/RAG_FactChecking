"""Uji pemuatan sumber daya sekali-muat dan pemanasan (offline: pabrik palsu, tanpa model sungguhan)."""

import logging
import sqlite3
import threading
import time
from datetime import date
from pathlib import Path

import pytest

from webapp import resources


def test_once_loads_a_single_time_even_when_warmup_and_a_session_ask_together(caplog: pytest.LogCaptureFixture) -> None:
    """Pemanasan (utas latar) dan sesi pengguna (lewat st.cache_resource) meminta model bersamaan: dimuat sekali."""
    started = threading.Event()

    def slow_factory() -> object:
        started.set()
        time.sleep(0.3)
        return object()

    loader = resources._Once("model uji", slow_factory)
    with caplog.at_level(logging.INFO, logger="resources"):
        warm = threading.Thread(target=resources._warmup, args=((loader,),))
        warm.start()
        started.wait()
        session_value = loader.get()  # menunggu pemuatan yang sedang berjalan, bukan memuat lagi
        warm.join()
    assert loader.load_count == 1 and loader.get() is session_value
    assert caplog.text.count("memuat model uji") == 1


def test_failed_load_is_not_cached_and_is_retried() -> None:
    attempts = []

    def flaky() -> str:
        attempts.append(1)
        if len(attempts) == 1:
            raise OSError("cache model belum ada")
        return "ok"

    loader = resources._Once("rapuh", flaky)
    with pytest.raises(OSError):
        loader.get()
    assert loader.get() == "ok" and loader.load_count == 2


def test_warmup_never_calls_the_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoCallProvider:
        def generate(self, *a: object, **k: object) -> str:
            raise AssertionError("pemanasan tidak boleh memanggil LLM")

    loader = resources._Once("penyedia LLM", NoCallProvider)
    resources._warmup((loader,))
    assert loader.loaded and resources.warmup_state() is resources.WarmupState.READY


def test_warmup_failure_is_reported_and_other_loaders_still_run() -> None:
    bad = resources._Once("rusak", lambda: (_ for _ in ()).throw(OSError("x")))
    good = resources._Once("baik", lambda: 1)
    resources._warmup((bad, good))
    assert good.loaded and resources.warmup_state() is resources.WarmupState.FAILED


def test_start_warmup_starts_only_one_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resources, "_warmup_thread", None)
    loader = resources._Once("ringan", lambda: 1)
    assert resources.start_warmup((loader,)) is True
    assert resources.start_warmup((loader,)) is False
    resources._warmup_thread.join()  # type: ignore[union-attr]
    assert loader.load_count == 1


def test_count_tokens_is_none_until_the_tokenizer_is_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resources, "tokenizer", resources._Once("tokenizer", lambda: lambda t: {"input_ids": t.split()}))
    assert resources.count_tokens("a b c") is None
    resources.tokenizer.get()
    assert resources.count_tokens("a b c") == 3


def _fake_index(tmp_path: Path, rows: list[tuple[str, str]]) -> Path:
    con = sqlite3.connect(tmp_path / "chroma.sqlite3")
    con.execute("create table embedding_metadata (id integer, key text, string_value text)")
    for i, (aid, d) in enumerate(rows):
        con.execute("insert into embedding_metadata values (?, 'article_id', ?)", (i, aid))
        con.execute("insert into embedding_metadata values (?, 'date', ?)", (i, d))
    con.commit()
    con.close()
    return tmp_path


def test_index_stats_counts_articles_and_parses_dates_not_compares_text(tmp_path: Path) -> None:
    # Sebagai teks "14/08/2026" > "01/10/2026"; tanggal sebenarnya yang terbaru adalah 1 Oktober.
    path = _fake_index(tmp_path, [("1", "14/08/2026"), ("1", "14/08/2026"), ("2", "01/10/2026"), ("3", "rusak")])
    stats = resources.index_stats(path)
    assert stats.article_count == 3 and stats.latest_date == date(2026, 10, 1)


def test_index_stats_without_index(tmp_path: Path) -> None:
    assert resources.index_stats(tmp_path) == resources.IndexStats(None, None)


@pytest.mark.parametrize(("value", "expected"), [("09/09/2026", date(2026, 9, 9)), ("31/02/2026", None),
                                                 ("2026-09-09", None), ("", None)])
def test_parse_metadata_date(value: str, expected: date | None) -> None:
    assert resources.parse_metadata_date(value) == expected
