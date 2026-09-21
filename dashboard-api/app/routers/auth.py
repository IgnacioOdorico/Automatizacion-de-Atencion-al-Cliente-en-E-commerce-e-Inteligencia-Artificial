from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError

from app.core import rate_limit
from app.core.config import settings
from app.core.deps import get_current_account_id
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.core.sql import iso
from app.db import execute_returning_one, fetch_all, fetch_one

router = APIRouter(tags=["auth"])

REFRESH_COOKIE = "refresh_token"
_used_refresh_jtis: set[str] = set()


class RegisterRequest(BaseModel):
    business_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


def _issue_tokens(response: Response, account_id: int) -> dict:
    access_token = create_access_token(account_id)
    refresh_token = create_refresh_token(account_id)
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> dict:
    email = payload.email.lower()
    if fetch_one("SELECT id FROM client_accounts WHERE email = :email", {"email": email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )
    try:
        # Una sola sentencia (atómica): la cuenta y sus 3 conexiones `disconnected`
        # (spec connections), así /me no devuelve `connections: []` tras el alta.
        account = execute_returning_one(
            f"""
            WITH new_account AS (
                INSERT INTO client_accounts (business_name, email, password_hash)
                VALUES (:business_name, :email, :password_hash)
                RETURNING id, business_name, email, created_at
            ),
            initial_connections AS (
                INSERT INTO channel_connections (client_account_id, channel)
                SELECT new_account.id, channel.name
                FROM new_account,
                     unnest(ARRAY['whatsapp', 'telegram', 'email']) AS channel(name)
            )
            SELECT id, business_name, email, {iso('created_at')} AS created_at
            FROM new_account
            """,
            {
                "business_name": payload.business_name,
                "email": email,
                "password_hash": hash_password(payload.password),
            },
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        ) from exc
    return account


@router.post("/auth/login")
def login(payload: LoginRequest, request: Request, response: Response) -> dict:
    email = payload.email.lower()
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"ip:{client_ip}"
    email_key = f"email:{email}"

    if rate_limit.is_blocked(ip_key, email_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Reintentá en unos minutos.",
        )

    account = fetch_one(
        "SELECT id, password_hash FROM client_accounts WHERE email = :email",
        {"email": email},
    )
    if account is None or not verify_password(payload.password, account["password_hash"]):
        rate_limit.record_failure(ip_key, email_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    rate_limit.clear(ip_key, email_key)
    return _issue_tokens(response, account["id"])


@router.post("/auth/refresh")
def refresh(payload: RefreshRequest, request: Request, response: Response) -> dict:
    token = payload.refresh_token or request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token ausente",
        )
    try:
        data = decode_refresh_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o vencido",
        ) from exc

    jti = data.get("jti")
    if not jti or jti in _used_refresh_jtis:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token ya utilizado",
        )
    _used_refresh_jtis.add(jti)
    return _issue_tokens(response, int(data["sub"]))


@router.get("/me")
def me(account_id: int = Depends(get_current_account_id)) -> dict:
    account = fetch_one(
        f"""
        SELECT id, business_name, email, {iso('created_at')} AS created_at
        FROM client_accounts
        WHERE id = :id
        """,
        {"id": account_id},
    )
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta no encontrada",
        )
    account["connections"] = fetch_all(
        f"""
        SELECT id, channel, status, external_reference,
               {iso('connected_at')} AS connected_at
        FROM channel_connections
        WHERE client_account_id = :id
        ORDER BY channel
        """,
        {"id": account_id},
    )
    return account