"""IP real del cliente detrás del proxy (nginx) para el rate limit de /auth/login.

Reglas: sin proxies configurados NO se confía en ningún header; con proxies, solo si el
peer directo es uno de ellos y solo se lee X-Real-IP (lo pisa nginx con $remote_addr).
"""

import socket

import pytest
from starlette.requests import Request

PROXY = "172.19.0.5"


def _request(peer, headers=None):
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/login",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": (peer, 40000) if peer is not None else None,
    }
    return Request(scope)


@pytest.fixture
def trusted(monkeypatch):
    from app.core import client_ip
    from app.core.config import settings

    def set_trusted(value):
        monkeypatch.setattr(settings, "dashboard_trusted_proxies", value)
        client_ip.reset_cache()

    yield set_trusted
    client_ip.reset_cache()


def test_without_trusted_proxies_headers_are_ignored(trusted):
    from app.core.client_ip import get_client_ip

    trusted("")
    request = _request(
        PROXY, {"X-Real-IP": "9.9.9.9", "X-Forwarded-For": "8.8.8.8"}
    )
    assert get_client_ip(request) == PROXY


def test_trusted_peer_uses_x_real_ip(trusted):
    from app.core.client_ip import get_client_ip

    trusted(PROXY)
    assert get_client_ip(_request(PROXY, {"X-Real-IP": "203.0.113.7"})) == "203.0.113.7"


def test_trusted_cidr_matches_the_peer(trusted):
    from app.core.client_ip import get_client_ip

    trusted("10.0.0.0/8, 172.19.0.0/16")
    assert get_client_ip(_request(PROXY, {"X-Real-IP": "203.0.113.7"})) == "203.0.113.7"


def test_untrusted_peer_cannot_spoof_via_headers(trusted):
    from app.core.client_ip import get_client_ip

    trusted("172.19.0.9")
    request = _request(PROXY, {"X-Real-IP": "9.9.9.9", "X-Forwarded-For": "8.8.8.8"})
    assert get_client_ip(request) == PROXY


def test_trusted_hostname_is_resolved_through_dns(trusted, monkeypatch):
    from app.core.client_ip import get_client_ip

    def fake_getaddrinfo(host, *args, **kwargs):
        assert host == "dashboard-web"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (PROXY, 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    trusted("dashboard-web")
    assert get_client_ip(_request(PROXY, {"X-Real-IP": "203.0.113.7"})) == "203.0.113.7"
    # otro contenedor de la red NO es el proxy conocido
    assert get_client_ip(_request("172.19.0.77", {"X-Real-IP": "9.9.9.9"})) == "172.19.0.77"


def test_unresolvable_hostname_trusts_nobody(trusted, monkeypatch):
    from app.core.client_ip import get_client_ip

    def boom(*args, **kwargs):
        raise socket.gaierror("no resuelve")

    monkeypatch.setattr(socket, "getaddrinfo", boom)
    trusted("dashboard-web")
    assert get_client_ip(_request(PROXY, {"X-Real-IP": "9.9.9.9"})) == PROXY


@pytest.mark.parametrize("bad", ["", "no-es-una-ip", "1.2.3.4, 5.6.7.8", "999.1.1.1", "1.2.3.4:80"])
def test_trusted_peer_with_missing_or_invalid_x_real_ip_falls_back_to_peer(trusted, bad):
    from app.core.client_ip import get_client_ip

    trusted(PROXY)
    headers = {"X-Real-IP": bad} if bad else {}
    assert get_client_ip(_request(PROXY, headers)) == PROXY


def test_x_forwarded_for_is_never_used(trusted):
    from app.core.client_ip import get_client_ip

    trusted(PROXY)
    assert get_client_ip(_request(PROXY, {"X-Forwarded-For": "8.8.8.8"})) == PROXY


def test_ipv6_is_normalized(trusted):
    from app.core.client_ip import get_client_ip

    trusted(PROXY)
    request = _request(PROXY, {"X-Real-IP": "2001:0DB8:0000:0000:0000:0000:0000:0001"})
    assert get_client_ip(request) == "2001:db8::1"


def test_request_without_client_is_unknown(trusted):
    from app.core.client_ip import get_client_ip

    trusted("")
    assert get_client_ip(_request(None)) == "unknown"
