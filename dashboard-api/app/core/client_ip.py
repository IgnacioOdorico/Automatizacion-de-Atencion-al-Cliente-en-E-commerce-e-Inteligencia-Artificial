"""IP real del cliente para el rate limit de /auth/login.

Detrás de nginx, `request.client.host` es SIEMPRE la IP del proxy: todos los clientes
compartirían un bucket (cualquiera podría bloquear el login de los demás). Pero leer
`X-Forwarded-For`/`X-Real-IP` sin más permite spoofearlos y evadir el límite. Por eso:

  - Solo se confía en el header si el peer directo es un proxy conocido
    (DASHBOARD_TRUSTED_PROXIES: IPs, CIDRs o nombres de host, p. ej. `dashboard-web`).
  - Solo se lee `X-Real-IP` (nginx lo PISA con $remote_addr; no lo concatena como XFF).
  - Un valor que no sea una IP válida se descarta y se usa la IP del peer.
"""

import ipaddress
import socket
import time

from fastapi import Request

from app.core.config import settings

_DNS_TTL_SECONDS = 10.0

_IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network
_cache: dict = {"key": None, "at": 0.0, "networks": [], "literals": set()}


def reset_cache() -> None:
    _cache.update(key=None, at=0.0, networks=[], literals=set())


def _load_trusted(entries: str) -> tuple[list[_IPNetwork], set[str]]:
    networks: list[_IPNetwork] = []
    literals: set[str] = set()
    for entry in (part.strip() for part in entries.split(",")):
        if not entry:
            continue
        literals.add(entry)
        try:
            networks.append(ipaddress.ip_network(entry, strict=False))
            continue
        except ValueError:
            pass
        # Nombre de host (p. ej. el servicio `dashboard-web` de docker compose).
        try:
            for info in socket.getaddrinfo(entry, None):
                networks.append(ipaddress.ip_network(info[4][0], strict=False))
        except (socket.gaierror, ValueError):
            continue  # no resuelve -> no se confía en nadie por esa entrada
    return networks, literals


def _trusted() -> tuple[list[_IPNetwork], set[str]]:
    entries = settings.dashboard_trusted_proxies
    now = time.monotonic()
    if _cache["key"] != entries or now - _cache["at"] > _DNS_TTL_SECONDS:
        networks, literals = _load_trusted(entries)
        _cache.update(key=entries, at=now, networks=networks, literals=literals)
    return _cache["networks"], _cache["literals"]


def _is_trusted_peer(peer: str) -> bool:
    networks, literals = _trusted()
    if peer in literals:
        return True
    try:
        address = ipaddress.ip_address(peer)
    except ValueError:
        return False
    return any(address in network for network in networks)


def get_client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    if peer == "unknown" or not _is_trusted_peer(peer):
        return peer
    forwarded = request.headers.get("x-real-ip", "").strip()
    try:
        return str(ipaddress.ip_address(forwarded))
    except ValueError:
        return peer
