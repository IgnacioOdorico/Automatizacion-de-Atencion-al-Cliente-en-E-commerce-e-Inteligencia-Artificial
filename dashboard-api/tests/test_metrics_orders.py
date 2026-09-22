from app.db import execute

import pytest

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


def get_metrics(client, headers, **params):
    resp = client.get("/metrics/orders", params=params, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_metrics_orders_requires_jwt(client):
    assert client.get("/metrics/orders").status_code == 401


def test_metrics_orders_without_hours_is_full_history(client, auth_headers, db_ready):
    body = get_metrics(client, auth_headers)
    assert body["window_hours"] is None
    assert body["generated_at"].endswith("Z")
    assert body["total_orders"] == 3
    assert set(body["by_status"]) == set(ORDER_STATUSES)
    assert body["by_status"]["confirmed"] == 1
    assert body["by_status"]["no_stock"] == 1
    assert body["by_status"]["pending"] == 1
    # ORD-FIX-001: mttd=60s, mttr=30s, e2e=90s · ORD-FIX-002: mttd=10s, mttr=10s, e2e=20s
    assert body["avg_mttd_seconds"] == pytest.approx(35.0)
    assert body["avg_mttr_seconds"] == pytest.approx(20.0)
    assert body["avg_end_to_end_seconds"] == pytest.approx(55.0)


def test_metrics_orders_window_is_configurable(client, auth_headers, db_ready):
    body = get_metrics(client, auth_headers, hours=1)
    assert body["window_hours"] == 1
    assert body["total_orders"] == 0
    assert body["avg_mttd_seconds"] is None
    assert body["avg_mttr_seconds"] is None
    assert body["avg_end_to_end_seconds"] is None
    assert all(v == 0 for v in body["by_status"].values())

    body = get_metrics(client, auth_headers, hours=168)
    assert body["total_orders"] == 3


def test_metrics_orders_with_only_received_at_yields_nulls_not_zero(
    client, auth_headers, db_ready
):
    # ORD-FIX-003 solo tiene received_at (processed_at/notified_at NULL);
    # sigue contando en total_orders y by_status, pero no debe romper los promedios.
    body = get_metrics(client, auth_headers, hours=168)
    assert body["total_orders"] == 3
    assert body["avg_mttd_seconds"] is not None  # las otras 2 sí tienen processed_at


def test_metrics_orders_no_data_yields_nulls_and_zeros_never_error(
    client, auth_headers, db_ready
):
    execute("TRUNCATE orders, order_items, tickets, interactions RESTART IDENTITY CASCADE")
    body = get_metrics(client, auth_headers)
    assert body["total_orders"] == 0
    assert body["avg_mttd_seconds"] is None
    assert body["avg_mttr_seconds"] is None
    assert body["avg_end_to_end_seconds"] is None
    assert all(v == 0 for v in body["by_status"].values())
    # "sin huecos": la serie diaria sigue cubriendo la ventana (acotada, sin `hours`),
    # solo que cada día queda en 0 — nunca una lista vacía.
    assert len(body["daily"]) > 0
    assert all(
        row["total_orders"] == 0 and row["confirmed"] == 0 for row in body["daily"]
    )


def test_metrics_orders_filters_by_data_source(client, auth_headers, db_ready):
    body = get_metrics(client, auth_headers, hours=168, data_source="synthetic")
    assert body["total_orders"] == 1
    assert body["by_status"]["pending"] == 1

    body = get_metrics(client, auth_headers, hours=168, data_source="measured")
    assert body["total_orders"] == 2


def test_metrics_orders_daily_series_has_no_gaps(client, auth_headers, db_ready):
    body = get_metrics(client, auth_headers, hours=168)
    dates = [row["date"] for row in body["daily"]]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))
    # 168hs = 7 días -> serie continua día a día, sin huecos aunque algún día no tenga datos
    assert len(dates) == 8  # incluye el día de hoy (UTC) y los 7 anteriores
    for row in body["daily"]:
        assert set(row) == {
            "date",
            "total_orders",
            "confirmed",
            "shipped",
            "delivered",
            "no_stock",
            "cancelled",
            "error",
        }


def test_metrics_orders_daily_series_is_capped_without_hours(client, auth_headers, db_ready):
    body = get_metrics(client, auth_headers)
    assert body["window_hours"] is None
    assert len(body["daily"]) <= 91  # tope documentado (~90 días) + día actual


@pytest.mark.parametrize("hours", [0, 8761, -1])
def test_metrics_orders_rejects_hours_out_of_range(client, auth_headers, hours):
    resp = client.get("/metrics/orders", params={"hours": hours}, headers=auth_headers)
    assert resp.status_code == 422


def test_metrics_orders_rejects_unknown_data_source(client, auth_headers):
    resp = client.get(
        "/metrics/orders", params={"data_source": "otra"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_metrics_orders_accepts_e4_manual_data_source(client, auth_headers, db_ready):
    execute(
        "UPDATE orders SET data_source = 'e4_manual' WHERE id = 3"
    )
    body = get_metrics(client, auth_headers, hours=168, data_source="e4_manual")
    assert body["total_orders"] == 1
