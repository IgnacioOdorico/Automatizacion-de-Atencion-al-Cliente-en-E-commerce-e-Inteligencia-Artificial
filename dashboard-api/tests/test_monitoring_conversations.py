import pytest

from app.db import execute

pytestmark = pytest.mark.integration

WA_USER = "5492614000001"
TIE_TS = "2026-09-20 15:00:00+00"


def add_interaction(
    channel="whatsapp",
    user_id=WA_USER,
    message="Hola",
    intent="GENERAL",
    ai_response="Hola!",
    received="NOW()",
    responded="NOW() + INTERVAL '2 seconds'",
    urgent=False,
    order_id=None,
    data_source="measured",
):
    execute(
        f"""
        INSERT INTO interactions
            (channel, user_id, message, intent, ai_response, order_id, is_urgent,
             received_at, responded_at, data_source)
        VALUES (:channel, :user_id, :message, :intent, :ai_response, :order_id, :urgent,
                {received}, {responded}, :data_source)
        """,
        {
            "channel": channel,
            "user_id": user_id,
            "message": message,
            "intent": intent,
            "ai_response": ai_response,
            "order_id": order_id,
            "urgent": urgent,
            "data_source": data_source,
        },
    )


def list_threads(client, headers, **params):
    resp = client.get("/monitoring/conversations", params=params, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def get_thread(client, headers, channel=None, user_id=None, **params):
    query = {"channel": channel, "user_id": user_id, **params}
    return client.get(
        "/monitoring/conversations/thread",
        params={k: v for k, v in query.items() if v is not None},
        headers=headers,
    )


# --------------------------------------------------------------------- lista


def test_conversations_require_jwt(client):
    assert client.get("/monitoring/conversations").status_code == 401
    assert client.get("/monitoring/conversations/thread").status_code == 401


def test_list_groups_by_channel_and_user_newest_first(client, auth_headers):
    body = list_threads(client, auth_headers)
    assert [(t["channel"], t["user_id"]) for t in body["items"]] == [
        ("whatsapp", WA_USER),
        ("email", "cliente@example.com"),
    ]
    assert body["has_more"] is False
    assert body["next_before"] is None

    first = body["items"][0]
    assert set(first) == {
        "channel",
        "user_id",
        "last_at",
        "messages",
        "last_intent",
        "last_message_preview",
        "has_urgent",
        "open_tickets",
    }
    assert first["last_at"].endswith("Z")
    assert first["messages"] == 1
    assert first["last_intent"] == "ESTADO_PEDIDO"
    assert first["last_message_preview"] == "¿Dónde está mi pedido?"
    assert first["has_urgent"] is False
    assert first["open_tickets"] == 1  # ticket 1 (whatsapp, open)
    assert body["items"][1]["open_tickets"] == 0  # su ticket está resuelto


def test_list_aggregates_a_thread_with_many_messages(client, auth_headers):
    add_interaction(
        message="M" * 300,
        intent="RECLAMO",
        urgent=True,
        received="NOW() + INTERVAL '1 minute'",
        responded="NOW() + INTERVAL '70 seconds'",
    )
    add_interaction(
        message="Último mensaje",
        intent="FAQ",
        received="NOW() + INTERVAL '2 minutes'",
        responded="NOW() + INTERVAL '121 seconds'",
    )
    thread = list_threads(client, auth_headers)["items"][0]
    assert thread["messages"] == 3
    assert thread["last_intent"] == "FAQ"
    assert thread["last_message_preview"] == "Último mensaje"
    assert thread["has_urgent"] is True

    add_interaction(
        message="M" * 300,
        received="NOW() + INTERVAL '3 minutes'",
        responded="NOW() + INTERVAL '181 seconds'",
    )
    preview = list_threads(client, auth_headers)["items"][0]["last_message_preview"]
    assert len(preview) == 120
    assert preview.endswith("…")


def test_list_channel_filter(client, auth_headers):
    body = list_threads(client, auth_headers, channel="email")
    assert [t["channel"] for t in body["items"]] == ["email"]
    assert list_threads(client, auth_headers, channel="telegram")["items"] == []


def test_list_search_matches_message_reply_and_user(client, auth_headers):
    by_message = list_threads(client, auth_headers, q="pedido")
    assert [t["user_id"] for t in by_message["items"]] == [WA_USER]
    by_reply = list_threads(client, auth_headers, q="EMITIMOS")
    assert [t["channel"] for t in by_reply["items"]] == ["email"]
    by_user = list_threads(client, auth_headers, q="cliente@")
    assert [t["channel"] for t in by_user["items"]] == ["email"]
    assert list_threads(client, auth_headers, q="no-existe-xyz")["items"] == []


def test_list_search_treats_wildcards_literally(client, auth_headers):
    add_interaction(user_id="5492614000009", message="Descuento del 50% hoy")
    assert [t["user_id"] for t in list_threads(client, auth_headers, q="50%")["items"]] == [
        "5492614000009"
    ]
    assert list_threads(client, auth_headers, q="%")["items"][0]["user_id"] == "5492614000009"
    assert len(list_threads(client, auth_headers, q="%")["items"]) == 1
    assert list_threads(client, auth_headers, q="_")["items"] == []


def test_list_data_source_filter(client, auth_headers):
    body = list_threads(client, auth_headers, data_source="synthetic")
    assert [t["channel"] for t in body["items"]] == ["email"]


def test_list_pagination_with_tied_last_at_has_no_duplicates_or_gaps(client, auth_headers):
    for n in range(7):
        add_interaction(
            user_id=f"tie-user-{n}",
            received=f"CAST('{TIE_TS}' AS timestamptz)",
            responded=f"CAST('{TIE_TS}' AS timestamptz) + INTERVAL '1 second'",
        )
    everything = list_threads(client, auth_headers, limit=100)["items"]
    expected = [(t["channel"], t["user_id"]) for t in everything]
    assert len(expected) == 9

    seen: list[tuple] = []
    cursor = None
    for _ in range(20):
        params = {"limit": 2}
        if cursor:
            params["before"] = cursor
        page = list_threads(client, auth_headers, **params)
        seen.extend((t["channel"], t["user_id"]) for t in page["items"])
        if not page["has_more"]:
            break
        cursor = page["next_before"]
        assert cursor
    else:
        pytest.fail("la paginación no terminó")
    assert seen == expected
    assert len(set(seen)) == len(seen)


@pytest.mark.parametrize(
    "params",
    [{"channel": "sms"}, {"limit": 0}, {"limit": 101}, {"before": "basura"}, {"q": "x" * 101}],
)
def test_list_rejects_invalid_parameters(client, auth_headers, params):
    resp = client.get("/monitoring/conversations", params=params, headers=auth_headers)
    assert resp.status_code == 422, resp.text


# -------------------------------------------------------------------- hilo


def test_thread_returns_messages_in_chronological_order(client, auth_headers):
    add_interaction(
        message="Segunda consulta",
        intent="FAQ",
        ai_response="Respuesta 2",
        received="NOW() + INTERVAL '1 minute'",
        responded="NOW() + INTERVAL '61 seconds'",
        urgent=True,
    )
    resp = get_thread(client, auth_headers, "whatsapp", WA_USER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["channel"] == "whatsapp"
    assert body["user_id"] == WA_USER
    assert body["has_more"] is False
    assert body["next_before"] is None
    first, second = body["items"]
    assert first["message"] == "¿Dónde está mi pedido?"
    assert first["ai_response"] == "Está en camino."
    assert first["intent"] == "ESTADO_PEDIDO"
    assert first["is_urgent"] is False
    assert first["tmr_seconds"] == pytest.approx(40.0)
    assert first["received_at"].endswith("Z")
    assert first["responded_at"].endswith("Z")
    assert first["order"] == {"id": 1, "order_number": "ORD-FIX-001", "status": "confirmed"}
    assert first["ticket"] == {"id": 1, "status": "open", "priority": "high"}
    assert set(first) == {
        "interaction_id",
        "received_at",
        "message",
        "responded_at",
        "ai_response",
        "intent",
        "is_urgent",
        "tmr_seconds",
        "order",
        "ticket",
    }
    assert second["message"] == "Segunda consulta"
    assert second["is_urgent"] is True
    assert second["order"] is None
    assert second["ticket"] is None
    assert first["received_at"] < second["received_at"]


def test_thread_message_without_reply_has_null_reply_fields(client, auth_headers):
    execute(
        """
        INSERT INTO interactions (channel, user_id, message, intent, ai_response,
                                  received_at, responded_at)
        VALUES ('telegram', '458721336', 'Hola?', 'GENERAL', 'Hola', NOW(), NULL)
        """
    )
    body = get_thread(client, auth_headers, "telegram", "458721336").json()
    assert body["items"][0]["responded_at"] is None
    assert body["items"][0]["tmr_seconds"] is None


def test_thread_user_id_with_special_characters_travels_in_the_query(client, auth_headers):
    add_interaction(channel="whatsapp", user_id="+54 9 261/555 0000?x=1&y", message="raro")
    resp = get_thread(client, auth_headers, "whatsapp", "+54 9 261/555 0000?x=1&y")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["message"] == "raro"


def test_thread_not_found_is_a_clean_404(client, auth_headers):
    resp = get_thread(client, auth_headers, "telegram", "nadie")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Conversación no encontrada"
    # mismo user_id pero otro canal: es otro hilo
    assert get_thread(client, auth_headers, "telegram", WA_USER).status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"channel": "sms", "user_id": "x"},
        {"channel": "whatsapp"},
        {"user_id": "x"},
        {"channel": "whatsapp", "user_id": ""},
        {"channel": "whatsapp", "user_id": "x" * 201},
        {"channel": "whatsapp", "user_id": WA_USER, "limit": 0},
        {"channel": "whatsapp", "user_id": WA_USER, "limit": 101},
        {"channel": "whatsapp", "user_id": WA_USER, "before": "basura"},
    ],
)
def test_thread_rejects_invalid_parameters(client, auth_headers, params):
    resp = client.get("/monitoring/conversations/thread", params=params, headers=auth_headers)
    assert resp.status_code == 422, resp.text


def test_thread_pages_backwards_without_duplicates_or_gaps(client, auth_headers):
    # 6 mensajes más (7 en total), varios con el mismo received_at
    for n in range(6):
        stamp = TIE_TS if n < 4 else "2026-09-20 16:00:00+00"
        add_interaction(
            message=f"msg-{n}",
            received=f"CAST('{stamp}' AS timestamptz)",
            responded=f"CAST('{stamp}' AS timestamptz) + INTERVAL '1 second'",
        )
    full = get_thread(client, auth_headers, "whatsapp", WA_USER, limit=100).json()["items"]
    expected = [item["interaction_id"] for item in full]
    assert len(expected) == 7
    stamps = [item["received_at"] for item in full]
    assert stamps == sorted(stamps)

    collected: list[int] = []
    cursor = None
    for _ in range(10):
        params = {"limit": 3}
        if cursor:
            params["before"] = cursor
        page = get_thread(client, auth_headers, "whatsapp", WA_USER, **params).json()
        collected = [item["interaction_id"] for item in page["items"]] + collected
        if not page["has_more"]:
            assert page["next_before"] is None
            break
        cursor = page["next_before"]
        assert cursor
    else:
        pytest.fail("la paginación no terminó")
    assert collected == expected


def test_thread_default_page_is_the_newest_messages(client, auth_headers):
    for n in range(4):
        add_interaction(
            message=f"nuevo-{n}",
            received=f"NOW() + INTERVAL '{n + 1} minutes'",
            responded=f"NOW() + INTERVAL '{n + 1} minutes 1 second'",
        )
    page = get_thread(client, auth_headers, "whatsapp", WA_USER, limit=2).json()
    assert [item["message"] for item in page["items"]] == ["nuevo-2", "nuevo-3"]
    assert page["has_more"] is True
