"""Métricas del negocio (K1/K2): reemplazo en vivo de los paneles de Grafana.

Se separan de `monitoring_*` a propósito: Monitoreo es el feed de eventos y la
traza del workflow (operación), Métricas son los KPIs agregados de la tesis
(MTTD/MTTR/TMR, distribución de estados/intents, series diarias) — mismo rol
que cumplían los dos dashboards de Grafana, ahora en vivo dentro del portal.
"""

from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_account_id
from app.core.metrics import fetch_chatbot_metrics, fetch_order_metrics
from app.core.monitoring_domain import DataSource

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(get_current_account_id)],
)

MAX_HOURS = 8760  # 365 días; ver docs/API_METRICAS.md

# `interactions.data_source` solo admite measured/synthetic (init_simple.sql:113-114);
# `e4_manual` es válido para `orders` pero no existe en `interactions`, así que este
# endpoint usa un dominio propio, más chico que el `DataSource` general.
ChatbotDataSource = Literal["measured", "synthetic"]


@router.get("/orders")
def metrics_orders(
    hours: int | None = Query(default=None, ge=1, le=MAX_HOURS),
    data_source: DataSource | None = Query(default=None),
) -> dict:
    return fetch_order_metrics(hours, data_source)


@router.get("/chatbot")
def metrics_chatbot(
    hours: int | None = Query(default=None, ge=1, le=MAX_HOURS),
    data_source: ChatbotDataSource | None = Query(default=None),
) -> dict:
    return fetch_chatbot_metrics(hours, data_source)
