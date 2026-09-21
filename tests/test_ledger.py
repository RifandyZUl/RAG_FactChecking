"""Uji buku besar kuota harian dan perencanaan anggaran (llm.ledger).
"""

from pathlib import Path


def test_daily_ledger_and_budget() -> None:
    import tempfile
    from datetime import datetime, timezone

    from llm.ledger import DailyLedger, plan_budget
    from llm.limits import ModelLimits

    def at(*a):
        return lambda: datetime(*a, tzinfo=timezone.utc)

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "ledger.json"
        # Musim panas (PDT, UTC-7): tengah malam Pasifik = 07:00 UTC
        before = DailyLedger("m", path, at(2026, 9, 21, 6, 59))
        after = DailyLedger("m", path, at(2026, 9, 21, 7, 1))
        assert before.day_key() == "2026-09-20" and after.day_key() == "2026-09-21"
        assert before.next_reset() == datetime(2026, 9, 21, 7, 0, tzinfo=timezone.utc)
        # Musim dingin (PST, UTC-8): tengah malam Pasifik = 08:00 UTC
        assert DailyLedger("m", path, at(2026, 11, 2, 7, 59)).day_key() == "2026-11-01"
        assert DailyLedger("m", path, at(2026, 11, 2, 8, 1)).day_key() == "2026-11-02"
        assert DailyLedger("m", path, at(2026, 11, 2, 7, 59)).next_reset() == \
            datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc)

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
