export type Channel = 'whatsapp' | 'telegram' | 'email';
export type ConnectionStatus = 'disconnected' | 'pending' | 'connected' | 'error';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface Account {
  id: number;
  business_name: string;
  email: string;
  created_at: string | null;
  connections?: Connection[];
}

export interface RegisterResponse {
  id: number;
  business_name: string;
  email: string;
  created_at: string | null;
}

export interface Connection {
  id: number;
  channel: Channel;
  status: ConnectionStatus;
  external_reference: string | null;
  connected_at: string | null;
  label?: string;
}

/** POST /connections/telegram/start: código de 6 dígitos válido 15 minutos. */
export interface TelegramStartResponse {
  code: string;
  expires_at: string;
  expires_in: number;
}

/** GET /connections/gmail/oauth-url: URL de consentimiento de Google con `state` firmado. */
export interface GmailOAuthUrlResponse {
  url: string;
  state: string;
  expires_in: number;
}

export interface Paginated<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface Summary {
  total_orders: number;
  orders_confirmed: number;
  /** Segundos; la API los serializa como number (0) o string ("90.00"). */
  avg_mttd_seg: string | number;
  avg_mttr_seg: string | number;
  total_interactions: number;
  avg_tmr_seg: string | number;
  total_tickets: number;
  tickets_resolved: number;
  orders_today: number;
  tickets_open: number;
  data_source: string;
}

export interface Order {
  id: number;
  order_number: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string | null;
  quantity: number;
  total_amount: string | number;
  status: string;
  received_at: string | null;
  processed_at: string | null;
  notified_at: string | null;
  data_source: string | null;
  product_sku: string | null;
  product_name: string | null;
}

export interface OrderDetail extends Order {
  raw_payload: unknown;
  order_items: Array<{
    id: number;
    product_id: number;
    quantity: number;
    unit_price: number;
    subtotal: number;
  }>;
}

export interface Ticket {
  id: number;
  interaction_id: number | null;
  order_id: number | null;
  channel: Channel;
  user_id: string | null;
  subject: string | null;
  status: string;
  priority: string;
  created_at: string | null;
  resolved_at: string | null;
  data_source: string | null;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  price: string | number;
  stock: number;
  stock_min: number;
  category: string | null;
  created_at: string | null;
}

export interface ApiErrorPayload {
  detail?: string;
}