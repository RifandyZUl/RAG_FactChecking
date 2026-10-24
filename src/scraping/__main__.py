"""Jalankan: python -m scraping (dari root proyek; paket dipasang dengan pip install -e .)."""

from scraping.pipeline import main

if __name__ == "__main__":
    main(max_articles=150)
