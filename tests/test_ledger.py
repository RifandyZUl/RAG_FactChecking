"""Uji buku besar kuota harian dan perencanaan anggaran (llm.ledger).
"""

from datetime import UTC
from pathlib import Path


def test_daily_ledger_and_budget() -> None:
    import tempfile
    from datetime import datetime

    from llm.ledger import DailyLedger, plan_budget
    from llm.limits import ModelLimits

    def at(*a):
        return lambda: datetime(*a, tzinfo=UTC)

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "ledger.json"
        # Musim panas (PDT, UTC-7): tengah malam Pasifik = 07:00 UTC
        before = DailyLedger("m", path, at(2026, 9, 21, 6, 59))
        after = DailyLedger("m", path, at(2026, 9, 21, 7, 1))
        assert before.day_key() == "2026-09-20" and after.day_key() == "2026-09-21"
        assert before.next_reset() == datetime(2026, 9, 21, 7, 0, tzinfo=UTC)
        # Musim dingin (PST, UTC-8): tengah malam Pasifik = 08:00 UTC
        assert DailyLedger("m", path, at(2026, 11, 2, 7, 59)).day_key() == "2026-11-01"
        assert DailyLedger("m", path, at(2026, 11, 2, 8, 1)).day_key() == "2026-11-02"
        assert DailyLedger("m", path, at(2026, 11, 2, 7, 59)).next_reset() == \
            datetime(2026, 11, 2, 8, 0, tzinfo=UTC)

        assert before.used_today() == 0
        before.add()
        before.add(3)
        assert before.used_today() == 4 and after.used_today() == 0, "hari baru mulai dari nol"
        assert DailyLedger("lain", path, at(2026, 9, 21, 6, 59)).used_today() == 0, "per model"
        before.seed(21)
        assert before.used_today() == 21

        lim = ModelLimits(rpm=5, tpm=250_000, rpd=20)
        plan = plan_budget(before, lim, n_queries=10, calls_per_query_worst=2)
        assert plan.remaining == 0 and not plan.ok, "21/20 terpakai: jangan mulai"
        plan = plan_budget(after, lim, n_queries=10, calls_per_query_worst=2)
        assert plan.ok and plan.remaining == 20 and plan.worst_case == 20
        after.seed(15)
        plan = plan_budget(after, lim, n_queries=10, calls_per_query_worst=2)
        assert not plan.ok and plan.remaining == 5
        after.seed(0)
        assert not plan_budget(after, lim, 21, 2).ok


def test_ledger_events_record_origin_and_attempt(tmp_path: Path, monkeypatch) -> None:
    import json
    from datetime import datetime

    from llm.ledger import DailyLedger

    monkeypatch.setenv("RAG_LEDGER_ORIGIN", "uji asal")
    led = DailyLedger("m", tmp_path / "ledger.json", lambda: datetime(2026, 10, 19, 6, 0, tzinfo=UTC))
    led.add(1, attempt=1)
    led.add(1, attempt=2)
    led.add()
    events = [json.loads(x) for x in led.events_path.read_text(encoding="utf-8").splitlines()]
    assert [e["percobaan"] for e in events] == [1, 2, None]
    assert [e["total_hari_ini"] for e in events] == [1, 2, 3] == [led.used_today() - 2, 2, led.used_today()]
    assert {e["asal"] for e in events} == {"uji asal"}
    assert events[0]["hari_pasifik"] == "2026-10-18" and events[0]["waktu_utc"] == "2026-10-19T06:00:00+00:00"
    assert json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8")) == {"m": {"2026-10-18": 3}}


def _fixed_now():
    from datetime import datetime

    return datetime(2026, 10, 22, 12, 0, tzinfo=UTC)


def test_concurrent_threads_never_lose_an_increment(tmp_path: Path) -> None:
    """Banyak utas (sesi demo) menambah bersamaan: total = jumlah semua penambahan."""
    import threading

    from llm.ledger import DailyLedger

    path = tmp_path / "ledger.json"
    threads_n, adds_per_thread = 8, 25
    start = threading.Barrier(threads_n)

    def worker() -> None:
        ledger = DailyLedger("m", path, _fixed_now)  # instans terpisah, berkas sama
        start.wait()
        for _ in range(adds_per_thread):
            ledger.add()

    threads = [threading.Thread(target=worker) for _ in range(threads_n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert DailyLedger("m", path, _fixed_now).used_today() == threads_n * adds_per_thread
    events = (tmp_path / "ledger_events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(events) == threads_n * adds_per_thread


_CHILD = """
import sys
from datetime import datetime, timezone
from pathlib import Path
from llm.ledger import DailyLedger
ledger = DailyLedger("m", Path(sys.argv[1]), lambda: datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc))
for _ in range(int(sys.argv[2])):
    ledger.add()
"""


def _python_env() -> dict:
    import os

    src = str(Path(__file__).resolve().parent.parent / "src")
    return {**os.environ, "PYTHONPATH": src, "RAG_LEDGER_ORIGIN": "uji"}


def test_concurrent_processes_never_lose_an_increment(tmp_path: Path) -> None:
    """Proses berbeda (demo dan evaluasi) berbagi berkas: kunci berkas OS mencegah saling menimpa."""
    import subprocess
    import sys

    from llm.ledger import DailyLedger

    path = tmp_path / "ledger.json"
    procs = [subprocess.Popen([sys.executable, "-c", _CHILD, str(path), "40"], env=_python_env())
             for _ in range(4)]
    assert [p.wait(timeout=120) for p in procs] == [0, 0, 0, 0]
    assert DailyLedger("m", path, _fixed_now).used_today() == 160


_HOLD_AND_DIE = """
import os, sys, time
from pathlib import Path
from llm.ledger import file_lock
with file_lock(Path(sys.argv[1])):
    print("terkunci", flush=True)
    os._exit(0)  # mati tanpa melepas kunci
"""


def test_lock_held_by_a_dead_process_is_released(tmp_path: Path) -> None:
    """Proses yang mati saat memegang kunci tidak meninggalkan kunci: OS melepasnya."""
    import subprocess
    import sys
    import time

    from llm.ledger import file_lock

    path = tmp_path / "ledger.json"
    out = subprocess.run([sys.executable, "-c", _HOLD_AND_DIE, str(path)], env=_python_env(),
                         capture_output=True, text=True, timeout=60, check=False)
    assert out.stdout.strip() == "terkunci" and (tmp_path / "ledger.json.lock").exists()
    t = time.monotonic()
    with file_lock(path, timeout_s=5):
        pass
    assert time.monotonic() - t < 1.0


_HOLD_FOR_TEN_SECONDS = """
import sys, time
from pathlib import Path
from llm.ledger import file_lock
with file_lock(Path(sys.argv[1])):
    print("terkunci", flush=True)
    time.sleep(10)
"""


def test_lock_times_out_while_another_process_holds_it(tmp_path: Path) -> None:
    import subprocess
    import sys

    import pytest

    from llm.ledger import file_lock

    path = tmp_path / "ledger.json"
    holder = subprocess.Popen([sys.executable, "-c", _HOLD_FOR_TEN_SECONDS, str(path)],
                              env=_python_env(), stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout is not None and holder.stdout.readline().strip() == "terkunci"
        with pytest.raises(TimeoutError), file_lock(path, timeout_s=0.3):
            pass
    finally:
        holder.kill()
        holder.wait()
