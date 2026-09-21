import { memo, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { ApiError } from '@/api/client';
import { CHANNEL_ICONS } from '@/components/channelIcons';
import { AlertIcon, ChevronLeftIcon, MessengerIcon } from '@/components/icons';
import { OrderDetailModal } from '@/components/OrderDetailModal';
import { QueryView } from '@/components/QueryView';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { useNow } from '@/hooks/useNow';
import { useThread } from '@/hooks/useThread';
import { threadDays, replyChips, type ConversationRef } from '@/lib/conversations';
import { orderStatusMeta, priorityMeta, ticketStatusMeta } from '@/lib/domain';
import { CHANNEL_LABELS, formatContact, formatTime } from '@/lib/format';
import type { ThreadItem } from '@/types/monitoring';

interface ConversationThreadProps {
  conversation: ConversationRef;
  /** Vuelve a la lista (en móvil el hilo ocupa toda la pantalla). */
  onBack: () => void;
}

const BACK_LABEL = 'Volver a las conversaciones';

function BackButton({ onBack }: { onBack: () => void }) {
  return (
    <Button variant="ghost" className="mon-chat__back" onClick={onBack}>
      <ChevronLeftIcon width={16} height={16} aria-hidden="true" />
      {BACK_LABEL}
    </Button>
  );
}

function ThreadSkeleton() {
  return (
    <div className="mon-chat__skeleton" aria-hidden="true">
      <Skeleton height={44} width="58%" radius={14} />
      <Skeleton height={64} width="66%" radius={14} style={{ marginLeft: 'auto' }} />
      <Skeleton height={44} width="46%" radius={14} />
      <Skeleton height={64} width="70%" radius={14} style={{ marginLeft: 'auto' }} />
    </div>
  );
}

interface ExchangeProps {
  item: ThreadItem;
  onOpenOrder: (orderId: number) => void;
}

/**
 * Un intercambio: el mensaje del cliente a un lado y la respuesta del bot al
 * otro, con su hora, intent, urgencia y TMR, y los enlaces al pedido o ticket
 * vinculados. Los textos van exactos y como texto de React (nunca como HTML).
 */
const Exchange = memo(function Exchange({ item, onOpenOrder }: ExchangeProps) {
  const chips = replyChips(item);
  const order = item.order;
  const ticket = item.ticket;

  return (
    <div className="mon-exchange">
      <div className="mon-bubble mon-bubble--customer">
        <span className="sr-only">El cliente escribió:</span>
        <p className="mon-bubble__text" dir="auto">
          {item.message}
        </p>
        <div className="mon-bubble__meta">
          <span>{formatTime(item.received_at)}</span>
        </div>
      </div>

      {item.responded_at ? (
        <div className="mon-bubble mon-bubble--bot">
          <span className="sr-only">El bot respondió:</span>
          <p className="mon-bubble__text" dir="auto">
            {item.ai_response ?? '—'}
          </p>
          <div className="mon-bubble__meta">
            <span>{formatTime(item.responded_at)}</span>
            {chips.map((chip) => (
              <Badge key={chip.text} tone={chip.tone}>
                {chip.text}
              </Badge>
            ))}
          </div>
        </div>
      ) : (
        <div className="mon-bubble mon-bubble--bot mon-bubble--pending">
          <p className="mon-bubble__text">El bot todavía no respondió</p>
        </div>
      )}

      {(order || ticket) && (
        <div className="mon-exchange__links">
          {order && (
            <button type="button" className="mon-linkchip" onClick={() => onOpenOrder(order.id)}>
              {`Pedido ${order.order_number} · ${orderStatusMeta(order.status).label}`}
            </button>
          )}
          {ticket && (
            <Link className="mon-linkchip" to="/tickets">
              {[
                `Ticket #${ticket.id}`,
                ticket.priority ? `Prioridad ${priorityMeta(ticket.priority).label.toLowerCase()}` : null,
                ticket.status ? ticketStatusMeta(ticket.status).label : null,
              ]
                .filter(Boolean)
                .join(' · ')}
            </Link>
          )}
        </div>
      )}
    </div>
  );
});

/**
 * Panel del hilo abierto: estilo chat, con separadores por día, "Cargar mensajes
 * anteriores" y refresco automático cada 5 s. Se monta con `key` = conversación.
 */
export function ConversationThread({ conversation, onBack }: ConversationThreadProps) {
  const { query, loadOlder, loadingOlder, olderError } = useThread(conversation);
  const [orderId, setOrderId] = useState<number | null>(null);
  const now = useNow(30_000);
  const ChannelIcon = CHANNEL_ICONS[conversation.channel];

  const scrollRef = useRef<HTMLDivElement>(null);
  /** Si estás leyendo lo último, un mensaje nuevo baja solo; si subiste a leer, no te mueve. */
  const stickToBottom = useRef(true);

  const items = query.data?.items;
  const count = items?.length ?? 0;
  useEffect(() => {
    const el = scrollRef.current;
    if (el && stickToBottom.current) el.scrollTop = el.scrollHeight;
  }, [count]);

  const days = useMemo(() => threadDays(items ?? [], now), [items, now]);
  const hasUrgent = items?.some((i) => i.is_urgent) ?? false;

  const notFound = query.error instanceof ApiError && query.error.status === 404 && !query.data;

  return (
    <div className="mon-chat__inner">
      <header className="mon-chat__head">
        <BackButton onBack={onBack} />
        <span className="mon-conv__avatar" aria-hidden="true">
          <ChannelIcon width={18} height={18} />
        </span>
        <div className="mon-chat__who">
          <h3>{formatContact(conversation.channel, conversation.userId)}</h3>
          <div className="mon-chat__tags">
            <Badge tone="neutral">{CHANNEL_LABELS[conversation.channel] ?? conversation.channel}</Badge>
            {hasUrgent && (
              <Badge tone="danger">
                <AlertIcon width={12} height={12} aria-hidden="true" />
                Tuvo mensajes urgentes
              </Badge>
            )}
          </div>
        </div>
      </header>

      {notFound ? (
        <div className="mon-chat__body">
          <EmptyState
            icon={<MessengerIcon width={24} height={24} />}
            title="Esa conversación no existe o todavía no tiene mensajes"
            text="Volvé a la lista y elegí otra."
            action={<BackButton onBack={onBack} />}
          />
        </div>
      ) : (
        <div
          className="mon-chat__body"
          ref={scrollRef}
          onScroll={(e) => {
            const el = e.currentTarget;
            stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
          }}
        >
          <QueryView query={query} loading={<ThreadSkeleton />} smallError>
            {(thread) => (
              <>
                {thread.hasOlder && (
                  <div className="mon-more">
                    {olderError !== null && (
                      <p className="field__error" role="alert">
                        No pudimos cargar los mensajes anteriores. Reintentá.
                      </p>
                    )}
                    <Button variant="ghost" onClick={() => void loadOlder()} loading={loadingOlder}>
                      Cargar mensajes anteriores
                    </Button>
                  </div>
                )}
                {days.map((day) => (
                  <section key={day.key} className="mon-daygroup">
                    <h4 className="mon-day">
                      <span>{day.label}</span>
                    </h4>
                    {day.items.map((item) => (
                      <Exchange key={item.interaction_id} item={item} onOpenOrder={setOrderId} />
                    ))}
                  </section>
                ))}
              </>
            )}
          </QueryView>
        </div>
      )}

      <OrderDetailModal orderId={orderId} onClose={() => setOrderId(null)} />
    </div>
  );
}
