from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.cursors import CursorError
from app.core.deps import get_current_account_id
from app.core.monitoring_domain import Channel, DataSource
from app.core.monitoring_feed import EVENT_TYPES, fetch_events
from app.core.monitoring_summary import build_summary

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    dependencies=[Depends(get_current_account_id)],
)


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


@router.get("/summary")
def monitoring_summary(
    hours: int = Query(default=24, ge=1, le=168),
    data_source: DataSource | None = Query(default=None),
) -> dict:
    return build_summary(hours, data_source)


@router.get("/events")
def monitoring_events(
    limit: int = Query(default=50, ge=1, le=100),
    before: str | None = Query(default=None, max_length=300),
    since: str | None = Query(default=None, max_length=300),
    types: str | None = Query(default=None, max_length=200),
    channel: Channel | None = Query(default=None),
    data_source: DataSource | None = Query(default=None),
) -> dict:
    if before and since:
        raise _unprocessable("No se pueden combinar los parámetros before y since")
    wanted: list[str] | None = None
    if types:
        wanted = [part.strip() for part in types.split(",") if part.strip()]
        unknown = sorted(set(wanted) - set(EVENT_TYPES))
        if unknown:
            raise _unprocessable(
                f"Tipos de evento desconocidos: {', '.join(unknown)}. "
                f"Válidos: {', '.join(EVENT_TYPES)}"
            )
    try:
        return fetch_events(
            limit=limit,
            before=before,
            since=since,
            types=wanted,
            channel=channel,
            data_source=data_source,
        )
    except CursorError as exc:
        raise _unprocessable("Cursor inválido") from exc
