import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from cryptography.fernet import Fernet

from app.core.config import settings

ALGORITHM = "HS256"
BCRYPT_ROUNDS = 12


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode(
        "utf-8"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_token(subject: int, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.dashboard_jwt_secret, algorithm=ALGORITHM)


def create_access_token(account_id: int) -> str:
    return _create_token(
        account_id, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(account_id: int) -> str:
    return _create_token(
        account_id, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.dashboard_jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Token inválido o vencido") from exc


def decode_access_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise InvalidTokenError("Se esperaba un access token")
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise InvalidTokenError("Se esperaba un refresh token")
    return payload


def _fernet() -> Fernet:
    if not settings.dashboard_enc_key:
        raise RuntimeError("DASHBOARD_ENC_KEY no está configurada")
    return Fernet(settings.dashboard_enc_key.encode("utf-8"))


def encrypt_credentials(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_credentials(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")