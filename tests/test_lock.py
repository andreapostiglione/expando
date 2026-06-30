import os
from pathlib import Path

from expando.lock import SingleInstanceLock


def test_single_instance_lock(tmp_path: Path):
    lock_path = tmp_path / "expando.lock"
    first = SingleInstanceLock(lock_path)
    second = SingleInstanceLock(lock_path)

    assert first.acquire() is True
    first_pid = lock_path.read_text(encoding="utf-8")
    assert second.acquire() is False
    assert lock_path.read_text(encoding="utf-8") == first_pid

    first.release()
    assert second.acquire() is True
    second.release()


def test_single_instance_lock_non_blocking(tmp_path: Path):
    lock_path = tmp_path / "expando.lock"
    first = SingleInstanceLock(lock_path)
    second = SingleInstanceLock(lock_path)

    assert first.acquire(blocking=False) is True
    first_pid = lock_path.read_text(encoding="utf-8")
    assert second.acquire(blocking=False) is False
    assert lock_path.read_text(encoding="utf-8") == first_pid

    first.release()
    assert second.acquire(blocking=False) is True
    second.release()
