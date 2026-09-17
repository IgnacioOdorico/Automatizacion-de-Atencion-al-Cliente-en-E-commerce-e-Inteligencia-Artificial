from datetime import datetime, timedelta, timezone

from app.core import telegram_codes


def test_start_returns_six_digit_code():
    result = telegram_codes.start_code(1)
    assert result["code"].isdigit()
    assert len(result["code"]) == 6


def test_ttl_is_15_minutes():
    telegram_codes.reset()
    result = telegram_codes.start_code(1)
    expires = datetime.fromisoformat(result["expires_at"])
    delta = expires - datetime.now(timezone.utc)
    assert timedelta(minutes=14, seconds=55) < delta <= timedelta(minutes=15)


def test_validate_code_returns_account_record():
    telegram_codes.reset()
    code = telegram_codes.start_code(7)["code"]
    record = telegram_codes.validate_code(code)
    assert record["account_id"] == 7


def test_invalid_code_returns_none():
    telegram_codes.reset()
    assert telegram_codes.validate_code("000000") is None


def test_second_start_rotates_and_invalidates_previous():
    telegram_codes.reset()
    first = telegram_codes.start_code(1)["code"]
    second = telegram_codes.start_code(1)["code"]
    assert first != second
    assert telegram_codes.validate_code(first) is None
    assert telegram_codes.validate_code(second) is not None


def test_expired_code_returns_none():
    telegram_codes.reset()
    code = telegram_codes.start_code(1)["code"]
    telegram_codes._records[code]["expires_at"] = datetime.now(timezone.utc) - timedelta(
        seconds=1
    )
    assert telegram_codes.validate_code(code) is None


def test_consume_makes_code_single_use():
    telegram_codes.reset()
    code = telegram_codes.start_code(1)["code"]
    assert telegram_codes.validate_code(code) is not None
    telegram_codes.consume(code)
    assert telegram_codes.validate_code(code) is None