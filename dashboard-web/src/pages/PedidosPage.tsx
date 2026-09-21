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
import { ORDER_STATUSES, orderStatusMeta } from '@/lib/domain';
import { formatCurrency, formatDateTime } from '@/lib/format';

/** Polling en vivo: spec client-dashboard/metrics (3-5s). */
const POLL_INTERVAL = 4000;

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
            Órdenes que entran por el pipeline post-venta. La lista se actualiza sola cada 4
            segundos; hacé clic en una fila para ver el detalle.
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
            <div className="table-wrap">
              <table className="table">
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
                        className="table__row-click"
                        onClick={() => setDetailId(order.id)}
                      >
                        <td>
                          <div className="table__cell-main">{order.order_number}</div>
                        </td>
                        <td>
                          <div className="table__cell-main">{order.customer_name}</div>
                          <div className="table__cell-sub">{order.customer_email}</div>
                        </td>
                        <td>
                          <div className="table__cell-main">{order.product_name ?? '—'}</div>
                          <div className="table__cell-sub">{order.product_sku ?? '—'}</div>
                        </td>
                        <td>
                          <Badge tone={meta.tone}>{meta.label}</Badge>
                        </td>
                        <td className="table__num">{formatCurrency(order.total_amount)}</td>
                        <td className="table__dates">
                          <div>
                            <span className="table__dates-label">Recibido</span>
                            {formatDateTime(order.received_at)}
                          </div>
                          <div>
                            <span className="table__dates-label">Procesado</span>
                            {formatDateTime(order.processed_at)}
                          </div>
                          <div>
                            <span className="table__dates-label">Notificado</span>
                            {formatDateTime(order.notified_at)}
                          </div>
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