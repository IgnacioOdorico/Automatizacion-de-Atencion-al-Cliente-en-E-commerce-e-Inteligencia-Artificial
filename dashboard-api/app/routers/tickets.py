from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_account_id
from app.core.pagination import PAGE_SIZE, paginated
from app.core.sql import iso
from app.db import fetch_all, fetch_one

router = APIRouter(prefix="/tickets", tags=["tickets"])

TICKET_COLUMNS = f"""
    t.id, t.interaction_id, t.order_id, t.channel, t.user_id, t.subject,
    t.status, t.priority,
    {iso('t.created_at')} AS created_at,
    {iso('t.resolved_at')} AS resolved_at,
    t.data_source
"""


@router.get("")
def list_tickets(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    account_id: int = Depends(get_current_account_id),
) -> dict:
    where = "WHERE t.status = :status" if status_filter else ""
    total = fetch_one(
        f"SELECT COUNT(*) AS c FROM tickets t {where}",
        {"status": status_filter} if status_filter else {},
    )["c"]
    params = {"limit": PAGE_SIZE, "offset": (page - 1) * PAGE_SIZE}
    if status_filter:
        params["status"] = status_filter
    items = fetch_all(
        f"""
        SELECT {TICKET_COLUMNS}
        FROM tickets t
        {where}
        ORDER BY t.created_at DESC
        LIMIT :limit OFFSET :offset
        """,
        params,
    )
    return paginated(items, total, page)


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    account_id: int = Depends(get_current_account_id),
) -> dict:
    ticket = fetch_one(
        f"SELECT {TICKET_COLUMNS} FROM tickets t WHERE t.id = :id",
        {"id": ticket_id},
    )
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado"
        )
    ticket["interaction"] = None
    if ticket["interaction_id"] is not None:
        ticket["interaction"] = fetch_one(
            f"""
            SELECT id, channel, user_id, message, intent, ai_response, is_urgent,
                   {iso('received_at')} AS received_at,
                   {iso('responded_at')} AS responded_at
            FROM interactions
            WHERE id = :id
            """,
            {"id": ticket["interaction_id"]},
        )
    return ticket