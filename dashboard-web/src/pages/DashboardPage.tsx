import type { ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { LiveBadge } from '@/components/LiveBadge';
import { QueryView } from '@/components/QueryView';
import { PackageIcon } from '@/components/icons';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { formatMetricDuration } from '@/lib/format';
import type { Summary } from '@/types/api';

/** Polling en vivo: spec client-dashboard/metrics (3-5s). */
const POLL_INTERVAL = 4000;

interface StatCard {
  id: string;
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: boolean;
}

interface StatSection {
  title: string;
  cards: StatCard[];
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
          {/* key = valor: al cambiar se remonta y dispara el "tick" (se nota el dato que se movió). */}
          <div key={String(card.value)} className="stat-card__value">
            {card.value}
          </div>
          {card.hint && <div className="stat-card__hint">{card.hint}</div>}
        </div>
      ))}
    </div>
  );
}

/**
 * El esqueleto de carga replica la grilla: cantidad de tarjetas y alto aproximado
 * de cada sección (las que llevan texto de ayuda son más altas), para que al
 * llegar los datos no se corra el contenido de abajo.
 */
const SKELETON_SECTIONS = [
  { size: 4, height: 148 },
  { size: 3, height: 167 },
  { size: 3, height: 124 },
];

function DashboardSkeleton() {
  return (
    <div aria-hidden="true">
      {SKELETON_SECTIONS.map(({ size, height }, s) => (
        <section key={s} className="dash-section">
          <Skeleton height={12} width={120} className="dash-section__title-skeleton" />
          <div className="stat-grid">
            {Array.from({ length: size }, (_, i) => (
              <div key={i} className="card stat-card stat-card--skeleton" style={{ minHeight: height }}>
                <Skeleton height={11} width="46%" />
                <Skeleton height={30} width="38%" style={{ marginTop: 10 }} />
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function buildSections(data: Summary): StatSection[] {
  return [
    {
      title: 'Hoy y abiertos',
      cards: [
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
      ],
    },
    {
      title: 'Tiempos de atención',
      cards: [
        {
          id: 'mttd',
          label: 'MTTD',
          value: formatMetricDuration(data.avg_mttd_seg, data.total_orders),
          hint: 'Tiempo medio entre el pedido y su procesamiento.',
        },
        {
          id: 'mttr',
          label: 'MTTR',
          value: formatMetricDuration(data.avg_mttr_seg, data.total_orders),
          hint: 'Tiempo medio entre el procesamiento y el aviso al cliente.',
        },
        {
          id: 'tmr',
          label: 'TMR',
          value: formatMetricDuration(data.avg_tmr_seg, data.total_interactions),
          hint: 'Tiempo medio del bot entre la consulta y su respuesta.',
        },
      ],
    },
    {
      title: 'Volumen',
      cards: [
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
      ],
    },
  ];
}

function hasNoActivity(data: Summary): boolean {
  return data.total_orders === 0 && data.total_tickets === 0 && data.total_interactions === 0;
}

export function DashboardPage() {
  const query = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => dashboardApi.summary(),
    refetchInterval: POLL_INTERVAL,
  });

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
        <LiveBadge paused={query.isError} />
      </header>

      <QueryView
        query={query}
        loading={<DashboardSkeleton />}
        isEmpty={hasNoActivity}
        empty={
          <EmptyState
            icon={<PackageIcon width={24} height={24} />}
            title="Todavía no hay actividad registrada"
            text="Cuando entren pedidos y consultas de tus clientes, las métricas se actualizan solas en menos de 5 segundos."
          />
        }
      >
        {(data) =>
          buildSections(data).map((section) => (
            <section key={section.title} className="dash-section">
              <h2 className="section-title">{section.title}</h2>
              <StatCards cards={section.cards} />
            </section>
          ))
        }
      </QueryView>
    </div>
  );
}
