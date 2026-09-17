import { describe, expect, it } from 'vitest';

import {
  ORDER_STATUSES,
  TICKET_PRIORITIES,
  TICKET_STATUSES,
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