import { useCallback, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { monitoringApi } from '@/api/endpoints';
import { ActivityIcon, PauseIcon, PlayIcon } from '@/components/icons';
import { BotStatus } from '@/components/monitoring/BotStatus';
import { EventCard } from '@/components/monitoring/EventCard';
import { EventDetailModal } from '@/components/monitoring/EventDetailModal';
import { EventFilters } from '@/components/monitoring/EventFilters';
import { KpiStrip } from '@/components/monitoring/KpiStrip';
import { OrderDetailModal } from '@/components/OrderDetailModal';
import { QueryView } from '@/components/QueryView';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { useEventFeed } from '@/hooks/useEventFeed';
import { useNow } from '@/hooks/useNow';
import { useScrolledAway } from '@/hooks/useScrolledAway';
import { cardTick, latestIso } from '@/lib/monitoringSummary';
import type { Channel } from '@/types/api';
import type { EventType, MonitoringEvent } from '@/types/monitoring';

/** El resumen (KPIs) se refresca más lento que el feed. */
const SUMMARY_POLL_MS = 5000;

function FeedSkeleton() {
  return (
    <ol className="mon-feed" aria-hidden="true">
      {Array.from({ length: 4 }, (_, i) => (
        <li key={i} className="mon-event mon-event--skeleton">
          <Skeleton height={40} width={40} radius={12} />
          <div>
            <Skeleton height={12} width="34%" />
            <Skeleton height={16} width="62%" style={{ marginTop: 10 }} />
            <Skeleton height={13} width="48%" style={{ marginTop: 8 }} />
          </div>
        </li>
      ))}
    </ol>
  );
}

/**
 * Monitoreo > En vivo: estado del bot, indicadores de las últimas horas y el
 * feed cronológico de todo lo que pasa (pedidos, mensajes, respuestas del bot,
 * tickets y alertas de stock), con pausa, filtros y detalle de cada evento.
 */
export function MonitoreoEnVivoPage() {
  const [manualPause, setManualPause] = useState(false);
  const [types, setTypes] = useState<EventType[]>([]);
  const [channel, setChannel] = useState<Channel | ''>('');
  const [selected, setSelected] = useState<MonitoringEvent | null>(null);
  const [orderId, setOrderId] = useState<number | null>(null);

  const listRef = useRef<HTMLDivElement>(null);
  const scrolledAway = useScrolledAway(listRef);
  // Pausa manual, o el usuario está leyendo más abajo: lo nuevo espera en el contador.
  const held = manualPause || scrolledAway;

  const feed = useEventFeed({ types, channel: channel || undefined, paused: held });
  const summary = useQuery({
    queryKey: ['monitoring-summary'],
    queryFn: () => monitoringApi.summary(),
    refetchInterval: SUMMARY_POLL_MS,
  });
  const now = useNow();

  const filtersActive = types.length > 0 || channel !== '';
  const clearFilters = () => {
    setTypes([]);
    setChannel('');
  };

  const openEvent = useCallback((event: MonitoringEvent) => setSelected(event), []);
  const openOrder = (id: number) => {
    setSelected(null);
    setOrderId(id);
  };

  const showNow = () => {
    feed.flush();
    if (scrolledAway) listRef.current?.scrollIntoView?.({ block: 'start', behavior: 'smooth' });
  };

  const badgeLabel = feed.failing ? 'Sin actualizar' : held ? 'En pausa' : 'En vivo';

  return (
    <div>
      <div className="mon-top">
        <BotStatus
          lastActivityAt={latestIso(summary.data?.last_activity_at, feed.newestTs)}
          nowMs={now}
          known={summary.data !== undefined || feed.query.data !== undefined}
        />
        <KpiStrip query={summary} />
      </div>

      <div className="mon-toolbar">
        <Button variant="ghost" onClick={() => setManualPause((p) => !p)}>
          {manualPause ? <PlayIcon width={16} height={16} /> : <PauseIcon width={16} height={16} />}
          {manualPause ? 'Reanudar' : 'Pausar'}
        </Button>

        {feed.pending > 0 && (
          <div className={`mon-pending${scrolledAway ? ' mon-pending--float' : ''}`}>
            <span aria-live="polite">
              {feed.pending === 1 ? '1 evento nuevo' : `${feed.pending} eventos nuevos`}
            </span>
            <Button variant="primary" onClick={showNow}>
              Ver ahora
            </Button>
          </div>
        )}

        <span className={`live-badge mon-live${held || feed.failing ? ' live-badge--paused' : ''}`}>
          <span className="live-badge__dot" aria-hidden="true" />
          {badgeLabel}
        </span>
      </div>

      <EventFilters
        types={types}
        onTypesChange={setTypes}
        channel={channel}
        onChannelChange={setChannel}
      />

      <div ref={listRef}>
        <QueryView
          query={feed.query}
          loading={<FeedSkeleton />}
          isEmpty={(items) => items.length === 0}
          empty={
            filtersActive ? (
              <EmptyState
                icon={<ActivityIcon width={24} height={24} />}
                title="Ningún evento coincide con los filtros"
                text="Probá con otros tipos de evento u otro canal, o quitá los filtros para ver todo."
                action={
                  <Button variant="ghost" onClick={clearFilters}>
                    Quitar filtros
                  </Button>
                }
              />
            ) : (
              <EmptyState
                icon={<ActivityIcon width={24} height={24} />}
                title="El bot todavía no tiene actividad"
                text="Cuando llegue un pedido o un mensaje de un cliente por WhatsApp, Telegram o email, lo vas a ver acá en el momento."
              />
            )
          }
        >
          {(items) => (
            <>
              <ol className="mon-feed" aria-label="Eventos del bot, del más nuevo al más viejo">
                {items.map((event) => (
                  <EventCard
                    key={event.id}
                    event={event}
                    tick={cardTick(event.ts, now)}
                    fresh={feed.fresh.has(event.id)}
                    onOpen={openEvent}
                  />
                ))}
              </ol>
              <div className="mon-more">
                {feed.moreError !== null && (
                  <p className="field__error" role="alert">
                    No pudimos cargar más eventos. Reintentá.
                  </p>
                )}
                {feed.hasMore ? (
                  <Button variant="ghost" onClick={() => void feed.loadMore()} loading={feed.loadingMore}>
                    Cargar eventos anteriores
                  </Button>
                ) : (
                  <p className="mon-end">Esos son todos los eventos registrados.</p>
                )}
              </div>
            </>
          )}
        </QueryView>
      </div>

      {selected && (
        <EventDetailModal
          event={selected}
          onClose={() => setSelected(null)}
          onOpenOrder={openOrder}
        />
      )}
      <OrderDetailModal orderId={orderId} onClose={() => setOrderId(null)} />
    </div>
  );
}
