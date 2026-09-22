import type { ReactNode } from 'react';

export interface MetricStatCard {
  id: string;
  label: string;
  value: ReactNode;
  hint?: string;
}

/** Grilla de tarjetas de estadística, mismo patrón visual que DashboardPage. */
export function StatCards({ cards }: { cards: MetricStatCard[] }) {
  return (
    <div className="stat-grid">
      {cards.map((card) => (
        <div key={card.id} className="card stat-card">
          <div className="stat-card__label">{card.label}</div>
          <div key={String(card.value)} className="stat-card__value">
            {card.value}
          </div>
          {card.hint && <div className="stat-card__hint">{card.hint}</div>}
        </div>
      ))}
    </div>
  );
}
