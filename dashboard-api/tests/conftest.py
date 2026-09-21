import os
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

# La API es fail-closed: rechaza secretos vacíos, cortos o de ejemplo (core/config.py).
# Estos son valores de prueba (>= 32 caracteres, distintos entre sí), no de ningún entorno real.
TEST_JWT_SECRET = "pytest-jwt-signing-secret-7Qm2Zx9LkP4vB8nR1sT6"
TEST_N8N_SECRET = "pytest-n8n-shared-secret-3Hc5Yw0DfJ9aE7uG2bK8"

os.environ["DASHBOARD_ENC_KEY"] = os.environ.get(
    "DASHBOARD_ENC_KEY", Fernet.generate_key().decode()
)
os.environ["DASHBOARD_JWT_SECRET"] = os.environ.get(
    "DASHBOARD_JWT_SECRET", TEST_JWT_SECRET
)
os.environ["DASHBOARD_N8N_SECRET"] = os.environ.get(
    "DASHBOARD_N8N_SECRET", TEST_N8N_SECRET
)
os.environ["DATABASE_URL"] = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://n8n_user:n8n_pass@localhost:5433/ecommerce_tesis_test",
)
os.environ["CORS_ORIGINS"] = os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
)
os.environ["DASHBOARD_GOOGLE_CLIENT_ID"] = os.environ.get(
    "DASHBOARD_GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com"
)
os.environ["DASHBOARD_GOOGLE_CLIENT_SECRET"] = os.environ.get(
    "DASHBOARD_GOOGLE_CLIENT_SECRET", "test-client-secret"
)
os.environ["DASHBOARD_GOOGLE_REDIRECT_URI"] = os.environ.get(
    "DASHBOARD_GOOGLE_REDIRECT_URI",
    "http://localhost:8000/connections/gmail/callback",
)
os.environ["DASHBOARD_FRONTEND_URL"] = os.environ.get(
    "DASHBOARD_FRONTEND_URL", "http://localhost:5173"
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEMO_EMAIL = "ventas@tecnoshopmza.com.ar"
DEMO_PASSWORD = "Demo2026!"
DEMO_HASH = "$2b$12$gFkzp0IobEcDZSP0zYjW/OfQtaF2tqxGTA6JgSXT3Ak476cnPt/M."

TRUNCATE_SQL = (
    "TRUNCATE orders, order_items, tickets, interactions, stock_alerts, "
    "channel_connections, client_accounts RESTART IDENTITY CASCADE"
)

FIXTURE_SQL = [
    """
    INSERT INTO client_accounts (business_name, email, password_hash)
    VALUES ('TecnoShop Mendoza SRL', :email, :password_hash)
    """,
    """
    INSERT INTO channel_connections
        (client_account_id, channel, status, external_reference, connected_at)
    VALUES
        (1, 'whatsapp', 'connected', '5492615550102', NOW() - INTERVAL '3 days'),
        (1, 'telegram', 'connected', '458721336', NOW() - INTERVAL '2 days'),
        (1, 'email', 'disconnected', NULL, NULL)
    """,
    """
    INSERT INTO orders
        (order_number, customer_name, customer_email, customer_phone, product_id,
         quantity, total_amount, status, received_at, processed_at, notified_at,
         raw_payload, data_source)
    VALUES
        ('ORD-FIX-001', 'Juana Pérez', 'juana@example.com', '5492614000001', 1,
         1, 599.99, 'confirmed',
         NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours' + INTERVAL '60 seconds',
         NOW() - INTERVAL '2 hours' + INTERVAL '90 seconds',
         '{"order_number": "ORD-FIX-001", "origin": "webhook"}'::jsonb, 'measured'),
        ('ORD-FIX-002', 'Marcos Díaz', 'marcos@example.com', '5492614000002', 5,
         99, 34649.01, 'no_stock',
         NOW() - INTERVAL '5 hours', NOW() - INTERVAL '5 hours' + INTERVAL '10 seconds',
         NOW() - INTERVAL '5 hours' + INTERVAL '20 seconds',
         '{"order_number": "ORD-FIX-002"}'::jsonb, 'measured'),
        ('ORD-FIX-003', 'Lucía Gómez', 'lucia@example.com', NULL, 2,
         2, 59.98, 'pending',
         NOW() - INTERVAL '3 days', NULL, NULL, NULL, 'synthetic')
    """,
    """
    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
    VALUES (1, 1, 1, 599.99), (2, 5, 99, 349.99)
    """,
    """
    INSERT INTO interactions
        (channel, user_id, message, intent, ai_response, order_id, is_urgent,
         received_at, responded_at, data_source)
    VALUES
        ('whatsapp', '5492614000001', '¿Dónde está mi pedido?', 'ESTADO_PEDIDO',
         'Está en camino.', 1, FALSE,
         NOW() - INTERVAL '90 minutes', NOW() - INTERVAL '90 minutes' + INTERVAL '40 seconds',
         'measured'),
        ('email', 'cliente@example.com', 'Quiero una factura', 'FAQ',
         'La emitimos al confirmar.', NULL, FALSE,
         NOW() - INTERVAL '4 hours', NOW() - INTERVAL '4 hours' + INTERVAL '2 minutes',
         'synthetic')
    """,
    """
    INSERT INTO tickets
        (interaction_id, order_id, channel, user_id, subject, status, priority,
         created_at, resolved_at, data_source)
    VALUES
        (1, 1, 'whatsapp', '5492614000001', 'Pedido demorado', 'open', 'high',
         NOW() - INTERVAL '80 minutes', NULL, 'measured'),
        (NULL, NULL, 'email', 'cliente@example.com', 'Devolución de producto', 'resolved',
         'normal', NOW() - INTERVAL '2 days', NULL, 'measured'),
        (NULL, 2, 'telegram', '458721336', 'Reclamo por falta de stock', 'in_progress',
         'urgent', NOW() - INTERVAL '3 hours', NULL, 'measured')
    """,
]


@pytest.fixture(autouse=True)
def _skip_integration_without_db(request):
    if request.node.get_closest_marker("integration"):
        from app.db import ping

        if not ping():
            pytest.skip("PostgreSQL no disponible en DATABASE_URL")


@pytest.fixture
def db_ready():
    from app.core import rate_limit, telegram_codes
    from app.db import execute

    execute(TRUNCATE_SQL)
    execute(FIXTURE_SQL[0], {"email": DEMO_EMAIL, "password_hash": DEMO_HASH})
    for statement in FIXTURE_SQL[1:]:
        execute(statement)
    rate_limit.reset()
    telegram_codes.reset()
    return True


@pytest.fixture(autouse=True)
def _clean_db(request):
    if request.node.get_closest_marker("integration"):
        request.getfixturevalue("db_ready")


@pytest.fixture(scope="session")
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client, db_ready):
    resp = client.post(
        "/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}