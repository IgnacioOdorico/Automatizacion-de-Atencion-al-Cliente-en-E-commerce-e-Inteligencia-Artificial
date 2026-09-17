import pytest

pytestmark = pytest.mark.integration


def test_tickets_list_requires_jwt(client):
    assert client.get("/tickets").status_code == 401


def test_tickets_list_shape(client, auth_headers):
    resp = client.get("/tickets", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 3
    assert body["total_pages"] == 1
    first = body["items"][0]
    for key in ["channel", "user_id", "subject", "priority", "created_at", "status"]:
        assert key in first


def test_tickets_status_filter(client, auth_headers):
    resp = client.get("/tickets?status=open", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "open"


def test_resolved_ticket_with_null_resolved_at_is_ok(client, auth_headers):
    resp = client.get("/tickets?status=resolved", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    ticket = body["items"][0]
    assert ticket["status"] == "resolved"
    assert ticket["resolved_at"] is None


def test_ticket_detail_references_interaction(client, auth_headers):
    resp = client.get("/tickets/1", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == 1
    assert body["interaction_id"] == 1
    assert body["interaction"]["id"] == 1
    assert body["interaction"]["intent"] == "ESTADO_PEDIDO"


def test_ticket_detail_without_interaction(client, auth_headers):
    resp = client.get("/tickets/2", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["interaction_id"] is None
    assert resp.json()["interaction"] is None


def test_ticket_detail_requires_jwt(client):
    assert client.get("/tickets/1").status_code == 401


def test_ticket_detail_not_found(client, auth_headers):
    assert client.get("/tickets/999999", headers=auth_headers).status_code == 404