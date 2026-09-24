import os


def test_settings_read_from_env():
    from app.core.config import settings

    assert settings.database_url.endswith("/ecommerce_tesis_test")
    assert settings.dashboard_jwt_secret == os.environ["DASHBOARD_JWT_SECRET"]
    assert settings.dashboard_n8n_secret == os.environ["DASHBOARD_N8N_SECRET"]
    assert settings.access_token_expire_minutes == 120
    assert settings.refresh_token_expire_days == 7


def test_cors_whitelist_is_explicit():
    from app.core.config import settings

    origins = settings.cors_origins_list
    assert origins == ["http://localhost:5173", "http://localhost:8080"]
    assert "*" not in origins


def test_cors_preflight_blocks_unknown_origin(client):
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") is None


def test_cors_preflight_allows_whitelisted_origin(client):
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

# ---------------------------------------------------------------------------
# Fail-closed: la API se niega a arrancar con secretos ausentes, cortos o de ejemplo.
# ---------------------------------------------------------------------------
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

STRONG_JWT = "Zk3v9Qm7Lp2Xc8Rb5Tn1Wy6Hd4Sf0Ja-Ue7Gi2Ko9"
STRONG_N8N = "Pw8Nd2Kc5Vb1Xz7Qm4Lr9Ts3Hj6Yf0Ge-Ua8Oi1Ek5"
API_DIR = Path(__file__).resolve().parents[1]


def _make(**overrides):
    from app.core.config import Settings

    values = {
        "dashboard_jwt_secret": STRONG_JWT,
        "dashboard_enc_key": Fernet.generate_key().decode(),
        "dashboard_n8n_secret": STRONG_N8N,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_validate_secrets_accepts_strong_values():
    from app.core.config import validate_secrets

    validate_secrets(_make())


@pytest.mark.parametrize(
    "variable,field",
    [
        ("DASHBOARD_JWT_SECRET", "dashboard_jwt_secret"),
        ("DASHBOARD_N8N_SECRET", "dashboard_n8n_secret"),
    ],
)
@pytest.mark.parametrize(
    "weak",
    [
        "",
        "   ",
        "demo-dashboard-jwt-secret",
        "demo-dashboard-jwt-secret-cambiar",
        "demo-n8n-secret",
        "demo-n8n-secret-cambiar",
        "changeme",
        "a-short-one",
        "x" * 40,
        "ab" * 20,
    ],
)
def test_validate_secrets_rejects_empty_short_or_known_defaults(variable, field, weak):
    from app.core.config import InsecureConfigurationError, validate_secrets

    with pytest.raises(InsecureConfigurationError) as exc:
        validate_secrets(_make(**{field: weak}))
    assert variable in str(exc.value)


@pytest.mark.parametrize("bad_key", ["", "no-es-fernet", "a" * 44, "===="])
def test_validate_secrets_rejects_missing_or_invalid_fernet_key(bad_key):
    from app.core.config import InsecureConfigurationError, validate_secrets

    with pytest.raises(InsecureConfigurationError) as exc:
        validate_secrets(_make(dashboard_enc_key=bad_key))
    assert "DASHBOARD_ENC_KEY" in str(exc.value)


def test_validate_secrets_rejects_reusing_one_secret_for_jwt_and_n8n():
    from app.core.config import InsecureConfigurationError, validate_secrets

    with pytest.raises(InsecureConfigurationError) as exc:
        validate_secrets(_make(dashboard_n8n_secret=STRONG_JWT))
    assert "DASHBOARD_N8N_SECRET" in str(exc.value)


def test_error_names_the_variables_but_never_echoes_a_value():
    from app.core.config import InsecureConfigurationError, validate_secrets

    leaked = "debil-que-no-sale-en-logs"
    with pytest.raises(InsecureConfigurationError) as exc:
        validate_secrets(_make(dashboard_jwt_secret=leaked, dashboard_enc_key="basura-enc"))
    text = str(exc.value)
    assert "DASHBOARD_JWT_SECRET" in text and "DASHBOARD_ENC_KEY" in text
    assert leaked not in text and "basura-enc" not in text


def _import_app(**env_overrides):
    import os

    env = {**os.environ, **env_overrides}
    return subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=API_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_the_app_refuses_to_start_with_a_weak_jwt_secret():
    result = _import_app(DASHBOARD_JWT_SECRET="demo-dashboard-jwt-secret-cambiar")
    assert result.returncode != 0
    assert "DASHBOARD_JWT_SECRET" in result.stderr


def test_the_app_refuses_to_start_with_no_encryption_key():
    result = _import_app(DASHBOARD_ENC_KEY="")
    assert result.returncode != 0
    assert "DASHBOARD_ENC_KEY" in result.stderr


def test_the_app_starts_with_strong_secrets():
    result = _import_app()
    assert result.returncode == 0, result.stderr
