"""
Probe tunggal ke server (LIVE, memakai 1 permintaan dari kuota harian model).

Tujuan: memastikan bentuk galat 429 ASLI (quotaId, retryDelay) dan bahwa satu
panggilan bertema-kecil berhasil. `classify_429` dan uji offline memakai bentuk
galat Gemini yang umum; probe ini membuktikan (atau menyangkal) bentuk itu pada
akun ini. Permintaan dicatat di buku besar harian seperti panggilan lain.

Pemakaian: python src/probe_quota.py [--model ID]
"""

import argparse
import json
import sys
import time

from llm import LLMConfigError, LLMQuotaExhaustedError, get_provider
from llm.gemini_errors import classify_429, error_payload, hinted_delay_s
from llm.limits import estimate_tokens

PROMPT = "Balas dengan satu kata: siap"


def quota_ids(payload: object) -> list[str]:
    """Semua quotaId/quotaMetric pada isi galat (untuk ditampilkan, bukan rahasia)."""
    found: list[str] = []
    stack = [payload]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k in ("quotaId", "quotaMetric"):
                if isinstance(cur.get(k), str):
                    found.append(f"{k}={cur[k]}")
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--model")
    args = ap.parse_args()
    try:
        p = get_provider(**({"model": args.model} if args.model else {}))
    except LLMConfigError as e:
        print(f"Konfigurasi LLM belum siap: {e}")
        return 2

    print(f"Model: {p.model} | thinking: {p.thinking_level} | "
          f"retry internal SDK dimatikan: {p.sdk_retry_disabled}")
    if p.ledger is not None and p.limits is not None:
        print(f"Buku besar lokal: {p.ledger.used_today()}/{p.limits.rpd} terpakai hari ini "
              f"(Pasifik); reset {p.ledger.next_reset().astimezone():%Y-%m-%d %H:%M %Z}")
    t0 = time.monotonic()
    try:
        p._before_call(estimate_tokens(PROMPT), t0, 1, "teks")
    except LLMQuotaExhaustedError as e:
        print("TIDAK DIKIRIM:", e)
        return 4
    try:
        it = p._create("Kamu asisten singkat.", PROMPT, None)
    except Exception as e:  # noqa: BLE001 - dilaporkan apa adanya, bukan ditelan
        print(f"GALAT setelah {time.monotonic() - t0:.1f}s: {type(e).__name__} "
              f"status={getattr(e, 'status_code', None)}")
        payload = error_payload(e)
        if getattr(e, "status_code", None) == 429:
            print("klasifikasi 429 :", classify_429(e))
            print("quotaId/metric  :", quota_ids(payload) or "(tidak ada pada isi galat)")
            print("saran tunggu    :", hinted_delay_s(e))
        print("isi galat (disamarkan):")
        print(p._safe(json.dumps(payload, ensure_ascii=False, indent=1, default=str))[:1500])
        return 1
    u = getattr(it, "usage", None)
    print(f"OK setelah {time.monotonic() - t0:.1f}s | status={getattr(it, 'status', None)} | "
          f"keluaran={p._safe(str(getattr(it, 'output_text', '')))!r} | "
          f"token masuk/keluar/pikir={getattr(u, 'total_input_tokens', None)}/"
          f"{getattr(u, 'total_output_tokens', None)}/{getattr(u, 'total_thought_tokens', None)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
