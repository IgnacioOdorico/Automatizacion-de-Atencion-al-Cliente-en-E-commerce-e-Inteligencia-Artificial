import { StatusIcon } from '@/components/workflow/StatusIcon';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import {
  EXECUTION_STATUS_FILTERS,
  executionModeLabel,
  executionStatusMeta,
} from '@/lib/executions';
import { formatDateTimeSeconds, formatEventClock, formatMs, formatRelative } from '@/lib/format';
import type { ExecutionSummary } from '@/types/monitoring';

interface ExecutionListProps {
  items: readonly ExecutionSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  /** Ids de ejecuciones que acaban de llegar (se resaltan un momento). */
  fresh: ReadonlySet<number>;
  nowMs: number;
  status: string;
  onStatusChange: (status: string) => void;
  hasMore: boolean;
  onLoadMore: () => void;
  loadingMore: boolean;
  moreError: boolean;
}

/**
 * Ejecuciones del workflow, de la más nueva a la más vieja. Cada una es un
 * botón: al elegirla se ilumina su camino en el diagrama. El error se muestra
 * como texto (viene de n8n, ya redactado por el backend).
 */
export function ExecutionList({
  items,
  selectedId,
  onSelect,
  fresh,
  nowMs,
  status,
  onStatusChange,
  hasMore,
  onLoadMore,
  loadingMore,
  moreError,
}: ExecutionListProps) {
  return (
    <section className="wf-runs card" aria-label="Ejecuciones del workflow">
      <header className="wf-runs__head">
        <h2 className="wf-section-title">Ejecuciones</h2>
        <div className="wf-runs-filter">
          <Select
            label="Estado"
            value={status}
            options={EXECUTION_STATUS_FILTERS.map((f) => ({ value: f.value, label: f.label }))}
            onChange={(e) => onStatusChange(e.target.value)}
          />
        </div>
      </header>

      {items.length === 0 ? (
        <div className="wf-runs__empty">
          <p>
            {status !== ''
              ? 'Ninguna ejecución coincide con el filtro.'
              : 'Todavía no hay ejecuciones de este workflow.'}
          </p>
          {status !== '' && (
            <Button variant="ghost" onClick={() => onStatusChange('')}>
              Quitar filtro
            </Button>
          )}
        </div>
      ) : (
        <ol className="wf-runs__list" aria-label="Ejecuciones, de la más nueva a la más vieja">
          {items.map((item) => {
            const meta = executionStatusMeta(item.status);
            const selected = item.id === selectedId;
            const classes = ['wf-run', `wf-run--${meta.tone}`];
            if (fresh.has(item.id)) classes.push('wf-run--fresh');
            return (
              <li key={item.id}>
                <button
                  type="button"
                  className={classes.join(' ')}
                  data-execution={item.id}
                  aria-current={selected ? 'true' : undefined}
                  onClick={() => onSelect(item.id)}
                >
                  <span className="wf-run__head">
                    <Badge tone={meta.tone}>
                      <StatusIcon name={meta.icon} />
                      {meta.label}
                    </Badge>
                    <span className="wf-run__id">#{item.id}</span>
                    <span className="wf-run__dur">{formatMs(item.duration_ms)}</span>
                  </span>
                  <span className="wf-run__meta">
                    <time dateTime={item.started_at} title={formatDateTimeSeconds(item.started_at)}>
                      {formatRelative(item.started_at, nowMs)} · {formatEventClock(item.started_at, nowMs)}
                    </time>
                    <span>{executionModeLabel(item.mode)}</span>
                  </span>
                  {item.error_message && <span className="wf-run__error">{item.error_message}</span>}
                </button>
              </li>
            );
          })}
        </ol>
      )}

      <div className="wf-runs-more">
        {moreError && (
          <p className="field__error" role="alert">
            No pudimos cargar más ejecuciones. Reintentá.
          </p>
        )}
        {hasMore ? (
          <Button variant="ghost" onClick={onLoadMore} loading={loadingMore}>
            Cargar ejecuciones anteriores
          </Button>
        ) : (
          items.length > 0 && <p className="mon-end">Esas son todas las ejecuciones registradas.</p>
        )}
      </div>
    </section>
  );
}
