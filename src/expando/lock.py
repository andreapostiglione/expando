from __future__ import annotations

import fcntl
import os
from pathlib import Path


class SingleInstanceLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle = None

    def acquire(self, *, blocking: bool = False) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = open(self.path, "a+", encoding="utf-8")
        flags = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
        try:
            fcntl.flock(self._handle.fileno(), flags)
        except BlockingIOError:
            self._handle.close()
            self._handle = None
            return False

        self._handle.seek(0)
        self._handle.write(str(os.getpid()))
        self._handle.truncate()
        self._handle.flush()
        return True

    def release(self) -> None:
        if not self._handle:
            return
        try:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
            self._handle.close()
        finally:
            self._handle = None
            self.path.unlink(missing_ok=True)

    def __enter__(self) -> SingleInstanceLock:
        if not self.acquire():
            raise RuntimeError("Another Expando instance is already running")
        return self

    def __exit__(self, *_args) -> None:
        self.release()
