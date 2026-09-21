"""Cursores opacos (keyset) y formato de fechas para el monitoreo.

Un cursor es un JSON `[tipo, ts_iso_microsegundos, ...resto]` en base64 url-safe.
El `ts` conserva los microsegundos de la BD: con el resto de la tupla desempata
eventos que comparten timestamp, así paginar no repite ni salta filas.
"""

import base64
import binascii
import json
from datetime import datetime, timezone

UTC = timezone.utc


class CursorError(ValueError):
    """El cursor recibido no es válido."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def to_iso(value: datetime | None) -> str | None:
    """ISO 8601 en UTC con milisegundos y `Z` (los naive se asumen UTC)."""
    if value is None:
        return None
    return _as_utc(value).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def encode_cursor(kind: str, ts: datetime, *rest: int | str) -> str:
    payload = [kind, _as_utc(ts).isoformat(timespec="microseconds"), *rest]
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(token: str, kind: str) -> tuple:
    """Devuelve `(ts, *rest)`; levanta `CursorError` si no es un cursor de `kind`."""
    try:
        padded = token + "=" * (-len(token) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        if not isinstance(payload, list) or len(payload) < 3 or payload[0] != kind:
            raise CursorError("Cursor inválido")
        ts = datetime.fromisoformat(payload[1])
    except CursorError:
        raise
    except (ValueError, TypeError, binascii.Error, UnicodeError) as exc:
        raise CursorError("Cursor inválido") from exc
    for item in payload[2:]:
        if isinstance(item, bool) or not isinstance(item, (int, str)):
            raise CursorError("Cursor inválido")
    return (_as_utc(ts), *payload[2:])
