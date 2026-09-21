"""
Jalur proyek terpusat, dijangkar ke root proyek agar tidak bergantung pada direktori kerja.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_HTML_DIR = DATA_DIR / "raw_html"
ARTICLES_PATH = DATA_DIR / "articles.json"
LEDGER_PATH = DATA_DIR / "quota_ledger.json"
