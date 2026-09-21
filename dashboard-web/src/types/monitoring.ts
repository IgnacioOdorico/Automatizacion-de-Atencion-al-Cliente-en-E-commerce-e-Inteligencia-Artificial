import type { Channel } from '@/types/api';

/**
 * Contratos de GET /monitoring/* (ver docs/API_MONITOREO.md). La API devuelve
 * datos estructurados; las etiquetas en español las pone el front.
 */

export const EVENT_TYPES = [
  'order_received',
  'order_processed',
  'order_notified',
  'chat_message',
  'bot_reply',
  'ticket_created',
  'stock_alert',
] as const;

export type EventType = (typeof EVENT_TYPES)[number];

export type Severity = 'info' | 'success' | 'warning' | 'error';

export interface EventRefs {
  order_id: number | null;
  order_number: string | null;
  interaction_id: number | null;
  ticket_id: number | null;
}

/**
 * `type` y `severity` son `string` a propósito: un valor nuevo del backend se
 * muestra con una etiqueta genérica en vez de romper la pantalla. `data` es un
 * mapa abierto: cada tipo trae sus campos (se leen con guardas en lib/monitoring).
 */
export interface MonitoringEvent {
  id: string;
  type: string;
  ts: string;
  channel: Channel | null;
  severity: string;
  data: Record<string, unknown>;
  refs: EventRefs;
}

export interface EventsPage {
  /** Del más nuevo al más viejo. */
  items: MonitoringEvent[];
  has_more: boolean;
  newest_cursor: string | null;
  oldest_cursor: string | null;
}

export interface EventsParams {
  limit?: number;
  before?: string;
  since?: string;
  types?: readonly string[];
  channel?: Channel;
}

export interface MonitoringSummary {
  window_hours: number;
  generated_at: string;
  data_source: string;
  last_activity_at: string | null;
  bot: {
    interactions: number;
    avg_tmr_seconds: number | null;
    urgent: number;
    by_intent: Record<string, number>;
    by_channel: Record<string, number>;
  };
  orders: {
    total: number;
    by_status: Record<string, number>;
  };
  tickets: {
    created: number;
    open: number;
    by_priority: Record<string, number>;
  };
  stock_alerts: number;
  executions: {
    available: boolean;
    total: number;
    success: number;
    error: number;
    last_error_at: string | null;
  };
}

export interface ConversationSummary {
  channel: Channel;
  user_id: string;
  last_at: string;
  messages: number;
  last_intent: string | null;
  last_message_preview: string | null;
  has_urgent: boolean;
  open_tickets: number;
}

export interface ConversationsPage {
  items: ConversationSummary[];
  has_more: boolean;
  next_before: string | null;
}

export interface ConversationsParams {
  limit?: number;
  before?: string;
  channel?: Channel;
  q?: string;
}

export interface ThreadOrderRef {
  id: number;
  order_number: string;
  status: string;
}

/** El primer ticket asociado a la interacción (el contrato solo garantiza `id`). */
export interface ThreadTicketRef {
  id: number;
  status?: string | null;
  priority?: string | null;
}

export interface ThreadItem {
  interaction_id: number;
  received_at: string;
  message: string;
  responded_at: string | null;
  ai_response: string | null;
  intent: string | null;
  is_urgent: boolean;
  tmr_seconds: number | null;
  order: ThreadOrderRef | null;
  ticket: ThreadTicketRef | null;
}

export interface ThreadPage {
  channel: Channel;
  user_id: string;
  /** En orden cronológico (viejo a nuevo). */
  items: ThreadItem[];
  has_more: boolean;
  next_before: string | null;
}

export interface ThreadParams {
  channel: Channel;
  userId: string;
  limit?: number;
  before?: string;
}
