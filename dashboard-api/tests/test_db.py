import pytest

pytestmark = pytest.mark.integration


def test_smoke_query_v_metrics_summary():
    from app.db import fetch_one

    row = fetch_one(
        "SELECT total_orders, orders_confirmed, avg_mttd_seg, avg_mttr_seg, "
        "avg_tmr_seg FROM v_metrics_summary"
    )
    assert row is not None
    assert set(row) == {
        "total_orders",
        "orders_confirmed",
        "avg_mttd_seg",
        "avg_mttr_seg",
        "avg_tmr_seg",
    }


def test_fetch_all_returns_rows():
    from app.db import fetch_all

    rows = fetch_all("SELECT id FROM products ORDER BY id LIMIT 3")
    assert isinstance(rows, list)
    assert len(rows) == 3


def test_params_are_bound_not_interpolated():
    from app.db import fetch_all

    rows = fetch_all(
        "SELECT id FROM products WHERE sku = :sku", {"sku": "PROD-001"}
    )
    assert len(rows) == 1


def test_fetch_one_returns_none_when_empty():
    from app.db import fetch_one

    row = fetch_one(
        "SELECT id FROM products WHERE sku = :sku", {"sku": "NO-EXISTE-999"}
    )
    assert row is None