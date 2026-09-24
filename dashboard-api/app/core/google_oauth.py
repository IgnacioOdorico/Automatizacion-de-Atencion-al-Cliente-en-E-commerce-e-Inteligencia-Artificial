from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import ALGORITHM, InvalidTokenError

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPES = "openid email https://www.googleapis.com/auth/gmail.modify"
STATE_TTL_MINUTES = 10

CLIENT_ID_KEY = "client_id"
REDIRECT_URI_KEY = "redirect_uri"


def create_client() -> httpx.Client:
    return httpx.Client(timeout=10.0)


def sign_state(account_id: int, channel: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(account_id),
        "type": "google_oauth_state",
        "channel": channel,
        "iat": now,
        "exp": now + timedelta(minutes=STATE_TTL_MINUTES),
    }
    return jwt.encode(payload, settings.dashboard_jwt_secret, algorithm=ALGORITHM)


def verify_state(state: str) -> dict:
    try:
        payload = jwt.decode(state, settings.dashboard_jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=400, detail="state de OAuth inválido o vencido"
        ) from exc
    if payload.get("type") != "google_oauth_state" or payload.get("channel") != "email":
        raise HTTPException(status_code=400, detail="state de OAuth inválido")
    return {"account_id": int(payload["sub"]), "channel": payload["channel"]}


def build_consent_url(state: str) -> str:
    params = {
        CLIENT_ID_KEY: settings.dashboard_google_client_id,
        REDIRECT_URI_KEY: settings.dashboard_google_redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str, redirect_uri: str, client: httpx.Client) -> dict:
    response = client.post(
        TOKEN_URL,
        data={
            "code": code,
            CLIENT_ID_KEY: settings.dashboard_google_client_id,
            "client_secret": settings.dashboard_google_client_secret,
            REDIRECT_URI_KEY: redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    response.raise_for_status()
    return response.json()


def fetch_user_email(access_token: str, client: httpx.Client) -> str:
    response = client.get(
        USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    return response.json()["email"]