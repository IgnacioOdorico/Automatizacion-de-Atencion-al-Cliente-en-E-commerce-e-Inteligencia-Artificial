import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/api/client';
import { monitoringApi } from '@/api/endpoints';
import { MonitoreoWorkflowPage } from '@/pages/MonitoreoWorkflowPage';
import type { ExecutionDetail, ExecutionsParams } from '@/types/monitoring';

import { installFakeResizeObserver } from './helpers/fakeResizeObserver';
import {
  FLUJO1_ID,
  flujo1Graph,
  makeExecution,
  makeWorkflowSummary,
  traceConStock,
  traceError,
  traceSinStock,
} from './helpers/workflowFixtures';

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

const executions = vi.mocked(monitoringApi.executions);
const execution = vi.mocked(monitoringApi.execution);

let container: HTMLDivElement;
let root: Root;
/** "Base de datos" de mentira: todas las ejecuciones que devuelve la API, de la más nueva a la más vieja. */
let all: ExecutionDetail[];
let visibility: 'visible' | 'hidden';

function at(id: number, base: ExecutionDetail): ExecutionDetail {
  return {
    ...base,
    execution: {
      ...base.execution,
      id,
      started_at: new Date(Date.UTC(2026, 8, 21, 14, 0, 0) - (100 - id) * 60_000).toISOString(),
    },
  };
}

function setAll(...items: ExecutionDetail[]) {
  all = [...items].sort((a, b) => b.execution.id - a.execution.id);
}

function apiExecutions(params: ExecutionsParams = {}) {
  const limit = params.limit ?? 20;
  const list = all
    .map((d) => d.execution)
    .filter((e) => (!params.status || e.status === params.status) && (!params.before || e.id < params.before));
  const page = list.slice(0, limit);
  const hasMore = list.length > limit;
  return { available: true, items: page, has_more: hasMore, next_before: hasMore ? page[page.length - 1].id : null };
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date'] });
  vi.setSystemTime(new Date('2026-09-21T14:05:00.000Z'));
  installFakeResizeObserver();
  vi.stubGlobal('matchMedia', undefined);
  visibility = 'visible';
  Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => visibility });

  setAll(at(15, traceConStock(15)), at(14, traceSinStock(14)), at(13, traceError(13)));
  vi.mocked(monitoringApi.workflows).mockReset().mockResolvedValue({
    available: true,
    items: [makeWorkflowSummary(FLUJO1_ID, flujo1Graph.name)],
  });
  vi.mocked(monitoringApi.workflowGraph).mockReset().mockResolvedValue(flujo1Graph);
  executions.mockReset().mockImplementation(async (params) => apiExecutions(params));
  execution.mockReset().mockImplementation(async (id: number) => {
    const found = all.find((d) => d.execution.id === id);
    if (!found) throw new ApiError(404, 'Ejecución no encontrada', 'Ejecución no encontrada');
    return found;
  });

  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

async function advance(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

async function settle() {
  for (let i = 0; i < 8; i += 1) await advance(0);
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
  await settle();
}

const rows = () => Array.from(container.querySelectorAll<HTMLButtonElement>('.wf-run'));
const rowById = (id: number) => rows().find((r) => r.getAttribute('data-execution') === String(id)) as HTMLButtonElement;
const nodes = () => Array.from(container.querySelectorAll<SVGGElement>('.wf-node'));
const nodeByName = (name: string) => nodes().find((n) => n.getAttribute('data-node') === name) as SVGGElement;
const count = (selector: string) => container.querySelectorAll(selector).length;
const buttonByText = (text: string) =>
  Array.from(container.querySelectorAll<HTMLButtonElement>('button')).find((b) => b.textContent?.trim() === text);
const click = (el: Element | undefined | null) => {
  if (!el) throw new Error('elemento no encontrado');
  act(() => (el as HTMLElement).click());
};
const text = () => container.textContent ?? '';
const followSwitch = () => container.querySelector<HTMLButtonElement>('[role="switch"]') as HTMLButtonElement;
const statusSelect = () => container.querySelector<HTMLSelectElement>('.wf-runs-filter select') as HTMLSelectElement;

async function chooseStatus(value: string) {
  await act(async () => {
    const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set;
    setter?.call(statusSelect(), value);
    statusSelect().dispatchEvent(new Event('change', { bubbles: true }));
  });
  await settle();
}

describe('Lista de ejecuciones', () => {
  it('lista las ejecuciones del workflow, de la más nueva a la más vieja', async () => {
    await mount();
    expect(rows().map((r) => r.getAttribute('data-execution'))).toEqual(['15', '14', '13']);
  });

  it('cada fila dice el estado con texto e ícono, el número, la hora relativa y absoluta, la duración y el modo', async () => {
    await mount();
    const row = rowById(15);
    expect(row.textContent).toContain('#15');
    expect(row.textContent).toContain('Correcta');
    expect(row.textContent).toContain('435 ms');
    expect(row.textContent).toContain('Webhook');
    expect(row.querySelector('time')?.textContent).toMatch(/hace .* · \d{2}:\d{2}:\d{2}/);
    expect(row.querySelector('time')?.getAttribute('title')).toMatch(/^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}$/);
  });

  it('una ejecución con error muestra el error resumido', async () => {
    await mount();
    const row = rowById(13);
    expect(row.textContent).toContain('Con error');
    expect(row.textContent).toContain('does not exist for type');
  });

  it('el texto del error se muestra como texto, nunca como HTML', async () => {
    setAll(at(15, { ...traceConStock(15), execution: makeExecution(15, { status: 'error', error_message: '<img src=x onerror=alert(1)>' }) }));
    await mount();
    expect(container.querySelector('.wf-runs img')).toBeNull();
    expect(rowById(15).textContent).toContain('<img src=x onerror=alert(1)>');
  });

  it('la ejecución que se ve en el diagrama queda marcada como actual', async () => {
    await mount();
    expect(rowById(15).getAttribute('aria-current')).toBe('true');
    expect(rowById(14).getAttribute('aria-current')).toBeNull();
  });

  it('elegir otra ejecución pide su detalle y cambia lo que se ilumina', async () => {
    await mount();
    click(rowById(14));
    await settle();
    expect(execution).toHaveBeenLastCalledWith(14);
    expect(rowById(14).getAttribute('aria-current')).toBe('true');
    expect(container.querySelector('.wf-exec')?.textContent).toContain('Ejecución #14');
    expect(container.querySelector('.wf-edge--active[data-to="Marcar Sin Stock"]')).not.toBeNull();
  });

  it('elegir una ejecución a mano apaga "Seguir en vivo"', async () => {
    await mount();
    expect(followSwitch().getAttribute('aria-checked')).toBe('true');
    click(rowById(14));
    await settle();
    expect(followSwitch().getAttribute('aria-checked')).toBe('false');
  });
});

describe('Filtro por estado', () => {
  it('ofrece los estados y pide al servidor solo esas ejecuciones', async () => {
    await mount();
    expect(Array.from(statusSelect().options).map((o) => o.value)).toEqual(
      expect.arrayContaining(['', 'success', 'error']),
    );
    await chooseStatus('error');
    expect(executions).toHaveBeenLastCalledWith(expect.objectContaining({ status: 'error', workflowId: FLUJO1_ID }));
    expect(rows().map((r) => r.getAttribute('data-execution'))).toEqual(['13']);
  });

  it('al filtrar, la ejecución que se ve pasa a ser la más nueva del filtro', async () => {
    await mount();
    await chooseStatus('error');
    expect(container.querySelector('.wf-exec')?.textContent).toContain('Ejecución #13');
    expect(nodeByName('Registrar Orden').getAttribute('class')).toContain('wf-node--error');
  });

  it('si ninguna coincide lo dice y ofrece quitar el filtro', async () => {
    await mount();
    await chooseStatus('crashed');
    expect(text()).toContain('Ninguna ejecución coincide con el filtro');
    click(buttonByText('Quitar filtro'));
    await settle();
    expect(rows()).toHaveLength(3);
  });
});

describe('Cargar más ejecuciones', () => {
  beforeEach(() => {
    setAll(...Array.from({ length: 25 }, (_, i) => at(i + 1, traceConStock(i + 1))));
  });

  it('muestra el botón solo si hay más y pide con el cursor `next_before`', async () => {
    await mount();
    expect(rows()).toHaveLength(20);
    click(buttonByText('Cargar ejecuciones anteriores'));
    await settle();
    expect(executions).toHaveBeenLastCalledWith(expect.objectContaining({ before: 6 }));
    expect(rows()).toHaveLength(25);
    expect(rows()[24].getAttribute('data-execution')).toBe('1');
    expect(buttonByText('Cargar ejecuciones anteriores')).toBeUndefined();
    expect(text()).toContain('Esas son todas las ejecuciones');
  });

  it('lo cargado a pedido sobrevive al refresco automático y no se duplica', async () => {
    await mount();
    click(buttonByText('Cargar ejecuciones anteriores'));
    await settle();
    await advance(4100);
    await settle();
    expect(rows()).toHaveLength(25);
    expect(new Set(rows().map((r) => r.getAttribute('data-execution'))).size).toBe(25);
  });

  it('si falla, avisa y deja reintentar sin perder lo que había', async () => {
    await mount();
    executions.mockRejectedValueOnce(new ApiError(500, 'boom'));
    click(buttonByText('Cargar ejecuciones anteriores'));
    await settle();
    expect(container.querySelector('.wf-runs-more [role="alert"]')?.textContent).toContain('No pudimos cargar más');
    expect(rows()).toHaveLength(20);
    click(buttonByText('Cargar ejecuciones anteriores'));
    await settle();
    expect(rows()).toHaveLength(25);
  });
});

describe('Seguir en vivo', () => {
  it('viene activado y consulta las ejecuciones cada 4 segundos', async () => {
    await mount();
    expect(followSwitch().getAttribute('aria-checked')).toBe('true');
    const before = executions.mock.calls.length;
    await advance(4100);
    expect(executions.mock.calls.length).toBe(before + 1);
    await advance(4000);
    expect(executions.mock.calls.length).toBe(before + 2);
  });

  it('desactivado, consulta más despacio', async () => {
    await mount();
    click(followSwitch());
    const before = executions.mock.calls.length;
    await advance(4100);
    expect(executions.mock.calls.length).toBe(before);
    await advance(6000);
    expect(executions.mock.calls.length).toBe(before + 1);
  });

  it('no consulta con la pestaña del navegador oculta y se pone al día al volver', async () => {
    await mount();
    visibility = 'hidden';
    document.dispatchEvent(new Event('visibilitychange'));
    const before = executions.mock.calls.length;
    await advance(20_000);
    expect(executions.mock.calls.length).toBe(before);
    visibility = 'visible';
    document.dispatchEvent(new Event('visibilitychange'));
    await advance(4100);
    expect(executions.mock.calls.length).toBeGreaterThan(before);
  });

  it('cuando llega una ejecución nueva se elige sola, se ilumina y se reproduce', async () => {
    await mount();
    expect(container.querySelector('.wf-exec')?.textContent).toContain('Ejecución #15');
    all = [at(16, traceSinStock(16)), ...all];
    await advance(4100);
    await settle();
    expect(rowById(16).getAttribute('aria-current')).toBe('true');
    expect(container.querySelector('.wf-exec')?.textContent).toContain('Ejecución #16');
    expect(container.querySelector('.wf-edge--active[data-to="Marcar Sin Stock"]')).toBeNull();
    // arranca reproduciendo su camino: primer paso a la vista
    expect(container.querySelector('.wf-caption')?.textContent).toContain('Paso 1 de 8');
    expect(count('.wf-node--pending')).toBe(7);
  });

  it('la ejecución nueva se marca como novedad en la lista', async () => {
    await mount();
    all = [at(16, traceSinStock(16)), ...all];
    await advance(4100);
    await settle();
    expect(rowById(16).getAttribute('class')).toContain('wf-run--fresh');
    expect(rowById(15).getAttribute('class')).not.toContain('wf-run--fresh');
  });

  it('apagado, una ejecución nueva aparece en la lista pero no cambia lo que se ve', async () => {
    await mount();
    click(followSwitch());
    all = [at(16, traceSinStock(16)), ...all];
    await advance(10_100);
    await settle();
    expect(rowById(16)).toBeDefined();
    expect(rowById(15).getAttribute('aria-current')).toBe('true');
    expect(container.querySelector('.wf-exec')?.textContent).toContain('Ejecución #15');
    expect(container.querySelector('.wf-caption')).toBeNull();
  });

  it('volver a activarlo no salta solo a lo que llegó mientras estaba apagado', async () => {
    await mount();
    click(followSwitch());
    all = [at(16, traceSinStock(16)), ...all];
    await advance(10_100);
    await settle();
    click(followSwitch());
    await settle();
    expect(container.querySelector('.wf-exec')?.textContent).toContain('Ejecución #15');
  });

  it('con el filtro "Con error" solo sigue las ejecuciones con error', async () => {
    await mount();
    await chooseStatus('error');
    all = [at(16, traceSinStock(16)), ...all];
    await advance(4100);
    await settle();
    expect(container.querySelector('.wf-exec')?.textContent).toContain('Ejecución #13');
  });

  it('con movimiento reducido la ejecución nueva se ve completa, sin animar', async () => {
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: query.includes('reduce'),
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }));
    await mount();
    all = [at(16, traceSinStock(16)), ...all];
    await advance(4100);
    await settle();
    expect(container.querySelector('.wf-exec')?.textContent).toContain('Ejecución #16');
    expect(count('.wf-node--pending')).toBe(0);
    expect(container.querySelector('.wf-caption')).toBeNull();
  });
});

describe('Detalle de un nodo', () => {
  const panel = () => container.querySelector<HTMLElement>('.wf-detail');
  const openNode = async (name: string) => {
    act(() => nodeByName(name).dispatchEvent(new MouseEvent('click', { bubbles: true })));
    await settle();
  };

  it('sin nodo elegido no hay panel', async () => {
    await mount();
    expect(panel()).toBeNull();
  });

  it('muestra nombre, tipo, estado, inicio, duración, items y salidas por rama', async () => {
    await mount();
    await openNode('IF Stock Disponible');
    const body = panel()?.textContent ?? '';
    expect(panel()?.querySelector('h3')?.textContent).toBe('IF Stock Disponible');
    expect(body).toContain('Condición');
    expect(body).toContain('Correcto');
    expect(body).toContain('11:03:20');
    expect(body).toContain('1 ms');
    expect(body).toContain('1 ítem');
    expect(body).toContain('Sí: 1 · No: 0');
  });

  it('la salida se muestra SOLO como texto en un bloque monoespaciado', async () => {
    all = [
      at(15, {
        ...traceConStock(15),
        nodes: traceConStock(15).nodes.map((n) =>
          n.name === 'Verificar Stock'
            ? { ...n, output_preview: [{ nota: '<img src=x onerror=alert(1)>', token: '[REDACTADO]' }] }
            : n,
        ),
      }),
    ];
    await mount();
    await openNode('Verificar Stock');
    const pre = panel()?.querySelector('pre.wf-preview');
    expect(pre).not.toBeNull();
    expect(pre?.textContent).toContain('<img src=x onerror=alert(1)>');
    expect(pre?.textContent).toContain('[REDACTADO]');
    expect(panel()?.querySelector('img')).toBeNull();
    expect(pre?.children).toHaveLength(0);
  });

  it('avisa cuando la vista previa está recortada', async () => {
    all = [
      at(15, {
        ...traceConStock(15),
        nodes: traceConStock(15).nodes.map((n) =>
          n.name === 'Verificar Stock' ? { ...n, output_preview: '[{"a":"muy larg…', output_truncated: true } : n,
        ),
      }),
    ];
    await mount();
    await openNode('Verificar Stock');
    expect(panel()?.textContent).toContain('vista previa recortada');
    expect(panel()?.querySelector('pre')?.textContent).toBe('[{"a":"muy larg…');
  });

  it('sin salida registrada lo dice', async () => {
    all = [
      at(15, {
        ...traceConStock(15),
        nodes: traceConStock(15).nodes.map((n) => (n.name === 'Verificar Stock' ? { ...n, output_preview: null } : n)),
      }),
    ];
    await mount();
    await openNode('Verificar Stock');
    expect(panel()?.textContent).toContain('Sin salida registrada');
    expect(panel()?.querySelector('pre')).toBeNull();
  });

  it('un nodo con error muestra el mensaje y la descripción', async () => {
    all = [at(13, traceError(13))];
    await mount();
    await openNode('Registrar Orden');
    const body = panel()?.textContent ?? '';
    expect(body).toContain('Con error');
    expect(body).toContain('Credential does not exist');
    expect(body).toContain('Configurá la credencial de Postgres.');
  });

  it('un nodo que no se ejecutó lo dice y no ofrece salida', async () => {
    await mount();
    await openNode('Marcar Sin Stock');
    expect(panel()?.textContent).toContain('No se ejecutó');
    expect(panel()?.textContent).toContain('no se ejecutó en esta ejecución');
  });

  it('un nodo que la traza no trae lo explica', async () => {
    all = [
      at(15, {
        ...traceConStock(15),
        nodes: traceConStock(15).nodes.filter((n) => n.name !== 'Marcar Sin Stock'),
      }),
    ];
    await mount();
    await openNode('Marcar Sin Stock');
    expect(panel()?.textContent).toContain('no figura en la ejecución');
  });

  it('sin ejecuciones muestra solo lo del nodo y invita a elegir una', async () => {
    all = [];
    await mount();
    await openNode('Verificar Stock');
    expect(panel()?.textContent).toContain('Base de datos');
    expect(panel()?.textContent).toContain('Cuando haya una ejecución');
  });

  it('el nodo elegido se conserva al cambiar de ejecución', async () => {
    await mount();
    await openNode('IF Stock Disponible');
    click(rowById(14));
    await settle();
    expect(panel()?.querySelector('h3')?.textContent).toBe('IF Stock Disponible');
    expect(panel()?.textContent).toContain('Sí: 0 · No: 1');
  });

  it('con Enter abre el detalle y el foco pasa al panel; Escape lo cierra y el foco vuelve al nodo', async () => {
    await mount();
    const node = nodeByName('Verificar Stock');
    node.focus();
    act(() => {
      node.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
    });
    await settle();
    expect(document.activeElement).toBe(panel());
    act(() => {
      panel()?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
    });
    await settle();
    expect(panel()).toBeNull();
    expect(document.activeElement).toBe(nodeByName('Verificar Stock'));
  });

  it('el botón Cerrar lo cierra', async () => {
    await mount();
    await openNode('Verificar Stock');
    click(panel()?.querySelector('button[aria-label="Cerrar detalle"]'));
    await settle();
    expect(panel()).toBeNull();
    expect(nodeByName('Verificar Stock').getAttribute('aria-pressed')).toBe('false');
  });

  it('el panel es una región con nombre accesible', async () => {
    await mount();
    await openNode('Verificar Stock');
    expect(panel()?.getAttribute('role')).toBe('region');
    expect(panel()?.getAttribute('aria-label')).toContain('Verificar Stock');
    expect(panel()?.getAttribute('tabindex')).toBe('-1');
  });
});
