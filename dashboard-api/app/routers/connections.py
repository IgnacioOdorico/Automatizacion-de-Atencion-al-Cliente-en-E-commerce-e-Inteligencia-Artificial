import json
import secrets
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.core import google_oauth, telegram_codes
from app.core.config import settings
from app.core.deps import get_current_account_id
from app.core.security import encrypt_credentials
from app.core.sql import iso
from app.db import execute, fetch_all, fetch_one

router = APIRouter(prefix="/connections", tags=["connections"])

CHANNELS = ("whatsapp", "telegram", "email")
CHANNEL_LABELS = {"whatsapp": "WhatsApp", "telegram": "Telegram", "email": "Gmail"}
ChannelName = Literal["whatsapp", "telegram", "email"]


class TelegramConfirmRequest(BaseModel):
    code: str
    chat_id: str


class WhatsAppApprovalRequest(BaseModel):
    phone: str = Field(pattern=r"^\+?[1-9]\d{1,14}$", min_length=8)


def _ensure_connection_rows(account_id: int) -> None:
    existing = {
        row["channel"]
        for row in fetch_all(
            "SELECT channel FROM channel_connections WHERE client_account_id = :id",
            {"id": account_id},
        )
    }
    for channel in CHANNELS:
        if channel not in existing:
            execute(
                "INSERT INTO channel_connections (client_account_id, channel) "
                "VALUES (:id, :channel)",
                {"id": account_id, "channel": channel},
            )


def _set_connection(
    account_id: int,
    channel: str,
    new_status: str,
    external_reference: str | None = None,
    encrypted_credentials: str | None = None,
) -> None:
    execute(
        """
        INSERT INTO channel_connections
            (client_account_id, channel, status, external_reference, encrypted_credentials, connected_at)
        VALUES
            (:id, :channel, :status, :external_reference, :encrypted_credentials, NOW())
        ON CONFLICT (client_account_id, channel) DO UPDATE SET
            status = EXCLUDED.status,
            external_reference = EXCLUDED.external_reference,
            encrypted_credentials = EXCLUDED.encrypted_credentials,
            connected_at = EXCLUDED.connected_at
        """,
        {
            "id": account_id,
            "channel": channel,
            "status": new_status,
            "external_reference": external_reference,
            "encrypted_credentials": encrypted_credentials,
        },
    )


@router.get("")
def list_connections(account_id: int = Depends(get_current_account_id)) -> dict:
    _ensure_connection_rows(account_id)
    rows = fetch_all(
        f"""
        SELECT id, channel, status, external_reference, {iso('connected_at')} AS connected_at
        FROM channel_connections
        WHERE client_account_id = :id
        ORDER BY channel
        """,
        {"id": account_id},
    )
    items = [
        {**row, "label": CHANNEL_LABELS[row["channel"]]}
        for row in rows
        if "encrypted_credentials" not in row
    ]
    return {"items": items}


@router.delete("/{channel}")
def disconnect_channel(
    channel: ChannelName, account_id: int = Depends(get_current_account_id)
) -> dict:
    execute(
        """
        UPDATE channel_connections
        SET status = 'disconnected', external_reference = NULL,
            encrypted_credentials = NULL, connected_at = NULL
        WHERE client_account_id = :id AND channel = :channel
        """,
        {"id": account_id, "channel": channel},
    )
    return {"channel": channel, "status": "disconnected"}


@router.post("/telegram/start")
def telegram_start(account_id: int = Depends(get_current_account_id)) -> dict:
    return telegram_codes.start_code(account_id)


@router.post("/telegram/confirm")
def telegram_confirm(
    payload: TelegramConfirmRequest,
    x_n8n_secret: str | None = Header(default=None, alias="X-N8N-SECRET"),
) -> dict:
    if not x_n8n_secret or not secrets.compare_digest(
        x_n8n_secret, settings.dashboard_n8n_secret
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Secreto compartido inválido"
        )

    record = telegram_codes.validate_code(payload.code)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido o vencido",
        )

    _set_connection(
        record["account_id"],
        "telegram",
        "connected",
        external_reference=payload.chat_id,
    )
    telegram_codes.consume(payload.code)
    return {
        "channel": "telegram",
        "status": "connected",
        "external_reference": payload.chat_id,
    }


@router.get("/gmail/oauth-url")
def gmail_oauth_url(account_id: int = Depends(get_current_account_id)) -> dict:
    if not settings.dashboard_google_client_id or not settings.dashboard_google_redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth no configurado (DASHBOARD_GOOGLE_CLIENT_ID / DASHBOARD_GOOGLE_REDIRECT_URI)",
        )
    state = google_oauth.sign_state(account_id, "email")
    return {
        "url": google_oauth.build_consent_url(state),
        "state": state,
        "expires_in": google_oauth.STATE_TTL_MINUTES * 60,
    }


@router.get("/gmail/callback")
def gmail_callback(
    state: str,
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> RedirectResponse:
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Autorización de Google denegada: {error_description or error}",
        )
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta el código de autorización de Google",
        )

    state_data = google_oauth.verify_state(state)
    account_id = state_data["account_id"]

    client = google_oauth.create_client()
    try:
        try:
            tokens = google_oauth.exchange_code(
                code, settings.dashboard_google_redirect_uri, client
            )
            email = google_oauth.fetch_user_email(tokens["access_token"], client)
        except (httpx.HTTPError, KeyError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error al contactar los servicios de Google",
            ) from exc
    finally:
        client.close()

    if "refresh_token" not in tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google no devolvió refresh token (usá access_type=offline y prompt=consent)",
        )

    _set_connection(
        account_id,
        "email",
        "connected",
        external_reference=email,
        encrypted_credentials=encrypt_credentials(
            json.dumps({"refresh_token": tokens["refresh_token"]})
        ),
    )
    return RedirectResponse(
        f"{settings.dashboard_frontend_url}/connections?gmail=connected"
    )


@router.post("/whatsapp/request-approval")
def whatsapp_request_approval(
    payload: WhatsAppApprovalRequest,
    account_id: int = Depends(get_current_account_id),
) -> dict:
    row = fetch_one(
        "SELECT status FROM channel_connections "
        "WHERE client_account_id = :id AND channel = 'whatsapp'",
        {"id": account_id},
    )

    if row is None or row["status"] != "connected":
        _set_connection(
            account_id,
            "whatsapp",
            "pending",
            external_reference=payload.phone.replace(" ", ""),
        )
        return {
            "channel": "whatsapp",
            "status": "pending",
            "message": "Solicitud enviada, Meta aprueba en 1-3 días hábiles",
        }

    return {
        "channel": "whatsapp",
        "status": "connected",
        "message": "El canal ya está conectado y operativo",
    }