import { QueryView } from '@/components/QueryView';
import { Skeleton } from '@/components/ui/Skeleton';
import { summaryKpis } from '@/lib/monitoringSummary';
import type { MonitoringSummary } from '@/types/monitoring';

interface SummaryQuery {
  data: MonitoringSummary | undefined;
  isError: boolean;
  error: unknown;
  isFetching: boolean;
  refetch: () => unknown;
}

function KpiSkeleton() {
  return (
    <div className="mon-kpis" aria-hidden="true">
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} className="mon-kpi">
          <Skeleton height={11} width="62%" />
          <Skeleton height={26} width="40%" style={{ marginTop: 8 }} />
          <Skeleton height={11} width="52%" style={{ marginTop: 6 }} />
        </div>
      ))}
    </div>
  );
}

/** Franja de indicadores de las últimas horas (GET /monitoring/summary). */
export function KpiStrip({ query }: { query: SummaryQuery }) {
  return (
    <QueryView query={query} loading={<KpiSkeleton />} smallError>
      {(summary) => (
        <div className="mon-kpis">
          {summaryKpis(summary).map((kpi) => {
            const classes = ['mon-kpi'];
            if (kpi.tone) classes.push(`mon-kpi--${kpi.tone}`);
            if (kpi.id === 'executions') classes.push('mon-kpi--text');
            return (
              <div key={kpi.id} className={classes.join(' ')}>
                <div className="mon-kpi__label">{kpi.label}</div>
                <div className="mon-kpi__value">
                  {kpi.parts
                    ? kpi.parts.map((part, i) => (
                        <span key={i} className={part.tone ? `mon-kpi__part--${part.tone}` : undefined}>
                          {part.text}
                        </span>
                      ))
                    : kpi.value}
                </div>
                {kpi.hint && <div className="mon-kpi__hint">{kpi.hint}</div>}
              </div>
            );
          })}
        </div>
      )}
    </QueryView>
  );
}
