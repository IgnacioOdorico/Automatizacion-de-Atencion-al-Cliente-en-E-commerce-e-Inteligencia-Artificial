import { describe, expect, it } from 'vitest';

import {
  CARD_H,
  CARD_W,
  branchLabel,
  cubicPoint,
  edgeKey,
  layoutGraph,
  relieveOverlaps,
  wrapLabel,
  type Box,
} from '@/lib/workflowGraph';
import type { WorkflowGraph } from '@/types/monitoring';

import { flujo1Graph, flujo2Graph } from './helpers/workflowFixtures';

function tinyGraph(overrides: Partial<WorkflowGraph> = {}): WorkflowGraph {
  return {
    id: 'w',
    name: 'Mini',
    active: true,
    nodes: [
      { name: 'A', type: 'n8n-nodes-base.webhook', short_type: 'webhook', position: [-240, 100], disabled: false },
      { name: 'B', type: 'n8n-nodes-base.postgres', short_type: 'postgres', position: [240, 100], disabled: false },
    ],
    edges: [{ from: 'A', to: 'B', output_index: 0, input_index: 0, kind: 'main' }],
    bounds: { min_x: -240, min_y: 100, max_x: 240, max_y: 100 },
    ...overrides,
  };
}

const overlaps = (a: Box, b: Box, gap = 0) =>
  a.x < b.x + b.w + gap && b.x < a.x + a.w + gap && a.y < b.y + b.h + gap && b.y < a.y + a.h + gap;

describe('layoutGraph: posiciones', () => {
  it('lleva las coordenadas de n8n al origen y las escala, sin perder el orden de izquierda a derecha', () => {
    const layout = layoutGraph(tinyGraph());
    const [a, b] = layout.nodes;
    expect(a.x).toBe(0);
    expect(a.y).toBe(0);
    expect(b.x).toBeGreaterThan(a.x + a.w);
    expect(b.y).toBe(0);
    expect(a.w).toBe(CARD_W);
    expect(a.h).toBe(CARD_H);
  });

  it('los límites contienen todas las tarjetas', () => {
    const layout = layoutGraph(flujo1Graph);
    for (const n of layout.nodes) {
      expect(n.x).toBeGreaterThanOrEqual(layout.bounds.minX);
      expect(n.y).toBeGreaterThanOrEqual(layout.bounds.minY);
      expect(n.x + n.w).toBeLessThanOrEqual(layout.bounds.maxX);
      expect(n.y + n.h).toBeLessThanOrEqual(layout.bounds.maxY);
    }
  });

  it('un grafo sin nodos da límites vacíos y sin romper', () => {
    const layout = layoutGraph(tinyGraph({ nodes: [], edges: [] }));
    expect(layout.nodes).toEqual([]);
    expect(layout.edges).toEqual([]);
    expect(layout.bounds).toEqual({ minX: 0, minY: 0, maxX: 0, maxY: 0 });
  });

  it('conserva el nombre, el tipo y si está deshabilitado', () => {
    const graph = tinyGraph();
    graph.nodes[1] = { ...graph.nodes[1], disabled: true };
    const [a, b] = layoutGraph(graph).nodes;
    expect([a.name, a.shortType, a.disabled]).toEqual(['A', 'webhook', false]);
    expect([b.name, b.shortType, b.disabled]).toEqual(['B', 'postgres', true]);
  });

  it.each([
    ['Flujo 1', flujo1Graph],
    ['Flujo 2', flujo2Graph],
  ])('ninguna tarjeta se pisa con otra en el %s real', (_name, graph) => {
    const { nodes } = layoutGraph(graph);
    expect(nodes.length).toBe(graph.nodes.length);
    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        expect(overlaps(nodes[i], nodes[j], 8), `${nodes[i].name} / ${nodes[j].name}`).toBe(false);
      }
    }
  });
});

describe('relieveOverlaps (separar tarjetas que se pisan)', () => {
  const box = (x: number, y: number): Box => ({ x, y, w: 100, h: 50 });

  it('deja como están las que no se tocan', () => {
    const input = [box(0, 0), box(200, 0), box(0, 200)];
    expect(relieveOverlaps(input, 10)).toEqual(input);
  });

  it('baja la más de abajo por debajo de la que pisa, con el margen', () => {
    const out = relieveOverlaps([box(0, 0), box(30, 20)], 10);
    expect(out[0]).toEqual(box(0, 0));
    expect(out[1].y).toBe(60);
    expect(out[1].x).toBe(30);
  });

  it('conserva el orden de entrada aunque las procese de arriba hacia abajo', () => {
    const out = relieveOverlaps([box(30, 20), box(0, 0)], 10);
    expect(out[1]).toEqual(box(0, 0));
    expect(out[0].y).toBe(60);
  });

  it('resuelve una cadena de choques', () => {
    const out = relieveOverlaps([box(0, 0), box(10, 10), box(20, 20)], 10);
    for (let i = 0; i < out.length; i += 1) {
      for (let j = i + 1; j < out.length; j += 1) expect(overlaps(out[i], out[j], 10)).toBe(false);
    }
  });

  it('no muta la entrada', () => {
    const input = [box(0, 0), box(30, 20)];
    relieveOverlaps(input, 10);
    expect(input[1]).toEqual(box(30, 20));
  });
});

describe('layoutGraph: aristas', () => {
  it('una conexión hacia la derecha sale del costado derecho y entra por el izquierdo', () => {
    const layout = layoutGraph(tinyGraph());
    const [a, b] = layout.nodes;
    const [edge] = layout.edges;
    expect(edge.start).toEqual({ x: a.x + a.w, y: a.y + a.h / 2 });
    expect(edge.end).toEqual({ x: b.x, y: b.y + b.h / 2 });
    expect(edge.d.startsWith(`M ${edge.start.x} ${edge.start.y} C `)).toBe(true);
    expect(edge.d.endsWith(`${edge.end.x} ${edge.end.y}`)).toBe(true);
  });

  it('ignora las conexiones que apuntan a un nodo que no está', () => {
    const graph = tinyGraph({
      edges: [
        { from: 'A', to: 'B', output_index: 0, input_index: 0, kind: 'main' },
        { from: 'A', to: 'Fantasma', output_index: 0, input_index: 0, kind: 'main' },
      ],
    });
    expect(layoutGraph(graph).edges).toHaveLength(1);
  });

  it('cada arista tiene una clave única, aunque dos salgan de la misma rama a destinos distintos', () => {
    const layout = layoutGraph(flujo2Graph);
    const keys = layout.edges.map((e) => e.key);
    expect(new Set(keys).size).toBe(keys.length);
    expect(layout.edges).toHaveLength(flujo2Graph.edges.length);
  });

  it('edgeKey distingue rama, destino y tipo', () => {
    const base = { from: 'A', to: 'B', output_index: 0, input_index: 0, kind: 'main' };
    expect(edgeKey(base)).not.toBe(edgeKey({ ...base, output_index: 1 }));
    expect(edgeKey(base)).not.toBe(edgeKey({ ...base, to: 'C' }));
    expect(edgeKey(base)).not.toBe(edgeKey({ ...base, kind: 'ai_tool' }));
  });

  it('un nodo de IA se une al nodo que lo usa por abajo (sub-nodo debajo, de arriba a abajo)', () => {
    const layout = layoutGraph(flujo2Graph);
    const ai = layout.edges.find((e) => e.kind === 'ai_languageModel');
    expect(ai).toBeDefined();
    const from = layout.nodes.find((n) => n.name === 'OpenAI Chat Model');
    const to = layout.nodes.find((n) => n.name === 'IA - Motor Decision');
    if (!ai || !from || !to) throw new Error('faltan nodos');
    expect(from.y).toBeGreaterThan(to.y);
    expect(ai.start.y).toBe(from.y);
    expect(ai.end.y).toBe(to.y + to.h);
    expect(ai.start.x).toBeCloseTo(from.x + from.w / 2);
    expect(ai.end.x).toBeCloseTo(to.x + to.w / 2);
  });

  it('si el destino queda debajo y no a la derecha, la conexión baja de costado a costado', () => {
    const graph = tinyGraph({
      nodes: [
        { name: 'A', type: 'x', short_type: 'code', position: [0, 0], disabled: false },
        { name: 'B', type: 'x', short_type: 'code', position: [0, 300], disabled: false },
      ],
    });
    const layout = layoutGraph(graph);
    const [a, b] = layout.nodes;
    const [edge] = layout.edges;
    expect(edge.start).toEqual({ x: a.x + a.w / 2, y: a.y + a.h });
    expect(edge.end).toEqual({ x: b.x + b.w / 2, y: b.y });
  });

  it('una conexión hacia atrás (destino a la izquierda y a la misma altura) sigue teniendo camino válido', () => {
    const graph = tinyGraph({
      nodes: [
        { name: 'A', type: 'x', short_type: 'code', position: [400, 0], disabled: false },
        { name: 'B', type: 'x', short_type: 'code', position: [0, 0], disabled: false },
      ],
      edges: [{ from: 'A', to: 'B', output_index: 0, input_index: 0, kind: 'main' }],
    });
    const [edge] = layoutGraph(graph).edges;
    expect(edge.d).toMatch(/^M [\d.-]+ [\d.-]+ C /);
    expect(edge.d).not.toContain('NaN');
  });

  it('ningún camino tiene NaN en el Flujo 1 ni en el Flujo 2 reales', () => {
    for (const graph of [flujo1Graph, flujo2Graph]) {
      for (const edge of layoutGraph(graph).edges) expect(edge.d).not.toContain('NaN');
    }
  });
});

describe('etiquetas de rama', () => {
  it('en un IF, la salida 0 es "Sí" y la 1 es "No"', () => {
    expect(branchLabel('if', 0)).toBe('Sí');
    expect(branchLabel('if', 1)).toBe('No');
  });

  it('en un Switch, cada salida es su número (empieza en 1)', () => {
    expect(branchLabel('switch', 0)).toBe('Salida 1');
    expect(branchLabel('switch', 3)).toBe('Salida 4');
  });

  it('el resto de los nodos no rotula', () => {
    expect(branchLabel('postgres', 0)).toBeNull();
    expect(branchLabel(null, 0)).toBeNull();
  });

  it('las aristas que salen de un IF llevan su rótulo, cerca del origen y dentro del tramo', () => {
    const layout = layoutGraph(flujo1Graph);
    const si = layout.edges.find((e) => e.from === 'IF Stock Disponible' && e.outputIndex === 0);
    const no = layout.edges.find((e) => e.from === 'IF Stock Disponible' && e.outputIndex === 1);
    expect(si?.label).toBe('Sí');
    expect(no?.label).toBe('No');
    if (!si) throw new Error('falta la arista');
    const minX = Math.min(si.start.x, si.end.x);
    const maxX = Math.max(si.start.x, si.end.x);
    expect(si.labelX).toBeGreaterThanOrEqual(minX);
    expect(si.labelX).toBeLessThanOrEqual(maxX);
    expect(Math.abs(si.labelX - si.start.x)).toBeLessThan(Math.abs(si.labelX - si.end.x));
  });

  it('una conexión de un nodo común no lleva rótulo', () => {
    const layout = layoutGraph(flujo1Graph);
    expect(layout.edges.find((e) => e.from === 'Registrar Orden')?.label).toBeNull();
  });

  it('las conexiones de IA tampoco', () => {
    const layout = layoutGraph(flujo2Graph);
    expect(layout.edges.find((e) => e.kind === 'ai_languageModel')?.label).toBeNull();
  });
});

describe('cubicPoint', () => {
  const p = (x: number, y: number) => ({ x, y });
  it('en los extremos da el inicio y el fin', () => {
    expect(cubicPoint(p(0, 0), p(10, 0), p(20, 10), p(30, 10), 0)).toEqual(p(0, 0));
    expect(cubicPoint(p(0, 0), p(10, 0), p(20, 10), p(30, 10), 1)).toEqual(p(30, 10));
  });

  it('en la mitad de una recta da el punto medio', () => {
    const mid = cubicPoint(p(0, 0), p(10, 0), p(20, 0), p(30, 0), 0.5);
    expect(mid.x).toBeCloseTo(15);
    expect(mid.y).toBeCloseTo(0);
  });
});

describe('wrapLabel (el nombre del nodo en la tarjeta)', () => {
  it('un nombre corto va en una línea', () => {
    expect(wrapLabel('Verificar Stock', 22, 3)).toEqual(['Verificar Stock']);
  });

  it('parte por palabras sin pasarse del ancho', () => {
    expect(wrapLabel('Registrar Notificación Sin Stock', 22, 3)).toEqual(['Registrar Notificación', 'Sin Stock']);
  });

  it('una palabra más larga que la línea se corta', () => {
    const lines = wrapLabel('Supercalifragilisticoespialidoso', 10, 4);
    expect(lines.every((l) => l.length <= 10)).toBe(true);
    expect(lines.join('')).toBe('Supercalifragilisticoespialidoso');
  });

  it('si no entra en las líneas permitidas termina en puntos suspensivos', () => {
    const lines = wrapLabel('uno dos tres cuatro cinco seis siete ocho', 8, 2);
    expect(lines).toHaveLength(2);
    expect(lines[1].endsWith('…')).toBe(true);
    expect(lines.every((l) => l.length <= 8)).toBe(true);
  });

  it('un texto vacío no da líneas', () => {
    expect(wrapLabel('', 20, 3)).toEqual([]);
    expect(wrapLabel('   ', 20, 3)).toEqual([]);
  });

  it('respeta los nombres reales de los flujos: ninguno pierde texto con el ancho de la tarjeta', () => {
    for (const graph of [flujo1Graph, flujo2Graph]) {
      for (const node of graph.nodes) {
        const lines = wrapLabel(node.name, 22, 3);
        expect(lines.some((l) => l.endsWith('…')), node.name).toBe(false);
        expect(lines.join(' ').replace(/\s+/g, ' ')).toBe(node.name);
      }
    }
  });
});
