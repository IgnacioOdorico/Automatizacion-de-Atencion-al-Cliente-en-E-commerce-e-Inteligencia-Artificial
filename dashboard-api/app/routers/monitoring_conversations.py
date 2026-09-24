from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.cursors import CursorError
from app.core.deps import get_current_account_id
from app.core.monitoring_conversations import (
    fetch_thread,
    list_conversations,
    thread_exists,
)
from app.core.monitoring_domain import Channel, DataSource

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    dependencies=[Depends(get_current_account_id)],
)


def _bad_cursor() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cursor inválido"
    )


@router.get("/conversations")
def monitoring_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    before: str | None = Query(default=None, max_length=400),
    channel: Channel | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    data_source: DataSource | None = Query(default=None),
) -> dict:
    try:
        return list_conversations(
            limit=limit, before=before, channel=channel, q=q, data_source=data_source
        )
    except CursorError as exc:
        raise _bad_cursor() from exc


@router.get("/conversations/thread")
def monitoring_conversation_thread(
    channel: Channel = Query(),
    user_id: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
    before: str | None = Query(default=None, max_length=400),
) -> dict:
    if not thread_exists(channel, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada"
        )
    try:
        return fetch_thread(channel=channel, user_id=user_id, limit=limit, before=before)
    except CursorError as exc:
        raise _bad_cursor() from exc
