"""Parser del formato `flatted` que usa n8n en `execution_data.data`.

`flatted` aplana un grafo de objetos en un arreglo JSON: la posición 0 es la raíz,
cada objeto o arreglo vive en una posición y en su interior toda cadena es el ÍNDICE
(como texto) de otra posición. Los números, booleanos y `null` quedan en línea, y una
cadena real es una posición cuyo valor es la propia cadena.

    [{"a":"1","n":7},"hola"]   ->   {"a": "hola", "n": 7}

Este parser es iterativo (no recursivo, para que datos hostiles no agoten la pila),
acepta ciclos (crea todos los contenedores antes de enlazarlos) y tiene un tope de
posiciones. El llamador acota además el tamaño del texto antes de llamarlo.
"""

import json
from typing import Any

DEFAULT_MAX_ITEMS = 200_000


class FlattedError(ValueError):
    """El texto no es un documento `flatted` válido o excede los topes."""


def parse_flatted(text: str, *, max_items: int = DEFAULT_MAX_ITEMS) -> Any:
    try:
        table = json.loads(text)
    except (TypeError, ValueError, RecursionError) as exc:
        raise FlattedError("El contenido no es JSON válido") from exc
    if not isinstance(table, list) or not table:
        raise FlattedError("El contenido no tiene forma de documento flatted")
    if len(table) > max_items:
        raise FlattedError("El documento excede el máximo de elementos permitido")

    size = len(table)
    resolved: list[Any] = [None] * size
    for position, item in enumerate(table):
        if isinstance(item, dict):
            resolved[position] = {}
        elif isinstance(item, list):
            resolved[position] = []
        else:
            resolved[position] = item

    def reference(raw: Any) -> Any:
        if isinstance(raw, str):
            if not raw.isascii() or not raw.isdigit():
                raise FlattedError("Referencia no numérica")
            index = int(raw)
            if index >= size:
                raise FlattedError("Referencia fuera de rango")
            return resolved[index]
        if isinstance(raw, (dict, list)):
            raise FlattedError("Contenedor anidado sin aplanar")
        return raw

    for position, item in enumerate(table):
        if isinstance(item, dict):
            target = resolved[position]
            for key, raw in item.items():
                target[key] = reference(raw)
        elif isinstance(item, list):
            target = resolved[position]
            for raw in item:
                target.append(reference(raw))
    return resolved[0]
