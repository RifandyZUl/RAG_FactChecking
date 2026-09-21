"""
Klien HTTP untuk turnbackhoax.id: sesi, timeout, retry dengan exponential backoff,
dan cache HTML mentah. Setiap permintaan jaringan wajib bertimeout (lihat CLAUDE.md).
"""

import time
from collections.abc import Callable
from pathlib import Path

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}
DELAY = 1.5  # jeda antar-request, hindari membebani server
TIMEOUT = 45  # detik; server turnbackhoax.id lambat mengirim respons pertama
MAX_RETRIES = 3  # retry setelah percobaan pertama (total maksimal 4 percobaan)
BACKOFF_BASE = 2.0  # jeda retry: 2 dtk, 4 dtk, 8 dtk (exponential backoff)


def make_session() -> requests.Session:
    """Buat Session yang dipakai ulang (koneksi keep-alive) dengan header browser."""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def fetch_html(
    url: str,
    session: requests.Session,
    cache_path: Path | None = None,
    force_refresh: bool = False,
    validate: Callable[[str], bool] | None = None,
) -> tuple[str | None, bool]:
    """
    Ambil HTML mentah sebuah halaman, memakai cache bila tersedia.

    Mengembalikan (html, dari_jaringan). Nilai kedua False bila HTML dibaca
    dari cache, sehingga pemanggil boleh melewati jeda antar-request.

    Retry dengan exponential backoff untuk read timeout, connection error,
    dan respons 200 yang gagal `validate` (halaman galat dari server).
    Galat HTTP (termasuk 404) tidak di-retry. HTML yang tidak lolos validasi
    tidak pernah ditulis ke cache, dan cache yang tidak lolos validasi
    diabaikan lalu diambil ulang dari jaringan.
    """
    if cache_path is not None and not force_refresh and cache_path.exists():
        cached = cache_path.read_text(encoding="utf-8")
        if validate is None or validate(cached):
            return cached, False
        print(f"  [cache rusak] {cache_path.name} tidak lolos validasi -> ambil ulang")

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
        except (requests.ReadTimeout, requests.ConnectionError) as e:
            # ConnectTimeout adalah turunan ConnectionError, jadi ikut tertangkap
            reason = type(e).__name__
        except requests.RequestException as e:
            # Termasuk HTTPError (404, 5xx): tidak di-retry
            print(f"  [gagal] {url} -> {e}")
            return None, True
        else:
            if validate is None or validate(resp.text):
                if cache_path is not None:
                    # Tulis ke berkas sementara lalu ganti, agar cache tidak
                    # berisi HTML terpotong bila proses terhenti di tengah jalan
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    tmp = cache_path.with_suffix(".tmp")
                    tmp.write_text(resp.text, encoding="utf-8")
                    tmp.replace(cache_path)
                return resp.text, True
            reason = "halaman galat (HTML tidak lolos validasi)"

        if attempt == MAX_RETRIES:
            print(f"  [gagal] {url} -> {reason} setelah {MAX_RETRIES + 1} percobaan")
            return None, True
        wait = BACKOFF_BASE * (2 ** attempt)
        print(f"  [retry {attempt + 1}/{MAX_RETRIES}] {reason}; menunggu {wait:.0f} dtk")
        time.sleep(wait)

    return None, True  # tak tercapai; menenangkan pemeriksa tipe
