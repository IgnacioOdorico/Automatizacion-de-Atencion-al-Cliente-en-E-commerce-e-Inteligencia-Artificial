import pytest

pytestmark = pytest.mark.integration


def test_products_list_requires_jwt(client):
    assert client.get("/products").status_code == 401


def test_products_list_shape_and_order(client, auth_headers):
    resp = client.get("/products", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 8
    assert body["total_pages"] == 1
    first = body["items"][0]
    for key in ["sku", "name", "price", "stock", "stock_min", "category"]:
        assert key in first
    names = [item["name"] for item in body["items"]]
    assert names == sorted(names)


def test_products_search_by_name(client, auth_headers):
    resp = client.get("/products?search=auricular", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert "Auriculares" in body["items"][0]["name"]


def test_products_search_is_case_insensitive_and_matches_sku(client, auth_headers):
    by_name = client.get("/products?search=LOGITECH", headers=auth_headers).json()
    assert by_name["total"] == 2

    by_sku = client.get("/products?search=prod-001", headers=auth_headers).json()
    assert by_sku["total"] == 1
    assert by_sku["items"][0]["sku"] == "PROD-001"


def test_products_search_without_matches(client, auth_headers):
    body = client.get("/products?search=zzzz", headers=auth_headers).json()
    assert body["total"] == 0
    assert body["items"] == []
    assert body["total_pages"] == 0