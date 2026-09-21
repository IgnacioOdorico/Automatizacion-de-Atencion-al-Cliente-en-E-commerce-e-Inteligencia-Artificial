from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.deps import get_current_account_id
from app.core.n8n_reader import (
    get_execution_trace,
    get_workflow_graph,
    list_executions,
    list_workflows,
)

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    dependencies=[Depends(get_current_account_id)],
)

ExecutionStatus = Literal[
    "canceled", "crashed", "error", "new", "running", "success", "unknown", "waiting"
]
WORKFLOW_ID_PATTERN = r"^[A-Za-z0-9_-]+$"


@router.get("/workflows")
def monitoring_workflows() -> dict:
    return list_workflows()


@router.get("/workflows/{workflow_id}/graph")
def monitoring_workflow_graph(
    workflow_id: str = Path(min_length=1, max_length=36, pattern=WORKFLOW_ID_PATTERN),
) -> dict:
    graph = get_workflow_graph(workflow_id)
    if graph is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow no encontrado"
        )
    return graph


@router.get("/executions")
def monitoring_executions(
    limit: int = Query(default=20, ge=1, le=100),
    before: int | None = Query(default=None, ge=1),
    status_filter: ExecutionStatus | None = Query(default=None, alias="status"),
    workflow_id: str | None = Query(
        default=None, min_length=1, max_length=36, pattern=WORKFLOW_ID_PATTERN
    ),
) -> dict:
    return list_executions(
        limit=limit, before=before, status=status_filter, workflow_id=workflow_id
    )


@router.get("/executions/{execution_id}")
def monitoring_execution_trace(execution_id: int = Path(ge=1)) -> dict:
    trace = get_execution_trace(execution_id)
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ejecución no encontrada"
        )
    return trace
