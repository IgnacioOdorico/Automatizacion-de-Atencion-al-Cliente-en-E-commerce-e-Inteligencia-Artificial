"""Feed unificado de eventos del bot y del pipeline (solo lectura).

Cada tabla de negocio aporta uno o más tipos de evento. El feed se arma con un
`UNION ALL` de fragmentos y se pagina con keyset sobre `(ts, rk, pk)`:

- `ts`: el instante del evento (con microsegundos de la BD).
- `rk`: rango fijo por tipo de evento; desempata eventos con el mismo `ts`.
- `pk`: clave primaria de la fila de origen.

Todo el SQL es estático (los filtros del usuario van siempre como binds), así que
armar fragmentos con f-strings no introduce entrada del usuario en la consulta.
"""

from dataclasses import dataclass

from app.core.cursors import CursorError, decode_cursor, encode_cursor, to_iso
from app.db import fetch_all

CURSOR_KIND = "ev"
NO_REF = "CAST(NULL AS integer)"


@dataclass(frozen=True)
class EventSpec:
    type: str
    rank: int
    from_sql: str
    ts: str
    pk: str
    data: str
    channel: str | None  # columna de canal; None si el evento no pertenece a un canal
    data_source: str
    order_id: str = NO_REF
    order_number: str = "CAST(NULL AS text)"
    interaction_id: str = NO_REF
    ticket_id: str = NO_REF


_INTERACTION_FROM = """
    interactions i
    LEFT JOIN orders ord ON ord.id = i.order_id
"""
_FIRST_TICKET = "(SELECT t.id FROM tickets t WHERE t.interaction_id = i.id ORDER BY t.id LIMIT 1)"

SPECS: tuple[EventSpec, ...] = (
    EventSpec(
        type="order_received",
        rank=10,
        from_sql="orders o LEFT JOIN products p ON p.id = o.product_id",
        ts="o.received_at",
        pk="o.id",
        channel=None,
        data_source="o.data_source",
        data="""jsonb_build_object(
            'order_number', o.order_number, 'customer_name', o.customer_name,
            'customer_email', o.customer_email, 'quantity', o.quantity,
            'total_amount', o.total_amount, 'product_sku', p.sku,
            'product_name', p.name)""",
        order_id="o.id",
        order_number="o.order_number",
    ),
    EventSpec(
        type="chat_message",
        rank=20,
        from_sql=_INTERACTION_FROM,
        ts="i.received_at",
        pk="i.id",
        channel="i.channel",
        data_source="i.data_source",
        data="jsonb_build_object('user_id', i.user_id, 'message', i.message)",
        order_id="i.order_id",
        order_number="ord.order_number",
        interaction_id="i.id",
        ticket_id=_FIRST_TICKET,
    ),
    EventSpec(
        type="order_processed",
        rank=30,
        from_sql="orders o",
        ts="o.processed_at",
        pk="o.id",
        channel=None,
        data_source="o.data_source",
        data="""jsonb_build_object(
            'order_number', o.order_number, 'status', o.status,
            'total_amount', o.total_amount,
            'mttd_seconds', ROUND(EXTRACT(EPOCH FROM (o.processed_at - o.received_at))::numeric, 3))""",
        order_id="o.id",
        order_number="o.order_number",
    ),
    EventSpec(
        type="bot_reply",
        rank=40,
        from_sql=_INTERACTION_FROM,
        ts="i.responded_at",
        pk="i.id",
        channel="i.channel",
        data_source="i.data_source",
        data="""jsonb_build_object(
            'user_id', i.user_id, 'ai_response', i.ai_response, 'intent', i.intent,
            'is_urgent', COALESCE(i.is_urgent, FALSE),
            'tmr_seconds', ROUND(EXTRACT(EPOCH FROM (i.responded_at - i.received_at))::numeric, 3))""",
        order_id="i.order_id",
        order_number="ord.order_number",
        interaction_id="i.id",
        ticket_id=_FIRST_TICKET,
    ),
    EventSpec(
        type="ticket_created",
        rank=50,
        from_sql="tickets t LEFT JOIN orders ord ON ord.id = t.order_id",
        ts="t.created_at",
        pk="t.id",
        channel="t.channel",
        data_source="t.data_source",
        data="""jsonb_build_object(
            'user_id', t.user_id, 'subject', t.subject, 'priority', t.priority,
            'status', t.status)""",
        order_id="t.order_id",
        order_number="ord.order_number",
        interaction_id="t.interaction_id",
        ticket_id="t.id",
    ),
    EventSpec(
        type="order_notified",
        rank=60,
        from_sql="orders o",
        ts="o.notified_at",
        pk="o.id",
        channel=None,
        data_source="o.data_source",
        data="""jsonb_build_object(
            'order_number', o.order_number, 'status', o.status,
            'mttr_seconds', ROUND(EXTRACT(EPOCH FROM (o.notified_at - o.processed_at))::numeric, 3))""",
        order_id="o.id",
        order_number="o.order_number",
    ),
    EventSpec(
        type="stock_alert",
        rank=70,
        from_sql="""stock_alerts s
            LEFT JOIN products p ON p.id = s.product_id
            LEFT JOIN orders ord ON ord.id = s.order_id""",
        ts="s.created_at",
        pk="s.id",
        channel=None,
        data_source="s.data_source",
        data="""jsonb_build_object(
            'sku', s.sku, 'product_name', p.name, 'stock_actual', s.stock_actual,
            'stock_min', s.stock_min)""",
        order_id="s.order_id",
        order_number="ord.order_number",
    ),
)

EVENT_TYPES: tuple[str, ...] = tuple(spec.type for spec in SPECS)


def severity(event_type: str, data: dict) -> str:
    """Severidad de un evento a partir de su tipo y sus datos exactos."""
    if event_type == "order_processed":
        status = data.get("status")
        if status == "error":
            return "error"
        return "warning" if status in ("no_stock", "cancelled") else "success"
    if event_type == "order_notified":
        return "warning" if data.get("status") in ("no_stock", "cancelled", "error") else "success"
    if event_type == "bot_reply":
        return "warning" if data.get("is_urgent") else "success"
    if event_type == "ticket_created":
        priority = data.get("priority")
        return "error" if priority == "urgent" else "warning" if priority == "high" else "info"
    if event_type == "stock_alert":
        return "error" if data.get("stock_actual") == 0 else "warning"
    return "info"


def _fragment(
    spec: EventSpec,
    *,
    direction: str,
    has_cursor: bool,
    data_source: bool,
    channel: bool,
) -> str:
    conditions = [f"{spec.ts} IS NOT NULL"]
    if data_source:
        conditions.append(f"{spec.data_source} = :data_source")
    if channel and spec.channel:
        conditions.append(f"{spec.channel} = :channel")
    if has_cursor:
        operator = "<" if direction == "DESC" else ">"
        conditions.append(
            f"({spec.ts}, {spec.rank}, {spec.pk}) {operator} (:cur_ts, :cur_rk, :cur_pk)"
        )
    return f"""(
        SELECT {spec.ts} AS ts, {spec.rank} AS rk, {spec.pk} AS pk,
               CAST('{spec.type}' AS text) AS type,
               {f'CAST({spec.channel} AS text)' if spec.channel else 'CAST(NULL AS text)'} AS channel,
               {spec.order_id} AS r_order_id,
               {spec.order_number} AS r_order_number,
               {spec.interaction_id} AS r_interaction_id,
               {spec.ticket_id} AS r_ticket_id,
               {spec.data} AS data
        FROM {spec.from_sql}
        WHERE {' AND '.join(conditions)}
        ORDER BY {spec.ts} {direction}, {spec.pk} {direction}
        LIMIT :fetch
    )"""


def _to_event(row: dict) -> dict:
    data = row["data"]
    event_type = row["type"]
    return {
        "id": f"{event_type}:{row['pk']}",
        "type": event_type,
        "ts": to_iso(row["ts"]),
        "channel": row["channel"],
        "severity": severity(event_type, data),
        "data": data,
        "refs": {
            "order_id": row["r_order_id"],
            "order_number": row["r_order_number"],
            "interaction_id": row["r_interaction_id"],
            "ticket_id": row["r_ticket_id"],
        },
    }


def _cursor_of(row: dict) -> str:
    return encode_cursor(CURSOR_KIND, row["ts"], row["rk"], row["pk"])


def fetch_events(
    *,
    limit: int,
    before: str | None = None,
    since: str | None = None,
    types: list[str] | None = None,
    channel: str | None = None,
    data_source: str | None = None,
) -> dict:
    """Página del feed. `before`/`since` son cursores opacos y no se combinan.

    - Sin cursor o con `before`: los `limit` eventos más nuevos anteriores al cursor.
    - Con `since`: los `limit` eventos MÁS VIEJOS posteriores al cursor (así un
      poller nunca se salta eventos si hay más de `limit`); `has_more` indica si
      quedan más recientes por pedir.
    En ambos casos `items` sale de más nuevo a más viejo.
    """
    cursor_value = before or since
    params: dict = {"fetch": limit + 1}
    if cursor_value is not None:
        cur_ts, cur_rk, cur_pk = decode_cursor(cursor_value, CURSOR_KIND)
        if not isinstance(cur_rk, int) or not isinstance(cur_pk, int):
            raise CursorError("Cursor inválido")
        params.update(cur_ts=cur_ts, cur_rk=cur_rk, cur_pk=cur_pk)
    if data_source:
        params["data_source"] = data_source
    if channel:
        params["channel"] = channel

    wanted = set(types) if types else set(EVENT_TYPES)
    direction = "ASC" if since else "DESC"
    fragments = [
        _fragment(
            spec,
            direction=direction,
            has_cursor=cursor_value is not None,
            data_source=bool(data_source),
            channel=bool(channel),
        )
        for spec in SPECS
        if spec.type in wanted and (not channel or spec.channel)
    ]
    if not fragments:
        return _page([], since_cursor=since, has_more=False)

    rows = fetch_all(
        f"""
        SELECT * FROM ({' UNION ALL '.join(fragments)}) e
        ORDER BY ts {direction}, rk {direction}, pk {direction}
        LIMIT :fetch
        """,
        params,
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    if since:
        rows.reverse()  # ASC -> más nuevo primero
    return _page(rows, since_cursor=since, has_more=has_more)


def _page(rows: list[dict], *, since_cursor: str | None, has_more: bool) -> dict:
    return {
        "items": [_to_event(row) for row in rows],
        "has_more": has_more,
        "newest_cursor": _cursor_of(rows[0]) if rows else since_cursor,
        "oldest_cursor": _cursor_of(rows[-1]) if rows else None,
    }
