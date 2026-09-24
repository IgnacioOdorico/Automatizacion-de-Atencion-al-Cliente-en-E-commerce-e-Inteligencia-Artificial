import { describe, expect, it } from 'vitest';

import { nodeAriaLabel, nodeMetaLines } from '@/lib/nodeCard';
import type { NodeOverlay } from '@/lib/workflowTrace';

import { makeTraceNode } from './helpers/workflowFixtures';

const overlay = (visual: NodeOverlay['visual'], trace: NodeOverlay['trace'] = null): NodeOverlay => ({ visual, trace });

describe('nodeMetaLines (las líneas chicas de la tarjeta)', () => {
  it('sin ejecución elegida no hay nada que decir', () => {
    expect(nodeMetaLines(overlay('plain'))).toEqual([]);
  });

  it('un nodo correcto muestra su duración y sus items', () => {
    const trace = makeTraceNode('A', 'success', { duration_ms: 435, items_out: 1 });
    expect(nodeMetaLines(overlay('success', trace))).toEqual(['435 ms', '1 ítem']);
  });

  it('con varios items y varias corridas lo aclara', () => {
    const trace = makeTraceNode('A', 'success', { duration_ms: 1400, items_out: 3, runs: 2 });
    expect(nodeMetaLines(overlay('success', trace))).toEqual(['1,4 s', '3 ítems · 2 corridas']);
  });

  it('un nodo sin salida y sin duración no inventa datos', () => {
    const trace = makeTraceNode('A', 'success', { duration_ms: null, items_out: 0 });
    expect(nodeMetaLines(overlay('success', trace))).toEqual(['—', '0 ítems']);
  });

  it('un nodo con error lo dice con palabras y muestra cuánto tardó', () => {
    const trace = makeTraceNode('A', 'error', { duration_ms: 12, outputs: [] });
    expect(nodeMetaLines(overlay('error', trace))).toEqual(['Con error', '12 ms']);
  });

  it('un nodo que no se ejecutó, que falta en la traza o que está a medias, lo dice', () => {
    expect(nodeMetaLines(overlay('skipped'))).toEqual(['No se ejecutó']);
    expect(nodeMetaLines(overlay('missing'))).toEqual(['Sin datos']);
    expect(nodeMetaLines(overlay('running'))).toEqual(['En curso']);
    expect(nodeMetaLines(overlay('waiting'))).toEqual(['En espera']);
    expect(nodeMetaLines(overlay('canceled'))).toEqual(['Cancelado']);
  });

  it('durante la reproducción, lo que todavía no llegó queda en blanco', () => {
    expect(nodeMetaLines(overlay('pending', makeTraceNode('A', 'success')))).toEqual([]);
  });
});

describe('nodeAriaLabel', () => {
  it('sin ejecución: nombre, tipo y la acción', () => {
    expect(nodeAriaLabel('Verificar Stock', 'Base de datos (PostgreSQL)', false, overlay('plain'))).toBe(
      'Verificar Stock. Base de datos (PostgreSQL). Abrir detalle.',
    );
  });

  it('con ejecución suma el estado y los datos que la tarjeta muestra', () => {
    const trace = makeTraceNode('A', 'success', { duration_ms: 435, items_out: 1 });
    expect(nodeAriaLabel('Verificar Stock', 'Base de datos (PostgreSQL)', false, overlay('success', trace))).toBe(
      'Verificar Stock. Base de datos (PostgreSQL). Correcto. 435 ms. 1 ítem. Abrir detalle.',
    );
  });

  it('un nodo con error dice "Con error" una sola vez', () => {
    const trace = makeTraceNode('A', 'error', { duration_ms: 12, outputs: [] });
    const label = nodeAriaLabel('Registrar Orden', 'Base de datos', false, overlay('error', trace));
    expect(label).toBe('Registrar Orden. Base de datos. Con error. 12 ms. Abrir detalle.');
  });

  it('un nodo que no se ejecutó lo dice', () => {
    expect(nodeAriaLabel('Marcar Sin Stock', 'Base de datos', false, overlay('skipped'))).toBe(
      'Marcar Sin Stock. Base de datos. No se ejecutó. Abrir detalle.',
    );
  });

  it('un nodo deshabilitado lo aclara', () => {
    expect(nodeAriaLabel('X', 'Código', true, overlay('plain'))).toBe('X. Código. Nodo deshabilitado. Abrir detalle.');
  });

  it('lo que todavía no llegó en la reproducción no afirma nada', () => {
    expect(nodeAriaLabel('X', 'Código', false, overlay('pending', makeTraceNode('X', 'success')))).toBe(
      'X. Código. Abrir detalle.',
    );
  });
});
