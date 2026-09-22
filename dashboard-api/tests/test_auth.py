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


def test_register_creates_three_disconnected_channel_rows(client):
    """Spec connections: al registrar, una fila `disconnected` por cada canal.

    Sin esto, /me de una cuenta recién creada devolvía `connections: []` hasta que
    alguien pedía /connections (que las creaba de forma perezosa).
    """
    email = "nueva@panaderialuna.com.ar"
    reg = client.post(
        "/auth/register",
        json={"business_name": "Panadería Luna", "email": email, "password": "Fuerte2026!"},
    )
    assert reg.status_code == 201

    from app.db import fetch_all

    rows = fetch_all(
        """
        SELECT cc.channel, cc.status, cc.external_reference, cc.encrypted_credentials
        FROM channel_connections cc
        JOIN client_accounts a ON a.id = cc.client_account_id
        WHERE a.email = :email
        ORDER BY cc.channel
        """,
        {"email": email},
    )
    assert [r["channel"] for r in rows] == ["email", "telegram", "whatsapp"]
    assert all(r["status"] == "disconnected" for r in rows)
    assert all(r["external_reference"] is None and r["encrypted_credentials"] is None for r in rows)

    login = client.post("/auth/login", json={"email": email, "password": "Fuerte2026!"})
    assert login.status_code == 200
    me = client.get(
        "/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"}
    )
    assert {c["channel"]: c["status"] for c in me.json()["connections"]} == {
        "email": "disconnected",
        "telegram": "disconnected",
        "whatsapp": "disconnected",
    }


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


def _bad_login(client, email, real_ip=None):
    headers = {"X-Real-IP": real_ip} if real_ip else {}
    return client.post(
        "/auth/login",
        json={"email": email, "password": "incorrecta"},
        headers=headers,
    )


def test_login_rate_limit_is_not_evaded_by_spoofing_x_real_ip(client):
    # Sin proxy de confianza configurado (default), el header lo controla el atacante:
    # rotarlo no puede darle un bucket nuevo por intento.
    for i in range(5):
        assert _bad_login(client, f"spray{i}@example.com", f"203.0.113.{i}").status_code == 401
    blocked = _bad_login(client, "spray9@example.com", "203.0.113.99")
    assert blocked.status_code == 429


def test_login_rate_limit_is_per_real_client_behind_the_trusted_proxy(
    client, monkeypatch
):
    from app.core import client_ip
    from app.core.config import settings

    # "testclient" es el peer que ve TestClient: hace de nginx.
    monkeypatch.setattr(settings, "dashboard_trusted_proxies", "testclient")
    client_ip.reset_cache()
    try:
        for i in range(5):
            assert _bad_login(client, f"a{i}@example.com", "203.0.113.10").status_code == 401
        # el cliente A quedó bloqueado...
        assert _bad_login(client, "a9@example.com", "203.0.113.10").status_code == 429
        # ...pero otro cliente detrás del mismo proxy NO comparte su bucket (no hay DoS)
        assert _bad_login(client, "b0@example.com", "203.0.113.20").status_code == 401
        good = client.post(
            "/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
            headers={"X-Real-IP": "203.0.113.20"},
        )
        assert good.status_code == 200
    finally:
        client_ip.reset_cache()


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
    assert body["business_name"] == "TechStore"
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