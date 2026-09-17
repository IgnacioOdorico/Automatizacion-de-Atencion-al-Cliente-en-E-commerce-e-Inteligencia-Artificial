import time
from collections import defaultdict

WINDOW_SECONDS = 300
MAX_FAILURES = 5

_failures: dict[str, list[float]] = defaultdict(list)


def _prune(key: str, now: float) -> None:
    threshold = now - WINDOW_SECONDS
    _failures[key] = [stamp for stamp in _failures[key] if stamp > threshold]


def is_blocked(*keys: str) -> bool:
    now = time.monotonic()
    for key in keys:
        _prune(key, now)
        if len(_failures[key]) >= MAX_FAILURES:
            return True
    return False


def record_failure(*keys: str) -> None:
    now = time.monotonic()
    for key in keys:
        _failures[key].append(now)


def clear(*keys: str) -> None:
    for key in keys:
        _failures.pop(key, None)


def reset() -> None:
    _failures.clear()