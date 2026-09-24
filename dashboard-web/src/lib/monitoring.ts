import {
  intentMeta,
  orderStatusMeta,
  priorityMeta,
  ticketStatusMeta,
  type StatusMeta,
} from '@/lib/domain';
import {
  CHANNEL_LABELS,
  formatContact,
  formatCurrency,
  formatDateTimeSeconds,
  formatTmr,
} from '@/lib/format';
import type { EventType, MonitoringEvent } from '@/types/monitoring';

/**
 * Cómo se ve cada evento del feed en vivo. Lógica pura (sin React): traduce el
 * dato estructurado de la API a etiquetas en español, chips y pares
 * "etiqueta: valor". Los textos de clientes y del bot pasan sin tocar: son
 * datos NO confiables y se dibujan siempre como texto.
 */

type Tone = StatusMeta['tone'];

/** Claves de ícono: el componente las resuelve a un SVG (esta capa no importa React). */
export type EventIconKey =
  | 'package'
  | 'gear'
  | 'mail'
  | 'message'
  | 'bot'
  | 'ticket'
  | 'stock'
  | 'activity';

export interface EventTypeMeta {
  label: string;
  icon: EventIconKey;
}

const TYPE_META: Record<EventType, EventTypeMeta> = {
  order_received: { label: 'Pedido recibido', icon: 'package' },
  order_processed: { label: 'Pedido procesado', icon: 'gear' },
  order_notified: { label: 'Cliente notificado', icon: 'mail' },
  chat_message: { label: 'Mensaje del cliente', icon: 'message' },
  bot_reply: { label: 'Respuesta del bot', icon: 'bot' },
  ticket_created: { label: 'Ticket creado', icon: 'ticket' },
  stock_alert: { label: 'Alerta de stock bajo', icon: 'stock' },
};

/** Opciones de los filtros por tipo, en el orden del ciclo del pedido y del chat. */
export const EVENT_TYPE_OPTIONS: ReadonlyArray<{ value: EventType; label: string }> = (
  Object.keys(TYPE_META) as EventType[]
).map((value) => ({ value, label: TYPE_META[value].label }));

const GENERIC_TYPE: EventTypeMeta = { label: 'Evento', icon: 'activity' };

export function eventTypeMeta(type: string): EventTypeMeta {
  return Object.prototype.hasOwnProperty.call(TYPE_META, type)
    ? TYPE_META[type as EventType]
    : GENERIC_TYPE;
}

export type SeverityIconKey = 'info' | 'check' | 'warning' | 'error';

export interface SeverityMeta {
  label: string;
  tone: Tone;
  icon: SeverityIconKey;
}

const SEVERITY_META: Record<string, SeverityMeta> = {
  info: { label: 'Info', tone: 'brand', icon: 'info' },
  success: { label: 'Correcto', tone: 'success', icon: 'check' },
  warning: { label: 'Atención', tone: 'warning', icon: 'warning' },
  error: { label: 'Error', tone: 'danger', icon: 'error' },
};

/** La severidad se comunica con color, ícono y texto: nunca solo con color. */
export function severityMeta(severity: string): SeverityMeta {
  return Object.prototype.hasOwnProperty.call(SEVERITY_META, severity)
    ? SEVERITY_META[severity]
    : SEVERITY_META.info;
}

export interface EventChip {
  text: string;
  tone: Tone;
}

export interface EventFact {
  label: string;
  value: string;
  /** Texto largo (mensajes del cliente o del bot): se muestra como bloque, respetando saltos de línea. */
  block?: boolean;
}

export interface EventView {
  typeLabel: string;
  icon: EventIconKey;
  /** Línea principal de la tarjeta. */
  headline: string;
  /** Línea secundaria (producto, tiempos, unidades). */
  detail: string | null;
  /** Texto exacto del cliente o del bot, sin recortar ni normalizar. */
  quote: string | null;
  chips: EventChip[];
  /** Todos los datos exactos del evento, para el detalle. */
  facts: EventFact[];
}

// ---------- lectura defensiva de `data` ----------

/** Texto tal cual (sin trim): los mensajes se muestran exactos. Vacío o no textual es "sin dato". */
function str(value: unknown): string | null {
  if (typeof value === 'string') return value === '' ? null : value;
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  return null;
}

/** Número o texto numérico ("349.99", como serializa la BD). */
function num(value: unknown): number | null {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  if (typeof value === 'string' && value.trim() !== '') {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

const DASH = '—';
const orDash = (value: string | null): string => value ?? DASH;

function joinParts(parts: Array<string | null>, separator = ' · '): string | null {
  const present = parts.filter((p): p is string => p !== null);
  return present.length > 0 ? present.join(separator) : null;
}

function money(value: unknown): string | null {
  const n = num(value);
  return n === null ? null : formatCurrency(n);
}

function timing(seconds: unknown, template: (formatted: string) => string): string | null {
  const n = num(seconds);
  return n === null ? null : template(formatTmr(n));
}

function statusChip(status: unknown): EventChip | null {
  const value = str(status);
  if (value === null) return null;
  const meta = orderStatusMeta(value);
  return { text: meta.label, tone: meta.tone };
}

function compact<T>(items: Array<T | null>): T[] {
  return items.filter((item): item is T => item !== null);
}

/**
 * Marcas de una respuesta del bot: cómo clasificó el mensaje, si es urgente y
 * cuánto tardó (TMR). Todas con texto; la que no tiene dato no se inventa.
 */
export function botReplyChips(
  intent: string | null | undefined,
  urgent: boolean,
  tmrSeconds: number | null | undefined,
): EventChip[] {
  const intentInfo = intent ? intentMeta(intent) : null;
  const tmr = typeof tmrSeconds === 'number' && Number.isFinite(tmrSeconds) ? tmrSeconds : null;
  return compact<EventChip>([
    intentInfo ? { text: intentInfo.label, tone: intentInfo.tone } : null,
    urgent ? { text: 'Urgente', tone: 'danger' } : null,
    tmr === null ? null : { text: `TMR ${formatTmr(tmr)}`, tone: 'neutral' },
  ]);
}

function productLabel(name: string | null, sku: string | null): string | null {
  if (name && sku) return `${name} (${sku})`;
  return name ?? sku;
}

function stockDetail(actual: number | null, min: number | null): string | null {
  const minPart = min === null ? null : `mínimo ${min}`;
  let now: string | null = null;
  if (actual === 0) now = 'Sin stock';
  else if (actual === 1) now = 'Queda 1 unidad';
  else if (actual !== null) now = `Quedan ${actual} unidades`;
  return joinParts([now, minPart]);
}

function factsOf(pairs: Array<[string, string | null, boolean?]>): EventFact[] {
  return pairs.map(([label, value, block]) => {
    const fact: EventFact = { label, value: orDash(value) };
    if (block) fact.block = true;
    return fact;
  });
}

function genericFacts(data: Record<string, unknown>): EventFact[] {
  return Object.entries(data).map(([label, value]) => {
    let text: string;
    if (value === null || value === undefined) text = DASH;
    else if (typeof value === 'string') text = value;
    else if (typeof value === 'object') text = JSON.stringify(value);
    else text = String(value);
    return { label, value: text };
  });
}

/** Arma todo lo que se dibuja de un evento. Nunca lanza: un campo ausente es "—". */
export function describeEvent(event: MonitoringEvent): EventView {
  const { label: typeLabel, icon } = eventTypeMeta(event.type);
  const d = event.data ?? {};
  const channelLabel = event.channel ? (CHANNEL_LABELS[event.channel] ?? event.channel) : null;
  const common: EventFact[] = factsOf([
    ['Fecha y hora', formatDateTimeSeconds(event.ts)],
    ...(channelLabel ? ([['Canal', channelLabel]] as Array<[string, string | null]>) : []),
  ]);

  const base = { typeLabel, icon, detail: null, quote: null, chips: [] as EventChip[] };

  switch (event.type) {
    case 'order_received': {
      const orderNumber = str(d.order_number);
      const customer = str(d.customer_name);
      const product = str(d.product_name);
      const quantity = num(d.quantity);
      const item = product && quantity !== null ? `${quantity} × ${product}` : product;
      return {
        ...base,
        headline: joinParts([orderNumber, customer]) ?? DASH,
        detail: joinParts([item, money(d.total_amount)]),
        facts: [
          ...common,
          ...factsOf([
            ['Pedido', orderNumber],
            ['Cliente', customer],
            ['Email', str(d.customer_email)],
            ['Producto', productLabel(product, str(d.product_sku))],
            ['Cantidad', quantity === null ? null : String(quantity)],
            ['Total', money(d.total_amount)],
          ]),
        ],
      };
    }

    case 'order_processed': {
      const chip = statusChip(d.status);
      return {
        ...base,
        headline: joinParts([str(d.order_number), chip?.text ?? null]) ?? DASH,
        detail: timing(d.mttd_seconds, (t) => `Procesado en ${t} (MTTD)`),
        chips: compact([chip]),
        facts: [
          ...common,
          ...factsOf([
            ['Pedido', str(d.order_number)],
            ['Estado', chip?.text ?? null],
            ['Total', money(d.total_amount)],
            ['Tiempo de procesamiento (MTTD)', timing(d.mttd_seconds, (t) => t)],
          ]),
        ],
      };
    }

    case 'order_notified': {
      const chip = statusChip(d.status);
      return {
        ...base,
        headline: joinParts([str(d.order_number), chip?.text ?? null]) ?? DASH,
        detail: timing(d.mttr_seconds, (t) => `Avisado en ${t} (MTTR)`),
        chips: compact([chip]),
        facts: [
          ...common,
          ...factsOf([
            ['Pedido', str(d.order_number)],
            ['Estado', chip?.text ?? null],
            ['Tiempo hasta avisar al cliente (MTTR)', timing(d.mttr_seconds, (t) => t)],
          ]),
        ],
      };
    }

    case 'chat_message': {
      const userId = str(d.user_id);
      const message = typeof d.message === 'string' && d.message !== '' ? d.message : null;
      return {
        ...base,
        headline: userId ? formatContact(event.channel ?? '', userId) : DASH,
        quote: message,
        facts: [...common, ...factsOf([['Usuario', userId], ['Mensaje', message, true]])],
      };
    }

    case 'bot_reply': {
      const userId = str(d.user_id);
      const reply = typeof d.ai_response === 'string' && d.ai_response !== '' ? d.ai_response : null;
      const intent = str(d.intent);
      const intentInfo = intent ? intentMeta(intent) : null;
      const urgent = d.is_urgent === true;
      const tmr = num(d.tmr_seconds);
      return {
        ...base,
        headline: userId ? formatContact(event.channel ?? '', userId) : DASH,
        quote: reply,
        chips: botReplyChips(intent, urgent, tmr),
        facts: [
          ...common,
          ...factsOf([
            ['Usuario', userId],
            ['Intención', intentInfo?.label ?? null],
            ['Urgente', urgent ? 'Sí' : 'No'],
            ['Tiempo de respuesta (TMR)', tmr === null ? null : formatTmr(tmr)],
            ['Respuesta', reply, true],
          ]),
        ],
      };
    }

    case 'ticket_created': {
      const userId = str(d.user_id);
      const priority = str(d.priority);
      const status = str(d.status);
      const priorityInfo = priority ? priorityMeta(priority) : null;
      const statusInfo = status ? ticketStatusMeta(status) : null;
      return {
        ...base,
        headline: str(d.subject) ?? 'Ticket sin asunto',
        detail: userId ? formatContact(event.channel ?? '', userId) : null,
        chips: compact<EventChip>([
          priorityInfo
            ? { text: `Prioridad ${priorityInfo.label.toLowerCase()}`, tone: priorityInfo.tone }
            : null,
          statusInfo ? { text: statusInfo.label, tone: statusInfo.tone } : null,
        ]),
        facts: [
          ...common,
          ...factsOf([
            ['Asunto', str(d.subject)],
            ['Usuario', userId],
            ['Prioridad', priorityInfo?.label ?? null],
            ['Estado', statusInfo?.label ?? null],
          ]),
        ],
      };
    }

    case 'stock_alert': {
      const name = str(d.product_name);
      const sku = str(d.sku);
      const actual = num(d.stock_actual);
      const min = num(d.stock_min);
      return {
        ...base,
        headline: productLabel(name, sku) ?? DASH,
        detail: stockDetail(actual, min),
        facts: [
          ...common,
          ...factsOf([
            ['Producto', name],
            ['SKU', sku],
            ['Stock actual', actual === null ? null : String(actual)],
            ['Stock mínimo', min === null ? null : String(min)],
          ]),
        ],
      };
    }

    default:
      return {
        ...base,
        headline: DASH,
        facts: [...common, ...genericFacts(d)],
      };
  }
}
