import { useId } from 'react';

import { axisTickIndices, isoDateShortLabel } from '@/lib/chartAxis';
import { stackedAreaLayers, type SeriesPoint } from '@/lib/areaChart';

export interface AreaSeriesDef {
  key: string;
  label: string;
  color: string;
}

interface StackedAreaChartProps {
  title: string;
  rows: SeriesPoint[];
  series: AreaSeriesDef[];
  reducedMotion?: boolean;
}

const WIDTH = 480;
const HEIGHT = 180;
const PADDING = 14;
const AXIS_Y_OFFSET = 16;
const MAX_TICKS = 6;

function seriesTotal(rows: SeriesPoint[], key: string): number {
  return rows.reduce((sum, r) => sum + (r.values[key] ?? 0), 0);
}

function description(rows: SeriesPoint[], series: AreaSeriesDef[]): string {
  if (rows.length === 0) return 'Sin datos en este período.';
  const totals = series.map((s) => `${s.label}: ${seriesTotal(rows, s.key).toLocaleString('es-AR')}`).join(', ');
  const span = rows.length === 1 ? rows[0].date : `${rows[0].date} a ${rows[rows.length - 1].date}`;
  return `Serie diaria del ${span}. Totales del período — ${totals}.`;
}

/**
 * Área apilada en SVG propio (serie diaria por estado/canal). Los huecos ya
 * vienen rellenos en 0 desde la API; con una sola muestra, `stackedAreaLayers`
 * dibuja un tramo plano en todo el ancho en vez de un punto invisible.
 */
export function StackedAreaChart({ title, rows, series, reducedMotion }: StackedAreaChartProps) {
  const geometry = { width: WIDTH, height: HEIGHT - AXIS_Y_OFFSET, padding: PADDING };
  const { layers, xTicks } = stackedAreaLayers(rows, series.map((s) => s.key), geometry);
  const colorByKey = new Map(series.map((s) => [s.key, s.color]));
  const uid = useId().replace(/[^A-Za-z0-9_-]/g, '');
  const titleId = `area-title-${uid}`;
  const descId = `area-desc-${uid}`;
  const tickIndices = axisTickIndices(xTicks.length, MAX_TICKS);

  return (
    <div className="chart-area">
      <svg className="chart-area__svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-labelledby={titleId} aria-describedby={descId}>
        <title id={titleId}>{title}</title>
        <desc id={descId}>{description(rows, series)}</desc>
        {layers.map((layer) => (
          <path
            key={layer.key}
            d={layer.path}
            style={{ fill: colorByKey.get(layer.key) }}
            className={reducedMotion ? 'chart-area__layer' : 'chart-area__layer chart-area__layer--animated'}
          />
        ))}
        {tickIndices.map((i) => (
          <text key={xTicks[i].date} x={xTicks[i].x} y={HEIGHT - 2} textAnchor="middle" className="chart-area__tick">
            {isoDateShortLabel(xTicks[i].date)}
          </text>
        ))}
      </svg>
      <ul className="chart-area__legend" aria-hidden="true">
        {series.map((s) => (
          <li key={s.key}>
            <span className="chart-donut__swatch" style={{ background: s.color }} />
            <span>{s.label}</span>
            <strong>{seriesTotal(rows, s.key).toLocaleString('es-AR')}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}
