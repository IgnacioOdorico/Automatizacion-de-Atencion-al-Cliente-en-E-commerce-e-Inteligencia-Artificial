"""Métricas en vivo (K1/K2): reemplazo de los paneles de Grafana dentro del portal.

Misma semántica de cálculo que `grafana/dashboards/tesis-flujo1.json` /
`tesis-flujo2.json` (MTTD/MTTR/end-to-end/TMR con `EXTRACT(EPOCH FROM (...))`),
pero recalculada en vivo sobre `orders`/`interactions` (nunca sobre
`v_chatbot_corpus`, que es una ventana congelada del 12/08 23-24h — ver
`docs/DESVIOS_SPEC.md` §2.12 y §3.2).

Sin `hours`, los promedios/totales/`by_status`/`by_intent` cubren el histórico
completo (no se acota: son escalares, no crecen con el volumen de datos). La
serie diaria (`daily`/`by_channel_daily`) sí se acota a `MAX_HISTORICAL_DAYS`
días cuando no hay `hours`, para no devolver una fila por cada día desde el
origen de los datos.
"""

from app.core.cursors import to_iso
from app.core.monitoring_domain import CHANNELS, INTENTS, ORDER_STATUSES
from app.db import fetch_all, fetch_one

MAX_HISTORICAL_DAYS = 90

DAILY_ORDER_STATUS_KEYS: tuple[str, ...] = (
    "confirmed",
    "shipped",
    "delivered",
    "no_stock",
    "cancelled",
    "error",
)


def _window_clause(column: str, hours: int | None) -> str:
    """Filtro de ventana estático; `hours` siempre viaja como bind cuando se usa."""
    if hours is None:
        return ""
    return f" AND {column} >= now() - make_interval(hours => :hours)"


def _source_clause(column: str, data_source: str | None) -> str:
    """Filtro de `data_source` estático; el valor siempre viaja como bind."""
    return f" AND {column} = :data_source" if data_source else ""


def _base_params(hours: int | None, data_source: str | None) -> dict:
    params: dict = {}
    if hours is not None:
        params["hours"] = hours
    if data_source:
        params["data_source"] = data_source
    return params


def _daily_params(hours: int | None, params: dict) -> dict:
    """Params de la serie diaria: la ventana es `hours`, o el tope documentado
    cuando no viene `hours` (ver MAX_HISTORICAL_DAYS), nunca "sin ventana"."""
    window_hours = hours if hours is not None else MAX_HISTORICAL_DAYS * 24
    return {**params, "window_hours": window_hours}


# ---------------------------------------------------------------------------
# K1 — GET /metrics/orders
# ---------------------------------------------------------------------------


def _order_aggregates(hours: int | None, data_source: str | None, params: dict) -> dict:
    row = fetch_one(
        f"""
        SELECT
            ROUND((AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))
                   FILTER (WHERE processed_at IS NOT NULL))::numeric, 3) AS avg_mttd,
            ROUND((AVG(EXTRACT(EPOCH FROM (notified_at - processed_at)))
                   FILTER (WHERE notified_at IS NOT NULL))::numeric, 3) AS avg_mttr,
            ROUND((AVG(EXTRACT(EPOCH FROM (notified_at - received_at)))
                   FILTER (WHERE notified_at IS NOT NULL AND processed_at IS NOT NULL)
                  )::numeric, 3) AS avg_end_to_end,
            COUNT(*) AS total_orders
        FROM orders
        WHERE TRUE{_window_clause('received_at', hours)}{_source_clause('data_source', data_source)}
        """,
        params,
    )
    return {
        "avg_mttd_seconds": None if row["avg_mttd"] is None else float(row["avg_mttd"]),
        "avg_mttr_seconds": None if row["avg_mttr"] is None else float(row["avg_mttr"]),
        "avg_end_to_end_seconds": (
            None if row["avg_end_to_end"] is None else float(row["avg_end_to_end"])
        ),
        "total_orders": row["total_orders"],
    }


def _order_by_status(hours: int | None, data_source: str | None, params: dict) -> dict:
    rows = fetch_all(
        f"""
        SELECT status, COUNT(*) AS n FROM orders
        WHERE TRUE{_window_clause('received_at', hours)}{_source_clause('data_source', data_source)}
        GROUP BY status
        """,
        params,
    )
    by_status = {status: 0 for status in ORDER_STATUSES}
    for row in rows:
        if row["status"] in by_status:
            by_status[row["status"]] = row["n"]
    return by_status


def _order_daily(hours: int | None, data_source: str | None, params: dict) -> list[dict]:
    daily_params = _daily_params(hours, params)
    status_filters = ", ".join(
        f"COUNT(*) FILTER (WHERE o.status = '{key}') AS {key}"
        for key in DAILY_ORDER_STATUS_KEYS
    )
    rows = fetch_all(
        f"""
        WITH days AS (
            SELECT generate_series(
                date_trunc('day', (now() AT TIME ZONE 'UTC') - make_interval(hours => :window_hours)),
                date_trunc('day', now() AT TIME ZONE 'UTC'),
                interval '1 day'
            )::date AS day
        )
        SELECT d.day,
               COALESCE(agg.total, 0) AS total_orders,
               COALESCE(agg.confirmed, 0) AS confirmed,
               COALESCE(agg.shipped, 0) AS shipped,
               COALESCE(agg.delivered, 0) AS delivered,
               COALESCE(agg.no_stock, 0) AS no_stock,
               COALESCE(agg.cancelled, 0) AS cancelled,
               COALESCE(agg.error, 0) AS error
        FROM days d
        LEFT JOIN (
            SELECT (o.received_at AT TIME ZONE 'UTC')::date AS day,
                   COUNT(*) AS total,
                   {status_filters}
            FROM orders o
            WHERE o.received_at >= now() - make_interval(hours => :window_hours)
                  {_source_clause('o.data_source', data_source)}
            GROUP BY 1
        ) agg ON agg.day = d.day
        ORDER BY d.day ASC
        """,
        daily_params,
    )
    return [
        {
            "date": row["day"].isoformat(),
            "total_orders": row["total_orders"],
            "confirmed": row["confirmed"],
            "shipped": row["shipped"],
            "delivered": row["delivered"],
            "no_stock": row["no_stock"],
            "cancelled": row["cancelled"],
            "error": row["error"],
        }
        for row in rows
    ]


def fetch_order_metrics(hours: int | None, data_source: str | None) -> dict:
    params = _base_params(hours, data_source)
    generated_at = to_iso(fetch_one("SELECT now() AS now")["now"])
    aggregates = _order_aggregates(hours, data_source, params)
    return {
        "window_hours": hours,
        "generated_at": generated_at,
        **aggregates,
        "by_status": _order_by_status(hours, data_source, params),
        "daily": _order_daily(hours, data_source, params),
    }


# ---------------------------------------------------------------------------
# K2 — GET /metrics/chatbot (solo `interactions`, nunca `v_chatbot_corpus`)
# ---------------------------------------------------------------------------


def _chatbot_aggregates(hours: int | None, data_source: str | None, params: dict) -> dict:
    row = fetch_one(
        f"""
        SELECT COUNT(*) AS total,
               ROUND((AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))
                      FILTER (WHERE responded_at IS NOT NULL))::numeric, 3) AS avg_tmr
        FROM interactions
        WHERE TRUE{_window_clause('received_at', hours)}{_source_clause('data_source', data_source)}
        """,
        params,
    )
    return {
        "total_interactions": row["total"],
        "avg_tmr_seconds": None if row["avg_tmr"] is None else float(row["avg_tmr"]),
    }


def _chatbot_by_intent(hours: int | None, data_source: str | None, params: dict) -> dict:
    selects = ", ".join(
        f"""COUNT(*) FILTER (WHERE intent = '{intent}') AS count_{i},
            ROUND((AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))
                   FILTER (WHERE intent = '{intent}' AND responded_at IS NOT NULL)
                  )::numeric, 3) AS avg_{i}"""
        for i, intent in enumerate(INTENTS)
    )
    row = fetch_one(
        f"""
        SELECT {selects}
        FROM interactions
        WHERE TRUE{_window_clause('received_at', hours)}{_source_clause('data_source', data_source)}
        """,
        params,
    )
    return {
        intent: {
            "count": row[f"count_{i}"],
            "avg_tmr_seconds": (
                None if row[f"avg_{i}"] is None else float(row[f"avg_{i}"])
            ),
        }
        for i, intent in enumerate(INTENTS)
    }


def _chatbot_by_channel_daily(
    hours: int | None, data_source: str | None, params: dict
) -> list[dict]:
    daily_params = _daily_params(hours, params)
    channel_filters = ", ".join(
        f"COUNT(*) FILTER (WHERE i.channel = '{channel}') AS {channel}"
        for channel in CHANNELS
    )
    rows = fetch_all(
        f"""
        WITH days AS (
            SELECT generate_series(
                date_trunc('day', (now() AT TIME ZONE 'UTC') - make_interval(hours => :window_hours)),
                date_trunc('day', now() AT TIME ZONE 'UTC'),
                interval '1 day'
            )::date AS day
        )
        SELECT d.day,
               COALESCE(agg.whatsapp, 0) AS whatsapp,
               COALESCE(agg.telegram, 0) AS telegram,
               COALESCE(agg.email, 0) AS email
        FROM days d
        LEFT JOIN (
            SELECT (i.received_at AT TIME ZONE 'UTC')::date AS day,
                   {channel_filters}
            FROM interactions i
            WHERE i.received_at >= now() - make_interval(hours => :window_hours)
                  {_source_clause('i.data_source', data_source)}
            GROUP BY 1
        ) agg ON agg.day = d.day
        ORDER BY d.day ASC
        """,
        daily_params,
    )
    return [
        {
            "date": row["day"].isoformat(),
            "whatsapp": row["whatsapp"],
            "telegram": row["telegram"],
            "email": row["email"],
        }
        for row in rows
    ]


def fetch_chatbot_metrics(hours: int | None, data_source: str | None) -> dict:
    params = _base_params(hours, data_source)
    generated_at = to_iso(fetch_one("SELECT now() AS now")["now"])
    aggregates = _chatbot_aggregates(hours, data_source, params)
    return {
        "window_hours": hours,
        "generated_at": generated_at,
        **aggregates,
        "by_intent": _chatbot_by_intent(hours, data_source, params),
        "by_channel_daily": _chatbot_by_channel_daily(hours, data_source, params),
    }
