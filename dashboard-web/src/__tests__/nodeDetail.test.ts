import { describe, expect, it } from 'vitest';

import { nodeDetailFacts, outputsSummary, previewText } from '@/lib/nodeDetail';
import type { NodeOverlay } from '@/lib/workflowTrace';

import { makeTraceNode } from './helpers/workflowFixtures';

const overlay = (visual: NodeOverlay['visual'], trace: NodeOverlay['trace'] = null): NodeOverlay => ({ visual, trace });

describe('outputsSummary (cuántos items salieron por cada rama)', () => {
  it('un IF nombra las ramas Sí y No', () => {
    expect(outputsSummary('if', [1, 0])).toBe('Sí: 1 · No: 0');
    expect(outputsSummary('if', [0, 3])).toBe('Sí: 0 · No: 3');
  });

  it('un Switch numera las salidas desde 1', () => {
    expect(outputsSummary('switch', [0, 1, 0, 0])).toBe('Salida 1: 0 · Salida 2: 1 · Salida 3: 0 · Salida 4: 0');
  });

  it('un nodo común con una sola salida no necesita el desglose', () => {
    expect(outputsSummary('postgres', [4])).toBeNull();
    expect(outputsSummary('postgres', [])).toBeNull();
  });

  it('un nodo común con varias salidas las numera', () => {
    expect(outputsSummary('merge', [1, 2])).toBe('Salida 1: 1 · Salida 2: 2');
  });

  it('un IF sin datos de salida no inventa nada', () => {
    expect(outputsSummary('if', [])).toBeNull();
  });
});

describe('previewText (la salida del nodo, como texto)', () => {
  it('sin salida no hay texto', () => {
    expect(previewText(null)).toBeNull();
    expect(previewText(undefined)).toBeNull();
  });

  it('una lista JSON se muestra indentada', () => {
    expect(previewText([{ stock: 10 }])).toBe('[\n  {\n    "stock": 10\n  }\n]');
  });

  it('el peor caso (un texto ya recortado por la API) pasa tal cual', () => {
    expect(previewText('[{"a":"muy larg…')).toBe('[{"a":"muy larg…');
  });

  it('un texto con HTML se conserva como texto: no se interpreta ni se modifica', () => {
    expect(previewText([{ html: '<img src=x onerror=alert(1)>' }])).toContain('<img src=x onerror=alert(1)>');
  });

  it('los valores raros no rompen', () => {
    expect(previewText(42)).toBe('42');
    expect(previewText(true)).toBe('true');
    expect(previewText([])).toBe('[]');
    expect(previewText({})).toBe('{}');
  });

  it('una estructura que JSON no puede serializar cae en texto plano sin lanzar', () => {
    const circular: Record<string, unknown> = {};
    circular.self = circular;
    expect(() => previewText(circular)).not.toThrow();
    expect(typeof previewText(circular)).toBe('string');
  });
});

describe('nodeDetailFacts (datos del nodo en la ejecución)', () => {
  it('un nodo correcto: inicio, duración, items y salidas por rama', () => {
    const trace = makeTraceNode('IF Stock', 'success', {
      started_at: '2026-09-21T14:03:20.055Z',
      duration_ms: 1,
      items_out: 1,
      outputs: [1, 0],
    });
    const facts = nodeDetailFacts(overlay('success', trace), 'if');
    expect(facts).toEqual([
      { label: 'Inicio', value: '21/09/2026 11:03:20' },
      { label: 'Duración', value: '1 ms' },
      { label: 'Items de salida', value: '1 ítem' },
      { label: 'Por cada salida', value: 'Sí: 1 · No: 0' },
    ]);
  });

  it('si corrió varias veces lo aclara (la duración las suma)', () => {
    const trace = makeTraceNode('X', 'success', { runs: 3, duration_ms: 30, items_out: 6, outputs: [6] });
    const facts = nodeDetailFacts(overlay('success', trace), 'postgres');
    expect(facts.find((f) => f.label.startsWith('Corridas'))?.value).toBe('3');
    expect(facts.find((f) => f.label === 'Items de salida')?.value).toBe('6 ítems');
  });

  it('un nodo con error no muestra items de salida que no produjo', () => {
    const trace = makeTraceNode('X', 'error', { items_out: 0, outputs: [], duration_ms: 12 });
    const labels = nodeDetailFacts(overlay('error', trace), 'postgres').map((f) => f.label);
    expect(labels).toEqual(['Inicio', 'Duración']);
  });

  it('un nodo que no se ejecutó, que falta o que todavía no llegó no tiene datos', () => {
    expect(nodeDetailFacts(overlay('skipped', makeTraceNode('X', 'skipped')), 'postgres')).toEqual([]);
    expect(nodeDetailFacts(overlay('missing'), 'postgres')).toEqual([]);
    expect(nodeDetailFacts(overlay('plain'), 'postgres')).toEqual([]);
    expect(nodeDetailFacts(overlay('pending', makeTraceNode('X', 'success')), 'postgres')).toEqual([]);
  });

  it('sin hora de inicio no inventa una', () => {
    const trace = makeTraceNode('X', 'running', { started_at: null, duration_ms: null });
    const facts = nodeDetailFacts(overlay('running', trace), 'postgres');
    expect(facts.find((f) => f.label === 'Inicio')).toBeUndefined();
    expect(facts.find((f) => f.label === 'Duración')?.value).toBe('—');
  });
});
