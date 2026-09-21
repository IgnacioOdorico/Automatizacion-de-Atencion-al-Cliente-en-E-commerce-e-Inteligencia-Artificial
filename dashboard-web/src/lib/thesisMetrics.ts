import { formatTmr } from '@/lib/format';
import type { Summary } from '@/types/api';

/**
 * Las tres métricas de la tesis explicadas con su definición REAL: qué marca de
 * tiempo abre y cuál cierra cada intervalo (vistas v_order_processing_time y
 * v_chatbot_response_time de init_simple.sql), y su valor actual.
 * Lógica pura (sin React).
 */

export interface ThesisMetric {
  id: 'mttd' | 'mttr' | 'tmr';
  short: string;
  name: string;
  flow: string;
  /** Qué mide, en palabras del cliente. */
  measures: string;
  /** Columnas de la base que abren y cierran el intervalo. */
  from: string;
  to: string;
  /** Promedio formateado ("—" si no hay muestras). */
  value: string;
  /** Sobre cuántas muestras se calculó. */
  sample: string;
}

type Definition = Omit<ThesisMetric, 'value' | 'sample'>;

const DEFINITIONS: readonly Definition[] = [
  {
    id: 'mttd',
    short: 'MTTD',
    name: 'Tiempo hasta procesar el pedido',
    flow: 'Flujo 1',
    measures: 'Desde que el pedido entra al sistema hasta que el pipeline termina de procesarlo.',
    from: 'received_at',
    to: 'processed_at',
  },
  {
    id: 'mttr',
    short: 'MTTR',
    name: 'Tiempo hasta avisarle al cliente',
    flow: 'Flujo 1',
    measures: 'Desde que el pedido se procesó hasta que el cliente recibe el email de aviso.',
    from: 'processed_at',
    to: 'notified_at',
  },
  {
    id: 'tmr',
    short: 'TMR',
    name: 'Tiempo de respuesta del chatbot',
    flow: 'Flujo 2',
    measures: 'Desde que llega el mensaje del cliente hasta que el bot le responde.',
    from: 'received_at',
    to: 'responded_at',
  },
];

/** Promedio con precisión de milisegundos: los tiempos de la tesis son cortos y "0s" no dice nada. */
function averageText(average: string | number | undefined, samples: number): string {
  if (samples <= 0 || average === undefined || average === '') return '—';
  return formatTmr(Number(average));
}

function sampleText(count: number | undefined, one: string, many: string, empty: string): string {
  if (count === undefined) return 'Sin datos';
  if (count <= 0) return empty;
  return `Sobre ${count === 1 ? `1 ${one}` : `${count} ${many}`}`;
}

export function thesisMetrics(summary: Summary | undefined): ThesisMetric[] {
  return DEFINITIONS.map((def) => {
    const isChat = def.id === 'tmr';
    const samples = isChat ? summary?.total_interactions : summary?.total_orders;
    const average = isChat ? summary?.avg_tmr_seg : def.id === 'mttd' ? summary?.avg_mttd_seg : summary?.avg_mttr_seg;
    return {
      ...def,
      value: samples === undefined ? '—' : averageText(average, samples),
      sample: isChat
        ? sampleText(samples, 'mensaje', 'mensajes', 'Todavía sin mensajes')
        : sampleText(samples, 'pedido', 'pedidos', 'Todavía sin pedidos'),
    };
  });
}
