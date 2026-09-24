from pathlib import Path

import pytest

from app.core.flatted import FlattedError, parse_flatted
from helpers_n8n import flatted_stringify

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_a_real_n8n_execution_dump():
    """Volcado real de la ejecución 1 del Flujo 1 (n8n 2.12.2), sin credenciales."""
    text = (FIXTURES / "n8n_execution_error_flujo1.flatted").read_text(encoding="utf-8")
    data = parse_flatted(text)

    result = data["resultData"]
    assert result["lastNodeExecuted"] == "Registrar Orden"
    assert list(result["runData"]) == ["Webhook - Recibir Orden", "Registrar Orden"]

    webhook_run = result["runData"]["Webhook - Recibir Orden"][0]
    assert webhook_run["executionStatus"] == "success"
    assert webhook_run["executionTime"] == 2
    item = webhook_run["data"]["main"][0][0]
    assert item["json"]["body"]["order_number"] == "ORD-E2E-001"
    assert item["json"]["body"]["quantity"] == 1
    assert item["json"]["headers"]["content-type"] == "application/json"

    failing_run = result["runData"]["Registrar Orden"][0]
    assert failing_run["executionStatus"] == "error"
    assert failing_run["startTime"] == 1789952801045
    assert "does not exist" in failing_run["error"]["message"]
    assert failing_run["source"][0]["previousNode"] == "Webhook - Recibir Orden"
    assert result["error"]["message"] == failing_run["error"]["message"]


def test_roundtrip_of_nested_structures():
    original = {
        "nombre": "Ñandú",
        "n": 3,
        "pi": 3.5,
        "ok": True,
        "nada": None,
        "lista": [1, "dos", {"tres": [3]}, []],
        "vacio": {},
    }
    assert parse_flatted(flatted_stringify(original)) == original


def test_strings_that_look_like_numbers_stay_strings():
    original = {"a": "0", "b": "12", "c": ["3", 3]}
    assert parse_flatted(flatted_stringify(original)) == original


def test_shared_references_resolve_to_equal_values():
    shared = {"x": 1}
    data = parse_flatted(flatted_stringify({"a": shared, "b": shared}))
    assert data["a"] == data["b"] == {"x": 1}


def test_circular_references_do_not_loop():
    node: dict = {"name": "nodo"}
    node["self"] = node
    node["hijos"] = [node]
    data = parse_flatted(flatted_stringify(node))
    assert data["name"] == "nodo"
    assert data["self"] is data
    assert data["hijos"][0] is data


def test_scalar_and_empty_documents():
    assert parse_flatted('[{}]') == {}
    assert parse_flatted('["hola"]') == "hola"
    assert parse_flatted("[3]") == 3


@pytest.mark.parametrize(
    "text",
    [
        "",
        "no es json",
        "{}",
        "[]",
        '[{"a":"5"}]',  # referencia fuera de rango
        '[{"a":"-1"}]',
        '[{"a":"x"}]',  # una cadena que no es índice: no es formato flatted
        '[{"a":{"b":1}}]',  # los contenedores anidados van siempre por índice
        "[[1,2],{}, null",
    ],
)
def test_malformed_documents_raise_flatted_error(text):
    with pytest.raises(FlattedError):
        parse_flatted(text)


def test_rejects_documents_over_the_item_limit():
    text = "[" + ",".join(['"x"'] * 50) + "]"
    with pytest.raises(FlattedError):
        parse_flatted(text, max_items=10)


def test_deep_structures_do_not_hit_the_recursion_limit():
    # 5000 niveles de anidación: un parser recursivo reventaría la pila.
    depth = 5000
    parts = [f'{{"n":"{i + 1}"}}' for i in range(depth)] + ['"fin"']
    text = "[" + ",".join(parts) + "]"
    data = parse_flatted(text)
    node = data
    for _ in range(depth):
        node = node["n"]
    assert node == "fin"
