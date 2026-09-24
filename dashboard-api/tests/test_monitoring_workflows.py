import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import helpers_n8n as n8n

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).parent / "fixtures"
UTC = timezone.utc
NOW = datetime.now(UTC)
F1 = "wf-flujo-1"
F2 = "wf-flujo-2"
ERROR_DUMP = (FIXTURES / "n8n_execution_error_flujo1.flatted").read_text(encoding="utf-8")


def success_dump(run_data: dict, last: str) -> str:
    return n8n.flatted_stringify(n8n.execution_payload(run_data, last_node=last))


def flujo1_version(workflow: dict) -> dict:
    return {"nodes": workflow["nodes"], "connections": workflow["connections"]}


@pytest.fixture
def seeded(client, auth_headers, n8n_tables):
    """Flujo 1 y 2 importados, con ejecuciones de todos los sabores."""
    flujo1 = n8n.insert_flujo1(F1)
    n8n.insert_flujo2(F2)
    version = flujo1_version(flujo1)
    ids = {}
    ids["old"] = n8n.insert_execution(
        F1, status="success", started=NOW - timedelta(days=3),
        data=success_dump(n8n.with_stock_run_data(), "Respuesta Confirmada"),
        workflow_data=version,
    )
    ids["with_stock"] = n8n.insert_execution(
        F1, status="success", started=NOW - timedelta(minutes=10), duration_ms=435,
        data=success_dump(n8n.with_stock_run_data(), "Respuesta Confirmada"),
        workflow_data=version,
    )
    ids["no_stock"] = n8n.insert_execution(
        F1, status="success", started=NOW - timedelta(minutes=8), duration_ms=352,
        data=success_dump(n8n.no_stock_run_data(), "Respuesta Sin Stock"),
        workflow_data=version,
    )
    ids["error"] = n8n.insert_execution(
        F1, status="error", started=NOW - timedelta(minutes=5), duration_ms=49,
        data=ERROR_DUMP, workflow_data=version,
    )
    ids["empty"] = n8n.insert_execution(
        F1, status="new", started=NOW - timedelta(minutes=4), stopped=False,
        data=n8n.flatted_stringify({"version": 1, "resultData": {"runData": {}}}),
        workflow_data=version,
    )
    ids["corrupt"] = n8n.insert_execution(
        F1, status="error", started=NOW - timedelta(minutes=3),
        data="esto no es flatted {{{", workflow_data=version,
    )
    ids["no_data"] = n8n.insert_execution(
        F1, status="crashed", started=NOW - timedelta(minutes=2),
    )
    ids["deleted"] = n8n.insert_execution(
        F1, status="error", started=NOW - timedelta(minutes=1), deleted=True,
        data=ERROR_DUMP, workflow_data=version,
    )
    return ids


def get(client, headers, path, **params):
    return client.get(path, params=params, headers=headers)


# --------------------------------------------------------------------- authz


@pytest.mark.parametrize(
    "path",
    [
        "/monitoring/workflows",
        "/monitoring/workflows/abc/graph",
        "/monitoring/executions",
        "/monitoring/executions/1",
    ],
)
def test_endpoints_require_jwt(client, path):
    assert client.get(path).status_code == 401


# ------------------------------------------------------ tablas de n8n ausentes


def test_everything_degrades_when_the_n8n_tables_are_missing(client, auth_headers, no_n8n_tables):
    resp = get(client, auth_headers, "/monitoring/workflows")
    assert resp.status_code == 200
    assert resp.json() == {"available": False, "items": []}

    resp = get(client, auth_headers, "/monitoring/executions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["items"] == []
    assert body["has_more"] is False
    assert body["next_before"] is None

    assert get(client, auth_headers, "/monitoring/workflows/wf-flujo-1/graph").status_code == 404
    assert get(client, auth_headers, "/monitoring/executions/1").status_code == 404


def test_empty_n8n_tables_are_available_but_empty(client, auth_headers, n8n_tables):
    body = get(client, auth_headers, "/monitoring/workflows").json()
    assert body == {"available": True, "items": []}
    body = get(client, auth_headers, "/monitoring/executions").json()
    assert body["available"] is True
    assert body["items"] == []


# ------------------------------------------------------------------ workflows


def test_workflows_list_with_24h_counters_and_last_execution(client, auth_headers, seeded):
    n8n.insert_workflow("wf-archived", "Viejo", [], {}, archived=True)
    body = get(client, auth_headers, "/monitoring/workflows").json()
    assert body["available"] is True
    assert [w["id"] for w in body["items"]] == [F1, F2]  # por nombre, sin archivados

    flujo1, flujo2 = body["items"]
    assert set(flujo1) == {
        "id", "name", "active", "updated_at", "executions_24h", "errors_24h", "last_execution",
    }
    assert flujo1["name"].startswith("Flujo 1")
    assert flujo1["active"] is True
    assert flujo1["updated_at"].endswith("Z")
    # 8 ejecuciones: una borrada y una de hace 3 días no cuentan
    assert flujo1["executions_24h"] == 6
    assert flujo1["errors_24h"] == 3  # error, corrupt (error) y no_data (crashed)
    last = flujo1["last_execution"]
    assert last["id"] == seeded["no_data"]  # la más nueva no borrada
    assert last["status"] == "crashed"
    assert last["started_at"].endswith("Z")
    assert last["duration_ms"] == 900

    assert flujo2["active"] is False
    assert flujo2["executions_24h"] == 0
    assert flujo2["errors_24h"] == 0
    assert flujo2["last_execution"] is None


def test_last_execution_without_stop_time_has_null_duration(client, auth_headers, n8n_tables):
    n8n.insert_workflow(F1, "Flujo", [], {})
    n8n.insert_execution(F1, status="running", started=NOW, stopped=False)
    item = get(client, auth_headers, "/monitoring/workflows").json()["items"][0]
    assert item["last_execution"]["status"] == "running"
    assert item["last_execution"]["duration_ms"] is None


# ---------------------------------------------------------------------- grafo


def test_workflow_graph_is_sanitized(client, auth_headers, seeded):
    resp = get(client, auth_headers, f"/monitoring/workflows/{F1}/graph")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"id", "name", "active", "nodes", "edges", "bounds"}
    assert body["id"] == F1
    assert len(body["nodes"]) == 15
    assert len(body["edges"]) == 15
    branches = sorted(
        (e["output_index"], e["to"]) for e in body["edges"] if e["from"] == "IF Stock Disponible"
    )
    assert branches == [(0, "Actualizar Stock"), (1, "Marcar Sin Stock")]
    assert body["bounds"]["min_x"] == -960 and body["bounds"]["max_x"] == 1440
    for forbidden in ("parameters", "credentials", "webhookId", "INSERT INTO", "3VBjtgn4"):
        assert forbidden not in resp.text


def test_workflow_graph_of_flujo2_has_no_sticky_notes(client, auth_headers, seeded):
    body = get(client, auth_headers, f"/monitoring/workflows/{F2}/graph").json()
    assert body["active"] is False
    assert all(not n["name"].startswith("Sticky") for n in body["nodes"])
    assert any(e["kind"] == "ai_languageModel" for e in body["edges"])


def test_workflow_graph_not_found(client, auth_headers, seeded):
    resp = get(client, auth_headers, "/monitoring/workflows/no-existe/graph")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Workflow no encontrado"


def test_workflow_graph_rejects_malformed_ids(client, auth_headers, seeded):
    assert get(client, auth_headers, "/monitoring/workflows/x'%20OR%201=1/graph").status_code == 422
    assert get(client, auth_headers, f"/monitoring/workflows/{'a' * 37}/graph").status_code == 422


# ------------------------------------------------------------ lista de ejecuciones


def test_executions_list_newest_first_without_deleted(client, auth_headers, seeded):
    body = get(client, auth_headers, "/monitoring/executions", limit=100).json()
    assert body["available"] is True
    ids = [item["id"] for item in body["items"]]
    assert ids == sorted(ids, reverse=True)
    assert seeded["deleted"] not in ids
    assert len(ids) == 7
    assert body["has_more"] is False

    error = next(i for i in body["items"] if i["id"] == seeded["error"])
    assert set(error) == {
        "id", "workflow_id", "workflow_name", "status", "mode", "started_at",
        "stopped_at", "duration_ms", "error_message",
    }
    assert error["workflow_id"] == F1
    assert error["workflow_name"].startswith("Flujo 1")
    assert error["status"] == "error"
    assert error["mode"] == "webhook"
    assert error["duration_ms"] == 49
    assert error["started_at"].endswith("Z") and error["stopped_at"].endswith("Z")
    assert error["error_message"].startswith("Credential with ID")
    assert "stack" not in json.dumps(error)


def test_executions_list_error_messages_only_for_failures(client, auth_headers, seeded):
    items = {
        i["id"]: i
        for i in get(client, auth_headers, "/monitoring/executions", limit=100).json()["items"]
    }
    assert items[seeded["with_stock"]]["error_message"] is None
    assert items[seeded["no_stock"]]["error_message"] is None
    assert items[seeded["corrupt"]]["error_message"] is None  # datos ilegibles: sin mensaje
    assert items[seeded["no_data"]]["error_message"] is None  # sin execution_data
    assert items[seeded["empty"]]["duration_ms"] is None  # nunca terminó


def test_executions_list_filters(client, auth_headers, seeded):
    body = get(client, auth_headers, "/monitoring/executions", status="error", limit=100).json()
    assert {i["status"] for i in body["items"]} == {"error"}
    assert len(body["items"]) == 2

    body = get(client, auth_headers, "/monitoring/executions", workflow_id=F2).json()
    assert body["items"] == []
    body = get(client, auth_headers, "/monitoring/executions", workflow_id=F1, limit=100).json()
    assert len(body["items"]) == 7


def test_executions_list_pages_by_id(client, auth_headers, seeded):
    collected: list[int] = []
    cursor = None
    for _ in range(10):
        params = {"limit": 3}
        if cursor:
            params["before"] = cursor
        page = get(client, auth_headers, "/monitoring/executions", **params).json()
        collected.extend(i["id"] for i in page["items"])
        if not page["has_more"]:
            assert page["next_before"] is None
            break
        cursor = page["next_before"]
        assert cursor == page["items"][-1]["id"]
    else:
        pytest.fail("la paginación no terminó")
    assert collected == sorted(collected, reverse=True)
    assert len(collected) == len(set(collected)) == 7


def test_executions_list_error_message_is_redacted(client, auth_headers, n8n_tables):
    n8n.insert_workflow(F1, "Flujo", [], {})
    token = "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw0"
    error = {"message": f"Falló https://api.telegram.org/bot{token}/getMe"}
    run = {"Enviar Telegram": [n8n.node_run(n8n.at(0), 0, 5, error=error)]}
    n8n.insert_execution(
        F1, status="error", started=NOW,
        data=n8n.flatted_stringify(n8n.execution_payload(run, last_node="Enviar Telegram", error=error)),
    )
    resp = get(client, auth_headers, "/monitoring/executions")
    assert token not in resp.text
    assert "[REDACTADO]" in resp.json()["items"][0]["error_message"]


def test_executions_list_skips_oversized_payloads(client, auth_headers, seeded, monkeypatch):
    monkeypatch.setattr("app.core.n8n_reader.LIST_MAX_BYTES", 50)
    items = {
        i["id"]: i
        for i in get(client, auth_headers, "/monitoring/executions", limit=100).json()["items"]
    }
    assert items[seeded["error"]]["error_message"] is None


@pytest.mark.parametrize(
    "params",
    [
        {"status": "inventado"},
        {"limit": 0},
        {"limit": 101},
        {"before": 0},
        {"before": "abc"},
        {"workflow_id": "x y"},
        {"workflow_id": "a" * 37},
    ],
)
def test_executions_list_rejects_invalid_parameters(client, auth_headers, seeded, params):
    assert get(client, auth_headers, "/monitoring/executions", **params).status_code == 422


# ------------------------------------------------------------ traza de ejecución


def trace_of(client, headers, execution_id):
    resp = get(client, headers, f"/monitoring/executions/{execution_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_trace_with_stock_lights_the_true_branch(client, auth_headers, seeded):
    body = trace_of(client, auth_headers, seeded["with_stock"])
    assert set(body) == {
        "execution", "workflow_id", "nodes", "path", "last_node_executed", "truncated", "error",
    }
    assert body["workflow_id"] == F1
    assert body["execution"]["id"] == seeded["with_stock"]
    assert body["execution"]["status"] == "success"
    assert body["execution"]["duration_ms"] == 435
    assert body["execution"]["error_message"] is None
    assert body["truncated"] is False
    assert body["error"] is None
    assert body["last_node_executed"] == "Respuesta Confirmada"
    nodes = {n["name"]: n for n in body["nodes"]}
    assert len(nodes) == 15
    assert nodes["IF Stock Disponible"]["outputs"] == [1, 0]
    assert nodes["Marcar Sin Stock"]["status"] == "skipped"
    assert nodes["Respuesta Confirmada"]["status"] == "success"
    assert body["path"][0] == "Webhook - Recibir Orden"
    assert body["path"][-1] == "Respuesta Confirmada"


def test_trace_without_stock_lights_the_false_branch(client, auth_headers, seeded):
    body = trace_of(client, auth_headers, seeded["no_stock"])
    nodes = {n["name"]: n for n in body["nodes"]}
    assert nodes["IF Stock Disponible"]["outputs"] == [0, 1]
    assert nodes["Marcar Sin Stock"]["status"] == "success"
    assert nodes["Actualizar Stock"]["status"] == "skipped"


def test_trace_of_a_failed_execution(client, auth_headers, seeded):
    body = trace_of(client, auth_headers, seeded["error"])
    assert body["execution"]["status"] == "error"
    assert body["execution"]["error_message"].startswith("Credential with ID")
    assert body["last_node_executed"] == "Registrar Orden"
    nodes = {n["name"]: n for n in body["nodes"]}
    assert nodes["Registrar Orden"]["status"] == "error"
    assert nodes["Registrar Orden"]["error"]["message"].startswith("Credential with ID")
    assert nodes["Verificar Stock"]["status"] == "skipped"
    assert body["path"] == ["Webhook - Recibir Orden", "Registrar Orden"]


def test_trace_without_run_data_skips_everything(client, auth_headers, seeded):
    body = trace_of(client, auth_headers, seeded["empty"])
    assert body["error"] is None
    assert body["path"] == []
    assert {n["status"] for n in body["nodes"]} == {"skipped"}


def test_trace_with_corrupt_data_is_empty_with_a_readable_error(client, auth_headers, seeded):
    body = trace_of(client, auth_headers, seeded["corrupt"])
    assert body["nodes"] == [] and body["path"] == []
    assert body["error"]
    assert body["truncated"] is False
    assert body["execution"]["status"] == "error"


def test_trace_without_execution_data_row(client, auth_headers, seeded):
    body = trace_of(client, auth_headers, seeded["no_data"])
    assert body["nodes"] == []
    assert "purgados" in body["error"]


def test_trace_of_an_oversized_payload_is_minimal_and_never_parsed(
    client, auth_headers, seeded, monkeypatch
):
    monkeypatch.setattr("app.core.n8n_reader.DETAIL_MAX_BYTES", 100)
    body = trace_of(client, auth_headers, seeded["with_stock"])
    assert body["truncated"] is True
    assert body["nodes"] == []
    assert body["path"] == []
    assert body["error"] is None
    assert body["execution"]["id"] == seeded["with_stock"]


def test_trace_uses_the_workflow_version_that_actually_ran(client, auth_headers, n8n_tables):
    flujo1 = n8n.insert_flujo1(F1)
    two_nodes = {
        "nodes": [n for n in flujo1["nodes"] if n["name"] in ("Webhook - Recibir Orden", "Registrar Orden")],
        "connections": {},
    }
    execution = n8n.insert_execution(
        F1, status="error", started=NOW, data=ERROR_DUMP, workflow_data=two_nodes
    )
    body = trace_of(client, auth_headers, execution)
    assert [n["name"] for n in body["nodes"]] == ["Webhook - Recibir Orden", "Registrar Orden"]


def test_trace_falls_back_to_the_current_workflow_when_the_snapshot_is_empty(
    client, auth_headers, n8n_tables
):
    n8n.insert_flujo1(F1)
    execution = n8n.insert_execution(F1, status="error", started=NOW, data=ERROR_DUMP)
    body = trace_of(client, auth_headers, execution)
    assert len(body["nodes"]) == 15


def test_trace_never_leaks_secrets_or_parameters(client, auth_headers, n8n_tables):
    workflow = n8n.insert_flujo1(F1)
    secret = "sk-proj-Abc123Def456Ghi789Jkl012Mno345Pqr678"
    token = "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw0"
    run_data = {
        "Webhook - Recibir Orden": [
            n8n.node_run(
                n8n.at(0), 0, 2,
                [[{
                    "headers": {"authorization": f"Bearer {secret}", "x-n8n-secret": "shh", "host": "h"},
                    "body": {"order_number": "ORD-1", "api_key": secret, "nota": f"bot{token}"},
                }]],
            )
        ],
        "Registrar Orden": [
            n8n.node_run(n8n.at(5), 1, 9, error={"message": f"falló con {secret}", "stack": "at x.ts:1"},
                         previous="Webhook - Recibir Orden")
        ],
    }
    dump = n8n.flatted_stringify(
        n8n.execution_payload(run_data, last_node="Registrar Orden", error={"message": f"falló con {secret}"})
    )
    execution = n8n.insert_execution(
        F1, status="error", started=NOW, data=dump, workflow_data=flujo1_version(workflow)
    )
    resp = get(client, auth_headers, f"/monitoring/executions/{execution}")
    assert resp.status_code == 200
    for forbidden in (secret, token, "shh", "at x.ts", "parameters", "credentials", "INSERT INTO"):
        assert forbidden not in resp.text, forbidden
    assert "ORD-1" in resp.text  # el dato de negocio sí se ve
    assert "[REDACTADO]" in resp.text


def test_trace_not_found(client, auth_headers, seeded):
    assert get(client, auth_headers, "/monitoring/executions/999999").status_code == 404
    deleted = get(client, auth_headers, f"/monitoring/executions/{seeded['deleted']}")
    assert deleted.status_code == 404
    assert deleted.json()["detail"] == "Ejecución no encontrada"
    assert get(client, auth_headers, "/monitoring/executions/abc").status_code == 422
    assert get(client, auth_headers, "/monitoring/executions/0").status_code == 422
