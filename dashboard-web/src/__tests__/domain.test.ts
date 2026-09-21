import { describe, expect, it } from 'vitest';

import {
  INTENTS,
  ORDER_STATUSES,
  TICKET_PRIORITIES,
  TICKET_STATUSES,
  intentMeta,
  orderStatusMeta,
  priorityMeta,
  ticketStatusMeta,
} from '@/lib/domain';

describe('Dominios de estado — CHECK de init_simple.sql', () => {
  it('orders.status coincide con el CHECK', () => {
    expect(ORDER_STATUSES).toEqual([
      'pending',
      'processing',
      'confirmed',
      'shipped',
      'delivered',
      'no_stock',
      'cancelled',
      'error',
    ]);
  });

  it('tickets.status coincide con el CHECK', () => {
    expect(TICKET_STATUSES).toEqual(['open', 'in_progress', 'resolved', 'closed']);
  });

  it('tickets.priority coincide con el CHECK', () => {
    expect(TICKET_PRIORITIES).toEqual(['low', 'normal', 'high', 'urgent']);
  });
});

describe('Metadatos de estado/prioridad', () => {
  it('todos los estados de orden tienen label y tone', () => {
    for (const status of ORDER_STATUSES) {
      const meta = orderStatusMeta(status);
      expect(meta.label, `label de ${status}`).toBeTruthy();
      expect(meta.tone, `tone de ${status}`).toBeTruthy();
    }
  });

  it('todos los estados de ticket tienen label y tone', () => {
    for (const status of TICKET_STATUSES) {
      const meta = ticketStatusMeta(status);
      expect(meta.label, `label de ${status}`).toBeTruthy();
      expect(meta.tone, `tone de ${status}`).toBeTruthy();
    }
  });

  it('todas las prioridades tienen label y tone', () => {
    for (const priority of TICKET_PRIORITIES) {
      const meta = priorityMeta(priority);
      expect(meta.label, `label de ${priority}`).toBeTruthy();
      expect(meta.tone, `tone de ${priority}`).toBeTruthy();
    }
  });

  it('un valor desconocido no explota (fallback neutral)', () => {
    const meta = orderStatusMeta('status_legacy_inexistente');
    expect(meta.tone).toBe('neutral');
    expect(meta.label).toBe('status_legacy_inexistente');
  });
});

describe('Intents del bot (clasificación de GPT-4o-mini)', () => {
  it('coinciden con el dominio cerrado de la API', () => {
    expect(INTENTS).toEqual(['FAQ', 'ESTADO_PEDIDO', 'RECLAMO', 'GENERAL']);
  });

  it('cada intent se muestra en lenguaje del cliente, sin el código interno', () => {
    expect(intentMeta('FAQ').label).toBe('Pregunta frecuente');
    expect(intentMeta('ESTADO_PEDIDO').label).toBe('Estado de pedido');
    expect(intentMeta('RECLAMO')).toEqual({ label: 'Reclamo', tone: 'warning' });
    expect(intentMeta('GENERAL').label).toBe('Consulta general');
  });

  it('un intent nuevo o ausente no rompe la pantalla', () => {
    expect(intentMeta('OTRO_INTENT')).toEqual({ label: 'OTRO_INTENT', tone: 'neutral' });
    expect(intentMeta(null)).toEqual({ label: '—', tone: 'neutral' });
  });
});
