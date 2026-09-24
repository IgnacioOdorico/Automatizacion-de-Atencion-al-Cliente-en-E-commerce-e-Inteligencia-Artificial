"""Chat de demostración de la landing: hablarle al asistente sin tener cuenta.

Quien mira la presentación escribe una consulta y recibe la respuesta real del
asistente, no una grabada. El camino es el mismo que el de un cliente por WhatsApp:
el mensaje entra al motor de flujos por su webhook, el motor clasifica la intención,
arma la respuesta y la deja escrita en `interactions`. Acá se dispara ese webhook y
se espera esa fila.

Por qué se espera en vez de leer la respuesta del webhook: el flujo del chatbot
termina en «Registrar Interacción», no en un nodo de respuesta, así que el webhook
contesta «Workflow was started» y nada más. La respuesta del asistente solo existe
cuando el flujo la escribió.

Aislamiento: cada visitante recibe un identificador propio derivado de su sesión
(`demo-<sesión>@whatsapp.sim`) y la espera filtra por ese identificador exacto. No
hay forma de leer la conversación de otro visitante ni las interacciones del corpus
de la tesis, que no llevan el prefijo `demo-`.

El sufijo `@whatsapp.sim` no es decorativo: el flujo enruta el canal por él.
"""
import re
import threading
import time

import httpx
from fastapi import HTTPException

from app import db
from app.core.config import settings

RUTA_WEBHOOK = "/webhook/whatsapp-business"
PREFIJO_SESION = "demo-"
SUFIJO_USUARIO = "@whatsapp.sim"
NOMBRE_VISITANTE = "Visitante"

MAX_MENSAJE_CARACTERES = 500
# Una sesión de la sesión de la landing: 8 a 40 caracteres, minúsculas y dígitos.
# Es un identificador opaco que genera el navegador, no un dato de nadie.
PATRON_SESION = re.compile(r"^[a-z0-9]{8,40}$")

# El asistente tarda entre 1 y 5 segundos con GPT-4o-mini; el margen cubre un
# arranque en frío del motor sin dejar la pestaña colgada para siempre.
ESPERA_MAXIMA_SEGUNDOS = 45.0
INTERVALO_SONDEO_SEGUNDOS = 0.4

MAX_MENSAJES_POR_VENTANA = 12
VENTANA_SEGUNDOS = 300

# Los detalles del fallo (host, puerto, excepción) se quedan del lado del servidor:
# el endpoint es público y un mensaje de error es un mapa de la infraestructura.
DETALLE_MOTOR_CAIDO = (
    "El asistente no está disponible en este momento. Probá de nuevo en un minuto."
)
DETALLE_SIN_RESPUESTA = (
    "El asistente tardó más de lo esperado en responder. Probá con otra consulta."
)
DETALLE_DEMASIADOS = (
    "Demasiadas consultas seguidas. Esperá un momento antes de escribir otra."
)


def usuario_de_sesion(sesion: str) -> str:
    """Identificador del visitante para el motor de flujos."""
    return f"{PREFIJO_SESION}{sesion}{SUFIJO_USUARIO}"


def crear_cliente() -> httpx.Client:
    """Punto de sustitución en las pruebas: nunca salen a la red."""
    return httpx.Client(timeout=10.0)


# --------------------------------------------------------------------------- límite de uso

_usos: dict[str, list[float]] = {}
_candado = threading.Lock()


def _podar(clave: str, ahora: float) -> list[float]:
    recientes = [t for t in _usos.get(clave, []) if t > ahora - VENTANA_SEGUNDOS]
    if recientes:
        _usos[clave] = recientes
    else:
        _usos.pop(clave, None)  # sin buckets vacíos: la memoria no crece con claves viejas
    return recientes


def registrar_uso(*claves: str) -> bool:
    """Anota un mensaje y devuelve False si alguna clave superó su cupo.

    Se cuenta por sesión y por IP: una pestaña no puede inundar el motor, y tampoco
    puede hacerlo alguien rotando el identificador de sesión desde la misma máquina.
    Cuando una clave está al tope no se anota ninguna, para que el bloqueo de una no
    consuma el cupo de la otra.
    """
    ahora = time.monotonic()
    with _candado:
        for clave in claves:
            if len(_podar(clave, ahora)) >= MAX_MENSAJES_POR_VENTANA:
                return False
        for clave in claves:
            _usos.setdefault(clave, []).append(ahora)
    return True


def reset_limite() -> None:
    with _candado:
        _usos.clear()


# --------------------------------------------------------------------------- motor de flujos


def disparar(user_id: str, mensaje: str) -> None:
    """Entrega el mensaje al motor. Traduce cualquier falla a un 503 sin detalles."""
    url = settings.dashboard_n8n_url.rstrip("/") + RUTA_WEBHOOK
    cuerpo = {
        "from": user_id,
        "name": NOMBRE_VISITANTE,
        "text": {"body": mensaje},
    }
    try:
        with crear_cliente() as cliente:
            respuesta = cliente.post(url, json=cuerpo)
    except httpx.HTTPError as exc:
        # El nombre de la excepción se pierde a propósito: no describe nada útil a
        # quien mira la landing y sí describe la red a quien no debería verla.
        raise HTTPException(status_code=503, detail=DETALLE_MOTOR_CAIDO) from exc
    # 404 = el flujo del chatbot está importado pero inactivo; 5xx = el motor falló.
    if respuesta.status_code >= 400:
        raise HTTPException(status_code=503, detail=DETALLE_MOTOR_CAIDO)


# --------------------------------------------------------------------------- espera


def ultimo_id(user_id: str) -> int:
    """Último mensaje ya registrado de este visitante, para no devolverlo de nuevo."""
    fila = db.fetch_one(
        "SELECT COALESCE(MAX(id), 0) AS ultimo FROM interactions WHERE user_id = :uid",
        {"uid": user_id},
    )
    return int(fila["ultimo"]) if fila else 0


def _buscar_respuesta(user_id: str, desde_id: int) -> dict | None:
    return db.fetch_one(
        """
        SELECT id,
               ai_response,
               intent,
               EXTRACT(EPOCH FROM (responded_at - received_at)) AS segundos
          FROM interactions
         WHERE user_id = :uid
           AND id > :desde
           AND ai_response IS NOT NULL
         ORDER BY id ASC
         LIMIT 1
        """,
        {"uid": user_id, "desde": desde_id},
    )


def esperar_respuesta(
    user_id: str,
    desde_id: int,
    *,
    ahora=time.monotonic,
    dormir=time.sleep,
) -> dict | None:
    """Sondea hasta que el flujo escriba la respuesta, o hasta agotar la espera."""
    limite = ahora() + ESPERA_MAXIMA_SEGUNDOS
    while True:
        fila = _buscar_respuesta(user_id, desde_id)
        if fila is not None:
            return fila
        if ahora() >= limite:
            return None
        dormir(INTERVALO_SONDEO_SEGUNDOS)


# --------------------------------------------------------------------------- métricas públicas

CLAVES_PROMEDIO = ("avg_mttd_seconds", "avg_mttr_seconds", "avg_tmr_seconds")


def estadisticas() -> dict:
    """Contadores agregados para la landing. Solo números: ningún dato de personas.

    Los totales cuentan todo lo que hay en la instalación. Los promedios, en cambio,
    se acotan a `data_source = 'measured'`: sin ese filtro el promedio mezclaría el
    baseline manual cronometrado (`e4_manual`, del orden de los minutos) con el
    pipeline automático y daría una cifra que no describe ni a uno ni a otro.
    """
    fila = db.fetch_one(
        """
        SELECT (SELECT count(*) FROM orders)                       AS orders,
               (SELECT count(*) FROM interactions)                 AS interactions,
               (SELECT count(*) FROM tickets)                      AS tickets,
               (SELECT count(*) FROM products)                     AS products,
               (SELECT avg(EXTRACT(EPOCH FROM (processed_at - received_at)))
                  FROM orders WHERE processed_at IS NOT NULL
                               AND data_source = 'measured')       AS avg_mttd_seconds,
               (SELECT avg(EXTRACT(EPOCH FROM (notified_at - processed_at)))
                  FROM orders WHERE notified_at IS NOT NULL
                               AND processed_at IS NOT NULL
                               AND data_source = 'measured')       AS avg_mttr_seconds,
               (SELECT avg(EXTRACT(EPOCH FROM (responded_at - received_at)))
                  FROM interactions WHERE responded_at IS NOT NULL
                                      AND data_source = 'measured') AS avg_tmr_seconds
        """
    )
    salida: dict[str, int | float | None] = {}
    for clave, valor in (fila or {}).items():
        if valor is None:
            salida[clave] = None  # sin datos todavía; la landing muestra un guión
        elif clave in CLAVES_PROMEDIO:
            # avg() en PostgreSQL vuelve como Decimal: no es serializable a JSON tal cual.
            salida[clave] = round(float(valor), 3)
        else:
            salida[clave] = int(valor)
    return salida
