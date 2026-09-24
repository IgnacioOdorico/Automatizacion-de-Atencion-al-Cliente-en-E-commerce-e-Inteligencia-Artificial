import pytest

pytestmark = pytest.mark.integration


def test_orders_list_requires_jwt(client):
    assert client.get("/orders").status_code == 401


def test_orders_list_shape_and_order(client, auth_headers):
    resp = client.get("/orders", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 3
    assert body["total_pages"] == 1
    numbers = [item["order_number"] for item in body["items"]]
    assert numbers == ["ORD-FIX-001", "ORD-FIX-002", "ORD-FIX-003"]

    first = body["items"][0]
    for key in [
        "order_number",
        "customer_name",
        "status",
        "total_amount",
        "received_at",
        "processed_at",
        "notified_at",
        "product_sku",
        "product_name",
    ]:
        assert key in first
    assert first["received_at"].endswith("Z")
    assert first["product_sku"] == "PROD-001"


def test_orders_status_filter(client, auth_headers):
    resp = client.get("/orders?status=no_stock", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["order_number"] == "ORD-FIX-002"
    assert all(item["status"] == "no_stock" for item in body["items"])


def test_orders_page_beyond_last_is_empty(client, auth_headers):
    resp = client.get("/orders?page=2", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert body["items"] == []


def test_order_detail_includes_items_and_raw_payload(client, auth_headers):
    resp = client.get("/orders/1", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["order_number"] == "ORD-FIX-001"
    assert body["raw_payload"]["order_number"] == "ORD-FIX-001"
    assert len(body["order_items"]) == 1
    item = body["order_items"][0]
    assert item["product_id"] == 1
    assert float(item["unit_price"]) == 599.99
    assert float(item["subtotal"]) == 599.99


def test_order_detail_requires_jwt(client):
    assert client.get("/orders/1").status_code == 401


def test_order_detail_not_found(client, auth_headers):
    assert client.get("/orders/999999", headers=auth_headers).status_code == 404