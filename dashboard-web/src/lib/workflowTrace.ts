import { edgeKey } from '@/lib/workflowGraph';
import type { ExecutionDetail, GraphEdge, TraceNode, WorkflowGraph } from '@/types/monitoring';

/**
 * Cruza el grafo de un workflow con la traza de una ejecución: estado de cada
 * nodo y de cada conexión para iluminar el camino recorrido. Lógica pura.
 */

/**
 * `plain`: sin ejecución elegida. `missing`: el nodo está en el diagrama pero la
 * traza no lo trae. `pending`: se ejecutó pero la reproducción todavía no llegó.
 */
export type NodeVisual =
  | 'plain'
  | 'success'
  | 'error'
  | 'skipped'
  | 'running'
  | 'waiting'
  | 'canceled'
  | 'missing'
  | 'pending';

export type EdgeVisual = 'idle' | 'active' | 'inactive';

export interface NodeOverlay {
  visual: NodeVisual;
  trace: TraceNode | null;
}

export interface EdgeOverlay {
  visual: EdgeVisual;
  /** La conexión por la que "está entrando" la reproducción al nodo actual. */
  flowing: boolean;
}

export interface Overlay {
  nodes: Map<string, NodeOverlay>;
  edges: Map<string, EdgeOverlay>;
  /** El nodo que la reproducción acaba de alcanzar; `null` en la vista final. */
  current: string | null;
  /** Hay una traza con nodos: si no, el diagrama se muestra sin pintar. */
  hasTrace: boolean;
}

const EXECUTED_VISUALS = new Set<string>(['success', 'error', 'running', 'waiting', 'canceled']);

/** El nodo corrió (o está corriendo): cualquier estado que no sea "no se ejecutó". */
function ran(node: TraceNode | undefined): node is TraceNode {
  return node !== undefined && EXECUTED_VISUALS.has(node.status);
}

/**
 * ¿Se recorrió esta conexión? Un nodo produjo items por esa salida
 * (`outputs[output_index] > 0`) y el destino se ejecutó. Las conexiones de IA
 * (sub-nodo -> nodo) no pasan por una salida "main": valen si ambos corrieron.
 */
export function isEdgeTraversed(edge: GraphEdge, byName: ReadonlyMap<string, TraceNode>): boolean {
  const from = byName.get(edge.from);
  const to = byName.get(edge.to);
  if (!ran(from) || !ran(to)) return false;
  if (edge.kind !== 'main') return true;
  return (from.outputs[edge.output_index] ?? 0) > 0;
}

/**
 * El orden en que corrieron los nodos: el `path` de la API; si no lo trae,
 * los nodos ejecutados en el orden del workflow.
 */
export function effectivePath(detail: ExecutionDetail | null): string[] {
  if (!detail) return [];
  if (detail.path.length > 0) return detail.path;
  return detail.nodes.filter((n) => ran(n)).map((n) => n.name);
}

interface OverlayOptions {
  /** Cuántos nodos del camino ya se revelaron (reproducción). `null`/omitido o >= total = vista final. */
  revealed?: number | null;
}

function visualOf(status: string): NodeVisual {
  if (EXECUTED_VISUALS.has(status)) return status as NodeVisual;
  return 'skipped';
}

export function buildOverlay(
  graph: WorkflowGraph,
  detail: ExecutionDetail | null,
  options: OverlayOptions = {},
): Overlay {
  const hasTrace = detail !== null && detail.nodes.length > 0;
  const nodes = new Map<string, NodeOverlay>();
  const edges = new Map<string, EdgeOverlay>();

  if (!hasTrace || detail === null) {
    for (const node of graph.nodes) nodes.set(node.name, { visual: 'plain', trace: null });
    for (const edge of graph.edges) edges.set(edgeKey(edge), { visual: 'idle', flowing: false });
    return { nodes, edges, current: null, hasTrace: false };
  }

  const byName = new Map(detail.nodes.map((n) => [n.name, n]));
  const path = effectivePath(detail);
  const partial =
    options.revealed !== null &&
    options.revealed !== undefined &&
    options.revealed >= 0 &&
    options.revealed < path.length;
  const revealedNames = partial ? new Set(path.slice(0, options.revealed as number)) : null;
  const current = partial && (options.revealed as number) > 0 ? path[(options.revealed as number) - 1] : null;

  for (const node of graph.nodes) {
    const trace = byName.get(node.name);
    if (!trace) {
      nodes.set(node.name, { visual: 'missing', trace: null });
      continue;
    }
    let visual = visualOf(trace.status);
    if (revealedNames && ran(trace) && !revealedNames.has(node.name)) visual = 'pending';
    nodes.set(node.name, { visual, trace });
  }

  for (const edge of graph.edges) {
    let active = isEdgeTraversed(edge, byName);
    if (active && revealedNames) active = revealedNames.has(edge.from) && revealedNames.has(edge.to);
    edges.set(edgeKey(edge), {
      visual: active ? 'active' : 'inactive',
      flowing: active && current !== null && edge.to === current,
    });
  }

  return { nodes, edges, current, hasTrace: true };
}

export interface TraceNotes {
  /** Nodos del diagrama que la traza no trae (el workflow cambió después de la ejecución). */
  missing: string[];
  /** Nodos de la traza que ya no existen en el workflow actual. */
  extra: TraceNode[];
  truncated: boolean;
  /** Por qué no se pudo leer la traza (texto de la API), si no se pudo. */
  readError: string | null;
}

export function traceNotes(graph: WorkflowGraph, detail: ExecutionDetail | null): TraceNotes {
  if (!detail) return { missing: [], extra: [], truncated: false, readError: null };
  const inGraph = new Set(graph.nodes.map((n) => n.name));
  const inTrace = new Set(detail.nodes.map((n) => n.name));
  const hasTrace = detail.nodes.length > 0;
  return {
    missing: hasTrace ? graph.nodes.map((n) => n.name).filter((name) => !inTrace.has(name)) : [],
    extra: detail.nodes.filter((n) => !inGraph.has(n.name)),
    truncated: detail.truncated,
    readError: detail.error,
  };
}
