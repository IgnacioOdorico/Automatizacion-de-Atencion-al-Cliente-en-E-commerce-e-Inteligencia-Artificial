import json

import httpx
import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.integration

from app.core import google_oauth


def _mock_google_client(mode="ok"):
    def handler(request):
        if request.url.path.endswith("/token"):
            if mode == "http_error":
                return httpx.Response(500, json={"error": "server_error"})
            if mode == "no_refresh":
                return httpx.Response(200, json={"access_token": "at", "expires_in": 3599})
            return httpx.Response(
                200,
                json={"access_token": "at-123", "refresh_token": "1//fake-refresh-token"},
            )
        if request.url.path.endswith("/userinfo"):
            return httpx.Response(200, json={"email": "demo@tecnoshopmza.com.ar"})
        return httpx.Response(404, json={"error": "not_found"})

    return httpx.Client(transport=httpx.MockTransport(handler), timeout=10.0)


def _no_redirect_client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app, follow_redirects=False)


def _email_row():
    from app.db import fetch_one

    return fetch_one(
        "SELECT status, external_reference, encrypted_credentials FROM channel_connections "
        "WHERE client_account_id = 1 AND channel = 'email'"
    )


# ---------- Consulta de URL de consentimiento (JWT) ----------


def test_oauth_url_requires_jwt(client):
    assert client.get("/connections/gmail/oauth-url").status_code == 401


def test_oauth_url_shape_and_signed_state(client, auth_headers):
    resp = client.get("/connections/gmail/oauth-url", headers=auth_headers)
    assert resp.status_code == 200
    url = resp.json()["url"]
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "client_id=test-client-id.apps.googleusercontent.com" in url
    assert "redirect_uri=" in url
    assert "response_type=code" in url
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    state = resp.json()["state"]
    data = google_oauth.verify_state(state)
    assert data["account_id"] == 1
    assert data["channel"] == "email"


def test_oauth_url_503_without_google_config(monkeypatch, client, auth_headers):
    from app.core.config import settings

    monkeypatch.setattr(settings, "dashboard_google_client_id", "")
    resp = client.get("/connections/gmail/oauth-url", headers=auth_headers)
    assert resp.status_code == 503


# ---------- Helpers puros ----------


def test_state_roundtrip():
    state = google_oauth.sign_state(7, "email")
    data = google_oauth.verify_state(state)
    assert data["account_id"] == 7
    assert data["channel"] == "email"


def test_verify_state_rejects_forged_state():
    with pytest.raises(HTTPException) as exc:
        google_oauth.verify_state("no-firmado")
    assert exc.value.status_code == 400


# ---------- Callback (sin JWT, redirect del browser) ----------


def test_callback_success_connects_and_encrypts(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client())
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()

    resp = c.get(f"/connections/gmail/callback?state={state}&code=auth-code-123")
    assert resp.status_code == 307
    assert resp.headers["location"].startswith("http://localhost:5173/connections")

    row = _email_row()
    assert row["status"] == "connected"
    assert row["external_reference"] == "demo@tecnoshopmza.com.ar"

    from app.core.security import decrypt_credentials

    stored = json.loads(decrypt_credentials(row["encrypted_credentials"]))
    assert stored == {"refresh_token": "1//fake-refresh-token"}
    assert row["encrypted_credentials"] != "1//fake-refresh-token"


def test_callback_bad_state_400_no_persist():
    c = _no_redirect_client()
    resp = c.get("/connections/gmail/callback?state=basura&code=abc")
    assert resp.status_code == 400
    assert _email_row()["status"] == "disconnected"


def test_callback_state_wrong_channel_400_no_persist(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client())
    state = google_oauth.sign_state(1, "whatsapp")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    assert resp.status_code == 400
    assert _email_row()["status"] == "disconnected"


def test_callback_google_error_400_no_persist(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client())
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&error=access_denied")
    assert resp.status_code == 400
    assert _email_row()["status"] == "disconnected"


def test_callback_token_upstream_error_502_no_persist(monkeypatch, db_ready):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client("http_error"))
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    assert resp.status_code == 502
    assert _email_row()["status"] == "disconnected"


def test_callback_missing_refresh_token_400_no_persist(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client("no_refresh"))
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    assert resp.status_code == 400
    assert _email_row()["status"] == "disconnected"