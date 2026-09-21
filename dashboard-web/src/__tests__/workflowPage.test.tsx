import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/api/client';
import { monitoringApi } from '@/api/endpoints';
import { MonitoreoWorkflowPage } from '@/pages/MonitoreoWorkflowPage';
import type { WorkflowGraph, WorkflowsResponse } from '@/types/monitoring';

import { installFakeResizeObserver } from './helpers/fakeResizeObserver';
import { FLUJO1_ID, FLUJO2_ID, flujo1Graph, flujo2Graph, makeWorkflowSummary } from './helpers/workflowFixtures';

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

const workflows = vi.mocked(monitoringApi.workflows);
const workflowGraph = vi.mocked(monitoringApi.workflowGraph);

const FLUJO1 = makeWorkflowSummary(FLUJO1_ID, flujo1Graph.name, {
  executions_24h: 12,
  errors_24h: 1,
  last_execution: { id: 15, status: 'success', started_at: '2026-09-21T14:03:20.000Z', duration_ms: 435 },
});
const FLUJO2 = makeWorkflowSummary(FLUJO2_ID, flujo2Graph.name, {
  executions_24h: 3,
  errors_24h: 0,
  last_execution: { id: 9, status: 'success', started_at: '2026-09-21T09:00:00.000Z', duration_ms: 900 },
});

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  installFakeResizeObserver();
  workflows.mockReset().mockResolvedValue({ available: true, items: [FLUJO2, FLUJO1] });
  workflowGraph.mockReset().mockImplementation(async (id: string): Promise<WorkflowGraph> => {
    if (id === FLUJO1_ID) return flujo1Graph;
    if (id === FLUJO2_ID) return flujo2Graph;
    throw new ApiError(404, 'Workflow no encontrado', 'Workflow no encontrado');
  });
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
  await flush();
  await flush();
}

const nodes = () => Array.from(container.querySelectorAll<SVGGElement>('.wf-node'));
const select = () => container.querySelector('select') as HTMLSelectElement;
const text = () => container.textContent ?? '';

describe('Pestaña Workflow: elección del workflow', () => {
  it('por defecto muestra el activo con la ejecución más reciente y pide solo su grafo', async () => {
    await mount();
    expect(workflowGraph).toHaveBeenCalledTimes(1);
    expect(workflowGraph).toHaveBeenCalledWith(FLUJO1_ID);
    expect(select().value).toBe(FLUJO1_ID);
    expect(nodes()).toHaveLength(flujo1Graph.nodes.length);
  });

  it('el selector lista los workflows por nombre y muestra el resumen de las últimas 24 h', async () => {
    await mount();
    const options = Array.from(select().options).map((o) => o.textContent);
    expect(options).toEqual([flujo2Graph.name, flujo1Graph.name]);
    expect(text()).toContain('12 ejecuciones en 24 h · 1 con error');
    expect(text()).toContain('Activo');
  });

  it('un workflow inactivo se avisa con texto', async () => {
    workflows.mockResolvedValue({ available: true, items: [{ ...FLUJO1, active: false }] });
    await mount();
    expect(text()).toContain('Inactivo');
  });

  it('elegir otro workflow dibuja el suyo', async () => {
    await mount();
    await act(async () => {
      const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set;
      setter?.call(select(), FLUJO2_ID);
      select().dispatchEvent(new Event('change', { bubbles: true }));
    });
    await flush();
    expect(workflowGraph).toHaveBeenLastCalledWith(FLUJO2_ID);
    expect(nodes()).toHaveLength(flujo2Graph.nodes.length);
    expect(text()).toContain('3 ejecuciones en 24 h · sin errores');
  });

  it('el nodo elegido queda marcado y se limpia al cambiar de workflow', async () => {
    await mount();
    act(() => nodes()[1].dispatchEvent(new MouseEvent('click', { bubbles: true })));
    expect(nodes()[1].getAttribute('aria-pressed')).toBe('true');
    await act(async () => {
      const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set;
      setter?.call(select(), FLUJO2_ID);
      select().dispatchEvent(new Event('change', { bubbles: true }));
    });
    await flush();
    expect(nodes().every((n) => n.getAttribute('aria-pressed') === 'false')).toBe(true);
  });
});

describe('Pestaña Workflow: estados', () => {
  it('mientras carga muestra un esqueleto que avisa a los lectores de pantalla', async () => {
    workflows.mockReturnValue(new Promise<WorkflowsResponse>(() => {}));
    await mount();
    const status = container.querySelector('[role="status"]');
    expect(status?.getAttribute('aria-busy')).toBe('true');
    expect(container.querySelector('.wf-node')).toBeNull();
  });

  it('con el grafo cargando muestra el esqueleto del lienzo', async () => {
    workflowGraph.mockReturnValue(new Promise<WorkflowGraph>(() => {}));
    await mount();
    expect(container.querySelector('.wf-canvas--skeleton')).not.toBeNull();
    expect(select().value).toBe(FLUJO1_ID);
  });

  it('n8n no disponible: explica qué falta en vez de romper', async () => {
    workflows.mockResolvedValue({ available: false, items: [] });
    await mount();
    expect(text()).toContain('No pudimos leer los workflows de n8n');
    expect(text()).toContain('importado');
    expect(container.querySelector('.wf-canvas')).toBeNull();
  });

  it('n8n disponible pero sin workflows: lo dice distinto', async () => {
    workflows.mockResolvedValue({ available: true, items: [] });
    await mount();
    expect(text()).toContain('Todavía no hay workflows en n8n');
    expect(container.querySelector('.wf-canvas')).toBeNull();
  });

  it('error al pedir los workflows: mensaje y Reintentar, que vuelve a pedirlos', async () => {
    workflows.mockRejectedValueOnce(new ApiError(500, 'boom'));
    await mount();
    expect(container.querySelector('[role="alert"]')).not.toBeNull();
    const retry = Array.from(container.querySelectorAll('button')).find((b) => b.textContent?.includes('Reintentar'));
    expect(retry).toBeDefined();
    workflows.mockResolvedValue({ available: true, items: [FLUJO1] });
    await act(async () => retry?.click());
    await flush();
    await flush();
    expect(workflows).toHaveBeenCalledTimes(2);
    expect(nodes().length).toBeGreaterThan(0);
  });

  it('error al pedir el grafo: Reintentar vuelve a pedirlo', async () => {
    workflowGraph.mockRejectedValueOnce(new ApiError(404, 'Workflow no encontrado', 'Workflow no encontrado'));
    await mount();
    expect(text()).toContain('Workflow no encontrado');
    const retry = Array.from(container.querySelectorAll('button')).find((b) => b.textContent?.includes('Reintentar'));
    await act(async () => retry?.click());
    await flush();
    await flush();
    expect(workflowGraph).toHaveBeenCalledTimes(2);
    expect(nodes()).toHaveLength(flujo1Graph.nodes.length);
  });

  it('un workflow sin nodos tiene su propio aviso', async () => {
    workflowGraph.mockResolvedValue({ ...flujo1Graph, nodes: [], edges: [] });
    await mount();
    expect(text()).toContain('todavía no tiene nodos');
  });
});
