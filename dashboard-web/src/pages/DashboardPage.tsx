import type { ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { PackageIcon } from '@/components/icons';
import { formatDuration } from '@/lib/format';
import { friendlyApiError } from '@/lib/messages';

/** Polling en vivo: spec client-dashboard/metrics (3-5s). */
const POLL_INTERVAL = 4000;

interface StatCard {
  id: string;
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: boolean;
}

function StatCards({ cards }: { cards: StatCard[] }) {
  return (
    <div className="stat-grid">
      {cards.map((card) => (
        <div
          key={card.id}
          className={`card stat-card${card.accent ? ' stat-card--accent' : ''}`}
        >
          <div className="stat-card__label">{card.label}</div>
          <div className="stat-card__value">{card.value}</div>
          {card.hint && <div className="stat-card__hint">{card.hint}</div>}
        </div>
      ))}
    </div>
  );
}

function LiveBadge() {
  return (
    <span className="live-badge">
      <span className="live-badge__dot" />
      En vivo
    </span>
  );
}

export function DashboardPage() {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => dashboardApi.summary(),
    refetchInterval: POLL_INTERVAL,
  });

  if (isPending) {
    return (
      <div className="page">
        <div className="stat-grid">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 104, borderRadius: 16 }} />
          ))}
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="page">
        <header className="page__head">
          <h1>Dashboard</h1>
          <p className="page__sub">
            Resumen en vivo de las métricas de atención: pedidos, tiempos de respuesta y tickets
            abiertos.
          </p>
        </header>
        <Alert variant="error" role="alert">
          {friendlyApiError(error)}
        </Alert>
        <div style={{ marginTop: 14 }}>
          <Button variant="ghost" onClick={() => refetch()}>
            Reintentar
          </Button>
        </div>
      </div>
    );
  }

  const noActivity =
    data.total_orders === 0 && data.total_tickets === 0 && data.total_interactions === 0;

  const mainCards: StatCard[] = [
    {
      id: 'orders-today',
      label: 'Pedidos hoy',
      value: data.orders_today.toLocaleString('es-AR'),
      hint: 'Órdenes recibidas en el día de hoy.',
      accent: true,
    },
    {
      id: 'tickets-open',
      label: 'Tickets abiertos',
      value: data.tickets_open.toLocaleString('es-AR'),
      accent: true,
    },
    {
      id: 'orders-confirmed',
      label: 'Pedidos confirmados',
      value: data.orders_confirmed.toLocaleString('es-AR'),
    },
    {
      id: 'orders-total',
      label: 'Pedidos totales',
      value: data.total_orders.toLocaleString('es-AR'),
    },
  ];

  const timeCards: StatCard[] = [
    {
      id: 'mttd',
      label: 'MTTD',
      value: formatDuration(data.avg_mttd_seg),
      hint: 'Tiempo medio entre el pedido y su procesamiento.',
    },
    {
      id: 'mttr',
      label: 'MTTR',
      value: formatDuration(data.avg_mttr_seg),
      hint: 'Tiempo medio entre el procesamiento y el aviso al cliente.',
    },
    {
      id: 'tmr',
      label: 'TMR',
      value: formatDuration(data.avg_tmr_seg),
      hint: 'Tiempo medio del bot entre la consulta y su respuesta.',
    },
  ];

  const volumeCards: StatCard[] = [
    {
      id: 'interactions',
      label: 'Interacciones',
      value: data.total_interactions.toLocaleString('es-AR'),
    },
    {
      id: 'tickets-total',
      label: 'Tickets totales',
      value: data.total_tickets.toLocaleString('es-AR'),
    },
    {
      id: 'tickets-resolved',
      label: 'Tickets resueltos',
      value: data.tickets_resolved.toLocaleString('es-AR'),
    },
  ];

  return (
    <div className="page">
      <header className="page__head page__head--row">
        <div>
          <h1>Dashboard</h1>
          <p className="page__sub">
            Resumen en vivo de las métricas de atención: pedidos, tiempos de respuesta y tickets
            abiertos.
          </p>
        </div>
        <LiveBadge />
      </header>

      {noActivity && (
        <EmptyState
          icon={<PackageIcon width={24} height={24} />}
          title="Todavía no hay actividad registrada"
          text="Cuando entren pedidos por el webhook del Flujo 1, las métricas se actualizan solas en menos de 5 segundos."
        />
      )}

      <section className="dash-section">
        <h2 className="section-title">Hoy y abiertos</h2>
        <StatCards cards={mainCards} />
      </section>

      <section className="dash-section">
        <h2 className="section-title">Tiempos de atención</h2>
        <StatCards cards={timeCards} />
      </section>

      <section className="dash-section">
        <h2 className="section-title">Volumen</h2>
        <StatCards cards={volumeCards} />
      </section>
    </div>
  );
}