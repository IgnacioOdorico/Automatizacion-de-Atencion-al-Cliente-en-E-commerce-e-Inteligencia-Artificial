import type { CSSProperties } from 'react';

interface SkeletonProps {
  height?: number | string;
  width?: number | string;
  radius?: number | string;
  className?: string;
  style?: CSSProperties;
}

/** Bloque gris con brillo: reserva el espacio del contenido mientras carga. */
export function Skeleton({ height = 14, width = '100%', radius, className, style }: SkeletonProps) {
  return (
    <span
      className={['skeleton', className].filter(Boolean).join(' ')}
      style={{ display: 'block', height, width, borderRadius: radius, ...style }}
    />
  );
}

/** Anchos fijos (no aleatorios) para que el esqueleto no "baile" entre renders. */
const CELL_WIDTHS = ['72%', '55%', '84%', '48%', '64%', '58%'];

interface TableSkeletonProps {
  columns?: number;
  rows?: number;
}

/** Esqueleto de una tabla: mismo marco y alto de fila que `.table` para no saltar al cargar. */
export function TableSkeleton({ columns = 5, rows = 7 }: TableSkeletonProps) {
  const cols = Array.from({ length: columns }, (_, i) => i);
  const template = { gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` };

  return (
    <div className="table-wrap table-skeleton" aria-hidden="true">
      <div className="table-skeleton__row table-skeleton__row--head" style={template}>
        {cols.map((c) => (
          <Skeleton key={c} height={10} width="40%" />
        ))}
      </div>
      {Array.from({ length: rows }, (_, r) => (
        <div key={r} className="table-skeleton__row" style={template}>
          {cols.map((c) => (
            <Skeleton key={c} height={12} width={CELL_WIDTHS[(r + c) % CELL_WIDTHS.length]} />
          ))}
        </div>
      ))}
    </div>
  );
}
