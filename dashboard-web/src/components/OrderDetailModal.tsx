import { useEffect, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { Badge } from '@/components/ui/Badge';
import { ErrorState } from '@/components/ui/ErrorState';
import { Spinner } from '@/components/ui/Spinner';
import { orderStatusMeta } from '@/lib/domain';
import { dataSourceLabel, formatCurrency, formatDateTime } from '@/lib/format';
import { describePayload, orderItemProduct } from '@/lib/orderDetail';

interface OrderDetailModalProps {
  orderId: number | null;
  onClose: () => void;
}

function DlItem({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="dl__item">
      <dt className="dl__label">{label}</dt>
      <dd className="dl__value">{value ?? '—'}</dd>
    </div>
  );
}

/** Datos con que entró el pedido: campos legibles y, aparte, el JSON crudo. */
function PayloadView({ raw }: { raw: unknown }) {
  const view = describePayload(raw);

  switch (view.kind) {
    case 'empty':
      return <p className="modal__muted">No se guardaron los datos originales de este pedido.</p>;
    case 'text':
      return <p className="modal__text modal__text--flat">{view.text}</p>;
    case 'json':
      return <pre className="json-block">{view.json}</pre>;
    default:
      return (
        <>
          <dl className="dl dl--compact">
            {view.fields.map((field) => (
              <DlItem key={field.key} label={field.label} value={field.value} />
            ))}
          </dl>
          <details className="raw-json">
            <summary>Ver JSON completo</summary>
            <pre className="json-block">{view.json}</pre>
          </details>
        </>
      );
  }
}

/**
 * Detalle de pedido (GET /orders/{id}): datos completos + order_items + los
 * datos originales del pedido (raw_payload JSONB del webhook) en campos legibles.
 */
export function OrderDetailModal({ orderId, onClose }: OrderDetailModalProps) {
  const { data, isPending, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['order', orderId],
    queryFn: () => dashboardApi.order(orderId as number),
    enabled: orderId !== null,
  });

  useEffect(() => {
    if (orderId === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [orderId, onClose]);

  if (orderId === null) return null;

  const statusMeta = data ? orderStatusMeta(data.status) : null;

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal" role="dialog" aria-modal="true" aria-label="Detalle de pedido">
        <header className="modal__head">
          <div>
            <h3>{data?.order_number ?? `Pedido #${orderId}`}</h3>
            {statusMeta && <Badge tone={statusMeta.tone}>{statusMeta.label}</Badge>}
          </div>
          <button type="button" className="modal__close" onClick={onClose} aria-label="Cerrar">
            ×
          </button>
        </header>

        <div className="modal__body">
          {isPending && (
            <div className="modal__loading">
              <Spinner />
              Cargando detalle…
            </div>
          )}

          {isError && (
            <ErrorState small error={error} onRetry={() => void refetch()} retrying={isFetching} />
          )}

          {data && (
            <>
              <dl className="dl">
                <DlItem label="Cliente" value={data.customer_name} />
                <DlItem label="Email" value={data.customer_email} />
                <DlItem label="Teléfono" value={data.customer_phone} />
                <DlItem label="Producto" value={data.product_name} />
                <DlItem label="SKU" value={data.product_sku} />
                <DlItem label="Cantidad" value={data.quantity} />
                <DlItem label="Total" value={formatCurrency(data.total_amount)} />
                <DlItem label="Origen del dato" value={dataSourceLabel(data.data_source)} />
                <DlItem label="Recibido" value={formatDateTime(data.received_at)} />
                <DlItem label="Procesado" value={formatDateTime(data.processed_at)} />
                <DlItem label="Notificado" value={formatDateTime(data.notified_at)} />
              </dl>

              {data.order_items.length > 0 && (
                <div className="modal__section">
                  <h4>Ítems de la orden</h4>
                  <div className="table-wrap">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Producto</th>
                          <th className="table__num">Cantidad</th>
                          <th className="table__num">P. unitario</th>
                          <th className="table__num">Subtotal</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.order_items.map((item) => (
                          <tr key={item.id}>
                            <td>{orderItemProduct(item, data.order_items.length, data)}</td>
                            <td className="table__num">{item.quantity}</td>
                            <td className="table__num">{formatCurrency(item.unit_price)}</td>
                            <td className="table__num">{formatCurrency(item.subtotal)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="modal__section">
                <h4>Datos originales del pedido</h4>
                <PayloadView raw={data.raw_payload} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}