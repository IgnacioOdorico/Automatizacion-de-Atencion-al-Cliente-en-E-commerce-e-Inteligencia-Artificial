import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { metricsApi } from '@/api/endpoints';
import { tokenStorage } from '@/auth/tokenStorage';

function b64url(json: string): string {
  return btoa(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

const fetchMock = vi.fn<typeof fetch>();

function ok(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

beforeEach(() => {
  localStorage.clear();
  const exp = Math.floor(Date.now() / 1000) + 3600;
  tokenStorage.setTokens({
    access_token: `hdr.${b64url(JSON.stringify({ sub: '1', type: 'access', exp }))}.sig`,
    refresh_token: 'refresh',
  });
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.mockReset();
  fetchMock.mockImplementation(() => Promise.resolve(ok({})));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const lastUrl = () => String(fetchMock.mock.calls[fetchMock.mock.calls.length - 1][0]);
const paramsOf = (url: string) => new URL(url, 'http://x').searchParams;

describe('metricsApi: URLs de GET /metrics/orders y /metrics/chatbot', () => {
  it('orders sin filtros: histórico completo, sin parámetros', async () => {
    await metricsApi.orders();
    expect(lastUrl()).toBe('/api/metrics/orders');
    expect(fetchMock.mock.calls[0][1]?.method).toBe('GET');
  });

  it('orders con hours y data_source', async () => {
    await metricsApi.orders({ hours: 168, data_source: 'e4_manual' });
    const params = paramsOf(lastUrl());
    expect(params.get('hours')).toBe('168');
    expect(params.get('data_source')).toBe('e4_manual');
  });

  it('chatbot sin filtros', async () => {
    await metricsApi.chatbot();
    expect(lastUrl()).toBe('/api/metrics/chatbot');
  });

  it('chatbot con hours y data_source', async () => {
    await metricsApi.chatbot({ hours: 24, data_source: 'synthetic' });
    const params = paramsOf(lastUrl());
    expect(params.get('hours')).toBe('24');
    expect(params.get('data_source')).toBe('synthetic');
  });

  it('un data_source vacío no se manda', async () => {
    await metricsApi.orders({ data_source: '' });
    expect(lastUrl()).toBe('/api/metrics/orders');
  });
});
