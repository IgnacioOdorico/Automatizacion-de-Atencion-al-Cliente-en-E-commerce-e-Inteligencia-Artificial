import { describe, expect, it } from 'vitest';

import {
  FEED_CAP,
  applyInitial,
  applyNewer,
  applyOlder,
  feedItems,
  initialFeed,
  isScrolledAway,
  newestFeedTs,
  olderCursor,
  pendingCount,
  resumeFeed,
  sinceCursor,
} from '@/lib/eventFeed';
import type { MonitoringEvent } from '@/types/monitoring';

import { makeEvent, makePage } from './helpers/monitoringFixtures';

/** Eventos de chat numerados; `ts` crece con el pk para que se lean en orden real. */
function ev(pk: number, ts?: string): MonitoringEvent {
  const seconds = String(pk % 60).padStart(2, '0');
  const minutes = String(Math.floor(pk / 60) % 60).padStart(2, '0');
  return makeEvent('chat_message', pk, { message: `m${pk}` }, { ts: ts ?? `2026-09-21T14:${minutes}:${seconds}.000Z` });
}

/** Página de eventos con pks de `from` a `to` (inclusive), del más nuevo al más viejo. */
function pageOf(from: number, to: number, extra: Parameters<typeof makePage>[1] = {}) {
  const items: MonitoringEvent[] = [];
  for (let pk = to; pk >= from; pk -= 1) items.push(ev(pk));
  return makePage(items, extra);
}

const ids = (items: readonly MonitoringEvent[]) => items.map((e) => e.id);

describe('applyInitial (primera carga o cambio de filtro)', () => {
  it('parte de un feed vacío que todavía no cargó', () => {
    const state = initialFeed();
    expect(feedItems(state)).toEqual([]);
    expect(state.loaded).toBe(false);
    expect(sinceCursor(state)).toBeNull();
    expect(pendingCount(state)).toBe(0);
  });

  it('guarda los eventos, el cursor de polling y si hay historia más vieja', () => {
    const page = pageOf(1, 5, { has_more: true });
    const state = applyInitial(initialFeed(), page);
    expect(ids(feedItems(state))).toEqual(['chat_message:5', 'chat_message:4', 'chat_message:3', 'chat_message:2', 'chat_message:1']);
    expect(sinceCursor(state)).toBe(page.newest_cursor);
    expect(olderCursor(state)).toBe(page.oldest_cursor);
    expect(state.hasMore).toBe(true);
    expect(state.loaded).toBe(true);
  });

  it('una página vacía igual marca el feed como cargado y sin cursor', () => {
    const state = applyInitial(initialFeed(), makePage([]));
    expect(state.loaded).toBe(true);
    expect(feedItems(state)).toEqual([]);
    expect(sinceCursor(state)).toBeNull();
    expect(olderCursor(state)).toBeNull();
    expect(state.hasMore).toBe(false);
  });

  it('reemplaza todo lo anterior (nuevo filtro = feed nuevo)', () => {
    const first = applyInitial(initialFeed(), pageOf(1, 3));
    const again = applyInitial(first, pageOf(10, 11));
    expect(ids(feedItems(again))).toEqual(['chat_message:11', 'chat_message:10']);
    expect(pendingCount(again)).toBe(0);
  });
});

describe('applyNewer (polling con `since`)', () => {
  const base = applyInitial(initialFeed(), pageOf(1, 5, { has_more: true }));

  it('los eventos nuevos van arriba y el cursor avanza', () => {
    const incoming = pageOf(6, 7);
    const next = applyNewer(base, incoming, false);
    expect(ids(feedItems(next)).slice(0, 3)).toEqual(['chat_message:7', 'chat_message:6', 'chat_message:5']);
    expect(sinceCursor(next)).toBe(incoming.newest_cursor);
  });

  it('el historial más viejo sigue apuntando al mismo cursor (no se pierde el "Cargar más")', () => {
    const next = applyNewer(base, pageOf(6, 7), false);
    expect(olderCursor(next)).toBe(olderCursor(base));
    expect(next.hasMore).toBe(true);
  });

  it('sin novedades: la lista no cambia y conserva el cursor recibido', () => {
    const idle = makePage([], { newest_cursor: sinceCursor(base) });
    const next = applyNewer(base, idle, false);
    expect(feedItems(next)).toEqual(feedItems(base));
    expect(sinceCursor(next)).toBe(sinceCursor(base));
  });

  it('una página vacía sin cursor no pisa el cursor que ya se tenía', () => {
    const next = applyNewer(base, makePage([]), false);
    expect(sinceCursor(next)).toBe(sinceCursor(base));
  });

  it('descarta duplicados por id (dos polls que se pisan)', () => {
    const next = applyNewer(base, pageOf(5, 7), false);
    expect(ids(feedItems(next))).toEqual([
      'chat_message:7',
      'chat_message:6',
      'chat_message:5',
      'chat_message:4',
      'chat_message:3',
      'chat_message:2',
      'chat_message:1',
    ]);
  });

  it('un feed vacío que recibe su primera página toma de ahí si hay más historia', () => {
    const empty = applyInitial(initialFeed(), makePage([]));
    const next = applyNewer(empty, pageOf(1, 3, { has_more: true }), false);
    expect(ids(feedItems(next))).toEqual(['chat_message:3', 'chat_message:2', 'chat_message:1']);
    expect(next.hasMore).toBe(true);
    expect(olderCursor(next)).toBe(`o:chat_message:1`);
  });

  it('no muta el estado anterior', () => {
    const before = JSON.stringify(base);
    applyNewer(base, pageOf(6, 7), false);
    expect(JSON.stringify(base)).toBe(before);
  });
});

describe('pausa: los eventos nuevos esperan sin mover la lista', () => {
  const base = applyInitial(initialFeed(), pageOf(1, 5));

  it('en pausa la lista visible no cambia, pero se cuenta lo que llegó', () => {
    const paused = applyNewer(base, pageOf(6, 8), true);
    expect(feedItems(paused)).toEqual(feedItems(base));
    expect(pendingCount(paused)).toBe(3);
    expect(sinceCursor(paused)).toBe(pageOf(6, 8).newest_cursor);
  });

  it('varios polls en pausa se acumulan sin duplicar', () => {
    const one = applyNewer(base, pageOf(6, 7), true);
    const two = applyNewer(one, pageOf(7, 9), true);
    expect(pendingCount(two)).toBe(4);
  });

  it('al reanudar, lo pendiente entra arriba en orden y el contador vuelve a cero', () => {
    const one = applyNewer(base, pageOf(6, 7), true);
    const two = applyNewer(one, pageOf(8, 9), true);
    const resumed = resumeFeed(two);
    expect(ids(feedItems(resumed)).slice(0, 5)).toEqual([
      'chat_message:9',
      'chat_message:8',
      'chat_message:7',
      'chat_message:6',
      'chat_message:5',
    ]);
    expect(pendingCount(resumed)).toBe(0);
    expect(sinceCursor(resumed)).toBe(sinceCursor(two));
  });

  it('un evento ya visible no se cuenta como pendiente', () => {
    const paused = applyNewer(base, pageOf(5, 5), true);
    expect(pendingCount(paused)).toBe(0);
  });

  it('reanudar sin pendientes no cambia nada', () => {
    expect(resumeFeed(base)).toEqual(base);
  });
});

describe('tope en memoria (~300) sin romper la paginación hacia atrás', () => {
  function bigFeed(): ReturnType<typeof initialFeed> {
    let state = applyInitial(initialFeed(), pageOf(1, 100, { has_more: false }));
    for (let start = 101; start <= 401; start += 100) {
      state = applyNewer(state, pageOf(start, start + 99), false);
    }
    return state;
  }

  it('el tope es de 300 eventos', () => {
    expect(FEED_CAP).toBe(300);
  });

  it('descarta páginas enteras del final y avisa que hay más historia', () => {
    const state = bigFeed();
    const items = feedItems(state);
    expect(items.length).toBeGreaterThanOrEqual(FEED_CAP);
    expect(items.length).toBeLessThanOrEqual(FEED_CAP + 99);
    expect(items[0].id).toBe('chat_message:500');
    expect(state.hasMore).toBe(true);
  });

  it('el cursor de "Cargar más" corresponde al último evento que quedó (no hay saltos)', () => {
    const state = bigFeed();
    const items = feedItems(state);
    const last = items[items.length - 1];
    // makePage deriva el cursor del id del último ítem de la página: sigue siendo continuo.
    expect(olderCursor(state)).toBe(`o:${last.id}`);
  });

  it('las páginas que el usuario pidió con "Cargar más" no se le esfuman debajo de los ojos', () => {
    let state = applyInitial(initialFeed(), pageOf(201, 300, { has_more: true }));
    state = applyOlder(state, pageOf(101, 200, { has_more: true }));
    state = applyOlder(state, pageOf(1, 100, { has_more: false }));
    for (let start = 301; start <= 601; start += 100) {
      state = applyNewer(state, pageOf(start, start + 99), false);
    }
    expect(feedItems(state).some((e) => e.id === 'chat_message:1')).toBe(true);
  });
});

describe('applyOlder ("Cargar más" hacia atrás con `before`)', () => {
  const base = applyInitial(initialFeed(), pageOf(6, 10, { has_more: true }));

  it('agrega abajo, mueve el cursor y respeta has_more', () => {
    const older = pageOf(1, 5, { has_more: false });
    const next = applyOlder(base, older);
    expect(ids(feedItems(next)).slice(-2)).toEqual(['chat_message:2', 'chat_message:1']);
    expect(feedItems(next)).toHaveLength(10);
    expect(olderCursor(next)).toBe(older.oldest_cursor);
    expect(next.hasMore).toBe(false);
    expect(sinceCursor(next)).toBe(sinceCursor(base));
  });

  it('descarta duplicados', () => {
    // Los eventos 6 y 7 ya estaban: de la página 4..7 solo entran el 5 y el 4.
    const next = applyOlder(base, pageOf(4, 7, { has_more: true }));
    expect(ids(feedItems(next))).toEqual([
      'chat_message:10',
      'chat_message:9',
      'chat_message:8',
      'chat_message:7',
      'chat_message:6',
      'chat_message:5',
      'chat_message:4',
    ]);
  });

  it('una página vacía sin más historia cierra el "Cargar más"', () => {
    const next = applyOlder(base, makePage([], { has_more: false }));
    expect(next.hasMore).toBe(false);
    expect(olderCursor(next)).toBe(olderCursor(base));
  });
});

describe('newestFeedTs (para el indicador "Bot activo")', () => {
  it('toma el evento más nuevo, incluso si está pendiente por la pausa', () => {
    const base = applyInitial(initialFeed(), pageOf(1, 5));
    const paused = applyNewer(base, pageOf(6, 7), true);
    expect(newestFeedTs(base)).toBe(ev(5).ts);
    expect(newestFeedTs(paused)).toBe(ev(7).ts);
  });

  it('feed vacío: null', () => {
    expect(newestFeedTs(initialFeed())).toBeNull();
  });
});

describe('isScrolledAway (con la lista lejos del borde superior, lo nuevo espera para no mover lo que estás leyendo)', () => {
  it('con la lista a la vista, no está lejos', () => {
    expect(isScrolledAway(120)).toBe(false);
    expect(isScrolledAway(0)).toBe(false);
    expect(isScrolledAway(-100)).toBe(false);
  });

  it('con el inicio de la lista más de 200 px arriba de la pantalla, sí', () => {
    expect(isScrolledAway(-201)).toBe(true);
    expect(isScrolledAway(-1200)).toBe(true);
  });

  it('el umbral es configurable', () => {
    expect(isScrolledAway(-50, 40)).toBe(true);
  });
});

