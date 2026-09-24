"""`POST /demo/order`: disparar un pedido real desde la landing.

Es el momento de la demostración: quien mira aprieta un botón, el pedido entra al
pipeline por el mismo webhook que usaría la tienda, y la página muestra los tiempos
reales de ese pedido. Acá se prueba que el pedido sale con un número que no puede
pisar ninguna corrida de la tesis, que el escenario sin stock no descuenta nada, y
que ninguna falla del motor se convierte en un 500.
"""
import httpx
import pytest
from sqlalchemy import text

from app.core import demo_chat, demo_order
from app.db import engine

pytestmark = pytest.mark.integration

SESION = "pedidodemo01"


def _motor(respuesta=200, al_recibir=None, cuerpo=None):
    def handler(request: httpx.Request) -> httpx.Response:
        if al_recibir is not None:
            al_recibir(request)
        if isinstance(respuesta, Exception):
            raise respuesta
        return httpx.Response(respuesta, json=cuerpo or {"success": True})

    return httpx.Client(transport=httpx.MockTransport(handler), timeout=5.0)


def _escribir_orden(numero, producto_id, cantidad, estado):
    """Lo que el pipeline habría dejado escrito al terminar."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO orders
                    (order_number, customer_name, customer_email, product_id, quantity,
                     total_amount, status, received_at, processed_at, notified_at, data_source)
                VALUES
                    (:num, 'Cliente de la demostración', 'demo@techstore.com.ar', :pid, :cant,
                     99.0, :estado, NOW(), NOW() + INTERVAL '40 milliseconds',
                     NOW() + INTERVAL '90 milliseconds', 'measured')
                """
            ),
            {"num": numero, "pid": producto_id, "cant": cantidad, "estado": estado},
        )


def _producto_mas_abundante():
    with engine.begin() as conn:
        return conn.execute(
            text("SELECT id, sku, stock FROM products ORDER BY stock DESC, id ASC LIMIT 1")
        ).mappings().first()


@pytest.fixture(autouse=True)
def _limpiar_limite():
    demo_chat.reset_limite()
    yield
    demo_chat.reset_limite()


# --------------------------------------------------------------------------- número de pedido


def test_el_numero_de_pedido_no_puede_pisar_una_corrida_de_la_tesis():
    # Las corridas medidas usan ORD-E1A-, ORD-E1B-, ORD-E4-. La demo usa lo suyo.
    numeros = {demo_order.nuevo_numero() for _ in range(200)}
    assert len(numeros) == 200, "se repitieron números"
    assert all(n.startswith("ORD-WEB-") for n in numeros)
    assert not any(n.startswith(("ORD-E1A", "ORD-E1B", "ORD-E4")) for n in numeros)


# --------------------------------------------------------------------------- camino feliz


def test_pedido_con_stock_devuelve_los_tiempos_reales_de_ese_pedido(client, monkeypatch, db_ready):
    producto = _producto_mas_abundante()
    enviados = []

    def al_recibir(request):
        import json as _json

        enviados.append(_json.loads(request.content))
        _escribir_orden(enviados[0]["order_number"], producto["id"], 1, "confirmed")

    monkeypatch.setattr(demo_order, "crear_cliente", lambda: _motor(al_recibir=al_recibir))

    r = client.post("/demo/order", json={"session": SESION, "scenario": "con_stock"})

    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["order_number"].startswith("ORD-WEB-")
    assert cuerpo["status"] == "confirmed"
    assert cuerpo["product"] == producto["sku"]
    assert cuerpo["quantity"] == 1
    # Los tiempos salen de la fila, no de un valor inventado por el endpoint.
    assert 0 <= cuerpo["mttd_seconds"] < 1
    assert 0 <= cuerpo["mttr_seconds"] < 1
    assert cuerpo["end_to_end_seconds"] >= cuerpo["mttd_seconds"]
    # El pedido salió con el producto que más stock tiene: la demo no lo agota.
    assert enviados[0]["product_sku"] == producto["sku"]
    assert enviados[0]["quantity"] == 1


def test_pedido_sin_stock_pide_mas_de_lo_que_hay(client, monkeypatch, db_ready):
    producto = _producto_mas_abundante()
    enviados = []

    def al_recibir(request):
        import json as _json

        enviados.append(_json.loads(request.content))
        _escribir_orden(enviados[0]["order_number"], producto["id"], enviados[0]["quantity"], "no_stock")

    monkeypatch.setattr(demo_order, "crear_cliente", lambda: _motor(al_recibir=al_recibir))

    r = client.post("/demo/order", json={"session": SESION, "scenario": "sin_stock"})

    assert r.status_code == 200, r.text
    assert r.json()["status"] == "no_stock"
    assert enviados[0]["quantity"] > producto["stock"], "tiene que pedir más de lo que hay"


# --------------------------------------------------------------------------- validación y fallas


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"session": SESION, "scenario": "cualquiera"},
        {"session": SESION},
        {"scenario": "con_stock"},
        {"session": "mal", "scenario": "con_stock"},
    ],
)
def test_pedidos_invalidos_no_llegan_al_motor(client, monkeypatch, cuerpo, db_ready):
    llamadas = []
    monkeypatch.setattr(demo_order, "crear_cliente", lambda: _motor(al_recibir=llamadas.append))

    assert client.post("/demo/order", json=cuerpo).status_code == 422
    assert llamadas == []


def test_si_el_motor_no_responde_devuelve_503_sin_filtrar_el_detalle(client, monkeypatch, db_ready):
    monkeypatch.setattr(
        demo_order,
        "crear_cliente",
        lambda: _motor(respuesta=httpx.ConnectError("sin ruta a 10.0.0.7:5678")),
    )

    r = client.post("/demo/order", json={"session": SESION, "scenario": "con_stock"})

    assert r.status_code == 503
    assert "10.0.0.7" not in r.text


def test_si_el_pipeline_no_escribio_la_orden_devuelve_504(client, monkeypatch, db_ready):
    # El motor aceptó el pedido pero nada quedó registrado: no se inventa un resultado.
    monkeypatch.setattr(demo_order, "crear_cliente", lambda: _motor())
    monkeypatch.setattr(demo_order, "ESPERA_MAXIMA_SEGUNDOS", 0.3)

    r = client.post("/demo/order", json={"session": SESION, "scenario": "con_stock"})

    assert r.status_code == 504


def test_sin_catalogo_no_se_dispara_nada(client, monkeypatch, db_ready):
    # El catálogo no se borra de verdad: `products` no está en el TRUNCATE del
    # conftest, así que borrarlo dejaría sin datos a todo lo que corra después.
    llamadas = []
    monkeypatch.setattr(demo_order, "crear_cliente", lambda: _motor(al_recibir=llamadas.append))
    monkeypatch.setattr(demo_order.db, "fetch_one", lambda *a, **k: None)

    r = client.post("/demo/order", json={"session": SESION, "scenario": "con_stock"})

    assert r.status_code == 503
    assert llamadas == []


def test_el_boton_no_se_puede_apretar_sin_freno(client, monkeypatch, db_ready):
    producto = _producto_mas_abundante()
    llamadas = []

    def al_recibir(request):
        import json as _json

        datos = _json.loads(request.content)
        llamadas.append(datos)
        _escribir_orden(datos["order_number"], producto["id"], datos["quantity"], "confirmed")

    monkeypatch.setattr(demo_order, "crear_cliente", lambda: _motor(al_recibir=al_recibir))
    monkeypatch.setattr(demo_chat, "MAX_MENSAJES_POR_VENTANA", 2)

    for _ in range(2):
        assert client.post("/demo/order", json={"session": SESION, "scenario": "con_stock"}).status_code == 200

    assert client.post("/demo/order", json={"session": SESION, "scenario": "con_stock"}).status_code == 429
    assert len(llamadas) == 2
