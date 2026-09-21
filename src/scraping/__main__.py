"""Jalankan: python -m scraping (dari root proyek, dengan PYTHONPATH=src)."""

from scraping.pipeline import main

if __name__ == "__main__":
    main(max_articles=150)
