import { useId } from 'react';

import { donutArcs, type DonutSlice } from '@/lib/donutChart';

export interface DonutEntry extends DonutSlice {
  label: string;
}

interface DonutChartProps {
  /** Título accesible del gráfico completo (no de cada porción). */
  title: string;
  entries: DonutEntry[];
  centerValue?: string;
  centerLabel?: string;
  reducedMotion?: boolean;
}

const GEOMETRY = { cx: 50, cy: 50, outerR: 46, innerR: 27 };

/** "Confirmado: 30 (71%), Sin stock: 3 (7%), ..." — lo que lee un lector de pantalla vía `<desc>`. */
function donutDescription(entries: DonutEntry[]): string {
  const total = entries.reduce((sum, e) => sum + Math.max(0, e.value), 0);
  if (total <= 0) return 'Sin datos en este período.';
  return entries
    .map((e) => `${e.label}: ${e.value.toLocaleString('es-AR')} (${Math.round((Math.max(0, e.value) / total) * 100)}%)`)
    .join(', ');
}

/**
 * Dona en SVG propio con leyenda. Accesibilidad: el SVG lleva `role="img"` +
 * `<title>`/`<desc>` con el desglose exacto (igual criterio en BarChart y
 * StackedAreaChart) — es la fuente accesible. La leyenda de abajo es la misma
 * información para quien mira la pantalla; se marca `aria-hidden` para no
 * duplicar el anuncio de cada categoría en un lector de pantalla.
 */
export function DonutChart({ title, entries, centerValue, centerLabel, reducedMotion }: DonutChartProps) {
  const arcs = donutArcs(entries, GEOMETRY);
  const arcByKey = new Map(arcs.map((a) => [a.key, a]));
  const total = entries.reduce((sum, e) => sum + Math.max(0, e.value), 0);
  const uid = useId().replace(/[^A-Za-z0-9_-]/g, '');
  const titleId = `donut-title-${uid}`;
  const descId = `donut-desc-${uid}`;

  return (
    <div className="chart-donut">
      <div className="chart-donut__figure">
        <svg className="chart-donut__svg" viewBox="0 0 100 100" role="img" aria-labelledby={titleId} aria-describedby={descId}>
          <title id={titleId}>{title}</title>
          <desc id={descId}>{donutDescription(entries)}</desc>
          {arcs.length === 0 ? (
            <circle cx={50} cy={50} r={38} className="chart-donut__empty-ring" />
          ) : (
            arcs.map((arc) => (
              <path
                key={arc.key}
                d={arc.path}
                style={{ fill: arc.color }}
                className={reducedMotion ? 'chart-donut__slice' : 'chart-donut__slice chart-donut__slice--animated'}
              />
            ))
          )}
        </svg>
        {(centerValue || arcs.length === 0) && (
          <div className="chart-donut__center" aria-hidden="true">
            <strong>{arcs.length === 0 ? '—' : centerValue}</strong>
            {centerLabel && <span>{centerLabel}</span>}
          </div>
        )}
      </div>
      <ul className="chart-donut__legend" aria-hidden="true">
        {entries.map((entry) => {
          const percent = total > 0 ? Math.round((Math.max(0, entry.value) / total) * 100) : 0;
          return (
            <li key={entry.key}>
              <span className="chart-donut__swatch" style={{ background: entry.color }} />
              <span className="chart-donut__label">{entry.label}</span>
              <span className="chart-donut__count">
                {entry.value.toLocaleString('es-AR')}
                {arcByKey.has(entry.key) && <span className="chart-donut__percent"> · {percent}%</span>}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
