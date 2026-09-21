import { ApiError } from '@/api/client';
import { CHANNEL_LABELS, CONNECTION_STATUS } from '@/lib/format';
import { friendlyApiError } from '@/lib/messages';
import type { Channel, Connection, ConnectionStatus } from '@/types/api';

/**
 * Lógica pura de la página Conexiones (sin React): mapeo de canales/estados y
 * qué acciones corresponden a cada card. Dominio de canal en BD: whatsapp,
 * telegram y `email` — la UI muestra `email` como "Gmail" (design.md decisión 5).
 */

/** Orden fijo de las cards (el backend responde alfabético: email, telegram, whatsapp). */
export const CHANNEL_ORDER: readonly Channel[] = ['whatsapp', 'telegram', 'email'];

export interface ChannelCardModel {
  channel: Channel;
  label: string;
  status: ConnectionStatus;
  statusMeta: { label: string; tone: 'success' | 'warning' | 'neutral' | 'danger' };
  externalReference: string | null;
  connectedAt: string | null;
}

function statusMeta(status: string): ChannelCardModel['statusMeta'] {
  return CONNECTION_STATUS[status] ?? { label: status, tone: 'neutral' };
}

/**
 * Siempre devuelve las tres cards, en orden fijo. Un canal que el server no
 * devolvió se muestra como desconectado; un canal desconocido se ignora.
 */
export function buildChannelCards(items: Connection[] | undefined): ChannelCardModel[] {
  const byChannel = new Map<Channel, Connection>();
  for (const item of items ?? []) {
    if ((CHANNEL_ORDER as readonly string[]).includes(item.channel)) {
      byChannel.set(item.channel, item);
    }
  }

  return CHANNEL_ORDER.map((channel) => {
    const item = byChannel.get(channel);
    const status: ConnectionStatus = item?.status ?? 'disconnected';
    return {
      channel,
      label: CHANNEL_LABELS[channel],
      status,
      statusMeta: statusMeta(status),
      externalReference: item?.external_reference ?? null,
      connectedAt: item?.connected_at ?? null,
    };
  });
}

export interface ChannelActions {
  canConnect: boolean;
  canDisconnect: boolean;
}

/**
 * Qué botones ofrece cada card según su estado.
 *  - connected: solo desconectar.
 *  - disconnected: solo conectar.
 *  - error: reintentar o limpiar.
 *  - pending (WhatsApp): la aprobación la resuelve Meta, solo se puede cancelar.
 */
export function channelActions(channel: Channel, status: ConnectionStatus): ChannelActions {
  const waitingForApproval = channel === 'whatsapp' && status === 'pending';
  return {
    canConnect: status !== 'connected' && !waitingForApproval,
    canDisconnect: status !== 'disconnected',
  };
}

export type ConnectionAction = 'telegram-start';

const ACTION_FALLBACKS: Record<ConnectionAction, string> = {
  'telegram-start': 'No pudimos generar el código de vinculación. Reintentá en unos segundos.',
};

/**
 * Mensaje en pantalla para un fallo de una acción de conexión. Nada falla en
 * silencio: errores de red y de server (400/502/503/...) terminan en un texto
 * claro. El 401 lo resuelve el cliente de API (refresh o cierre de sesión).
 */
export function connectionActionError(error: unknown, action: ConnectionAction): string {
  if (!(error instanceof ApiError)) return friendlyApiError(error);
  return error.detail ?? ACTION_FALLBACKS[action];
}
