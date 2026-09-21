"""
Pembatas laju sisi klien: jendela geser 60 dtk untuk RPM dan TPM.

Tujuan: batas per menit tidak pernah tersentuh, sehingga retry 429 hanya jaring pengaman.
"""

import time
from collections import deque
from collections.abc import Callable

from llm.limits import ModelLimits


WINDOW_S = 60.0


MARGIN_S = 0.5  # tambahan di atas jendela 60 dtk agar tidak berada tepat di batas


class RateLimiter:
    """
    Jendela geser 60 dtk untuk RPM dan TPM. `acquire` menunggu secukupnya agar
    permintaan berikutnya tidak melampaui batas pada jendela mana pun (yang juga
    menjamin tidak melampaui batas pada menit kalender mana pun). Setiap percobaan,
    termasuk retry, harus melewati `acquire`.
    """

    def __init__(
        self,
        limits: ModelLimits,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.limits = limits
        self._clock, self._sleep = clock, sleep
        self._events: deque[list] = deque()  # [waktu, token]

    def _prune(self, now: float) -> None:
        while self._events and self._events[0][0] <= now - WINDOW_S:
            self._events.popleft()

    def _wait_needed(self, now: float, est_tokens: int) -> float:
        lim = self.limits
        wait = 0.0
        if len(self._events) >= lim.rpm:
            wait = max(wait, self._events[0][0] + WINDOW_S - now)
        used = sum(e[1] for e in self._events)
        if used + est_tokens > lim.tpm:
            need, freed = used + est_tokens - lim.tpm, 0
            for t, k in self._events:
                freed += k
                if freed >= need:
                    wait = max(wait, t + WINDOW_S - now)
                    break
        return wait

    def acquire(self, est_tokens: int) -> float:
        """Blok sampai boleh mengirim; catat permintaan. Mengembalikan detik menunggu."""
        if est_tokens > self.limits.tpm:
            raise ValueError(
                f"Satu prompt (~{est_tokens} token) melebihi TPM model ({self.limits.tpm}); "
                "tidak akan pernah bisa dikirim."
            )
        waited = 0.0
        for _ in range(1000):  # pagar: jangan berputar selamanya bila jam macet
            now = self._clock()
            self._prune(now)
            wait = self._wait_needed(now, est_tokens)
            if wait <= 0:
                self._events.append([now, est_tokens])
                return waited
            self._sleep(wait + MARGIN_S)
            waited += wait + MARGIN_S
        raise RuntimeError("RateLimiter tidak kunjung memberi izin (jam tidak maju?)")

    def settle(self, actual_tokens: int | None) -> None:
        """Ganti perkiraan token permintaan terakhir dengan angka nyata dari server."""
        if actual_tokens is not None and self._events:
            self._events[-1][1] = actual_tokens
