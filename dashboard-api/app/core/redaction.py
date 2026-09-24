"""Redacción de secretos para todo dato de n8n que sale por la API.

Dos defensas independientes:

- por CLAVE: el valor de una clave sensible (`authorization`, `token`, `password`,
  `x-n8n-secret`, `cookie`, ...) se reemplaza entero, sin importar su tipo ni la
  profundidad, comparando sin distinguir mayúsculas ni separadores;
- por VALOR: en cualquier cadena se reemplaza lo que tenga forma de credencial
  (Bearer/Basic, JWT, `sk-…`, tokens de bot de Telegram, claves de Google/GitHub/Slack,
  hex largo y base64 largo), aunque esté incrustado dentro de un texto más largo.

La redacción de cadenas se hace ANTES de truncar: un token cortado a la mitad ya no
sería reconocible y se filtraría su prefijo.
"""

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

REDACTED = "[REDACTADO]"
TRUNCATED_MARK = "[…]"

# --------------------------------------------------------------------- claves

_SENSITIVE_FRAGMENTS = (
    "authorization",
    "password",
    "passwd",
    "passphrase",
    "secret",
    "cookie",
    "apikey",
    "privatekey",
    "credential",
    "bearer",
)


def is_sensitive_key(key: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
    if any(fragment in normalized for fragment in _SENSITIVE_FRAGMENTS):
        return True
    # `access_token`, `x-auth-token`, `id_token`… pero no los contadores `promptTokens`.
    return normalized.endswith("token") or normalized.endswith("jwt")


# -------------------------------------------------------------------- valores

_TOKEN_PATTERNS = [
    re.compile(r"(?i)\b(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}(?:\.[A-Za-z0-9_-]*)?"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"(?<!\d)\d{8,10}:[A-Za-z0-9_-]{30,}"),
    re.compile(r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"(?<![A-Za-z0-9])ya29\.[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9-]{10,}"),
]
_HEX_KEY = re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])")
_LONG_KEY = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/_-]{40,}={0,2}(?![A-Za-z0-9+/=_-])")


def _entropy(text: str) -> float:
    counts = Counter(text)
    total = len(text)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def _redact_hex(match: re.Match) -> str:
    text = match.group(0)
    has_digit = any(c.isdigit() for c in text)
    has_letter = any(c.isalpha() for c in text)
    return REDACTED if has_digit and has_letter else text


def _redact_long_key(match: re.Match) -> str:
    text = match.group(0)
    looks_random = (
        any(c.isdigit() for c in text)
        and any(c.islower() for c in text)
        and any(c.isupper() for c in text)
        and _entropy(text) >= 4.0
    )
    return REDACTED if looks_random else text


def redact_string(value: str) -> str:
    for pattern in _TOKEN_PATTERNS:
        value = pattern.sub(REDACTED, value)
    value = _HEX_KEY.sub(_redact_hex, value)
    return _LONG_KEY.sub(_redact_long_key, value)


# ------------------------------------------------------------------- recorrido


@dataclass(frozen=True)
class Limits:
    max_depth: int
    max_string: int
    max_list: int
    max_keys: int
    max_nodes: int


class _State:
    def __init__(self) -> None:
        self.nodes = 0
        self.truncated = False


FULL = Limits(max_depth=40, max_string=1_000_000, max_list=10_000, max_keys=10_000, max_nodes=100_000)


def _clip(text: str, limits: Limits, state: _State) -> str:
    if len(text) > limits.max_string:
        state.truncated = True
        return text[: limits.max_string] + "…"
    return text


def _walk(value: Any, depth: int, limits: Limits, state: _State) -> Any:
    state.nodes += 1
    if state.nodes > limits.max_nodes:
        state.truncated = True
        return TRUNCATED_MARK
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _clip(redact_string(value), limits, state)
    if isinstance(value, dict):
        if depth >= limits.max_depth:
            state.truncated = True
            return TRUNCATED_MARK
        result: dict = {}
        for index, (key, child) in enumerate(value.items()):
            if index >= limits.max_keys:
                state.truncated = True
                break
            name = _clip(str(key), limits, state)
            result[name] = REDACTED if is_sensitive_key(key) else _walk(child, depth + 1, limits, state)
        return result
    if isinstance(value, (list, tuple)):
        if depth >= limits.max_depth:
            state.truncated = True
            return TRUNCATED_MARK
        items = []
        for index, child in enumerate(value):
            if index >= limits.max_list:
                state.truncated = True
                break
            items.append(_walk(child, depth + 1, limits, state))
        return items
    return _clip(redact_string(str(value)), limits, state)


def redact_value(value: Any) -> Any:
    """Copia profunda de `value` con todo secreto reemplazado por `[REDACTADO]`."""
    return _walk(value, 0, FULL, _State())


# ---------------------------------------------------------------------- vista

PREVIEW_MAX_BYTES = 2048

# (ítems, largo de cadena, elementos por lista, claves por objeto, profundidad, nodos)
_PREVIEW_LEVELS = (
    (10, 500, 50, 50, 9, 3000),
    (5, 300, 20, 30, 7, 1500),
    (3, 160, 10, 15, 5, 800),
    (2, 80, 5, 8, 4, 400),
    (1, 40, 3, 5, 3, 200),
)


def _size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def build_preview(items: list | None, *, max_bytes: int = PREVIEW_MAX_BYTES) -> tuple[Any, bool]:
    """Vista acotada y redactada de la salida de un nodo: `(valor, recortado)`.

    Devuelve una lista JSON con los primeros ítems y, si ni siquiera el nivel más
    chico entra en `max_bytes`, un texto recortado. `None` si no hay salida.
    """
    if not items:
        return None, False
    result: Any = None
    truncated = False
    for count, max_string, max_list, max_keys, max_depth, max_nodes in _PREVIEW_LEVELS:
        limits = Limits(max_depth, max_string, max_list, max_keys, max_nodes)
        state = _State()
        result = _walk(list(items[:count]), 0, limits, state)
        truncated = state.truncated or len(items) > count
        if _size(result) <= max_bytes:
            return result, truncated
    text = json.dumps(result, ensure_ascii=False)
    budget = max(1, min(len(text), max_bytes // 3))
    return text[:budget] + "…", True
