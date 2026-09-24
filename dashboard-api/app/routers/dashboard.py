from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_account_id
from app.db import fetch_one

router = APIRouter(tags=["dashboard"])

METRIC_KEYS = [
    "total_orders",
    "orders_confirmed",
    "avg_mttd_seg",
    "avg_mttr_seg",
    "total_interactions",
    "avg_tmr_seg",
    "total_tickets",
    "tickets_resolved",
]

MEASURED_AGGREGATES = """
SELECT
    (SELECT COUNT(*) FROM orders WHERE data_source = :source) AS total_orders,
    (SELECT COUNT(*) FROM orders
     WHERE status = 'confirmed' AND data_source = :source) AS orders_confirmed,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::NUMERIC, 2)
     FROM orders WHERE processed_at IS NOT NULL AND data_source = :source) AS avg_mttd_seg,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (notified_at - processed_at)))::NUMERIC, 2)
     FROM orders WHERE notified_at IS NOT NULL AND data_source = :source) AS avg_mttr_seg,
    (SELECT COUNT(*) FROM interactions WHERE data_source = :source) AS total_interactions,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))::NUMERIC, 2)
     FROM interactions WHERE responded_at IS NOT NULL AND data_source = :source) AS avg_tmr_seg,
    (SELECT COUNT(*) FROM tickets WHERE data_source = :source) AS total_tickets,
    (SELECT COUNT(*) FROM tickets
     WHERE status = 'resolved' AND data_source = :source) AS tickets_resolved
"""


def _summary(data_source: str | None) -> dict:
    if data_source:
        metrics = fetch_one(MEASURED_AGGREGATES, {"source": data_source})
        source_clause = "AND data_source = :source"
        params = {"source": data_source}
    else:
        metrics = fetch_one(
            f"SELECT {', '.join(METRIC_KEYS)} FROM v_metrics_summary"
        )
        source_clause = ""
        params = {}

    orders_today = fetch_one(
        f"""
        SELECT COUNT(*) AS c FROM orders
        WHERE received_at >= date_trunc('day', now()) {source_clause}
        """,
        params,
    )["c"]
    tickets_open = fetch_one(
        f"""
        SELECT COUNT(*) AS c FROM tickets
        WHERE status IN ('open', 'in_progress') {source_clause}
        """,
        params,
    )["c"]

    summary = {key: (0 if metrics[key] is None else metrics[key]) for key in METRIC_KEYS}
    summary["orders_today"] = orders_today
    summary["tickets_open"] = tickets_open
    summary["data_source"] = data_source or "all"
    return summary


@router.get("/dashboard/summary")
def dashboard_summary(
    data_source: str | None = Query(default=None),
    account_id: int = Depends(get_current_account_id),
) -> dict:
    return _summary(data_source)