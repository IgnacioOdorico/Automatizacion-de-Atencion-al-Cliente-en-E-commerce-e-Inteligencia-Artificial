from datetime import datetime, timedelta, timezone

import pytest

import helpers_n8n
from app.db import execute

pytestmark = pytest.mark.integration

ORDER_STATUSES = [
    "pending",
    "processing",
    "confirmed",
    "shipped",
    "delivered",
    "no_stock",
    "cancelled",
    "error",
]


def get_summary(client, headers, **params):
    resp = client.get("/monitoring/summary", params=params, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_summary_requires_jwt(client):
    assert client.get("/monitoring/summary").status_code == 401


def test_summary_counts_the_last_24_hours(client, auth_headers, no_n8n_tables):
    body = get_summary(client, auth_headers)
    assert body["window_hours"] == 24
    assert body["generated_at"].endswith("Z")
    assert body["data_source"] == "all"

    assert body["bot"]["interactions"] == 2
    assert body["bot"]["avg_tmr_seconds"] == pytest.approx(80.0)
    assert body["bot"]["urgent"] == 0
    assert body["bot"]["by_intent"] == {
        "FAQ": 1,
        "ESTADO_PEDIDO": 1,
        "RECLAMO": 0,
        "GENERAL": 0,
    }
    assert body["bot"]["by_channel"] == {"whatsapp": 1, "telegram": 0, "email": 1}

    assert body["orders"]["total"] == 2
    assert set(body["orders"]["by_status"]) == set(ORDER_STATUSES)
    assert body["orders"]["by_status"]["confirmed"] == 1
    assert body["orders"]["by_status"]["no_stock"] == 1
    assert body["orders"]["by_status"]["pending"] == 0

    assert body["tickets"]["created"] == 2
    assert body["tickets"]["open"] == 2
    assert body["tickets"]["by_priority"] == {
        "low": 0,
        "normal": 0,
        "high": 1,
        "urgent": 1,
    }
    assert body["stock_alerts"] == 0


def test_summary_window_is_configurable(client, auth_headers, no_n8n_tables):
    body = get_summary(client, auth_headers, hours=168)
    assert body["window_hours"] == 168
    assert body["orders"]["total"] == 3
    assert body["orders"]["by_status"]["pending"] == 1
    assert body["tickets"]["created"] == 3
    assert body["tickets"]["by_priority"]["normal"] == 1

    body = get_summary(client, auth_headers, hours=1)
    assert body["orders"]["total"] == 0
    assert body["bot"]["interactions"] == 0
    assert body["bot"]["avg_tmr_seconds"] is None


def test_summary_open_tickets_ignore_the_window(client, auth_headers, no_n8n_tables):
    execute("UPDATE tickets SET created_at = NOW() - INTERVAL '30 days' WHERE id = 3")
    body = get_summary(client, auth_headers)
    assert body["tickets"]["created"] == 1
    assert body["tickets"]["open"] == 2  # estado actual, no evento de la ventana


def test_summary_filters_by_data_source(client, auth_headers, no_n8n_tables):
    body = get_summary(client, auth_headers, hours=168, data_source="synthetic")
    assert body["data_source"] == "synthetic"
    assert body["orders"]["total"] == 1
    assert body["bot"]["interactions"] == 1
    assert body["bot"]["by_channel"]["email"] == 1
    assert body["tickets"]["created"] == 0


def test_summary_counts_urgent_replies_and_stock_alerts(client, auth_headers, no_n8n_tables):
    execute("UPDATE interactions SET is_urgent = TRUE WHERE id = 1")
    execute(
        "INSERT INTO stock_alerts (product_id, order_id, sku, stock_actual, stock_min) "
        "VALUES (1, 1, 'PROD-001', 2, 5)"
    )
    body = get_summary(client, auth_headers)
    assert body["bot"]["urgent"] == 1
    assert body["stock_alerts"] == 1


def test_summary_last_activity_matches_the_newest_feed_event(
    client, auth_headers, no_n8n_tables
):
    body = get_summary(client, auth_headers)
    newest = client.get(
        "/monitoring/events", params={"limit": 1}, headers=auth_headers
    ).json()["items"][0]
    assert body["last_activity_at"] == newest["ts"]


def test_summary_last_activity_is_null_without_data(client, auth_headers, no_n8n_tables):
    execute("TRUNCATE orders, tickets, interactions, stock_alerts RESTART IDENTITY CASCADE")
    body = get_summary(client, auth_headers)
    assert body["last_activity_at"] is None
    assert body["bot"]["interactions"] == 0
    assert body["orders"]["total"] == 0


@pytest.mark.parametrize("hours", [0, 169, -1])
def test_summary_rejects_hours_out_of_range(client, auth_headers, hours):
    resp = client.get("/monitoring/summary", params={"hours": hours}, headers=auth_headers)
    assert resp.status_code == 422


def test_summary_rejects_unknown_data_source(client, auth_headers):
    resp = client.get(
        "/monitoring/summary", params={"data_source": "otra"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_executions_degrade_when_n8n_tables_are_missing(client, auth_headers, no_n8n_tables):
    body = get_summary(client, auth_headers)
    assert body["executions"] == {
        "available": False,
        "total": 0,
        "success": 0,
        "error": 0,
        "last_error_at": None,
    }


def test_executions_summary_reads_the_n8n_tables(client, auth_headers, n8n_tables):
    now = datetime.now(timezone.utc)
    helpers_n8n.insert_workflow("wf-1", "Flujo 1", [], {})
    helpers_n8n.insert_execution("wf-1", status="success", started=now - timedelta(hours=1))
    helpers_n8n.insert_execution("wf-1", status="success", started=now - timedelta(hours=2))
    error_at = now - timedelta(minutes=30)
    helpers_n8n.insert_execution("wf-1", status="error", started=now - timedelta(hours=3))
    helpers_n8n.insert_execution("wf-1", status="crashed", started=error_at)
    helpers_n8n.insert_execution("wf-1", status="running", started=now - timedelta(minutes=1))
    # fuera de la ventana y borrada: no cuentan
    helpers_n8n.insert_execution("wf-1", status="error", started=now - timedelta(days=3))
    helpers_n8n.insert_execution(
        "wf-1", status="error", started=now - timedelta(hours=1), deleted=True
    )

    body = get_summary(client, auth_headers)
    assert body["executions"]["available"] is True
    assert body["executions"]["total"] == 5
    assert body["executions"]["success"] == 2
    assert body["executions"]["error"] == 2
    assert body["executions"]["last_error_at"] is not None
    assert body["executions"]["last_error_at"].endswith("Z")
