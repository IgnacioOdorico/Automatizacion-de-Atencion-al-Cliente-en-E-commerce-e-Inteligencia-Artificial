/**
 * Gráfico de área apilada en SVG propio (serie diaria de órdenes por estado /
 * interacciones por canal). Lógica pura: cada capa (`key`) es la franja entre
 * la suma acumulada de las claves anteriores y la suya, para que el total
 * apilado sea la suma de todas.
 *
 * La API ya rellena los huecos (un día sin datos llega en 0, nunca falta la
 * fila) — acá solo falta el caso de una sola muestra: con un único día no hay
 * "ancho" para trazar una línea, así que se dibuja como un tramo plano en todo
 * el ancho del gráfico (dos puntos virtuales con el mismo valor) en vez de un
 * punto invisible.
 */

export interface SeriesPoint {
  date: string;
  values: Record<string, number>;
}

export interface AreaGeometry {
  width: number;
  height: number;
  padding: number;
}

export interface AreaPoint {
  x: number;
  y: number;
}

export interface StackedAreaLayer {
  key: string;
  /** Path cerrado (línea superior + inferior invertida): el relleno de la franja. */
  path: string;
  /** Línea superior de la franja (para trazar el borde o un punto por día). */
  points: AreaPoint[];
}

export interface AxisTick {
  date: string;
  x: number;
}

export interface StackedAreaResult {
  layers: StackedAreaLayer[];
  xTicks: AxisTick[];
}

function rowTotal(row: SeriesPoint, keys: readonly string[]): number {
  return keys.reduce((sum, k) => sum + (row.values[k] ?? 0), 0);
}

function cumulativeAt(row: SeriesPoint, keys: readonly string[], upto: number): number {
  let sum = 0;
  for (let i = 0; i <= upto; i += 1) sum += row.values[keys[i]] ?? 0;
  return sum;
}

export function stackedAreaLayers(
  rows: readonly SeriesPoint[],
  keys: readonly string[],
  geometry: AreaGeometry,
): StackedAreaResult {
  if (rows.length === 0) return { layers: [], xTicks: [] };

  const { width, height, padding } = geometry;
  const innerWidth = width - 2 * padding;
  const innerHeight = height - 2 * padding;
  const baseline = height - padding;
  const single = rows.length === 1;

  const maxTotal = Math.max(0, ...rows.map((r) => rowTotal(r, keys)));
  const yFor = (value: number): number => (maxTotal <= 0 ? baseline : baseline - (value / maxTotal) * innerHeight);

  /** Una posición por día (para el eje): con un solo día, al centro. */
  const xForRow = (index: number): number =>
    single ? padding + innerWidth / 2 : padding + (index / (rows.length - 1)) * innerWidth;

  const xTicks: AxisTick[] = rows.map((row, i) => ({ date: row.date, x: xForRow(i) }));

  // Para dibujar: con un solo día, dos puntos virtuales (mismo valor) que estiran la franja a todo el ancho.
  const drawXs: number[] = single ? [padding, width - padding] : rows.map((_, i) => xForRow(i));
  const drawRowIndices: number[] = single ? [0, 0] : rows.map((_, i) => i);

  const layers: StackedAreaLayer[] = keys.map((key, keyIndex) => {
    const topPoints: AreaPoint[] = drawRowIndices.map((rowIndex, i) => ({
      x: drawXs[i],
      y: yFor(cumulativeAt(rows[rowIndex], keys, keyIndex)),
    }));
    const bottomPoints: AreaPoint[] = drawRowIndices.map((rowIndex, i) => ({
      x: drawXs[i],
      y: yFor(keyIndex === 0 ? 0 : cumulativeAt(rows[rowIndex], keys, keyIndex - 1)),
    }));

    const top = topPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
    const bottom = [...bottomPoints]
      .reverse()
      .map((p) => `L ${p.x} ${p.y}`)
      .join(' ');

    return { key, path: `${top} ${bottom} Z`, points: topPoints };
  });

  return { layers, xTicks };
}
