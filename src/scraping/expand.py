"""
Perluasan basis data (tahap 3): kumpulkan artikel LEBIH TUA dari artikel tertua yang sudah dimiliki,
per kelompok, tanpa menyentuh data/articles.json maupun archive/v1.

Halaman daftar TurnBackHoax diurutkan dari yang terbaru; posisinya bergeser setiap ada artikel
baru, dan id artikel TIDAK menurun monoton. Karena itu titik mulai dicari lewat URL jangkar (artikel
tertua yang dimiliki, dalam urutan daftar), bukan lewat id atau nomor halaman tetap.

Tiap kelompok ditulis ke data/expansion/batch_NN.json (artikel, urutan daftar) dan
batch_NN_report.json (berhasil, gagal beserta alasan, id gagal, jumlah retry, seksi kosong, rentang
tanggal). Setiap artikel gagal (kedua mode) juga ditambahkan ke data/expansion/failed_ids.json, yang
tidak pernah ditimpa antar-jalan: ia catatan KEJADIAN, bukan status. Status "terbuka/teratasi" diturunkan
dengan membandingkannya dengan artikel yang dimiliki (--failed-status; `gagal_terbuka` di laporan). Status
lanjutan disimpan di data/expansion/state.json. HTML mentah di-cache di data/raw_html/ lewat
scrape_article, sehingga parsing dapat diulang tanpa memanggil server. Penggabungan ke
data/articles.json dilakukan TERPISAH setelah seluruh kelompok lolos pemeriksaan kualitas.

Ketentuan jaringan mengikuti scraping.client: timeout 45 dtk, retry terbatas, jeda 1,5 dtk.

Pemutus sirkuit: bila MAX_CONSECUTIVE_NETWORK_FAILURES artikel BERUNTUN gagal karena jaringan
(timeout/connection error setelah seluruh retry klien), jalan dihentikan (kode keluar 4). Jalan yang
terputus TIDAK menulis berkas artikel dan TIDAK memajukan state.json, sehingga menjalankan ulang
perintah yang sama mengulang kelompok itu (artikel yang sudah berhasil terbaca dari cache). Yang
ditulis hanya laporan kejadian `*_terputus_<waktu UTC>_report.json` dan entri failed_ids.json.

Mode maju (--forward): artikel LEBIH BARU dari yang dimiliki. Mulai dari halaman daftar terbaru,
bergerak ke halaman lebih tua, dan berhenti pada artikel pertama (urutan daftar) yang sudah dimiliki
(data/articles.json, kelompok mundur di state.json, atau hasil maju sebelumnya). Keluaran:
data/expansion/forward_YYYY-MM-DD.json dan forward_YYYY-MM-DD_report.json; state.json (jangkar mode
mundur) tidak diubah. Mode ini adalah dasar pembaruan berkala: logikanya sama, hanya perlu dijadwalkan.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m scraping.expand --batch-size 250
  PYTHONPATH=src python -m scraping.expand --forward
  PYTHONPATH=src python -m scraping.expand --failed-status
"""

import argparse
import contextlib
import io
import json
import re
import sys
import time
import traceback
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from paths import ARTICLES_PATH, DATA_DIR, RAW_HTML_DIR
from scraping.client import DELAY, make_session
from scraping.discovery import LIST_URL, find_article_urls, get_soup
from scraping.pipeline import scrape_article

EXPANSION_DIR = DATA_DIR / "expansion"
STATE_PATH = EXPANSION_DIR / "state.json"
MAX_FAILURE_RATE = 0.05  # ambang sewenang-wenang dari pemilik proyek (bukan berbasis data)
SECTIONS = ("narasi", "penjelasan", "kesimpulan")
FAILED_PATH = EXPANSION_DIR / "failed_ids.json"  # buku gagal: hanya ditambah, tidak pernah ditimpa antar-jalan
_FAIL_LINE = re.compile(r"\[gagal\] \S+ -> (.+)")
_RETRY_LINE = re.compile(r"\[retry \d+/\d+\]")
# Jumlah retry scraping.client pada jalan ini (dibaca dari keluarannya; modul klien tidak diubah).
RETRIES = {"artikel": 0, "halaman_daftar": 0}

# Pemutus sirkuit (ditambahkan 2026-10-02 setelah kelompok 5: jaringan putus total, 209 artikel
# beruntun dicoba sia-sia selama 1,5 jam karena MAX_FAILURE_RATE baru diperiksa di akhir).
# Satu "kegagalan jaringan" di sini sudah berarti 4 permintaan gagal dengan jeda 2+4+8 dtk
# (scraping.client), jadi 5 beruntun = 20 permintaan gagal berturut-turut selama >= ~75 dtk
# (terukur pada kelompok 5: ~26 dtk per artikel gagal, jadi ~2 menit). Gangguan sesaat (kelompok 5
# urutan 39: satu artikel gagal lalu pulih) tidak memutus. Disetujui pemilik proyek 2026-10-02; dapat
# ditimpa lewat --max-network-failures.
MAX_CONSECUTIVE_NETWORK_FAILURES = 5
EXIT_NETWORK_DOWN = 4
# Alasan gagal dari scraping.client untuk galat yang di-retry: "<NamaGalat> setelah N percobaan".
# Hanya galat jaringan (ReadTimeout, ConnectTimeout, ConnectionError, SSLError, ProxyError) yang
# cocok; "halaman galat (...) setelah N percobaan", galat HTTP (404, 5xx), dan gagal parse tidak.
_NETWORK_FAILURE = re.compile(r"^\w*(?:Timeout|ConnectionError|SSLError|ProxyError) setelah \d+ percobaan$")


class NetworkDownError(RuntimeError):
    """Pemutus sirkuit terpicu; membawa hasil sebagian agar pemanggil dapat menulis laporan kejadian."""

    def __init__(self, articles: list[dict], failures: list[dict], attempted: int, total: int,
                 consecutive: int) -> None:
        super().__init__(f"{consecutive} kegagalan jaringan beruntun setelah {attempted} dari {total} artikel dicoba")
        self.articles, self.failures = articles, failures
        self.attempted, self.total, self.consecutive = attempted, total, consecutive


def is_network_failure(reason: str) -> bool:
    """Apakah alasan gagal sebuah artikel adalah galat jaringan (bukan cacat artikel itu sendiri)."""
    return _NETWORK_FAILURE.match(reason) is not None


# Jenis kegagalan artikel, dicatat di failed_ids.json dan laporan agar bug kode tidak tercampur
# dengan gangguan koneksi. "galat_kode" = exception tak terduga saat mengambil/mem-parse satu
# artikel (bug di kode kita atau HTML yang tidak diantisipasi): bila jumlahnya banyak, itu bug
# sistematis, bukan masalah jaringan.
UNEXPECTED_PREFIX = "galat tak terduga: "
PARSE_NONE_REASON = "HTML sah tetapi parse_article mengembalikan None"


def failure_kind(reason: str) -> str:
    """jaringan | galat_kode | halaman_galat | parse_kosong | http_atau_lain (dari alasan gagal)."""
    if is_network_failure(reason):
        return "jaringan"
    if reason.startswith(UNEXPECTED_PREFIX):
        return "galat_kode"
    if reason.startswith("halaman galat"):
        return "halaman_galat"
    if reason == PARSE_NONE_REASON:
        return "parse_kosong"
    return "http_atau_lain"


def article_id_of(url: str) -> str | None:
    m = re.search(r"/articles/(\d+)-", url)
    return m.group(1) if m else None


def urls_after_anchor(page_urls: list[str], anchor_url: str | None) -> tuple[list[str], bool]:
    """
    URL pada satu halaman yang terletak SETELAH jangkar (lebih tua). (daftar, jangkar_ditemukan).
    Tanpa jangkar (None), seluruh URL halaman dikembalikan.
    """
    if anchor_url is None:
        return list(page_urls), True
    if anchor_url in page_urls:
        return page_urls[page_urls.index(anchor_url) + 1:], True
    return [], False


def batch_stats(articles: list[dict], failures: list[dict], attempted: int) -> dict[str, Any]:
    """Ringkasan kelompok: berhasil, gagal (alasan), seksi kosong, rentang tanggal, tingkat gagal."""
    empty = [a["article_id"] for a in articles if any(not a.get(k) for k in SECTIONS)]
    empty_by_section = {k: sum(1 for a in articles if not a.get(k)) for k in SECTIONS}
    dates = []
    for a in articles:
        try:
            day, month, year = (int(x) for x in a["date"].split("/"))
            dates.append(date(year, month, day))  # tanggal kalender, tanpa zona waktu
        except (KeyError, ValueError):
            pass
    reasons: dict[str, int] = {}
    for f in failures:
        reasons[f["alasan"]] = reasons.get(f["alasan"], 0) + 1
    kinds = _count(f.get("jenis") or failure_kind(f["alasan"]) for f in failures)
    return {
        "dicoba": attempted,
        "berhasil": len(articles),
        "gagal": len(failures),
        "tingkat_gagal": round(len(failures) / attempted, 4) if attempted else 0.0,
        "alasan_gagal": reasons,
        "gagal_per_jenis": kinds,
        "exception_galat_kode": _count(f["exception"] for f in failures if f.get("exception")),
        "artikel_seksi_kosong": len(empty),
        "seksi_kosong_per_seksi": empty_by_section,
        "id_seksi_kosong": empty,
        "tanggal_tanpa_format_sah": len(articles) - len(dates),
        "rentang_tanggal": [min(dates).isoformat(), max(dates).isoformat()] if dates else None,
        "label": _count(a.get("label") for a in articles),
        "id_gagal": [f["article_id"] for f in failures],
    }


def _count(values: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _captured(fn: Any, *args: Any) -> tuple[Any, str]:
    """Jalankan fn sambil menangkap keluarannya (lalu dicetak ulang), untuk membaca baris retry/gagal."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(*args)
    log = buf.getvalue()
    if log:
        print(log, end="")
    return result, log


def fetch_list_page(page: int, session: Any) -> list[str] | None:
    soup, log = _captured(get_soup, f"{LIST_URL}?page={page}", session)
    RETRIES["halaman_daftar"] += len(_RETRY_LINE.findall(log))
    if soup is None:
        return None
    seen: list[str] = []
    for u in find_article_urls(soup):
        if u not in seen:
            seen.append(u)
    return seen


def collect_urls(session: Any, anchor_url: str, start_page: int, n: int, known_ids: set[str],
                 max_scan_pages: int = 80) -> tuple[list[str], int]:
    """
    Kumpulkan n URL lebih tua dari jangkar, dimulai dari `start_page` (jangkar dicari maju).
    Mengembalikan (url, halaman_terakhir_dibaca).
    """
    urls: list[str] = []
    found_anchor = False
    page = start_page
    for page in range(start_page, start_page + max_scan_pages):
        page_urls = fetch_list_page(page, session)
        time.sleep(DELAY)
        if page_urls is None:
            raise RuntimeError(f"halaman daftar {page} gagal diambil")
        if not found_anchor:
            candidates, found_anchor = urls_after_anchor(page_urls, anchor_url)
            print(f"[daftar] halaman {page}: jangkar {'DITEMUKAN' if found_anchor else 'belum ada'}")
        else:
            candidates = page_urls
        for u in candidates:
            aid = article_id_of(u)
            if aid and aid not in known_ids and u not in urls:
                urls.append(u)
        if len(urls) >= n:
            break
    if not found_anchor:
        raise RuntimeError(f"jangkar {anchor_url} tidak ditemukan pada halaman {start_page}-{page}")
    return urls[:n], page


def collect_new_urls(session: Any, known_ids: set[str], max_pages: int = 30
                     ) -> tuple[list[str], dict[str, Any]]:
    """
    Kumpulkan URL yang BELUM dimiliki dari halaman 1 ke belakang, berhenti pada artikel pertama yang
    sudah dimiliki. Mengembalikan (url_baru, titik_henti). Sisa URL pada halaman titik henti yang
    tidak dikenal TIDAK diambil, hanya dilaporkan (penanda urutan daftar tidak rapi).
    """
    urls: list[str] = []
    for page in range(1, max_pages + 1):
        page_urls = fetch_list_page(page, session)
        time.sleep(DELAY)
        if page_urls is None:
            raise RuntimeError(f"halaman daftar {page} gagal diambil")
        for i, u in enumerate(page_urls):
            aid = article_id_of(u)
            if aid is None or u in urls:
                continue
            if aid in known_ids:
                rest = [r for r in page_urls[i + 1:] if (article_id_of(r) or "") not in known_ids]
                print(f"[daftar] halaman {page}: titik henti {u}")
                return urls, {"url": u, "article_id": aid, "halaman": page,
                              "tak_dikenal_setelah_titik_henti": rest}
            urls.append(u)
        print(f"[daftar] halaman {page}: {len(urls)} URL baru sejauh ini")
    raise RuntimeError(f"tidak bertemu artikel yang sudah dimiliki dalam {max_pages} halaman")


def forward_known_ids(state: dict[str, Any]) -> set[str]:
    """Id yang sudah dimiliki: basis, kelompok mundur (state), dan hasil mode maju sebelumnya."""
    known = {a["article_id"] for a in json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))}
    known |= set(state.get("known_ids", []))
    for f in sorted(EXPANSION_DIR.glob("forward_*.json")):
        if not f.name.endswith("_report.json"):
            known |= {a["article_id"] for a in json.loads(f.read_text(encoding="utf-8"))}
    return known


def scrape_with_reason(url: str, session: Any) -> tuple[dict | None, bool, str, int]:
    """
    scrape_article + alasan gagal + jumlah retry (keduanya dibaca dari keluaran fetch_html; modul
    klien tidak diubah). Mengembalikan (artikel, dari_jaringan, alasan, retry).

    Exception tak terduga (mis. bug parsing pada HTML yang tidak diantisipasi) TIDAK menggugurkan
    jalan: ia menjadi kegagalan artikel itu dengan alasan "galat tak terduga: <Jenis>: <pesan>
    (<berkas>:<baris> <fungsi>)", dan jejak lengkapnya dicetak ke log. `dari_jaringan` pada kasus
    itu diperkirakan dari ada/tidaknya cache sebelum pengambilan.
    """
    aid = article_id_of(url)
    cached_before = aid is not None and (RAW_HTML_DIR / f"{aid}.html").exists()
    buf = io.StringIO()
    error: Exception | None = None
    art, from_network = None, not cached_before
    try:
        with contextlib.redirect_stdout(buf):
            art, from_network = scrape_article(url, session)
    except Exception as e:  # noqa: BLE001 -- sengaja luas; dicatat lengkap di bawah, tidak ditelan
        error = e
    log = buf.getvalue()
    if log:
        print(log, end="")
    retries = len(_RETRY_LINE.findall(log))
    if error is not None:
        frame = traceback.extract_tb(error.__traceback__)[-1]
        where = f"{Path(frame.filename).name}:{frame.lineno} {frame.name}"
        print("".join(traceback.format_exception(error)), end="")
        return None, from_network, f"{UNEXPECTED_PREFIX}{type(error).__name__}: {error} ({where})", retries
    if art is not None:
        return art, from_network, "", retries
    m = _FAIL_LINE.search(log)
    reason = m.group(1).strip() if m else PARSE_NONE_REASON
    return None, from_network, reason, retries


def record_failure(failure: dict[str, Any], run: str, path: Path | None = None) -> None:
    """
    Tambahkan satu kegagalan ke buku gagal (`failed_ids.json`). Entri lama tidak pernah ditimpa atau
    dihapus; ditulis segera per kegagalan (berkas sementara lalu ganti) agar tetap tercatat bila jalan
    terhenti sesudahnya.
    """
    path = path or FAILED_PATH
    entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    entries.append({**failure, "jalan": run, "waktu_utc": datetime.now(UTC).isoformat(timespec="seconds")})
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_failures(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or FAILED_PATH
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def owned_ids() -> set[str]:
    """
    Id artikel yang BERHASIL dimiliki: data/articles.json dan berkas hasil kelompok/maju di
    data/expansion/ (bukan laporan). Berbeda dari state.json.known_ids, yang berarti "sudah dicoba".
    """
    files = [ARTICLES_PATH] if ARTICLES_PATH.exists() else []
    files += [f for pattern in ("batch_*.json", "forward_*.json") for f in sorted(EXPANSION_DIR.glob(pattern))
              if not f.name.endswith("_report.json")]
    return {a["article_id"] for f in files for a in json.loads(f.read_text(encoding="utf-8"))}


def failure_status(entries: list[dict[str, Any]], owned: set[str]) -> dict[str, Any]:
    """
    Status TURUNAN buku gagal. failed_ids.json adalah catatan kejadian yang hanya bertambah: entri
    tidak dihapus saat artikelnya kemudian berhasil. "Terbuka" = pernah gagal dan belum dimiliki;
    "teratasi" = pernah gagal tetapi kini dimiliki. Dihitung saat diminta, tidak disimpan.
    """
    last: dict[str, dict[str, Any]] = {}
    count: dict[str, int] = {}
    for e in entries:
        aid = e["article_id"]
        last[aid] = e
        count[aid] = count.get(aid, 0) + 1
    open_ids = [aid for aid in last if aid not in owned]
    return {
        "entri": len(entries),
        "id_unik": len(last),
        "teratasi": len(last) - len(open_ids),
        "terbuka": len(open_ids),
        "id_terbuka": open_ids,
        "terbuka_per_jenis": _count(last[aid].get("jenis") or failure_kind(last[aid]["alasan"]) for aid in open_ids),
        "rincian_terbuka": [{"article_id": aid, "url": last[aid]["url"], "kali_gagal": count[aid],
                             "alasan_terakhir": last[aid]["alasan"], "jalan_terakhir": last[aid]["jalan"],
                             "waktu_utc_terakhir": last[aid]["waktu_utc"]} for aid in open_ids],
    }


def open_failure_ids() -> list[str]:
    return failure_status(load_failures(), owned_ids())["id_terbuka"]


def scrape_all(urls: list[str], session: Any, run: str,
               max_network_failures: int = MAX_CONSECUTIVE_NETWORK_FAILURES) -> tuple[list[dict], list[dict]]:
    """
    Ambil semua URL; tiap kegagalan langsung dicatat ke buku gagal dengan label jalan `run`.

    Melempar NetworkDownError setelah `max_network_failures` kegagalan jaringan BERUNTUN. Hitungan
    kembali ke nol setiap kali server terbukti terjangkau: artikel berhasil diambil dari jaringan,
    atau gagal dengan alasan non-jaringan dari jaringan (404, halaman galat, gagal parse). Artikel
    yang terbaca dari cache tidak mengubah hitungan (bukan bukti keadaan jaringan).
    """
    articles: list[dict] = []
    failures: list[dict] = []
    consecutive = 0
    for i, url in enumerate(urls, 1):
        art, from_network, reason, retries = scrape_with_reason(url, session)
        RETRIES["artikel"] += retries
        if art is None:
            failure = {"url": url, "article_id": article_id_of(url), "alasan": reason, "retry": retries,
                       "jenis": failure_kind(reason)}
            if failure["jenis"] == "galat_kode":
                failure["exception"] = reason.removeprefix(UNEXPECTED_PREFIX).split(":", 1)[0]
            failures.append(failure)
            record_failure(failure, run)
        else:
            articles.append(art)
        status = "ok" if art else f"GAGAL [{failure_kind(reason)}]: {reason}"
        print(f"[{i}/{len(urls)}] {article_id_of(url)} {status}")
        if art is None and is_network_failure(reason):
            consecutive += 1
            if consecutive >= max_network_failures:
                raise NetworkDownError(articles, failures, i, len(urls), consecutive)
        elif from_network:
            consecutive = 0
        if from_network:
            time.sleep(DELAY)
    return articles, failures


def write_interrupted_report(run: str, err: NetworkDownError, extra: dict[str, Any]) -> Path:
    """
    Laporan kejadian untuk jalan yang diputus pemutus sirkuit. Nama berkas memuat waktu UTC, jadi
    tidak pernah menimpa laporan lain (termasuk laporan jalan ulang kelompok yang sama).
    """
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = EXPANSION_DIR / f"{run}_terputus_{stamp}_report.json"
    report = {**extra, "terputus": True, "alasan_berhenti": str(err),
              "belum_dicoba": err.total - err.attempted,
              "statistik": batch_stats(err.articles, err.failures, err.attempted),
              "retry": dict(RETRIES), "gagal": err.failures, "gagal_terbuka": open_failure_ids(),
              "catatan": "berkas artikel tidak ditulis dan state.json tidak diubah; artikel yang berhasil ada di cache"}
    EXPANSION_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"TERPUTUS: {err}. Laporan kejadian: {path}")
    print("Berkas artikel tidak ditulis dan state.json tidak diubah; jalankan ulang perintah yang sama "
          "setelah jaringan pulih.")
    return path


def run_forward(state: dict[str, Any], max_pages: int,
                max_network_failures: int = MAX_CONSECUTIVE_NETWORK_FAILURES) -> int:
    session = make_session()
    known = forward_known_ids(state)
    tag = datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat()  # tanggal WIB, zona situs sumber
    out = EXPANSION_DIR / f"forward_{tag}.json"
    if out.exists():
        raise RuntimeError(f"{out} sudah ada; hapus atau tunggu hari berikutnya")
    print(f"=== Mode maju: {len(known)} id sudah dimiliki ===")
    urls, stop = collect_new_urls(session, known, max_pages)
    print(f"{len(urls)} URL baru; titik henti {stop['url']} (halaman {stop['halaman']})")
    try:
        articles, failures = scrape_all(urls, session, f"forward_{tag}", max_network_failures)
    except NetworkDownError as e:
        # Hasil sebagian sengaja TIDAK ditulis: artikel terbaru yang tercatat "dimiliki" akan menjadi
        # titik henti jalan berikutnya, sehingga artikel lebih tua yang belum terambil terlewat.
        write_interrupted_report(f"forward_{tag}", e, {"mode": "maju", "tanggal_jalan": tag, "titik_henti": stop})
        return EXIT_NETWORK_DOWN
    stats = batch_stats(articles, failures, len(urls))
    EXPANSION_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"mode": "maju", "tanggal_jalan": tag, "titik_henti": stop, "statistik": stats,
              "retry": dict(RETRIES), "gagal": failures, "gagal_terbuka": open_failure_ids()}
    (EXPANSION_DIR / f"forward_{tag}_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if stats["tingkat_gagal"] > MAX_FAILURE_RATE:
        print(f"BERHENTI: tingkat gagal {stats['tingkat_gagal']:.1%} > {MAX_FAILURE_RATE:.0%}")
        return 3
    return 0


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    base = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    return {"batch": 0, "anchor_url": base[-1]["url"], "start_page": 1,
            "known_ids": [a["article_id"] for a in base], "catatan": "jangkar awal = artikel terakhir data/articles.json"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--batch-size", type=int, default=250)
    ap.add_argument("--start-page", type=int, default=None, help="halaman awal pencarian jangkar (bawaan: dari status)")
    ap.add_argument("--forward", action="store_true", help="mode maju: artikel lebih baru dari yang dimiliki")
    ap.add_argument("--max-pages", type=int, default=30, help="mode maju: batas halaman daftar yang dibaca")
    ap.add_argument("--failed-status", action="store_true",
                    help="cetak status turunan failed_ids.json (terbuka/teratasi) lalu keluar; tanpa jaringan")
    ap.add_argument("--max-network-failures", type=int, default=MAX_CONSECUTIVE_NETWORK_FAILURES,
                    help="pemutus sirkuit: berhenti setelah sekian artikel beruntun gagal karena jaringan")
    args = ap.parse_args()

    if args.failed_status:
        print(json.dumps(failure_status(load_failures(), owned_ids()), ensure_ascii=False, indent=2))
        return 0
    state = load_state()
    if args.forward:
        return run_forward(state, args.max_pages, args.max_network_failures)
    known = set(state["known_ids"])
    batch_no = state["batch"] + 1
    start_page = args.start_page or state["start_page"]
    session = make_session()

    print(f"=== Kelompok {batch_no}: {args.batch_size} artikel setelah {state['anchor_url']} ===")
    urls, last_page = collect_urls(session, state["anchor_url"], start_page, args.batch_size, known)
    print(f"{len(urls)} URL terkumpul (halaman daftar s.d. {last_page})")

    try:
        articles, failures = scrape_all(urls, session, f"batch_{batch_no:02d}", args.max_network_failures)
    except NetworkDownError as e:
        write_interrupted_report(f"batch_{batch_no:02d}", e, {
            "kelompok": batch_no, "jangkar_awal": state["anchor_url"], "halaman_daftar_terakhir": last_page})
        return EXIT_NETWORK_DOWN
    stats = batch_stats(articles, failures, len(urls))
    EXPANSION_DIR.mkdir(parents=True, exist_ok=True)
    (EXPANSION_DIR / f"batch_{batch_no:02d}.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"kelompok": batch_no, "jangkar_awal": state["anchor_url"], "halaman_daftar_terakhir": last_page,
              "statistik": stats, "retry": dict(RETRIES), "gagal": failures,
              "gagal_terbuka": open_failure_ids()}  # dihitung SETELAH batch_NN.json ditulis
    (EXPANSION_DIR / f"batch_{batch_no:02d}_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    state.update({"batch": batch_no, "anchor_url": urls[-1] if urls else state["anchor_url"],
                  "start_page": last_page, "known_ids": sorted(known | {article_id_of(u) for u in urls})})
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**stats, "retry": dict(RETRIES)}, ensure_ascii=False, indent=2))
    if stats["tingkat_gagal"] > MAX_FAILURE_RATE:
        print(f"BERHENTI: tingkat gagal {stats['tingkat_gagal']:.1%} > {MAX_FAILURE_RATE:.0%}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
