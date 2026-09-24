/**
 * Eje de fechas de los gráficos de líneas/área de Métricas. Lógica pura.
 *
 * Decisión no obvia: `daily[].date` / `by_channel_daily[].date` son "fecha
 * calendario UTC" (ver docs/API_METRICAS.md), no un instante. Pasarlas por
 * `new Date(...)` y formatear en la zona horaria del negocio (lib/format.ts
 * usa America/Argentina/Mendoza, UTC-3) correría el día mostrado un día para
 * atrás a la medianoche. Por eso este eje formatea con un split de texto,
 * nunca con `Date`.
 */

/** "2026-09-14" -> "14/09". Un valor sin ese formato se muestra tal cual (nunca rompe el eje). */
export function isoDateShortLabel(date: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
  if (!match) return date === '' ? '—' : date;
  const [, , month, day] = match;
  return `${day}/${month}`;
}

/**
 * Qué índices (0-based) del eje mostrar como etiqueta, sin amontonarse: con
 * `count` puntos y como máximo `maxTicks` etiquetas, siempre incluye el primero
 * y el último y reparte el resto lo más parejo posible.
 */
export function axisTickIndices(count: number, maxTicks = 6): number[] {
  if (count <= 0) return [];
  if (count <= maxTicks) return Array.from({ length: count }, (_, i) => i);

  const ticks = Math.max(2, maxTicks);
  const step = (count - 1) / (ticks - 1);
  const indices = new Set<number>();
  for (let i = 0; i < ticks; i += 1) {
    indices.add(Math.round(i * step));
  }
  return [...indices].sort((a, b) => a - b);
}
