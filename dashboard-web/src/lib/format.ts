export const CHANNEL_LABELS: Record<string, string> = {
  whatsapp: 'WhatsApp',
  telegram: 'Telegram',
  email: 'Gmail',
};

export const CONNECTION_STATUS: Record<
  string,
  { label: string; tone: 'success' | 'warning' | 'neutral' | 'danger' }
> = {
  connected: { label: 'Conectado', tone: 'success' },
  pending: { label: 'Pendiente', tone: 'warning' },
  disconnected: { label: 'Desconectado', tone: 'neutral' },
  error: { label: 'Error', tone: 'danger' },
};

export function initials(name?: string | null): string {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? '';
  const second = parts.length > 1 ? parts[1][0] : '';
  return (first + second).toUpperCase();
}

function toDate(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

/**
 * Las marcas de tiempo se muestran siempre en la hora del negocio (Mendoza,
 * la misma zona en que corre n8n), no en la de la máquina que mira la pantalla:
 * el dashboard se ve igual desde cualquier lado y en las grabaciones.
 */
export const DISPLAY_TIME_ZONE = 'America/Argentina/Mendoza';

const DATE_TIME_FORMAT = new Intl.DateTimeFormat('es-AR', {
  timeZone: DISPLAY_TIME_ZONE,
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
});

/** Arma las partes a mano: "dd/mm/aaaa hh:mm" idéntico en cualquier motor (sin "p. m."). */
function dateParts(d: Date): Record<string, string> {
  const parts: Record<string, string> = {};
  for (const part of DATE_TIME_FORMAT.formatToParts(d)) parts[part.type] = part.value;
  return parts;
}

export function formatDate(iso: string | null | undefined): string {
  const d = toDate(iso);
  if (!d) return '—';
  const p = dateParts(d);
  return `${p.day}/${p.month}/${p.year}`;
}

export function formatDateTime(iso: string | null | undefined): string {
  const d = toDate(iso);
  if (!d) return '—';
  const p = dateParts(d);
  return `${p.day}/${p.month}/${p.year} ${p.hour}:${p.minute}`;
}

/**
 * Duración legible a partir de segundos: "12s", "1m 30s", "2h 5m", "1d 4h".
 * La API devuelve promedios en segundos (v_metrics_summary), a veces como
 * string ("90.00") porque son columnas NUMERIC — acá se tolera ambas formas.
 */
export function formatDuration(seconds: string | number | null | undefined): string {
  if (seconds === null || seconds === undefined || seconds === '') return '—';
  const n = typeof seconds === 'string' ? Number(seconds) : seconds;
  if (Number.isNaN(n)) return '—';
  const s = Math.round(Math.abs(n));
  if (s < 60) return `${s}s`;

  const m = Math.floor(s / 60);
  const restS = s % 60;
  if (m < 60) return restS ? `${m}m ${restS}s` : `${m}m`;

  const h = Math.floor(m / 60);
  const restM = m % 60;
  if (h < 24) return restM ? `${h}h ${restM}m` : `${h}h`;

  const d = Math.floor(h / 24);
  const restH = h % 24;
  return restH ? `${d}d ${restH}h` : `${d}d`;
}

/**
 * Monedas en "$ X,XX" con separador de miles es-AR. La API serializa DECIMAL
 * como string ("349.99"), así que acepta ambas formas. El signo va antes del $.
 */
export function formatCurrency(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—';
  const n = typeof value === 'string' ? Number(value) : value;
  if (Number.isNaN(n)) return '—';
  const amount = Math.abs(n).toLocaleString('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${n < 0 ? '-' : ''}$${amount}`;
}

/**
 * Cómo se lee el `user_id` de un ticket según el canal: número de teléfono en
 * WhatsApp, chat en Telegram y la dirección en Gmail. Un canal desconocido se
 * muestra tal cual.
 */
export function formatContact(channel: string, userId: string | null | undefined): string {
  if (!userId) return '—';
  switch (channel) {
    case 'whatsapp': {
      const digits = userId.replace(/\D/g, '');
      if (!digits) return userId;
      if (digits.startsWith('549')) return `+54 9 ${digits.slice(3)}`;
      if (digits.startsWith('54')) return `+54 ${digits.slice(2)}`;
      return `+${digits}`;
    }
    case 'telegram':
      return `Chat ${userId}`;
    default:
      return userId;
  }
}

const DATA_SOURCE_LABELS: Record<string, string> = {
  measured: 'Medido',
  synthetic: 'Sintético',
  e4_manual: 'Carga manual',
};

/** Origen del dato (CHECK de `data_source` en la BD) en palabras del cliente. */
export function dataSourceLabel(value: string | null | undefined): string {
  if (!value) return '—';
  return DATA_SOURCE_LABELS[value] ?? value;
}
