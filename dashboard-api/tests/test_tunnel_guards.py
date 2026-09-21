"""Guardas del túnel público de Telegram (perfil `tunnel` del compose), sin red ni Docker.

Cubren lo que NO debe romperse: que el arranque por defecto siga sin ngrok ni tokens, que el
gateway no publique puertos ni tenga más rutas que el webhook del Telegram Trigger, y que el
Flujo 3 no dependa de `$env` (n8n 2.x lo bloquea por defecto) ni lleve secretos en el JSON.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
GATEWAY_CONF = (ROOT / "webhook-gateway" / "nginx.conf").read_text(encoding="utf-8")
FLUJO3_PATH = ROOT / "workflows" / "Flujo 3 — Telegram Vínculo de Cuenta.json"

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def _service(name: str) -> str:
    """Bloque de texto del servicio `name` en el compose (líneas con >= 4 espacios)."""
    match = re.search(
        rf"^  {re.escape(name)}:\n((?:(?:    .*)?\n)+)", COMPOSE, flags=re.MULTILINE
    )
    assert match, f"el servicio {name} no está en docker-compose.yml"
    return match.group(1)


def _code(text: str) -> str:
    """Texto sin las líneas de comentario."""
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


# ---------------------------------------------------------------- compose

def test_tunnel_services_only_start_with_the_tunnel_profile():
    for name in ("webhook-gateway", "ngrok"):
        assert re.search(r'^\s+profiles:\s*\["tunnel"\]\s*$', _service(name), re.MULTILINE), name


def test_default_startup_never_requires_tunnel_variables():
    # Compose interpola TODO el archivo aunque el perfil esté inactivo: un `${VAR:?...}`
    # en el túnel rompería `docker compose up -d` para quien no usa ngrok.
    for name in ("webhook-gateway", "ngrok"):
        assert ":?" not in _code(_service(name)), name
    for var in ("NGROK_AUTHTOKEN", "NGROK_DOMAIN"):
        assert re.search(rf"{var}=\$\{{{var}:-\}}\s*$", _service("ngrok"), re.MULTILINE), var


def test_ngrok_carries_no_secret_literal():
    ngrok = _code(_service("ngrok"))
    assert not re.search(r"NGROK_AUTHTOKEN=(?!\$\{NGROK_AUTHTOKEN:-\})\S", ngrok)
    assert "--authtoken" not in ngrok  # el token viaja solo por la variable de entorno


def test_gateway_publishes_no_port_to_the_host():
    # Solo ngrok (misma red de Docker) le habla: un puerto publicado lo expondría en la LAN.
    assert "ports:" not in _code(_service("webhook-gateway"))


def test_gateway_config_is_mounted_read_only_from_the_repo():
    assert "./webhook-gateway/nginx.conf:/etc/nginx/conf.d/default.conf:ro" in _service(
        "webhook-gateway"
    )


def test_ngrok_waits_for_a_healthy_gateway_and_points_at_it():
    ngrok = _service("ngrok")
    assert re.search(r"webhook-gateway:\s*\n\s+condition:\s*service_healthy", ngrok)
    assert "webhook-gateway:80" in ngrok


def test_n8n_does_not_receive_dashboard_secrets_nor_unblock_env_access():
    # Los secretos del vínculo viven como credenciales de n8n (cifradas), no como env
    # legibles con `$env` desde cualquier Code node de cualquier flujo.
    n8n = _code(_service("n8n"))
    assert "DASHBOARD_N8N_SECRET" not in n8n
    assert "DASHBOARD_BOT_TOKEN_VINCULO" not in n8n
    assert "N8N_BLOCK_ENV_ACCESS_IN_NODE" not in n8n


def test_n8n_proxy_hops_and_editor_url_have_backwards_compatible_defaults():
    n8n = _service("n8n")
    # Sin túnel, n8n no confía en X-Forwarded-* y el editor sigue siendo localhost.
    assert "N8N_PROXY_HOPS=${N8N_PROXY_HOPS:-0}" in n8n
    assert "N8N_EDITOR_BASE_URL=${N8N_EDITOR_BASE_URL:-http://localhost:5678}" in n8n
    assert "WEBHOOK_URL=${WEBHOOK_URL:-http://localhost:5678/}" in n8n


# ---------------------------------------------------------------- gateway

def test_gateway_denies_everything_except_the_telegram_webhook():
    conf = _code(GATEWAY_CONF)
    # Un único destino: el webhook del Telegram Trigger, con UUID en minúsculas.
    assert conf.count("proxy_pass") == 1
    locations = re.findall(r"^\s*location\s+(.+?)\s+\{\s*$", conf, flags=re.MULTILINE)
    hook = [l for l in locations if "webhook" in l and l != "= /healthz"]
    assert len(hook) == 1
    # Entre comillas: nginx toma las llaves de {8} como bloque si no.
    assert hook[0].startswith('~ "^/webhook/[0-9a-f]{8}-')
    assert hook[0].endswith('/webhook$"')
    # Todo lo demás: 404.
    assert re.search(r"location\s+/\s*\{\s*return\s+404", conf)
    # Solo POST, sin query string, sin reenviar credenciales de n8n.
    assert "$request_method != POST" in conf
    assert '$args != ""' in conf
    for header in ("Authorization", "Cookie", "X-N8N-API-KEY"):
        assert f'proxy_set_header {header} ""' in conf, header
    # El upstream se arma con el URI ya validado, no con el crudo del cliente.
    assert "proxy_pass $n8n_upstream$uri;" in conf
    assert re.search(r"client_max_body_size\s+\d+k;", conf)
    assert "limit_req " in conf


def test_gateway_healthcheck_listener_is_loopback_only():
    assert "listen 127.0.0.1:8081;" in GATEWAY_CONF


# ---------------------------------------------------------------- Flujo 3

def _flujo3() -> dict:
    return json.loads(FLUJO3_PATH.read_text(encoding="utf-8"))


def test_flujo3_stays_inactive_and_is_valid_json():
    assert _flujo3()["active"] is False


def test_flujo3_does_not_use_env_expressions():
    # n8n 2.x: `$env` en expresiones tira "access to env vars denied" por defecto.
    for node in _flujo3()["nodes"]:
        if node["type"] == "n8n-nodes-base.stickyNote":
            continue
        assert "$env" not in json.dumps(node["parameters"]), node["name"]


def test_flujo3_authenticates_the_api_call_with_a_header_auth_credential():
    nodes = {n["name"]: n for n in _flujo3()["nodes"] if "name" in n}
    http = nodes["Confirmar Vínculo (API)"]
    assert http["parameters"]["url"] == "http://dashboard-api:8000/connections/telegram/confirm"
    assert http["parameters"]["authentication"] == "genericCredentialType"
    assert http["parameters"]["genericAuthType"] == "httpHeaderAuth"
    assert "httpHeaderAuth" in http["credentials"]
    # El secreto no viaja en el JSON: ni como header literal ni como parámetro.
    assert "X-N8N-SECRET" not in json.dumps(http["parameters"])


def test_flujo3_trigger_webhook_id_is_a_uuid_so_the_gateway_lets_it_through():
    trigger = next(n for n in _flujo3()["nodes"] if n["type"] == "n8n-nodes-base.telegramTrigger")
    assert UUID_RE.match(trigger["webhookId"]), trigger["webhookId"]


def test_flujo3_carries_no_token_or_secret_values():
    raw = FLUJO3_PATH.read_text(encoding="utf-8")
    assert not re.search(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b", raw)  # forma de token de Telegram
