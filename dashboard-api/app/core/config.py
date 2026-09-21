from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False
    )

    app_name: str = "TESIS Dashboard API"
    database_url: str = (
        "postgresql+psycopg://n8n_user:n8n_pass@postgres:5432/ecommerce_tesis"
    )
    # Sin valor por defecto utilizable: `validate_secrets` (abajo) hace que la API
    # NO arranque si falta, está vacío o es un valor de ejemplo (fail-closed).
    dashboard_jwt_secret: str = ""
    dashboard_enc_key: str = ""
    dashboard_n8n_secret: str = ""
    dashboard_google_client_id: str = ""
    dashboard_google_client_secret: str = ""
    dashboard_google_redirect_uri: str = ""
    dashboard_frontend_url: str = "http://localhost:5173"
    telegram_code_ttl_minutes: int = 15
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    # Proxies (IP, CIDR o nombre de host) en los que se confía para leer X-Real-IP.
    # Vacío = no se confía en ningún header (se usa la IP del peer directo).
    dashboard_trusted_proxies: str = ""
    # /docs, /redoc y /openapi.json exponen el mapa completo de la API: apagados por
    # defecto; se prenden solo para desarrollo (DASHBOARD_ENABLE_DOCS=true).
    dashboard_enable_docs: bool = False

    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


MIN_SECRET_LENGTH = 32
# Valores de ejemplo que circularon en el repo/compose o son los típicos de un tutorial.
_WEAK_SECRETS = frozenset(
    {"changeme", "change-me", "secret", "password", "cambiar", "demo", "test"}
)
_WEAK_MARKERS = ("cambiar", "changeme", "change-me", "demo-", "example", "ejemplo", "placeholder")


class InsecureConfigurationError(RuntimeError):
    """Configuración de seguridad inválida. El mensaje nombra variables, NUNCA valores."""


def _weakness(value: str) -> str | None:
    """Por qué un secreto no es aceptable (None si lo es). Nunca incluye el valor."""
    if not value.strip():
        return "está vacía"
    if value != value.strip():
        return "tiene espacios al inicio o al final"
    if len(value) < MIN_SECRET_LENGTH:
        return f"es demasiado corta (mínimo {MIN_SECRET_LENGTH} caracteres)"
    lowered = value.lower()
    if lowered in _WEAK_SECRETS or any(marker in lowered for marker in _WEAK_MARKERS):
        return "es un valor de ejemplo o por defecto"
    if len(set(value)) < 8:
        return "tiene muy poca variedad de caracteres"
    return None


def validate_secrets(config: Settings) -> None:
    """Fail-closed: la API no corre con secretos ausentes, débiles o de ejemplo."""
    problems: list[str] = []

    for variable, value in (
        ("DASHBOARD_JWT_SECRET", config.dashboard_jwt_secret),
        ("DASHBOARD_N8N_SECRET", config.dashboard_n8n_secret),
    ):
        reason = _weakness(value)
        if reason:
            problems.append(f"{variable} {reason}")

    if (
        config.dashboard_jwt_secret
        and config.dashboard_jwt_secret == config.dashboard_n8n_secret
    ):
        problems.append("DASHBOARD_N8N_SECRET no puede ser igual a DASHBOARD_JWT_SECRET")

    try:
        Fernet(config.dashboard_enc_key.encode("utf-8"))
    except (ValueError, TypeError):
        problems.append(
            "DASHBOARD_ENC_KEY no está definida o no es una clave Fernet válida "
            "(base64 urlsafe de 32 bytes)"
        )

    if problems:
        raise InsecureConfigurationError(
            "Configuración de seguridad inválida, la API no arranca: "
            + "; ".join(problems)
            + ". Definí valores propios en .env (ver .env.example para cómo generarlos)."
        )


settings = Settings()
validate_secrets(settings)