import type { StatusMeta } from '@/lib/domain';
import type { ExecutionSummary, WorkflowSummary } from '@/types/monitoring';

/**
 * Cómo se ven las ejecuciones y los workflows de n8n en la pestaña Workflow:
 * etiquetas en español, filtros, unión de páginas y workflow por defecto.
 * Lógica pura (sin React).
 */

/** Claves de ícono: el componente las resuelve a un SVG. Nunca solo color. */
export type StatusIconKey = 'check' | 'error' | 'clock' | 'skip' | 'info';

export interface StatusView extends StatusMeta {
  icon: StatusIconKey;
}

const EXECUTION_STATUS: Record<string, StatusView> = {
  success: { label: 'Correcta', tone: 'success', icon: 'check' },
  error: { label: 'Con error', tone: 'danger', icon: 'error' },
  crashed: { label: 'Interrumpida', tone: 'danger', icon: 'error' },
  running: { label: 'En curso', tone: 'brand', icon: 'clock' },
  waiting: { label: 'En espera', tone: 'warning', icon: 'clock' },
  new: { label: 'En cola', tone: 'neutral', icon: 'clock' },
  canceled: { label: 'Cancelada', tone: 'neutral', icon: 'skip' },
  unknown: { label: 'Sin estado', tone: 'neutral', icon: 'info' },
};

const has = (map: Record<string, unknown>, key: string): boolean =>
  Object.prototype.hasOwnProperty.call(map, key);

export function executionStatusMeta(status: string): StatusView {
  if (has(EXECUTION_STATUS, status)) return EXECUTION_STATUS[status];
  return { label: status || '—', tone: 'neutral', icon: 'info' };
}

/** Estado de un nodo dentro de una ejecución (o `missing`: el diagrama lo tiene y la traza no). */
const TRACE_STATUS: Record<string, StatusView> = {
  success: { label: 'Correcto', tone: 'success', icon: 'check' },
  error: { label: 'Con error', tone: 'danger', icon: 'error' },
  skipped: { label: 'No se ejecutó', tone: 'neutral', icon: 'skip' },
  running: { label: 'En curso', tone: 'brand', icon: 'clock' },
  waiting: { label: 'En espera', tone: 'warning', icon: 'clock' },
  canceled: { label: 'Cancelado', tone: 'neutral', icon: 'skip' },
  missing: { label: 'Sin datos en esta ejecución', tone: 'neutral', icon: 'info' },
};

/** Un estado que no se reconoce nunca se muestra como éxito: cae en "No se ejecutó". */
export function traceStatusMeta(status: string): StatusView {
  return has(TRACE_STATUS, status) ? TRACE_STATUS[status] : TRACE_STATUS.skipped;
}

const MODE_LABELS: Record<string, string> = {
  webhook: 'Entrada de datos',
  trigger: 'Disparador',
  manual: 'Manual',
  cli: 'Consola',
  retry: 'Reintento',
  error: 'Flujo de errores',
  integrated: 'Integrado',
  internal: 'Interno',
  evaluation: 'Evaluación',
};

export function executionModeLabel(mode: string | null | undefined): string {
  if (!mode) return '—';
  return has(MODE_LABELS, mode) ? MODE_LABELS[mode] : mode;
}

/** Opciones del filtro por estado; los valores son los que acepta `GET /monitoring/executions`. */
export const EXECUTION_STATUS_FILTERS: ReadonlyArray<{ value: string; label: string }> = [
  { value: '', label: 'Todas' },
  { value: 'success', label: 'Correctas' },
  { value: 'error', label: 'Con error' },
  { value: 'crashed', label: 'Interrumpidas' },
  { value: 'running', label: 'En curso' },
  { value: 'waiting', label: 'En espera' },
];

/**
 * Une la página fresca (que se refresca sola) con lo cargado a pedido con
 * "Cargar más": sin duplicados, de la más nueva a la más vieja. Si una
 * ejecución está en las dos, gana la fresca.
 */
export function mergeExecutionPages(
  first: readonly ExecutionSummary[],
  more: readonly ExecutionSummary[],
): ExecutionSummary[] {
  const byId = new Map<number, ExecutionSummary>();
  for (const item of more) byId.set(item.id, item);
  for (const item of first) byId.set(item.id, item);
  return [...byId.values()].sort((a, b) => b.id - a.id);
}

const startedAt = (w: WorkflowSummary): number =>
  w.last_execution ? Date.parse(w.last_execution.started_at) || 0 : 0;

/**
 * El workflow que se muestra al entrar: el activo con la actividad más
 * reciente; si ninguno corrió, el primer activo; si ninguno está activo, el de
 * actividad más reciente (o el primero).
 */
export function pickDefaultWorkflow(items: readonly WorkflowSummary[]): string | null {
  if (items.length === 0) return null;
  const best = (list: readonly WorkflowSummary[]): WorkflowSummary =>
    list.reduce((top, w) => (startedAt(w) > startedAt(top) ? w : top), list[0]);
  const active = items.filter((w) => w.active);
  return best(active.length > 0 ? active : items).id;
}

/** "12 ejecuciones en 24 h · 1 con error". */
export function workflowStats(workflow: WorkflowSummary): string {
  const { executions_24h: total, errors_24h: errors } = workflow;
  if (total === 0) return 'Sin ejecuciones en las últimas 24 h';
  const runs = total === 1 ? '1 ejecución' : `${total} ejecuciones`;
  const failed = errors === 0 ? 'sin errores' : `${errors} con error`;
  return `${runs} en 24 h · ${failed}`;
}
