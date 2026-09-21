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

export type ConnectionAction =
  | 'telegram-start'
  | 'gmail-connect'
  | 'whatsapp-request'
  | 'disconnect';

const ACTION_FALLBACKS: Record<ConnectionAction, string> = {
  'telegram-start': 'No pudimos generar el código de vinculación. Reintentá en unos segundos.',
  'gmail-connect': 'No pudimos iniciar la conexión con Gmail. Reintentá en unos segundos.',
  'whatsapp-request':
    'No pudimos enviar la solicitud de aprobación. Reintentá en unos segundos.',
  disconnect: 'No pudimos desconectar el canal. Reintentá en unos segundos.',
};

/**
 * Mensaje en pantalla para un fallo de una acción de conexión. Nada falla en
 * silencio: errores de red y de server (400/502/503/...) terminan en un texto
 * claro. El 401 lo resuelve el cliente de API (refresh o cierre de sesión).
 */
export function connectionActionError(error: unknown, action: ConnectionAction): string {
  if (!(error instanceof ApiError)) return friendlyApiError(error);

  if (action === 'gmail-connect') {
    // 503: el server no tiene las credenciales de Google. El detalle nombra
    // variables de entorno, que no le sirven al cliente del portal.
    if (error.status === 503) {
      return 'Gmail todavía no está configurado en el servidor: faltan las credenciales de Google. Avisale a quien administra la plataforma.';
    }
    if (error.status === 502) {
      return 'Google no respondió correctamente. Reintentá en unos minutos.';
    }
  }
  if (action === 'whatsapp-request' && error.status === 422) {
    // pydantic devuelve el detalle como array: el front lo trata como sin detalle.
    return 'El número no tiene un formato válido. Usá el formato internacional, ej. +54 9 261 555 1234.';
  }
  return error.detail ?? ACTION_FALLBACKS[action];
}

/** Nota explicativa del estado de WhatsApp (la aprobación la resuelve Meta, off-band). */
export function whatsappStatusNote(status: ConnectionStatus): string | null {
  switch (status) {
    case 'pending':
      return 'Solicitud enviada: Meta aprueba en 1-3 días hábiles. Cuando la aprueben, esta tarjeta pasa a Conectado.';
    case 'connected':
      return 'Número aprobado por Meta: el canal está operativo.';
    case 'error':
      return 'Hubo un problema con este canal. Reenviá la solicitud o desconectalo.';
    default:
      return null;
  }
}

/** Host de la pantalla de consentimiento de Google (google_oauth.AUTH_URL en el backend). */
const GOOGLE_CONSENT_HOST = 'accounts.google.com';

/** Solo se redirige a Google: cualquier otra URL devuelta por el server se descarta. */
export function isGoogleConsentUrl(url: string | null | undefined): boolean {
  if (!url) return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' && parsed.hostname === GOOGLE_CONSENT_HOST;
  } catch {
    return false;
  }
}

/**
 * Códigos de `?gmail=error&reason=<código>` que emite el callback del backend
 * (connections.py, `GmailErrorReason`). Son un catálogo cerrado: cualquier otro
 * valor del query se trata como "sin motivo" y nunca se muestra tal cual.
 */
export type GmailErrorReason =
  | 'denied'
  | 'google_error'
  | 'invalid_state'
  | 'missing_code'
  | 'exchange_failed'
  | 'upstream'
  | 'no_email'
  | 'no_refresh'
  | 'internal';

export type GmailReturn =
  | { result: 'connected' }
  | { result: 'error'; reason: GmailErrorReason | null };

const GMAIL_GENERIC_ERROR = 'Google no completó la autorización. Reintentá conectar Gmail.';

const GMAIL_ERROR_MESSAGES: Record<GmailErrorReason, string> = {
  denied:
    'Cancelaste la autorización en Google, así que Gmail no quedó conectado. Reintentá cuando quieras.',
  google_error: 'Google no pudo completar la autorización. Reintentá conectar Gmail en unos minutos.',
  invalid_state:
    'La solicitud de conexión venció o no es válida. Iniciá la conexión de Gmail de nuevo.',
  missing_code: 'Google no nos envió el código de autorización. Reintentá conectar Gmail.',
  exchange_failed: 'Google rechazó la autorización. Reintentá conectar Gmail desde el principio.',
  upstream: 'Google no respondió correctamente. Reintentá en unos minutos.',
  no_email:
    'No pudimos obtener el email de tu cuenta de Google. Reintentá y aceptá el permiso de acceso al email.',
  no_refresh:
    'Google no nos dio permiso para mantener la conexión. Reintentá y aceptá todos los permisos que se piden.',
  internal: 'Tuvimos un problema al guardar la conexión de Gmail. Reintentá en unos segundos.',
};

function isGmailErrorReason(value: unknown): value is GmailErrorReason {
  return typeof value === 'string' && Object.hasOwn(GMAIL_ERROR_MESSAGES, value);
}

/**
 * Query con que el backend devuelve al usuario tras el callback de Google:
 * `?gmail=connected` o `?gmail=error&reason=<código>`. Lo desconocido se ignora.
 */
export function parseGmailReturn(search: string): GmailReturn | null {
  const params = new URLSearchParams(search);
  const value = params.get('gmail');
  if (value === 'connected') return { result: 'connected' };
  if (value === 'error') {
    const reason = params.get('reason');
    return { result: 'error', reason: isGmailErrorReason(reason) ? reason : null };
  }
  return null;
}

export interface ConnectionNotice {
  tone: 'success' | 'error';
  text: string;
}

/**
 * Aviso al volver de Google. Espera a tener los datos de GET /connections para
 * no afirmar una conexión que el server no confirma.
 */
export function gmailReturnNotice(
  returned: GmailReturn | null,
  card: ChannelCardModel,
  dataLoaded: boolean,
): ConnectionNotice | null {
  if (!returned) return null;

  if (returned.result === 'error') {
    return {
      tone: 'error',
      text: isGmailErrorReason(returned.reason)
        ? GMAIL_ERROR_MESSAGES[returned.reason]
        : GMAIL_GENERIC_ERROR,
    };
  }

  if (!dataLoaded) return null;
  if (card.status !== 'connected') {
    return {
      tone: 'error',
      text: 'Volviste de Google, pero Gmail no figura como conectado. Reintentá la conexión.',
    };
  }
  return {
    tone: 'success',
    text: card.externalReference
      ? `Gmail conectado. Cuenta autorizada: ${card.externalReference}.`
      : 'Gmail conectado.',
  };
}

/**
 * Red de seguridad: el backend ya redirige el callback de Gmail directo a
 * `/conexiones`, pero una `DASHBOARD_FRONTEND_URL`/build vieja podría seguir
 * apuntando a `/connections`. El alias conserva el query string.
 */
export function connectionsAliasPath(search: string): string {
  const query = search.replace(/^\?/, '');
  return query ? `/conexiones?${query}` : '/conexiones';
}

export interface DisconnectCopy {
  /** Texto del botón de la card. */
  triggerLabel: string;
  title: string;
  message: string;
  confirmLabel: string;
}

/**
 * Textos de la confirmación de desconexión. En WhatsApp `pending` no hay nada
 * conectado todavía: lo que se hace es cancelar la solicitud a Meta.
 */
export function disconnectCopy(card: ChannelCardModel): DisconnectCopy {
  const ref = card.externalReference ? ` (${card.externalReference})` : '';

  if (card.channel === 'whatsapp' && card.status === 'pending') {
    return {
      triggerLabel: 'Cancelar solicitud',
      title: 'Cancelar solicitud de WhatsApp',
      message: `Se cancela la solicitud de aprobación del número${ref}. Podés enviar una nueva cuando quieras.`,
      confirmLabel: 'Cancelar solicitud',
    };
  }
  return {
    triggerLabel: 'Desconectar',
    title: `Desconectar ${card.label}`,
    message: `Vas a desconectar ${card.label}${ref}. Se borran la referencia y las credenciales guardadas; podés volver a conectarlo cuando quieras.`,
    confirmLabel: 'Desconectar',
  };
}
