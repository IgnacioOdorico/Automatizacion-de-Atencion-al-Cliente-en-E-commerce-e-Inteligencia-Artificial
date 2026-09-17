import secrets
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.core.config import settings

_records: dict[str, dict] = {}
_current_by_account: dict[int, str] = {}
_lock = Lock()


def reset() -> None:
    with _lock:
        _records.clear()
        _current_by_account.clear()


def start_code(account_id: int) -> dict:
    with _lock:
        previous = _current_by_account.pop(account_id, None)
        if previous:
            _records.pop(previous, None)

        code = f"{secrets.randbelow(1_000_000):06d}"
        while code in _records:
            code = f"{secrets.randbelow(1_000_000):06d}"

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.telegram_code_ttl_minutes
        )
        _records[code] = {"account_id": account_id, "expires_at": expires_at}
        _current_by_account[account_id] = code
        return {
            "code": code,
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "expires_in": settings.telegram_code_ttl_minutes * 60,
        }


def validate_code(code: str) -> dict | None:
    record = _records.get(code)
    if record is None:
        return None
    if datetime.now(timezone.utc) >= record["expires_at"]:
        _records.pop(code, None)
        return None
    return record


def consume(code: str) -> None:
    _records.pop(code, None)