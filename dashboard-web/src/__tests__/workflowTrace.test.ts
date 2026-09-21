import { describe, expect, it } from 'vitest';

import { edgeKey } from '@/lib/workflowGraph';
import { buildOverlay, effectivePath, isEdgeTraversed, traceNotes } from '@/lib/workflowTrace';
import type { ExecutionDetail, GraphEdge } from '@/types/monitoring';

import {
  CON_STOCK_PATH,
  SIN_STOCK_PATH,
  flujo1Graph,
  flujo2Graph,
  makeTraceNode,
  traceConStock,
  traceError,
  traceSinStock,
} from './helpers/workflowFixtures';

const visuals = (detail: ExecutionDetail | null, revealed?: number | null, graph = flujo1Graph) => {
  const overlay = buildOverlay(graph, detail, { revealed });
  return Object.fromEntries([...overlay.nodes].map(([name, n]) => [name, n.visual]));
};

const activeEdges = (detail: ExecutionDetail | null, revealed?: number | null) => {
  const overlay = buildOverlay(flujo1Graph, detail, { revealed });
  return flujo1Graph.edges
    .filter((e) => overlay.edges.get(edgeKey(e))?.visual === 'active')
    .map((e) => `${e.from} -> ${e.to}`);
};

describe('buildOverlay sin ejecución elegida', () => {
  it('todos los nodos quedan "plain" y todas las aristas "idle"', () => {
    const overlay = buildOverlay(flujo1Graph, null);
    expect([...overlay.nodes.values()].every((n) => n.visual === 'plain')).toBe(true);
    expect([...overlay.edges.values()].every((e) => e.visual === 'idle' && !e.flowing)).toBe(true);
    expect(overlay.hasTrace).toBe(false);
  });

  it('una traza vacía (datos purgados, demasiado grande) tampoco pinta nada', () => {
    const detail: ExecutionDetail = { ...traceConStock(), nodes: [], path: [], truncated: true };
    const overlay = buildOverlay(flujo1Graph, detail);
    expect([...overlay.nodes.values()].every((n) => n.visual === 'plain')).toBe(true);
    expect(overlay.hasTrace).toBe(false);
  });
});

describe('buildOverlay: pedido con stock', () => {
  it('los nodos del camino salen "success" y los de la otra rama "skipped"', () => {
    const v = visuals(traceConStock());
    for (const name of CON_STOCK_PATH) expect(v[name], name).toBe('success');
    for (const name of SIN_STOCK_PATH.filter((n) => !CON_STOCK_PATH.includes(n))) {
      expect(v[name], name).toBe('skipped');
    }
    expect(v['Registrar Alerta Stock Bajo']).toBe('skipped');
  });

  it('se ilumina la rama "Sí" del IF y la de "No" queda apagada', () => {
    const active = activeEdges(traceConStock());
    expect(active).toContain('IF Stock Disponible -> Actualizar Stock');
    expect(active).not.toContain('IF Stock Disponible -> Marcar Sin Stock');
    expect(active).toContain('IF Stock Bajo -> Confirmar Orden');
    expect(active).not.toContain('IF Stock Bajo -> Registrar Alerta Stock Bajo');
  });

  it('las aristas del camino recorrido son exactamente las que unen nodos consecutivos ejecutados', () => {
    expect(activeEdges(traceConStock()).sort()).toEqual(
      [
        'Webhook - Recibir Orden -> Registrar Orden',
        'Registrar Orden -> Verificar Stock',
        'Verificar Stock -> IF Stock Disponible',
        'IF Stock Disponible -> Actualizar Stock',
        'Actualizar Stock -> IF Stock Bajo',
        'IF Stock Bajo -> Confirmar Orden',
        'Confirmar Orden -> Enviar Email Confirmación',
        'Enviar Email Confirmación -> Registrar Notificación',
        'Registrar Notificación -> Respuesta Confirmada',
      ].sort(),
    );
  });

  it('las aristas que no se recorrieron con overlay quedan "inactive" (no "idle")', () => {
    const overlay = buildOverlay(flujo1Graph, traceConStock());
    const edge = flujo1Graph.edges.find((e) => e.to === 'Marcar Sin Stock');
    if (!edge) throw new Error('falta la arista');
    expect(overlay.edges.get(edgeKey(edge))?.visual).toBe('inactive');
  });
});

describe('buildOverlay: pedido sin stock', () => {
  it('se ilumina la rama "No" del IF', () => {
    const active = activeEdges(traceSinStock());
    expect(active).toContain('IF Stock Disponible -> Marcar Sin Stock');
    expect(active).not.toContain('IF Stock Disponible -> Actualizar Stock');
    expect(visuals(traceSinStock())['Actualizar Stock']).toBe('skipped');
    expect(visuals(traceSinStock())['Respuesta Sin Stock']).toBe('success');
  });
});

describe('buildOverlay: ejecución con error', () => {
  it('el nodo que falló sale "error" y nada después se ilumina', () => {
    const v = visuals(traceError());
    expect(v['Webhook - Recibir Orden']).toBe('success');
    expect(v['Registrar Orden']).toBe('error');
    expect(v['Verificar Stock']).toBe('skipped');
    expect(activeEdges(traceError())).toEqual(['Webhook - Recibir Orden -> Registrar Orden']);
  });
});

describe('buildOverlay: nodos que no coinciden', () => {
  it('un nodo del diagrama que no figura en la traza queda "missing"', () => {
    const detail = traceConStock();
    detail.nodes = detail.nodes.filter((n) => n.name !== 'Marcar Sin Stock');
    expect(visuals(detail)['Marcar Sin Stock']).toBe('missing');
  });

  it('no hay arista activa hacia un nodo que no figura en la traza', () => {
    const detail = traceConStock();
    detail.nodes = detail.nodes.filter((n) => n.name !== 'Confirmar Orden');
    expect(activeEdges(detail)).not.toContain('IF Stock Bajo -> Confirmar Orden');
  });

  it('los estados poco comunes se conservan', () => {
    const detail = traceConStock();
    const node = detail.nodes.find((n) => n.name === 'Verificar Stock');
    if (node) node.status = 'running';
    expect(visuals(detail)['Verificar Stock']).toBe('running');
    if (node) node.status = 'waiting';
    expect(visuals(detail)['Verificar Stock']).toBe('waiting');
    if (node) node.status = 'canceled';
    expect(visuals(detail)['Verificar Stock']).toBe('canceled');
  });

  it('un estado desconocido se trata como "skipped": nunca se afirma un éxito que la API no dijo', () => {
    const detail = traceConStock();
    const node = detail.nodes.find((n) => n.name === 'Verificar Stock');
    if (node) node.status = 'algo-nuevo';
    expect(visuals(detail)['Verificar Stock']).toBe('skipped');
  });
});

describe('isEdgeTraversed', () => {
  const edge = (over: Partial<GraphEdge> = {}): GraphEdge => ({
    from: 'A',
    to: 'B',
    output_index: 0,
    input_index: 0,
    kind: 'main',
    ...over,
  });
  const byName = (nodes: Array<ReturnType<typeof makeTraceNode>>) => new Map(nodes.map((n) => [n.name, n]));

  it('recorrida: el origen produjo items por esa salida y el destino se ejecutó', () => {
    expect(isEdgeTraversed(edge(), byName([makeTraceNode('A', 'success'), makeTraceNode('B', 'success')]))).toBe(true);
  });

  it('no recorrida: la salida elegida no produjo items', () => {
    const a = makeTraceNode('A', 'success', { outputs: [0, 2] });
    const b = makeTraceNode('B', 'success');
    expect(isEdgeTraversed(edge({ output_index: 0 }), byName([a, b]))).toBe(false);
    expect(isEdgeTraversed(edge({ output_index: 1 }), byName([a, b]))).toBe(true);
  });

  it('no recorrida: el destino no se ejecutó (skipped) o no figura', () => {
    const a = makeTraceNode('A', 'success');
    expect(isEdgeTraversed(edge(), byName([a, makeTraceNode('B', 'skipped')]))).toBe(false);
    expect(isEdgeTraversed(edge(), byName([a]))).toBe(false);
  });

  it('no recorrida: el origen falló (sin salidas)', () => {
    const a = makeTraceNode('A', 'error', { outputs: [] });
    expect(isEdgeTraversed(edge(), byName([a, makeTraceNode('B', 'success')]))).toBe(false);
  });

  it('una salida que no existe en outputs no cuenta', () => {
    const a = makeTraceNode('A', 'success', { outputs: [1] });
    expect(isEdgeTraversed(edge({ output_index: 3 }), byName([a, makeTraceNode('B', 'success')]))).toBe(false);
  });

  it('las conexiones de IA (sub-nodo -> nodo) valen si ambos se ejecutaron', () => {
    const model = makeTraceNode('A', 'success', { outputs: [] });
    const chain = makeTraceNode('B', 'success');
    const ai = edge({ kind: 'ai_languageModel' });
    expect(isEdgeTraversed(ai, byName([model, chain]))).toBe(true);
    expect(isEdgeTraversed(ai, byName([makeTraceNode('A', 'skipped'), chain]))).toBe(false);
  });
});

describe('effectivePath', () => {
  it('usa el path de la API', () => {
    expect(effectivePath(traceConStock())).toEqual(CON_STOCK_PATH);
  });

  it('si la API no manda path, toma los nodos ejecutados en el orden del workflow', () => {
    const detail = { ...traceSinStock(), path: [] };
    const expected = flujo1Graph.nodes.map((n) => n.name).filter((n) => SIN_STOCK_PATH.includes(n));
    expect(effectivePath(detail)).toEqual(expected);
  });

  it('sin ejecución no hay camino', () => {
    expect(effectivePath(null)).toEqual([]);
  });
});

describe('buildOverlay: reproducción del camino (revealed)', () => {
  it('con revealed en 3 solo los tres primeros nodos están encendidos y el resto "pending"', () => {
    const v = visuals(traceConStock(), 3);
    expect(v['Webhook - Recibir Orden']).toBe('success');
    expect(v['Registrar Orden']).toBe('success');
    expect(v['Verificar Stock']).toBe('success');
    expect(v['IF Stock Disponible']).toBe('pending');
    expect(v['Respuesta Confirmada']).toBe('pending');
  });

  it('lo que nunca se ejecutó sigue "skipped" durante la reproducción', () => {
    expect(visuals(traceConStock(), 2)['Marcar Sin Stock']).toBe('skipped');
  });

  it('solo se iluminan las aristas entre nodos ya revelados y la que entra al actual "fluye"', () => {
    const overlay = buildOverlay(flujo1Graph, traceConStock(), { revealed: 3 });
    expect(overlay.current).toBe('Verificar Stock');
    const active = flujo1Graph.edges.filter((e) => overlay.edges.get(edgeKey(e))?.visual === 'active');
    expect(active.map((e) => `${e.from} -> ${e.to}`).sort()).toEqual([
      'Registrar Orden -> Verificar Stock',
      'Webhook - Recibir Orden -> Registrar Orden',
    ]);
    const flowing = flujo1Graph.edges.filter((e) => overlay.edges.get(edgeKey(e))?.flowing);
    expect(flowing.map((e) => `${e.from} -> ${e.to}`)).toEqual(['Registrar Orden -> Verificar Stock']);
  });

  it('revealed null o igual al total es la vista final: sin nodo actual ni aristas que fluyen', () => {
    const total = CON_STOCK_PATH.length;
    for (const revealed of [null, undefined, total, total + 5]) {
      const overlay = buildOverlay(flujo1Graph, traceConStock(), { revealed });
      expect(overlay.current).toBeNull();
      expect([...overlay.edges.values()].some((e) => e.flowing)).toBe(false);
      expect(overlay.nodes.get('Respuesta Confirmada')?.visual).toBe('success');
    }
  });

  it('revealed 0 no enciende nada', () => {
    const v = visuals(traceConStock(), 0);
    expect(v['Webhook - Recibir Orden']).toBe('pending');
    expect(buildOverlay(flujo1Graph, traceConStock(), { revealed: 0 }).current).toBeNull();
  });
});

describe('traceNotes (avisos para el usuario)', () => {
  it('una ejecución completa no trae avisos', () => {
    const notes = traceNotes(flujo1Graph, traceConStock());
    expect(notes.missing).toEqual([]);
    expect(notes.extra).toEqual([]);
    expect(notes.truncated).toBe(false);
    expect(notes.readError).toBeNull();
  });

  it('lista los nodos del diagrama que la traza no tiene', () => {
    const detail = traceConStock();
    detail.nodes = detail.nodes.filter((n) => n.name !== 'Marcar Sin Stock' && n.name !== 'Respuesta Sin Stock');
    expect(traceNotes(flujo1Graph, detail).missing.sort()).toEqual(['Marcar Sin Stock', 'Respuesta Sin Stock']);
  });

  it('lista aparte los nodos de la traza que ya no existen en el workflow actual', () => {
    const detail = traceConStock();
    detail.nodes.push(makeTraceNode('Nodo Viejo', 'success', { short_type: null }));
    const notes = traceNotes(flujo1Graph, detail);
    expect(notes.extra.map((n) => n.name)).toEqual(['Nodo Viejo']);
  });

  it('informa si la ejecución quedó truncada o si no se pudo leer', () => {
    const truncated = { ...traceConStock(), nodes: [], path: [], truncated: true };
    expect(traceNotes(flujo1Graph, truncated).truncated).toBe(true);
    const broken = { ...traceConStock(), nodes: [], path: [], error: 'La ejecución no tiene datos de traza (¿fueron purgados?)' };
    expect(traceNotes(flujo1Graph, broken).readError).toContain('purgados');
  });

  it('sin traza (nodes vacío) no lista todos los nodos como faltantes: el aviso es el de lectura', () => {
    const empty = { ...traceConStock(), nodes: [], path: [], truncated: true };
    expect(traceNotes(flujo1Graph, empty).missing).toEqual([]);
  });

  it('sin ejecución no hay avisos', () => {
    expect(traceNotes(flujo1Graph, null)).toEqual({ missing: [], extra: [], truncated: false, readError: null });
  });

  it('un grafo de otro workflow marca todo lo suyo como faltante', () => {
    const notes = traceNotes(flujo2Graph, traceConStock());
    expect(notes.missing.length).toBe(flujo2Graph.nodes.length);
    expect(notes.extra.length).toBe(traceConStock().nodes.length);
  });
});
