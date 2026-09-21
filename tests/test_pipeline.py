"""Uji orkestrasi scraping (scraping.pipeline): jalur keluaran bawaan dijangkar ke root proyek."""

import inspect
import json

import scraping.pipeline as pipeline
from paths import ARTICLES_PATH


def test_default_output_path_is_project_root_not_cwd() -> None:
    assert inspect.signature(pipeline.main).parameters["out_path"].default is None
    assert pipeline.ARTICLES_PATH == ARTICLES_PATH and ARTICLES_PATH.is_absolute()
    assert ARTICLES_PATH.name == "articles.json" and ARTICLES_PATH.parent.name == "data"


def test_main_writes_to_anchored_default_even_from_another_directory(monkeypatch, tmp_path) -> None:
    """Dijalankan dari direktori lain, main() tidak boleh menulis data/articles.json relatif ke direktori kerja."""
    target = tmp_path / "root" / "data" / "articles.json"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setattr(pipeline, "ARTICLES_PATH", target)  # jangan menyentuh data/articles.json asli
    monkeypatch.setattr(pipeline, "make_session", lambda: object())
    monkeypatch.setattr(pipeline, "discover_article_urls",
                        lambda session, max_articles: ["https://turnbackhoax.id/articles/1-x"])
    article = {"article_id": "1", "kesimpulan": "Faktanya, k"}
    monkeypatch.setattr(pipeline, "scrape_article", lambda url, session, force_refresh: (article, False))

    pipeline.main()

    assert target.exists(), "keluaran harus ke jalur bawaan yang dijangkar"
    assert json.loads(target.read_text(encoding="utf-8")) == [article]
    assert not (elsewhere / "data").exists(), "tidak boleh menulis relatif terhadap direktori kerja"


def test_main_respects_explicit_out_path(monkeypatch, tmp_path) -> None:
    out = tmp_path / "custom.json"
    monkeypatch.setattr(pipeline, "make_session", lambda: object())
    monkeypatch.setattr(pipeline, "discover_article_urls", lambda session, max_articles: ["u"])
    monkeypatch.setattr(pipeline, "scrape_article", lambda url, session, force_refresh: ({"kesimpulan": "k"}, False))
    pipeline.main(out_path=str(out))
    assert json.loads(out.read_text(encoding="utf-8")) == [{"kesimpulan": "k"}]
