/**
 * Datos de prueba de la pestaña Workflow con la forma exacta de
 * docs/API_MONITOREO.md §4. Los grafos usan los nombres, tipos, posiciones y
 * conexiones reales de los Flujos 1 y 2 (workflows/*.json); las trazas se armaron
 * con el formato observado en la ejecución real disponible (anonimizadas).
 */
import type {
  ExecutionDetail,
  ExecutionSummary,
  GraphEdge,
  GraphNode,
  TraceNode,
  WorkflowGraph,
  WorkflowSummary,
} from '@/types/monitoring';

function graphOf(
  id: string,
  name: string,
  nodes: Array<[string, string, number, number]>,
  edges: Array<[string, string, number?, string?]>,
): WorkflowGraph {
  const graphNodes: GraphNode[] = nodes.map(([n, shortType, x, y]) => ({
    name: n,
    type: `n8n-nodes-base.${shortType}`,
    short_type: shortType,
    position: [x, y],
    disabled: false,
  }));
  const graphEdges: GraphEdge[] = edges.map(([from, to, output = 0, kind = 'main']) => ({
    from,
    to,
    output_index: output,
    input_index: 0,
    kind,
  }));
  const xs = graphNodes.map((n) => n.position[0]);
  const ys = graphNodes.map((n) => n.position[1]);
  return {
    id,
    name,
    active: true,
    nodes: graphNodes,
    edges: graphEdges,
    bounds: { min_x: Math.min(...xs), min_y: Math.min(...ys), max_x: Math.max(...xs), max_y: Math.max(...ys) },
  };
}

export const FLUJO1_ID = '797bI0eXTmiaSmvJ';
export const FLUJO2_ID = 'Qm2Xc9ChatbotOmni';

export const flujo1Graph: WorkflowGraph = graphOf(
  FLUJO1_ID,
  'Flujo 1 — Pipeline de Procesamiento de Órdenes',
  [
    ['Webhook - Recibir Orden', 'webhook', -960, 144],
    ['Registrar Orden', 'postgres', -720, 144],
    ['Verificar Stock', 'postgres', -480, 144],
    ['IF Stock Disponible', 'if', -240, 144],
    ['Actualizar Stock', 'postgres', 0, 0],
    ['Confirmar Orden', 'postgres', 720, 0],
    ['Enviar Email Confirmación', 'emailSend', 960, 0],
    ['Registrar Notificación', 'postgres', 1200, 0],
    ['Respuesta Confirmada', 'respondToWebhook', 1440, 0],
    ['Marcar Sin Stock', 'postgres', 0, 304],
    ['Enviar Email Sin Stock', 'emailSend', 240, 304],
    ['Respuesta Sin Stock', 'respondToWebhook', 656, 304],
    ['Registrar Notificación Sin Stock', 'postgres', 448, 304],
    ['IF Stock Bajo', 'if', 240, 176],
    ['Registrar Alerta Stock Bajo', 'postgres', 480, 288],
  ],
  [
    ['Webhook - Recibir Orden', 'Registrar Orden'],
    ['Registrar Orden', 'Verificar Stock'],
    ['Verificar Stock', 'IF Stock Disponible'],
    ['IF Stock Disponible', 'Actualizar Stock', 0],
    ['IF Stock Disponible', 'Marcar Sin Stock', 1],
    ['Actualizar Stock', 'IF Stock Bajo'],
    ['Confirmar Orden', 'Enviar Email Confirmación'],
    ['Enviar Email Confirmación', 'Registrar Notificación'],
    ['Registrar Notificación', 'Respuesta Confirmada'],
    ['Marcar Sin Stock', 'Enviar Email Sin Stock'],
    ['Enviar Email Sin Stock', 'Registrar Notificación Sin Stock'],
    ['Registrar Notificación Sin Stock', 'Respuesta Sin Stock'],
    ['IF Stock Bajo', 'Registrar Alerta Stock Bajo', 0],
    ['IF Stock Bajo', 'Confirmar Orden', 1],
    ['Registrar Alerta Stock Bajo', 'Confirmar Orden'],
  ],
);

export const flujo2Graph: WorkflowGraph = graphOf(
  FLUJO2_ID,
  'Flujo 2 — Chatbot WhatsApp + Telegram',
  [
    ['Trigger Telegram', 'telegramTrigger', -1900, 0],
    ['Trigger WhatsApp Business', 'webhook', -1900, 400],
    ['Normalizar Mensaje', 'function', -1340, 200],
    ['Buscar FAQ', 'postgres', -1100, 200],
    ['Preparar Contexto FAQ', 'function', -860, 200],
    ['IA - Motor Decision', 'chainLlm', -620, 200],
    ['OpenAI Chat Model', 'lmChatOpenAi', -652, 400],
    ['Parse JSON', 'function', -380, 200],
    ['Switch Intent', 'switch', -140, 200],
    ['Buscar Pedido', 'postgres', 100, 0],
    ['Preparar Respuesta Pedido', 'function', 340, 0],
    ['Crear Ticket', 'postgres', 100, 400],
    ['Preparar Respuesta Ticket', 'function', 340, 400],
    ['Router Canal', 'if', 820, 200],
    ['Enviar Telegram', 'telegram', 1060, 60],
    ['Enviar Respuesta (Producción)', 'emailSend', 1060, 340],
    ['Registrar Interacción', 'postgres', 1320, 200],
  ],
  [
    ['Trigger Telegram', 'Normalizar Mensaje'],
    ['Trigger WhatsApp Business', 'Normalizar Mensaje'],
    ['Normalizar Mensaje', 'Buscar FAQ'],
    ['Buscar FAQ', 'Preparar Contexto FAQ'],
    ['Preparar Contexto FAQ', 'IA - Motor Decision'],
    ['IA - Motor Decision', 'Parse JSON'],
    ['OpenAI Chat Model', 'IA - Motor Decision', 0, 'ai_languageModel'],
    ['Parse JSON', 'Switch Intent'],
    ['Switch Intent', 'Router Canal', 0],
    ['Switch Intent', 'Buscar Pedido', 1],
    ['Switch Intent', 'Crear Ticket', 2],
    ['Switch Intent', 'Router Canal', 3],
    ['Buscar Pedido', 'Preparar Respuesta Pedido'],
    ['Preparar Respuesta Pedido', 'Router Canal'],
    ['Crear Ticket', 'Preparar Respuesta Ticket'],
    ['Preparar Respuesta Ticket', 'Router Canal'],
    ['Router Canal', 'Enviar Telegram', 0],
    ['Router Canal', 'Enviar Respuesta (Producción)', 1],
    ['Enviar Telegram', 'Registrar Interacción'],
    ['Enviar Respuesta (Producción)', 'Registrar Interacción'],
  ],
);

export function makeTraceNode(
  name: string,
  status: string,
  overrides: Partial<TraceNode> = {},
): TraceNode {
  const executed = status !== 'skipped';
  return {
    name,
    short_type: null,
    status,
    started_at: executed ? '2026-09-21T14:03:20.010Z' : null,
    duration_ms: executed ? 3 : null,
    items_out: executed ? 1 : 0,
    outputs: executed ? [1] : [],
    runs: executed ? 1 : 0,
    error: null,
    output_preview: executed ? [{ ok: true }] : null,
    output_truncated: false,
    ...overrides,
  };
}

export function makeExecution(id: number, overrides: Partial<ExecutionSummary> = {}): ExecutionSummary {
  return {
    id,
    workflow_id: FLUJO1_ID,
    workflow_name: flujo1Graph.name,
    status: 'success',
    mode: 'webhook',
    started_at: '2026-09-21T14:03:20.000Z',
    stopped_at: '2026-09-21T14:03:20.435Z',
    duration_ms: 435,
    error_message: null,
    ...overrides,
  };
}

function detailOf(
  execution: ExecutionSummary,
  graph: WorkflowGraph,
  executed: Record<string, Partial<TraceNode>>,
  path: string[],
): ExecutionDetail {
  const nodes = graph.nodes.map((n) => {
    const over = executed[n.name];
    return over
      ? makeTraceNode(n.name, 'success', { short_type: n.short_type, ...over })
      : makeTraceNode(n.name, 'skipped', { short_type: n.short_type });
  });
  return {
    execution,
    workflow_id: graph.id,
    nodes,
    path,
    last_node_executed: path[path.length - 1] ?? null,
    truncated: false,
    error: null,
  };
}

export const CON_STOCK_PATH = [
  'Webhook - Recibir Orden',
  'Registrar Orden',
  'Verificar Stock',
  'IF Stock Disponible',
  'Actualizar Stock',
  'IF Stock Bajo',
  'Confirmar Orden',
  'Enviar Email Confirmación',
  'Registrar Notificación',
  'Respuesta Confirmada',
];

/** Pedido con stock (y stock no bajo): el IF Stock Disponible sale por "Sí" y el IF Stock Bajo por "No". */
export function traceConStock(id = 15): ExecutionDetail {
  const executed: Record<string, Partial<TraceNode>> = {};
  for (const name of CON_STOCK_PATH) executed[name] = {};
  executed['IF Stock Disponible'] = { outputs: [1, 0], duration_ms: 1, output_preview: [{ stock: 10 }] };
  executed['IF Stock Bajo'] = { outputs: [0, 1], duration_ms: 1 };
  return detailOf(makeExecution(id), flujo1Graph, executed, CON_STOCK_PATH);
}

export const SIN_STOCK_PATH = [
  'Webhook - Recibir Orden',
  'Registrar Orden',
  'Verificar Stock',
  'IF Stock Disponible',
  'Marcar Sin Stock',
  'Enviar Email Sin Stock',
  'Registrar Notificación Sin Stock',
  'Respuesta Sin Stock',
];

/** Pedido sin stock: el IF Stock Disponible sale por "No". */
export function traceSinStock(id = 14): ExecutionDetail {
  const executed: Record<string, Partial<TraceNode>> = {};
  for (const name of SIN_STOCK_PATH) executed[name] = {};
  executed['IF Stock Disponible'] = { outputs: [0, 1], duration_ms: 1 };
  return detailOf(makeExecution(id), flujo1Graph, executed, SIN_STOCK_PATH);
}

/** Como la ejecución 1 real: falla "Registrar Orden" y el resto no corre. */
export function traceError(id = 1): ExecutionDetail {
  const execution = makeExecution(id, {
    status: 'error',
    duration_ms: 49,
    error_message: 'Credential with ID "[REDACTADO]" does not exist for type "postgres".',
  });
  const detail = detailOf(
    execution,
    flujo1Graph,
    {
      'Webhook - Recibir Orden': {},
      'Registrar Orden': {
        outputs: [],
        items_out: 0,
        output_preview: null,
        error: { message: 'Credential does not exist', description: 'Configurá la credencial de Postgres.' },
      },
    },
    ['Webhook - Recibir Orden', 'Registrar Orden'],
  );
  const failing = detail.nodes.find((n) => n.name === 'Registrar Orden');
  if (failing) failing.status = 'error';
  return detail;
}

export function makeWorkflowSummary(
  id: string,
  name: string,
  overrides: Partial<WorkflowSummary> = {},
): WorkflowSummary {
  return {
    id,
    name,
    active: true,
    updated_at: '2026-09-21T01:06:00.678Z',
    executions_24h: 12,
    errors_24h: 1,
    last_execution: { id: 15, status: 'success', started_at: '2026-09-21T14:03:20.000Z', duration_ms: 435 },
    ...overrides,
  };
}
