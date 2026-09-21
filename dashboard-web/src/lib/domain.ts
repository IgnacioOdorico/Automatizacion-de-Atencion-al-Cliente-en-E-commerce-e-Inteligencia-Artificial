/**
 * Dominios canónicos de estado/label del dashboard.
 * Fuente: CHECK constraints de init_simple.sql (orders.status, tickets.status,
 * tickets.priority) — NO inventar valores nuevos.
 */

export const ORDER_STATUSES = [
  'pending',
  'processing',
  'confirmed',
  'shipped',
  'delivered',
  'no_stock',
  'cancelled',
  'error',
] as const;

export const TICKET_STATUSES = ['open', 'in_progress', 'resolved', 'closed'] as const;

export const INTENTS = ['FAQ', 'ESTADO_PEDIDO', 'RECLAMO', 'GENERAL'] as const;

export const TICKET_PRIORITIES = ['low', 'normal', 'high', 'urgent'] as const;

export interface StatusMeta {
  label: string;
  tone: 'brand' | 'neutral' | 'success' | 'warning' | 'danger';
}

const ORDER_STATUS_META: Record<string, StatusMeta> = {
  pending: { label: 'Pendiente', tone: 'neutral' },
  processing: { label: 'Procesando', tone: 'brand' },
  confirmed: { label: 'Confirmado', tone: 'success' },
  shipped: { label: 'Enviado', tone: 'brand' },
  delivered: { label: 'Entregado', tone: 'success' },
  no_stock: { label: 'Sin stock', tone: 'warning' },
  cancelled: { label: 'Cancelado', tone: 'neutral' },
  error: { label: 'Error', tone: 'danger' },
};

const TICKET_STATUS_META: Record<string, StatusMeta> = {
  open: { label: 'Abierto', tone: 'brand' },
  in_progress: { label: 'En curso', tone: 'warning' },
  resolved: { label: 'Resuelto', tone: 'success' },
  closed: { label: 'Cerrado', tone: 'neutral' },
};

const PRIORITY_META: Record<string, StatusMeta> = {
  low: { label: 'Baja', tone: 'neutral' },
  normal: { label: 'Normal', tone: 'neutral' },
  high: { label: 'Alta', tone: 'warning' },
  urgent: { label: 'Urgente', tone: 'danger' },
};

const INTENT_META: Record<string, StatusMeta> = {
  FAQ: { label: 'Pregunta frecuente', tone: 'neutral' },
  ESTADO_PEDIDO: { label: 'Estado de pedido', tone: 'brand' },
  RECLAMO: { label: 'Reclamo', tone: 'warning' },
  GENERAL: { label: 'Consulta general', tone: 'neutral' },
};

/** Fallback neutral: la BD está restringida por CHECK, pero un valor raro no debe romper la UI. */
function meta(map: Record<string, StatusMeta>, value: string | null | undefined): StatusMeta {
  if (value && map[value]) return map[value];
  return { label: value || '—', tone: 'neutral' };
}

export function orderStatusMeta(status: string | null | undefined): StatusMeta {
  return meta(ORDER_STATUS_META, status);
}

export function ticketStatusMeta(status: string | null | undefined): StatusMeta {
  return meta(TICKET_STATUS_META, status);
}

export function priorityMeta(priority: string | null | undefined): StatusMeta {
  return meta(PRIORITY_META, priority);
}

/** Intent con que el bot clasificó el mensaje, en palabras del cliente (no el código interno). */
export function intentMeta(intent: string | null | undefined): StatusMeta {
  return meta(INTENT_META, intent);
}
