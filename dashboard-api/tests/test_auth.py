import pytest

from tests.conftest import DEMO_EMAIL, DEMO_PASSWORD

pytestmark = pytest.mark.integration


def test_register_creates_bcrypt_account(client):
    resp = client.post(
        "/auth/register",
        json={
            "business_name": "Dietética Verde",
            "email": "hola@dieteticaverde.com",
            "password": "Fuerte2026!",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["business_name"] == "Dietética Verde"
    assert body["email"] == "hola@dieteticaverde.com"
    assert "password_hash" not in body
    assert body["created_at"]

    from app.db import fetch_one

    row = fetch_one(
        "SELECT password_hash FROM client_accounts WHERE email = :email",
        {"email": "hola@dieteticaverde.com"},
    )
    assert row is not None
    assert row["password_hash"].startswith("$2")
    assert row["password_hash"] != "Fuerte2026!"


def test_register_duplicate_email_conflict(client):
    resp = client.post(
        "/auth/register",
        json={
            "business_name": "Otra",
            "email": DEMO_EMAIL,
            "password": "Fuerte2026!",
        },
    )
    assert resp.status_code == 409


def test_login_ok_returns_tokens(client):
    from app.core.security import decode_access_token, decode_refresh_token

    resp = client.post(
        "/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 7200
    assert decode_access_token(body["access_token"])["sub"] == "1"
    assert decode_refresh_token(body["refresh_token"])["type"] == "refresh"
    assert "refresh_token" in resp.cookies


def test_login_wrong_password_401(client):
    resp = client.post(
        "/auth/login", json={"email": DEMO_EMAIL, "password": "incorrecta"}
    )
    assert resp.status_code == 401
    assert "access_token" not in resp.json()


def test_login_unknown_email_401(client):
    resp = client.post(
        "/auth/login", json={"email": "nadie@example.com", "password": "incorrecta"}
    )
    assert resp.status_code == 401


def test_login_rate_limit_blocks_sixth_attempt(client):
    for _ in range(5):
        resp = client.post(
            "/auth/login", json={"email": DEMO_EMAIL, "password": "incorrecta"}
        )
        assert resp.status_code == 401
    blocked = client.post(
        "/auth/login", json={"email": DEMO_EMAIL, "password": "incorrecta"}
    )
    assert blocked.status_code == 429


def test_refresh_rotates_and_invalidates_old_token(client):
    login = client.post(
        "/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
    ).json()
    first_refresh = login["refresh_token"]

    refreshed = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert refreshed.status_code == 200
    rotated = refreshed.json()
    assert rotated["refresh_token"] != first_refresh
    assert rotated["access_token"]

    reused = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert reused.status_code == 401


def test_refresh_rejects_garbage_token(client):
    resp = client.post("/auth/refresh", json={"refresh_token": "no-es-un-jwt"})
    assert resp.status_code == 401


def test_me_returns_account_and_connections(client, auth_headers):
    resp = client.get("/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["business_name"] == "TecnoShop Mendoza SRL"
    assert body["email"] == DEMO_EMAIL
    assert body["created_at"]
    channels = {c["channel"]: c["status"] for c in body["connections"]}
    assert channels == {
        "whatsapp": "connected",
        "telegram": "connected",
        "email": "disconnected",
    }
    assert all("encrypted_credentials" not in c for c in body["connections"])


def test_me_without_token_is_401(client):
    resp = client.get("/me")
    assert resp.status_code == 401