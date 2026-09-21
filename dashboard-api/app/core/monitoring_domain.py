"""Dominios cerrados de las tablas de negocio (espejo de los CHECK de init_simple.sql)."""

from typing import Literal

Channel = Literal["whatsapp", "telegram", "email"]
DataSource = Literal["measured", "synthetic", "e4_manual"]

CHANNELS: tuple[str, ...] = ("whatsapp", "telegram", "email")
INTENTS: tuple[str, ...] = ("FAQ", "ESTADO_PEDIDO", "RECLAMO", "GENERAL")
ORDER_STATUSES: tuple[str, ...] = (
    "pending",
    "processing",
    "confirmed",
    "shipped",
    "delivered",
    "no_stock",
    "cancelled",
    "error",
)
TICKET_PRIORITIES: tuple[str, ...] = ("low", "normal", "high", "urgent")
