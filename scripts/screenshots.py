"""
Tangkapan layar bukti tampilan demo (alat PENGEMBANGAN; butuh `playwright` dari requirements-dev.txt).

Demo harus sudah berjalan (`streamlit run src/webapp/app.py --server.port 8599`). Untuk keadaan hasil, satu
pemeriksaan sungguhan dijalankan per klaim (memakai kuota Gemini), lalu halaman yang SAMA difoto pada
lebar 390px dan 1280px tanpa memeriksa ulang.

    .\\.venv\\Scripts\\python.exe scripts\\screenshots.py --found "<klaim>" --not-found "<klaim>"
"""

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "tampilan"
WIDTHS = (390, 1280)
RESULT_TIMEOUT_MS = 240_000  # pemeriksaan pertama memuat model


def _settle(page: Page) -> None:
    """Tunggu Streamlit selesai menggambar (tidak ada indikator 'running') dan font termuat."""
    page.wait_for_load_state("networkidle")
    page.wait_for_selector('[data-testid="stApp"][data-test-script-state="notRunning"]', timeout=RESULT_TIMEOUT_MS)
    # Font dimuat malas per bobot: `document.fonts.status` bisa sudah "loaded" sebelum bobot yang dipakai
    # diminta, sehingga foto sesekali memakai font cadangan (terlihat 2026-10-23). Muat bobotnya eksplisit.
    page.evaluate("""() => Promise.all(['400', '500', '600', '700'].map(
        w => document.fonts.load(`${w} 16px "IBM Plex Sans"`))).then(() => document.fonts.ready)""")
    time.sleep(1.0)


def _shoot(page: Page, name: str) -> None:
    """Foto seluruh isi: Streamlit menggulir di dalam `stMain`, jadi tinggi viewport disamakan dengan isinya."""
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        time.sleep(0.8)
        height = page.evaluate("document.querySelector('[data-testid=stMain]').scrollHeight")
        page.set_viewport_size({"width": width, "height": max(900, int(height))})
        time.sleep(0.8)
        path = OUT_DIR / f"{name}-{width}.png"
        page.screenshot(path=str(path))
        print(f"tersimpan: {path.relative_to(OUT_DIR.parent.parent)}")


def _check(page: Page, base_url: str, claim: str, expect: str) -> None:
    page.goto(base_url)
    _settle(page)
    box = page.get_by_label("Pesan yang Anda terima")
    box.fill(claim)
    box.press("Tab")  # nilai text_area masuk saat kotak ditinggalkan
    _settle(page)
    page.get_by_role("button", name="Periksa pesan").click()
    page.wait_for_selector(f"text={expect}", timeout=RESULT_TIMEOUT_MS)
    _settle(page)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8599")
    ap.add_argument("--found", help="klaim yang diharapkan 'ditemukan'")
    ap.add_argument("--not-found", help="klaim yang diharapkan 'belum ditemukan'")
    ap.add_argument("--only", choices=["beranda", "tentang", "ditemukan", "belum-ditemukan"], action="append")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wanted = set(args.only or ["beranda", "tentang", "ditemukan", "belum-ditemukan"])
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTHS[0], "height": 900}, device_scale_factor=1)
        if "beranda" in wanted:
            page.goto(args.url)
            _settle(page)
            _shoot(page, "beranda")
        if "tentang" in wanted:
            page.goto(f"{args.url}/tentang")
            _settle(page)
            _shoot(page, "tentang")
        if "ditemukan" in wanted and args.found:
            _check(page, args.url, args.found, "menurut TurnBackHoax.id")
            _shoot(page, "ditemukan")
        if "belum-ditemukan" in wanted and args.not_found:
            _check(page, args.url, args.not_found, "Ini bukan berarti pesannya benar.")
            _shoot(page, "belum-ditemukan")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
