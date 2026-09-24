import { useQuery } from '@tanstack/react-query';

import { metricsApi } from '@/api/endpoints';
import { QueryView } from '@/components/QueryView';
import { PackageIcon } from '@/components/icons';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { StatCards } from '@/components/metrics/StatCards';
import { DonutChart } from '@/components/metrics/DonutChart';
import { StackedAreaChart } from '@/components/metrics/StackedAreaChart';
import { ORDER_STATUSES, orderStatusMeta } from '@/lib/domain';
import { formatRelative, formatTmr } from '@/lib/format';
import { ordersDataSourceParam, ordersIsEmpty } from '@/lib/metricsFilters';
import { orderStatusColor } from '@/lib/chartColors';
import { useNow } from '@/hooks/useNow';
import type { OrdersDailyPoint, OrdersMetrics } from '@/types/metrics';

/** Menos seguido que el feed de Monitoreo (3 s): esto es una agregación, no un evento puntual. */
const POLL_MS = 10_000;
/** Subconjunto deliberado del dominio para el apilado diario (ver docs/API_METRICAS.md §1). */
const DAILY_STATUS_KEYS = ['confirmed', 'shipped', 'delivered', 'no_stock', 'cancelled', 'error'] as const;

function OrdersSkeleton() {
  return (
    <div aria-hidden="true">
      <div className="stat-grid">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="card stat-card stat-card--skeleton">
            <Skeleton height={11} width="46%" />
            <Skeleton height={26} width="38%" style={{ marginTop: 10 }} />
          </div>
        ))}
      </div>
      <div className="metrics-charts">
        <div className="metrics-chart-card chart-skeleton" />
        <div className="metrics-chart-card metrics-chart-card--wide chart-skeleton" />
      </div>
    </div>
  );
}

/** Los mismos 6 campos de `daily`, como mapa clave→valor (lo que pide StackedAreaChart). */
function dailyValues(d: OrdersDailyPoint): Record<string, number> {
  return {
    confirmed: d.confirmed,
    shipped: d.shipped,
    delivered: d.delivered,
    no_stock: d.no_stock,
    cancelled: d.cancelled,
    error: d.error,
  };
}

function buildStatCards(data: OrdersMetrics) {
  return [
    { id: 'mttd', label: 'MTTD promedio', value: formatTmr(data.avg_mttd_seconds), hint: 'Recibido → procesado.' },
    { id: 'mttr', label: 'MTTR promedio', value: formatTmr(data.avg_mttr_seconds), hint: 'Procesado → avisado.' },
    {
      id: 'e2e',
      label: 'Extremo a extremo',
      value: formatTmr(data.avg_end_to_end_seconds),
      hint: 'Recibido → avisado.',
    },
    { id: 'total', label: 'Órdenes totales', value: data.total_orders.toLocaleString('es-AR') },
  ];
}

interface OrdersMetricsSectionProps {
  hours?: number;
  dataSource: string;
  reducedMotion: boolean;
}

/** Bloque "Pedidos": reemplazo en vivo de MTTD/MTTR/end-to-end, distribución de estados y serie diaria. */
export function OrdersMetricsSection({ hours, dataSource, reducedMotion }: OrdersMetricsSectionProps) {
  const now = useNow(1000);
  const query = useQuery({
    queryKey: ['metrics-orders', hours, dataSource],
    queryFn: () => metricsApi.orders({ hours, data_source: ordersDataSourceParam(dataSource) }),
    refetchInterval: POLL_MS,
  });

  return (
    <section className="card metrics-block" aria-labelledby="metrics-orders-title">
      <div className="metrics-block__head">
        <h2 className="metrics-block__title" id="metrics-orders-title">
          Pedidos
        </h2>
        {query.dataUpdatedAt > 0 && (
          <span className="metrics-updated">Actualizado {formatRelative(new Date(query.dataUpdatedAt).toISOString(), now)}</span>
        )}
      </div>

      <QueryView
        query={query}
        loading={<OrdersSkeleton />}
        isEmpty={ordersIsEmpty}
        empty={
          <EmptyState
            icon={<PackageIcon width={24} height={24} />}
            title="Todavía no hay pedidos para este período"
            text="Probá una ventana más amplia o esperá a que entren pedidos nuevos: el bloque se actualiza solo."
          />
        }
      >
        {(data) => (
          <>
            <StatCards cards={buildStatCards(data)} />
            <div className="metrics-charts">
              <div className="metrics-chart-card">
                <h3 className="metrics-chart-card__title">Distribución de estados</h3>
                <DonutChart
                  title="Distribución de estados de pedidos"
                  entries={ORDER_STATUSES.map((status) => ({
                    key: status,
                    label: orderStatusMeta(status).label,
                    value: data.by_status[status] ?? 0,
                    color: orderStatusColor(status),
                  }))}
                  centerValue={data.total_orders.toLocaleString('es-AR')}
                  centerLabel="pedidos"
                  reducedMotion={reducedMotion}
                />
              </div>
              <div className="metrics-chart-card metrics-chart-card--wide">
                <h3 className="metrics-chart-card__title">Órdenes por día</h3>
                <StackedAreaChart
                  title="Órdenes por día, por estado"
                  rows={data.daily.map((d) => ({ date: d.date, values: dailyValues(d) }))}
                  series={DAILY_STATUS_KEYS.map((key) => ({
                    key,
                    label: orderStatusMeta(key).label,
                    color: orderStatusColor(key),
                  }))}
                  reducedMotion={reducedMotion}
                />
              </div>
            </div>
          </>
        )}
      </QueryView>
    </section>
  );
}
