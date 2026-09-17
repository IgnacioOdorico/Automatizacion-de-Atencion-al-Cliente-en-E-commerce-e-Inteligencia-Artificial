from datetime import datetime, timezone

import jwt
import pytest

DEMO_HASH = "$2b$12$gFkzp0IobEcDZSP0zYjW/OfQtaF2tqxGTA6JgSXT3Ak476cnPt/M."


def test_hash_password_is_bcrypt_and_not_plaintext():
    from app.core.security import hash_password

    digest = hash_password("Demo2026!")
    assert digest != "Demo2026!"
    assert digest.startswith("$2")
    assert len(digest) == 60


def test_verify_password_ok_and_wrong():
    from app.core.security import hash_password, verify_password

    digest = hash_password("Secreta123")
    assert verify_password("Secreta123", digest) is True
    assert verify_password("Secreta124", digest) is False


def test_demo_seed_hash_matches_demo_password():
    from app.core.security import verify_password

    assert verify_password("Demo2026!", DEMO_HASH) is True
    assert verify_password("otra", DEMO_HASH) is False


def test_access_token_roundtrip_and_expiry():
    from app.core.security import create_access_token, decode_access_token

    token = create_access_token(42)
    payload = decode_access_token(token)
    assert int(payload["sub"]) == 42
    assert payload["type"] == "access"
    assert payload["exp"] - payload["iat"] == 2 * 60 * 60


def test_refresh_token_has_seven_day_expiry():
    from app.core.security import create_refresh_token, decode_refresh_token

    token = create_refresh_token(7)
    payload = decode_refresh_token(token)
    assert int(payload["sub"]) == 7
    assert payload["type"] == "refresh"
    assert payload["exp"] - payload["iat"] == 7 * 24 * 60 * 60


def test_decode_rejects_wrong_signature():
    from app.core.security import InvalidTokenError, decode_access_token

    forged = jwt.encode(
        {"sub": "1", "type": "access", "iat": datetime.now(timezone.utc)},
        "otro-secreto",
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(forged)


def test_decode_access_rejects_refresh_token():
    from app.core.security import InvalidTokenError, create_refresh_token, decode_access_token

    token = create_refresh_token(1)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_fernet_roundtrip():
    from app.core.security import decrypt_credentials, encrypt_credentials

    secret = '{"refresh_token":"1//abc"}'
    ciphertext = encrypt_credentials(secret)
    assert ciphertext != secret
    assert decrypt_credentials(ciphertext) == secret


def test_fernet_wrong_key_cannot_decrypt(monkeypatch):
    from app.core import security
    from cryptography.fernet import Fernet, InvalidToken

    ciphertext = security.encrypt_credentials("hola")
    other = Fernet(Fernet.generate_key())
    with pytest.raises(InvalidToken):
        other.decrypt(ciphertext.encode())


def test_auth_dependency_missing_header_raises_401():
    from fastapi import HTTPException

    from app.core.deps import get_current_account_id

    with pytest.raises(HTTPException) as exc:
        get_current_account_id(None)
    assert exc.value.status_code == 401


def test_auth_dependency_injects_account_id():
    from app.core.deps import get_current_account_id
    from app.core.security import create_access_token

    token = create_access_token(99)
    assert get_current_account_id(f"Bearer {token}") == 99


def test_auth_dependency_rejects_invalid_token():
    from fastapi import HTTPException

    from app.core.deps import get_current_account_id

    with pytest.raises(HTTPException) as exc:
        get_current_account_id("Bearer no-es-un-jwt")
    assert exc.value.status_code == 401