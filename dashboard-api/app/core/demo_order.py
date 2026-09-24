"""Disparar un pedido real desde la landing, para mostrar el pipeline funcionando.

El botón de la landing entra por el mismo webhook que usaría la tienda: no hay un
camino de demostración aparte. Lo que se ve en pantalla —el estado del pedido y sus
tiempos— sale de la fila que escribió el pipeline, no de un valor que arme esta capa.

Dos escenarios, los dos interesantes de mostrar:
  con_stock  una unidad del producto con más stock. El pipeline confirma, descuenta
             y notifica.
  sin_stock  más unidades de las que hay. El pipeline marca el pedido como sin stock
             y avisa, en vez de vender de más. Es el caso que justifica el sistema.

El número de pedido lleva el prefijo `ORD-WEB-`, que ninguna corrida de la tesis usa
(esas van con ORD-E1A-, ORD-E1B- y ORD-E4-): un pedido de demostración nunca puede
mezclarse con los datos medidos.
"""
import secrets
import time

import httpx
from fastapi import HTTPException

from app import db
from app.core.config import settings

RUTA_WEBHOOK = "/webhook/orden-nueva"
PREFIJO_PEDIDO = "ORD-WEB-"
CLIENTE_DEMO = "Cliente de la demostración"
EMAIL_DEMO = "demo@techstore.com.ar"

ESCENARIOS = ("con_stock", "sin_stock")
# Cuánto se pide de más en el escenario sin stock: suficiente para que ningún
# producto del catálogo lo cubra, sin llegar a un total absurdo en pantalla.
EXCEDENTE_SIN_STOCK = 50

ESPERA_MAXIMA_SEGUNDOS = 20.0
INTERVALO_SONDEO_SEGUNDOS = 0.25

DETALLE_MOTOR_CAIDO = (
    "El sistema de pedidos no está disponible en este momento. Probá de nuevo en un minuto."
)
DETALLE_SIN_CATALOGO = "No hay productos cargados para simular un pedido."
DETALLE_SIN_REGISTRO = (
    "El pedido se envió pero todavía no quedó registrado. Miralo en el panel en unos segundos."
)


def crear_cliente() -> httpx.Client:
    """Punto de sustitución en las pruebas: nunca salen a la red."""
    return httpx.Client(timeout=30.0)


def nuevo_numero() -> str:
    """Número irrepetible y legible en pantalla."""
    return PREFIJO_PEDIDO + secrets.token_hex(4).upper()


def producto_para_la_demo() -> dict:
    """El de más stock: apretar el botón muchas veces no deja el catálogo en cero."""
    fila = db.fetch_one(
        "SELECT id, sku, name, price, stock FROM products ORDER BY stock DESC, id ASC LIMIT 1"
    )
    if fila is None:
        raise HTTPException(status_code=503, detail=DETALLE_SIN_CATALOGO)
    return fila


def cantidad_para(escenario: str, stock: int) -> int:
    return 1 if escenario == "con_stock" else max(int(stock), 0) + EXCEDENTE_SIN_STOCK


def disparar(numero: str, producto: dict, cantidad: int) -> None:
    """Entrega el pedido al pipeline. Cualquier falla se traduce a un 503 sin detalles."""
    url = settings.dashboard_n8n_url.rstrip("/") + RUTA_WEBHOOK
    cuerpo = {
        "order_number": numero,
        "customer_name": CLIENTE_DEMO,
        "customer_email": EMAIL_DEMO,
        "customer_phone": "5492610000000",
        "product_sku": producto["sku"],
        "quantity": cantidad,
    }
    try:
        with crear_cliente() as cliente:
            respuesta = cliente.post(url, json=cuerpo)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=DETALLE_MOTOR_CAIDO) from exc
    if respuesta.status_code >= 400:
        raise HTTPException(status_code=503, detail=DETALLE_MOTOR_CAIDO)


def esperar_pedido(numero: str, *, ahora=time.monotonic, dormir=time.sleep) -> dict | None:
    """Sondea hasta que el pipeline deje la fila escrita, o hasta agotar la espera."""
    consulta = """
        SELECT order_number, status, quantity, total_amount,
               EXTRACT(EPOCH FROM (processed_at - received_at)) AS mttd,
               EXTRACT(EPOCH FROM (notified_at - processed_at)) AS mttr,
               EXTRACT(EPOCH FROM (notified_at - received_at))  AS end_to_end
          FROM orders
         WHERE order_number = :num
    """
    limite = ahora() + ESPERA_MAXIMA_SEGUNDOS
    while True:
        fila = db.fetch_one(consulta, {"num": numero})
        if fila is not None:
            return fila
        if ahora() >= limite:
            return None
        dormir(INTERVALO_SONDEO_SEGUNDOS)
