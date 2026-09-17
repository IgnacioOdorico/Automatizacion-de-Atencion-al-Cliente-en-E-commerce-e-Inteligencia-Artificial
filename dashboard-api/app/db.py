from sqlalchemy import Engine, create_engine, text

from app.core.config import settings

engine: Engine = create_engine(settings.database_url, pool_pre_ping=True)


def ping() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def fetch_all(query: str, params: dict | None = None) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row) for row in result.mappings()]


def fetch_one(query: str, params: dict | None = None) -> dict | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute(query: str, params: dict | None = None) -> int:
    with engine.begin() as conn:
        result = conn.execute(text(query), params or {})
        return result.rowcount


def execute_returning_one(query: str, params: dict | None = None) -> dict | None:
    with engine.begin() as conn:
        result = conn.execute(text(query), params or {})
        row = result.mappings().first()
        return dict(row) if row else None