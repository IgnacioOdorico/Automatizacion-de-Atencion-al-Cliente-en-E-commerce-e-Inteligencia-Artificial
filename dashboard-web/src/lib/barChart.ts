/**
 * Gráfico de barras en SVG propio: escala de valores a coordenadas. Lógica
 * pura. `value: null` es "sin dato" (ningún intent respondido en la ventana,
 * TMR indefinido) y se distingue de `value: 0` (hubo respuestas, promedio 0s)
 * con `hasData: false` — el componente lo dibuja distinto, nunca como una
 * barra normal en 0 (eso se leería como "responde instantáneo").
 */

export interface BarDatum {
  key: string;
  value: number | null;
}

export interface BarGeometry {
  width: number;
  height: number;
  gap: number;
  /** Para compartir escala entre gráficos o fijar un techo; por defecto, el máximo de los valores. */
  maxValue?: number;
}

export interface BarLayout {
  key: string;
  value: number | null;
  hasData: boolean;
  x: number;
  /** Origen arriba-izquierda (SVG): a mayor valor, menor `y`. */
  y: number;
  width: number;
  height: number;
}

/**
 * Corta una etiqueta de dos palabras en 2 líneas (para que no se pise con la
 * barra de al lado en un gráfico angosto). Una palabra sola, o que ya entra
 * en `maxChars`, queda en una sola línea; con más de dos palabras corta en el
 * último espacio antes de la mitad.
 */
export function wrapBarLabel(label: string, maxChars = 12): [string] | [string, string] {
  if (label.length <= maxChars) return [label];
  const mid = Math.floor(label.length / 2);
  let splitAt = label.lastIndexOf(' ', mid);
  if (splitAt <= 0) splitAt = label.indexOf(' ', mid);
  if (splitAt <= 0) return [label];
  return [label.slice(0, splitAt), label.slice(splitAt + 1)];
}

export function barLayout(data: readonly BarDatum[], geometry: BarGeometry): BarLayout[] {
  if (data.length === 0) return [];

  const { width, height, gap } = geometry;
  const values = data.map((d) => d.value ?? 0);
  const max = geometry.maxValue ?? Math.max(0, ...values);

  const totalGap = gap * (data.length - 1);
  const barWidth = Math.max(0, (width - totalGap) / data.length);

  return data.map((d, i) => {
    const hasData = d.value !== null;
    const ratio = max > 0 ? Math.max(0, d.value ?? 0) / max : 0;
    const barHeight = ratio * height;
    return {
      key: d.key,
      value: d.value,
      hasData,
      x: i * (barWidth + gap),
      y: height - barHeight,
      width: barWidth,
      height: barHeight,
    };
  });
}
