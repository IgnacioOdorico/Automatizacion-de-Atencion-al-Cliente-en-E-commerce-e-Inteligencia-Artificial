import { useState } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { LiveBadge } from '@/components/LiveBadge';
import { OrderDetailModal } from '@/components/OrderDetailModal';
import { Pagination } from '@/components/Pagination';
import { PackageIcon } from '@/components/icons';
import { QueryView } from '@/components/QueryView';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Select, type SelectOption } from '@/components/ui/Select';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { useFreshRows } from '@/hooks/useFreshRows';
import { ORDER_STATUSES, orderStatusMeta } from '@/lib/domain';
import { formatCurrency, formatDateTime } from '@/lib/format';
import type { Order } from '@/types/api';

/** Polling en vivo: spec client-dashboard/metrics (3-5s). */
const POLL_INTERVAL = 4000;

/** Solo los hitos que ya ocurrieron: un pedido sin procesar no muestra guiones de relleno. */
function orderTimeline(order: Order): Array<{ label: string; at: string }> {
  const steps: Array<[string, string | null]> = [
    ['Recibido', order.received_at],
    ['Procesado', order.processed_at],
    ['Notificado', order.notified_at],
  ];
  return steps.flatMap(([label, at]) => (at ? [{ label, at }] : []));
}

const STATUS_OPTIONS: SelectOption[] = [
  { value: '', label: 'Todos los estados' },
  ...ORDER_STATUSES.map((status) => ({ value: status, label: orderStatusMeta(status).label })),
];

export function PedidosPage() {
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [detailId, setDetailId] = useState<number | null>(null);

  const query = useQuery({
    queryKey: ['orders', statusFilter, page],
    queryFn: () => dashboardApi.orders({ status: statusFilter || undefined, page }),
    refetchInterval: POLL_INTERVAL,
    placeholderData: keepPreviousData,
  });
  const { refetch } = query;

  // Pedido que entra entre dos polls: se resalta unos segundos (efecto "en vivo").
  const orderIds = query.data?.items.map((order) => order.id);
  const freshIds = useFreshRows(
    `${statusFilter}|${page}`,
    query.isPlaceholderData ? undefined : orderIds,
  );

  const changeStatus = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  const filterMeta = statusFilter ? orderStatusMeta(statusFilter) : null;

  return (
    <div className="page">
      <header className="page__head page__head--row">
        <div>
          <h1>Pedidos</h1>
          <p className="page__sub">
            Los pedidos de tu tienda con su estado de procesamiento. La lista se actualiza sola
            cada 4 segundos; hacé clic en uno para ver el detalle.
          </p>
        </div>
        <LiveBadge paused={query.isError} />
      </header>

      <div className="filters">
        <Select
          label="Estado"
          value={statusFilter}
          options={STATUS_OPTIONS}
          onChange={(e) => changeStatus(e.target.value)}
        />
        <Button variant="ghost" onClick={() => refetch()}>
          Actualizar
        </Button>
      </div>

      <QueryView
        query={query}
        loading={<TableSkeleton columns={6} rows={8} />}
        isEmpty={(data) => data.items.length === 0}
        empty={
          <EmptyState
            icon={<PackageIcon width={24} height={24} />}
            title={
              filterMeta ? `Sin pedidos en estado "${filterMeta.label}"` : 'Sin pedidos todavía'
            }
            text={
              filterMeta
                ? 'Probá con otro estado o quitá el filtro para ver el listado completo.'
                : 'Cuando entre un pedido nuevo, va a aparecer acá sin recargar la página.'
            }
          />
        }
      >
        {(data) => (
          <>
            <div className={`table-wrap${query.isPlaceholderData ? ' is-refreshing' : ''}`}>
              <table className="table table--stack table--compact">
                <thead>
                  <tr>
                    <th>Pedido</th>
                    <th>Cliente</th>
                    <th>Producto</th>
                    <th>Estado</th>
                    <th className="table__num">Total</th>
                    <th>Fechas</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((order) => {
                    const meta = orderStatusMeta(order.status);
                    return (
                      <tr
                        key={order.id}
                        className={`table__row-click${freshIds.has(order.id) ? ' table__row-fresh' : ''}`}
                        onClick={() => setDetailId(order.id)}
                      >
                        <td data-label="Pedido">
                          <button
                            type="button"
                            className="table__link"
                            aria-label={`Ver detalle del pedido ${order.order_number}`}
                            onClick={() => setDetailId(order.id)}
                          >
                            {order.order_number}
                          </button>
                        </td>
                        <td data-label="Cliente">
                          <div className="table__cell-main" title={order.customer_name}>
                            {order.customer_name}
                          </div>
                          <div className="table__cell-sub" title={order.customer_email}>
                            {order.customer_email}
                          </div>
                        </td>
                        <td data-label="Producto">
                          <div className="table__cell-main" title={order.product_name ?? undefined}>
                            {order.product_name ?? '—'}
                          </div>
                          <div className="table__cell-sub">{order.product_sku ?? '—'}</div>
                        </td>
                        <td data-label="Estado">
                          <Badge tone={meta.tone}>{meta.label}</Badge>
                        </td>
                        <td className="table__num" data-label="Total">
                          {formatCurrency(order.total_amount)}
                        </td>
                        <td className="table__dates" data-label="Fechas">
                          {orderTimeline(order).map((step) => (
                            <div key={step.label}>
                              <span className="table__dates-label">{step.label}</span>
                              {formatDateTime(step.at)}
                            </div>
                          ))}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <Pagination
              page={data.page}
              totalPages={data.total_pages}
              total={data.total}
              onPageChange={setPage}
            />
          </>
        )}
      </QueryView>

      <OrderDetailModal orderId={detailId} onClose={() => setDetailId(null)} />
    </div>
  );
}