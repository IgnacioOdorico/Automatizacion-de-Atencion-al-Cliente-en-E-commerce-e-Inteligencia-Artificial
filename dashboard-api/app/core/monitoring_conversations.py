"""Conversaciones del bot: hilos agrupados por `(channel, user_id)` (solo lectura)."""

from app.core.cursors import CursorError, decode_cursor, encode_cursor, to_iso
from app.db import fetch_all, fetch_one

LIST_KIND = "conv"
THREAD_KIND = "msg"
PREVIEW_LENGTH = 120


def preview(text: str | None) -> str:
    """Texto acotado a `PREVIEW_LENGTH` caracteres en total (con `…` si se recortó)."""
    text = text or ""
    if len(text) <= PREVIEW_LENGTH:
        return text
    return text[: PREVIEW_LENGTH - 1] + "…"


def _like_pattern(term: str) -> str:
    """Patrón `ILIKE` con `%` y `_` del usuario tratados como texto (escape `!`)."""
    escaped = term.replace("!", "!!").replace("%", "!%").replace("_", "!_")
    return f"%{escaped}%"


def list_conversations(
    *,
    limit: int,
    before: str | None = None,
    channel: str | None = None,
    q: str | None = None,
    data_source: str | None = None,
) -> dict:
    params: dict = {"fetch": limit + 1}
    where = ["received_at IS NOT NULL"]
    lateral_where = ["i.received_at IS NOT NULL"]
    having = ["TRUE"]
    if channel:
        where.append("channel = :channel")
        params["channel"] = channel
    if data_source:
        where.append("data_source = :data_source")
        lateral_where.append("i.data_source = :data_source")
        params["data_source"] = data_source
    term = (q or "").strip()
    if term:
        having.append(
            "bool_or(message ILIKE :q ESCAPE '!' OR ai_response ILIKE :q ESCAPE '!'"
            " OR user_id ILIKE :q ESCAPE '!')"
        )
        params["q"] = _like_pattern(term)
    if before:
        cur_ts, cur_channel, cur_user = decode_cursor(before, LIST_KIND)
        if not isinstance(cur_channel, str) or not isinstance(cur_user, str):
            raise CursorError("Cursor inválido")
        having.append("(MAX(received_at), channel, user_id) < (:cur_ts, :cur_channel, :cur_user)")
        params.update(cur_ts=cur_ts, cur_channel=cur_channel, cur_user=cur_user)

    rows = fetch_all(
        f"""
        SELECT g.channel, g.user_id, g.last_at, g.messages, g.has_urgent,
               l.intent AS last_intent, l.message AS last_message,
               (SELECT COUNT(*) FROM tickets t
                WHERE t.channel = g.channel AND t.user_id = g.user_id
                  AND t.status IN ('open', 'in_progress')) AS open_tickets
        FROM (
            SELECT channel, user_id, MAX(received_at) AS last_at, COUNT(*) AS messages,
                   COALESCE(bool_or(is_urgent), FALSE) AS has_urgent
            FROM interactions
            WHERE {' AND '.join(where)}
            GROUP BY channel, user_id
            HAVING {' AND '.join(having)}
        ) g
        JOIN LATERAL (
            SELECT i.intent, i.message FROM interactions i
            WHERE i.channel = g.channel AND i.user_id = g.user_id
              AND {' AND '.join(lateral_where)}
            ORDER BY i.received_at DESC, i.id DESC
            LIMIT 1
        ) l ON TRUE
        ORDER BY g.last_at DESC, g.channel DESC, g.user_id DESC
        LIMIT :fetch
        """,
        params,
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [
        {
            "channel": row["channel"],
            "user_id": row["user_id"],
            "last_at": to_iso(row["last_at"]),
            "messages": row["messages"],
            "last_intent": row["last_intent"],
            "last_message_preview": preview(row["last_message"]),
            "has_urgent": row["has_urgent"],
            "open_tickets": row["open_tickets"],
        }
        for row in rows
    ]
    last = rows[-1] if rows else None
    return {
        "items": items,
        "has_more": has_more,
        "next_before": (
            encode_cursor(LIST_KIND, last["last_at"], last["channel"], last["user_id"])
            if has_more and last
            else None
        ),
    }


def thread_exists(channel: str, user_id: str) -> bool:
    row = fetch_one(
        "SELECT 1 AS found FROM interactions WHERE channel = :channel AND user_id = :user_id LIMIT 1",
        {"channel": channel, "user_id": user_id},
    )
    return row is not None


def fetch_thread(*, channel: str, user_id: str, limit: int, before: str | None = None) -> dict:
    """Los `limit` mensajes más nuevos anteriores a `before`, en orden cronológico."""
    params: dict = {"channel": channel, "user_id": user_id, "fetch": limit + 1}
    cursor_clause = ""
    if before:
        cur_ts, cur_id = decode_cursor(before, THREAD_KIND)
        if not isinstance(cur_id, int):
            raise CursorError("Cursor inválido")
        cursor_clause = "AND (i.received_at, i.id) < (:cur_ts, :cur_id)"
        params.update(cur_ts=cur_ts, cur_id=cur_id)

    rows = fetch_all(
        f"""
        SELECT i.id, i.received_at, i.message, i.responded_at, i.ai_response, i.intent,
               COALESCE(i.is_urgent, FALSE) AS is_urgent,
               ROUND(EXTRACT(EPOCH FROM (i.responded_at - i.received_at))::numeric, 3) AS tmr_seconds,
               ord.id AS order_id, ord.order_number, ord.status AS order_status,
               tk.id AS ticket_id, tk.status AS ticket_status, tk.priority AS ticket_priority
        FROM interactions i
        LEFT JOIN orders ord ON ord.id = i.order_id
        LEFT JOIN LATERAL (
            SELECT t.id, t.status, t.priority FROM tickets t
            WHERE t.interaction_id = i.id ORDER BY t.id LIMIT 1
        ) tk ON TRUE
        WHERE i.channel = :channel AND i.user_id = :user_id
          AND i.received_at IS NOT NULL {cursor_clause}
        ORDER BY i.received_at DESC, i.id DESC
        LIMIT :fetch
        """,
        params,
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    rows.reverse()  # cronológico: el más viejo primero
    items = [
        {
            "interaction_id": row["id"],
            "received_at": to_iso(row["received_at"]),
            "message": row["message"],
            "responded_at": to_iso(row["responded_at"]),
            "ai_response": row["ai_response"],
            "intent": row["intent"],
            "is_urgent": row["is_urgent"],
            "tmr_seconds": None if row["tmr_seconds"] is None else float(row["tmr_seconds"]),
            "order": (
                None
                if row["order_id"] is None
                else {
                    "id": row["order_id"],
                    "order_number": row["order_number"],
                    "status": row["order_status"],
                }
            ),
            "ticket": (
                None
                if row["ticket_id"] is None
                else {
                    "id": row["ticket_id"],
                    "status": row["ticket_status"],
                    "priority": row["ticket_priority"],
                }
            ),
        }
        for row in rows
    ]
    oldest = rows[0] if rows else None
    return {
        "channel": channel,
        "user_id": user_id,
        "items": items,
        "has_more": has_more,
        "next_before": (
            encode_cursor(THREAD_KIND, oldest["received_at"], oldest["id"])
            if has_more and oldest
            else None
        ),
    }
