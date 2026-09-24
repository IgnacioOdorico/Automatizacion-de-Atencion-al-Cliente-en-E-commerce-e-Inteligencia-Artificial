"""Grafo sanitizado de un workflow de n8n.

De cada nodo solo salen nombre, tipo, posición y si está deshabilitado. NUNCA salen
`parameters`, `credentials`, `webhookId`, notas ni ningún otro campo: se construye
una lista blanca explícita, no se filtra una lista negra.
"""

from typing import Any

STICKY_NOTE = "n8n-nodes-base.stickyNote"
MAX_NODES = 500


def short_type(node_type: str) -> str:
    """Última parte del tipo: `n8n-nodes-base.emailSend` -> `emailSend`."""
    return node_type.rsplit(".", 1)[-1]


def _position(raw: Any) -> list[float | int]:
    if (
        isinstance(raw, (list, tuple))
        and len(raw) == 2
        and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in raw)
    ):
        return [raw[0], raw[1]]
    return [0, 0]


def sanitize_nodes(raw_nodes: Any) -> list[dict]:
    """Lista blanca de nodos; sin notas adhesivas y con nombres únicos."""
    nodes: list[dict] = []
    seen: set[str] = set()
    if not isinstance(raw_nodes, list):
        return nodes
    for raw in raw_nodes[:MAX_NODES]:
        if not isinstance(raw, dict):
            continue
        name = raw.get("name")
        node_type = raw.get("type")
        if not isinstance(name, str) or not name or name in seen:
            continue
        node_type = node_type if isinstance(node_type, str) else ""
        if node_type == STICKY_NOTE:
            continue
        seen.add(name)
        nodes.append(
            {
                "name": name,
                "type": node_type,
                "short_type": short_type(node_type),
                "position": _position(raw.get("position")),
                "disabled": raw.get("disabled") is True,
            }
        )
    return nodes


def _edges(connections: Any, names: set[str]) -> list[dict]:
    """`connections[origen][tipo][output_index] = [{node, type, index}]`."""
    edges: list[dict] = []
    if not isinstance(connections, dict):
        return edges
    for source, by_kind in connections.items():
        if source not in names or not isinstance(by_kind, dict):
            continue
        for kind, outputs in by_kind.items():
            if not isinstance(outputs, list):
                continue
            for output_index, targets in enumerate(outputs):
                if not isinstance(targets, list):
                    continue
                for target in targets:
                    if not isinstance(target, dict):
                        continue
                    destination = target.get("node")
                    input_index = target.get("index", 0)
                    if destination not in names or isinstance(input_index, bool):
                        continue
                    if not isinstance(input_index, int):
                        input_index = 0
                    edges.append(
                        {
                            "from": source,
                            "to": destination,
                            "output_index": output_index,
                            "input_index": input_index,
                            "kind": str(kind),
                        }
                    )
    return edges


def sanitize_graph(raw_nodes: Any, raw_connections: Any) -> dict:
    nodes = sanitize_nodes(raw_nodes)
    names = {node["name"] for node in nodes}
    xs = [node["position"][0] for node in nodes] or [0]
    ys = [node["position"][1] for node in nodes] or [0]
    return {
        "nodes": nodes,
        "edges": _edges(raw_connections, names),
        "bounds": {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)},
    }
