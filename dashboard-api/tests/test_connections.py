import pytest

pytestmark = pytest.mark.integration


def test_connections_requires_jwt(client):
    assert client.get("/connections").status_code == 401


def test_connections_returns_three_channels(client, auth_headers):
    resp = client.get("/connections", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 3
    by_channel = {c["channel"]: c for c in items}
    assert set(by_channel) == {"whatsapp", "telegram", "email"}
    assert by_channel["whatsapp"]["status"] == "connected"
    assert by_channel["whatsapp"]["external_reference"] == "5492615550102"
    assert by_channel["telegram"]["status"] == "connected"
    assert by_channel["telegram"]["external_reference"] == "458721336"
    assert by_channel["email"]["status"] == "disconnected"
    assert by_channel["email"]["label"] == "Gmail"
    assert all("encrypted_credentials" not in c for c in items)


def test_connections_new_account_gets_default_rows(client):
    client.post(
        "/auth/register",
        json={
            "business_name": "Panadería Sol",
            "email": "panaderia@sol.com",
            "password": "Fuerte2026!",
        },
    )
    login = client.post(
        "/auth/login", json={"email": "panaderia@sol.com", "password": "Fuerte2026!"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = client.get("/connections", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert [c["channel"] for c in items] == ["email", "telegram", "whatsapp"]
    assert all(c["status"] == "disconnected" for c in items)


def test_delete_connection_cleans_credentials(client, auth_headers):
    resp = client.delete("/connections/telegram", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"channel": "telegram", "status": "disconnected"}

    from app.db import fetch_one

    row = fetch_one(
        "SELECT status, external_reference, encrypted_credentials, connected_at "
        "FROM channel_connections WHERE client_account_id = 1 AND channel = 'telegram'"
    )
    assert row["status"] == "disconnected"
    assert row["external_reference"] is None
    assert row["encrypted_credentials"] is None
    assert row["connected_at"] is None


def test_delete_connection_requires_jwt(client):
    assert client.delete("/connections/telegram").status_code == 401


def test_delete_connection_invalid_channel(client, auth_headers):
    assert client.delete("/connections/sms", headers=auth_headers).status_code == 422