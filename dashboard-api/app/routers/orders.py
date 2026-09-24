from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_account_id
from app.core.pagination import PAGE_SIZE, paginated
from app.core.sql import iso
from app.db import fetch_all, fetch_one

router = APIRouter(prefix="/orders", tags=["orders"])

ORDER_COLUMNS = f"""
    o.id, o.order_number, o.customer_name, o.customer_email, o.customer_phone,
    o.quantity, o.total_amount, o.status,
    {iso('o.received_at')} AS received_at,
    {iso('o.processed_at')} AS processed_at,
    {iso('o.notified_at')} AS notified_at,
    o.data_source, p.sku AS product_sku, p.name AS product_name
"""


@router.get("")
def list_orders(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    account_id: int = Depends(get_current_account_id),
) -> dict:
    where = "WHERE o.status = :status" if status_filter else ""
    total = fetch_one(
        f"SELECT COUNT(*) AS c FROM orders o {where}",
        {"status": status_filter} if status_filter else {},
    )["c"]
    params = {"limit": PAGE_SIZE, "offset": (page - 1) * PAGE_SIZE}
    if status_filter:
        params["status"] = status_filter
    items = fetch_all(
        f"""
        SELECT {ORDER_COLUMNS}
        FROM orders o
        LEFT JOIN products p ON p.id = o.product_id
        {where}
        ORDER BY o.received_at DESC
        LIMIT :limit OFFSET :offset
        """,
        params,
    )
    return paginated(items, total, page)


@router.get("/{order_id}")
def get_order(
    order_id: int,
    account_id: int = Depends(get_current_account_id),
) -> dict:
    order = fetch_one(
        f"""
        SELECT {ORDER_COLUMNS}, o.raw_payload
        FROM orders o
        LEFT JOIN products p ON p.id = o.product_id
        WHERE o.id = :id
        """,
        {"id": order_id},
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada"
        )
    order["order_items"] = fetch_all(
        """
        SELECT id, product_id, quantity, unit_price, subtotal
        FROM order_items
        WHERE order_id = :id
        ORDER BY id
        """,
        {"id": order_id},
    )
    return order