import { describe, expect, it } from 'vitest';

import {
  ALL_HOURS_VALUE,
  DATA_SOURCE_OPTIONS,
  HOURS_OPTIONS,
  chatbotDataSourceIgnored,
  chatbotDataSourceParam,
  chatbotIsEmpty,
  hoursForOption,
  ordersDataSourceParam,
  ordersIsEmpty,
} from '@/lib/metricsFilters';
import type { ChatbotMetrics, OrdersMetrics } from '@/types/metrics';

describe('HOURS_OPTIONS / hoursForOption: ventana de tiempo compartida', () => {
  it('trae las 3 ventanas pedidas por el usuario', () => {
    expect(HOURS_OPTIONS.map((o) => o.value)).toEqual(['24', '168', ALL_HOURS_VALUE]);
    expect(HOURS_OPTIONS.map((o) => o.label)).toEqual([
      'Últimas 24 h',
      'Últimos 7 días',
      'Todo el histórico',
    ]);
  });

  it('"24" y "168" mapean a horas; "todo" no manda el parámetro (histórico completo)', () => {
    expect(hoursForOption('24')).toBe(24);
    expect(hoursForOption('168')).toBe(168);
    expect(hoursForOption(ALL_HOURS_VALUE)).toBeUndefined();
  });

  it('un valor desconocido no rompe: se toma como histórico completo', () => {
    expect(hoursForOption('lo-que-sea')).toBeUndefined();
  });
});

describe('data_source: dominios distintos entre /metrics/orders y /metrics/chatbot', () => {
  it('DATA_SOURCE_OPTIONS incluye "Carga manual" marcado como solo-pedidos', () => {
    const manual = DATA_SOURCE_OPTIONS.find((o) => o.value === 'e4_manual');
    expect(manual?.ordersOnly).toBe(true);
    expect(manual?.label).toMatch(/pedidos/i);
  });

  it('ordersDataSourceParam: pasa cualquier valor no vacío tal cual (dominio completo)', () => {
    expect(ordersDataSourceParam('')).toBeUndefined();
    expect(ordersDataSourceParam('measured')).toBe('measured');
    expect(ordersDataSourceParam('synthetic')).toBe('synthetic');
    expect(ordersDataSourceParam('e4_manual')).toBe('e4_manual');
  });

  it('chatbotDataSourceParam: solo measured|synthetic; e4_manual y vacío se omiten (histórico completo para ese bloque)', () => {
    expect(chatbotDataSourceParam('')).toBeUndefined();
    expect(chatbotDataSourceParam('measured')).toBe('measured');
    expect(chatbotDataSourceParam('synthetic')).toBe('synthetic');
    expect(chatbotDataSourceParam('e4_manual')).toBeUndefined();
  });

  it('chatbotDataSourceIgnored: avisa cuándo el filtro elegido no aplica a Chatbot', () => {
    expect(chatbotDataSourceIgnored('e4_manual')).toBe(true);
    expect(chatbotDataSourceIgnored('measured')).toBe(false);
    expect(chatbotDataSourceIgnored('')).toBe(false);
  });
});

function orders(total: number): OrdersMetrics {
  return {
    window_hours: null,
    generated_at: '2026-09-21T00:00:00.000Z',
    avg_mttd_seconds: null,
    avg_mttr_seconds: null,
    avg_end_to_end_seconds: null,
    total_orders: total,
    by_status: {},
    daily: [],
  };
}

function chatbot(total: number): ChatbotMetrics {
  return {
    window_hours: null,
    generated_at: '2026-09-21T00:00:00.000Z',
    avg_tmr_seconds: null,
    total_interactions: total,
    by_intent: {},
    by_channel_daily: [],
  };
}

describe('ordersIsEmpty / chatbotIsEmpty: "sin datos todavía" por bloque, no por gráfico', () => {
  it('vacío cuando el contador total es 0', () => {
    expect(ordersIsEmpty(orders(0))).toBe(true);
    expect(chatbotIsEmpty(chatbot(0))).toBe(true);
  });

  it('con datos, no es vacío', () => {
    expect(ordersIsEmpty(orders(1))).toBe(false);
    expect(chatbotIsEmpty(chatbot(3))).toBe(false);
  });
});
