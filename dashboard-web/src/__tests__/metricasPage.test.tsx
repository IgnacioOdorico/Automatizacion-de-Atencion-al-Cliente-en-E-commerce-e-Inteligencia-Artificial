import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { metricsApi } from '@/api/endpoints';
import { MetricasPage } from '@/pages/MetricasPage';
import type { ChatbotMetrics, OrdersMetrics } from '@/types/metrics';

vi.mock('@/api/endpoints', () => ({
  metricsApi: { orders: vi.fn(), chatbot: vi.fn() },
}));

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const ordersMock = vi.mocked(metricsApi.orders);
const chatbotMock = vi.mocked(metricsApi.chatbot);

function orders(overrides: Partial<OrdersMetrics> = {}): OrdersMetrics {
  return {
    window_hours: null,
    generated_at: '2026-09-21T00:00:00.000Z',
    avg_mttd_seconds: 34.2,
    avg_mttr_seconds: 18.7,
    avg_end_to_end_seconds: 52.9,
    total_orders: 42,
    by_status: {
      pending: 1,
      processing: 0,
      confirmed: 30,
      shipped: 4,
      delivered: 2,
      no_stock: 3,
      cancelled: 1,
      error: 1,
    },
    daily: [{ date: '2026-09-14', total_orders: 5, confirmed: 4, shipped: 0, delivered: 0, no_stock: 1, cancelled: 0, error: 0 }],
    ...overrides,
  };
}

function chatbot(overrides: Partial<ChatbotMetrics> = {}): ChatbotMetrics {
  return {
    window_hours: null,
    generated_at: '2026-09-21T00:00:00.000Z',
    avg_tmr_seconds: 4.1,
    total_interactions: 37,
    by_intent: {
      FAQ: { count: 15, avg_tmr_seconds: 3.2 },
      ESTADO_PEDIDO: { count: 12, avg_tmr_seconds: 5.5 },
      RECLAMO: { count: 6, avg_tmr_seconds: 6.8 },
      GENERAL: { count: 4, avg_tmr_seconds: null },
    },
    by_channel_daily: [{ date: '2026-09-14', whatsapp: 3, telegram: 1, email: 0 }],
    ...overrides,
  };
}

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  ordersMock.mockReset().mockResolvedValue(orders());
  chatbotMock.mockReset().mockResolvedValue(chatbot());
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.restoreAllMocks();
});

async function flush() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

async function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } });
  await act(async () => {
    root.render(
      <QueryClientProvider client={client}>
        <MetricasPage />
      </QueryClientProvider>,
    );
  });
  await flush();
  await flush();
}

const text = () => container.textContent ?? '';
const selects = () => Array.from(container.querySelectorAll('select'));
const retryButtons = () => Array.from(container.querySelectorAll('button')).filter((b) => b.textContent === 'Reintentar');

describe('MetricasPage: bloque Pedidos', () => {
  it('con datos: stat cards, dona de estados y área diaria', async () => {
    await mount();
    expect(text()).toContain('MTTD promedio');
    expect(text()).toContain('34,2 s');
    expect(text()).toContain('Confirmado');
    expect(container.querySelector('.chart-donut')).not.toBeNull();
    expect(container.querySelector('.chart-area')).not.toBeNull();
  });

  it('total_orders 0: estado vacío explicativo, no gráficos rotos', async () => {
    ordersMock.mockResolvedValue(orders({ total_orders: 0, by_status: {}, daily: [] }));
    await mount();
    expect(text()).toContain('Todavía no hay pedidos para este período');
  });

  it('error: "Reintentar" vuelve a pedir los datos', async () => {
    ordersMock.mockRejectedValue(new TypeError('Failed to fetch'));
    await mount();
    expect(retryButtons().length).toBeGreaterThan(0);
    ordersMock.mockResolvedValue(orders());
    await act(async () => {
      retryButtons()[0]?.click();
    });
    await flush();
    await flush();
    expect(text()).toContain('MTTD promedio');
  });
});

describe('MetricasPage: bloque Chatbot', () => {
  it('con datos: TMR, barras por intent (con "sin respuestas" cuando corresponde) y dona', async () => {
    await mount();
    expect(text()).toContain('TMR promedio');
    expect(text()).toContain('Pregunta frecuente');
    expect(text()).toContain('Sin respuestas'); // GENERAL: avg_tmr_seconds null
    expect(container.querySelectorAll('.chart-bar').length).toBeGreaterThan(0);
  });

  it('total_interactions 0: estado vacío explicativo', async () => {
    chatbotMock.mockResolvedValue(chatbot({ total_interactions: 0, by_intent: {}, by_channel_daily: [] }));
    await mount();
    expect(text()).toContain('Todavía no hay interacciones para este período');
  });
});

describe('MetricasPage: filtros compartidos', () => {
  it('la ventana de tiempo se manda como `hours` a los dos endpoints', async () => {
    await mount();
    const [hoursSelect] = selects();
    await act(async () => {
      hoursSelect.value = '24';
      hoursSelect.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await flush();
    expect(ordersMock).toHaveBeenLastCalledWith({ hours: 24, data_source: undefined });
    expect(chatbotMock).toHaveBeenLastCalledWith({ hours: 24, data_source: undefined });
  });

  it('"Carga manual" sigue en Pedidos y se ignora (con aviso) en Chatbot', async () => {
    await mount();
    const [, dataSourceSelect] = selects();
    await act(async () => {
      dataSourceSelect.value = 'e4_manual';
      dataSourceSelect.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await flush();
    expect(ordersMock).toHaveBeenLastCalledWith({ hours: undefined, data_source: 'e4_manual' });
    expect(chatbotMock).toHaveBeenLastCalledWith({ hours: undefined, data_source: undefined });
    expect(text()).toContain('no existe como origen de las interacciones del chatbot');
  });
});
