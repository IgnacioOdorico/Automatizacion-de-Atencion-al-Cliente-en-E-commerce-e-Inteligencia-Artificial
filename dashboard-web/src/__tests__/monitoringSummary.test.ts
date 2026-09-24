import { describe, expect, it } from 'vitest';

import {
  BOT_ACTIVE_WINDOW_MS,
  BOT_IDLE_WINDOW_MS,
  botActivity,
  cardTick,
  latestIso,
  summaryKpis,
} from '@/lib/monitoringSummary';
import type { MonitoringSummary } from '@/types/monitoring';

const NOW = Date.parse('2026-09-21T14:00:00.000Z');
const ago = (ms: number) => new Date(NOW - ms).toISOString();

describe('botActivity (el indicador "Bot activo" no inventa actividad)', () => {
  it('actividad reciente: activo y con la hora relativa del último evento', () => {
    const a = botActivity(ago(12_000), NOW);
    expect(a.state).toBe('active');
    expect(a.title).toBe('Bot activo');
    expect(a.detail).toBe('último evento hace 12 s');
  });

  it('el límite de "activo" es de 5 minutos', () => {
    expect(BOT_ACTIVE_WINDOW_MS).toBe(5 * 60_000);
    expect(botActivity(ago(BOT_ACTIVE_WINDOW_MS), NOW).state).toBe('active');
    expect(botActivity(ago(BOT_ACTIVE_WINDOW_MS + 1_000), NOW).state).toBe('idle');
  });

  it('pasado un rato sin eventos: ámbar, con texto explícito', () => {
    const a = botActivity(ago(25 * 60_000), NOW);
    expect(a.state).toBe('idle');
    expect(a.title).toBe('Sin actividad reciente');
    expect(a.detail).toBe('último evento hace 25 min');
  });

  it('más de una hora: en reposo (gris)', () => {
    expect(BOT_IDLE_WINDOW_MS).toBe(60 * 60_000);
    const a = botActivity(ago(3 * 3_600_000), NOW);
    expect(a.state).toBe('quiet');
    expect(a.title).toBe('En reposo');
    expect(a.detail).toBe('último evento hace 3 h');
  });

  it('sin ningún evento: no afirma que el bot esté activo', () => {
    const a = botActivity(null, NOW);
    expect(a.state).toBe('none');
    expect(a.title).toBe('Todavía sin actividad');
    expect(a.detail).toBe('cuando el bot atienda algo, lo vas a ver acá');
  });

  it('una marca inválida se trata como sin actividad', () => {
    expect(botActivity('basura', NOW).state).toBe('none');
  });
});

describe('latestIso (la actividad más reciente entre el resumen y el feed)', () => {
  it('devuelve la más nueva, ignorando nulos', () => {
    expect(latestIso('2026-09-21T13:00:00.000Z', null, '2026-09-21T14:00:00.000Z', undefined)).toBe(
      '2026-09-21T14:00:00.000Z',
    );
  });

  it('sin valores: null', () => {
    expect(latestIso(null, undefined)).toBeNull();
  });

  it('descarta fechas inválidas', () => {
    expect(latestIso('basura', '2026-09-21T13:00:00.000Z')).toBe('2026-09-21T13:00:00.000Z');
  });
});

describe('cardTick (solo las tarjetas jóvenes se redibujan cada segundo)', () => {
  const minute = Math.floor(NOW / 60_000) * 60_000;

  it('menos de un minuto: el tick es el propio reloj', () => {
    expect(cardTick(ago(20_000), NOW)).toBe(NOW);
  });

  it('más de un minuto: se redondea al minuto para no redibujar 300 tarjetas por segundo', () => {
    expect(cardTick(ago(5 * 60_000), NOW)).toBe(minute);
    expect(cardTick(ago(5 * 60_000), NOW + 30_000)).toBe(minute);
  });

  it('marca inválida: el tick por minuto', () => {
    expect(cardTick('basura', NOW)).toBe(minute);
  });
});

function summary(overrides: Partial<MonitoringSummary> = {}): MonitoringSummary {
  return {
    window_hours: 24,
    generated_at: '2026-09-21T14:05:00.120Z',
    data_source: 'all',
    last_activity_at: '2026-09-21T14:03:22.418Z',
    bot: {
      interactions: 12,
      avg_tmr_seconds: 3.42,
      urgent: 1,
      by_intent: { FAQ: 5, ESTADO_PEDIDO: 4, RECLAMO: 2, GENERAL: 1 },
      by_channel: { whatsapp: 7, telegram: 5, email: 0 },
    },
    orders: {
      total: 9,
      by_status: {
        pending: 0,
        processing: 0,
        confirmed: 7,
        shipped: 0,
        delivered: 0,
        no_stock: 2,
        cancelled: 0,
        error: 0,
      },
    },
    tickets: { created: 2, open: 3, by_priority: { low: 0, normal: 1, high: 1, urgent: 0 } },
    stock_alerts: 1,
    executions: {
      available: true,
      total: 21,
      success: 19,
      error: 2,
      last_error_at: '2026-09-21T13:40:01.000Z',
    },
    ...overrides,
  };
}

describe('summaryKpis (franja de las últimas 24 h)', () => {
  it('arma los cinco indicadores con su valor formateado', () => {
    const kpis = summaryKpis(summary());
    expect(kpis.map((k) => k.id)).toEqual([
      'interactions',
      'tmr',
      'urgent',
      'tickets-open',
      'executions',
    ]);
    const byId = Object.fromEntries(kpis.map((k) => [k.id, k]));
    expect(byId.interactions.value).toBe('12');
    expect(byId.tmr.value).toBe('3,4 s');
    expect(byId.urgent.value).toBe('1');
    expect(byId['tickets-open'].value).toBe('3');
    expect(byId.executions.value).toBe('19 ok · 2 con error');
  });

  it('la ventana se refleja en las etiquetas', () => {
    const hint = (s: MonitoringSummary) => summaryKpis(s).find((k) => k.id === 'interactions')?.hint;
    expect(hint(summary())).toBe('Últimas 24 h');
    expect(hint(summary({ window_hours: 6 }))).toBe('Últimas 6 h');
    expect(hint(summary({ window_hours: 1 }))).toBe('Última hora');
  });

  it('sin respuestas del bot, el TMR es un guion y no "0 ms"', () => {
    const kpis = summaryKpis(summary({ bot: { ...summary().bot, avg_tmr_seconds: null, interactions: 0 } }));
    expect(kpis.find((k) => k.id === 'tmr')?.value).toBe('—');
  });

  it('los urgentes se marcan con tono, además del número', () => {
    const byId = Object.fromEntries(summaryKpis(summary()).map((k) => [k.id, k]));
    expect(byId.urgent.tone).toBe('warning');
    const calm = summaryKpis(summary({ bot: { ...summary().bot, urgent: 0 } }));
    expect(calm.find((k) => k.id === 'urgent')?.tone).toBeUndefined();
  });

  it('en ejecuciones solo lo que falló se marca (los "ok" no se pintan de error)', () => {
    const exec = summaryKpis(summary()).find((k) => k.id === 'executions');
    expect(exec?.parts).toEqual([
      { text: '19 ok' },
      { text: ' · ' },
      { text: '2 con error', tone: 'danger' },
    ]);
    expect(exec?.parts?.map((p) => p.text).join('')).toBe(exec?.value);
    expect(exec?.tone).toBeUndefined();

    const clean = summaryKpis(
      summary({ executions: { available: true, total: 5, success: 5, error: 0, last_error_at: null } }),
    ).find((k) => k.id === 'executions');
    expect(clean?.parts?.some((p) => p.tone)).toBe(false);
  });

  it('sin datos de ejecuciones (n8n no disponible) se degrada sin romper', () => {
    const kpis = summaryKpis(
      summary({ executions: { available: false, total: 0, success: 0, error: 0, last_error_at: null } }),
    );
    const exec = kpis.find((k) => k.id === 'executions');
    expect(exec?.value).toBe('—');
    expect(exec?.hint).toBe('No disponible por ahora');
  });

  it('una respuesta sin el bloque de ejecuciones (backend viejo) tampoco rompe', () => {
    const partial = { ...summary() } as Partial<MonitoringSummary>;
    delete partial.executions;
    expect(() => summaryKpis(partial as MonitoringSummary)).not.toThrow();
  });
});
