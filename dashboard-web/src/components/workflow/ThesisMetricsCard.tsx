import { useQuery } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { QueryView } from '@/components/QueryView';
import { Skeleton } from '@/components/ui/Skeleton';
import { thesisMetrics } from '@/lib/thesisMetrics';
import type { Summary } from '@/types/api';

/** Los promedios se refrescan solos, igual que en el Dashboard. */
const SUMMARY_POLL_MS = 10_000;

function MetricsSkeleton() {
  return (
    <div className="wf-metrics__list" aria-hidden="true">
      {Array.from({ length: 3 }, (_, i) => (
        <div key={i} className="wf-metric">
          <Skeleton height={12} width="30%" />
          <Skeleton height={28} width="44%" style={{ marginTop: 8 }} />
          <Skeleton height={12} width="90%" style={{ marginTop: 10 }} />
        </div>
      ))}
    </div>
  );
}

/** El conjunto de métricas con su definición real y el valor actual (o guiones si no hay datos). */
function MetricsList({ summary }: { summary: Summary | undefined }) {
  return (
    <ul className="wf-metrics__list">
      {thesisMetrics(summary).map((metric) => (
        <li key={metric.id} className="wf-metric">
          <div className="wf-metric__head">
            <span className="wf-metric__short">{metric.short}</span>
            <span className="wf-metric__flow">{metric.flow}</span>
          </div>
          <strong className="wf-metric__value">{metric.value}</strong>
          <p className="wf-metric__name">{metric.name}</p>
          <p className="wf-metric__measures">{metric.measures}</p>
          <p className="wf-metric__formula">
            <code>
              {metric.to} − {metric.from}
            </code>
          </p>
          <p className="wf-metric__sample">{metric.sample}</p>
        </li>
      ))}
    </ul>
  );
}

/**
 * Tarjeta didáctica de las métricas de la tesis (MTTD, MTTR, TMR): qué mide
 * cada una, con la definición de las vistas de la base, y su promedio actual.
 * Es independiente del diagrama: no depende de qué nodos tenga el workflow.
 */
export function ThesisMetricsCard() {
  const query = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => dashboardApi.summary(),
    refetchInterval: SUMMARY_POLL_MS,
  });

  return (
    <section className="wf-metrics card" aria-labelledby="wf-metrics-title">
      <h2 className="wf-section-title" id="wf-metrics-title">
        Métricas de la tesis
      </h2>
      <p className="wf-metrics__intro">
        El workflow guarda una marca de tiempo en cada paso importante. Restando esas marcas se calculan estos tres
        promedios.
      </p>
      <QueryView query={query} loading={<MetricsSkeleton />} smallError>
        {(summary) => <MetricsList summary={summary} />}
      </QueryView>
    </section>
  );
}
