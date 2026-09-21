import json

import pytest

from app.core.n8n_graph import sanitize_graph, short_type
from helpers_n8n import FLUJO1_PATH, FLUJO2_PATH, load_workflow


def graph_of(path):
    workflow = load_workflow(path)
    return workflow, sanitize_graph(workflow["nodes"], workflow["connections"])


def edges_from(graph, name):
    return sorted(
        (e["output_index"], e["to"]) for e in graph["edges"] if e["from"] == name
    )


@pytest.mark.parametrize(
    "full, short",
    [
        ("n8n-nodes-base.webhook", "webhook"),
        ("n8n-nodes-base.postgres", "postgres"),
        ("n8n-nodes-base.if", "if"),
        ("n8n-nodes-base.emailSend", "emailSend"),
        ("n8n-nodes-base.respondToWebhook", "respondToWebhook"),
        ("@n8n/n8n-nodes-langchain.chainLlm", "chainLlm"),
        ("webhook", "webhook"),
        ("", ""),
    ],
)
def test_short_type_is_the_last_part_of_the_type(full, short):
    assert short_type(full) == short


def test_flujo1_graph_has_every_node_and_edge():
    workflow, graph = graph_of(FLUJO1_PATH)
    assert len(graph["nodes"]) == len(workflow["nodes"]) == 15
    assert {n["name"] for n in graph["nodes"]} == {n["name"] for n in workflow["nodes"]}
    assert len(graph["edges"]) == 15
    for edge in graph["edges"]:
        assert set(edge) == {"from", "to", "output_index", "input_index", "kind"}
        assert edge["kind"] == "main"
        assert edge["input_index"] == 0


def test_node_fields_are_a_strict_whitelist():
    _, graph = graph_of(FLUJO1_PATH)
    for node in graph["nodes"]:
        assert set(node) == {"name", "type", "short_type", "position", "disabled"}
        assert isinstance(node["position"], list) and len(node["position"]) == 2
        assert node["disabled"] is False
    webhook = next(n for n in graph["nodes"] if n["name"] == "Webhook - Recibir Orden")
    assert webhook["type"] == "n8n-nodes-base.webhook"
    assert webhook["short_type"] == "webhook"
    assert webhook["position"] == [-960, 144]


def test_if_branches_respect_the_output_index():
    _, graph = graph_of(FLUJO1_PATH)
    # 0 = verdadero (hay stock), 1 = falso (sin stock)
    assert edges_from(graph, "IF Stock Disponible") == [
        (0, "Actualizar Stock"),
        (1, "Marcar Sin Stock"),
    ]
    assert edges_from(graph, "IF Stock Bajo") == [
        (0, "Registrar Alerta Stock Bajo"),
        (1, "Confirmar Orden"),
    ]


def test_graph_never_leaks_parameters_credentials_or_notes():
    workflow, graph = graph_of(FLUJO1_PATH)
    dumped = json.dumps(graph, ensure_ascii=False)
    for forbidden in ("parameters", "credentials", "webhookId", "notes", "typeVersion"):
        assert forbidden not in dumped
    for node in workflow["nodes"]:
        for cred in (node.get("credentials") or {}).values():
            assert cred["id"] not in dumped
            assert cred["name"] not in dumped
        for value in json.dumps(node.get("parameters", {})).split('"'):
            if len(value) > 25:  # consultas SQL, rutas, cuerpos de mail
                assert value not in dumped


def test_bounds_cover_all_positions():
    _, graph = graph_of(FLUJO1_PATH)
    xs = [n["position"][0] for n in graph["nodes"]]
    ys = [n["position"][1] for n in graph["nodes"]]
    assert graph["bounds"] == {
        "min_x": min(xs),
        "min_y": min(ys),
        "max_x": max(xs),
        "max_y": max(ys),
    }
    assert graph["bounds"]["min_x"] == -960
    assert graph["bounds"]["max_x"] == 1440


def test_flujo2_skips_sticky_notes_and_keeps_disabled_flag_and_ai_edges():
    workflow, graph = graph_of(FLUJO2_PATH)
    names = {n["name"] for n in graph["nodes"]}
    assert not any(name.startswith("Sticky Note") for name in names)
    assert len(graph["nodes"]) == len(workflow["nodes"]) - 1
    gmail = next(n for n in graph["nodes"] if n["name"] == "Trigger Gmail")
    assert gmail["disabled"] is True
    assert gmail["short_type"] == "gmailTrigger"

    ai = [e for e in graph["edges"] if e["kind"] == "ai_languageModel"]
    assert [(e["from"], e["to"]) for e in ai] == [("OpenAI Chat Model", "IA - Motor Decision")]
    assert edges_from(graph, "Switch Intent") == [
        (0, "Router Canal"),
        (1, "Buscar Pedido"),
        (2, "Crear Ticket"),
        (3, "Router Canal"),
    ]
    assert edges_from(graph, "Router Canal") == [
        (0, "Enviar Telegram"),
        (1, "Enviar Respuesta (Producción)"),
    ]


def test_edges_to_or_from_unknown_nodes_are_dropped():
    nodes = [{"name": "A", "type": "n8n-nodes-base.set", "position": [0, 0]}]
    connections = {
        "A": {"main": [[{"node": "Fantasma", "type": "main", "index": 0}]]},
        "Otro": {"main": [[{"node": "A", "type": "main", "index": 0}]]},
    }
    assert sanitize_graph(nodes, connections)["edges"] == []


def test_malformed_input_degrades_to_an_empty_graph():
    assert sanitize_graph(None, None) == {
        "nodes": [],
        "edges": [],
        "bounds": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
    }
    graph = sanitize_graph(
        [{"name": "A", "type": "x.y"}, "basura", {"type": "sin-nombre"}, {"name": 5}],
        {"A": {"main": "no-es-lista"}, "B": 3, "C": {"main": [None, [None, 4, {}]]}},
    )
    assert [n["name"] for n in graph["nodes"]] == ["A"]
    assert graph["nodes"][0]["position"] == [0, 0]
    assert graph["edges"] == []


def test_multiple_inputs_and_outputs_keep_their_indexes():
    nodes = [
        {"name": n, "type": "n8n-nodes-base.set", "position": [i * 10, 0]}
        for i, n in enumerate("ABC")
    ]
    connections = {
        "A": {"main": [[{"node": "C", "type": "main", "index": 1}], [{"node": "B", "type": "main", "index": 0}]]}
    }
    edges = sanitize_graph(nodes, connections)["edges"]
    assert {(e["from"], e["to"], e["output_index"], e["input_index"]) for e in edges} == {
        ("A", "C", 0, 1),
        ("A", "B", 1, 0),
    }
