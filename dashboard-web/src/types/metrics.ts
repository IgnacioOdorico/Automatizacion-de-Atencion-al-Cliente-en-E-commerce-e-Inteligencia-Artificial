/**
 * Contratos de GET /metrics/* (ver docs/API_METRICAS.md). Reemplazo en vivo,
 * dentro del portal, de los paneles de Grafana (tesis-flujo1.json / tesis-flujo2.json).
 * La API devuelve datos estructurados; las etiquetas en español las pone el front.
 */

/** Dominio real de `orders.data_source` (init_simple.sql:65-66). */
export type OrdersDataSource = 'measured' | 'synthetic' | 'e4_manual';
/** Dominio real de `interactions.data_source` (init_simple.sql:113-114) — sin `e4_manual`. */
export type ChatbotDataSource = 'measured' | 'synthetic';

export interface OrdersDailyPoint {
  date: string;
  total_orders: number;
  confirmed: number;
  shipped: number;
  delivered: number;
  no_stock: number;
  cancelled: number;
  error: number;
}

export interface OrdersMetrics {
  window_hours: number | null;
  generated_at: string;
  avg_mttd_seconds: number | null;
  avg_mttr_seconds: number | null;
  avg_end_to_end_seconds: number | null;
  total_orders: number;
  by_status: Record<string, number>;
  daily: OrdersDailyPoint[];
}

export interface ChatbotIntentMetric {
  count: number;
  avg_tmr_seconds: number | null;
}

export interface ChatbotChannelDailyPoint {
  date: string;
  whatsapp: number;
  telegram: number;
  email: number;
}

export interface ChatbotMetrics {
  window_hours: number | null;
  generated_at: string;
  avg_tmr_seconds: number | null;
  total_interactions: number;
  by_intent: Record<string, ChatbotIntentMetric>;
  by_channel_daily: ChatbotChannelDailyPoint[];
}

export interface MetricsParams {
  hours?: number;
  data_source?: string;
}
