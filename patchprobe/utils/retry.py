from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(fn: Callable[[], T], attempts: int = 3, delay: float = 0.5) -> T:
    last_exc = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last_exc = e
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]
