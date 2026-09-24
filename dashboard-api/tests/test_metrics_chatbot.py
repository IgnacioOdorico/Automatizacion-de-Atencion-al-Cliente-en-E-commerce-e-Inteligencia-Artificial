import pytest

from app.db import execute

pytestmark = pytest.mark.integration

INTENTS = ["FAQ", "ESTADO_PEDIDO", "RECLAMO", "GENERAL"]


def get_metrics(client, headers, **params):
    resp = client.get("/metrics/chatbot", params=params, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_metrics_chatbot_requires_jwt(client):
    assert client.get("/metrics/chatbot").status_code == 401


def test_metrics_chatbot_without_hours_is_full_history(client, auth_headers, db_ready):
    body = get_metrics(client, auth_headers)
    assert body["window_hours"] is None
    assert body["generated_at"].endswith("Z")
    assert body["total_interactions"] == 2
    # ESTADO_PEDIDO: 40s · FAQ: 120s -> avg = 80.0
    assert body["avg_tmr_seconds"] == pytest.approx(80.0)
    assert set(body["by_intent"]) == set(INTENTS)
    assert body["by_intent"]["ESTADO_PEDIDO"]["count"] == 1
    assert body["by_intent"]["ESTADO_PEDIDO"]["avg_tmr_seconds"] == pytest.approx(40.0)
    assert body["by_intent"]["FAQ"]["count"] == 1
    assert body["by_intent"]["FAQ"]["avg_tmr_seconds"] == pytest.approx(120.0)
    assert body["by_intent"]["RECLAMO"]["count"] == 0
    assert body["by_intent"]["RECLAMO"]["avg_tmr_seconds"] is None
    assert body["by_intent"]["GENERAL"]["count"] == 0


def test_metrics_chatbot_window_is_configurable(client, auth_headers, db_ready):
    body = get_metrics(client, auth_headers, hours=1)
    assert body["total_interactions"] == 0
    assert body["avg_tmr_seconds"] is None
    for intent in INTENTS:
        assert body["by_intent"][intent]["count"] == 0
        assert body["by_intent"][intent]["avg_tmr_seconds"] is None

    body = get_metrics(client, auth_headers, hours=168)
    assert body["total_interactions"] == 2


def test_metrics_chatbot_counts_unanswered_but_excludes_from_tmr(
    client, auth_headers, db_ready
):
    execute("UPDATE interactions SET responded_at = NULL WHERE id = 1")
    body = get_metrics(client, auth_headers)
    assert body["total_interactions"] == 2  # cuenta todas, respondidas o no
    assert body["by_intent"]["ESTADO_PEDIDO"]["count"] == 1
    assert body["by_intent"]["ESTADO_PEDIDO"]["avg_tmr_seconds"] is None
    assert body["avg_tmr_seconds"] == pytest.approx(120.0)  # solo la FAQ respondida


def test_metrics_chatbot_no_data_yields_nulls_and_zeros_never_error(
    client, auth_headers, db_ready
):
    execute("TRUNCATE orders, order_items, tickets, interactions RESTART IDENTITY CASCADE")
    body = get_metrics(client, auth_headers)
    assert body["total_interactions"] == 0
    assert body["avg_tmr_seconds"] is None
    for intent in INTENTS:
        assert body["by_intent"][intent] == {"count": 0, "avg_tmr_seconds": None}
    # "sin huecos": la serie sigue cubriendo la ventana acotada, en 0 — nunca vacía.
    assert len(body["by_channel_daily"]) > 0
    assert all(
        row["whatsapp"] == 0 and row["telegram"] == 0 and row["email"] == 0
        for row in body["by_channel_daily"]
    )


def test_metrics_chatbot_filters_by_data_source(client, auth_headers, db_ready):
    body = get_metrics(client, auth_headers, hours=168, data_source="synthetic")
    assert body["total_interactions"] == 1
    assert body["by_intent"]["FAQ"]["count"] == 1

    body = get_metrics(client, auth_headers, hours=168, data_source="measured")
    assert body["total_interactions"] == 1
    assert body["by_intent"]["ESTADO_PEDIDO"]["count"] == 1


def test_metrics_chatbot_by_channel_daily_has_no_gaps(client, auth_headers, db_ready):
    body = get_metrics(client, auth_headers, hours=168)
    dates = [row["date"] for row in body["by_channel_daily"]]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))
    assert len(dates) == 8
    for row in body["by_channel_daily"]:
        assert set(row) == {"date", "whatsapp", "telegram", "email"}
    totals = {"whatsapp": 0, "telegram": 0, "email": 0}
    for row in body["by_channel_daily"]:
        for channel in totals:
            totals[channel] += row[channel]
    assert totals == {"whatsapp": 1, "telegram": 0, "email": 1}


@pytest.mark.parametrize("hours", [0, 8761, -1])
def test_metrics_chatbot_rejects_hours_out_of_range(client, auth_headers, hours):
    resp = client.get("/metrics/chatbot", params={"hours": hours}, headers=auth_headers)
    assert resp.status_code == 422


def test_metrics_chatbot_rejects_unknown_data_source(client, auth_headers):
    resp = client.get(
        "/metrics/chatbot", params={"data_source": "otra"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_metrics_chatbot_rejects_e4_manual_data_source(client, auth_headers):
    # e4_manual es válido para `orders`, pero interactions solo admite measured/synthetic
    # (init_simple.sql:113-114): a diferencia de /metrics/orders, acá se rechaza.
    resp = client.get(
        "/metrics/chatbot", params={"data_source": "e4_manual"}, headers=auth_headers
    )
    assert resp.status_code == 422
