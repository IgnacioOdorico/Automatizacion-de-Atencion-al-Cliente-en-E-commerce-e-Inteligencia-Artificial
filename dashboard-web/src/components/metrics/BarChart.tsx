import { useId } from 'react';

import { barLayout } from '@/lib/barChart';
import { formatTmr } from '@/lib/format';

export interface BarEntry {
  key: string;
  label: string;
  value: number | null;
  color: string;
  /** Cuántas muestras hay detrás de este promedio (ej. cuántas interacciones de ese intent). */
  count: number;
}

interface BarChartProps {
  title: string;
  entries: BarEntry[];
  reducedMotion?: boolean;
}

const WIDTH = 320;
const HEIGHT = 170;
const PAD_X = 8;
const PAD_TOP = 26;
const PAD_BOTTOM = 46;
const CHART_H = HEIGHT - PAD_TOP - PAD_BOTTOM;
const CHART_W = WIDTH - PAD_X * 2;
const GAP = 14;
/** Alto mínimo visible de una barra con dato real (aunque el promedio sea 0s): nunca "altura 0" silenciosa. */
const MIN_BAR_H = 4;

function description(entries: BarEntry[]): string {
  return entries
    .map((e) =>
      e.value === null
        ? `${e.label}: sin respuestas todavía (${e.count} interacciones)`
        : `${e.label}: ${formatTmr(e.value)} de promedio (sobre ${e.count})`,
    )
    .join(', ');
}

/**
 * Barras en SVG propio (TMR promedio por intent). `value: null` (ningún
 * mensaje respondido) se dibuja como un hueco punteado con "Sin respuestas",
 * nunca como una barra en 0 — eso se leería como "responde instantáneo".
 */
export function BarChart({ title, entries, reducedMotion }: BarChartProps) {
  const bars = barLayout(
    entries.map((e) => ({ key: e.key, value: e.value })),
    { width: CHART_W, height: CHART_H, gap: GAP },
  );
  const byKey = new Map(entries.map((e) => [e.key, e]));
  const uid = useId().replace(/[^A-Za-z0-9_-]/g, '');
  const titleId = `bar-title-${uid}`;
  const descId = `bar-desc-${uid}`;

  return (
    <div className="chart-bar">
      <svg
        className="chart-bar__svg"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-labelledby={titleId}
        aria-describedby={descId}
      >
        <title id={titleId}>{title}</title>
        <desc id={descId}>{description(entries)}</desc>
        <line x1={PAD_X} y1={PAD_TOP + CHART_H} x2={WIDTH - PAD_X} y2={PAD_TOP + CHART_H} className="chart-bar__baseline" />
        {bars.map((bar) => {
          const entry = byKey.get(bar.key);
          if (!entry) return null;
          const cx = PAD_X + bar.x + bar.width / 2;
          const baseY = PAD_TOP + CHART_H;
          return (
            <g key={bar.key} className="chart-bar__group">
              {bar.hasData ? (
                <rect
                  x={PAD_X + bar.x}
                  y={PAD_TOP + Math.min(bar.y, CHART_H - MIN_BAR_H)}
                  width={bar.width}
                  height={Math.max(bar.height, MIN_BAR_H)}
                  rx={4}
                  style={{ fill: entry.color }}
                  className={reducedMotion ? 'chart-bar__rect' : 'chart-bar__rect chart-bar__rect--animated'}
                />
              ) : (
                <rect
                  x={PAD_X + bar.x}
                  y={baseY - MIN_BAR_H}
                  width={bar.width}
                  height={MIN_BAR_H}
                  rx={2}
                  className="chart-bar__rect chart-bar__rect--empty"
                />
              )}
              <text x={cx} y={PAD_TOP - 8} textAnchor="middle" className="chart-bar__value">
                {entry.value === null ? 'Sin respuestas' : formatTmr(entry.value)}
              </text>
              <text x={cx} y={baseY + 18} textAnchor="middle" className="chart-bar__label">
                {entry.label}
              </text>
              <text x={cx} y={baseY + 33} textAnchor="middle" className="chart-bar__count">
                ({entry.count.toLocaleString('es-AR')})
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
