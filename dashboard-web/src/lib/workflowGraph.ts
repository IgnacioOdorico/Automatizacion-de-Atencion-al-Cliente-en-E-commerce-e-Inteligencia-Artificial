import type { Point, Rect } from '@/lib/viewport';
import type { GraphEdge, WorkflowGraph } from '@/types/monitoring';

/**
 * Del grafo sanitizado de n8n al dibujo: tamaño y posición de cada tarjeta,
 * camino curvo de cada conexión y rótulos de rama. Lógica pura (sin React).
 */

/** Tarjeta de un nodo, en unidades del lienzo. */
export const CARD_W = 156;
export const CARD_H = 100;
/** Las posiciones de n8n se escalan: el ancho de tarjeta y la separación de n8n no son los mismos. */
export const SPREAD_X = 0.85;
export const SPREAD_Y = 1;
/** Aire mínimo entre tarjetas cuando hay que separar las que se pisan. */
export const CARD_GAP = 20;

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface NodeBox extends Box {
  name: string;
  shortType: string | null;
  disabled: boolean;
}

export interface EdgeShape {
  key: string;
  from: string;
  to: string;
  kind: string;
  outputIndex: number;
  /** Camino SVG (curva cúbica). */
  d: string;
  start: Point;
  end: Point;
  /** Rótulo de rama ("Sí", "No", "Salida 2") o `null`. */
  label: string | null;
  labelX: number;
  labelY: number;
}

export interface GraphLayout {
  nodes: NodeBox[];
  edges: EdgeShape[];
  bounds: Rect;
}

/** Identifica una arista de forma única (dos ramas de un mismo nodo pueden ir al mismo destino). */
export function edgeKey(edge: GraphEdge): string {
  return `${edge.from}|${edge.output_index}|${edge.to}|${edge.input_index}|${edge.kind}`;
}

const overlap = (a: Box, b: Box, gap: number): boolean =>
  a.x < b.x + b.w + gap && b.x < a.x + a.w + gap && a.y < b.y + b.h + gap && b.y < a.y + a.h + gap;

/**
 * Separa las tarjetas que se pisan (o quedan a menos de `gap`): se procesan de
 * arriba hacia abajo y la que pisa a otra ya ubicada baja por debajo de ella.
 * Devuelve copias en el orden de entrada; es determinista.
 */
export function relieveOverlaps<T extends Box>(boxes: readonly T[], gap: number): T[] {
  const order = boxes
    .map((box, index) => ({ box, index }))
    .sort((a, b) => a.box.y - b.box.y || a.box.x - b.box.x || a.index - b.index);
  const placed: T[] = [];
  const out: T[] = new Array<T>(boxes.length);
  for (const { box, index } of order) {
    let current = { ...box };
    let moved = true;
    while (moved) {
      moved = false;
      for (const other of placed) {
        if (overlap(current, other, gap)) {
          current = { ...current, y: other.y + other.h + gap };
          moved = true;
        }
      }
    }
    placed.push(current);
    out[index] = current;
  }
  return out;
}

export function branchLabel(shortType: string | null, outputIndex: number): string | null {
  if (shortType === 'if') return outputIndex === 0 ? 'Sí' : 'No';
  if (shortType === 'switch') return `Salida ${outputIndex + 1}`;
  return null;
}

export function cubicPoint(p0: Point, p1: Point, p2: Point, p3: Point, t: number): Point {
  const u = 1 - t;
  const a = u * u * u;
  const b = 3 * u * u * t;
  const c = 3 * u * t * t;
  const d = t * t * t;
  return {
    x: a * p0.x + b * p1.x + c * p2.x + d * p3.x,
    y: a * p0.y + b * p1.y + c * p2.y + d * p3.y,
  };
}

const round = (n: number): number => Math.round(n * 100) / 100;
const clamp = (n: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, n));

/** Dónde en la curva va el rótulo de rama: cerca del origen, para que se lea de qué salida es. */
const LABEL_T = 0.3;

interface Anchors {
  start: Point;
  end: Point;
  c1: Point;
  c2: Point;
}

function anchorsFor(from: Box, to: Box, kind: string): Anchors {
  const isAi = kind !== 'main';
  const fromCx = from.x + from.w / 2;
  const toCx = to.x + to.w / 2;

  // Sub-nodos de IA: se unen por arriba/abajo con el nodo que los usa.
  // Un destino en la misma columna o más abajo sale por abajo; uno arriba, por arriba.
  const goesVertical =
    isAi || (to.x < from.x + from.w - 1 && (to.y >= from.y + from.h || to.y + to.h <= from.y));

  if (goesVertical) {
    const down = to.y + to.h / 2 > from.y + from.h / 2;
    const start = { x: fromCx, y: down ? from.y + from.h : from.y };
    const end = { x: toCx, y: down ? to.y : to.y + to.h };
    const dy = clamp(Math.abs(end.y - start.y) * 0.5, 24, 120) * (down ? 1 : -1);
    return { start, end, c1: { x: start.x, y: start.y + dy }, c2: { x: end.x, y: end.y - dy } };
  }

  const start = { x: from.x + from.w, y: from.y + from.h / 2 };
  const end = { x: to.x, y: to.y + to.h / 2 };
  const backwards = end.x < start.x;
  const dx = backwards ? 140 : clamp(Math.abs(end.x - start.x) * 0.5, 24, 140);
  return { start, end, c1: { x: start.x + dx, y: start.y }, c2: { x: end.x - dx, y: end.y } };
}

/** Bordes del dibujo: el mínimo rectángulo que contiene todas las tarjetas. */
function boundsOf(boxes: readonly Box[]): Rect {
  if (boxes.length === 0) return { minX: 0, minY: 0, maxX: 0, maxY: 0 };
  return {
    minX: Math.min(...boxes.map((b) => b.x)),
    minY: Math.min(...boxes.map((b) => b.y)),
    maxX: Math.max(...boxes.map((b) => b.x + b.w)),
    maxY: Math.max(...boxes.map((b) => b.y + b.h)),
  };
}

/** Calcula todo lo que hace falta para dibujar el grafo. */
export function layoutGraph(graph: WorkflowGraph): GraphLayout {
  if (graph.nodes.length === 0) {
    return { nodes: [], edges: [], bounds: { minX: 0, minY: 0, maxX: 0, maxY: 0 } };
  }

  const originX = Math.min(...graph.nodes.map((n) => n.position[0]));
  const originY = Math.min(...graph.nodes.map((n) => n.position[1]));

  const raw = graph.nodes.map((n) => ({
    x: round((n.position[0] - originX) * SPREAD_X),
    y: round((n.position[1] - originY) * SPREAD_Y),
    w: CARD_W,
    h: CARD_H,
  }));
  const placed = relieveOverlaps(raw, CARD_GAP);

  const nodes: NodeBox[] = graph.nodes.map((n, i) => ({
    ...placed[i],
    name: n.name,
    shortType: n.short_type,
    disabled: n.disabled,
  }));
  const byName = new Map(nodes.map((n) => [n.name, n]));

  const edges: EdgeShape[] = [];
  for (const edge of graph.edges) {
    const from = byName.get(edge.from);
    const to = byName.get(edge.to);
    if (!from || !to) continue;
    const { start, end, c1, c2 } = anchorsFor(from, to, edge.kind);
    const label = edge.kind === 'main' ? branchLabel(from.shortType, edge.output_index) : null;
    const at = cubicPoint(start, c1, c2, end, LABEL_T);
    edges.push({
      key: edgeKey(edge),
      from: edge.from,
      to: edge.to,
      kind: edge.kind,
      outputIndex: edge.output_index,
      d: `M ${round(start.x)} ${round(start.y)} C ${round(c1.x)} ${round(c1.y)} ${round(c2.x)} ${round(c2.y)} ${round(end.x)} ${round(end.y)}`,
      start,
      end,
      label,
      labelX: round(at.x),
      labelY: round(at.y),
    });
  }

  return { nodes, edges, bounds: boundsOf(nodes) };
}

/**
 * Parte un nombre en líneas para la tarjeta (SVG no ajusta texto solo): por
 * palabras, sin pasar de `maxChars`; una palabra más larga se corta; si no entra
 * en `maxLines` la última termina en "…".
 */
export function wrapLabel(text: string, maxChars: number, maxLines: number): string[] {
  const words = text.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return [];

  // Palabras más largas que la línea: se parten en trozos.
  const pieces: string[] = [];
  for (const word of words) {
    for (let i = 0; i < word.length; i += maxChars) pieces.push(word.slice(i, i + maxChars));
  }

  const lines: string[] = [];
  let current = '';
  for (const piece of pieces) {
    if (current === '') current = piece;
    else if (current.length + 1 + piece.length <= maxChars) current += ` ${piece}`;
    else {
      lines.push(current);
      current = piece;
    }
  }
  lines.push(current);

  if (lines.length <= maxLines) return lines;
  const kept = lines.slice(0, maxLines);
  const last = kept[maxLines - 1];
  kept[maxLines - 1] = `${last.slice(0, Math.max(maxChars - 1, 0)).trimEnd()}…`;
  return kept;
}
