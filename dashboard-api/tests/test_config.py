def test_settings_read_from_env():
    from app.core.config import settings

    assert settings.database_url.endswith("/ecommerce_tesis_test")
    assert settings.dashboard_jwt_secret == "test-jwt-secret"
    assert settings.dashboard_n8n_secret == "test-n8n-secret"
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