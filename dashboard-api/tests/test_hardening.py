"""Hardening de la Fase 8 (auditoría de seguridad): entradas, tokens, docs, CORS, contenedor."""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

from tests.conftest import DEMO_EMAIL, TEST_N8N_SECRET

API_DIR = Path(__file__).resolve().parents[1]


# --- login: sin oráculo de timing entre usuario existente e inexistente -------------
@pytest.mark.integration
def test_login_unknown_email_still_runs_a_bcrypt_check(client, monkeypatch):
    """Si el usuario no existe igual se hace un bcrypt (misma latencia que una clave mala)."""
    from app.routers import auth

    calls = []
    real = auth.verify_password

    def spy(password, password_hash):
        calls.append(password_hash)
        return real(password, password_hash)

    monkeypatch.setattr(auth, "verify_password", spy)
    resp = client.post(
        "/auth/login", json={"email": "nadie@example.com", "password": "incorrecta"}
    )
    assert resp.status_code == 401
    assert len(calls) == 1 and calls[0].startswith("$2")


@pytest.mark.integration
def test_login_unknown_and_wrong_password_answer_the_same(client):
    unknown = client.post(
        "/auth/login", json={"email": "nadie@example.com", "password": "incorrecta"}
    )
    wrong = client.post("/auth/login", json={"email": DEMO_EMAIL, "password": "incorrecta"})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


# --- tamaños de entrada -------------------------------------------------------------
def test_login_password_has_a_length_cap(client):
    resp = client.post(
        "/auth/login", json={"email": "a@example.com", "password": "x" * 129}
    )
    assert resp.status_code == 422


def test_register_rejects_passwords_bcrypt_would_silently_truncate(client):
    # 40 caracteres pero 80 bytes en UTF-8: bcrypt solo mira los primeros 72.
    resp = client.post(
        "/auth/register",
        json={"business_name": "Tienda", "email": "trunc@example.com", "password": "ñ" * 40},
    )
    assert resp.status_code == 422


def test_telegram_confirm_fields_have_length_caps(client):
    headers = {"X-N8N-SECRET": TEST_N8N_SECRET}
    long_code = client.post(
        "/connections/telegram/confirm",
        json={"code": "1" * 100, "chat_id": "111"},
        headers=headers,
    )
    long_chat = client.post(
        "/connections/telegram/confirm",
        json={"code": "123456", "chat_id": "9" * 200},
        headers=headers,
    )
    assert long_code.status_code == 422
    assert long_chat.status_code == 422


def test_telegram_confirm_non_ascii_secret_is_401_not_500(client):
    # compare_digest sobre str explota (TypeError) con caracteres no ASCII.
    resp = client.post(
        "/connections/telegram/confirm",
        json={"code": "123456", "chat_id": "111"},
        headers={"X-N8N-SECRET": "secreto-é".encode("latin-1")},
    )
    assert resp.status_code == 401


# --- JWT ----------------------------------------------------------------------------
def _forge(payload):
    from app.core.config import settings

    return jwt.encode(payload, settings.dashboard_jwt_secret, algorithm="HS256")


@pytest.mark.parametrize("missing", ["exp", "sub", "type"])
def test_token_signed_with_the_right_secret_but_missing_claims_is_rejected(missing):
    from app.core.security import InvalidTokenError, decode_access_token

    payload = {
        "sub": "1",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    payload.pop(missing)
    with pytest.raises(InvalidTokenError):
        decode_access_token(_forge(payload))


def test_expired_token_is_rejected():
    from app.core.security import InvalidTokenError, decode_access_token

    payload = {
        "sub": "1",
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=5),
    }
    with pytest.raises(InvalidTokenError):
        decode_access_token(_forge(payload))


def test_alg_none_token_is_rejected():
    from app.core.security import InvalidTokenError, decode_access_token

    unsigned = jwt.encode(
        {"sub": "1", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        key=None,
        algorithm="none",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(unsigned)


def test_token_with_another_hmac_algorithm_is_rejected():
    from app.core.config import settings
    from app.core.security import InvalidTokenError, decode_access_token

    other = jwt.encode(
        {"sub": "1", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.dashboard_jwt_secret,
        algorithm="HS512",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(other)


def test_used_refresh_store_forgets_expired_entries_and_detects_reuse():
    from app.routers import auth

    auth._used_refresh_jtis.clear()
    now = time.time()
    assert auth._consume_refresh_jti("vieja", now - 5) is True
    assert auth._consume_refresh_jti("nueva", now + 100) is True
    assert "vieja" not in auth._used_refresh_jtis  # no crece sin límite
    assert auth._consume_refresh_jti("nueva", now + 100) is False  # reutilización
    auth._used_refresh_jtis.clear()


def test_rate_limit_does_not_keep_empty_buckets():
    from app.core import rate_limit

    rate_limit.reset()
    assert rate_limit.is_blocked("ip:1.2.3.4", "email:a@example.com") is False
    assert rate_limit._failures == {}


# --- documentación de la API ---------------------------------------------------------
@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_api_docs_are_not_exposed_by_default(client, path):
    assert client.get(path).status_code == 404


def test_api_docs_can_be_enabled_explicitly(monkeypatch):
    from app.core.config import settings
    from app.main import create_app

    monkeypatch.setattr(settings, "dashboard_enable_docs", True)
    with TestClient(create_app()) as docs_client:
        assert docs_client.get("/docs").status_code == 200
        assert docs_client.get("/openapi.json").status_code == 200


# --- CORS -----------------------------------------------------------------------------
def test_cors_never_answers_with_wildcards(client):
    resp = client.options(
        "/health",
        headers={"Origin": "http://localhost:8080", "Access-Control-Request-Method": "GET"},
    )
    assert resp.headers["access-control-allow-origin"] == "http://localhost:8080"
    for header, value in resp.headers.items():
        if header.lower().startswith("access-control-allow-"):
            assert "*" not in value, header


@pytest.mark.parametrize(
    "origin", ["null", "http://localhost:8080.evil.com", "https://localhost:8080"]
)
def test_cors_rejects_lookalike_origins(client, origin):
    resp = client.options(
        "/health", headers={"Origin": origin, "Access-Control-Request-Method": "GET"}
    )
    assert resp.headers.get("access-control-allow-origin") is None


def test_cors_preflight_only_allows_declared_methods_and_headers(client):
    base = {"Origin": "http://localhost:5173"}
    put = client.options("/health", headers={**base, "Access-Control-Request-Method": "PUT"})
    assert put.status_code == 400
    odd = client.options(
        "/health",
        headers={
            **base,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Evil-Header",
        },
    )
    assert odd.status_code == 400
    ok = client.options(
        "/health",
        headers={
            **base,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert ok.status_code == 200


# --- contenedor -------------------------------------------------------------------------
def test_dockerfile_runs_the_api_as_a_non_root_user():
    lines = [
        line.strip()
        for line in (API_DIR / "Dockerfile").read_text(encoding="utf-8").splitlines()
    ]
    user_at = [i for i, line in enumerate(lines) if line.upper().startswith("USER ")]
    assert user_at, "el Dockerfile no define USER (corre como root)"
    assert lines[user_at[-1]].split()[1].lower() not in {"root", "0"}
    # USER va antes del CMD para que el proceso lo herede
    assert user_at[-1] < max(i for i, line in enumerate(lines) if line.upper().startswith("CMD "))
