"""Peluncur container (webapp.serve): penanda siap hanya ditulis setelah pemanasan berhasil."""

import threading
from pathlib import Path

from webapp import resources, serve
from webapp.resources import WarmupState


def test_ready_file_is_written_only_after_warmup_succeeds(tmp_path: Path) -> None:
    states = iter([WarmupState.RUNNING, WarmupState.RUNNING, WarmupState.READY])
    seen_before_ready: list[bool] = []
    marker = tmp_path / "siap"

    def state() -> WarmupState:
        seen_before_ready.append(marker.exists())
        return next(states)

    assert serve.wait_and_mark_ready(state, WarmupState.READY, WarmupState.FAILED, marker, poll_s=0) is True
    assert marker.is_file()
    assert seen_before_ready == [False, False, False]


def test_failed_warmup_never_writes_the_ready_file(tmp_path: Path) -> None:
    marker = tmp_path / "siap"
    states = iter([WarmupState.RUNNING, WarmupState.FAILED])
    assert serve.wait_and_mark_ready(lambda: next(states), WarmupState.READY, WarmupState.FAILED, marker,
                                     poll_s=0) is False
    assert not marker.exists()


def test_ready_file_follows_the_real_warmup(tmp_path: Path) -> None:
    """Dengan pemanasan sungguhan (pemuat palsu): penanda muncul setelah semua pemuat selesai."""
    gate = threading.Event()
    loaders = (resources._Once("palsu", lambda: gate.wait(5)),)
    marker = tmp_path / "siap"
    saved = resources._warmup_thread, resources._warmup_state
    resources._warmup_thread, resources._warmup_state = None, WarmupState.NOT_STARTED
    try:
        assert resources.start_warmup(loaders) is True
        watcher = threading.Thread(target=serve.wait_and_mark_ready, kwargs={
            "state": resources.warmup_state, "ready": WarmupState.READY, "failed": WarmupState.FAILED,
            "ready_file": marker, "poll_s": 0.01})
        watcher.start()
        watcher.join(0.2)
        assert not marker.exists(), "penanda tidak boleh ada selama pemanasan berjalan"
        gate.set()
        watcher.join(5)
        assert marker.is_file()
    finally:
        resources._warmup_thread, resources._warmup_state = saved
