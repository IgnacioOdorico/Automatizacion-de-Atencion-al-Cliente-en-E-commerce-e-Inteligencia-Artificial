import pytest

pytestmark = pytest.mark.integration

APPROVAL_MESSAGE = "Meta aprueba en 1-3 días hábiles"


def test_request_approval_requires_jwt(client):
    resp = client.post("/connections/whatsapp/request-approval", json={"phone": "+5492615550102"})
    assert resp.status_code == 401


def test_request_approval_invalid_phone_422(client, auth_headers):
    for phone in ["abc", "123", "+55-11-9999", ""]:
        resp = client.post(
            "/connections/whatsapp/request-approval",
            json={"phone": phone},
            headers=auth_headers,
        )
        assert resp.status_code == 422, phone


def test_request_approval_sets_pending_when_disconnected(client, auth_headers):
    assert client.delete("/connections/whatsapp", headers=auth_headers).status_code == 200

    resp = client.post(
        "/connections/whatsapp/request-approval",
        json={"phone": "+5492615550102"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert APPROVAL_MESSAGE in resp.json()["message"]

    from app.db import fetch_one

    row = fetch_one(
        "SELECT status, external_reference FROM channel_connections "
        "WHERE client_account_id = 1 AND channel = 'whatsapp'"
    )
    assert row["status"] == "pending"
    assert row["external_reference"] == "+5492615550102"


def test_request_approval_keeps_seed_connected(client, auth_headers):
    resp = client.post(
        "/connections/whatsapp/request-approval",
        json={"phone": "+5492615550102"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    from app.db import fetch_one

    row = fetch_one(
        "SELECT status, external_reference FROM channel_connections "
        "WHERE client_account_id = 1 AND channel = 'whatsapp'"
    )
    assert row["status"] == "connected"
    assert row["external_reference"] == "5492615550102"