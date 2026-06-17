from __future__ import annotations

import time
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class TimedCache(Generic[T]):
    def __init__(self, ttl_seconds: float = 0.25) -> None:
        self._ttl = ttl_seconds
        self._value: T | None = None
        self._expires_at = 0.0

    def get(self, factory: Callable[[], T]) -> T:
        now = time.monotonic()
        if self._value is not None and now < self._expires_at:
            return self._value
        self._value = factory()
        self._expires_at = time.monotonic() + self._ttl
        return self._value

    def invalidate(self) -> None:
        self._value = None
        self._expires_at = 0.0