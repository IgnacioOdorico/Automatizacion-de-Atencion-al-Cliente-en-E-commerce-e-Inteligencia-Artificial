import { formatRelative, formatTmr } from '@/lib/format';
import type { MonitoringSummary } from '@/types/monitoring';

/**
 * Franja superior de "En vivo": estado del bot (a partir de su último evento
 * real) y los indicadores de las últimas horas. Lógica pura, sin React.
 */

/** Hasta acá el último evento cuenta como "el bot está activo". */
export const BOT_ACTIVE_WINDOW_MS = 5 * 60_000;
/** Hasta acá es "sin actividad reciente" (ámbar); más allá, "en reposo" (gris). */
export const BOT_IDLE_WINDOW_MS = 60 * 60_000;

export type BotActivityState = 'active' | 'idle' | 'quiet' | 'none';

export interface BotActivity {
  state: BotActivityState;
  title: string;
  detail: string;
}

function parseMs(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const ms = new Date(iso).getTime();
  return Number.isNaN(ms) ? null : ms;
}

/**
 * Estado del indicador "Bot activo". No hay latido del bot: solo se afirma que
 * está activo si hubo un evento real hace poco. Sin eventos no se inventa nada.
 */
export function botActivity(lastActivityAt: string | null | undefined, nowMs: number): BotActivity {
  const last = parseMs(lastActivityAt);
  if (last === null) {
    return {
      state: 'none',
      title: 'Todavía sin actividad',
      detail: 'cuando el bot atienda algo, lo vas a ver acá',
    };
  }
  const age = Math.max(0, nowMs - last);
  const relative = formatRelative(lastActivityAt, nowMs);
  const detail = relative === 'ahora' ? 'último evento recién' : `último evento ${relative}`;
  if (age <= BOT_ACTIVE_WINDOW_MS) return { state: 'active', title: 'Bot activo', detail };
  if (age <= BOT_IDLE_WINDOW_MS) return { state: 'idle', title: 'Sin actividad reciente', detail };
  return { state: 'quiet', title: 'En reposo', detail };
}

/** La marca de tiempo más reciente (ISO) entre las que sean válidas; null si no hay ninguna. */
export function latestIso(...values: Array<string | null | undefined>): string | null {
  let best: { ms: number; iso: string } | null = null;
  for (const iso of values) {
    const ms = parseMs(iso);
    if (ms !== null && iso && (best === null || ms > best.ms)) best = { ms, iso };
  }
  return best?.iso ?? null;
}

/**
 * Reloj con el que se redibuja una tarjeta del feed. Solo las de menos de un
 * minuto necesitan actualizarse cada segundo ("hace 12 s"); el resto cambia
 * una vez por minuto. Así 300 tarjetas no se redibujan todas cada segundo.
 */
export function cardTick(iso: string, nowMs: number): number {
  const minute = Math.floor(nowMs / 60_000) * 60_000;
  const ts = parseMs(iso);
  if (ts === null) return minute;
  return nowMs - ts < 60_000 ? nowMs : minute;
}

export interface KpiPart {
  text: string;
  /** Solo el fragmento con este tono se pinta (por ejemplo, los "con error" y no los "ok"). */
  tone?: 'warning' | 'danger';
}

export interface Kpi {
  id: string;
  label: string;
  value: string;
  /** El mismo `value` en fragmentos, cuando solo una parte lleva tono. */
  parts?: KpiPart[];
  hint?: string;
  /** Marca visual adicional al número (el número y el texto ya lo dicen todo). */
  tone?: 'warning' | 'danger';
}

function windowHint(hours: number): string {
  return hours === 1 ? 'Última hora' : `Últimas ${hours} h`;
}

/** Indicadores de la ventana del resumen. Tolera un bloque de ejecuciones ausente. */
export function summaryKpis(summary: MonitoringSummary): Kpi[] {
  const window = windowHint(summary.window_hours);
  const { bot, tickets, executions } = summary;

  const executionKpi: Kpi =
    executions && executions.available
      ? {
          id: 'executions',
          label: 'Ejecuciones',
          value: `${executions.success} ok · ${executions.error} con error`,
          parts: [
            { text: `${executions.success} ok` },
            { text: ' · ' },
            { text: `${executions.error} con error`, tone: executions.error > 0 ? 'danger' : undefined },
          ],
          hint: window,
        }
      : {
          id: 'executions',
          label: 'Ejecuciones',
          value: '—',
          hint: 'No disponible por ahora',
        };

  return [
    { id: 'interactions', label: 'Interacciones del bot', value: String(bot.interactions), hint: window },
    {
      id: 'tmr',
      label: 'TMR promedio',
      value: formatTmr(bot.avg_tmr_seconds),
      hint: 'Tiempo medio de respuesta del bot',
    },
    {
      id: 'urgent',
      label: 'Urgentes',
      value: String(bot.urgent),
      hint: window,
      tone: bot.urgent > 0 ? 'warning' : undefined,
    },
    { id: 'tickets-open', label: 'Tickets abiertos', value: String(tickets.open), hint: 'Ahora' },
    executionKpi,
  ];
}
