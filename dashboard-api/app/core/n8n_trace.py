"""Traza nodo por nodo de una ejecución de n8n.

Lee `resultData.runData` del `execution_data.data` (formato `flatted`) y lo cruza con
los nodos del workflow. De cada nodo sale su estado, tiempos, cantidad de items y una
vista previa acotada y redactada de la salida. NUNCA sale `stack`, `parameters` ni
datos binarios.
"""

from datetime import datetime, timezone
from typing import Any

from app.core.cursors import to_iso
from app.core.flatted import FlattedError, parse_flatted
from app.core.redaction import build_preview, redact_string

MAX_MESSAGE = 500
MAX_LIST_MESSAGE = 300
MAX_DESCRIPTION = 1000
MAX_PREVIEW_ITEMS = 50
DEFAULT_ERROR_MESSAGE = "El nodo terminó con error"
NO_DATA_ERROR = "La ejecución no tiene datos de traza (¿fueron purgados?)"
CORRUPT_ERROR = "No se pudo leer el detalle de la ejecución: los datos están corruptos"

_ERROR_STATUSES = {"error", "crashed"}
_LIVE_STATUSES = {"running", "waiting", "canceled"}


def _empty(*, truncated: bool = False, error: str | None = None) -> dict:
    return {
        "nodes": [],
        "path": [],
        "last_node_executed": None,
        "truncated": truncated,
        "error": error,
        "execution_error": None,
    }


def clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "…"


def extract_error(raw: Any) -> dict:
    """`{message, description}` redactados y acotados; nunca `stack` ni `node`."""
    message: Any = None
    description: Any = None
    if isinstance(raw, dict):
        message = raw.get("message")
        description = raw.get("description")
    elif isinstance(raw, str):
        message = raw
    text = str(message).strip() if message not in (None, "") else DEFAULT_ERROR_MESSAGE
    detail = str(description).strip() if description not in (None, "") else None
    return {
        "message": clip(redact_string(text), MAX_MESSAGE),
        "description": None if detail is None else clip(redact_string(detail), MAX_DESCRIPTION),
    }


def _epoch_ms(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def _iso_from_ms(value: Any) -> str | None:
    millis = _epoch_ms(value)
    if millis is None:
        return None
    try:
        return to_iso(datetime.fromtimestamp(millis / 1000, tz=timezone.utc))
    except (OverflowError, OSError, ValueError):
        return None


def _outputs(run: dict) -> list[list]:
    data = run.get("data")
    main = data.get("main") if isinstance(data, dict) else None
    if not isinstance(main, list):
        return []
    return [branch if isinstance(branch, list) else [] for branch in main]


def _item_jsons(branches: list[list]) -> list:
    items: list = []
    for branch in branches:
        for item in branch:
            if isinstance(item, dict) and item.get("json") is not None:
                items.append(item["json"])
            if len(items) >= MAX_PREVIEW_ITEMS:
                return items
    return items


def _status(runs: list[dict]) -> str:
    if any(run.get("executionStatus") in _ERROR_STATUSES or run.get("error") for run in runs):
        return "error"
    last = runs[-1].get("executionStatus")
    return last if last in _LIVE_STATUSES else "success"


def _node_trace(name: str, short: str | None, runs: list[dict]) -> dict:
    first, last = runs[0], runs[-1]
    status = _status(runs)
    error = None
    if status == "error":
        failing = next(
            (r for r in runs if r.get("error") or r.get("executionStatus") in _ERROR_STATUSES),
            last,
        )
        error = extract_error(failing.get("error"))
    branches = _outputs(last)
    preview, truncated = build_preview(_item_jsons(branches))
    durations = [_epoch_ms(r.get("executionTime")) for r in runs]
    return {
        "name": name,
        "short_type": short,
        "status": status,
        "started_at": _iso_from_ms(first.get("startTime")),
        "duration_ms": sum(d for d in durations if d is not None) if any(
            d is not None for d in durations
        ) else None,
        "items_out": sum(len(branch) for branch in branches),
        "outputs": [len(branch) for branch in branches],
        "runs": len(runs),
        "error": error,
        "output_preview": preview,
        "output_truncated": truncated,
    }


def _skipped(name: str, short: str | None) -> dict:
    return {
        "name": name,
        "short_type": short,
        "status": "skipped",
        "started_at": None,
        "duration_ms": None,
        "items_out": 0,
        "outputs": [],
        "runs": 0,
        "error": None,
        "output_preview": None,
        "output_truncated": False,
    }


def _first_error(result: dict, executed: dict[str, list[dict]]) -> Any:
    """Error a nivel de ejecución; si falta, el del primer nodo que falló."""
    if result.get("error"):
        return result["error"]
    for runs in executed.values():
        for run in runs:
            if run.get("error") is not None or run.get("executionStatus") in _ERROR_STATUSES:
                return run.get("error") or {}
    return None


def _order_key(item: tuple[str, list[dict]]) -> tuple:
    first = item[1][0]
    index = _epoch_ms(first.get("executionIndex"))
    start = _epoch_ms(first.get("startTime"))
    return (index if index is not None else 1 << 60, start if start is not None else 1 << 60)


def build_trace(
    text: str | None, graph_nodes: list[dict], *, oversized: bool = False
) -> dict:
    """Traza de una ejecución.

    `graph_nodes` son los nodos ya sanitizados (`name`, `short_type`, ...). Con
    `oversized` el llamador ya decidió no parsear: se devuelve la traza mínima.
    """
    if oversized:
        return _empty(truncated=True)
    if not text:
        return _empty(error=NO_DATA_ERROR)
    try:
        payload = parse_flatted(text)
    except FlattedError:
        return _empty(error=CORRUPT_ERROR)
    if not isinstance(payload, dict):
        return _empty(error=CORRUPT_ERROR)

    result = payload.get("resultData")
    result = result if isinstance(result, dict) else {}
    run_data = result.get("runData")
    run_data = run_data if isinstance(run_data, dict) else {}

    executed: dict[str, list[dict]] = {}
    for name, runs in run_data.items():
        if isinstance(name, str) and isinstance(runs, list):
            valid = [run for run in runs if isinstance(run, dict)]
            if valid:
                executed[name] = valid

    ordered = sorted(executed.items(), key=_order_key)
    path = [name for name, _ in ordered]

    known = {node["name"] for node in graph_nodes}
    nodes: list[dict] = []
    for node in graph_nodes:
        runs = executed.get(node["name"])
        short = node.get("short_type")
        nodes.append(_node_trace(node["name"], short, runs) if runs else _skipped(node["name"], short))
    for name in path:
        if name not in known:
            nodes.append(_node_trace(name, None, executed[name]))

    last = result.get("lastNodeExecuted")
    if not isinstance(last, str):
        last = path[-1] if path else None
    failure = _first_error(result, executed)
    return {
        "nodes": nodes,
        "path": path,
        "last_node_executed": last,
        "truncated": False,
        "error": None,
        "execution_error": (
            None if failure is None else clip(extract_error(failure)["message"], MAX_LIST_MESSAGE)
        ),
    }


def execution_error_message(text: str | None) -> str | None:
    """Mensaje (redactado y corto) del error de una ejecución; `None` si no hay o no se lee."""
    if not text:
        return None
    return build_trace(text, [])["execution_error"]
