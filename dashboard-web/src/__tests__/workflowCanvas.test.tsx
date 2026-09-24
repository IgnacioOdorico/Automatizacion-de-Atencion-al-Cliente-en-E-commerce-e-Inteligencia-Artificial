import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { WorkflowCanvas } from '@/components/workflow/WorkflowCanvas';
import { ZOOM_STEP, fitView, initialView } from '@/lib/viewport';
import { buildOverlay } from '@/lib/workflowTrace';
import { layoutGraph } from '@/lib/workflowGraph';
import type { WorkflowGraph } from '@/types/monitoring';

import { flujo1Graph, flujo2Graph } from './helpers/workflowFixtures';

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// ---------- entorno: jsdom no mide nada, así que el tamaño del lienzo lo da un ResizeObserver de mentira ----------

type Callback = (entries: Array<{ target: Element; contentRect: { width: number; height: number } }>) => void;
let observers: Array<{ cb: Callback; el: Element | null }> = [];
let canvasSize = { width: 900, height: 400 };

class FakeResizeObserver {
  private entry: { cb: Callback; el: Element | null };
  constructor(cb: Callback) {
    this.entry = { cb, el: null };
    observers.push(this.entry);
  }
  observe(el: Element) {
    this.entry.el = el;
    this.entry.cb([{ target: el, contentRect: { ...canvasSize } }]);
  }
  unobserve() {}
  disconnect() {
    observers = observers.filter((o) => o !== this.entry);
  }
}

function resizeTo(width: number, height: number) {
  canvasSize = { width, height };
  act(() => {
    for (const o of observers) if (o.el) o.cb([{ target: o.el, contentRect: { width, height } }]);
  });
}

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  observers = [];
  canvasSize = { width: 900, height: 400 };
  vi.stubGlobal('ResizeObserver', FakeResizeObserver);
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});

function mount(
  graph: WorkflowGraph = flujo1Graph,
  extra: Partial<Parameters<typeof WorkflowCanvas>[0]> = {},
) {
  const layout = layoutGraph(graph);
  const props = {
    title: graph.name,
    layout,
    overlay: buildOverlay(graph, null),
    selected: null,
    onSelect: vi.fn(),
    resetKey: graph.id,
    ...extra,
  };
  act(() => root.render(<WorkflowCanvas {...props} />));
  return { layout, props };
}

const canvas = () => container.querySelector<HTMLElement>('.wf-canvas') as HTMLElement;
const viewport = () => container.querySelector('.wf-viewport') as SVGGElement;
const nodes = () => Array.from(container.querySelectorAll<SVGGElement>('.wf-node'));
const nodeByName = (name: string) => nodes().find((n) => n.getAttribute('data-node') === name) as SVGGElement;
const button = (label: string) =>
  Array.from(container.querySelectorAll<HTMLButtonElement>('button')).find((b) => b.getAttribute('aria-label') === label) as HTMLButtonElement;

/** Lee `translate(xpx, ypx) scale(k)` del grupo que se mueve. */
function currentView() {
  const css = viewport().style.transform;
  const match = /translate\(([-\d.e]+)px, ([-\d.e]+)px\) scale\(([-\d.e]+)\)/.exec(css);
  if (!match) throw new Error(`transform inesperado: ${css}`);
  return { x: Number(match[1]), y: Number(match[2]), k: Number(match[3]) };
}

/** jsdom no tiene PointerEvent: un MouseEvent con `pointerId` alcanza para React. */
function pointer(type: string, target: Element, id: number, x: number, y: number, init: MouseEventInit = {}) {
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, ...init });
  Object.defineProperty(event, 'pointerId', { value: id });
  Object.defineProperty(event, 'pointerType', { value: 'mouse' });
  act(() => {
    target.dispatchEvent(event);
  });
}

const key = (target: Element, k: string) => {
  const event = new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true });
  act(() => {
    target.dispatchEvent(event);
  });
  return event;
};

describe('WorkflowCanvas: dibujo', () => {
  it('dibuja una tarjeta enfocable por nodo y una conexión por arista', () => {
    mount();
    expect(nodes()).toHaveLength(flujo1Graph.nodes.length);
    for (const node of nodes()) {
      expect(node.getAttribute('role')).toBe('button');
      expect(node.getAttribute('tabindex')).toBe('0');
    }
    expect(container.querySelectorAll('.wf-edge')).toHaveLength(flujo1Graph.edges.length);
  });

  it('cada nodo muestra su nombre tal cual (ya viene en español)', () => {
    mount();
    const text = canvas().textContent ?? '';
    expect(text).toContain('Webhook');
    expect(nodeByName('Enviar Email Confirmación').textContent).toContain('Enviar Email');
    expect(nodeByName('Enviar Email Confirmación').textContent).toContain('Confirmación');
  });

  it('cada nodo tiene un nombre accesible con su tipo y sin jerga', () => {
    mount();
    const label = nodeByName('Verificar Stock').getAttribute('aria-label') ?? '';
    expect(label).toContain('Verificar Stock');
    expect(label).toContain('Base de datos');
  });

  it('los nodos IF rotulan sus ramas con "Sí" y "No"', () => {
    mount();
    const labels = Array.from(container.querySelectorAll('.wf-elabel')).map((l) => l.textContent);
    expect(labels).toEqual(expect.arrayContaining(['Sí', 'No']));
  });

  it('el Flujo 2 rotula las salidas del Switch y dibuja la conexión de IA punteada', () => {
    mount(flujo2Graph);
    const labels = Array.from(container.querySelectorAll('.wf-elabel')).map((l) => l.textContent);
    expect(labels).toEqual(expect.arrayContaining(['Salida 1', 'Salida 4']));
    expect(container.querySelectorAll('.wf-edge--ai')).toHaveLength(1);
  });

  it('un nodo deshabilitado se atenúa y lo dice con texto', () => {
    const graph: WorkflowGraph = {
      ...flujo1Graph,
      nodes: flujo1Graph.nodes.map((n) => (n.name === 'Marcar Sin Stock' ? { ...n, disabled: true } : n)),
    };
    mount(graph);
    const node = nodeByName('Marcar Sin Stock');
    expect(node.getAttribute('class')).toContain('wf-node--disabled');
    expect(node.textContent).toContain('Deshabilitado');
    expect(node.getAttribute('aria-label')).toContain('deshabilitado');
  });

  it('un nombre con HTML se muestra como texto, nunca se interpreta', () => {
    const graph: WorkflowGraph = {
      ...flujo1Graph,
      nodes: flujo1Graph.nodes.map((n, i) => (i === 0 ? { ...n, name: '<img src=x onerror=alert(1)>' } : n)),
      edges: [],
    };
    mount(graph);
    expect(container.querySelector('img')).toBeNull();
    expect(canvas().textContent).toContain('<img');
  });

  it('el diagrama tiene título y descripción para lectores de pantalla', () => {
    mount();
    const svg = container.querySelector('svg.wf-svg') as SVGSVGElement;
    expect(svg.getAttribute('role')).toBe('group');
    const title = svg.querySelector('title');
    expect(title?.textContent).toBe(flujo1Graph.name);
    expect(svg.getAttribute('aria-labelledby')).toBe(title?.id);
    expect(svg.querySelector('desc')?.textContent).toContain(`${flujo1Graph.nodes.length} nodos`);
  });
});

describe('WorkflowCanvas: ajustar a pantalla', () => {
  it('arranca ajustado al lienzo', () => {
    const { layout } = mount();
    const expected = initialView(layout.bounds, canvasSize);
    const view = currentView();
    expect(view.k).toBeCloseTo(expected.k, 3);
    expect(view.x).toBeCloseTo(expected.x, 1);
    expect(view.y).toBeCloseTo(expected.y, 1);
  });

  it('si cambia el tamaño y no se tocó la vista, se vuelve a ajustar', () => {
    const { layout } = mount();
    resizeTo(500, 300);
    const expected = initialView(layout.bounds, { width: 500, height: 300 });
    expect(currentView().k).toBeCloseTo(expected.k, 3);
  });

  it('si el usuario ya movió la vista, un cambio de tamaño no se la pisa', () => {
    mount();
    act(() => button('Acercar').click());
    const zoomed = currentView();
    resizeTo(500, 300);
    expect(currentView()).toEqual(zoomed);
  });

  it('cambiar de workflow (resetKey) ajusta de nuevo aunque el usuario haya movido la vista', () => {
    const first = mount();
    act(() => button('Acercar').click());
    const second = layoutGraph(flujo2Graph);
    act(() =>
      root.render(
        <WorkflowCanvas
          title={flujo2Graph.name}
          layout={second}
          overlay={buildOverlay(flujo2Graph, null)}
          selected={null}
          onSelect={first.props.onSelect}
          resetKey={flujo2Graph.id}
        />,
      ),
    );
    expect(currentView().k).toBeCloseTo(fitView(second.bounds, canvasSize).k, 3);
  });
});

describe('WorkflowCanvas: botones de zoom', () => {
  it('Acercar y Alejar cambian la escala en un paso, alrededor del centro', () => {
    mount();
    const start = currentView();
    act(() => button('Acercar').click());
    expect(currentView().k).toBeCloseTo(start.k * ZOOM_STEP, 3);
    act(() => button('Alejar').click());
    act(() => button('Alejar').click());
    expect(currentView().k).toBeCloseTo(start.k / ZOOM_STEP, 3);
  });

  it('"Ajustar a pantalla" vuelve a la vista inicial', () => {
    mount();
    const start = currentView();
    act(() => button('Acercar').click());
    act(() => button('Acercar').click());
    act(() => button('Ajustar a pantalla').click());
    const back = currentView();
    expect(back.k).toBeCloseTo(start.k, 3);
    expect(back.x).toBeCloseTo(start.x, 1);
  });

  it('muestra el nivel de zoom en porcentaje', () => {
    mount();
    const percent = container.querySelector('.wf-zoom__level')?.textContent ?? '';
    expect(percent).toMatch(/^\d+ ?%$/);
  });
});

describe('WorkflowCanvas: teclado', () => {
  it('el lienzo se puede enfocar y tiene instrucciones', () => {
    mount();
    expect(canvas().getAttribute('tabindex')).toBe('0');
    const described = canvas().getAttribute('aria-describedby');
    expect(described && document.getElementById(described)?.textContent).toContain('flechas');
  });

  it('+ y - hacen zoom, las flechas mueven y 0 ajusta', () => {
    mount();
    const start = currentView();
    key(canvas(), '+');
    expect(currentView().k).toBeGreaterThan(start.k);
    key(canvas(), '-');
    key(canvas(), '-');
    expect(currentView().k).toBeLessThan(start.k);
    const before = currentView();
    key(canvas(), 'ArrowRight');
    expect(currentView().x).toBeLessThan(before.x);
    key(canvas(), 'ArrowDown');
    expect(currentView().y).toBeLessThan(before.y);
    key(canvas(), '0');
    expect(currentView().k).toBeCloseTo(start.k, 3);
  });

  it('desde un nodo enfocado las teclas también mueven la vista (el evento sube)', () => {
    mount();
    const before = currentView();
    key(nodeByName('Verificar Stock'), 'ArrowLeft');
    expect(currentView().x).toBeGreaterThan(before.x);
  });

  it('las teclas manejadas no scrollean la página', () => {
    mount();
    expect(key(canvas(), 'ArrowDown').defaultPrevented).toBe(true);
    expect(key(canvas(), 'a').defaultPrevented).toBe(false);
  });

  it('Enter y Espacio sobre un nodo lo eligen', () => {
    const { props } = mount();
    key(nodeByName('Registrar Orden'), 'Enter');
    expect(props.onSelect).toHaveBeenLastCalledWith('Registrar Orden');
    key(nodeByName('Verificar Stock'), ' ');
    expect(props.onSelect).toHaveBeenLastCalledWith('Verificar Stock');
  });

  it('las teclas de los botones de zoom no mueven el diagrama', () => {
    mount();
    const before = currentView();
    key(button('Acercar'), 'ArrowRight');
    expect(currentView()).toEqual(before);
  });
});

describe('WorkflowCanvas: mouse y rueda', () => {
  const wheel = (init: WheelEventInit) => {
    const event = new WheelEvent('wheel', { bubbles: true, cancelable: true, ...init });
    act(() => {
      canvas().dispatchEvent(event);
    });
    return event;
  };

  it('Ctrl + rueda hace zoom y no scrollea la página', () => {
    mount();
    const start = currentView();
    const event = wheel({ deltaY: -120, ctrlKey: true, clientX: 100, clientY: 100 });
    expect(event.defaultPrevented).toBe(true);
    expect(currentView().k).toBeGreaterThan(start.k);
  });

  it('la rueda sola no toca el diagrama y deja scrollear la página', () => {
    mount();
    const start = currentView();
    const event = wheel({ deltaY: 120 });
    expect(event.defaultPrevented).toBe(false);
    expect(currentView()).toEqual(start);
  });

  it('arrastrar mueve el diagrama la distancia que se movió el mouse', () => {
    mount();
    const start = currentView();
    pointer('pointerdown', canvas(), 1, 100, 100);
    pointer('pointermove', canvas(), 1, 140, 130);
    pointer('pointermove', canvas(), 1, 160, 150);
    pointer('pointerup', canvas(), 1, 160, 150);
    const end = currentView();
    expect(end.x - start.x).toBeCloseTo(60, 1);
    expect(end.y - start.y).toBeCloseTo(50, 1);
    expect(end.k).toBeCloseTo(start.k, 5);
  });

  it('un temblor de menos de unos píxeles no es un arrastre', () => {
    mount();
    const start = currentView();
    pointer('pointerdown', canvas(), 1, 100, 100);
    pointer('pointermove', canvas(), 1, 102, 101);
    pointer('pointerup', canvas(), 1, 102, 101);
    expect(currentView()).toEqual(start);
  });

  it('un clic en un nodo lo elige', () => {
    const { props } = mount();
    act(() => nodeByName('Actualizar Stock').dispatchEvent(new MouseEvent('click', { bubbles: true })));
    expect(props.onSelect).toHaveBeenCalledWith('Actualizar Stock');
  });

  it('dos dedos: separarlos hace zoom', () => {
    mount();
    const start = currentView();
    pointer('pointerdown', canvas(), 1, 300, 200);
    pointer('pointerdown', canvas(), 2, 400, 200);
    pointer('pointermove', canvas(), 2, 500, 200);
    expect(currentView().k).toBeGreaterThan(start.k);
    pointer('pointerup', canvas(), 2, 500, 200);
    pointer('pointerup', canvas(), 1, 300, 200);
  });
});

describe('WorkflowCanvas: selección', () => {
  it('el nodo elegido queda marcado (aria-pressed y clase)', () => {
    mount(flujo1Graph, { selected: 'Verificar Stock' });
    const node = nodeByName('Verificar Stock');
    expect(node.getAttribute('aria-pressed')).toBe('true');
    expect(node.getAttribute('class')).toContain('wf-node--selected');
    expect(nodeByName('Registrar Orden').getAttribute('aria-pressed')).toBe('false');
  });
});
