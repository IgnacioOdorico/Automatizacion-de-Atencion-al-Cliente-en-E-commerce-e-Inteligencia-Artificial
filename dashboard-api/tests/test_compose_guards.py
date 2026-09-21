"""Guardas sobre docker-compose.yml (sin BD ni red): config coherente y sin secretos."""

import re
from pathlib import Path

COMPOSE = (Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text(
    encoding="utf-8"
)


def _default(var: str) -> str:
    """Valor por defecto `${VAR:-default}` que el compose le da a `var` en dashboard-api."""
    match = re.search(rf"{var}=\$\{{{var}:-([^}}]*)\}}", COMPOSE)
    assert match, f"{var} no tiene la forma ${{{var}:-default}} en docker-compose.yml"
    return match.group(1)


def test_frontend_url_default_points_to_the_dockerized_web():
    # La demo Docker sirve el front en :8080; el callback de Gmail redirige ahí.
    # En desarrollo con Vite se pisa por .env con http://localhost:5173.
    assert _default("DASHBOARD_FRONTEND_URL") == "http://localhost:8080"


def test_frontend_url_default_is_whitelisted_in_cors():
    origins = [o.strip() for o in _default("CORS_ORIGINS").split(",") if o.strip()]
    assert "*" not in origins
    assert _default("DASHBOARD_FRONTEND_URL") in origins
    assert "http://localhost:5173" in origins


SECRET_VARS = ("DASHBOARD_JWT_SECRET", "DASHBOARD_ENC_KEY", "DASHBOARD_N8N_SECRET")


def test_compose_has_no_default_value_for_dashboard_secrets():
    # Fail-closed: sin valor en .env el contenedor recibe vacío y la API no arranca
    # (en vez de correr con un secreto de ejemplo publicado en el repo).
    for var in SECRET_VARS:
        for match in re.finditer(rf"{var}=\$\{{{var}:-([^}}]*)\}}", COMPOSE):
            assert match.group(1) == "", f"{var} tiene un default en docker-compose.yml"


def test_compose_never_hardcodes_a_secret_literal():
    for var in SECRET_VARS + ("DASHBOARD_GOOGLE_CLIENT_SECRET", "DASHBOARD_BOT_TOKEN_VINCULO"):
        for line in COMPOSE.splitlines():
            if f"{var}=" in line and not line.lstrip().startswith("#"):
                assert re.search(rf"{var}=\$\{{{var}(:-)?\}}\s*$", line), line.strip()


def test_compose_has_no_known_weak_secret_strings():
    assert "-cambiar" not in COMPOSE
    assert "demo-dashboard" not in COMPOSE and "demo-n8n" not in COMPOSE


def test_only_the_web_proxy_is_trusted_for_the_client_ip():
    # Nunca un rango amplio: un acceso directo a :8000 podría spoofear X-Real-IP.
    assert _default("DASHBOARD_TRUSTED_PROXIES") == "dashboard-web"


def test_api_docs_are_off_by_default_in_compose():
    assert _default("DASHBOARD_ENABLE_DOCS") == "false"
