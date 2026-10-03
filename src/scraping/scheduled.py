"""
Pembungkus pembaruan berkala (SCRAPING SAJA; ingest tetap manual) -- docs/rancangan_pembaruan_berkala.md.

Dipanggil Task Scheduler (atau manual) sekali per jalan:
  1. kunci satu-instans (data/expansion/pembaruan.lock);
  2. coba ulang kegagalan terbuka yang masih layak dicoba (expand --retry-failed);
  3. mode maju (expand --forward): artikel lebih baru dari yang dimiliki. Hasilnya hanya MASUK ANTREAN
     (data/expansion/forward_*.json, retry_*.json); penggabungan ke articles.json dan ingest manual;
  4. pemeriksaan kualitas hasil hari itu (seksi kosong, label tak dikenal, tumpang tindih, URL tidak sah);
  5. status ditulis ke data/expansion/pembaruan_status.json dan pembaruan_riwayat.jsonl (kode keluar
     dicatat dari proses Python ini sendiri, bukan dari pembungkus luar);
  6. pemberitahuan dua lapis bila jalan tidak bersih: berkas penanda PERHATIAN_PEMBARUAN.txt di root
     proyek (dihapus pada jalan bersih berikutnya) dan notifikasi Windows.

Jalan yang terlewat (laptop tertidur) aman dijalankan begitu laptop menyala: mode maju berhenti di artikel
pertama yang sudah dimiliki, dan bila hasil mode maju hari itu sudah ada, langkah 3 dilewati.

Kode keluar: 0 bersih | 3 ditahan (kegagalan sistematis) | 4 jaringan putus | 5 ditahan (akan dicoba
lagi) | 6 ada yang perlu ditinjau | 7 batas mode maju tidak ditemukan | 8 galat tak terduga | 9 jalan
lain sedang berlangsung.

Pemakaian (dari root proyek):
  PYTHONPATH=src python -m scraping.scheduled [--no-notify] [--reset]
"""

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from paths import ARTICLES_PATH, PROJECT_ROOT
from scraping import expand
from scraping.parser import KNOWN_LABELS

MARKER_PATH = PROJECT_ROOT / "PERHATIAN_PEMBARUAN.txt"
STATUS_NAME, HISTORY_NAME, LOCK_NAME, LOG_DIR_NAME = "pembaruan_status.json", "pembaruan_riwayat.jsonl", "pembaruan.lock", "logs"
LOCK_STALE_SECONDS = 3 * 3600  # kunci lebih tua dari ini dianggap sisa jalan yang mati
MAX_PAGES = 30
MAX_CONSECUTIVE_SYSTEMATIC = 3  # setelah sekian jalan beruntun ditahan sistematis: berhenti mencoba

EXIT_BOUNDARY_LOST, EXIT_UNEXPECTED, EXIT_LOCKED = 7, 8, 9
EXIT_MEANING = {
    0: "bersih",
    expand.EXIT_HELD_SYSTEMATIC: "DITAHAN: kegagalan sistematis (banyak artikel gagal); perlu ditangani manusia",
    expand.EXIT_NETWORK_DOWN: "jaringan putus; akan dicoba lagi pada jalan berikutnya",
    expand.EXIT_HELD_RETRY: "DITAHAN: ada artikel gagal yang akan dicoba lagi pada jalan berikutnya",
    expand.EXIT_NEEDS_REVIEW: "ada yang PERLU DITINJAU (kegagalan permanen, atau label/isi artikel baru yang janggal)",
    EXIT_BOUNDARY_LOST: "mode maju tidak bertemu artikel yang sudah dimiliki; perlu ditinjau",
    EXIT_UNEXPECTED: "galat tak terduga di pembungkus atau scraping",
    EXIT_LOCKED: "jalan lain sedang berlangsung; jalan ini dilewati",
}
# Label yang sudah diputuskan cara menampilkannya (presentation.STATUS_ALIASES); label lain menahan penggabungan.
REVIEWED_LABELS = frozenset(KNOWN_LABELS) | {"SATIRE", "SATIR", "KOMEDI"}
INVALID_URL_REASON = "URL tidak sah"


def now_utc() -> datetime:
    return datetime.now(UTC)


def acquire_lock(path: Path, now: float | None = None) -> bool:
    """Ambil kunci satu-instans; False bila jalan lain masih memegangnya (kunci basi diambil alih)."""
    now = time.time() if now is None else now
    if path.exists() and now - path.stat().st_mtime < LOCK_STALE_SECONDS:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pid": os.getpid(), "mulai_utc": now_utc().isoformat(timespec="seconds")}), encoding="utf-8")
    return True


def classify_exception(exc: BaseException) -> int:
    """Kode keluar untuk exception dari expand: halaman daftar gagal = jaringan; batas tak ditemukan = 7."""
    text = str(exc)
    if isinstance(exc, RuntimeError) and "gagal diambil" in text:
        return expand.EXIT_NETWORK_DOWN
    if isinstance(exc, RuntimeError) and "tidak bertemu artikel yang sudah dimiliki" in text:
        return EXIT_BOUNDARY_LOST
    return EXIT_UNEXPECTED


def quality_report(articles: list[dict], owned_before: set[str]) -> dict[str, Any]:
    """Pemeriksaan kualitas hasil satu jalan; `tahan_penggabungan` True bila ada yang perlu ditinjau manusia."""
    empty = [a["article_id"] for a in articles if any(not a.get(k) for k in expand.SECTIONS)]
    labels = sorted({a.get("label") or "" for a in articles} - REVIEWED_LABELS)
    odd_label_ids = [a["article_id"] for a in articles if (a.get("label") or "") not in REVIEWED_LABELS]
    ids = [a["article_id"] for a in articles]
    overlap = sorted(set(ids) & owned_before)
    invalid = [a["article_id"] for a in articles
               if any(INVALID_URL_REASON in r.get("reasons", []) for r in a.get("references_filtered", []))]
    return {
        "artikel": len(articles),
        "seksi_kosong": empty,
        "label_belum_ditinjau": labels,
        "id_label_belum_ditinjau": odd_label_ids,
        "duplikat": len(ids) - len(set(ids)),
        "tumpang_tindih_dengan_yang_dimiliki": overlap,
        "url_tidak_sah": invalid,
        # label baru / TIDAK DIKETAHUI / duplikat menahan penggabungan; seksi kosong dan URL tidak sah hanya dilaporkan
        "tahan_penggabungan": bool(labels or overlap or len(ids) != len(set(ids))),
    }


def pending_merge(articles_path: Path | None = None) -> int:
    """Jumlah artikel yang sudah diambil tetapi belum digabung ke articles.json (antrean ingest manual)."""
    path = articles_path or ARTICLES_PATH
    merged = {a["article_id"] for a in json.loads(path.read_text(encoding="utf-8"))} if path.exists() else set()
    return len(expand.owned_ids() - merged)


def consecutive_systematic(history_path: Path) -> int:
    """Berapa jalan TERAKHIR beruntun yang berakhir ditahan sistematis (entri 'reset' memutus hitungan)."""
    if not history_path.exists():
        return 0
    n = 0
    for line in reversed(history_path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("kode_keluar") != expand.EXIT_HELD_SYSTEMATIC or entry.get("reset"):
            break
        n += 1
    return n


def marker_text(status: dict[str, Any]) -> str:
    lines = [
        "PEMBARUAN BERKALA: JALAN TERAKHIR TIDAK BERSIH",
        "",
        f"Waktu (WIB)  : {status['waktu_wib']}",
        f"Kode keluar  : {status['kode_keluar']} -- {status['arti']}",
    ]
    if status.get("berhenti_mencoba"):
        lines.append(f"BERHENTI MENCOBA: {MAX_CONSECUTIVE_SYSTEMATIC} jalan beruntun ditahan. Setelah diperbaiki: "
                     "python -m scraping.scheduled --reset")
    if status.get("gagal_per_jenis"):
        lines.append(f"Gagal/jenis  : {status['gagal_per_jenis']}")
    if status.get("perlu_tinjauan"):
        lines.append(f"Perlu tinjauan (artikel gagal permanen): {status['perlu_tinjauan']}")
    q = status.get("kualitas") or {}
    if q.get("tahan_penggabungan"):
        lines.append(f"Penggabungan DITAHAN: label belum ditinjau {q['label_belum_ditinjau']} pada {q['id_label_belum_ditinjau']}; "
                     f"tumpang tindih {q['tumpang_tindih_dengan_yang_dimiliki']}")
    if status.get("galat"):
        lines.append(f"Galat        : {status['galat']}")
    lines += [
        f"Antrean belum digabung: {status.get('antrean_belum_digabung')} artikel",
        f"Log          : {status.get('log')}",
        f"Status       : {status.get('berkas_status')}",
        "",
        "Berkas ini ditulis otomatis dan dihapus sendiri pada jalan bersih berikutnya.",
        "Status kegagalan artikel: python -m scraping.expand --failed-status",
    ]
    return "\n".join(lines) + "\n"


_TOAST_PS = r"""
$ErrorActionPreference = 'Stop'
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$nodes = $xml.GetElementsByTagName('text')
$nodes.Item(0).AppendChild($xml.CreateTextNode($env:RAG_TOAST_TITLE)) | Out-Null
$nodes.Item(1).AppendChild($xml.CreateTextNode($env:RAG_TOAST_BODY)) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show($toast)
"""


def notify_windows(title: str, body: str) -> bool:
    """Notifikasi Windows (toast) lewat PowerShell bawaan; True bila perintahnya berhasil. Tidak pernah melempar."""
    if sys.platform != "win32":
        return False
    env = {**os.environ, "RAG_TOAST_TITLE": title, "RAG_TOAST_BODY": body}
    try:
        done = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _TOAST_PS],
                              env=env, capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[notifikasi] gagal dijalankan: {e}")
        return False
    if done.returncode != 0:
        print(f"[notifikasi] PowerShell kode {done.returncode}: {done.stderr.decode('utf-8', 'replace')[:300]}")
    return done.returncode == 0


class _Tee(io.TextIOBase):
    """Tulis ke beberapa aliran sekaligus (konsol + berkas log)."""

    def __init__(self, *streams: Any) -> None:
        self.streams = streams

    def write(self, text: str) -> int:
        for s in self.streams:
            s.write(text)
            s.flush()
        return len(text)


def _scrape_steps(today: str) -> tuple[int, dict[str, Any]]:
    """Langkah 2-4. Mengembalikan (kode keluar, rincian)."""
    detail: dict[str, Any] = {}
    owned_before = expand.owned_ids()
    status = expand.failure_status(expand.load_failures(), owned_before)
    retry_code = 0
    if status["id_bisa_dicoba_ulang"]:
        print(f"--- coba ulang {len(status['id_bisa_dicoba_ulang'])} kegagalan terbuka ---")
        retry_code = expand.run_retry(False)
        detail["kode_coba_ulang"] = retry_code
        if retry_code == expand.EXIT_NETWORK_DOWN:
            return retry_code, detail

    forward_path = expand.EXPANSION_DIR / f"forward_{today}.json"
    if forward_path.exists():
        print(f"--- mode maju dilewati: {forward_path.name} sudah ada (sudah berjalan hari ini) ---")
        forward_code, detail["mode_maju"] = 0, "dilewati: sudah berjalan hari ini"
    else:
        print("--- mode maju ---")
        forward_code = expand.run_forward(expand.load_state(), MAX_PAGES)
        detail["mode_maju"] = "dijalankan"
        if forward_path.exists():
            articles = json.loads(forward_path.read_text(encoding="utf-8"))
            detail["kualitas"] = quality_report(articles, owned_before)
            if detail["kualitas"]["tahan_penggabungan"] and forward_code == 0:
                forward_code = expand.EXIT_NEEDS_REVIEW
    detail["kode_mode_maju"] = forward_code
    return (forward_code or retry_code), detail


def run_once(notify: bool = True) -> int:
    """Satu jalan pembaruan. Mengembalikan kode keluar (lihat docstring modul)."""
    exp = expand.EXPANSION_DIR
    exp.mkdir(parents=True, exist_ok=True)
    lock, history = exp / LOCK_NAME, exp / HISTORY_NAME
    if not acquire_lock(lock):
        print(f"jalan lain sedang berlangsung (kunci {lock}); jalan ini dilewati")
        return EXIT_LOCKED
    started = now_utc()
    wib = started.astimezone(ZoneInfo("Asia/Jakarta"))
    today = wib.date().isoformat()
    log_path = exp / LOG_DIR_NAME / f"pembaruan_{started.strftime('%Y%m%dT%H%M%SZ')}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    status: dict[str, Any] = {"waktu_utc": started.isoformat(timespec="seconds"),
                              "waktu_wib": wib.strftime("%Y-%m-%d %H:%M"), "log": str(log_path),
                              "berkas_status": str(exp / STATUS_NAME)}
    try:
        with open(log_path, "w", encoding="utf-8") as log_file, contextlib.redirect_stdout(_Tee(sys.stdout, log_file)):
            stuck = consecutive_systematic(history)
            if stuck >= MAX_CONSECUTIVE_SYSTEMATIC:
                print(f"BERHENTI MENCOBA: {stuck} jalan beruntun ditahan (kegagalan sistematis). "
                      "Perbaiki penyebabnya lalu jalankan: python -m scraping.scheduled --reset")
                code, status["berhenti_mencoba"] = expand.EXIT_HELD_SYSTEMATIC, True
            else:
                try:
                    code, detail = _scrape_steps(today)
                    status.update(detail)
                except Exception as e:  # noqa: BLE001 -- dicatat lengkap; pembungkus tak boleh mati diam-diam
                    code = classify_exception(e)
                    status["galat"] = f"{type(e).__name__}: {e}"
                    print("".join(traceback.format_exception(e)), end="")
            after = expand.failure_status(expand.load_failures(), expand.owned_ids())
            status.update({
                "kode_keluar": code, "arti": EXIT_MEANING.get(code, "tidak dikenal"),
                "gagal_terbuka": after["terbuka"], "bisa_dicoba_ulang": after["id_bisa_dicoba_ulang"],
                "perlu_tinjauan": after["id_perlu_tinjauan"], "gagal_per_jenis": after["terbuka_per_jenis"],
                "antrean_belum_digabung": pending_merge(),
                "durasi_detik": round((now_utc() - started).total_seconds(), 1),
            })
            if code == 0 and after["id_perlu_tinjauan"]:
                # jalan ini bersih, tetapi masih ada artikel gagal permanen yang belum ditinjau
                status["kode_keluar"] = code = expand.EXIT_NEEDS_REVIEW
                status["arti"] = EXIT_MEANING[code]
            print(f"=== selesai: kode {code} ({status['arti']}); antrean belum digabung {status['antrean_belum_digabung']} ===")
            if code == 0:
                if MARKER_PATH.exists():
                    MARKER_PATH.unlink()
                    print(f"penanda {MARKER_PATH.name} dihapus (jalan bersih)")
                status["notifikasi"] = "tidak perlu"
            else:
                MARKER_PATH.write_text(marker_text(status), encoding="utf-8")
                print(f"penanda ditulis: {MARKER_PATH}")
                if notify:
                    sent = notify_windows("Pembaruan basis data cek fakta: perlu perhatian",
                                          f"Kode {code}: {status['arti']}. Lihat {MARKER_PATH.name} di folder proyek.")
                    status["notifikasi"] = "terkirim" if sent else "GAGAL dikirim"
                else:
                    status["notifikasi"] = "dimatikan (--no-notify)"
                print(f"notifikasi Windows: {status['notifikasi']}")
            (exp / STATUS_NAME).write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            with open(history, "a", encoding="utf-8") as h:
                h.write(json.dumps({k: status.get(k) for k in ("waktu_utc", "kode_keluar", "arti", "antrean_belum_digabung",
                                                               "gagal_terbuka", "berhenti_mencoba")}, ensure_ascii=False) + "\n")
        return code
    finally:
        lock.unlink(missing_ok=True)


def reset() -> None:
    """Putus hitungan 'berhenti mencoba' setelah penyebab kegagalan sistematis diperbaiki."""
    history = expand.EXPANSION_DIR / HISTORY_NAME
    history.parent.mkdir(parents=True, exist_ok=True)
    with open(history, "a", encoding="utf-8") as h:
        h.write(json.dumps({"waktu_utc": now_utc().isoformat(timespec="seconds"), "reset": True}, ensure_ascii=False) + "\n")
    print("hitungan 'berhenti mencoba' direset; jalan berikutnya akan mencoba lagi")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--no-notify", action="store_true", help="jangan kirim notifikasi Windows (penanda tetap ditulis)")
    ap.add_argument("--reset", action="store_true", help="reset hitungan 'berhenti mencoba' lalu keluar")
    args = ap.parse_args()
    if args.reset:
        reset()
        return 0
    return run_once(notify=not args.no_notify)


if __name__ == "__main__":
    sys.exit(main())
