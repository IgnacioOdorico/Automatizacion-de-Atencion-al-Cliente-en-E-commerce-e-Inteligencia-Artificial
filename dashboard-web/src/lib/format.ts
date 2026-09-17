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

export function formatDate(iso: string | null | undefined): string {
  const d = toDate(iso);
  if (!d) return '—';
  return d.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function formatDateTime(iso: string | null | undefined): string {
  const d = toDate(iso);
  if (!d) return '—';
  return d.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}