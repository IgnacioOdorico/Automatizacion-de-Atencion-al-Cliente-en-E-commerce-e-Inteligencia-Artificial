/**
 * Lógica pura del vínculo de Telegram por código de 6 dígitos (spec connections):
 * el código dura 15 minutos y el front consulta GET /connections hasta que el
 * workflow n8n confirme el vínculo (la card pasa a `connected` sin recargar).
 */

/** TTL de la spec (15 min); se usa solo si la respuesta no trae un vencimiento válido. */
export const TELEGRAM_CODE_FALLBACK_TTL_SECONDS = 15 * 60;

/** Intervalo de consulta mientras se espera el vínculo (ventana 3-5s de la spec). */
export const TELEGRAM_POLL_MS = 3000;

export interface TelegramCodeExpiry {
  expires_at: string;
  expires_in: number;
}

/**
 * Instante (ms epoch) en que vence el código. Se prefiere `expires_in` medido
 * desde que llegó la respuesta: no depende de que el reloj del navegador y el
 * del server estén sincronizados. `expires_at` es el respaldo.
 */
export function codeDeadline(start: TelegramCodeExpiry, receivedAt: number): number {
  if (Number.isFinite(start.expires_in) && start.expires_in > 0) {
    return receivedAt + start.expires_in * 1000;
  }
  const parsed = Date.parse(start.expires_at);
  if (Number.isFinite(parsed)) return parsed;
  return receivedAt + TELEGRAM_CODE_FALLBACK_TTL_SECONDS * 1000;
}

/** Segundos que le quedan al código; redondea hacia arriba y nunca es negativo. */
export function secondsRemaining(deadline: number, now: number): number {
  return Math.max(0, Math.ceil((deadline - now) / 1000));
}

/** "mm:ss" para la cuenta regresiva. */
export function formatCountdown(seconds: number): string {
  const total = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0;
  const mm = String(Math.floor(total / 60)).padStart(2, '0');
  const ss = String(total % 60).padStart(2, '0');
  return `${mm}:${ss}`;
}

/** Se consulta el estado solo mientras hay un código vigente esperando el vínculo. */
export function shouldPollTelegram(state: { hasCode: boolean; expired: boolean }): boolean {
  return state.hasCode && !state.expired;
}
