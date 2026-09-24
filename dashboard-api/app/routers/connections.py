import json
import logging
import secrets
from typing import Literal
from urllib.parse import urlencode

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
logger = logging.getLogger(__name__)

CHANNELS = ("whatsapp", "telegram", "email")
CHANNEL_LABELS = {"whatsapp": "WhatsApp", "telegram": "Telegram", "email": "Gmail"}
ChannelName = Literal["whatsapp", "telegram", "email"]


class TelegramConfirmRequest(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    chat_id: str = Field(min_length=1, max_length=64)


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
    if channel == "telegram":
        # Un código de vinculación vivo no puede reconectar el canal después de
        # desconectarlo: se invalida el pendiente de ESTA cuenta.
        telegram_codes.cancel(account_id)
    return {"channel": channel, "status": "disconnected"}


@router.post("/telegram/start")
def telegram_start(account_id: int = Depends(get_current_account_id)) -> dict:
    return telegram_codes.start_code(account_id)


@router.delete("/telegram/code")
def telegram_cancel_code(account_id: int = Depends(get_current_account_id)) -> dict:
    """Cancela el código de vinculación pendiente de la cuenta autenticada.

    No toca el estado del canal (eso es DELETE /connections/telegram) y es
    idempotente: sin código pendiente responde 200 con `cancelled: false`.
    """
    return {"cancelled": telegram_codes.cancel(account_id)}


@router.post("/telegram/confirm")
def telegram_confirm(
    payload: TelegramConfirmRequest,
    x_n8n_secret: str | None = Header(default=None, alias="X-N8N-SECRET"),
) -> dict:
    # En bytes: compare_digest sobre str lanza TypeError con caracteres no ASCII.
    if not x_n8n_secret or not secrets.compare_digest(
        x_n8n_secret.encode("utf-8"), settings.dashboard_n8n_secret.encode("utf-8")
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


# Ruta del front a la que vuelve el navegador tras el callback de Google.
FRONTEND_CONNECTIONS_PATH = "/conexiones"

# Códigos cortos y estables de `?gmail=error&reason=<código>`. El front los mapea
# a un mensaje; nunca viajan detalles internos, tokens ni mensajes de excepción.
GmailErrorReason = Literal[
    "denied",  # el usuario canceló en Google (access_denied)
    "google_error",  # otro `error` informado por Google
    "invalid_state",  # state ausente, inválido, vencido o de otro canal
    "missing_code",  # Google no envió el código de autorización
    "exchange_failed",  # Google rechazó el canje del código
    "upstream",  # Google no respondió bien (red, timeout, 5xx)
    "no_email",  # no se pudo obtener el email de la cuenta
    "no_refresh",  # Google no devolvió refresh token
    "internal",  # falló el guardado en nuestra BD
]


class _GmailCallbackError(Exception):
    def __init__(self, reason: GmailErrorReason) -> None:
        super().__init__(reason)
        self.reason = reason


def _frontend_redirect(gmail: str, reason: GmailErrorReason | None = None) -> RedirectResponse:
    """Redirect al front. El destino sale siempre de la configuración, nunca del request."""
    query = {"gmail": gmail}
    if reason:
        query["reason"] = reason
    base = settings.dashboard_frontend_url.rstrip("/")
    return RedirectResponse(f"{base}{FRONTEND_CONNECTIONS_PATH}?{urlencode(query)}")


def _complete_gmail_connection(
    state: str | None, code: str | None, error: str | None
) -> None:
    # La seguridad del endpoint (sin JWT) es el `state` firmado: se valida primero.
    if not state:
        raise _GmailCallbackError("invalid_state")
    try:
        state_data = google_oauth.verify_state(state)
    except (HTTPException, KeyError, ValueError) as exc:
        raise _GmailCallbackError("invalid_state") from exc
    account_id = state_data["account_id"]

    if error:
        raise _GmailCallbackError("denied" if error == "access_denied" else "google_error")
    if not code:
        raise _GmailCallbackError("missing_code")

    client = google_oauth.create_client()
    try:
        try:
            tokens = google_oauth.exchange_code(
                code, settings.dashboard_google_redirect_uri, client
            )
        except httpx.HTTPStatusError as exc:
            reason = "exchange_failed" if exc.response.status_code < 500 else "upstream"
            raise _GmailCallbackError(reason) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise _GmailCallbackError("upstream") from exc

        access_token = tokens.get("access_token") if isinstance(tokens, dict) else None
        if not access_token:
            raise _GmailCallbackError("exchange_failed")

        try:
            email = google_oauth.fetch_user_email(access_token, client)
        except (KeyError, TypeError) as exc:
            raise _GmailCallbackError("no_email") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise _GmailCallbackError("upstream") from exc
    finally:
        client.close()

    if not email:
        raise _GmailCallbackError("no_email")
    if "refresh_token" not in tokens:
        raise _GmailCallbackError("no_refresh")

    try:
        _set_connection(
            account_id,
            "email",
            "connected",
            external_reference=email,
            encrypted_credentials=encrypt_credentials(
                json.dumps({"refresh_token": tokens["refresh_token"]})
            ),
        )
    except Exception as exc:  # noqa: BLE001 - el navegador nunca debe ver un 500 crudo
        logger.error("Falló el guardado de la conexión de Gmail (%s)", type(exc).__name__)
        raise _GmailCallbackError("internal") from exc


@router.get("/gmail/callback")
def gmail_callback(
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Callback de Google (sin JWT: lo llama el navegador). Siempre responde con un redirect al front."""
    try:
        _complete_gmail_connection(state, code, error)
    except _GmailCallbackError as exc:
        return _frontend_redirect("error", exc.reason)
    return _frontend_redirect("connected")


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