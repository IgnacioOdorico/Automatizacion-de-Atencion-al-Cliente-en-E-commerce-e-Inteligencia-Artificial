import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/api/client';
import { dashboardApi, monitoringApi } from '@/api/endpoints';
import { MonitoreoConversacionesPage } from '@/pages/MonitoreoConversacionesPage';
import type {
  ConversationsPage,
  ConversationsParams,
  ThreadPage,
  ThreadParams,
} from '@/types/monitoring';

import { makeConversation, makeThreadItem } from './helpers/monitoringFixtures';

vi.mock('@/api/endpoints', () => ({
  monitoringApi: { summary: vi.fn(), events: vi.fn(), conversations: vi.fn(), thread: vi.fn() },
  dashboardApi: { order: vi.fn() },
}));

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const conversations = vi.mocked(monitoringApi.conversations);
const thread = vi.mocked(monitoringApi.thread);
const order = vi.mocked(dashboardApi.order);

// ---------- fixtures ----------

const PHONE = '+5492610000000';
const HTML_MESSAGE = 'Hola <b>equipo</b>\nquiero saber de mi pedido';

const lucia = makeConversation({
  channel: 'whatsapp',
  user_id: PHONE,
  last_at: '2026-09-21T14:03:20.000Z',
  messages: 4,
  last_intent: 'RECLAMO',
  last_message_preview: 'Me llegó roto, quiero un reembolso',
  has_urgent: true,
  open_tickets: 2,
});
const caro = makeConversation({
  channel: 'telegram',
  user_id: '1289347651',
  last_at: '2026-09-21T13:50:00.000Z',
  messages: 1,
  last_intent: 'FAQ',
  last_message_preview: '¿Cuánto tarda el envío?',
  has_urgent: false,
  open_tickets: 0,
});
const mail = makeConversation({
  channel: 'email',
  user_id: 'cliente@example.com',
  last_at: '2026-09-20T10:00:00.000Z',
  messages: 2,
  last_intent: 'GENERAL',
  last_message_preview: 'Gracias!',
  has_urgent: false,
  open_tickets: 0,
});

const listPage: ConversationsPage = { items: [lucia, caro, mail], has_more: false, next_before: null };

const t1 = makeThreadItem(1, {
  received_at: '2026-09-20T15:00:00.000Z',
  message: HTML_MESSAGE,
  responded_at: '2026-09-20T15:00:03.000Z',
  ai_response: '¡Hola! Ya te ayudo.',
  intent: 'FAQ',
  tmr_seconds: 3,
});
const t2 = makeThreadItem(2, {
  received_at: '2026-09-21T14:00:00.000Z',
  message: '¿Dónde está mi pedido ORD-2026-0007?',
  responded_at: '2026-09-21T14:00:04.000Z',
  ai_response: 'Tu pedido está confirmado.',
  intent: 'ESTADO_PEDIDO',
  tmr_seconds: 3.918,
  order: { id: 7, order_number: 'ORD-2026-0007', status: 'confirmed' },
});
const t3 = makeThreadItem(3, {
  received_at: '2026-09-21T14:03:00.000Z',
  message: 'Me llegó roto, quiero un reembolso',
  responded_at: '2026-09-21T14:03:05.000Z',
  ai_response: 'Lamento lo sucedido, ya generé un ticket.',
  intent: 'RECLAMO',
  is_urgent: true,
  tmr_seconds: 5,
  ticket: { id: 3, status: 'open', priority: 'high' },
});
const t4 = makeThreadItem(4, {
  received_at: '2026-09-21T14:04:30.000Z',
  message: 'Sigo esperando',
  responded_at: null,
  ai_response: null,
  intent: null,
  tmr_seconds: null,
});

const threadPage = (items = [t1, t2, t3, t4], extra: Partial<ThreadPage> = {}): ThreadPage => ({
  channel: 'whatsapp',
  user_id: PHONE,
  items,
  has_more: false,
  next_before: null,
  ...extra,
});

// ---------- entorno ----------

let container: HTMLDivElement;
let root: Root;
let visibility: 'visible' | 'hidden';
let nextThread: ThreadPage;

function Where() {
  const { pathname, search } = useLocation();
  return <span data-testid="where">{pathname + search}</span>;
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date'] });
  vi.setSystemTime(new Date('2026-09-21T14:05:00.000Z'));
  visibility = 'visible';
  nextThread = threadPage();
  Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => visibility });

  order.mockReset();
  conversations.mockReset().mockImplementation(async (_p: ConversationsParams = {}) => listPage);
  thread.mockReset().mockImplementation(async (_p: ThreadParams) => nextThread);

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

async function mount(entry = '/monitoreo/conversaciones') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } });
  await act(async () => {
    root.render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[entry]}>
          <Routes>
            <Route path="/monitoreo/conversaciones" element={<MonitoreoConversacionesPage />} />
          </Routes>
          <Where />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  });
  await advance(0);
}

const where = () => container.querySelector('[data-testid="where"]')?.textContent;
const items = () => Array.from(container.querySelectorAll<HTMLElement>('.mon-conv'));
const bubbles = () => Array.from(container.querySelectorAll<HTMLElement>('.mon-bubble'));
const buttonByText = (text: string) =>
  Array.from(document.querySelectorAll<HTMLButtonElement>('button')).find((b) => b.textContent?.trim() === text);
const click = (el: Element | undefined | null) => {
  if (!el) throw new Error('elemento no encontrado');
  act(() => (el as HTMLElement).click());
};
const lastCall = <T,>(fn: { mock: { calls: T[][] } }) => fn.mock.calls[fn.mock.calls.length - 1][0];

function type(input: HTMLInputElement, value: string) {
  act(() => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, value);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
}

const OPEN = `/monitoreo/conversaciones?canal=whatsapp&usuario=${encodeURIComponent(PHONE)}`;

// ---------- tests ----------

describe('Conversaciones: lista de hilos', () => {
  it('muestra cada hilo con contacto, canal, vista previa, urgencia y tickets abiertos', async () => {
    await mount();
    expect(items()).toHaveLength(3);
    const first = items()[0];
    expect(first.textContent).toContain('+54 9 2610000000');
    expect(first.textContent).toContain('WhatsApp');
    expect(first.textContent).toContain('Me llegó roto, quiero un reembolso');
    expect(first.textContent).toContain('Urgente');
    expect(first.textContent).toContain('2 tickets abiertos');
    expect(first.textContent).toContain('4 mensajes');
    expect(first.textContent).toContain('Reclamo');
    expect(items()[1].textContent).toContain('Chat 1289347651');
    expect(items()[1].textContent).not.toContain('Urgente');
    expect(items()[1].textContent).toContain('1 mensaje');
  });

  it('sin hilos: explica qué va a aparecer y cuándo', async () => {
    conversations.mockResolvedValue({ items: [], has_more: false, next_before: null });
    await mount();
    expect(container.textContent).toContain('El bot todavía no atendió mensajes');
    expect(container.textContent).toContain('WhatsApp, Telegram o email');
  });

  it('se actualiza sola cada 5 segundos', async () => {
    await mount();
    expect(conversations).toHaveBeenCalledTimes(1);
    await advance(5000);
    expect(conversations).toHaveBeenCalledTimes(2);
  });

  it('con la pestaña del navegador oculta no consulta', async () => {
    await mount();
    visibility = 'hidden';
    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await advance(12000);
    expect(conversations).toHaveBeenCalledTimes(1);
  });

  it('error: mensaje claro y "Reintentar"', async () => {
    conversations.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    await mount();
    expect(container.querySelector('[role="alert"]')?.textContent).toContain('Sin conexión con el servidor');
    click(buttonByText('Reintentar'));
    await advance(0);
    expect(items()).toHaveLength(3);
  });

  it('la búsqueda espera a que termines de escribir y va a la API recortada', async () => {
    await mount();
    const input = container.querySelector('input[type="search"], input[type="text"]') as HTMLInputElement;
    expect(input).not.toBeNull();
    type(input, ' pedido 7 ');
    await advance(100);
    expect(conversations).toHaveBeenCalledTimes(1);
    await advance(300);
    expect(lastCall(conversations)).toMatchObject({ q: 'pedido 7' });
  });

  it('el filtro de canal se manda a la API', async () => {
    await mount();
    const select = container.querySelector('select') as HTMLSelectElement;
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(select, 'telegram');
      select.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await advance(0);
    expect(lastCall(conversations)).toMatchObject({ channel: 'telegram' });
  });

  it('sin resultados para la búsqueda: lo dice y ofrece limpiarla', async () => {
    await mount();
    conversations.mockResolvedValue({ items: [], has_more: false, next_before: null });
    const input = container.querySelector('input[type="search"], input[type="text"]') as HTMLInputElement;
    type(input, 'zzz');
    await advance(400);
    await advance(0); // el render con la respuesta llega un ciclo después de la request
    expect(container.textContent).toContain('Ninguna conversación coincide');
    conversations.mockResolvedValue(listPage);
    click(buttonByText('Quitar filtros'));
    await advance(400);
    await advance(0);
    expect(items()).toHaveLength(3);
  });

  it('"Cargar más conversaciones" pide con `before` y agrega debajo', async () => {
    conversations.mockImplementation(async (p: ConversationsParams = {}) =>
      p.before
        ? { items: [makeConversation({ user_id: 'viejo', last_at: '2026-09-19T10:00:00.000Z' })], has_more: false, next_before: null }
        : { items: [lucia, caro], has_more: true, next_before: 'cur-1' },
    );
    await mount();
    click(buttonByText('Cargar más conversaciones'));
    await advance(0);
    expect(lastCall(conversations)).toMatchObject({ before: 'cur-1' });
    expect(items()).toHaveLength(3);
    expect(buttonByText('Cargar más conversaciones')).toBeUndefined();
  });
});

describe('Conversaciones: hilo abierto', () => {
  it('sin hilo elegido, el panel invita a elegir uno', async () => {
    await mount();
    expect(container.textContent).toContain('Elegí una conversación');
    expect(thread).not.toHaveBeenCalled();
  });

  it('elegir un hilo lo pone en la URL (con el "+" codificado) y pide sus mensajes', async () => {
    await mount();
    click(items()[0]);
    await advance(0);
    expect(where()).toBe(OPEN);
    expect(lastCall(thread)).toMatchObject({ channel: 'whatsapp', userId: PHONE, limit: 50 });
    expect(bubbles().length).toBeGreaterThan(0);
  });

  it('un enlace directo abre el hilo y lo marca como elegido en la lista', async () => {
    await mount(OPEN);
    expect(lastCall(thread)).toMatchObject({ userId: PHONE });
    expect(items()[0].getAttribute('aria-current')).toBe('true');
    expect(items()[1].getAttribute('aria-current')).toBeNull();
  });

  it('un enlace con un canal inválido se ignora', async () => {
    await mount('/monitoreo/conversaciones?canal=sms&usuario=1');
    expect(thread).not.toHaveBeenCalled();
    expect(container.textContent).toContain('Elegí una conversación');
  });

  it('el mensaje del cliente va de un lado y la respuesta del bot del otro, con el texto exacto como texto', async () => {
    await mount(OPEN);
    const customer = container.querySelectorAll('.mon-bubble--customer');
    const bot = container.querySelectorAll('.mon-bubble--bot');
    expect(customer).toHaveLength(4);
    expect(customer[0].querySelector('.mon-bubble__text')?.textContent).toBe(HTML_MESSAGE);
    expect(container.querySelector('.mon-bubble b')).toBeNull();
    expect(bot[0].querySelector('.mon-bubble__text')?.textContent).toBe('¡Hola! Ya te ayudo.');
  });

  it('cada respuesta trae su hora, intent, urgencia y TMR con texto', async () => {
    await mount(OPEN);
    const bot = Array.from(container.querySelectorAll('.mon-bubble--bot'));
    expect(bot[1].textContent).toContain('Estado de pedido');
    expect(bot[1].textContent).toContain('TMR 3,9 s');
    expect(bot[1].textContent).toContain('11:00');
    expect(bot[2].textContent).toContain('Reclamo');
    expect(bot[2].textContent).toContain('Urgente');
  });

  it('separa por día con Ayer y Hoy', async () => {
    await mount(OPEN);
    const days = Array.from(container.querySelectorAll('.mon-day')).map((d) => d.textContent);
    expect(days).toEqual(['Ayer', 'Hoy']);
  });

  it('un mensaje sin respuesta todavía lo indica en vez de inventar una', async () => {
    await mount(OPEN);
    const pending = container.querySelector('.mon-bubble--pending');
    expect(pending?.textContent).toContain('El bot todavía no respondió');
    expect(container.querySelectorAll('.mon-bubble--bot')).toHaveLength(4);
  });

  it('el pedido y el ticket vinculados aparecen como enlaces', async () => {
    order.mockResolvedValue({
      id: 7, order_number: 'ORD-2026-0007', customer_name: 'Ana Pérez', customer_email: 'ana@example.com',
      customer_phone: null, quantity: 2, total_amount: '349.99', status: 'confirmed', received_at: null,
      processed_at: null, notified_at: null, data_source: 'measured', product_sku: 'PROD-001',
      product_name: 'Notebook 14"', raw_payload: null, order_items: [],
    });
    await mount(OPEN);
    click(buttonByText('Pedido ORD-2026-0007 · Confirmado'));
    await advance(0);
    expect(order).toHaveBeenCalledWith(7);
    expect(document.querySelector('[role="dialog"]')?.textContent).toContain('ORD-2026-0007');

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    const ticket = container.querySelector<HTMLAnchorElement>('a[href="/tickets"]');
    expect(ticket?.textContent).toContain('Ticket #3');
    expect(ticket?.textContent).toContain('Prioridad alta');
  });

  it('se actualiza sola cada 5 segundos y suma lo nuevo sin perder lo anterior', async () => {
    await mount(OPEN);
    const before = bubbles().length;
    const t5 = makeThreadItem(5, {
      received_at: '2026-09-21T14:05:03.000Z',
      message: 'Hola de nuevo',
      responded_at: '2026-09-21T14:05:05.000Z',
      ai_response: 'Acá estoy.',
    });
    nextThread = threadPage([t2, t3, t4, t5]); // la ventana del server ya no incluye al primero
    await advance(5000);
    expect(thread.mock.calls.length).toBeGreaterThan(1);
    expect(container.textContent).toContain('Hola de nuevo');
    expect(container.textContent).toContain(HTML_MESSAGE.split('\n')[0]);
    expect(bubbles().length).toBeGreaterThan(before);
  });

  it('cuando el bot responde, la burbuja pendiente se completa', async () => {
    await mount(OPEN);
    expect(container.querySelector('.mon-bubble--pending')).not.toBeNull();
    nextThread = threadPage([
      t1, t2, t3,
      { ...t4, responded_at: '2026-09-21T14:05:02.000Z', ai_response: 'Ya lo reviso.', intent: 'GENERAL', tmr_seconds: 2.1 },
    ]);
    await advance(5000);
    expect(container.querySelector('.mon-bubble--pending')).toBeNull();
    expect(container.textContent).toContain('Ya lo reviso.');
  });

  it('"Cargar mensajes anteriores" pide con `before` y los pone arriba', async () => {
    nextThread = threadPage([t3, t4], { has_more: true, next_before: 'cur-old' });
    await mount(OPEN);
    thread.mockImplementation(async (p: ThreadParams) =>
      p.before ? threadPage([t1, t2], { has_more: false, next_before: null }) : nextThread,
    );
    click(buttonByText('Cargar mensajes anteriores'));
    await advance(0);
    expect(lastCall(thread)).toMatchObject({ before: 'cur-old' });
    const texts = Array.from(container.querySelectorAll('.mon-bubble--customer .mon-bubble__text')).map((n) => n.textContent);
    expect(texts[0]).toBe(HTML_MESSAGE);
    expect(texts).toHaveLength(4);
    expect(buttonByText('Cargar mensajes anteriores')).toBeUndefined();
  });

  it('el botón Volver limpia el hilo de la URL (en móvil vuelve a la lista)', async () => {
    await mount(OPEN);
    click(buttonByText('Volver a las conversaciones'));
    expect(where()).toBe('/monitoreo/conversaciones');
    expect(container.textContent).toContain('Elegí una conversación');
  });

  it('una conversación que no existe se explica y permite volver', async () => {
    thread.mockRejectedValue(new ApiError(404, 'Conversación no encontrada', 'Conversación no encontrada'));
    await mount(OPEN);
    expect(container.textContent).toContain('Esa conversación no existe o todavía no tiene mensajes');
    expect(buttonByText('Volver a las conversaciones')).toBeTruthy();
  });

  it('error al cargar el hilo: "Reintentar"', async () => {
    thread.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    await mount(OPEN);
    expect(container.querySelector('.mon-chat [role="alert"]')?.textContent).toContain('Sin conexión con el servidor');
    click(Array.from(container.querySelectorAll('.mon-chat button')).find((b) => b.textContent === 'Reintentar'));
    await advance(0);
    expect(bubbles().length).toBeGreaterThan(0);
  });

  it('cambiar de hilo no arrastra los mensajes del anterior', async () => {
    await mount(OPEN);
    thread.mockImplementation(async () => ({
      channel: 'telegram', user_id: '1289347651', items: [makeThreadItem(9, { message: 'Consulta de Caro', ai_response: 'Respuesta a Caro' })],
      has_more: false, next_before: null,
    }));
    click(items()[1]);
    await advance(0);
    expect(container.textContent).toContain('Consulta de Caro');
    expect(container.querySelector('.mon-chat')?.textContent).not.toContain('Tu pedido está confirmado.');
    expect(where()).toBe('/monitoreo/conversaciones?canal=telegram&usuario=1289347651');
  });
});
