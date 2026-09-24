"""Resumen del monitoreo: contadores del bot, del pipeline y de las ejecuciones de n8n."""

from app.core.cursors import to_iso
from app.core.monitoring_domain import (
    CHANNELS,
    INTENTS,
    ORDER_STATUSES,
    TICKET_PRIORITIES,
)
from app.core.n8n_db import n8n_fetch_all
from app.db import fetch_all, fetch_one

WINDOW = "now() - make_interval(hours => :hours)"


def _source(column: str, data_source: str | None) -> str:
    """Condición estática por `data_source` (el valor siempre viaja como bind)."""
    return f" AND {column} = :data_source" if data_source else ""


def _bot(data_source: str | None, params: dict) -> dict:
    intents = ", ".join(
        f"COUNT(*) FILTER (WHERE intent = '{intent}') AS intent_{index}"
        for index, intent in enumerate(INTENTS)
    )
    channels = ", ".join(
        f"COUNT(*) FILTER (WHERE channel = '{channel}') AS channel_{index}"
        for index, channel in enumerate(CHANNELS)
    )
    row = fetch_one(
        f"""
        SELECT COUNT(*) AS interactions,
               ROUND(AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))::numeric, 2) AS avg_tmr,
               COUNT(*) FILTER (WHERE is_urgent) AS urgent,
               {intents}, {channels}
        FROM interactions
        WHERE received_at >= {WINDOW}{_source('data_source', data_source)}
        """,
        params,
    )
    return {
        "interactions": row["interactions"],
        "avg_tmr_seconds": None if row["avg_tmr"] is None else float(row["avg_tmr"]),
        "urgent": row["urgent"],
        "by_intent": {intent: row[f"intent_{i}"] for i, intent in enumerate(INTENTS)},
        "by_channel": {channel: row[f"channel_{i}"] for i, channel in enumerate(CHANNELS)},
    }


def _orders(data_source: str | None, params: dict) -> dict:
    rows = fetch_all(
        f"""
        SELECT status, COUNT(*) AS n FROM orders
        WHERE received_at >= {WINDOW}{_source('data_source', data_source)}
        GROUP BY status
        """,
        params,
    )
    by_status = {status: 0 for status in ORDER_STATUSES}
    for row in rows:
        by_status[row["status"]] = row["n"]
    return {"total": sum(by_status.values()), "by_status": by_status}


def _tickets(data_source: str | None, params: dict) -> dict:
    priorities = ", ".join(
        f"COUNT(*) FILTER (WHERE created_at >= {WINDOW} AND priority = '{priority}')"
        f" AS priority_{index}"
        for index, priority in enumerate(TICKET_PRIORITIES)
    )
    row = fetch_one(
        f"""
        SELECT COUNT(*) FILTER (WHERE created_at >= {WINDOW}) AS created,
               COUNT(*) FILTER (WHERE status IN ('open', 'in_progress')) AS open,
               {priorities}
        FROM tickets
        WHERE TRUE{_source('data_source', data_source)}
        """,
        params,
    )
    return {
        "created": row["created"],
        "open": row["open"],
        "by_priority": {p: row[f"priority_{i}"] for i, p in enumerate(TICKET_PRIORITIES)},
    }


def _stock_alerts(data_source: str | None, params: dict) -> int:
    return fetch_one(
        f"""
        SELECT COUNT(*) AS n FROM stock_alerts
        WHERE created_at >= {WINDOW}{_source('data_source', data_source)}
        """,
        params,
    )["n"]


def _last_activity(data_source: str | None) -> str | None:
    source = _source("data_source", data_source)
    row = fetch_one(
        f"""
        SELECT MAX(ts) AS last_at FROM (
            SELECT GREATEST(received_at, processed_at, notified_at) AS ts
            FROM orders WHERE TRUE{source}
            UNION ALL
            SELECT GREATEST(received_at, responded_at)
            FROM interactions WHERE TRUE{source}
            UNION ALL
            SELECT created_at FROM tickets WHERE TRUE{source}
            UNION ALL
            SELECT created_at FROM stock_alerts WHERE TRUE{source}
        ) activity
        """,
        {"data_source": data_source} if data_source else {},
    )
    return to_iso(row["last_at"])


def _executions(hours: int) -> dict:
    rows = n8n_fetch_all(
        f"""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE status = 'success') AS success,
               COUNT(*) FILTER (WHERE status IN ('error', 'crashed')) AS error,
               (SELECT MAX(COALESCE("stoppedAt", "startedAt")) FROM execution_entity
                WHERE status IN ('error', 'crashed') AND "deletedAt" IS NULL) AS last_error_at
        FROM execution_entity
        WHERE "deletedAt" IS NULL
          AND COALESCE("startedAt", "createdAt") >= {WINDOW}
        """,
        {"hours": hours},
    )
    if rows is None:
        return {"available": False, "total": 0, "success": 0, "error": 0, "last_error_at": None}
    row = rows[0]
    return {
        "available": True,
        "total": row["total"],
        "success": row["success"],
        "error": row["error"],
        "last_error_at": to_iso(row["last_error_at"]),
    }


def build_summary(hours: int, data_source: str | None) -> dict:
    params: dict = {"hours": hours}
    if data_source:
        params["data_source"] = data_source
    generated_at = fetch_one("SELECT now() AS now")["now"]
    return {
        "window_hours": hours,
        "generated_at": to_iso(generated_at),
        "data_source": data_source or "all",
        "last_activity_at": _last_activity(data_source),
        "bot": _bot(data_source, params),
        "orders": _orders(data_source, params),
        "tickets": _tickets(data_source, params),
        "stock_alerts": _stock_alerts(data_source, params),
        "executions": _executions(hours),
    }
