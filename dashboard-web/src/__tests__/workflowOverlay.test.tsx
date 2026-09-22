import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/api/client';
import { monitoringApi } from '@/api/endpoints';
import { BASE_STEP_MS } from '@/lib/playback';
import { FOLLOW_SCALE } from '@/lib/viewport';
import { MonitoreoWorkflowPage } from '@/pages/MonitoreoWorkflowPage';
import type { ExecutionDetail, ExecutionsPage } from '@/types/monitoring';

import { installFakeResizeObserver } from './helpers/fakeResizeObserver';
import {
  CON_STOCK_PATH,
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
const workflows = vi.mocked(monitoringApi.workflows);
const workflowGraph = vi.mocked(monitoringApi.workflowGraph);

let container: HTMLDivElement;
let root: Root;
let details: Record<number, ExecutionDetail>;
let page: ExecutionsPage;

function setExecutions(...items: ExecutionDetail[]) {
  details = Object.fromEntries(items.map((d) => [d.execution.id, d]));
  page = {
    available: true,
    items: items.map((d) => d.execution),
    has_more: false,
    next_before: null,
  };
}

function stubReducedMotion(reduced: boolean) {
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: reduced && query.includes('reduce'),
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
  }));
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date'] });
  vi.setSystemTime(new Date('2026-09-21T14:05:00.000Z'));
  installFakeResizeObserver();
  stubReducedMotion(false);

  setExecutions(traceConStock(15), traceSinStock(14));
  workflows.mockReset().mockResolvedValue({
    available: true,
    items: [makeWorkflowSummary(FLUJO1_ID, flujo1Graph.name)],
  });
  workflowGraph.mockReset().mockResolvedValue(flujo1Graph);
  executions.mockReset().mockImplementation(async () => page);
  execution.mockReset().mockImplementation(async (id: number) => {
    const found = details[id];
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

/** Un paso a la vez: React re-arma el temporizador entre uno y otro, así que no alcanza con adelantar todo junto. */
async function advanceSteps(steps: number) {
  for (let i = 0; i < steps; i += 1) await advance(BASE_STEP_MS);
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
  // workflows -> grafo y ejecuciones -> detalle: cada paso depende del anterior
  for (let i = 0; i < 8; i += 1) await advance(0);
}

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
const activeEdge = (from: string, to: string) =>
  container.querySelector(`.wf-edge--active[data-from="${from}"][data-to="${to}"]`) !== null;

function currentK() {
  const css = (container.querySelector('.wf-viewport') as SVGGElement).style.transform;
  return Number(/scale\(([-\d.e]+)\)/.exec(css)?.[1]);
}

describe('Overlay de la ejecución más reciente', () => {
  it('colorea los nodos por estado: el camino en verde y lo que no corrió, apagado', async () => {
    await mount();
    expect(count('.wf-node--success')).toBe(CON_STOCK_PATH.length);
    expect(count('.wf-node--skipped')).toBe(flujo1Graph.nodes.length - CON_STOCK_PATH.length);
    expect(nodeByName('Verificar Stock').getAttribute('class')).toContain('wf-node--success');
    expect(nodeByName('Marcar Sin Stock').getAttribute('class')).toContain('wf-node--skipped');
  });

  it('cada nodo dice con texto cuánto tardó y cuántos items produjo (no solo con color)', async () => {
    await mount();
    const node = nodeByName('Verificar Stock');
    expect(node.textContent).toContain('3 ms');
    expect(node.textContent).toContain('1 ítem');
    expect(nodeByName('Marcar Sin Stock').textContent).toContain('No se ejecutó');
  });

  it('ilumina el camino recorrido: la rama "Sí" del IF con stock, y no la del "No"', async () => {
    await mount();
    expect(count('.wf-edge--active')).toBe(9);
    expect(activeEdge('IF Stock Disponible', 'Actualizar Stock')).toBe(true);
    expect(activeEdge('IF Stock Disponible', 'Marcar Sin Stock')).toBe(false);
    expect(activeEdge('IF Stock Bajo', 'Confirmar Orden')).toBe(true);
  });

  it('con una ejecución sin stock se ilumina la otra rama', async () => {
    setExecutions(traceSinStock(20), traceConStock(15));
    await mount();
    expect(activeEdge('IF Stock Disponible', 'Marcar Sin Stock')).toBe(true);
    expect(activeEdge('IF Stock Disponible', 'Actualizar Stock')).toBe(false);
    expect(nodeByName('Respuesta Sin Stock').getAttribute('class')).toContain('wf-node--success');
  });

  it('una ejecución con error marca el nodo que falló y su mensaje', async () => {
    setExecutions(traceError(30));
    await mount();
    const failed = nodeByName('Registrar Orden');
    expect(failed.getAttribute('class')).toContain('wf-node--error');
    expect(failed.textContent).toContain('Con error');
    expect(failed.getAttribute('aria-label')).toContain('Con error');
    expect(count('.wf-edge--active')).toBe(1);
    expect(text()).toContain('does not exist for type');
  });

  it('el encabezado dice qué ejecución se está viendo', async () => {
    await mount();
    const header = container.querySelector('.wf-exec')?.textContent ?? '';
    expect(header).toContain('Ejecución #15');
    expect(header).toContain('Correcta');
    expect(header).toContain('435 ms');
    expect(header).toContain('Entrada de datos');
  });

  it('pide el detalle solo de la ejecución que se ve', async () => {
    await mount();
    expect(execution).toHaveBeenCalledTimes(1);
    expect(execution).toHaveBeenCalledWith(15);
  });

  it('pide las ejecuciones del workflow elegido', async () => {
    await mount();
    expect(executions).toHaveBeenCalledWith(expect.objectContaining({ workflowId: FLUJO1_ID }));
  });
});

describe('Sin ejecuciones o con problemas', () => {
  it('sin ejecuciones, el diagrama se ve sin pintar y lo explica', async () => {
    setExecutions();
    await mount();
    expect(count('.wf-node--plain')).toBe(flujo1Graph.nodes.length);
    expect(text()).toContain('Todavía no hay ejecuciones');
    expect(buttonByText('Reproducir camino')?.disabled).toBe(true);
    expect(execution).not.toHaveBeenCalled();
  });

  it('mientras llega el detalle avisa y el diagrama sigue visible', async () => {
    execution.mockReturnValue(new Promise<ExecutionDetail>(() => {}));
    await mount();
    expect(text()).toContain('Cargando el recorrido');
    expect(nodes()).toHaveLength(flujo1Graph.nodes.length);
  });

  it('si falla el detalle: aviso con Reintentar', async () => {
    execution.mockRejectedValueOnce(new ApiError(500, 'boom'));
    await mount();
    expect(container.querySelector('.wf-notice[role="alert"]')?.textContent).toContain('No pudimos cargar');
    await act(async () => buttonByText('Reintentar')?.click());
    await advance(0);
    await advance(0);
    expect(execution).toHaveBeenCalledTimes(2);
    expect(count('.wf-node--success')).toBe(CON_STOCK_PATH.length);
  });

  it('si fallan las ejecuciones: aviso con Reintentar y el diagrama sigue', async () => {
    executions.mockRejectedValueOnce(new ApiError(500, 'boom'));
    await mount();
    expect(container.querySelector('.wf-notice[role="alert"]')?.textContent).toContain('ejecuciones');
    expect(nodes()).toHaveLength(flujo1Graph.nodes.length);
  });

  it('una ejecución sin datos de traza no rompe: dice por qué y no pinta nada', async () => {
    const purged = {
      ...traceConStock(15),
      nodes: [],
      path: [],
      last_node_executed: null,
      error: 'La ejecución no tiene datos de traza (¿fueron purgados?)',
    };
    setExecutions(purged);
    await mount();
    expect(text()).toContain('No se pudo mostrar el detalle');
    expect(text()).toContain('purgados');
    expect(count('.wf-node--plain')).toBe(flujo1Graph.nodes.length);
    expect(buttonByText('Reproducir camino')?.disabled).toBe(true);
  });

  it('una ejecución truncada lo avisa', async () => {
    setExecutions({ ...traceConStock(15), nodes: [], path: [], truncated: true });
    await mount();
    expect(text()).toContain('demasiado grande');
  });

  it('nodos que faltan en la traza y nodos que ya no existen: los dice y los lista aparte', async () => {
    const detail = traceConStock(15);
    detail.nodes = detail.nodes.filter((n) => n.name !== 'Marcar Sin Stock');
    detail.nodes.push({ ...detail.nodes[0], name: 'Nodo Viejo <b>x</b>', short_type: null });
    setExecutions(detail);
    await mount();
    const notices = container.querySelector('.wf-notices')?.textContent ?? '';
    expect(notices).toContain('1 nodo del diagrama no figura');
    expect(notices).toContain('Marcar Sin Stock');
    expect(notices).toContain('Nodo Viejo <b>x</b>');
    expect(container.querySelector('.wf-notices b')).toBeNull();
    expect(nodeByName('Marcar Sin Stock').getAttribute('class')).toContain('wf-node--missing');
  });
});

describe('Reproducir camino', () => {
  it('arranca en reposo con el resultado final a la vista', async () => {
    await mount();
    expect(count('.wf-node--pending')).toBe(0);
    expect(container.querySelector('.wf-caption')).toBeNull();
    expect(buttonByText('Reproducir camino')?.disabled).toBe(false);
  });

  it('reproduce nodo por nodo en el orden del camino', async () => {
    await mount();
    click(buttonByText('Reproducir camino'));
    // primer nodo encendido; el resto del camino, todavía apagado; lo que no corrió sigue "no se ejecutó"
    expect(count('.wf-node--success')).toBe(1);
    expect(count('.wf-node--pending')).toBe(CON_STOCK_PATH.length - 1);
    expect(nodeByName(CON_STOCK_PATH[0]).getAttribute('class')).toContain('wf-node--success');
    expect(nodeByName(CON_STOCK_PATH[0]).getAttribute('class')).toContain('wf-node--current');
    expect(container.querySelector('.wf-caption')?.textContent).toContain('Paso 1 de 10');
    expect(container.querySelector('.wf-caption')?.textContent).toContain(CON_STOCK_PATH[0]);
    expect(count('.wf-edge--active')).toBe(0);

    await advance(BASE_STEP_MS);
    expect(count('.wf-node--success')).toBe(2);
    expect(count('.wf-edge--active')).toBe(1);
    expect(count('.wf-edge--flowing')).toBe(1);
    expect(nodeByName(CON_STOCK_PATH[1]).getAttribute('class')).toContain('wf-node--current');
    expect(container.querySelector('.wf-caption')?.textContent).toContain('Paso 2 de 10');

    await advance(BASE_STEP_MS);
    expect(count('.wf-node--success')).toBe(3);
  });

  it('al terminar vuelve al reposo con todo el camino iluminado', async () => {
    await mount();
    click(buttonByText('Reproducir camino'));
    await advanceSteps(CON_STOCK_PATH.length);
    expect(count('.wf-node--pending')).toBe(0);
    expect(count('.wf-node--success')).toBe(CON_STOCK_PATH.length);
    expect(count('.wf-edge--active')).toBe(9);
    expect(container.querySelector('.wf-caption')).toBeNull();
    expect(buttonByText('Reproducir camino')).toBeDefined();
  });

  it('pausar congela el paso; continuar sigue desde ahí', async () => {
    await mount();
    click(buttonByText('Reproducir camino'));
    await advance(BASE_STEP_MS);
    click(buttonByText('Pausar'));
    expect(container.querySelector('.wf-caption')?.textContent).toContain('en pausa');
    await advance(BASE_STEP_MS * 5);
    expect(count('.wf-node--success')).toBe(2);
    click(buttonByText('Continuar'));
    await advance(BASE_STEP_MS);
    expect(count('.wf-node--success')).toBe(3);
  });

  it('la velocidad cambia el ritmo: 2× va al doble y 0,5× a la mitad', async () => {
    await mount();
    click(buttonByText('2×'));
    expect(buttonByText('2×')?.getAttribute('aria-pressed')).toBe('true');
    expect(buttonByText('1×')?.getAttribute('aria-pressed')).toBe('false');
    click(buttonByText('Reproducir camino'));
    await advance(BASE_STEP_MS / 2);
    expect(count('.wf-node--success')).toBe(2);
    click(buttonByText('Pausar'));
    click(buttonByText('0,5×'));
    click(buttonByText('Continuar'));
    await advance(BASE_STEP_MS);
    expect(count('.wf-node--success')).toBe(2);
    await advance(BASE_STEP_MS);
    expect(count('.wf-node--success')).toBe(3);
  });

  it('reiniciar vuelve al primer nodo', async () => {
    await mount();
    click(buttonByText('Reproducir camino'));
    await advanceSteps(3);
    expect(count('.wf-node--success')).toBe(4);
    click(buttonByText('Reiniciar'));
    expect(count('.wf-node--success')).toBe(1);
    expect(container.querySelector('.wf-caption')?.textContent).toContain('Paso 1 de 10');
  });

  it('"Ver resultado final" salta al final', async () => {
    await mount();
    click(buttonByText('Reproducir camino'));
    await advance(BASE_STEP_MS);
    click(buttonByText('Ver resultado final'));
    expect(count('.wf-node--success')).toBe(CON_STOCK_PATH.length);
    expect(container.querySelector('.wf-caption')).toBeNull();
  });

  it('con movimiento reducido no anima: reproducir muestra el resultado final y lo explica', async () => {
    stubReducedMotion(true);
    await mount();
    expect(text()).toContain('menos movimiento');
    click(buttonByText('Reproducir camino'));
    expect(count('.wf-node--pending')).toBe(0);
    expect(count('.wf-node--success')).toBe(CON_STOCK_PATH.length);
    expect(container.querySelector('.wf-caption')).toBeNull();
  });
});

describe('Cámara durante la reproducción', () => {
  it('"Seguir con la cámara" viene activada y se puede apagar', async () => {
    await mount();
    const toggle = buttonByText('Seguir con la cámara');
    expect(toggle?.getAttribute('aria-pressed')).toBe('true');
    click(toggle);
    expect(toggle?.getAttribute('aria-pressed')).toBe('false');
  });

  it('acerca hasta un tamaño legible para seguir el nodo y, al terminar, vuelve a mostrar todo', async () => {
    await mount();
    const overview = currentK();
    expect(overview).toBeLessThan(FOLLOW_SCALE);
    click(buttonByText('Reproducir camino'));
    expect(currentK()).toBeGreaterThanOrEqual(FOLLOW_SCALE);
    await advanceSteps(CON_STOCK_PATH.length);
    expect(currentK()).toBeCloseTo(overview, 3);
  });

  it('con la cámara apagada el diagrama no se mueve', async () => {
    await mount();
    const overview = currentK();
    click(buttonByText('Seguir con la cámara'));
    click(buttonByText('Reproducir camino'));
    await advanceSteps(3);
    expect(count('.wf-node--success')).toBe(4);
    expect(currentK()).toBeCloseTo(overview, 5);
  });
});

describe('Ejecución en curso', () => {
  it('sigue pidiendo el detalle mientras no termine', async () => {
    const running = traceConStock(40);
    running.execution = makeExecution(40, { status: 'running', stopped_at: null, duration_ms: null });
    setExecutions(running);
    await mount();
    expect(execution).toHaveBeenCalledTimes(1);
    await advance(2100);
    expect(execution.mock.calls.length).toBeGreaterThan(1);
    expect(container.querySelector('.wf-exec')?.textContent).toContain('En curso');
  });
});
