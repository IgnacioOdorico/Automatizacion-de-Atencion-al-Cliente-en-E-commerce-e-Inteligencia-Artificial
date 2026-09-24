import { latestIso } from '@/lib/monitoringSummary';
import type { EventsPage, MonitoringEvent } from '@/types/monitoring';

/**
 * Estado del feed en vivo: la lista que se ve, lo que llegó mientras estaba en
 * pausa, los cursores para seguir pidiendo (`since` hacia adelante, `before`
 * hacia atrás) y el tope en memoria. Todo son funciones puras: cada una recibe
 * el estado y devuelve otro, sin mutar el anterior.
 *
 * La lista se guarda en "trozos" (una página de la API cada uno) porque los
 * cursores son opacos y solo la API sabe armarlos: cada trozo recuerda el
 * cursor de su evento más viejo. Así, al descartar trozos del final por el
 * tope, el "Cargar más" sigue partiendo justo del último evento que quedó.
 */

/** Tope aproximado de eventos en memoria (se descartan trozos enteros del final). */
export const FEED_CAP = 300;

interface FeedChunk {
  /** Del más nuevo al más viejo. */
  items: MonitoringEvent[];
  /** Cursor `before` de su evento más viejo. */
  oldestCursor: string | null;
  /** Lo pidió el usuario con "Cargar más": no se descarta por el tope. */
  manual?: boolean;
}

export interface FeedState {
  chunks: FeedChunk[];
  /** Llegado durante la pausa, todavía sin mostrar (el más nuevo primero). */
  pending: FeedChunk[];
  /** Cursor para el próximo `since`. */
  newestCursor: string | null;
  /** Hay eventos más viejos que los que se tienen. */
  hasMore: boolean;
  /** Ya llegó la primera respuesta del servidor. */
  loaded: boolean;
}

export function initialFeed(): FeedState {
  return { chunks: [], pending: [], newestCursor: null, hasMore: false, loaded: false };
}

const flat = (chunks: readonly FeedChunk[]): MonitoringEvent[] => chunks.flatMap((c) => c.items);
const size = (chunks: readonly FeedChunk[]): number => chunks.reduce((n, c) => n + c.items.length, 0);

export function feedItems(state: FeedState): MonitoringEvent[] {
  return flat(state.chunks);
}

export function pendingCount(state: FeedState): number {
  return size(state.pending);
}

export function sinceCursor(state: FeedState): string | null {
  return state.newestCursor;
}

export function olderCursor(state: FeedState): string | null {
  const tail = state.chunks[state.chunks.length - 1];
  return tail ? tail.oldestCursor : null;
}

/** El evento más reciente que se conoce, contando lo que espera por la pausa. */
export function newestFeedTs(state: FeedState): string | null {
  return latestIso(state.chunks[0]?.items[0]?.ts, state.pending[0]?.items[0]?.ts);
}

function knownIds(state: FeedState): Set<string> {
  return new Set([...flat(state.chunks), ...flat(state.pending)].map((e) => e.id));
}

function freshItems(items: readonly MonitoringEvent[], seen: Set<string>): MonitoringEvent[] {
  const out: MonitoringEvent[] = [];
  for (const item of items) {
    if (seen.has(item.id)) continue;
    seen.add(item.id);
    out.push(item);
  }
  return out;
}

/**
 * Aplica el tope: mientras el trozo más viejo quede totalmente fuera de las
 * primeras `cap` posiciones, se descarta (y se avisa que hay más historia).
 * Nunca toca lo que el usuario cargó a mano.
 */
function trim(chunks: FeedChunk[], hasMore: boolean, cap: number): { chunks: FeedChunk[]; hasMore: boolean } {
  let kept = chunks;
  let more = hasMore;
  while (kept.length > 1) {
    const tail = kept[kept.length - 1];
    if (tail.manual || size(kept) - tail.items.length < cap) break;
    kept = kept.slice(0, -1);
    more = true;
  }
  return { chunks: kept, hasMore: more };
}

/** Primera página (o cambio de filtro): reemplaza todo lo anterior. */
export function applyInitial(_state: FeedState, page: EventsPage): FeedState {
  return {
    chunks: page.items.length > 0 ? [{ items: [...page.items], oldestCursor: page.oldest_cursor }] : [],
    pending: [],
    newestCursor: page.newest_cursor,
    hasMore: page.has_more,
    loaded: true,
  };
}

/**
 * Respuesta de un poll (`since`, o el pedido sin cursor si el feed estaba
 * vacío). En pausa los eventos esperan aparte y la lista visible no se mueve.
 */
export function applyNewer(state: FeedState, page: EventsPage, paused: boolean, cap = FEED_CAP): FeedState {
  const newestCursor = page.newest_cursor ?? state.newestCursor;
  const incoming = freshItems(page.items, knownIds(state));
  if (incoming.length === 0) return { ...state, newestCursor, loaded: true };

  const chunk: FeedChunk = { items: incoming, oldestCursor: page.oldest_cursor };
  if (paused) return { ...state, pending: [chunk, ...state.pending], newestCursor, loaded: true };

  const wasEmpty = state.chunks.length === 0 && state.pending.length === 0;
  const trimmed = trim([chunk, ...state.chunks], wasEmpty ? page.has_more : state.hasMore, cap);
  return { ...state, ...trimmed, newestCursor, loaded: true };
}

/** "Reanudar": lo pendiente entra arriba, en orden. */
export function resumeFeed(state: FeedState, cap = FEED_CAP): FeedState {
  if (state.pending.length === 0) return state;
  const wasEmpty = state.chunks.length === 0;
  const trimmed = trim([...state.pending, ...state.chunks], wasEmpty ? false : state.hasMore, cap);
  return { ...state, ...trimmed, pending: [] };
}

/** "Cargar más": historia hacia atrás con `before`. Se agrega abajo y no cuenta para el tope. */
export function applyOlder(state: FeedState, page: EventsPage): FeedState {
  const items = freshItems(page.items, knownIds(state));
  const chunks =
    items.length > 0
      ? [...state.chunks, { items, oldestCursor: page.oldest_cursor ?? olderCursor(state), manual: true }]
      : state.chunks;
  return { ...state, chunks, hasMore: page.has_more };
}

/** Distancia (px) a la que el inicio de la lista se considera fuera de la vista. */
export const SCROLL_HOLD_PX = 200;

/**
 * `listTop` es la posición del inicio de la lista respecto de la pantalla
 * (getBoundingClientRect().top). Si ya se desplazó bien arriba de la vista, el
 * usuario está leyendo más abajo: lo nuevo espera en el contador en vez de
 * empujar el contenido y hacer saltar el scroll.
 */
export function isScrolledAway(listTop: number, threshold = SCROLL_HOLD_PX): boolean {
  return listTop < -threshold;
}

