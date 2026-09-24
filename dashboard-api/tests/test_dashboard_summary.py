import pytest

pytestmark = pytest.mark.integration

METRIC_KEYS = [
    "total_orders",
    "orders_confirmed",
    "avg_mttd_seg",
    "avg_mttr_seg",
    "total_interactions",
    "avg_tmr_seg",
    "total_tickets",
    "tickets_resolved",
]

METRIC_KEYS_SELECT = f"SELECT {', '.join(METRIC_KEYS)} FROM v_metrics_summary"

MEASURED_SQL = """
SELECT
    (SELECT COUNT(*) FROM orders WHERE data_source = 'measured') AS total_orders,
    (SELECT COUNT(*) FROM orders
     WHERE status = 'confirmed' AND data_source = 'measured') AS orders_confirmed,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::NUMERIC, 2)
     FROM orders WHERE processed_at IS NOT NULL AND data_source = 'measured') AS avg_mttd_seg,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (notified_at - processed_at)))::NUMERIC, 2)
     FROM orders WHERE notified_at IS NOT NULL AND data_source = 'measured') AS avg_mttr_seg,
    (SELECT COUNT(*) FROM interactions WHERE data_source = 'measured') AS total_interactions,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))::NUMERIC, 2)
     FROM interactions WHERE responded_at IS NOT NULL AND data_source = 'measured') AS avg_tmr_seg,
    (SELECT COUNT(*) FROM tickets WHERE data_source = 'measured') AS total_tickets,
    (SELECT COUNT(*) FROM tickets
     WHERE status = 'resolved' AND data_source = 'measured') AS tickets_resolved
"""


def test_summary_requires_jwt(client):
    assert client.get("/dashboard/summary").status_code == 401


def test_summary_matches_view(client, auth_headers):
    from app.db import fetch_one

    resp = client.get("/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    view = fetch_one(METRIC_KEYS_SELECT)
    for key in METRIC_KEYS:
        assert key in body
        expected = view[key]
        expected = 0 if expected is None else float(expected)
        assert float(body[key]) == expected, key

    today = fetch_one(
        "SELECT COUNT(*) AS c FROM orders WHERE received_at >= date_trunc('day', now())"
    )
    open_tickets = fetch_one(
        "SELECT COUNT(*) AS c FROM tickets WHERE status IN ('open', 'in_progress')"
    )
    assert body["orders_today"] == today["c"]
    assert body["tickets_open"] == open_tickets["c"]


def test_summary_measured_filter_is_honest(client, auth_headers):
    from app.db import fetch_one

    resp = client.get(
        "/dashboard/summary?data_source=measured", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()

    expected = fetch_one(MEASURED_SQL)
    for key in METRIC_KEYS:
        value = expected[key]
        value = 0 if value is None else float(value)
        assert float(body[key]) == value, key

    measured_today = fetch_one(
        "SELECT COUNT(*) AS c FROM orders WHERE received_at >= date_trunc('day', now()) "
        "AND data_source = 'measured'"
    )
    assert body["orders_today"] == measured_today["c"]


def test_summary_without_data_returns_zeros(client, auth_headers):
    from app.db import execute

    execute("TRUNCATE orders, interactions, tickets RESTART IDENTITY CASCADE")
    resp = client.get("/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_orders"] == 0
    assert body["avg_mttd_seg"] == 0
    assert body["avg_tmr_seg"] == 0
    assert body["orders_today"] == 0
    assert body["tickets_open"] == 0