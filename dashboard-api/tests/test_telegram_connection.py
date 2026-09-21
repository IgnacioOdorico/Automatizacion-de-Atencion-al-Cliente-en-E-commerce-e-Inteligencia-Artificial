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

# ---------- Cancelar el código pendiente (DELETE /connections/telegram/code) ----------


def _second_account_headers(client):
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
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _confirm(client, code, chat_id="458721336"):
    return client.post(
        "/connections/telegram/confirm",
        json={"code": code, "chat_id": chat_id},
        headers={"X-N8N-SECRET": N8N_SECRET},
    )


def test_cancel_code_requires_jwt(client):
    assert client.delete("/connections/telegram/code").status_code == 401


def test_cancel_code_invalidates_the_pending_code(client, auth_headers):
    code = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]

    resp = client.delete("/connections/telegram/code", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"cancelled": True}

    assert _confirm(client, code).status_code == 400


def test_cancel_code_is_idempotent_without_pending_code(client, auth_headers):
    first = client.delete("/connections/telegram/code", headers=auth_headers)
    again = client.delete("/connections/telegram/code", headers=auth_headers)
    assert first.status_code == 200 and first.json() == {"cancelled": False}
    assert again.status_code == 200 and again.json() == {"cancelled": False}


def test_cancel_code_twice_after_start_is_idempotent(client, auth_headers):
    client.post("/connections/telegram/start", headers=auth_headers)
    assert client.delete("/connections/telegram/code", headers=auth_headers).json() == {
        "cancelled": True
    }
    assert client.delete("/connections/telegram/code", headers=auth_headers).json() == {
        "cancelled": False
    }


def test_can_start_a_new_code_after_cancelling(client, auth_headers):
    client.post("/connections/telegram/start", headers=auth_headers)
    client.delete("/connections/telegram/code", headers=auth_headers)

    code = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]
    assert _confirm(client, code).status_code == 200


def test_cancel_code_never_touches_another_accounts_code(client, auth_headers):
    other_headers = _second_account_headers(client)
    other_code = client.post("/connections/telegram/start", headers=other_headers).json()[
        "code"
    ]
    my_code = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]

    resp = client.delete("/connections/telegram/code", headers=auth_headers)
    assert resp.json() == {"cancelled": True}

    assert _confirm(client, my_code).status_code == 400
    # El código de la otra cuenta sigue vivo y vincula a SU cuenta.
    assert _confirm(client, other_code, chat_id="999000111").status_code == 200

    from app.db import fetch_one

    row = fetch_one(
        "SELECT client_account_id, status, external_reference FROM channel_connections "
        "WHERE channel = 'telegram' AND client_account_id <> 1"
    )
    assert row["status"] == "connected"
    assert row["external_reference"] == "999000111"


def test_cancel_code_does_not_disconnect_the_channel(client, auth_headers):
    # /telegram/code no debe colisionar con DELETE /connections/{channel}:
    # cancelar el código no toca el canal (la fixture lo deja conectado).
    client.post("/connections/telegram/start", headers=auth_headers)
    assert client.delete("/connections/telegram/code", headers=auth_headers).status_code == 200

    from app.db import fetch_one

    row = fetch_one(
        "SELECT status, external_reference FROM channel_connections "
        "WHERE client_account_id = 1 AND channel = 'telegram'"
    )
    assert row["status"] == "connected"
    assert row["external_reference"] == "458721336"


def test_disconnect_channel_route_still_works_next_to_cancel_code(client, auth_headers):
    resp = client.delete("/connections/telegram", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"channel": "telegram", "status": "disconnected"}


def test_disconnect_invalidates_the_pending_code(client, auth_headers):
    # Un código vivo NO puede reconectar el canal después de desconectarlo.
    code = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]

    assert client.delete("/connections/telegram", headers=auth_headers).status_code == 200

    assert _confirm(client, code).status_code == 400
    from app.db import fetch_one

    row = fetch_one(
        "SELECT status, external_reference FROM channel_connections "
        "WHERE client_account_id = 1 AND channel = 'telegram'"
    )
    assert row["status"] == "disconnected"
    assert row["external_reference"] is None


def test_disconnecting_other_channels_keeps_the_pending_telegram_code(client, auth_headers):
    code = client.post("/connections/telegram/start", headers=auth_headers).json()["code"]

    assert client.delete("/connections/whatsapp", headers=auth_headers).status_code == 200

    assert _confirm(client, code).status_code == 200


def test_disconnect_never_invalidates_another_accounts_code(client, auth_headers):
    other_headers = _second_account_headers(client)
    other_code = client.post("/connections/telegram/start", headers=other_headers).json()[
        "code"
    ]

    assert client.delete("/connections/telegram", headers=auth_headers).status_code == 200

    assert _confirm(client, other_code, chat_id="999000111").status_code == 200
