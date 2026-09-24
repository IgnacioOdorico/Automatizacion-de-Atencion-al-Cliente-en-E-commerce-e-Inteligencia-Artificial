"""Endpoints públicos de la landing: probar el asistente y mostrar los contadores.

Son los únicos endpoints sin JWT fuera de `/auth/*` y `/connections/telegram/confirm`.
Por eso: solo lectura de agregados, límite de uso por sesión y por IP, tope de largo
del mensaje y ningún dato de personas en la respuesta. La lógica vive en
`app/core/demo_chat.py`; acá queda el contrato HTTP.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.core import demo_chat, demo_order
from app.core.client_ip import get_client_ip

router = APIRouter(prefix="/demo", tags=["demo"])


def _con_cupo(sesion: str, request: Request) -> None:
    """Mismo freno para las dos acciones públicas: por sesión y por IP."""
    ip = get_client_ip(request)
    if not demo_chat.registrar_uso(f"sesion:{sesion}", f"ip:{ip}"):
        raise HTTPException(status_code=429, detail=demo_chat.DETALLE_DEMASIADOS)


class ConsultaDemo(BaseModel):
    message: str = Field(max_length=demo_chat.MAX_MENSAJE_CARACTERES)
    session: str = Field(max_length=40)

    @field_validator("message")
    @classmethod
    def _mensaje_con_contenido(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio:
            raise ValueError("el mensaje no puede estar vacío")
        return limpio

    @field_validator("session")
    @classmethod
    def _sesion_opaca(cls, valor: str) -> str:
        if not demo_chat.PATRON_SESION.fullmatch(valor):
            raise ValueError("identificador de sesión inválido")
        return valor


class RespuestaDemo(BaseModel):
    reply: str
    intent: str | None
    seconds: float | None


@router.post("/chat", response_model=RespuestaDemo)
def chat(consulta: ConsultaDemo, request: Request) -> RespuestaDemo:
    """Manda la consulta al asistente y devuelve su respuesta real."""
    _con_cupo(consulta.session, request)

    user_id = demo_chat.usuario_de_sesion(consulta.session)
    # Se toma antes de disparar: así una respuesta anterior de la misma sesión nunca
    # se devuelve como si fuera la de este mensaje.
    desde_id = demo_chat.ultimo_id(user_id)

    demo_chat.disparar(user_id, consulta.message)

    fila = demo_chat.esperar_respuesta(user_id, desde_id)
    if fila is None:
        raise HTTPException(status_code=504, detail=demo_chat.DETALLE_SIN_RESPUESTA)

    segundos = fila.get("segundos")
    return RespuestaDemo(
        reply=fila["ai_response"],
        intent=fila.get("intent"),
        seconds=round(float(segundos), 2) if segundos is not None else None,
    )


class PedidoDemo(BaseModel):
    session: str = Field(max_length=40)
    scenario: str

    @field_validator("session")
    @classmethod
    def _sesion_opaca(cls, valor: str) -> str:
        if not demo_chat.PATRON_SESION.fullmatch(valor):
            raise ValueError("identificador de sesión inválido")
        return valor

    @field_validator("scenario")
    @classmethod
    def _escenario_conocido(cls, valor: str) -> str:
        if valor not in demo_order.ESCENARIOS:
            raise ValueError("escenario inválido")
        return valor


class ResultadoPedido(BaseModel):
    order_number: str
    status: str
    product: str
    product_name: str
    quantity: int
    total_amount: float | None
    mttd_seconds: float | None
    mttr_seconds: float | None
    end_to_end_seconds: float | None
    notified_to: str


def _segundos(valor) -> float | None:
    return round(float(valor), 3) if valor is not None else None


@router.post("/order", response_model=ResultadoPedido)
def pedido(consulta: PedidoDemo, request: Request) -> ResultadoPedido:
    """Dispara un pedido real por el pipeline y devuelve lo que quedó registrado."""
    _con_cupo(consulta.session, request)

    producto = demo_order.producto_para_la_demo()
    cantidad = demo_order.cantidad_para(consulta.scenario, producto["stock"])
    numero = demo_order.nuevo_numero()

    demo_order.disparar(numero, producto, cantidad)

    fila = demo_order.esperar_pedido(numero)
    if fila is None:
        raise HTTPException(status_code=504, detail=demo_order.DETALLE_SIN_REGISTRO)

    return ResultadoPedido(
        order_number=fila["order_number"],
        status=fila["status"],
        product=producto["sku"],
        product_name=producto["name"],
        quantity=int(fila["quantity"]),
        total_amount=float(fila["total_amount"]) if fila["total_amount"] is not None else None,
        mttd_seconds=_segundos(fila["mttd"]),
        mttr_seconds=_segundos(fila["mttr"]),
        end_to_end_seconds=_segundos(fila["end_to_end"]),
        notified_to=demo_order.EMAIL_DEMO,
    )


@router.get("/stats")
def stats() -> dict:
    """Contadores agregados del sistema para la landing. Solo números."""
    return demo_chat.estadisticas()
