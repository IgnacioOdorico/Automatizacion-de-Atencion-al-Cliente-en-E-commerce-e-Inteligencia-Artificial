import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { dashboardApi, monitoringApi } from '@/api/endpoints';
import { MonitoreoEnVivoPage } from '@/pages/MonitoreoEnVivoPage';
import type { EventsPage, EventsParams, MonitoringSummary } from '@/types/monitoring';

import { makeEvent, makePage } from './helpers/monitoringFixtures';

vi.mock('@/api/endpoints', () => ({
  monitoringApi: { summary: vi.fn(), events: vi.fn(), conversations: vi.fn(), thread: vi.fn() },
  dashboardApi: { order: vi.fn() },
}));

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const events = vi.mocked(monitoringApi.events);
const summary = vi.mocked(monitoringApi.summary);
const order = vi.mocked(dashboardApi.order);

// ---------- fixtures ----------

const MESSAGE = '¿Dónde está mi <b>pedido</b> ORD-2026-0007?\nGracias';
const REPLY = 'Tu pedido está confirmado y en preparación.';

const orderReceived = makeEvent(
  'order_received',
  7,
  {
    order_number: 'ORD-2026-0007',
    customer_name: 'Ana Pérez',
    customer_email: 'ana@example.com',
    quantity: 2,
    total_amount: 349.99,
    product_sku: 'PROD-001',
    product_name: 'Notebook 14"',
  },
  {
    ts: '2026-09-21T14:03:20.000Z',
    severity: 'info',
    refs: { order_id: 7, order_number: 'ORD-2026-0007' },
  },
);
const chat = makeEvent(
  'chat_message',
  41,
  { user_id: '+5492610000000', message: MESSAGE },
  { ts: '2026-09-21T14:04:50.000Z', channel: 'whatsapp', refs: { interaction_id: 41 } },
);
const reply = makeEvent(
  'bot_reply',
  41,
  {
    user_id: '+5492610000000',
    ai_response: REPLY,
    intent: 'ESTADO_PEDIDO',
    is_urgent: false,
    tmr_seconds: 3.918,
  },
  { ts: '2026-09-21T14:04:54.000Z', channel: 'whatsapp', severity: 'success', refs: { interaction_id: 41 } },
);
const fresh = makeEvent(
  'ticket_created',
  3,
  { user_id: '123456', subject: 'Reclamo por demora', priority: 'high', status: 'open' },
  { ts: '2026-09-21T14:05:01.000Z', channel: 'telegram', severity: 'warning', refs: { ticket_id: 3 } },
);
const older1 = makeEvent('stock_alert', 1, { sku: 'PROD-002', product_name: 'Mouse', stock_actual: 2, stock_min: 5 }, {
  ts: '2026-09-21T13:00:00.000Z',
  severity: 'warning',
});

const firstPage: EventsPage = makePage([reply, chat, orderReceived], { has_more: true });
const olderPage: EventsPage = makePage([older1], { has_more: false });

const SUMMARY: MonitoringSummary = {
  window_hours: 24,
  generated_at: '2026-09-21T14:05:00.000Z',
  data_source: 'all',
  last_activity_at: '2026-09-21T14:04:54.000Z',
  bot: {
    interactions: 12,
    avg_tmr_seconds: 3.42,
    urgent: 1,
    by_intent: { FAQ: 5, ESTADO_PEDIDO: 4, RECLAMO: 2, GENERAL: 1 },
    by_channel: { whatsapp: 7, telegram: 5, email: 0 },
  },
  orders: { total: 9, by_status: {} },
  tickets: { created: 2, open: 3, by_priority: {} },
  stock_alerts: 1,
  executions: { available: true, total: 21, success: 19, error: 2, last_error_at: null },
};

// ---------- entorno ----------

let container: HTMLDivElement;
let root: Root;
let nextPage: EventsPage | null;
let visibility: 'visible' | 'hidden';

function setVisibility(state: 'visible' | 'hidden') {
  visibility = state;
  document.dispatchEvent(new Event('visibilitychange'));
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date'] });
  vi.setSystemTime(new Date('2026-09-21T14:05:00.000Z'));
  nextPage = null;
  visibility = 'visible';
  Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => visibility });

  summary.mockReset().mockResolvedValue(SUMMARY);
  order.mockReset();
  events.mockReset().mockImplementation(async (params: EventsParams = {}) => {
    if (params.before) return olderPage;
    if (params.since) return nextPage ?? makePage([], { newest_cursor: params.since });
    return firstPage;
  });

  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.useRealTimers();
  vi.restoreAllMocks();
});

async function advance(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

async function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } });
  await act(async () => {
    root.render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={['/monitoreo/en-vivo']}>
          <Routes>
            <Route path="/monitoreo/en-vivo" element={<MonitoreoEnVivoPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  });
  await advance(0);
}

const cards = () => Array.from(container.querySelectorAll<HTMLElement>('.mon-event'));
const buttonByText = (text: string) =>
  Array.from(document.querySelectorAll<HTMLButtonElement>('button')).find((b) => b.textContent?.trim() === text);
const click = (el: Element | undefined | null) => {
  if (!el) throw new Error('elemento no encontrado');
  act(() => (el as HTMLElement).click());
};
const chip = (label: string) =>
  Array.from(container.querySelectorAll<HTMLButtonElement>('.mon-chips button')).find((b) =>
    b.textContent?.includes(label),
  );

// ---------- tests ----------

describe('En vivo: feed', () => {
  it('muestra los eventos del más nuevo al más viejo, con etiquetas en español', async () => {
    await mount();
    expect(cards()).toHaveLength(3);
    const types = cards().map((c) => c.querySelector('.mon-event__type')?.textContent);
    expect(types).toEqual(['Respuesta del bot', 'Mensaje del cliente', 'Pedido recibido']);
  });

  it('los textos del cliente y del bot se dibujan exactos y como texto (nunca como HTML)', async () => {
    await mount();
    const quotes = Array.from(container.querySelectorAll('.mon-quote'));
    expect(quotes.map((q) => q.textContent)).toEqual([REPLY, MESSAGE]);
    expect(container.querySelector('.mon-quote b')).toBeNull();
  });

  it('cada tarjeta trae severidad con texto, canal, intent y TMR', async () => {
    await mount();
    const botCard = cards()[0];
    expect(botCard.className).toContain('mon-event--success');
    expect(botCard.textContent).toContain('Correcto');
    expect(botCard.textContent).toContain('WhatsApp');
    expect(botCard.textContent).toContain('Estado de pedido');
    expect(botCard.textContent).toContain('TMR 3,9 s');
  });

  it('la hora es relativa y absoluta (hora de Mendoza)', async () => {
    await mount();
    const time = cards()[0].querySelector('time');
    expect(time?.textContent).toContain('hace 6 s');
    expect(time?.textContent).toContain('11:04:54');
    expect(time?.getAttribute('datetime')).toBe('2026-09-21T14:04:54.000Z');
    expect(time?.getAttribute('title')).toBe('21/09/2026 11:04:54');
  });

  it('la hora relativa avanza sola cada segundo', async () => {
    await mount();
    await advance(4000);
    expect(cards()[0].querySelector('time')?.textContent).toContain('hace 10 s');
  });

  it('polling cada 3 s con `since` incremental: lo nuevo aparece arriba y resaltado un momento', async () => {
    await mount();
    expect(events).toHaveBeenCalledTimes(1);
    expect(events.mock.calls[0][0]).not.toHaveProperty('since');

    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await advance(3000);

    expect(events).toHaveBeenCalledTimes(2);
    expect(events.mock.calls[1][0]).toMatchObject({ since: firstPage.newest_cursor });
    expect(cards()).toHaveLength(4);
    expect(cards()[0].querySelector('.mon-event__type')?.textContent).toBe('Ticket creado');
    expect(cards()[0].className).toContain('mon-event--fresh');
    expect(cards()[1].className).not.toContain('mon-event--fresh');

    await advance(3500);
    expect(cards()[0].className).not.toContain('mon-event--fresh');
  });

  it('el siguiente poll usa el cursor nuevo y no repite eventos', async () => {
    await mount();
    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await advance(3000);
    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await advance(3000);
    expect(events.mock.calls[2][0]).toMatchObject({ since: 'cur-2' });
    expect(cards()).toHaveLength(4);
  });

  it('si el server dice que hay más para ponerse al día, pide de nuevo enseguida', async () => {
    await mount();
    const e1 = makeEvent('ticket_created', 10, { subject: 'a' }, { ts: '2026-09-21T14:05:01.000Z' });
    const e2 = makeEvent('ticket_created', 11, { subject: 'b' }, { ts: '2026-09-21T14:05:02.000Z' });
    const pages = [
      makePage([e1], { has_more: true, newest_cursor: 'c1' }),
      makePage([e2], { has_more: false, newest_cursor: 'c2' }),
    ];
    events.mockImplementation(async (params: EventsParams = {}) => (params.since ? (pages.shift() ?? makePage([], { newest_cursor: params.since })) : firstPage));
    await advance(3000);
    expect(cards().slice(0, 2).map((c) => c.querySelector('.mon-event__headline')?.textContent)).toEqual(['b', 'a']);
  });

  it('con la pestaña del navegador oculta no consulta; al volver, consulta enseguida', async () => {
    await mount();
    setVisibility('hidden');
    await advance(9000);
    expect(events).toHaveBeenCalledTimes(1);

    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await act(async () => {
      setVisibility('visible');
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(events).toHaveBeenCalledTimes(2);
    expect(cards()).toHaveLength(4);
  });
});

describe('En vivo: pausa', () => {
  it('en pausa la lista no se mueve y un contador dice cuántos eventos nuevos hay', async () => {
    await mount();
    click(buttonByText('Pausar'));
    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await advance(3000);

    expect(cards()).toHaveLength(3);
    const pending = container.querySelector('.mon-pending');
    expect(pending?.textContent).toContain('1 evento nuevo');
    expect(buttonByText('Reanudar')).toBeTruthy();
    expect(buttonByText('Pausar')).toBeUndefined();
  });

  it('el contador es un aviso educado (polite) y no un panel ruidoso', async () => {
    await mount();
    click(buttonByText('Pausar'));
    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await advance(3000);
    const live = container.querySelector('.mon-pending [aria-live]');
    expect(live?.getAttribute('aria-live')).toBe('polite');
    expect(container.querySelectorAll('[aria-live="assertive"]')).toHaveLength(0);
  });

  it('al reanudar, lo acumulado entra arriba y el contador desaparece', async () => {
    await mount();
    click(buttonByText('Pausar'));
    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await advance(3000);
    click(buttonByText('Reanudar'));
    await advance(0);

    expect(cards()).toHaveLength(4);
    expect(cards()[0].querySelector('.mon-event__type')?.textContent).toBe('Ticket creado');
    expect(container.querySelector('.mon-pending')).toBeNull();
    expect(buttonByText('Pausar')).toBeTruthy();
  });

  it('"Ver ahora" vuelca lo pendiente sin salir de la pausa', async () => {
    await mount();
    click(buttonByText('Pausar'));
    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await advance(3000);
    click(buttonByText('Ver ahora'));
    await advance(0);
    expect(cards()).toHaveLength(4);
    expect(buttonByText('Reanudar')).toBeTruthy();
  });

  it('si el usuario está leyendo más abajo, lo nuevo espera solo y vuelve al subir', async () => {
    const rect = vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect');
    rect.mockReturnValue({ top: 0 } as DOMRect);
    await mount();

    rect.mockReturnValue({ top: -900 } as DOMRect);
    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await advance(3000);
    expect(cards()).toHaveLength(3);
    expect(container.querySelector('.mon-pending')?.textContent).toContain('1 evento nuevo');
    // No es una pausa manual: el botón sigue diciendo "Pausar".
    expect(buttonByText('Pausar')).toBeTruthy();

    rect.mockReturnValue({ top: 0 } as DOMRect);
    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    await advance(0);
    expect(cards()).toHaveLength(4);
    expect(container.querySelector('.mon-pending')).toBeNull();
  });
});

describe('En vivo: "Ver ahora" desde más abajo', () => {
  it('vuelca lo pendiente y lleva al principio de la lista una vez dibujado (no antes, para que no pelee con el scroll)', async () => {
    const scrollIntoView = vi.fn();
    HTMLElement.prototype.scrollIntoView = scrollIntoView;
    const rect = vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect');
    rect.mockReturnValue({ top: 0 } as DOMRect);
    await mount();

    rect.mockReturnValue({ top: -900 } as DOMRect);
    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await advance(3000);
    expect(scrollIntoView).not.toHaveBeenCalled();

    click(buttonByText('Ver ahora'));
    await advance(0);
    expect(cards()).toHaveLength(4);
    expect(scrollIntoView).toHaveBeenCalledTimes(1);
    // Se pidió sin animación: con "smooth" el navegador pelea con el reajuste del scroll.
    expect(scrollIntoView.mock.calls[0][0]).toMatchObject({ block: 'start' });
    expect((scrollIntoView.mock.calls[0][0] as ScrollIntoViewOptions).behavior).not.toBe('smooth');
    delete (HTMLElement.prototype as { scrollIntoView?: unknown }).scrollIntoView;
  });
});

describe('En vivo: filtros y más historia', () => {
  it('un chip de tipo vuelve a pedir el feed filtrado desde cero', async () => {
    await mount();
    click(chip('Respuesta del bot'));
    await advance(0);

    const call = events.mock.calls[events.mock.calls.length - 1][0] as EventsParams;
    expect(call.types).toEqual(['bot_reply']);
    expect(call).not.toHaveProperty('since');
    expect(chip('Respuesta del bot')?.getAttribute('aria-pressed')).toBe('true');
    expect(chip('Todos')?.getAttribute('aria-pressed')).toBe('false');
  });

  it('los chips se pueden combinar y "Todos" los limpia', async () => {
    await mount();
    click(chip('Respuesta del bot'));
    click(chip('Ticket creado'));
    await advance(0);
    const call = events.mock.calls[events.mock.calls.length - 1][0] as EventsParams;
    expect([...(call.types ?? [])].sort()).toEqual(['bot_reply', 'ticket_created']);

    click(chip('Todos'));
    await advance(0);
    const last = events.mock.calls[events.mock.calls.length - 1][0] as EventsParams;
    expect(last.types ?? []).toEqual([]);
  });

  it('el filtro de canal se manda a la API y avisa que pedidos y stock no tienen canal', async () => {
    await mount();
    const select = container.querySelector('select') as HTMLSelectElement;
    await act(async () => {
      const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set;
      setter?.call(select, 'telegram');
      select.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await advance(0);
    const call = events.mock.calls[events.mock.calls.length - 1][0] as EventsParams;
    expect(call.channel).toBe('telegram');
    expect(container.textContent).toContain('no tienen canal');
  });

  it('"Cargar eventos anteriores" pide con `before` y agrega abajo; al terminar el botón desaparece', async () => {
    await mount();
    click(buttonByText('Cargar eventos anteriores'));
    await advance(0);

    const call = events.mock.calls[events.mock.calls.length - 1][0] as EventsParams;
    expect(call.before).toBe(firstPage.oldest_cursor);
    expect(cards()).toHaveLength(4);
    expect(cards()[3].querySelector('.mon-event__type')?.textContent).toBe('Alerta de stock bajo');
    expect(buttonByText('Cargar eventos anteriores')).toBeUndefined();
  });
});

describe('En vivo: estados', () => {
  it('cargando: esqueleto sin datos inventados', async () => {
    events.mockImplementation(() => new Promise(() => {}));
    await mount();
    expect(container.querySelector('[aria-busy="true"]')).not.toBeNull();
    expect(cards().filter((c) => !c.className.includes('skeleton'))).toHaveLength(0);
  });

  it('vacío: explica qué va a aparecer y cuándo', async () => {
    events.mockResolvedValue(makePage([]));
    await mount();
    expect(container.textContent).toContain('El bot todavía no tiene actividad');
    expect(container.textContent).toContain('WhatsApp, Telegram o email');
  });

  it('vacío con filtros: lo dice y ofrece quitarlos', async () => {
    await mount();
    events.mockResolvedValue(makePage([]));
    click(chip('Ticket creado'));
    await advance(0);
    expect(container.textContent).toContain('Ningún evento coincide con los filtros');
    events.mockImplementation(async () => firstPage);
    click(buttonByText('Quitar filtros'));
    await advance(0);
    expect(cards()).toHaveLength(3);
  });

  it('error al cargar: mensaje claro y "Reintentar" que funciona', async () => {
    events.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    await mount();
    expect(container.querySelector('[role="alert"]')?.textContent).toContain('Sin conexión con el servidor');
    expect(cards()).toHaveLength(0);

    click(buttonByText('Reintentar'));
    await advance(0);
    expect(cards()).toHaveLength(3);
    expect(container.querySelector('[role="alert"]')).toBeNull();
  });

  it('un fallo al actualizar no borra lo que ya se veía: avisa en una franja', async () => {
    await mount();
    events.mockRejectedValue(new TypeError('Failed to fetch'));
    await advance(3000);
    expect(cards()).toHaveLength(3);
    expect(container.querySelector('.error-banner')?.textContent).toContain('Mostramos los últimos datos');
  });
});

describe('En vivo: franja superior', () => {
  it('KPIs de las últimas 24 h', async () => {
    await mount();
    const kpis = Object.fromEntries(
      Array.from(container.querySelectorAll('.mon-kpi')).map((k) => [
        k.querySelector('.mon-kpi__label')?.textContent,
        k.querySelector('.mon-kpi__value')?.textContent,
      ]),
    );
    expect(kpis).toEqual({
      'Interacciones del bot': '12',
      'TMR promedio': '3,4 s',
      Urgentes: '1',
      'Tickets abiertos': '3',
      Ejecuciones: '19 ok · 2 con error',
    });
  });

  it('"Bot activo" con el último evento real', async () => {
    await mount();
    const bot = container.querySelector('.mon-bot');
    expect(bot?.className).toContain('mon-bot--active');
    expect(bot?.textContent).toContain('Bot activo');
    expect(bot?.textContent).toContain('último evento hace 6 s');
  });

  it('mientras todavía no sabe nada, no afirma que el bot esté sin actividad', async () => {
    events.mockImplementation(() => new Promise(() => {}));
    summary.mockImplementation(() => new Promise(() => {}));
    await mount();
    const bot = container.querySelector('.mon-bot');
    expect(bot?.textContent).toContain('Consultando');
    expect(bot?.textContent).not.toContain('Todavía sin actividad');
    expect(bot?.textContent).not.toContain('Bot activo');
  });

  it('si no se puede consultar nada, lo dice en vez de quedarse en "Consultando"', async () => {
    events.mockRejectedValue(new TypeError('Failed to fetch'));
    summary.mockRejectedValue(new TypeError('Failed to fetch'));
    await mount();
    const bot = container.querySelector('.mon-bot');
    expect(bot?.textContent).toContain('No pudimos consultar la actividad del bot');
    expect(bot?.textContent).not.toContain('Consultando');
    expect(bot?.textContent).not.toContain('Bot activo');
  });

  it('con mucho tiempo sin eventos ya no dice "activo"', async () => {
    summary.mockResolvedValue({ ...SUMMARY, last_activity_at: '2026-09-21T12:00:00.000Z' });
    // El último evento del feed es de hace 35 minutos: ni "activo" ni "en reposo".
    const stale = makeEvent('stock_alert', 2, { sku: 'PROD-002', product_name: 'Mouse' }, { ts: '2026-09-21T13:30:00.000Z' });
    events.mockResolvedValue(makePage([stale]));
    await mount();
    const bot = container.querySelector('.mon-bot');
    expect(bot?.className).toContain('mon-bot--idle');
    expect(bot?.textContent).not.toContain('Bot activo');
    expect(bot?.textContent).toContain('Sin actividad reciente');
  });

  it('sin ejecuciones de n8n disponibles se degrada sin romper', async () => {
    summary.mockResolvedValue({
      ...SUMMARY,
      executions: { available: false, total: 0, success: 0, error: 0, last_error_at: null },
    });
    await mount();
    expect(container.textContent).toContain('No disponible por ahora');
    expect(cards()).toHaveLength(3);
  });

  it('si falla el resumen, el feed sigue funcionando y se puede reintentar', async () => {
    summary.mockRejectedValue(new TypeError('Failed to fetch'));
    await mount();
    expect(cards()).toHaveLength(3);
    const alert = container.querySelector('[role="alert"]');
    expect(alert?.textContent).toContain('Reintentar');
    // El indicador del bot igual sale del último evento del feed.
    expect(container.querySelector('.mon-bot')?.textContent).toContain('Bot activo');
  });
});

describe('En vivo: detalle de un evento', () => {
  it('abre un diálogo con todos los datos exactos y el texto completo', async () => {
    await mount();
    click(cards()[1].querySelector('.mon-event__headline'));
    const dialog = document.querySelector('[role="dialog"]') as HTMLElement;
    expect(dialog).not.toBeNull();
    expect(dialog.textContent).toContain('Mensaje del cliente');
    expect(dialog.textContent).toContain('21/09/2026 11:04:50');
    expect(dialog.querySelector('.mon-detail-quote')?.textContent).toBe(MESSAGE);
    expect(dialog.querySelector('.mon-detail-quote b')).toBeNull();
  });

  it('Escape lo cierra', async () => {
    await mount();
    click(cards()[0].querySelector('.mon-event__headline'));
    expect(document.querySelector('[role="dialog"]')).not.toBeNull();
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(document.querySelector('[role="dialog"]')).toBeNull();
  });

  it('un mensaje o respuesta enlaza a su conversación (con el "+" del teléfono codificado)', async () => {
    await mount();
    click(cards()[1].querySelector('.mon-event__headline'));
    const link = document.querySelector<HTMLAnchorElement>('[role="dialog"] a');
    expect(link?.textContent).toContain('Ver la conversación');
    expect(link?.getAttribute('href')).toBe('/monitoreo/conversaciones?canal=whatsapp&usuario=%2B5492610000000');
  });

  it('un evento de pedido abre el detalle del pedido existente', async () => {
    order.mockResolvedValue({
      id: 7, order_number: 'ORD-2026-0007', customer_name: 'Ana Pérez', customer_email: 'ana@example.com',
      customer_phone: null, quantity: 2, total_amount: '349.99', status: 'confirmed', received_at: null,
      processed_at: null, notified_at: null, data_source: 'measured', product_sku: 'PROD-001',
      product_name: 'Notebook 14"', raw_payload: null, order_items: [],
    });
    await mount();
    click(cards()[2].querySelector('.mon-event__headline'));
    click(buttonByText('Ver pedido ORD-2026-0007'));
    await advance(0);
    expect(order).toHaveBeenCalledWith(7);
    expect(document.querySelectorAll('[role="dialog"]')).toHaveLength(1);
    expect(document.querySelector('[role="dialog"]')?.textContent).toContain('ORD-2026-0007');
  });

  it('un ticket enlaza a la pantalla de Tickets', async () => {
    nextPage = makePage([fresh], { newest_cursor: 'cur-2' });
    await mount();
    await advance(3000);
    click(cards()[0].querySelector('.mon-event__headline'));
    const link = document.querySelector<HTMLAnchorElement>('[role="dialog"] a[href="/tickets"]');
    expect(link?.textContent).toContain('Ver en Tickets');
  });
});
