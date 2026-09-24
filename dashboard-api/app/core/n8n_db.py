"""Acceso de solo lectura a las tablas internas de n8n con degradación.

Las tablas `workflow_entity`, `execution_entity` y `execution_data` las crea y
mantiene n8n (2.12.2) en la misma PostgreSQL. Si no existen o el usuario no puede
leerlas, el monitoreo sigue funcionando y solo informa `available: false`.
"""

import logging

from sqlalchemy.exc import ProgrammingError

from app.db import fetch_all

logger = logging.getLogger(__name__)


def n8n_fetch_all(query: str, params: dict | None = None) -> list[dict] | None:
    """Ejecuta una consulta sobre tablas de n8n; `None` si no están disponibles."""
    try:
        return fetch_all(query, params)
    except ProgrammingError as exc:
        logger.warning(
            "Tablas de n8n no disponibles para el monitoreo: %s",
            type(exc.orig).__name__ if exc.orig is not None else type(exc).__name__,
        )
        return None
