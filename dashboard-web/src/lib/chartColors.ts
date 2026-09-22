/**
 * Paleta categórica de los gráficos de Métricas (dona/barras/área apilada):
 * 8 tonos distinguibles sobre fondo oscuro. Los valores están en sync con
 * `--chart-1`..`--chart-8` de styles/tokens.css (test: chartColors.test.ts
 * verifica esa igualdad y el contraste >= 3:1, WCAG 1.4.11).
 *
 * Se usan como literales (no `var(--chart-N)`) porque un `fill` de SVG con
 * `var()` depende del soporte del motor de render; un hex directo no falla
 * nunca. `lib/domain.ts` sigue siendo la fuente de las etiquetas en español;
 * este módulo solo agrega el color para las series de un gráfico.
 */

export const CHART_COLORS = {
  1: '#818cf8',
  2: '#4ade80',
  3: '#fbbf24',
  4: '#f0878b',
  5: '#38bdf8',
  6: '#a78bfa',
  7: '#2dd4bf',
  8: '#94a3b8',
} as const;

/** Un color por estado de orden, sin repetir entre los 8 valores del dominio (init_simple.sql:51-60). */
export const ORDER_STATUS_COLORS: Record<string, string> = {
  pending: CHART_COLORS[8],
  processing: CHART_COLORS[1],
  confirmed: CHART_COLORS[2],
  shipped: CHART_COLORS[5],
  delivered: CHART_COLORS[6],
  no_stock: CHART_COLORS[3],
  cancelled: CHART_COLORS[7],
  error: CHART_COLORS[4],
};

/** Un color por intent (dominio de 4, init_simple.sql:106-107). */
export const INTENT_COLORS: Record<string, string> = {
  FAQ: CHART_COLORS[1],
  ESTADO_PEDIDO: CHART_COLORS[5],
  RECLAMO: CHART_COLORS[4],
  GENERAL: CHART_COLORS[8],
};

/** Un color por canal (dominio de 3). */
export const CHANNEL_COLORS: Record<string, string> = {
  whatsapp: CHART_COLORS[2],
  telegram: CHART_COLORS[5],
  email: CHART_COLORS[7],
};

const FALLBACK_COLOR = CHART_COLORS[8];

function colorFrom(map: Record<string, string>, key: string | null | undefined): string {
  if (key && map[key]) return map[key];
  return FALLBACK_COLOR;
}

export function orderStatusColor(status: string | null | undefined): string {
  return colorFrom(ORDER_STATUS_COLORS, status);
}

export function intentColor(intent: string | null | undefined): string {
  return colorFrom(INTENT_COLORS, intent);
}

export function channelColor(channel: string | null | undefined): string {
  return colorFrom(CHANNEL_COLORS, channel);
}
