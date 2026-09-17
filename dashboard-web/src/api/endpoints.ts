import { apiRequest } from '@/api/client';
import {
  Account,
  AuthTokens,
  Connection,
  Order,
  OrderDetail,
  Paginated,
  Product,
  RegisterResponse,
  Summary,
  Ticket,
} from '@/types/api';

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