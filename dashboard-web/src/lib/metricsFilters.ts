import type { ChatbotMetrics, OrdersMetrics } from '@/types/metrics';

/**
 * Filtros compartidos de la página Métricas (ventana de tiempo y origen de
 * dato) y las reglas de "sin datos" por bloque. Lógica pura (sin React) para
 * poder testear la semántica sin montar componentes.
 *
 * Dominios distintos a propósito (ver docs/API_METRICAS.md): `/metrics/orders`
 * acepta measured|synthetic|e4_manual; `/metrics/chatbot` solo measured|synthetic
 * (e4_manual no existe en `interactions.data_source`). Con un solo selector
 * compartido en la página, elegir "Carga manual" sigue andando en Pedidos y,
 * en Chatbot, se ignora el filtro (ese bloque muestra todos los orígenes) en
 * vez de romper o pedir un 422 — se avisa con `chatbotDataSourceIgnored`.
 */

/** Valor del selector de ventana para "sin `hours`" (histórico completo). */
export const ALL_HOURS_VALUE = 'all';

export interface HoursOption {
  value: string;
  label: string;
  hours: number | undefined;
}

export const HOURS_OPTIONS: readonly HoursOption[] = [
  { value: '24', label: 'Últimas 24 h', hours: 24 },
  { value: '168', label: 'Últimos 7 días', hours: 168 },
  { value: ALL_HOURS_VALUE, label: 'Todo el histórico', hours: undefined },
];

/** Un valor que no está en la lista (dato corrupto en localStorage, etc.) cae en histórico completo. */
export function hoursForOption(value: string): number | undefined {
  return HOURS_OPTIONS.find((o) => o.value === value)?.hours;
}

export interface DataSourceOption {
  value: string;
  label: string;
  /** No existe en el dominio de `interactions.data_source`: solo aplica a Pedidos. */
  ordersOnly?: boolean;
}

export const DATA_SOURCE_OPTIONS: readonly DataSourceOption[] = [
  { value: '', label: 'Todos los orígenes' },
  { value: 'measured', label: 'Medido' },
  { value: 'synthetic', label: 'Sintético' },
  { value: 'e4_manual', label: 'Carga manual (solo pedidos)', ordersOnly: true },
];

const CHATBOT_DATA_SOURCE_DOMAIN = new Set(['measured', 'synthetic']);

/** `/metrics/orders` acepta el dominio completo: se manda tal cual (vacío = sin filtro). */
export function ordersDataSourceParam(value: string): string | undefined {
  return value === '' ? undefined : value;
}

/** `/metrics/chatbot` solo acepta measured|synthetic: cualquier otra cosa se omite (histórico sin filtro). */
export function chatbotDataSourceParam(value: string): string | undefined {
  return CHATBOT_DATA_SOURCE_DOMAIN.has(value) ? value : undefined;
}

/** El usuario eligió un origen que no existe para Chatbot (hoy, solo `e4_manual`). */
export function chatbotDataSourceIgnored(value: string): boolean {
  return value !== '' && !CHATBOT_DATA_SOURCE_DOMAIN.has(value);
}

/** "Todavía no hay pedidos": el bloque entero se reemplaza por el vacío diseñado, no cada gráfico por separado. */
export function ordersIsEmpty(data: OrdersMetrics): boolean {
  return data.total_orders === 0;
}

/** Igual que `ordersIsEmpty`, para el bloque Chatbot. */
export function chatbotIsEmpty(data: ChatbotMetrics): boolean {
  return data.total_interactions === 0;
}
