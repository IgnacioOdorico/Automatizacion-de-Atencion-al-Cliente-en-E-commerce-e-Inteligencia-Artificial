import copy
import json

import pytest

from app.core.redaction import (
    REDACTED,
    build_preview,
    is_sensitive_key,
    redact_string,
    redact_value,
)

JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0."
    "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJVadQssw5c"
)
OPENAI_KEY = "sk-proj-Abc123Def456Ghi789Jkl012Mno345Pqr678"
BOT_TOKEN = "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw0"
BASE64_KEY = "dGhpc0lzQVNlY3JldEtleTEyMzQ1Njc4OTBhYmNkZWZnaA1234"
HEX_KEY = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"


# ---------------------------------------------------------------- por clave


@pytest.mark.parametrize(
    "key",
    [
        "authorization",
        "Authorization",
        "AUTHORIZATION",
        "token",
        "Token",
        "secret",
        "password",
        "Password",
        "passwd",
        "api_key",
        "apiKey",
        "API_KEY",
        "apikey",
        "x-api-key",
        "cookie",
        "Cookie",
        "set-cookie",
        "Set-Cookie",
        "x-n8n-secret",
        "X-N8N-SECRET",
        "access_token",
        "accessToken",
        "refresh_token",
        "id_token",
        "bot_token",
        "client_secret",
        "clientSecret",
        "private_key",
        "credentials",
        "proxy-authorization",
    ],
)
def test_sensitive_keys_are_detected_case_insensitively(key):
    assert is_sensitive_key(key)


@pytest.mark.parametrize(
    "key",
    [
        "name",
        "order_number",
        "customer_email",
        "message",
        "tokenUsage",
        "promptTokens",
        "completionTokens",
        "totalTokens",
        "author",
        "monkey",
        "status",
        "content-type",
        "host",
        "user-agent",
    ],
)
def test_harmless_keys_are_not_flagged(key):
    assert not is_sensitive_key(key)


def test_values_under_sensitive_keys_are_redacted_whatever_their_type():
    data = {
        "authorization": "Bearer abc",
        "token": 12345,
        "secret": {"nested": "value"},
        "password": ["a", "b"],
        "cookie": None,
        "Api_Key": True,
        "name": "visible",
    }
    assert redact_value(data) == {
        "authorization": REDACTED,
        "token": REDACTED,
        "secret": REDACTED,
        "password": REDACTED,
        "cookie": REDACTED,
        "Api_Key": REDACTED,
        "name": "visible",
    }


def test_sensitive_keys_are_redacted_at_any_depth_and_inside_arrays():
    data = {
        "json": {
            "headers": {"Authorization": "Bearer xyz", "accept": "*/*"},
            "items": [
                {"id": 1, "access_token": "aaa"},
                [{"deep": {"deeper": {"client_secret": "bbb", "ok": 2}}}],
            ],
        }
    }
    assert redact_value(data) == {
        "json": {
            "headers": {"Authorization": REDACTED, "accept": "*/*"},
            "items": [
                {"id": 1, "access_token": REDACTED},
                [{"deep": {"deeper": {"client_secret": REDACTED, "ok": 2}}}],
            ],
        }
    }


def test_token_usage_counters_survive():
    data = {"tokenUsage": {"promptTokens": 12, "completionTokens": 30, "totalTokens": 42}}
    assert redact_value(data) == data


# ----------------------------------------------------------------- por valor


@pytest.mark.parametrize(
    "secret",
    [
        JWT,
        OPENAI_KEY,
        "sk-ant-api03-Abc123Def456Ghi789Jkl012Mno345",
        BOT_TOKEN,
        BASE64_KEY,
        HEX_KEY,
        "AIzaSyA1234567890abcdefghijklmnopqrstuvw",
        "ya29.a0AfH6SMBx1234567890abcdefghijklmnop",
        "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8",
        "xoxb-1234567890-abcdefghijkl",
    ],
)
def test_token_shaped_values_are_redacted_even_under_harmless_keys(secret):
    assert redact_value({"comment": secret}) == {"comment": REDACTED}
    assert redact_value([secret]) == [REDACTED]
    assert redact_value(secret) == REDACTED


@pytest.mark.parametrize(
    "template",
    [
        "Authorization: Bearer {s}",
        "falló con {s} en la llamada",
        "https://api.telegram.org/bot{s}/sendMessage",
        "key={s}&other=1",
        "[{s}]",
    ],
)
@pytest.mark.parametrize("secret", [JWT, OPENAI_KEY, BOT_TOKEN])
def test_tokens_embedded_in_text_are_redacted_but_the_text_survives(template, secret):
    clean = redact_string(template.format(s=secret))
    assert secret not in clean
    assert REDACTED in clean
    assert len(clean) > len(REDACTED)


def test_bearer_and_basic_credentials_are_redacted():
    assert redact_string("Bearer abcdef1234567890") == REDACTED
    assert redact_string("bearer   abcdef1234567890") == REDACTED
    assert "dXNlcjpwYXNz" not in redact_string("Authorization: Basic dXNlcjpwYXNzd29yZA==")


@pytest.mark.parametrize(
    "harmless",
    [
        "ORD-E2E-001",
        "e2e-test@example.com",
        "5492615550100",
        "¿Dónde está mi pedido?",
        "http://localhost:5678/webhook/orden-nueva",
        "2026-09-21T01:06:41.028Z",
        "3f2b1c4e-9a7d-4e21-8c55-0a1b2c3d4e5f",  # UUID
        "orden-de-compra-especial-para-cliente-mayorista-2026-septiembre",
        "n8n-nodes-base.postgres",
        "Credential with ID does not exist for type postgres",
        "El pedido ORD-123 fue confirmado y se envió el correo al cliente",
        "1234567890",
        "",
    ],
)
def test_ordinary_text_is_not_touched(harmless):
    assert redact_string(harmless) == harmless
    assert redact_value({"campo": harmless}) == {"campo": harmless}


def test_numbers_booleans_and_none_pass_through():
    assert redact_value([1, 2.5, True, None]) == [1, 2.5, True, None]


def test_redaction_does_not_mutate_the_input():
    data = {"token": "abc", "items": [{"password": "p", "v": JWT}]}
    snapshot = copy.deepcopy(data)
    redact_value(data)
    assert data == snapshot


def test_exhaustive_walk_leaves_no_secret_in_the_serialized_output():
    payload = {
        "headers": {
            "Authorization": f"Bearer {JWT}",
            "x-n8n-secret": "shh-shh-shh-shh-shh-shh-shh-shh-shh-shh",
            "Cookie": "session=abc123; other=def456",
            "Set-Cookie": ["a=b", "c=d"],
            "accept": "application/json",
        },
        "body": {
            "user": {"name": "Ana", "password": "hunter2hunter2", "api_key": OPENAI_KEY},
            "notes": [f"token {BOT_TOKEN} visto", {"refresh_token": "rrr", "n": [1, 2]}],
            "url": f"https://api.telegram.org/bot{BOT_TOKEN}/getMe",
            "blob": BASE64_KEY,
        },
        "list": [[[[{"client_secret": "zzz", "hash": HEX_KEY}]]]],
    }
    dumped = json.dumps(redact_value(payload), ensure_ascii=False)
    for secret in (
        JWT,
        OPENAI_KEY,
        BOT_TOKEN,
        BASE64_KEY,
        HEX_KEY,
        "hunter2hunter2",
        "shh-shh",
        "abc123",
        "rrr",
        "zzz",
    ):
        assert secret not in dumped, secret
    assert "Ana" in dumped
    assert "application/json" in dumped


# ------------------------------------------------------------ topes y vista


def test_cyclic_structures_terminate():
    node: dict = {"name": "n"}
    node["self"] = node
    node["list"] = [node, node]
    result = redact_value(node)
    assert result["name"] == "n"


def test_shared_reference_bombs_are_bounded():
    layer: dict = {"leaf": "x"}
    for _ in range(40):
        layer = {"a": layer, "b": layer, "c": layer}
    result, truncated = build_preview([layer])
    assert truncated is True
    assert len(json.dumps(result)) <= 2048


def test_preview_of_small_values_is_returned_untouched():
    items = [{"order_number": "ORD-1", "quantity": 2}]
    preview, truncated = build_preview(items)
    assert preview == items
    assert truncated is False


def test_preview_is_capped_to_about_two_kilobytes():
    items = [{"id": n, "texto": "lorem ipsum " * 40, "lista": list(range(50))} for n in range(30)]
    preview, truncated = build_preview(items)
    assert truncated is True
    assert len(json.dumps(preview, ensure_ascii=False).encode("utf-8")) <= 2048


def test_preview_redacts_before_truncating_strings():
    text = "A" * 150 + " " + OPENAI_KEY + " " + "B" * 400
    preview, _ = build_preview([{"texto": text}])
    dumped = json.dumps(preview)
    assert "sk-" not in dumped
    assert OPENAI_KEY[:12] not in dumped


def test_preview_redacts_sensitive_keys():
    preview, _ = build_preview([{"headers": {"authorization": "Bearer 12345678"}, "ok": 1}])
    assert preview == [{"headers": {"authorization": REDACTED}, "ok": 1}]


def test_preview_of_nothing_is_none():
    assert build_preview([]) == (None, False)
    assert build_preview(None) == (None, False)


def test_preview_limits_wide_objects():
    keys = {f"campo_{n:04d}": n for n in range(400)}
    preview, truncated = build_preview([keys])
    assert truncated is True
    assert len(json.dumps(preview, ensure_ascii=False).encode("utf-8")) <= 2048


def test_preview_falls_back_to_text_when_nothing_fits():
    preview, truncated = build_preview([{"campo": "valor"}] * 3, max_bytes=12)
    assert truncated is True
    assert isinstance(preview, str)
    assert preview.endswith("…")
    assert len(preview) < 12


def test_full_redaction_of_a_reference_bomb_is_bounded():
    layer: dict = {"leaf": "x"}
    for _ in range(60):
        layer = {"a": layer, "b": layer, "c": layer, "token": "zzz"}
    result = redact_value(layer)
    assert result["token"] == REDACTED
