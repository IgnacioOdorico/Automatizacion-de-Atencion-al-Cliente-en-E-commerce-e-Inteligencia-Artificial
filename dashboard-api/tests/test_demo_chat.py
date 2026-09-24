"""Chat de demostración de la landing: `POST /demo/chat` y `GET /demo/stats`.

Es el único par de endpoints públicos (sin JWT) fuera de `/auth/*`: la landing los
usa para que quien mira la presentación escriba una consulta y reciba la respuesta
real del asistente. Por eso acá se prueba, además del camino feliz, que no se pueda
usar para leer la conversación de otra persona ni para inundar el motor de mensajes.

El motor de flujos se simula con `httpx.MockTransport` (mismo patrón que
`test_gmail_oauth.py`): estas pruebas nunca salen a la red.
"""
import httpx
import pytest
from sqlalchemy import text

from app.core import demo_chat
from app.db import engine

pytestmark = pytest.mark.integration

SESION = "abc123def456"
USUARIO = "demo-abc123def456@whatsapp.sim"


# --------------------------------------------------------------------------- utilidades


def _motor(respuesta=202, al_recibir=None):
    """Motor de flujos simulado. `al_recibir` corre con el cuerpo del pedido."""

    def handler(request: httpx.Request) -> httpx.Response:
        if al_recibir is not None:
            al_recibir(request)
        if isinstance(respuesta, Exception):
            raise respuesta
        return httpx.Response(respuesta, json={"message": "Workflow was started"})

    return httpx.Client(transport=httpx.MockTransport(handler), timeout=5.0)


def _registrar_interaccion(user_id, mensaje, respuesta, intent="FAQ", segundos=1.5):
    """Escribe la interacción que el motor de flujos habría dejado al responder."""
    with engine.begin() as conn:
        fila = conn.execute(
            text(
                """
                INSERT INTO interactions
                    (user_id, channel, message, ai_response, intent,
                     received_at, responded_at, data_source)
                VALUES
                    (:uid, 'whatsapp', :msg, :resp, :intent,
                     NOW() - make_interval(secs => :seg), NOW(), 'measured')
                RETURNING id
                """
            ),
            {
                "uid": user_id,
                "msg": mensaje,
                "resp": respuesta,
                "intent": intent,
                "seg": segundos,
            },
        ).scalar_one()
    return fila


@pytest.fixture(autouse=True)
def _limpiar_limite():
    demo_chat.reset_limite()
    yield
    demo_chat.reset_limite()


# --------------------------------------------------------------------------- user_id


def test_el_usuario_de_la_sesion_termina_en_el_sufijo_que_espera_el_flujo():
    # El Flujo 2 enruta por el sufijo del identificador: sin él no clasifica el canal.
    assert demo_chat.usuario_de_sesion(SESION) == USUARIO
    assert demo_chat.usuario_de_sesion(SESION).endswith("@whatsapp.sim")


def test_dos_sesiones_distintas_son_dos_usuarios_distintos():
    assert demo_chat.usuario_de_sesion("aaa111bbb222") != demo_chat.usuario_de_sesion(
        "ccc333ddd444"
    )


# --------------------------------------------------------------------------- camino feliz


def test_chat_devuelve_la_respuesta_real_del_asistente(client, monkeypatch):
    enviados = []

    def al_recibir(request):
        enviados.append(request)
        # El motor responde enseguida; la interacción la escribe el flujo después.
        _registrar_interaccion(
            USUARIO, "¿Hacen envíos a Mendoza?", "Sí, llegan en 1 a 3 días hábiles.",
            intent="FAQ", segundos=1.42,
        )

    monkeypatch.setattr(demo_chat, "crear_cliente", lambda: _motor(al_recibir=al_recibir))

    r = client.post(
        "/demo/chat", json={"message": "¿Hacen envíos a Mendoza?", "session": SESION}
    )

    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["reply"] == "Sí, llegan en 1 a 3 días hábiles."
    assert cuerpo["intent"] == "FAQ"
    assert cuerpo["seconds"] == pytest.approx(1.42, abs=0.2)
    # El mensaje viaja al motor con el identificador de la sesión, no con uno fijo.
    assert enviados and enviados[0].url.path.endswith("/webhook/whatsapp-business")
    import json as _json

    payload = _json.loads(enviados[0].content)
    assert payload["from"] == USUARIO
    assert payload["text"]["body"] == "¿Hacen envíos a Mendoza?"


def test_solo_devuelve_interacciones_posteriores_al_pedido(client, monkeypatch):
    # Una respuesta vieja de la MISMA sesión no se puede colar como si fuera la nueva.
    _registrar_interaccion(USUARIO, "hola", "RESPUESTA VIEJA")

    def al_recibir(_request):
        _registrar_interaccion(USUARIO, "y el pedido?", "RESPUESTA NUEVA", intent="ESTADO_PEDIDO")

    monkeypatch.setattr(demo_chat, "crear_cliente", lambda: _motor(al_recibir=al_recibir))

    r = client.post("/demo/chat", json={"message": "y el pedido?", "session": SESION})

    assert r.status_code == 200
    assert r.json()["reply"] == "RESPUESTA NUEVA"


def test_nunca_devuelve_la_conversacion_de_otra_sesion(client, monkeypatch):
    otro = demo_chat.usuario_de_sesion("zzz999yyy888")

    def al_recibir(_request):
        _registrar_interaccion(otro, "privado", "ESTO ES DE OTRA PERSONA")

    monkeypatch.setattr(demo_chat, "crear_cliente", lambda: _motor(al_recibir=al_recibir))
    monkeypatch.setattr(demo_chat, "ESPERA_MAXIMA_SEGUNDOS", 0.3)

    r = client.post("/demo/chat", json={"message": "hola", "session": SESION})

    assert r.status_code == 504
    assert "ESTO ES DE OTRA PERSONA" not in r.text


def test_nunca_devuelve_una_interaccion_ajena_a_la_demo(client, monkeypatch):
    # Las 2540 interacciones del corpus no llevan prefijo `demo-`: no se pueden leer.
    def al_recibir(_request):
        _registrar_interaccion("5492610000999@whatsapp.sim", "corpus", "DATO DEL CORPUS")

    monkeypatch.setattr(demo_chat, "crear_cliente", lambda: _motor(al_recibir=al_recibir))
    monkeypatch.setattr(demo_chat, "ESPERA_MAXIMA_SEGUNDOS", 0.3)

    r = client.post("/demo/chat", json={"message": "hola", "session": SESION})

    assert r.status_code == 504
    assert "DATO DEL CORPUS" not in r.text


# --------------------------------------------------------------------------- validación


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"message": "", "session": SESION},
        {"message": "   ", "session": SESION},
        {"message": "x" * 501, "session": SESION},
        {"message": "hola"},
        {"session": SESION},
        {"message": "hola", "session": "corta"},
        {"message": "hola", "session": "tiene espacios aca"},
        {"message": "hola", "session": "MAYUSCULAS1234"},
        {"message": "hola", "session": "punto.y.coma;"},
    ],
)
def test_pedidos_invalidos_no_llegan_al_motor(client, monkeypatch, cuerpo):
    llamadas = []
    monkeypatch.setattr(
        demo_chat, "crear_cliente", lambda: _motor(al_recibir=llamadas.append)
    )

    r = client.post("/demo/chat", json=cuerpo)

    assert r.status_code == 422, r.text
    assert llamadas == []


# --------------------------------------------------------------------------- fallas


def test_si_el_motor_no_responde_devuelve_503_y_no_filtra_el_detalle(client, monkeypatch):
    monkeypatch.setattr(
        demo_chat,
        "crear_cliente",
        lambda: _motor(respuesta=httpx.ConnectError("conexión rechazada en 10.0.0.7:5678")),
    )

    r = client.post("/demo/chat", json={"message": "hola", "session": SESION})

    assert r.status_code == 503
    assert "10.0.0.7" not in r.text
    assert "ConnectError" not in r.text


def test_si_el_flujo_esta_apagado_el_404_del_motor_se_traduce(client, monkeypatch):
    monkeypatch.setattr(demo_chat, "crear_cliente", lambda: _motor(respuesta=404))

    r = client.post("/demo/chat", json={"message": "hola", "session": SESION})

    assert r.status_code == 503
    assert "asistente" in r.json()["detail"].lower()


def test_si_la_respuesta_no_llega_a_tiempo_devuelve_504(client, monkeypatch):
    monkeypatch.setattr(demo_chat, "crear_cliente", lambda: _motor())
    monkeypatch.setattr(demo_chat, "ESPERA_MAXIMA_SEGUNDOS", 0.3)

    r = client.post("/demo/chat", json={"message": "hola", "session": SESION})

    assert r.status_code == 504


# --------------------------------------------------------------------------- límite de uso


def test_una_sesion_no_puede_inundar_el_motor(client, monkeypatch):
    llamadas = []

    def al_recibir(request):
        llamadas.append(request)
        _registrar_interaccion(USUARIO, "hola", "respuesta")

    monkeypatch.setattr(demo_chat, "crear_cliente", lambda: _motor(al_recibir=al_recibir))
    monkeypatch.setattr(demo_chat, "MAX_MENSAJES_POR_VENTANA", 3)

    for _ in range(3):
        assert client.post("/demo/chat", json={"message": "hola", "session": SESION}).status_code == 200

    bloqueado = client.post("/demo/chat", json={"message": "hola", "session": SESION})

    assert bloqueado.status_code == 429
    assert len(llamadas) == 3  # el cuarto nunca llegó al motor


# --------------------------------------------------------------------------- métricas públicas


def test_stats_devuelve_agregados_sin_datos_personales(client):
    r = client.get("/demo/stats")

    assert r.status_code == 200
    cuerpo = r.json()
    for clave in ("orders", "interactions", "tickets", "avg_mttd_seconds", "avg_tmr_seconds"):
        assert clave in cuerpo
    # Ningún campo de texto libre: solo números. Nada de nombres, emails ni teléfonos.
    assert all(isinstance(v, (int, float, type(None))) for v in cuerpo.values()), cuerpo


def test_stats_no_necesita_sesion_iniciada(client):
    assert client.get("/demo/stats").status_code == 200


def test_stats_no_mezcla_el_baseline_manual_en_los_promedios(client):
    # El baseline manual se cronometró en minutos; promediarlo con el pipeline
    # automático daría una cifra que no describe a ninguno de los dos.
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO orders
                    (order_number, customer_name, customer_email, product_id, quantity,
                     total_amount, status, received_at, processed_at, notified_at, data_source)
                VALUES
                    ('ORD-AUTO-900', 'Automático', 'a@example.com', 1, 1, 10, 'confirmed',
                     NOW() - INTERVAL '10 seconds', NOW() - INTERVAL '10 seconds' + INTERVAL '2 seconds',
                     NOW() - INTERVAL '10 seconds' + INTERVAL '3 seconds', 'measured'),
                    ('ORD-E4-900', 'Manual', 'm@example.com', 1, 1, 10, 'confirmed',
                     NOW() - INTERVAL '20 minutes', NOW() - INTERVAL '20 minutes' + INTERVAL '600 seconds',
                     NOW() - INTERVAL '20 minutes' + INTERVAL '900 seconds', 'e4_manual')
                """
            )
        )

    cuerpo = client.get("/demo/stats").json()

    assert cuerpo["orders"] >= 2  # el total sí cuenta las dos
    assert cuerpo["avg_mttd_seconds"] < 60  # el promedio, solo la automática
