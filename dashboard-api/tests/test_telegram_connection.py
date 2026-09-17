from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.integration

N8N_SECRET = "test-n8n-secret"


def test_start_returns_code_and_expiry(client, auth_headers):
    resp = client.post("/connections/telegram/start", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["code"]) == 6 and body["code"].isdigit()
    assert body["expires_in"] == 900
    assert body["expires_at"].endswith("Z")


def test_second_start_rotates_and_invalidates_previous(client, auth_headers):
    first = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]
    second = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]
    assert first != second

    stale = client.post(
        "/connections/telegram/confirm",
        json={"code": first, "chat_id": "458721336"},
        headers={"X-N8N-SECRET": N8N_SECRET},
    )
    assert stale.status_code == 400


def test_confirm_requires_secret_header(client):
    resp = client.post(
        "/connections/telegram/confirm", json={"code": "123456", "chat_id": "111"}
    )
    assert resp.status_code == 401


def test_confirm_rejects_bad_secret(client):
    resp = client.post(
        "/connections/telegram/confirm",
        json={"code": "123456", "chat_id": "111"},
        headers={"X-N8N-SECRET": "secreto-malo"},
    )
    assert resp.status_code == 401


def test_confirm_full_flow_connects_channel(client, auth_headers):
    code = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]
    resp = client.post(
        "/connections/telegram/confirm",
        json={"code": code, "chat_id": "458721336"},
        headers={"X-N8N-SECRET": N8N_SECRET},
    )
    assert resp.status_code == 200
    assert resp.json()["channel"] == "telegram"
    assert resp.json()["status"] == "connected"
    assert resp.json()["external_reference"] == "458721336"

    from app.db import fetch_one

    row = fetch_one(
        "SELECT status, external_reference FROM channel_connections "
        "WHERE client_account_id = 1 AND channel = 'telegram'"
    )
    assert row["status"] == "connected"
    assert row["external_reference"] == "458721336"


def test_confirm_unknown_code_400(client):
    resp = client.post(
        "/connections/telegram/confirm",
        json={"code": "000000", "chat_id": "458721336"},
        headers={"X-N8N-SECRET": N8N_SECRET},
    )
    assert resp.status_code == 400


def test_confirm_expired_code_400(client, auth_headers):
    from app.core import telegram_codes

    code = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]
    telegram_codes._records[code]["expires_at"] = datetime.now(timezone.utc) - timedelta(
        seconds=1
    )
    resp = client.post(
        "/connections/telegram/confirm",
        json={"code": code, "chat_id": "458721336"},
        headers={"X-N8N-SECRET": N8N_SECRET},
    )
    assert resp.status_code == 400


def test_confirm_is_single_use(client, auth_headers):
    code = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]
    first = client.post(
        "/connections/telegram/confirm",
        json={"code": code, "chat_id": "458721336"},
        headers={"X-N8N-SECRET": N8N_SECRET},
    )
    assert first.status_code == 200
    again = client.post(
        "/connections/telegram/confirm",
        json={"code": code, "chat_id": "458721336"},
        headers={"X-N8N-SECRET": N8N_SECRET},
    )
    assert again.status_code == 400