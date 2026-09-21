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
