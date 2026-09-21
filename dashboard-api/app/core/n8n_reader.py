"""Lectura de solo lectura de workflows y ejecuciones desde las tablas internas de n8n.

Tablas (n8n 2.12.2, misma PostgreSQL): `workflow_entity`, `execution_entity` y
`execution_data`. Si no existen o no son legibles, las funciones devuelven la forma
"no disponible" en vez de fallar. Todo el SQL es estático y parametrizado.
"""

import json
from datetime import datetime
from typing import Any

from app.core.cursors import to_iso
from app.core.n8n_db import n8n_fetch_all
from app.core.n8n_graph import sanitize_graph, sanitize_nodes
from app.core.n8n_trace import build_trace, execution_error_message

# Tope de `execution_data.data` que se parsea: por encima se devuelve la traza mínima.
DETAIL_MAX_BYTES = 2_000_000
# Tope, más chico, para extraer el mensaje de error de cada fila de la lista.
LIST_MAX_BYTES = 500_000

_FAILED = "('error', 'crashed')"


def _duration_ms(started: datetime | None, stopped: datetime | None) -> int | None:
    if started is None or stopped is None:
        return None
    return round((stopped - started).total_seconds() * 1000)


def _json(value: Any) -> Any:
    """Las columnas `json` llegan ya parseadas; por las dudas también acepta texto."""
    if isinstance(value, (str, bytes)):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


# ------------------------------------------------------------------ workflows


def list_workflows() -> dict:
    rows = n8n_fetch_all(
        f"""
        SELECT w.id, w.name, w.active, w."updatedAt" AS updated_at,
               (SELECT COUNT(*) FROM execution_entity e
                WHERE e."workflowId" = w.id AND e."deletedAt" IS NULL
                  AND COALESCE(e."startedAt", e."createdAt") >= now() - INTERVAL '24 hours'
               ) AS executions_24h,
               (SELECT COUNT(*) FROM execution_entity e
                WHERE e."workflowId" = w.id AND e."deletedAt" IS NULL
                  AND e.status IN {_FAILED}
                  AND COALESCE(e."startedAt", e."createdAt") >= now() - INTERVAL '24 hours'
               ) AS errors_24h,
               last.id AS last_id, last.status AS last_status,
               last.started_at AS last_started_at, last.stopped_at AS last_stopped_at
        FROM workflow_entity w
        LEFT JOIN LATERAL (
            SELECT e.id, e.status, COALESCE(e."startedAt", e."createdAt") AS started_at,
                   e."stoppedAt" AS stopped_at
            FROM execution_entity e
            WHERE e."workflowId" = w.id AND e."deletedAt" IS NULL
            ORDER BY e.id DESC
            LIMIT 1
        ) last ON TRUE
        WHERE NOT w."isArchived"
        ORDER BY w.name, w.id
        """
    )
    if rows is None:
        return {"available": False, "items": []}
    return {
        "available": True,
        "items": [
            {
                "id": row["id"],
                "name": row["name"],
                "active": row["active"],
                "updated_at": to_iso(row["updated_at"]),
                "executions_24h": row["executions_24h"],
                "errors_24h": row["errors_24h"],
                "last_execution": (
                    None
                    if row["last_id"] is None
                    else {
                        "id": row["last_id"],
                        "status": row["last_status"],
                        "started_at": to_iso(row["last_started_at"]),
                        "duration_ms": _duration_ms(
                            row["last_started_at"], row["last_stopped_at"]
                        ),
                    }
                ),
            }
            for row in rows
        ],
    }


def get_workflow_graph(workflow_id: str) -> dict | None:
    rows = n8n_fetch_all(
        """
        SELECT id, name, active, nodes, connections
        FROM workflow_entity
        WHERE id = :id
        """,
        {"id": workflow_id},
    )
    if not rows:
        return None
    row = rows[0]
    graph = sanitize_graph(_json(row["nodes"]), _json(row["connections"]))
    return {"id": row["id"], "name": row["name"], "active": row["active"], **graph}


# ----------------------------------------------------------------- ejecuciones

_EXECUTION_COLUMNS = """
    e.id, e."workflowId" AS workflow_id, w.name AS workflow_name, e.status, e.mode,
    COALESCE(e."startedAt", e."createdAt") AS started_at, e."stoppedAt" AS stopped_at
"""


def _execution(row: dict, error_message: str | None) -> dict:
    return {
        "id": row["id"],
        "workflow_id": row["workflow_id"],
        "workflow_name": row["workflow_name"],
        "status": row["status"],
        "mode": row["mode"],
        "started_at": to_iso(row["started_at"]),
        "stopped_at": to_iso(row["stopped_at"]),
        "duration_ms": _duration_ms(row["started_at"], row["stopped_at"]),
        "error_message": error_message,
    }


def _error_messages(ids: list[int]) -> dict[int, str | None]:
    if not ids:
        return {}
    rows = n8n_fetch_all(
        """
        SELECT "executionId" AS id,
               CASE WHEN octet_length(data) <= :cap THEN data END AS data
        FROM execution_data
        WHERE "executionId" = ANY(:ids)
        """,
        {"cap": LIST_MAX_BYTES, "ids": ids},
    )
    return {row["id"]: execution_error_message(row["data"]) for row in rows or []}


def list_executions(
    *,
    limit: int,
    before: int | None = None,
    status: str | None = None,
    workflow_id: str | None = None,
) -> dict:
    conditions = ['e."deletedAt" IS NULL']
    params: dict = {"fetch": limit + 1}
    if before is not None:
        conditions.append("e.id < :before")
        params["before"] = before
    if status:
        conditions.append("e.status = :status")
        params["status"] = status
    if workflow_id:
        conditions.append('e."workflowId" = :workflow_id')
        params["workflow_id"] = workflow_id
    rows = n8n_fetch_all(
        f"""
        SELECT {_EXECUTION_COLUMNS}
        FROM execution_entity e
        LEFT JOIN workflow_entity w ON w.id = e."workflowId"
        WHERE {' AND '.join(conditions)}
        ORDER BY e.id DESC
        LIMIT :fetch
        """,
        params,
    )
    if rows is None:
        return {"available": False, "items": [], "has_more": False, "next_before": None}
    has_more = len(rows) > limit
    rows = rows[:limit]
    messages = _error_messages([r["id"] for r in rows if r["status"] in ("error", "crashed")])
    items = [_execution(row, messages.get(row["id"])) for row in rows]
    return {
        "available": True,
        "items": items,
        "has_more": has_more,
        "next_before": items[-1]["id"] if has_more and items else None,
    }


def get_execution_trace(execution_id: int) -> dict | None:
    rows = n8n_fetch_all(
        f"""
        SELECT {_EXECUTION_COLUMNS}
        FROM execution_entity e
        LEFT JOIN workflow_entity w ON w.id = e."workflowId"
        WHERE e.id = :id AND e."deletedAt" IS NULL
        """,
        {"id": execution_id},
    )
    if not rows:
        return None
    row = rows[0]

    detail = n8n_fetch_all(
        """
        SELECT CASE WHEN octet_length(d.data) <= :cap THEN d.data END AS data,
               octet_length(d.data) > :cap AS oversized,
               d."workflowData" -> 'nodes' AS nodes
        FROM execution_data d
        WHERE d."executionId" = :id
        """,
        {"cap": DETAIL_MAX_BYTES, "id": execution_id},
    )
    data = detail[0] if detail else None

    graph_nodes = sanitize_nodes(_json(data["nodes"])) if data else []
    if not graph_nodes:  # sin instantánea del workflow: usa el actual
        current = n8n_fetch_all(
            "SELECT nodes FROM workflow_entity WHERE id = :id", {"id": row["workflow_id"]}
        )
        if current:
            graph_nodes = sanitize_nodes(_json(current[0]["nodes"]))

    trace = build_trace(
        data["data"] if data else None,
        graph_nodes,
        oversized=bool(data and data["oversized"]),
    )
    execution_error = trace.pop("execution_error")
    return {
        "execution": _execution(row, execution_error),
        "workflow_id": row["workflow_id"],
        **trace,
    }
