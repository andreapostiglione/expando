import os
from pathlib import Path

from expando.lock import SingleInstanceLock


def test_single_instance_lock(tmp_path: Path):
    lock_path = tmp_path / "expando.lock"
    first = SingleInstanceLock(lock_path)
    second = SingleInstanceLock(lock_path)

    assert first.acquire() is True
    assert second.acquire() is False

    first.release()
    assert second.acquire() is True
    second.release()


def test_single_instance_lock_non_blocking(tmp_path: Path):
    lock_path = tmp_path / "expando.lock"
    first = SingleInstanceLock(lock_path)
    second = SingleInstanceLock(lock_path)

    assert first.acquire(blocking=False) is True
    assert second.acquire(blocking=False) is False

    first.release()
    assert second.acquire(blocking=False) is True
    second.release()