"""Fixtures de las tablas internas de n8n (2.12.2) para los tests de monitoreo.

Las tablas de n8n NO existen en la BD de test: este módulo crea DDL mínimo que
espeja las columnas reales (`\\d workflow_entity`, `\\d execution_entity`,
`\\d execution_data`) y arma datos con el mismo formato que escribe n8n, incluido
el formato `flatted` de `execution_data.data`.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from app.db import execute, execute_returning_one, fetch_one

REPO_ROOT = Path(__file__).resolve().parents[2]
FLUJO1_PATH = REPO_ROOT / "workflows" / "Flujo 1 — Pipeline de Procesamiento de Órdenes.json"
FLUJO2_PATH = REPO_ROOT / "workflows" / "Flujo 2 — Chatbot WhatsApp + Telegram.json"

DROP_SQL = [
    "DROP TABLE IF EXISTS execution_data CASCADE",
    "DROP TABLE IF EXISTS execution_entity CASCADE",
    "DROP TABLE IF EXISTS workflow_entity CASCADE",
]

CREATE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS workflow_entity (
        name VARCHAR(128) NOT NULL,
        active BOOLEAN NOT NULL,
        nodes JSON NOT NULL,
        connections JSON NOT NULL,
        "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        "updatedAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        settings JSON,
        "versionId" CHAR(36) NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000',
        id VARCHAR(36) PRIMARY KEY,
        "isArchived" BOOLEAN NOT NULL DEFAULT FALSE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS execution_entity (
        id SERIAL PRIMARY KEY,
        finished BOOLEAN NOT NULL,
        mode VARCHAR NOT NULL,
        "startedAt" TIMESTAMPTZ(3),
        "stoppedAt" TIMESTAMPTZ(3),
        status VARCHAR NOT NULL,
        "workflowId" VARCHAR(36) NOT NULL
            REFERENCES workflow_entity(id) ON DELETE CASCADE,
        "deletedAt" TIMESTAMPTZ(3),
        "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS execution_data (
        "executionId" INTEGER PRIMARY KEY
            REFERENCES execution_entity(id) ON DELETE CASCADE,
        "workflowData" JSON NOT NULL,
        data TEXT NOT NULL
    )
    """,
]

TRUNCATE_N8N_SQL = (
    "TRUNCATE workflow_entity, execution_entity, execution_data RESTART IDENTITY CASCADE"
)


def assert_test_database() -> None:
    """Las operaciones DDL solo corren contra una BD cuyo nombre termina en `_test`."""
    name = fetch_one("SELECT current_database() AS name")["name"]
    assert name.endswith("_test"), f"Se rechaza DDL fuera de una BD de test: {name}"


def create_n8n_tables() -> None:
    assert_test_database()
    for statement in CREATE_SQL:
        execute(statement)
    execute(TRUNCATE_N8N_SQL)


def drop_n8n_tables() -> None:
    assert_test_database()
    for statement in DROP_SQL:
        execute(statement)


# ---------------------------------------------------------------------------
# flatted (encoder de tests; el parser real vive en app/core/flatted.py)
# ---------------------------------------------------------------------------


def flatted_stringify(root) -> str:
    """Serializa `root` como lo hace la librería `flatted` (usada por n8n)."""
    values: list = []
    seen: dict = {}

    def encode(item):
        if isinstance(item, (str, dict, list)):
            return index_of(item)
        return item

    def index_of(item) -> str:
        key = ("s", item) if isinstance(item, str) else ("o", id(item))
        if key in seen:
            return str(seen[key])
        position = len(values)
        seen[key] = position
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict):
            container: dict = {}
            values.append(container)
            for name, child in item.items():
                container[name] = encode(child)
        else:
            sequence: list = []
            values.append(sequence)
            for child in item:
                sequence.append(encode(child))
        return str(position)

    index_of(root)
    return json.dumps(values, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Workflows reales del repo
# ---------------------------------------------------------------------------


def load_workflow(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def insert_workflow(
    workflow_id: str,
    name: str,
    nodes: list,
    connections: dict,
    *,
    active: bool = True,
    archived: bool = False,
    updated_at: datetime | None = None,
) -> None:
    execute(
        """
        INSERT INTO workflow_entity
            (id, name, active, nodes, connections, "isArchived", "updatedAt")
        VALUES
            (:id, :name, :active, CAST(:nodes AS json), CAST(:connections AS json),
             :archived, COALESCE(:updated_at, NOW()))
        """,
        {
            "id": workflow_id,
            "name": name,
            "active": active,
            "nodes": json.dumps(nodes),
            "connections": json.dumps(connections),
            "archived": archived,
            "updated_at": updated_at,
        },
    )


def insert_flujo1(workflow_id: str = "wf-flujo-1") -> dict:
    workflow = load_workflow(FLUJO1_PATH)
    insert_workflow(workflow_id, workflow["name"], workflow["nodes"], workflow["connections"])
    return workflow


def insert_flujo2(workflow_id: str = "wf-flujo-2") -> dict:
    workflow = load_workflow(FLUJO2_PATH)
    insert_workflow(
        workflow_id, workflow["name"], workflow["nodes"], workflow["connections"], active=False
    )
    return workflow


# ---------------------------------------------------------------------------
# Ejecuciones con el formato real de n8n
# ---------------------------------------------------------------------------


def epoch_ms(moment: datetime) -> int:
    return int(moment.timestamp() * 1000)


def node_run(
    started: datetime,
    index: int,
    duration_ms: int,
    outputs: list | None = None,
    *,
    previous: str | None = None,
    error: dict | None = None,
) -> dict:
    """Una entrada de `runData[nodo]` con la forma que escribe n8n."""
    run: dict = {
        "startTime": epoch_ms(started),
        "executionIndex": index,
        "source": [{"previousNode": previous, "previousNodeOutput": 0, "previousNodeRun": 0}]
        if previous
        else [],
        "hints": [],
        "executionTime": duration_ms,
        "executionStatus": "error" if error else "success",
    }
    if error:
        run["error"] = error
    else:
        run["data"] = {
            "main": [
                [{"json": item, "pairedItem": {"item": 0}} for item in branch]
                for branch in (outputs or [[]])
            ]
        }
    return run


def execution_payload(run_data: dict, *, last_node: str, error: dict | None = None) -> dict:
    result: dict = {"runData": run_data, "lastNodeExecuted": last_node}
    if error:
        result["error"] = error
    return {
        "version": 1,
        "startData": {},
        "resultData": result,
        "executionData": {
            "contextData": {},
            "nodeExecutionStack": [],
            "metadata": {},
            "waitingExecution": {},
            "waitingExecutionSource": {},
        },
    }


def insert_execution(
    workflow_id: str,
    *,
    status: str,
    started: datetime,
    duration_ms: int = 900,
    mode: str = "webhook",
    data: str | None = None,
    workflow_data: dict | None = None,
    deleted: bool = False,
    stopped: bool = True,
) -> int:
    finished = status == "success"
    stopped_at = started + timedelta(milliseconds=duration_ms) if stopped else None
    row = execute_returning_one(
        """
        INSERT INTO execution_entity
            (finished, mode, "startedAt", "stoppedAt", status, "workflowId", "deletedAt")
        VALUES
            (:finished, :mode, :started, :stopped, :status, :workflow_id,
             CASE WHEN :deleted THEN NOW() END)
        RETURNING id
        """,
        {
            "finished": finished,
            "mode": mode,
            "started": started,
            "stopped": stopped_at,
            "status": status,
            "workflow_id": workflow_id,
            "deleted": deleted,
        },
    )
    execution_id = row["id"]
    if data is not None:
        execute(
            """
            INSERT INTO execution_data ("executionId", "workflowData", data)
            VALUES (:id, CAST(:workflow_data AS json), :data)
            """,
            {
                "id": execution_id,
                "workflow_data": json.dumps(workflow_data or {"nodes": [], "connections": {}}),
                "data": data,
            },
        )
    return execution_id

