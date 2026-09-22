import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/api/client';
import { dashboardApi, monitoringApi } from '@/api/endpoints';
import { MonitoreoWorkflowPage } from '@/pages/MonitoreoWorkflowPage';
import type { Summary } from '@/types/api';

import { installFakeResizeObserver } from './helpers/fakeResizeObserver';
import { FLUJO1_ID, flujo1Graph, makeWorkflowSummary } from './helpers/workflowFixtures';

vi.mock('@/api/endpoints', () => ({
  monitoringApi: {
    workflows: vi.fn(),
    workflowGraph: vi.fn(),
    executions: vi.fn(),
    execution: vi.fn(),
  },
  dashboardApi: { summary: vi.fn() },
}));

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const summary = vi.mocked(dashboardApi.summary);
const workflows = vi.mocked(monitoringApi.workflows);

const SUMMARY: Summary = {
  total_orders: 31,
  orders_confirmed: 24,
  avg_mttd_seg: '0.46',
  avg_mttr_seg: '2.31',
  total_interactions: 12,
  avg_tmr_seg: '3.42',
  total_tickets: 2,
  tickets_resolved: 1,
  orders_today: 9,
  tickets_open: 1,
  data_source: 'all',
};

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  installFakeResizeObserver();
  summary.mockReset().mockResolvedValue(SUMMARY);
  workflows.mockReset().mockResolvedValue({ available: true, items: [makeWorkflowSummary(FLUJO1_ID, flujo1Graph.name)] });
  vi.mocked(monitoringApi.workflowGraph).mockReset().mockResolvedValue(flujo1Graph);
  vi.mocked(monitoringApi.executions)
    .mockReset()
    .mockResolvedValue({ available: true, items: [], has_more: false, next_before: null });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
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
        <MemoryRouter initialEntries={['/monitoreo/workflow']}>
          <Routes>
            <Route path="/monitoreo/workflow" element={<MonitoreoWorkflowPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  });
  for (let i = 0; i < 4; i += 1) await flush();
}

const card = () => container.querySelector<HTMLElement>('.wf-metrics');
const metrics = () => Array.from(container.querySelectorAll<HTMLElement>('li.wf-metric'));

describe('Tarjeta "Métricas de la tesis"', () => {
  it('explica MTTD, MTTR y TMR en el orden de la tesis, cada una con su flujo y su nombre', async () => {
    await mount();
    expect(card()?.querySelector('h2')?.textContent).toBe('Métricas de la tesis');
    expect(metrics().map((m) => m.querySelector('.wf-metric__short')?.textContent)).toEqual(['MTTD', 'MTTR', 'TMR']);
    expect(metrics().map((m) => m.querySelector('.wf-metric__flow')?.textContent)).toEqual(['Pedidos', 'Pedidos', 'Asistente']);
    expect(metrics()[0].textContent).toContain('Tiempo hasta procesar el pedido');
    expect(metrics()[2].textContent).toContain('Tiempo de respuesta del chatbot');
  });

  it('cada una dice qué mide y con qué marcas de tiempo se calcula (la definición real de las vistas)', async () => {
    await mount();
    expect(metrics()[0].textContent).toContain('processed_at − received_at');
    expect(metrics()[1].textContent).toContain('notified_at − processed_at');
    expect(metrics()[2].textContent).toContain('responded_at − received_at');
    expect(metrics()[1].textContent).toMatch(/email de aviso/);
  });

  it('muestra los promedios actuales y sobre cuántas muestras salen', async () => {
    await mount();
    expect(metrics()[0].querySelector('.wf-metric__value')?.textContent).toBe('460 ms');
    expect(metrics()[1].querySelector('.wf-metric__value')?.textContent).toBe('2,3 s');
    expect(metrics()[2].querySelector('.wf-metric__value')?.textContent).toBe('3,4 s');
    expect(metrics()[0].textContent).toContain('Sobre 31 pedidos');
    expect(metrics()[2].textContent).toContain('Sobre 12 mensajes');
  });

  it('sin muestras muestra guiones y lo explica, no ceros inventados', async () => {
    summary.mockResolvedValue({ ...SUMMARY, total_orders: 0, total_interactions: 0, avg_mttd_seg: 0, avg_mttr_seg: 0, avg_tmr_seg: 0 });
    await mount();
    expect(metrics().map((m) => m.querySelector('.wf-metric__value')?.textContent)).toEqual(['—', '—', '—']);
    expect(metrics()[0].textContent).toContain('Todavía sin pedidos');
    expect(metrics()[2].textContent).toContain('Todavía sin mensajes');
  });

  it('mientras carga muestra un esqueleto que avisa a los lectores de pantalla', async () => {
    summary.mockReturnValue(new Promise<Summary>(() => {}));
    await mount();
    expect(card()?.querySelector('[role="status"]')?.getAttribute('aria-busy')).toBe('true');
    expect(metrics()).toHaveLength(0);
  });

  it('si falla: mensaje con Reintentar, y el diagrama sigue funcionando', async () => {
    summary.mockRejectedValueOnce(new ApiError(500, 'boom'));
    await mount();
    expect(card()?.querySelector('[role="alert"]')).not.toBeNull();
    expect(container.querySelectorAll('.wf-node').length).toBeGreaterThan(0);
    const retry = Array.from(card()?.querySelectorAll('button') ?? []).find((b) => b.textContent?.includes('Reintentar'));
    await act(async () => retry?.click());
    for (let i = 0; i < 3; i += 1) await flush();
    expect(summary).toHaveBeenCalledTimes(2);
    expect(metrics()).toHaveLength(3);
  });

  it('no depende del diagrama: ningún nombre de nodo aparece en la tarjeta', async () => {
    await mount();
    const text = card()?.textContent ?? '';
    for (const node of flujo1Graph.nodes) expect(text).not.toContain(node.name);
  });

  it('con n8n sin workflows también se puede leer la explicación de las métricas', async () => {
    workflows.mockResolvedValue({ available: false, items: [] });
    await mount();
    expect(container.textContent).toContain('No pudimos leer los procesos');
    expect(metrics()).toHaveLength(3);
  });
});

describe('Leyenda del diagrama', () => {
  it('explica cada estado con texto (no solo con color) y cómo moverse', async () => {
    await mount();
    const legend = container.querySelector('.wf-legend');
    const text = legend?.textContent ?? '';
    for (const label of ['Correcto', 'Con error', 'No se ejecutó', 'Camino recorrido', 'Camino no tomado', 'Sí / No']) {
      expect(text).toContain(label);
    }
    expect(text).toContain('Ctrl + rueda');
    expect(legend?.getAttribute('aria-label')).toBeTruthy();
  });

  it('las muestras de la leyenda son decorativas: el texto ya lo dice', async () => {
    await mount();
    const swatches = container.querySelectorAll('.wf-legend__swatch, .wf-legend__line, .wf-legend__tag');
    expect(swatches.length).toBeGreaterThan(0);
    for (const swatch of swatches) expect(swatch.getAttribute('aria-hidden')).toBe('true');
  });
});
