"""Uji pembatas laju jendela geser (llm.throttle).
"""


def test_rate_limiter_sliding_window() -> None:
    from llm.limits import ModelLimits
    from llm.throttle import RateLimiter

    now = [0.0]
    sleeps: list[float] = []

    def sleep(x: float) -> None:
        sleeps.append(x)
        now[0] += x

    # RPM 5: dalam JENDELA 60 dtk mana pun tak boleh ada > 5 permintaan
    rl = RateLimiter(ModelLimits(rpm=5, tpm=250_000, rpd=20), clock=lambda: now[0], sleep=sleep)
    stamps = []
    for _ in range(13):
        rl.acquire(100)
        stamps.append(now[0])
    for t in stamps:
        in_window = [x for x in stamps if t - 60 < x <= t]
        assert len(in_window) <= 5, f"jendela 60 dtk berisi {len(in_window)} permintaan"
    assert sleeps and abs(sleeps[0] - 60.5) < 1e-6, "permintaan ke-6 menunggu 60 dtk + margin 0,5 dtk"

    # TPM: dua prompt 600 token tak muat dalam 1000 token/menit -> yang kedua menunggu
    now[0], sleeps[:] = 0.0, []
    rl = RateLimiter(ModelLimits(rpm=100, tpm=1000, rpd=100), clock=lambda: now[0], sleep=sleep)
    rl.acquire(600)
    assert rl.acquire(600) > 0 and sleeps
    # settle: perkiraan besar diganti angka nyata kecil -> permintaan berikut tidak menunggu
    now[0], sleeps[:] = 0.0, []
    rl = RateLimiter(ModelLimits(rpm=100, tpm=1000, rpd=100), clock=lambda: now[0], sleep=sleep)
    rl.acquire(900)
    rl.settle(100)
    assert rl.acquire(900) == 0 and not sleeps
    # prompt yang mustahil muat di TPM ditolak, bukan menunggu selamanya
    try:
        rl.acquire(5000)
        raise AssertionError("seharusnya ValueError")
    except ValueError:
        pass
