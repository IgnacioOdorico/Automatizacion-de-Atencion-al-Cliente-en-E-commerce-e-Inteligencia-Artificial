from datetime import datetime, timedelta, timezone

import pytest

from app.core.cursors import CursorError, decode_cursor, encode_cursor, to_iso

UTC = timezone.utc


def test_to_iso_formats_utc_with_milliseconds_and_z():
    dt = datetime(2026, 9, 21, 12, 30, 15, 123456, tzinfo=UTC)
    assert to_iso(dt) == "2026-09-21T12:30:15.123Z"


def test_to_iso_converts_other_zones_to_utc():
    dt = datetime(2026, 9, 21, 9, 0, 0, tzinfo=timezone(timedelta(hours=-3)))
    assert to_iso(dt) == "2026-09-21T12:00:00.000Z"


def test_to_iso_treats_naive_datetimes_as_utc():
    assert to_iso(datetime(2026, 9, 21, 12, 0, 0)) == "2026-09-21T12:00:00.000Z"


def test_to_iso_none_is_none():
    assert to_iso(None) is None


def test_cursor_roundtrip_keeps_microseconds():
    ts = datetime(2026, 9, 21, 12, 30, 15, 123456, tzinfo=UTC)
    token = encode_cursor("ev", ts, 40, 77)
    assert decode_cursor(token, "ev") == (ts, 40, 77)


def test_cursor_is_opaque_urlsafe_text():
    token = encode_cursor("ev", datetime(2026, 9, 21, tzinfo=UTC), 10, 1)
    assert all(c.isalnum() or c in "-_" for c in token)
    assert "2026" not in token


@pytest.mark.parametrize("bad", ["", "no-es-base64!", "e30", "W10", "bnVsbA"])
def test_cursor_rejects_garbage(bad):
    with pytest.raises(CursorError):
        decode_cursor(bad, "ev")


def test_cursor_rejects_other_kind():
    token = encode_cursor("conv", datetime(2026, 9, 21, tzinfo=UTC), 0, 5)
    with pytest.raises(CursorError):
        decode_cursor(token, "ev")
