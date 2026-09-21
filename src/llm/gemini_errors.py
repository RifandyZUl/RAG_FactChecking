"""
Penafsiran galat HTTP Gemini API: isi galat, saran waktu tunggu, klasifikasi 429, dan
ringkasan untuk log. Bentuk galat mengikuti SDK `google-genai` (body berupa dict).
"""

import json
import re
from typing import Any


def error_payload(err: Any) -> Any:
    """Isi JSON galat HTTP. Pada SDK terpasang `body` berupa dict; str diterima juga."""
    body = getattr(err, "body", None)
    if isinstance(body, str) and body:
        try:
            return json.loads(body)
        except ValueError:
            return None
    return body


def _error_headers(err: Any) -> Any:
    """Header respons: `err.headers` bila ada, kalau tidak `err.response.headers`."""
    headers = getattr(err, "headers", None)
    if headers is None:
        headers = getattr(getattr(err, "response", None), "headers", None)
    return headers


def hinted_delay_s(err: Any) -> float | None:
    """Ambil saran waktu tunggu dari galat 429: Retry-After atau RetryInfo.retryDelay."""
    headers = _error_headers(err)
    if headers is not None:
        ra = headers.get("retry-after")
        if ra and re.fullmatch(r"\d+(\.\d+)?", ra.strip()):
            return float(ra)
    stack = [error_payload(err)]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            rd = cur.get("retryDelay")
            if isinstance(rd, str):
                m = re.fullmatch(r"(\d+(?:\.\d+)?)s", rd.strip())
                if m:
                    return float(m.group(1))
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def classify_429(err: Any) -> str:
    """
    Jenis batas pada galat 429: "harian", "per_menit", atau "tidak_diketahui".

    Dibaca dari `quotaId` pada rincian QuotaFailure (mis. ...PerDayPerProjectPer
    Model-FreeTier). Bila ada batas harian di antara pelanggaran, hasilnya "harian"
    karena itu yang mengikat. Format ini dikenal dari galat Gemini API umumnya;
    belum diamati langsung pada akun ini (lihat CLAUDE.md).
    """
    joined = " ".join(_quota_ids(err)).lower()
    if "perday" in joined or "per_day" in joined:
        return "harian"
    if "perminute" in joined or "per_minute" in joined:
        return "per_menit"
    return "tidak_diketahui"


def _quota_ids(err: Any) -> list[str]:
    """Semua nilai quotaId/quotaMetric pada isi galat (kosong bila tidak ada)."""
    ids: list[str] = []
    stack = [error_payload(err)]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for key in ("quotaId", "quotaMetric"):
                if isinstance(cur.get(key), str):
                    ids.append(cur[key])
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return ids


def error_detail(err: Any) -> str:
    """
    Ringkasan isi galat HTTP untuk log: status/pesan server dan quotaId bila ada.

    Ditambahkan setelah 429 pada akun ini tidak dapat diklasifikasi ("tidak_diketahui")
    dan log tidak memuat alasannya. Pemanggil wajib menyamarkan hasilnya (`_safe`).
    """
    payload = error_payload(err)
    body = payload.get("error", payload) if isinstance(payload, dict) else None
    parts: list[str] = []
    if isinstance(body, dict):
        for key in ("status", "message"):
            if isinstance(body.get(key), str):
                parts.append(f"{key}={body[key][:200]!r}")
    ids = _quota_ids(err)
    parts.append(f"quota={ids}" if ids else "quota=(tidak ada quotaId pada isi galat)")
    if not isinstance(body, dict):
        parts.append(f"isi={str(payload)[:120]!r}")
    return " ".join(parts)
