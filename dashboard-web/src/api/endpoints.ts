import { apiRequest } from '@/api/client';
import {
  Account,
  AuthTokens,
  Channel,
  Connection,
  DisconnectResponse,
  GmailOAuthUrlResponse,
  Order,
  OrderDetail,
  Paginated,
  Product,
  RegisterResponse,
  Summary,
  TelegramCancelResponse,
  TelegramStartResponse,
  Ticket,
  WhatsAppApprovalResponse,
} from '@/types/api';
import type {
  ConversationsPage,
  ConversationsParams,
  EventsPage,
  EventsParams,
  MonitoringSummary,
  ThreadPage,
  ThreadParams,
} from '@/types/monitoring';

export const authApi = {
  login(body: { email: string; password: string }): Promise<AuthTokens> {
    return apiRequest<AuthTokens>('/auth/login', { method: 'POST', body, auth: false });
  },
  register(body: {
    business_name: string;
    email: string;
    password: string;
  }): Promise<RegisterResponse> {
    return apiRequest<RegisterResponse>('/auth/register', {
      method: 'POST',
      body,
      auth: false,
    });
  },
  me(): Promise<Account> {
    return apiRequest<Account>('/me');
  },
};

// Endpoint preparados para Fases 5-6 (el shell de esta fase no los consume).
export const dashboardApi = {
  summary(params?: { data_source?: 'measured' }): Promise<Summary> {
    const q = params?.data_source ? `?data_source=${params.data_source}` : '';
    return apiRequest<Summary>(`/dashboard/summary${q}`);
  },
  orders(params?: { status?: string; page?: number }): Promise<Paginated<Order>> {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.page && params.page > 1) qs.set('page', String(params.page));
    const q = qs.size ? `?${qs.toString()}` : '';
    return apiRequest<Paginated<Order>>(`/orders${q}`);
  },
  order(id: number): Promise<OrderDetail> {
    return apiRequest<OrderDetail>(`/orders/${id}`);
  },
  tickets(params?: { status?: string; page?: number }): Promise<Paginated<Ticket>> {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.page && params.page > 1) qs.set('page', String(params.page));
    const q = qs.size ? `?${qs.toString()}` : '';
    return apiRequest<Paginated<Ticket>>(`/tickets${q}`);
  },
  products(params?: { search?: string; page?: number }): Promise<Paginated<Product>> {
    const qs = new URLSearchParams();
    if (params?.search) qs.set('search', params.search);
    if (params?.page && params.page > 1) qs.set('page', String(params.page));
    const q = qs.size ? `?${qs.toString()}` : '';
    return apiRequest<Paginated<Product>>(`/products${q}`);
  },
  connections(): Promise<{ items: Connection[] }> {
    return apiRequest<{ items: Connection[] }>('/connections');
  },
};
/** Acciones sobre canales (Fase 3 del backend). El listado está en dashboardApi.connections. */
export const connectionsApi = {
  telegramStart(): Promise<TelegramStartResponse> {
    return apiRequest<TelegramStartResponse>('/connections/telegram/start', { method: 'POST' });
  },
  /** Invalida el código pendiente en el server (no toca el estado del canal). */
  telegramCancelCode(): Promise<TelegramCancelResponse> {
    return apiRequest<TelegramCancelResponse>('/connections/telegram/code', {
      method: 'DELETE',
    });
  },
  gmailOAuthUrl(): Promise<GmailOAuthUrlResponse> {
    return apiRequest<GmailOAuthUrlResponse>('/connections/gmail/oauth-url');
  },
  disconnect(channel: Channel): Promise<DisconnectResponse> {
    return apiRequest<DisconnectResponse>(`/connections/${channel}`, { method: 'DELETE' });
  },
  whatsappRequestApproval(phone: string): Promise<WhatsAppApprovalResponse> {
    return apiRequest<WhatsAppApprovalResponse>('/connections/whatsapp/request-approval', {
      method: 'POST',
      body: { phone },
    });
  },
};


/** Largo máximo de la búsqueda de conversaciones (lo valida también la API). */
const SEARCH_MAX_LENGTH = 100;

/** Arma `?a=1&b=2` con URLSearchParams (codifica `+`, espacios y `/`); sin parámetros devuelve ''. */
function queryString(params: Record<string, string | number | undefined | null>): string {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue;
    qs.set(key, String(value));
  }
  const text = qs.toString();
  return text ? `?${text}` : '';
}

/**
 * Sección "Monitoreo" (solo lectura). Los cursores son opacos: se devuelven tal
 * cual los entregó la API. `since` (polling) y `before` (historia) no se combinan.
 */
export const monitoringApi = {
  summary(params?: { hours?: number }): Promise<MonitoringSummary> {
    return apiRequest<MonitoringSummary>(`/monitoring/summary${queryString({ hours: params?.hours })}`);
  },
  events(params: EventsParams = {}): Promise<EventsPage> {
    const query = queryString({
      limit: params.limit,
      since: params.since,
      before: params.since ? undefined : params.before,
      types: params.types && params.types.length > 0 ? params.types.join(',') : undefined,
      channel: params.channel,
    });
    return apiRequest<EventsPage>(`/monitoring/events${query}`);
  },
  conversations(params: ConversationsParams = {}): Promise<ConversationsPage> {
    const q = Array.from((params.q ?? '').trim()).slice(0, SEARCH_MAX_LENGTH).join('');
    const query = queryString({
      limit: params.limit,
      before: params.before,
      channel: params.channel,
      q,
    });
    return apiRequest<ConversationsPage>(`/monitoring/conversations${query}`);
  },
  /** El user_id va por query (puede traer `+`, `/` o espacios): nunca en el path. */
  thread(params: ThreadParams): Promise<ThreadPage> {
    const query = queryString({
      channel: params.channel,
      user_id: params.userId,
      limit: params.limit,
      before: params.before,
    });
    return apiRequest<ThreadPage>(`/monitoring/conversations/thread${query}`);
  },
};
