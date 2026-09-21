"""Aislamiento entre cuentas (checklist 9.8) y credenciales cifradas en reposo (9.3).

Lo que ES por cuenta (perfil, conexiones, códigos de Telegram, estado de Gmail,
solicitud de WhatsApp) nunca cruza cuentas. `orders`, `tickets` y `products` son globales
POR DISEÑO (un comercio por instalación; ver SPEC §10): también se documenta con un test.
"""

import json

import httpx
import pytest

from app.core import google_oauth
from tests.conftest import DEMO_EMAIL, DEMO_PASSWORD, TEST_N8N_SECRET

pytestmark = pytest.mark.integration

REFRESH_TOKEN = "1//refresh-token-que-no-debe-quedar-en-claro"
OTHER_EMAIL = "panaderia@sol.com"
OTHER_PASSWORD = "Fuerte2026!"


def _headers_for(client, email, password):
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def headers_a(client, auth_headers):
    return auth_headers  # cuenta demo (id 1), con conexiones sembradas por la fixture


@pytest.fixture
def headers_b(client, headers_a):
    client.post(
        "/auth/register",
        json={
            "business_name": "Panadería Sol",
            "email": OTHER_EMAIL,
            "password": OTHER_PASSWORD,
        },
    )
    return _headers_for(client, OTHER_EMAIL, OTHER_PASSWORD)


def _google_ok():
    def handler(request):
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200, json={"access_token": "at-123", "refresh_token": REFRESH_TOKEN}
            )
        return httpx.Response(200, json={"email": "duenio@tecnoshopmza.com.ar"})

    return httpx.Client(transport=httpx.MockTransport(handler), timeout=10.0)


def _row(account_id, channel):
    from app.db import fetch_one

    return fetch_one(
        "SELECT status, external_reference, encrypted_credentials FROM channel_connections "
        "WHERE client_account_id = :id AND channel = :channel",
        {"id": account_id, "channel": channel},
    )


def _account_id(client, headers):
    return client.get("/me", headers=headers).json()["id"]


# ---------- perfil y conexiones ----------


def test_me_and_connections_only_list_the_callers_rows(client, headers_a, headers_b):
    me_a = client.get("/me", headers=headers_a).json()
    me_b = client.get("/me", headers=headers_b).json()
    assert me_a["email"] == DEMO_EMAIL and me_b["email"] == OTHER_EMAIL
    assert me_a["id"] != me_b["id"]

    ids_a = {c["id"] for c in me_a["connections"]}
    ids_b = {c["id"] for c in me_b["connections"]}
    assert ids_a and ids_b and not (ids_a & ids_b)

    list_a = client.get("/connections", headers=headers_a).json()["items"]
    list_b = client.get("/connections", headers=headers_b).json()["items"]
    assert {c["id"] for c in list_a} == ids_a
    assert {c["id"] for c in list_b} == ids_b
    # la cuenta B no ve NADA de lo conectado por A (chat de Telegram, número de WhatsApp)
    assert all(c["status"] == "disconnected" for c in list_b)
    assert all(c["external_reference"] is None for c in list_b)
    assert "458721336" not in json.dumps(list_b) and "5492615550102" not in json.dumps(list_b)


def test_account_id_in_the_query_string_is_ignored(client, headers_a, headers_b):
    b_id = _account_id(client, headers_b)
    me = client.get(f"/me?id={b_id}&client_account_id={b_id}", headers=headers_a).json()
    assert me["email"] == DEMO_EMAIL
    items = client.get(
        f"/connections?client_account_id={b_id}", headers=headers_a
    ).json()["items"]
    assert any(c["external_reference"] == "458721336" for c in items)  # las de A, no las de B


def test_token_of_a_missing_account_cannot_read_a_profile(client):
    from app.core.security import create_access_token

    ghost = {"Authorization": f"Bearer {create_access_token(999999)}"}
    assert client.get("/me", headers=ghost).status_code == 401


def test_connection_writes_by_one_account_never_touch_the_other(
    client, headers_a, headers_b
):
    a_id = _account_id(client, headers_a)
    b_id = _account_id(client, headers_b)

    # B pide WhatsApp -> queda pending; A sigue conectado con SU número
    pending = client.post(
        "/connections/whatsapp/request-approval",
        json={"phone": "+5492615551111"},
        headers=headers_b,
    )
    assert pending.json()["status"] == "pending"
    assert _row(a_id, "whatsapp")["status"] == "connected"
    assert _row(a_id, "whatsapp")["external_reference"] == "5492615550102"

    # A desconecta WhatsApp -> la solicitud pendiente de B sigue intacta
    assert client.delete("/connections/whatsapp", headers=headers_a).status_code == 200
    assert _row(a_id, "whatsapp")["status"] == "disconnected"
    assert _row(b_id, "whatsapp")["status"] == "pending"
    assert _row(b_id, "whatsapp")["external_reference"] == "+5492615551111"


def test_telegram_code_links_only_the_account_that_asked_for_it(
    client, headers_a, headers_b
):
    a_id = _account_id(client, headers_a)
    b_id = _account_id(client, headers_b)
    code_b = client.post("/connections/telegram/start", headers=headers_b).json()["code"]

    resp = client.post(
        "/connections/telegram/confirm",
        json={"code": code_b, "chat_id": "777000111"},
        headers={"X-N8N-SECRET": TEST_N8N_SECRET},
    )
    assert resp.status_code == 200
    assert _row(b_id, "telegram")["external_reference"] == "777000111"
    assert _row(a_id, "telegram")["external_reference"] == "458721336"  # A no cambió


def test_a_pending_code_of_one_account_is_not_valid_for_the_other_after_disconnect(
    client, headers_a, headers_b
):
    a_id = _account_id(client, headers_a)
    code_a = client.post("/connections/telegram/start", headers=headers_a).json()["code"]
    # B desconecta SU telegram: el código de A tiene que seguir vivo (y solo vincula a A)
    assert client.delete("/connections/telegram", headers=headers_b).status_code == 200

    resp = client.post(
        "/connections/telegram/confirm",
        json={"code": code_a, "chat_id": "123123123"},
        headers={"X-N8N-SECRET": TEST_N8N_SECRET},
    )
    assert resp.status_code == 200
    assert _row(a_id, "telegram")["external_reference"] == "123123123"


def test_gmail_state_of_one_account_only_connects_that_account(
    client, monkeypatch, headers_a, headers_b
):
    from fastapi.testclient import TestClient

    from app.main import app

    a_id = _account_id(client, headers_a)
    b_id = _account_id(client, headers_b)
    monkeypatch.setattr(google_oauth, "create_client", _google_ok)
    state_b = google_oauth.sign_state(b_id, "email")

    resp = TestClient(app, follow_redirects=False).get(
        f"/connections/gmail/callback?state={state_b}&code=auth-code"
    )
    assert resp.status_code == 307
    assert _row(b_id, "email")["status"] == "connected"
    assert _row(a_id, "email")["status"] == "disconnected"
    assert _row(a_id, "email")["encrypted_credentials"] is None


def test_api_never_returns_credentials_to_any_account(client, monkeypatch, headers_a):
    from fastapi.testclient import TestClient

    from app.main import app

    a_id = _account_id(client, headers_a)
    monkeypatch.setattr(google_oauth, "create_client", _google_ok)
    TestClient(app, follow_redirects=False).get(
        f"/connections/gmail/callback?state={google_oauth.sign_state(a_id, 'email')}&code=x"
    )
    ciphertext = _row(a_id, "email")["encrypted_credentials"]
    assert ciphertext

    for path in ("/me", "/connections"):
        body = client.get(path, headers=headers_a).text
        assert "encrypted_credentials" not in body
        assert ciphertext not in body and REFRESH_TOKEN not in body


# ---------- 9.3: credenciales cifradas en reposo ----------


def test_persisted_credentials_are_fernet_ciphertext_never_the_token(
    client, monkeypatch, headers_a
):
    from fastapi.testclient import TestClient

    from app.core.security import decrypt_credentials
    from app.db import fetch_one
    from app.main import app

    a_id = _account_id(client, headers_a)
    monkeypatch.setattr(google_oauth, "create_client", _google_ok)
    TestClient(app, follow_redirects=False).get(
        f"/connections/gmail/callback?state={google_oauth.sign_state(a_id, 'email')}&code=x"
    )

    # Lo que hay en la BD, fila entera (como haría un SELECT * de quien accede a la BD)
    stored = fetch_one(
        "SELECT cc::text AS whole, encrypted_credentials AS cipher "
        "FROM channel_connections cc WHERE client_account_id = :id AND channel = 'email'",
        {"id": a_id},
    )
    assert REFRESH_TOKEN not in stored["whole"]
    assert stored["cipher"].startswith("gAAAA")  # formato de token Fernet
    assert json.loads(decrypt_credentials(stored["cipher"])) == {"refresh_token": REFRESH_TOKEN}


def test_encrypting_the_same_secret_twice_gives_different_ciphertexts():
    from app.core.security import decrypt_credentials, encrypt_credentials

    first = encrypt_credentials("mismo-secreto")
    second = encrypt_credentials("mismo-secreto")
    assert first != second  # IV aleatorio: no se pueden comparar cifrados entre filas
    assert decrypt_credentials(first) == decrypt_credentials(second) == "mismo-secreto"


def test_tampered_ciphertext_is_rejected():
    from cryptography.fernet import InvalidToken

    from app.core.security import decrypt_credentials, encrypt_credentials

    token = encrypt_credentials("secreto")
    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    with pytest.raises(InvalidToken):
        decrypt_credentials(tampered)


# ---------- lo global por diseño ----------


def test_orders_tickets_and_products_are_shared_by_design(client, headers_a, headers_b):
    """Limitación conocida (SPEC §10): esas tablas no tienen client_account_id.

    Son las tablas del e-commerce único que atienden los Flujos 1 y 2 (no modificables).
    Cada instalación atiende UN comercio, así que todas las cuentas ven lo mismo.
    """
    for path in ("/orders", "/tickets", "/products", "/dashboard/summary"):
        seen_a = client.get(path, headers=headers_a)
        seen_b = client.get(path, headers=headers_b)
        assert seen_a.status_code == seen_b.status_code == 200, path
        assert seen_a.json() == seen_b.json(), path
    # y el detalle de un recurso inexistente responde 404 igual para ambas
    for headers in (headers_a, headers_b):
        assert client.get("/orders/999999", headers=headers).status_code == 404
        assert client.get("/tickets/999999", headers=headers).status_code == 404


def test_login_of_one_account_never_accepts_the_other_accounts_password(
    client, headers_a, headers_b
):
    resp = client.post("/auth/login", json={"email": OTHER_EMAIL, "password": DEMO_PASSWORD})
    assert resp.status_code == 401
