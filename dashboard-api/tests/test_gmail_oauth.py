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
            if mode == "token_400":
                return httpx.Response(400, json={"error": "invalid_grant"})
            if mode == "connect_error":
                raise httpx.ConnectError("no hay ruta a Google", request=request)
            if mode == "no_refresh":
                return httpx.Response(200, json={"access_token": "at", "expires_in": 3599})
            if mode == "no_access_token":
                return httpx.Response(200, json={"refresh_token": "1//x"})
            return httpx.Response(
                200,
                json={"access_token": "at-123", "refresh_token": "1//fake-refresh-token"},
            )
        if request.url.path.endswith("/userinfo"):
            if mode == "userinfo_500":
                return httpx.Response(500, json={"error": "server_error"})
            if mode == "no_email":
                return httpx.Response(200, json={"id": "1234"})
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
# El callback NUNCA responde JSON al navegador: éxito y fallo terminan en un
# redirect al front (/conexiones) con un código corto y estable en `reason`.

FRONTEND = "http://localhost:5173"
OK_LOCATION = f"{FRONTEND}/conexiones?gmail=connected"


def _error_location(reason):
    return f"{FRONTEND}/conexiones?gmail=error&reason={reason}"


def _assert_error_redirect(resp, reason):
    assert resp.status_code == 307
    assert resp.headers["location"] == _error_location(reason)
    assert _email_row()["status"] == "disconnected"


def test_callback_success_connects_and_encrypts(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client())
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()

    resp = c.get(f"/connections/gmail/callback?state={state}&code=auth-code-123")
    assert resp.status_code == 307
    assert resp.headers["location"] == OK_LOCATION

    row = _email_row()
    assert row["status"] == "connected"
    assert row["external_reference"] == "demo@tecnoshopmza.com.ar"

    from app.core.security import decrypt_credentials

    stored = json.loads(decrypt_credentials(row["encrypted_credentials"]))
    assert stored == {"refresh_token": "1//fake-refresh-token"}
    assert row["encrypted_credentials"] != "1//fake-refresh-token"


def test_callback_bad_state_redirects_invalid_state_no_persist():
    c = _no_redirect_client()
    resp = c.get("/connections/gmail/callback?state=basura&code=abc")
    _assert_error_redirect(resp, "invalid_state")


def test_callback_missing_state_redirects_invalid_state_no_persist():
    c = _no_redirect_client()
    resp = c.get("/connections/gmail/callback?code=abc")
    _assert_error_redirect(resp, "invalid_state")


def test_callback_state_wrong_channel_redirects_invalid_state_no_persist(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client())
    state = google_oauth.sign_state(1, "whatsapp")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    _assert_error_redirect(resp, "invalid_state")


def test_callback_expired_state_redirects_invalid_state_no_persist(monkeypatch):
    from datetime import datetime, timedelta, timezone

    import jwt

    from app.core.config import settings
    from app.core.security import ALGORITHM

    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client())
    past = datetime.now(timezone.utc) - timedelta(minutes=30)
    state = jwt.encode(
        {
            "sub": "1",
            "type": "google_oauth_state",
            "channel": "email",
            "iat": past,
            "exp": past + timedelta(minutes=10),
        },
        settings.dashboard_jwt_secret,
        algorithm=ALGORITHM,
    )
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    _assert_error_redirect(resp, "invalid_state")


def test_callback_user_cancels_redirects_denied_no_persist(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client())
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&error=access_denied")
    _assert_error_redirect(resp, "denied")


def test_callback_other_google_error_redirects_google_error_no_persist():
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&error=invalid_scope")
    _assert_error_redirect(resp, "google_error")


def test_callback_google_error_with_bad_state_prefers_invalid_state():
    # El state se valida primero: sin state firmado no se atiende nada más.
    c = _no_redirect_client()
    resp = c.get("/connections/gmail/callback?state=basura&error=access_denied")
    _assert_error_redirect(resp, "invalid_state")


def test_callback_missing_code_redirects_missing_code_no_persist():
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}")
    _assert_error_redirect(resp, "missing_code")


def test_callback_token_rejected_redirects_exchange_failed_no_persist(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client("token_400"))
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    _assert_error_redirect(resp, "exchange_failed")


def test_callback_token_without_access_token_redirects_exchange_failed(monkeypatch):
    monkeypatch.setattr(
        google_oauth, "create_client", lambda: _mock_google_client("no_access_token")
    )
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    _assert_error_redirect(resp, "exchange_failed")


def test_callback_token_upstream_error_redirects_upstream_no_persist(monkeypatch, db_ready):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client("http_error"))
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    _assert_error_redirect(resp, "upstream")


def test_callback_network_error_redirects_upstream_no_persist(monkeypatch):
    monkeypatch.setattr(
        google_oauth, "create_client", lambda: _mock_google_client("connect_error")
    )
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    _assert_error_redirect(resp, "upstream")


def test_callback_userinfo_upstream_error_redirects_upstream_no_persist(monkeypatch):
    monkeypatch.setattr(
        google_oauth, "create_client", lambda: _mock_google_client("userinfo_500")
    )
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    _assert_error_redirect(resp, "upstream")


def test_callback_userinfo_without_email_redirects_no_email_no_persist(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client("no_email"))
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    _assert_error_redirect(resp, "no_email")


def test_callback_missing_refresh_token_redirects_no_refresh_no_persist(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client("no_refresh"))
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    _assert_error_redirect(resp, "no_refresh")


def test_callback_persistence_failure_redirects_internal(monkeypatch):
    from app.routers import connections

    def boom(*args, **kwargs):
        raise RuntimeError("password=super-secreto host=db.interno")

    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client())
    monkeypatch.setattr(connections, "_set_connection", boom)
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=abc")
    assert resp.status_code == 307
    assert resp.headers["location"] == _error_location("internal")
    assert "secreto" not in resp.headers["location"]
    assert _email_row()["status"] == "disconnected"


def test_callback_error_redirect_never_leaks_internals(monkeypatch):
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client("http_error"))
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(f"/connections/gmail/callback?state={state}&code=el-code-secreto")
    location = resp.headers["location"]
    for forbidden in ("el-code-secreto", "at-123", "1//", state, "server_error", "500"):
        assert forbidden not in location


def test_callback_does_not_reflect_google_error_params():
    state = google_oauth.sign_state(1, "email")
    c = _no_redirect_client()
    resp = c.get(
        f"/connections/gmail/callback?state={state}&error=%3Cscript%3E"
        "&error_description=https%3A%2F%2Fevil.example.com"
    )
    location = resp.headers["location"]
    assert location == _error_location("google_error")
    assert "script" not in location and "evil" not in location


def test_callback_redirects_only_to_configured_frontend(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "dashboard_frontend_url", "https://portal.tienda.com.ar/")
    monkeypatch.setattr(google_oauth, "create_client", lambda: _mock_google_client())
    c = _no_redirect_client()

    ok = c.get(
        f"/connections/gmail/callback?state={google_oauth.sign_state(1, 'email')}&code=abc",
        headers={"Host": "evil.example.com", "Referer": "https://evil.example.com/"},
    )
    assert ok.headers["location"] == "https://portal.tienda.com.ar/conexiones?gmail=connected"

    failed = c.get(
        "/connections/gmail/callback?state=basura&code=abc",
        headers={"Host": "evil.example.com", "Origin": "https://evil.example.com"},
    )
    assert (
        failed.headers["location"]
        == "https://portal.tienda.com.ar/conexiones?gmail=error&reason=invalid_state"
    )
