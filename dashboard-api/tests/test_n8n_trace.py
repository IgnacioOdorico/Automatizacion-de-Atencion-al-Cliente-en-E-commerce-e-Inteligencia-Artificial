import json
from pathlib import Path

import pytest

from app.core.n8n_graph import sanitize_nodes
from app.core.n8n_trace import build_trace
from app.core.redaction import REDACTED
from helpers_n8n import (
    FLUJO1_PATH,
    IF_STOCK,
    ORDER,
    REGISTRAR,
    VERIFICAR,
    WEBHOOK,
    at,
    execution_payload,
    flatted_stringify,
    load_workflow,
    no_stock_run_data,
    node_run,
    with_stock_run_data,
)

FIXTURES = Path(__file__).parent / "fixtures"

FLUJO1_NODES = sanitize_nodes(load_workflow(FLUJO1_PATH)["nodes"])
NODE_NAMES = [n["name"] for n in FLUJO1_NODES]

def trace_of(run_data: dict, last: str, error: dict | None = None) -> dict:
    text = flatted_stringify(execution_payload(run_data, last_node=last, error=error))
    return build_trace(text, FLUJO1_NODES)


def by_name(trace: dict) -> dict:
    return {node["name"]: node for node in trace["nodes"]}


# ----------------------------------------------------------------- con stock


def test_success_with_stock_marks_the_true_branch_and_skips_the_other():
    trace = trace_of(with_stock_run_data(), "Respuesta Confirmada")
    nodes = by_name(trace)
    assert trace["truncated"] is False
    assert trace["error"] is None
    assert trace["last_node_executed"] == "Respuesta Confirmada"
    assert [n["name"] for n in trace["nodes"]] == NODE_NAMES  # orden del grafo

    assert trace["path"] == [
        WEBHOOK,
        REGISTRAR,
        VERIFICAR,
        IF_STOCK,
        "Actualizar Stock",
        "IF Stock Bajo",
        "Confirmar Orden",
        "Enviar Email Confirmación",
        "Registrar Notificación",
        "Respuesta Confirmada",
    ]
    for name in trace["path"]:
        assert nodes[name]["status"] == "success", name
    for name in (
        "Marcar Sin Stock",
        "Enviar Email Sin Stock",
        "Registrar Notificación Sin Stock",
        "Respuesta Sin Stock",
        "Registrar Alerta Stock Bajo",
    ):
        assert nodes[name]["status"] == "skipped", name
        assert nodes[name]["started_at"] is None
        assert nodes[name]["duration_ms"] is None
        assert nodes[name]["items_out"] == 0
        assert nodes[name]["outputs"] == []
        assert nodes[name]["output_preview"] is None
        assert nodes[name]["error"] is None
        assert nodes[name]["runs"] == 0

    if_node = nodes[IF_STOCK]
    assert if_node["outputs"] == [1, 0]  # salió por la rama verdadera
    assert if_node["items_out"] == 1
    assert nodes["IF Stock Bajo"]["outputs"] == [0, 1]


def test_node_detail_fields():
    nodes = by_name(trace_of(with_stock_run_data(), "Respuesta Confirmada"))
    registrar = nodes[REGISTRAR]
    assert set(registrar) == {
        "name",
        "short_type",
        "status",
        "started_at",
        "duration_ms",
        "items_out",
        "outputs",
        "runs",
        "error",
        "output_preview",
        "output_truncated",
    }
    assert registrar["short_type"] == "postgres"
    assert registrar["started_at"] == "2026-09-21T12:00:00.005Z"
    assert registrar["duration_ms"] == 31
    assert registrar["items_out"] == 1
    assert registrar["runs"] == 1
    assert registrar["output_truncated"] is False
    assert registrar["output_preview"] == [{"order_id": 7, **ORDER}]


# ------------------------------------------------------------------ sin stock


def test_success_without_stock_marks_the_false_branch():
    trace = trace_of(no_stock_run_data(), "Respuesta Sin Stock")
    nodes = by_name(trace)
    assert nodes[IF_STOCK]["outputs"] == [0, 1]
    assert trace["path"][-4:] == [
        "Marcar Sin Stock",
        "Enviar Email Sin Stock",
        "Registrar Notificación Sin Stock",
        "Respuesta Sin Stock",
    ]
    assert nodes["Actualizar Stock"]["status"] == "skipped"
    assert nodes["Confirmar Orden"]["status"] == "skipped"
    assert nodes["Respuesta Confirmada"]["status"] == "skipped"


# ---------------------------------------------------------------------- error


def test_real_error_dump_from_n8n_2_12_2():
    text = (FIXTURES / "n8n_execution_error_flujo1.flatted").read_text(encoding="utf-8")
    trace = build_trace(text, FLUJO1_NODES)
    nodes = by_name(trace)
    assert trace["path"] == [WEBHOOK, REGISTRAR]
    assert trace["last_node_executed"] == REGISTRAR
    assert nodes[WEBHOOK]["status"] == "success"
    assert nodes[WEBHOOK]["duration_ms"] == 2
    assert nodes[REGISTRAR]["status"] == "error"
    assert nodes[REGISTRAR]["duration_ms"] == 31
    assert nodes[REGISTRAR]["error"]["message"].startswith("Credential with ID")
    assert nodes[REGISTRAR]["error"]["description"] is None
    assert nodes[REGISTRAR]["output_preview"] is None
    assert nodes[VERIFICAR]["status"] == "skipped"
    assert "stack" not in json.dumps(trace)
    assert "credentials-helper" not in json.dumps(trace)
    # el webhook recibió el pedido: su salida se ve en el detalle
    assert nodes[WEBHOOK]["output_preview"][0]["body"]["order_number"] == "ORD-E2E-001"


def test_error_details_are_redacted_and_bounded():
    token = "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw0"
    error = {
        "message": f"Bad request https://api.telegram.org/bot{token}/sendMessage",
        "description": "Unauthorized " + "x" * 3000,
        "stack": "Error: boom\n    at secret.ts:1",
        "node": {"name": REGISTRAR, "parameters": {"query": "SELECT secret"}},
    }
    run_data = {WEBHOOK: [node_run(at(0), 0, 2, [[ORDER]])], REGISTRAR: [node_run(at(5), 1, 9, error=error)]}
    trace = trace_of(run_data, REGISTRAR, error=error)
    node_error = by_name(trace)[REGISTRAR]["error"]
    assert token not in json.dumps(trace)
    assert REDACTED in node_error["message"]
    assert len(node_error["description"]) <= 1001
    dumped = json.dumps(trace)
    assert "boom" not in dumped
    assert "SELECT secret" not in dumped


def test_missing_error_message_gets_a_readable_default():
    run_data = {REGISTRAR: [node_run(at(0), 0, 9, error={})]}
    node = by_name(trace_of(run_data, REGISTRAR))[REGISTRAR]
    assert node["status"] == "error"
    assert node["error"]["message"] == "El nodo terminó con error"


# ----------------------------------------------------------- casos especiales


def test_execution_without_run_data_skips_every_node():
    text = flatted_stringify({"version": 1, "resultData": {"runData": {}}})
    trace = build_trace(text, FLUJO1_NODES)
    assert trace["error"] is None
    assert trace["path"] == []
    assert trace["last_node_executed"] is None
    assert {n["status"] for n in trace["nodes"]} == {"skipped"}
    assert len(trace["nodes"]) == len(FLUJO1_NODES)


def test_execution_without_result_data_is_an_empty_trace():
    trace = build_trace(flatted_stringify({"version": 1}), FLUJO1_NODES)
    assert trace["path"] == []
    assert {n["status"] for n in trace["nodes"]} == {"skipped"}


@pytest.mark.parametrize("text", ["esto no es json {{{", "[]", '[{"a":"9"}]', "", None])
def test_corrupt_or_missing_data_gives_an_empty_trace_with_a_readable_error(text):
    trace = build_trace(text, FLUJO1_NODES)
    assert trace["nodes"] == []
    assert trace["path"] == []
    assert trace["last_node_executed"] is None
    assert trace["truncated"] is False
    assert isinstance(trace["error"], str) and trace["error"]


def test_oversized_data_is_not_parsed():
    trace = build_trace(None, FLUJO1_NODES, oversized=True)
    assert trace["truncated"] is True
    assert trace["nodes"] == []
    assert trace["path"] == []
    assert trace["error"] is None


def test_node_that_ran_twice_is_aggregated():
    run_data = {
        REGISTRAR: [
            node_run(at(0), 0, 10, [[{"n": 1}]]),
            node_run(at(50), 3, 25, [[{"n": 2}, {"n": 3}]]),
        ],
        WEBHOOK: [node_run(at(0), 1, 2, [[ORDER]])],
    }
    trace = trace_of(run_data, REGISTRAR)
    node = by_name(trace)[REGISTRAR]
    assert node["runs"] == 2
    assert node["duration_ms"] == 35
    assert node["started_at"] == "2026-09-21T12:00:00.000Z"
    assert node["items_out"] == 2  # la última corrida
    assert node["output_preview"] == [{"n": 2}, {"n": 3}]
    assert trace["path"] == [REGISTRAR, WEBHOOK]  # orden por executionIndex de la 1ª corrida


def test_one_failing_run_makes_the_node_an_error():
    run_data = {
        REGISTRAR: [
            node_run(at(0), 0, 10, [[{"n": 1}]]),
            node_run(at(50), 1, 25, error={"message": "falló la segunda"}),
        ]
    }
    node = by_name(trace_of(run_data, REGISTRAR))[REGISTRAR]
    assert node["status"] == "error"
    assert node["error"]["message"] == "falló la segunda"


def test_nodes_missing_from_the_graph_are_appended_without_type():
    run_data = {"Nodo Renombrado": [node_run(at(0), 0, 4, [[{"a": 1}]])]}
    trace = trace_of(run_data, "Nodo Renombrado")
    assert trace["nodes"][-1]["name"] == "Nodo Renombrado"
    assert trace["nodes"][-1]["short_type"] is None
    assert trace["nodes"][-1]["status"] == "success"
    assert trace["path"] == ["Nodo Renombrado"]


def test_disabled_graph_nodes_are_skipped_even_if_named_in_run_data():
    graph = [{"name": "A", "type": "n8n-nodes-base.set", "short_type": "set", "position": [0, 0], "disabled": True}]
    text = flatted_stringify(execution_payload({}, last_node="A"))
    trace = build_trace(text, graph)
    assert trace["nodes"][0]["status"] == "skipped"


def test_output_preview_is_redacted_and_capped():
    secret = "sk-proj-Abc123Def456Ghi789Jkl012Mno345Pqr678"
    big = [{"n": i, "texto": "lorem ipsum " * 50, "authorization": "Bearer abcdefgh1234"} for i in range(40)]
    big[0]["nota"] = f"clave {secret}"
    run_data = {WEBHOOK: [node_run(at(0), 0, 2, [big])]}
    trace = trace_of(run_data, WEBHOOK)
    node = by_name(trace)[WEBHOOK]
    dumped = json.dumps(node["output_preview"], ensure_ascii=False)
    assert len(dumped.encode("utf-8")) <= 2048
    assert node["output_truncated"] is True
    assert node["items_out"] == 40
    assert secret not in dumped
    assert "Bearer" not in dumped
    assert REDACTED in dumped


def test_binary_data_is_never_returned():
    run_data = {
        WEBHOOK: [
            {
                **node_run(at(0), 0, 2, [[ORDER]]),
                "data": {
                    "main": [[{"json": {"ok": 1}, "binary": {"data": {"data": "QUJD" * 100}}}]]
                },
            }
        ]
    }
    node = by_name(trace_of(run_data, WEBHOOK))[WEBHOOK]
    assert "QUJD" not in json.dumps(node["output_preview"])
    assert node["output_preview"] == [{"ok": 1}]


def test_lists_of_ai_and_null_outputs_do_not_break_the_trace():
    run_data = {
        REGISTRAR: [
            {
                "startTime": 1789952801045,
                "executionIndex": 0,
                "executionTime": 5,
                "executionStatus": "success",
                "data": {"main": [None, [{"json": {"ok": True}}]], "ai_languageModel": [[{"json": {"x": 1}}]]},
            }
        ]
    }
    node = by_name(trace_of(run_data, REGISTRAR))[REGISTRAR]
    assert node["outputs"] == [0, 1]
    assert node["items_out"] == 1


# ------------------------------------------------- error a nivel de ejecución


def real_error_dump() -> str:
    return (FIXTURES / "n8n_execution_error_flujo1.flatted").read_text(encoding="utf-8")


def test_trace_exposes_the_execution_error_message():
    from app.core.n8n_trace import execution_error_message

    trace = build_trace(real_error_dump(), FLUJO1_NODES)
    assert trace["execution_error"].startswith("Credential with ID")
    assert execution_error_message(real_error_dump()).startswith("Credential with ID")

    ok = flatted_stringify(execution_payload(with_stock_run_data(), last_node="Respuesta Confirmada"))
    assert build_trace(ok, FLUJO1_NODES)["execution_error"] is None
    assert execution_error_message(ok) is None


def test_execution_error_falls_back_to_the_failing_node_and_never_raises():
    from app.core.n8n_trace import execution_error_message

    run_data = {REGISTRAR: [node_run(at(0), 0, 9, error={"message": "falló el nodo"})]}
    text = flatted_stringify(execution_payload(run_data, last_node=REGISTRAR))
    assert execution_error_message(text) == "falló el nodo"
    for bad in ("no es json", "[]", "", None):
        assert execution_error_message(bad) is None


def test_execution_error_message_is_redacted_and_short():
    token = "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw0"
    error = {"message": f"bot{token} " + "y" * 2000}
    text = flatted_stringify(execution_payload({}, last_node=REGISTRAR, error=error))
    from app.core.n8n_trace import execution_error_message

    message = execution_error_message(text)
    assert token not in message
    assert len(message) <= 301
