import { useId } from 'react';
import { Link } from 'react-router-dom';

import { SEVERITY_ICONS } from '@/components/monitoring/eventIcons';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { conversationSearch } from '@/lib/conversations';
import { describeEvent, severityMeta } from '@/lib/monitoring';
import { MONITORING_BASE_PATH } from '@/lib/monitoringTabs';
import type { MonitoringEvent } from '@/types/monitoring';

interface EventDetailModalProps {
  event: MonitoringEvent;
  onClose: () => void;
  /** Abre el detalle del pedido existente (la pantalla cierra este diálogo antes). */
  onOpenOrder: (orderId: number) => void;
}

const CONVERSATION_TYPES = new Set(['chat_message', 'bot_reply', 'ticket_created']);

/**
 * Detalle de un evento: todos los datos exactos (el texto del cliente y de la
 * respuesta completos, sin recortar y como texto) y los enlaces a lo vinculado:
 * pedido, ticket y conversación.
 */
export function EventDetailModal({ event, onClose, onOpenOrder }: EventDetailModalProps) {
  const titleId = useId();
  const view = describeEvent(event);
  const severity = severityMeta(event.severity);
  const SeverityIcon = SEVERITY_ICONS[severity.icon];

  const inline = view.facts.filter((f) => !f.block);
  const blocks = view.facts.filter((f) => f.block);

  const userId = typeof event.data.user_id === 'string' ? event.data.user_id : null;
  const conversationLink =
    event.channel && userId && CONVERSATION_TYPES.has(event.type)
      ? { pathname: `${MONITORING_BASE_PATH}/conversaciones`, search: conversationSearch(event.channel, userId) }
      : null;
  const { order_id: orderId, order_number: orderNumber, ticket_id: ticketId } = event.refs;
  const showTicket = ticketId !== null || event.type === 'ticket_created';

  return (
    <Modal labelledBy={titleId} onClose={onClose}>
      <header className="modal__head">
        <div>
          <h3 id={titleId}>{view.typeLabel}</h3>
          <Badge tone={severity.tone}>
            <SeverityIcon width={12} height={12} aria-hidden="true" />
            {severity.label}
          </Badge>
        </div>
        <button type="button" className="modal__close" onClick={onClose} aria-label="Cerrar">
          ×
        </button>
      </header>

      <div className="modal__body">
        <dl className="dl">
          {inline.map((fact) => (
            <div key={fact.label} className="dl__item">
              <dt className="dl__label">{fact.label}</dt>
              <dd className="dl__value">{fact.value}</dd>
            </div>
          ))}
        </dl>

        {blocks.map((fact) => (
          <div key={fact.label} className="modal__section">
            <h4>{fact.label}</h4>
            <p
              className={`mon-quote mon-detail-quote${event.type === 'bot_reply' ? ' mon-quote--bot' : ''}`}
              dir="auto"
            >
              {fact.value}
            </p>
          </div>
        ))}

        {(orderId !== null || showTicket || conversationLink) && (
          <div className="mon-detail-links">
            {orderId !== null && (
              <Button variant="ghost" onClick={() => onOpenOrder(orderId)}>
                {orderNumber ? `Ver pedido ${orderNumber}` : 'Ver pedido'}
              </Button>
            )}
            {showTicket && (
              <Link className="btn btn--ghost" to="/tickets">
                Ver en Tickets
              </Link>
            )}
            {conversationLink && (
              <Link className="btn btn--ghost" to={conversationLink}>
                Ver la conversación
              </Link>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
