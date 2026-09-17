from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_account_id
from app.core.pagination import PAGE_SIZE, paginated
from app.core.sql import iso
from app.db import fetch_all, fetch_one

router = APIRouter(prefix="/products", tags=["products"])

PRODUCT_COLUMNS = f"""
    id, sku, name, price, stock, stock_min, category,
    {iso('created_at')} AS created_at
"""


@router.get("")
def list_products(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    account_id: int = Depends(get_current_account_id),
) -> dict:
    params = {"limit": PAGE_SIZE, "offset": (page - 1) * PAGE_SIZE}
    count_params: dict = {}
    if search:
        where = "WHERE name ILIKE :pattern OR sku ILIKE :pattern"
        pattern = f"%{search}%"
        params["pattern"] = pattern
        count_params["pattern"] = pattern
    else:
        where = ""

    total = fetch_one(
        f"SELECT COUNT(*) AS c FROM products {where}", count_params
    )["c"]
    items = fetch_all(
        f"""
        SELECT {PRODUCT_COLUMNS}
        FROM products
        {where}
        ORDER BY name
        LIMIT :limit OFFSET :offset
        """,
        params,
    )
    return paginated(items, total, page)