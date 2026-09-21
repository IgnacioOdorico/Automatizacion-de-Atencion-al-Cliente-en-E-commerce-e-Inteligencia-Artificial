import { describe, expect, it } from 'vitest';

import { thesisMetrics } from '@/lib/thesisMetrics';
import type { Summary } from '@/types/api';

const SUMMARY: Summary = {
  total_orders: 9,
  orders_confirmed: 7,
  avg_mttd_seg: '0.46',
  avg_mttr_seg: 2.5,
  total_interactions: 12,
  avg_tmr_seg: '3.42',
  total_tickets: 2,
  tickets_resolved: 1,
  orders_today: 3,
  tickets_open: 1,
  data_source: 'all',
};

const byId = (summary: Summary | undefined) => Object.fromEntries(thesisMetrics(summary).map((m) => [m.id, m]));

describe('thesisMetrics', () => {
  it('explica las tres métricas en el orden de la tesis', () => {
    expect(thesisMetrics(SUMMARY).map((m) => m.short)).toEqual(['MTTD', 'MTTR', 'TMR']);
  });

  it('las definiciones salen de las vistas reales: qué marca de tiempo abre y cierra cada intervalo', () => {
    const m = byId(SUMMARY);
    expect([m.mttd.from, m.mttd.to]).toEqual(['received_at', 'processed_at']);
    expect([m.mttr.from, m.mttr.to]).toEqual(['processed_at', 'notified_at']);
    expect([m.tmr.from, m.tmr.to]).toEqual(['received_at', 'responded_at']);
  });

  it('cada una dice a qué flujo pertenece y qué mide, en palabras del cliente', () => {
    const m = byId(SUMMARY);
    expect(m.mttd.flow).toBe('Flujo 1');
    expect(m.mttr.flow).toBe('Flujo 1');
    expect(m.tmr.flow).toBe('Flujo 2');
    expect(m.mttd.measures).toMatch(/entra|recibe/i);
    expect(m.mttd.measures).toMatch(/procesa/i);
    expect(m.mttr.measures).toMatch(/email|aviso|notific/i);
    expect(m.tmr.measures).toMatch(/mensaje/i);
    expect(m.tmr.measures).toMatch(/respond/i);
  });

  it('los valores salen del resumen con el formato del portal', () => {
    const m = byId(SUMMARY);
    expect(m.mttd.value).toBe('0s');
    expect(m.mttr.value).toBe('3s');
    expect(m.tmr.value).toBe('3s');
  });

  it('cuenta sobre cuántas muestras se calculó', () => {
    const m = byId(SUMMARY);
    expect(m.mttd.sample).toBe('Sobre 9 pedidos');
    expect(m.tmr.sample).toBe('Sobre 12 mensajes');
    expect(byId({ ...SUMMARY, total_orders: 1, total_interactions: 1 }).mttd.sample).toBe('Sobre 1 pedido');
    expect(byId({ ...SUMMARY, total_interactions: 1 }).tmr.sample).toBe('Sobre 1 mensaje');
  });

  it('sin datos (todavía no hay muestras) muestra guion y no un cero inventado', () => {
    const m = byId({ ...SUMMARY, total_orders: 0, total_interactions: 0, avg_mttd_seg: 0, avg_mttr_seg: 0, avg_tmr_seg: 0 });
    expect(m.mttd.value).toBe('—');
    expect(m.mttr.value).toBe('—');
    expect(m.tmr.value).toBe('—');
    expect(m.mttd.sample).toBe('Todavía sin pedidos');
    expect(m.tmr.sample).toBe('Todavía sin mensajes');
  });

  it('sin resumen (cargando o con error) también son guiones', () => {
    const m = byId(undefined);
    expect([m.mttd.value, m.mttr.value, m.tmr.value]).toEqual(['—', '—', '—']);
    expect(m.mttd.sample).toBe('Sin datos');
  });
});
