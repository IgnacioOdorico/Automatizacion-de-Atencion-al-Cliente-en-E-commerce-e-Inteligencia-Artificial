/**
 * Datos de prueba con la forma exacta de docs/API_MONITOREO.md (anonimizados).
 */
import type {
  ConversationSummary,
  EventsPage,
  MonitoringEvent,
  ThreadItem,
} from '@/types/monitoring';

type EventOverrides = Partial<Omit<MonitoringEvent, 'data' | 'refs'>> & {
  refs?: Partial<MonitoringEvent['refs']>;
};

/** Evento con `id = <type>:<pk>` y refs completas en null salvo lo que se pise. */
export function makeEvent(
  type: string,
  pk: number,
  data: Record<string, unknown> = {},
  overrides: EventOverrides = {},
): MonitoringEvent {
  const { refs, ...rest } = overrides;
  return {
    id: `${type}:${pk}`,
    type,
    ts: '2026-09-21T14:03:22.418Z',
    channel: null,
    severity: 'info',
    data,
    refs: { order_id: null, order_number: null, interaction_id: null, ticket_id: null, ...refs },
    ...rest,
  };
}

/** Página del feed: `items` de más nuevo a más viejo; los cursores son opacos. */
export function makePage(
  items: MonitoringEvent[],
  extra: Partial<Omit<EventsPage, 'items'>> = {},
): EventsPage {
  return {
    items,
    has_more: false,
    newest_cursor: items.length ? `n:${items[0].id}` : null,
    oldest_cursor: items.length ? `o:${items[items.length - 1].id}` : null,
    ...extra,
  };
}

export function makeThreadItem(
  interactionId: number,
  overrides: Partial<ThreadItem> = {},
): ThreadItem {
  const second = (offset: number) => String((interactionId + offset) % 60).padStart(2, '0');
  return {
    interaction_id: interactionId,
    received_at: `2026-09-21T14:03:${second(0)}.000Z`,
    message: `Mensaje ${interactionId}`,
    responded_at: `2026-09-21T14:03:${second(2)}.000Z`,
    ai_response: `Respuesta ${interactionId}`,
    intent: 'FAQ',
    is_urgent: false,
    tmr_seconds: 2.5,
    order: null,
    ticket: null,
    ...overrides,
  };
}

export function makeConversation(
  overrides: Partial<ConversationSummary> = {},
): ConversationSummary {
  return {
    channel: 'whatsapp',
    user_id: '5492610000000',
    last_at: '2026-09-21T14:03:20.001Z',
    messages: 4,
    last_intent: 'ESTADO_PEDIDO',
    last_message_preview: '¿Dónde está mi pedido ORD-2026-0007?',
    has_urgent: false,
    open_tickets: 0,
    ...overrides,
  };
}
