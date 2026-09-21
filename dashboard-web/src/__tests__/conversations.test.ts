import { describe, expect, it } from 'vitest';

import {
  applyThreadLatest,
  applyThreadOlder,
  conversationSearch,
  initialThread,
  mergeConversationPages,
  parseConversationSearch,
  replyChips,
  sameConversation,
  threadDays,
} from '@/lib/conversations';

import { makeConversation, makeThreadItem } from './helpers/monitoringFixtures';

describe('conversationSearch / parseConversationSearch (el hilo abierto vive en la URL)', () => {
  it('arma ?canal=&usuario= y lo codifica', () => {
    expect(conversationSearch('telegram', '12345')).toBe('?canal=telegram&usuario=12345');
  });

  it('un "+" o un espacio en el usuario no se pierden en el viaje de ida y vuelta', () => {
    for (const userId of ['+5492610000000', 'ana perez@example.com', 'a/b?c=d&e', '  ']) {
      const search = conversationSearch('whatsapp', userId);
      expect(search).not.toContain('+549');
      expect(parseConversationSearch(search)).toEqual({ channel: 'whatsapp', userId });
    }
  });

  it('acepta la búsqueda con o sin "?" inicial', () => {
    expect(parseConversationSearch('canal=email&usuario=a%40b.com')).toEqual({
      channel: 'email',
      userId: 'a@b.com',
    });
  });

  it('un canal fuera del dominio, un usuario vacío o demasiado largo no abren nada', () => {
    expect(parseConversationSearch('?canal=sms&usuario=1')).toBeNull();
    expect(parseConversationSearch('?canal=telegram')).toBeNull();
    expect(parseConversationSearch('?canal=telegram&usuario=')).toBeNull();
    expect(parseConversationSearch(`?canal=telegram&usuario=${'x'.repeat(201)}`)).toBeNull();
    expect(parseConversationSearch('')).toBeNull();
  });
});

describe('sameConversation', () => {
  it('compara canal y usuario', () => {
    const a = { channel: 'whatsapp' as const, userId: '1' };
    expect(sameConversation(a, { channel: 'whatsapp', userId: '1' })).toBe(true);
    expect(sameConversation(a, { channel: 'telegram', userId: '1' })).toBe(false);
    expect(sameConversation(a, { channel: 'whatsapp', userId: '2' })).toBe(false);
    expect(sameConversation(a, null)).toBe(false);
  });
});

describe('mergeConversationPages (lista de hilos con "Cargar más")', () => {
  const a = makeConversation({ user_id: 'a', last_at: '2026-09-21T14:03:00.000Z' });
  const b = makeConversation({ user_id: 'b', last_at: '2026-09-21T14:02:00.000Z' });
  const c = makeConversation({ user_id: 'c', last_at: '2026-09-21T14:01:00.000Z' });

  it('la primera página manda; lo cargado después va abajo', () => {
    expect(mergeConversationPages([a, b], [c]).map((x) => x.user_id)).toEqual(['a', 'b', 'c']);
  });

  it('un hilo que se movió a la primera página no aparece dos veces (gana la versión fresca)', () => {
    const fresh = { ...c, messages: 9, last_at: '2026-09-21T14:04:00.000Z' };
    const merged = mergeConversationPages([fresh, a], [b, c]);
    expect(merged.map((x) => x.user_id)).toEqual(['c', 'a', 'b']);
    expect(merged[0].messages).toBe(9);
  });

  it('el mismo usuario en otro canal es otro hilo', () => {
    const other = makeConversation({ user_id: 'a', channel: 'telegram' });
    expect(mergeConversationPages([a], [other])).toHaveLength(2);
  });
});

describe('estado del hilo: ventana reciente + historia cargada a pedido', () => {
  it('la primera carga guarda mensajes, cursor de historia y si hay más', () => {
    const page = { channel: 'whatsapp' as const, user_id: 'u', items: [makeThreadItem(3), makeThreadItem(4)], has_more: true, next_before: 'cur-a' };
    const state = applyThreadLatest(initialThread(), page);
    expect(state.items.map((i) => i.interaction_id)).toEqual([3, 4]);
    expect(state.olderCursor).toBe('cur-a');
    expect(state.hasOlder).toBe(true);
    expect(state.loaded).toBe(true);
  });

  it('el polling suma mensajes nuevos y actualiza los que cambiaron (el bot respondió)', () => {
    const first = applyThreadLatest(initialThread(), {
      channel: 'whatsapp', user_id: 'u',
      items: [makeThreadItem(3), makeThreadItem(4, { responded_at: null, ai_response: null, tmr_seconds: null })],
      has_more: false, next_before: null,
    });
    const next = applyThreadLatest(first, {
      channel: 'whatsapp', user_id: 'u',
      items: [makeThreadItem(3), makeThreadItem(4), makeThreadItem(5)],
      has_more: false, next_before: null,
    });
    expect(next.items.map((i) => i.interaction_id)).toEqual([3, 4, 5]);
    expect(next.items[1].ai_response).toBe('Respuesta 4');
  });

  it('el polling NO pisa el cursor de historia ya establecido', () => {
    const first = applyThreadLatest(initialThread(), {
      channel: 'whatsapp', user_id: 'u', items: [makeThreadItem(50)], has_more: true, next_before: 'cur-1',
    });
    const next = applyThreadLatest(first, {
      channel: 'whatsapp', user_id: 'u', items: [makeThreadItem(50), makeThreadItem(51)], has_more: true, next_before: 'cur-2',
    });
    expect(next.olderCursor).toBe('cur-1');
  });

  it('los mensajes que salen de la ventana reciente no se pierden si ya estaban cargados', () => {
    const first = applyThreadLatest(initialThread(), {
      channel: 'whatsapp', user_id: 'u', items: [makeThreadItem(10), makeThreadItem(11)], has_more: false, next_before: null,
    });
    // La ventana del server ahora arranca en el 11: el 10 sigue en pantalla.
    const next = applyThreadLatest(first, {
      channel: 'whatsapp', user_id: 'u', items: [makeThreadItem(11), makeThreadItem(12)], has_more: false, next_before: null,
    });
    expect(next.items.map((i) => i.interaction_id)).toEqual([10, 11, 12]);
  });

  it('"Cargar anteriores" agrega arriba, en orden cronológico, y mueve el cursor', () => {
    const first = applyThreadLatest(initialThread(), {
      channel: 'whatsapp', user_id: 'u', items: [makeThreadItem(10), makeThreadItem(11)], has_more: true, next_before: 'cur-1',
    });
    const older = applyThreadOlder(first, {
      channel: 'whatsapp', user_id: 'u', items: [makeThreadItem(8), makeThreadItem(9)], has_more: false, next_before: null,
    });
    expect(older.items.map((i) => i.interaction_id)).toEqual([8, 9, 10, 11]);
    expect(older.hasOlder).toBe(false);
    expect(older.olderCursor).toBeNull();
  });

  it('un hilo se ordena por hora de llegada, aunque los ids no vengan ordenados', () => {
    const early = makeThreadItem(99, { received_at: '2026-09-21T10:00:00.000Z' });
    const late = makeThreadItem(1, { received_at: '2026-09-21T12:00:00.000Z' });
    const state = applyThreadLatest(initialThread(), {
      channel: 'whatsapp', user_id: 'u', items: [late, early], has_more: false, next_before: null,
    });
    expect(state.items.map((i) => i.interaction_id)).toEqual([99, 1]);
  });
});

describe('threadDays (separadores por día, hora de Mendoza)', () => {
  // 21/09/2026 11:00 en Mendoza (14:00Z)
  const NOW = Date.parse('2026-09-21T14:00:00.000Z');

  it('agrupa por día y rotula Hoy / Ayer / fecha', () => {
    const items = [
      makeThreadItem(1, { received_at: '2026-09-19T15:00:00.000Z' }),
      makeThreadItem(2, { received_at: '2026-09-20T15:00:00.000Z' }),
      makeThreadItem(3, { received_at: '2026-09-21T12:00:00.000Z' }),
      makeThreadItem(4, { received_at: '2026-09-21T13:00:00.000Z' }),
    ];
    const days = threadDays(items, NOW);
    expect(days.map((d) => d.label)).toEqual(['19/09/2026', 'Ayer', 'Hoy']);
    expect(days[2].items.map((i) => i.interaction_id)).toEqual([3, 4]);
  });

  it('el día se corta en la medianoche de Mendoza, no en la de UTC', () => {
    // 22/09 01:30Z = 21/09 22:30 en Mendoza: sigue siendo "Hoy" para el negocio.
    const items = [makeThreadItem(1, { received_at: '2026-09-22T01:30:00.000Z' })];
    expect(threadDays(items, NOW)[0].label).toBe('Hoy');
  });

  it('sin mensajes no hay días', () => {
    expect(threadDays([], NOW)).toEqual([]);
  });
});

describe('replyChips (intent, urgencia y TMR de la respuesta del bot)', () => {
  it('muestra las tres marcas con texto', () => {
    const chips = replyChips(makeThreadItem(1, { intent: 'RECLAMO', is_urgent: true, tmr_seconds: 3.918 }));
    expect(chips).toEqual([
      { text: 'Reclamo', tone: 'warning' },
      { text: 'Urgente', tone: 'danger' },
      { text: 'TMR 3,9 s', tone: 'neutral' },
    ]);
  });

  it('sin respuesta todavía: sin chips inventados', () => {
    expect(
      replyChips(makeThreadItem(1, { intent: null, is_urgent: false, tmr_seconds: null, responded_at: null, ai_response: null })),
    ).toEqual([]);
  });
});
