/**
 * Gráfico de dona en SVG propio (sin librería de charts): ángulos y `path` de
 * cada porción. Lógica pura, la testea sin montar nada.
 */

export interface DonutSlice {
  key: string;
  value: number;
  color: string;
}

export interface DonutGeometry {
  cx: number;
  cy: number;
  outerR: number;
  innerR: number;
}

export interface DonutArc {
  key: string;
  value: number;
  color: string;
  /** Grados, 0 = arriba (12 en punto), crece en sentido horario. */
  startAngle: number;
  endAngle: number;
  /** Del total (0-100). */
  percent: number;
  path: string;
}

/**
 * Una sola porción con el 100% no se puede dibujar como un arco de 360°: el
 * punto de inicio y de fin coinciden y el comando `A` de SVG queda degenerado
 * (no dibuja nada). Se recorta un pelo para que siga siendo un arco válido;
 * la diferencia (0.02°) no se nota a simple vista.
 */
const MAX_SWEEP_DEGREES = 359.98;

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number): { x: number; y: number } {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function slicePath(geometry: DonutGeometry, startAngle: number, endAngle: number): string {
  const { cx, cy, outerR, innerR } = geometry;
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  const startOuter = polarToCartesian(cx, cy, outerR, endAngle);
  const endOuter = polarToCartesian(cx, cy, outerR, startAngle);
  const startInner = polarToCartesian(cx, cy, innerR, startAngle);
  const endInner = polarToCartesian(cx, cy, innerR, endAngle);
  return [
    `M ${startOuter.x} ${startOuter.y}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 0 ${endOuter.x} ${endOuter.y}`,
    `L ${startInner.x} ${startInner.y}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 1 ${endInner.x} ${endInner.y}`,
    'Z',
  ].join(' ');
}

/** Porciones con ángulo y `path`, en el mismo orden que `slices`. Las de valor 0 se omiten (no dibujan nada). */
export function donutArcs(slices: readonly DonutSlice[], geometry: DonutGeometry): DonutArc[] {
  const total = slices.reduce((sum, s) => sum + Math.max(0, s.value), 0);
  if (total <= 0) return [];

  const arcs: DonutArc[] = [];
  let cursor = 0;
  for (const slice of slices) {
    const value = Math.max(0, slice.value);
    if (value <= 0) continue;
    const sweep = Math.min((value / total) * 360, MAX_SWEEP_DEGREES);
    const startAngle = cursor;
    const endAngle = cursor + sweep;
    arcs.push({
      key: slice.key,
      value: slice.value,
      color: slice.color,
      startAngle,
      endAngle,
      percent: (value / total) * 100,
      path: slicePath(geometry, startAngle, endAngle),
    });
    cursor = endAngle;
  }
  return arcs;
}
