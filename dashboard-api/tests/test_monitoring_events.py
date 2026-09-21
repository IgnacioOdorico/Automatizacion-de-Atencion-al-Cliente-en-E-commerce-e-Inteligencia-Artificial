import pytest

from app.db import execute

pytestmark = pytest.mark.integration

TIE_TS = "2026-09-20 15:00:00+00"


def get_events(client, headers, **params):
    resp = client.get("/monitoring/events", params=params, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def by_id(events):
    return {event["id"]: event for event in events}


def insert_tied_orders(count: int, ts: str = TIE_TS) -> None:
    for n in range(count):
        execute(
            """
            INSERT INTO orders
                (order_number, customer_name, customer_email, product_id, quantity,
                 total_amount, status, received_at, data_source)
            VALUES (:num, 'Empate', 'empate@example.com', 1, 1, 10, 'pending',
                    CAST(:ts AS timestamptz), 'measured')
            """,
            {"num": f"ORD-TIE-{n:03d}", "ts": ts},
        )


def test_events_require_jwt(client):
    assert client.get("/monitoring/events").status_code == 401


def test_events_shape_and_descending_order(client, auth_headers):
    body = get_events(client, auth_headers, limit=100)
    events = body["items"]
    assert events, "el fixture tiene actividad"
    stamps = [event["ts"] for event in events]
    assert stamps == sorted(stamps, reverse=True)
    for event in events:
        assert event["ts"].endswith("Z")
        assert set(event) == {"id", "type", "ts", "channel", "severity", "data", "refs"}
        assert set(event["refs"]) == {
            "order_id",
            "order_number",
            "interaction_id",
            "ticket_id",
        }
        assert event["severity"] in {"info", "success", "warning", "error"}
        assert event["id"].startswith(event["type"] + ":")
    assert set(body) >= {"items", "has_more", "newest_cursor", "oldest_cursor"}
    ids = [event["id"] for event in events]
    assert len(ids) == len(set(ids))


def test_all_event_types_for_the_fixture(client, auth_headers):
    execute(
        """
        INSERT INTO stock_alerts (product_id, order_id, sku, stock_actual, stock_min)
        VALUES (1, 1, 'PROD-001', 2, 5)
        """
    )
    events = get_events(client, auth_headers, limit=100)["items"]
    types = {event["type"] for event in events}
    assert types == {
        "order_received",
        "order_processed",
        "order_notified",
        "chat_message",
        "bot_reply",
        "ticket_created",
        "stock_alert",
    }


def test_bot_reply_carries_exact_text_and_metrics(client, auth_headers):
    events = by_id(get_events(client, auth_headers, limit=100)["items"])
    reply = events["bot_reply:1"]
    assert reply["channel"] == "whatsapp"
    assert reply["severity"] == "success"
    assert reply["data"]["ai_response"] == "Está en camino."
    assert reply["data"]["intent"] == "ESTADO_PEDIDO"
    assert reply["data"]["is_urgent"] is False
    assert reply["data"]["tmr_seconds"] == pytest.approx(40.0)
    assert reply["refs"] == {
        "order_id": 1,
        "order_number": "ORD-FIX-001",
        "interaction_id": 1,
        "ticket_id": 1,
    }
    message = events["chat_message:1"]
    assert message["channel"] == "whatsapp"
    assert message["data"]["message"] == "¿Dónde está mi pedido?"
    assert message["data"]["user_id"] == "5492614000001"
    assert message["severity"] == "info"


def test_bot_reply_without_response_time_creates_no_reply_event(client, auth_headers):
    execute(
        """
        INSERT INTO interactions (channel, user_id, message, intent, ai_response,
                                  received_at, responded_at)
        VALUES ('telegram', '458721336', 'Hola?', 'GENERAL', 'Hola', NOW(), NULL)
        """
    )
    events = by_id(get_events(client, auth_headers, limit=100)["items"])
    assert "chat_message:3" in events
    assert "bot_reply:3" not in events


def test_urgent_reply_is_a_warning(client, auth_headers):
    execute(
        """
        INSERT INTO interactions (channel, user_id, message, intent, ai_response,
                                  is_urgent, received_at, responded_at)
        VALUES ('telegram', '458721336', 'Me estafaron', 'RECLAMO', 'Lo escalamos',
                TRUE, NOW(), NOW() + INTERVAL '3 seconds')
        """
    )
    events = by_id(get_events(client, auth_headers, limit=100)["items"])
    reply = events["bot_reply:3"]
    assert reply["severity"] == "warning"
    assert reply["data"]["is_urgent"] is True


def test_order_event_severities_and_data(client, auth_headers):
    events = by_id(get_events(client, auth_headers, limit=100)["items"])
    assert events["order_received:1"]["severity"] == "info"
    received = events["order_received:1"]
    assert received["channel"] is None
    assert received["data"]["order_number"] == "ORD-FIX-001"
    assert received["data"]["product_sku"] == "PROD-001"
    assert received["refs"]["order_id"] == 1
    assert received["refs"]["order_number"] == "ORD-FIX-001"

    assert events["order_processed:1"]["severity"] == "success"
    assert events["order_processed:1"]["data"]["status"] == "confirmed"
    assert events["order_processed:1"]["data"]["mttd_seconds"] == pytest.approx(60.0)
    assert events["order_notified:1"]["severity"] == "success"
    assert events["order_notified:1"]["data"]["mttr_seconds"] == pytest.approx(30.0)

    assert events["order_processed:2"]["severity"] == "warning"
    assert events["order_processed:2"]["data"]["status"] == "no_stock"
    assert events["order_notified:2"]["severity"] == "warning"
    assert "order_processed:3" not in events
    assert "order_notified:3" not in events


def test_error_orders_are_errors(client, auth_headers):
    execute("UPDATE orders SET status = 'error' WHERE id = 1")
    events = by_id(get_events(client, auth_headers, limit=100)["items"])
    assert events["order_processed:1"]["severity"] == "error"


def test_ticket_and_stock_alert_events(client, auth_headers):
    execute(
        """
        INSERT INTO stock_alerts (product_id, order_id, sku, stock_actual, stock_min)
        VALUES (1, 1, 'PROD-001', 2, 5), (5, NULL, 'PROD-005', 0, 5)
        """
    )
    events = by_id(get_events(client, auth_headers, limit=100)["items"])
    assert events["ticket_created:1"]["severity"] == "warning"  # high
    assert events["ticket_created:1"]["data"]["subject"] == "Pedido demorado"
    assert events["ticket_created:1"]["data"]["priority"] == "high"
    assert events["ticket_created:1"]["channel"] == "whatsapp"
    assert events["ticket_created:1"]["refs"]["interaction_id"] == 1
    assert events["ticket_created:1"]["refs"]["order_number"] == "ORD-FIX-001"
    assert events["ticket_created:3"]["severity"] == "error"  # urgent
    assert events["ticket_created:2"]["severity"] == "info"  # normal

    alert = events["stock_alert:1"]
    assert alert["severity"] == "warning"
    assert alert["data"]["sku"] == "PROD-001"
    assert alert["data"]["stock_actual"] == 2
    assert alert["data"]["stock_min"] == 5
    assert alert["refs"]["order_number"] == "ORD-FIX-001"
    assert events["stock_alert:2"]["severity"] == "error"  # stock agotado
    assert events["stock_alert:2"]["refs"]["order_id"] is None


def test_paging_with_tied_timestamps_has_no_duplicates_or_gaps(client, auth_headers):
    insert_tied_orders(7)
    everything = get_events(client, auth_headers, limit=100)["items"]
    expected = [event["id"] for event in everything]

    seen: list[str] = []
    cursor = None
    for _ in range(50):
        params = {"limit": 3}
        if cursor:
            params["before"] = cursor
        page = get_events(client, auth_headers, **params)
        seen.extend(event["id"] for event in page["items"])
        if not page["has_more"]:
            assert page["items"], "la última página no puede estar vacía"
            break
        cursor = page["oldest_cursor"]
    else:
        pytest.fail("la paginación no terminó")

    assert seen == expected
    assert len(seen) == len(set(seen))
    tied = [event for event in everything if event["ts"].startswith("2026-09-20T15:00:00")]
    assert len(tied) == 7


def test_oldest_page_reports_no_more(client, auth_headers):
    total = len(get_events(client, auth_headers, limit=100)["items"])
    page = get_events(client, auth_headers, limit=total)
    assert page["has_more"] is False
    page = get_events(client, auth_headers, limit=total - 1)
    assert page["has_more"] is True


def test_since_returns_only_newer_events_and_keeps_cursor_when_idle(client, auth_headers):
    first = get_events(client, auth_headers, limit=100)
    cursor = first["newest_cursor"]
    assert cursor

    idle = get_events(client, auth_headers, since=cursor)
    assert idle["items"] == []
    assert idle["has_more"] is False
    assert idle["newest_cursor"] == cursor

    execute(
        """
        INSERT INTO orders
            (order_number, customer_name, customer_email, product_id, quantity,
             total_amount, status, received_at, processed_at, notified_at)
        VALUES ('ORD-NEW-001', 'Nueva', 'n@example.com', 1, 1, 10, 'confirmed',
                NOW() + INTERVAL '1 minute', NOW() + INTERVAL '2 minutes',
                NOW() + INTERVAL '3 minutes')
        """
    )
    fresh = get_events(client, auth_headers, since=cursor)
    assert [event["type"] for event in fresh["items"]] == [
        "order_notified",
        "order_processed",
        "order_received",
    ]
    assert fresh["newest_cursor"] != cursor


def test_since_never_skips_events_when_there_are_more_than_the_limit(client, auth_headers):
    cursor = get_events(client, auth_headers, limit=1)["newest_cursor"]
    for n in range(5):
        execute(
            """
            INSERT INTO orders
                (order_number, customer_name, customer_email, product_id, quantity,
                 total_amount, status, received_at)
            VALUES (:num, 'Poll', 'p@example.com', 1, 1, 10, 'pending',
                    NOW() + (:n * INTERVAL '1 minute'))
            """,
            {"num": f"ORD-POLL-{n}", "n": n + 1},
        )
    collected: list[str] = []
    for _ in range(10):
        page = get_events(client, auth_headers, since=cursor, limit=2)
        collected.extend(reversed([event["id"] for event in page["items"]]))
        cursor = page["newest_cursor"]
        if not page["has_more"]:
            break
    else:
        pytest.fail("el polling no terminó")
    assert len(collected) == 5
    assert len(set(collected)) == 5
    numbers = get_events(client, auth_headers, limit=5)["items"]
    assert collected == [event["id"] for event in reversed(numbers)]


def test_filter_by_types(client, auth_headers):
    body = get_events(client, auth_headers, types="bot_reply,chat_message", limit=100)
    assert {event["type"] for event in body["items"]} == {"bot_reply", "chat_message"}


def test_filter_by_channel_only_returns_chat_related_events(client, auth_headers):
    body = get_events(client, auth_headers, channel="telegram", limit=100)
    assert {event["type"] for event in body["items"]} == {"ticket_created"}
    assert all(event["channel"] == "telegram" for event in body["items"])
    body = get_events(client, auth_headers, channel="whatsapp", limit=100)
    assert {event["type"] for event in body["items"]} == {
        "chat_message",
        "bot_reply",
        "ticket_created",
    }


def test_filter_by_data_source(client, auth_headers):
    body = get_events(client, auth_headers, data_source="synthetic", limit=100)
    ids = {event["id"] for event in body["items"]}
    assert "order_received:3" in ids
    assert "chat_message:2" in ids
    assert "order_received:1" not in ids
    assert "ticket_created:1" not in ids


@pytest.mark.parametrize(
    "params",
    [
        {"types": "no_existe"},
        {"channel": "sms"},
        {"data_source": "otra"},
        {"limit": 0},
        {"limit": 101},
        {"before": "basura"},
        {"since": "basura"},
    ],
)
def test_invalid_parameters_are_rejected(client, auth_headers, params):
    resp = client.get("/monitoring/events", params=params, headers=auth_headers)
    assert resp.status_code == 422, resp.text


def test_before_and_since_cannot_be_combined(client, auth_headers):
    cursor = get_events(client, auth_headers, limit=1)["newest_cursor"]
    resp = client.get(
        "/monitoring/events",
        params={"before": cursor, "since": cursor},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "before" in resp.json()["detail"]


def test_cursor_of_another_kind_is_rejected(client, auth_headers):
    from datetime import datetime, timezone

    from app.core.cursors import encode_cursor

    other = encode_cursor("conv", datetime(2026, 9, 21, tzinfo=timezone.utc), "whatsapp", "x")
    resp = client.get("/monitoring/events", params={"before": other}, headers=auth_headers)
    assert resp.status_code == 422
