import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { monitoringApi } from '@/api/endpoints';
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

describe('monitoringApi: URLs (solo GET, con el JWT)', () => {
  it('summary sin parámetros', async () => {
    await monitoringApi.summary();
    expect(lastUrl()).toBe('/api/monitoring/summary');
    const init = fetchMock.mock.calls[0][1];
    expect(init?.method).toBe('GET');
    expect((init?.headers as Record<string, string>).Authorization).toMatch(/^Bearer /);
  });

  it('events sin filtros: solo el límite', async () => {
    await monitoringApi.events({ limit: 50 });
    expect(lastUrl()).toBe('/api/monitoring/events?limit=50');
  });

  it('events con filtros: tipos separados por coma y canal', async () => {
    await monitoringApi.events({ limit: 50, types: ['chat_message', 'bot_reply'], channel: 'telegram' });
    const params = paramsOf(lastUrl());
    expect(params.get('types')).toBe('chat_message,bot_reply');
    expect(params.get('channel')).toBe('telegram');
  });

  it('events: el cursor viaja codificado (since y before nunca juntos)', async () => {
    await monitoringApi.events({ since: 'eyJ0IjoiKz0ifQ==' });
    expect(lastUrl()).toBe('/api/monitoring/events?since=eyJ0IjoiKz0ifQ%3D%3D');

    await monitoringApi.events({ before: 'abc_-' });
    expect(lastUrl()).toBe('/api/monitoring/events?before=abc_-');

    await monitoringApi.events({ since: 's', before: 'b' });
    const params = paramsOf(lastUrl());
    expect(params.get('since')).toBe('s');
    expect(params.has('before')).toBe(false);
  });

  it('events: una lista de tipos vacía no manda el parámetro', async () => {
    await monitoringApi.events({ types: [], channel: undefined });
    expect(lastUrl()).toBe('/api/monitoring/events');
  });

  it('conversations: búsqueda recortada y limitada a 100 caracteres', async () => {
    await monitoringApi.conversations({ q: '  pedido 7  ', channel: 'whatsapp', limit: 20 });
    const params = paramsOf(lastUrl());
    expect(params.get('q')).toBe('pedido 7');
    expect(params.get('channel')).toBe('whatsapp');
    expect(params.get('limit')).toBe('20');

    await monitoringApi.conversations({ q: 'x'.repeat(150) });
    expect(paramsOf(lastUrl()).get('q')).toHaveLength(100);

    await monitoringApi.conversations({ q: '   ' });
    expect(lastUrl()).toBe('/api/monitoring/conversations');
  });

  it('thread: el user_id viaja por query y codificado (un "+" no se pierde)', async () => {
    await monitoringApi.thread({ channel: 'whatsapp', userId: '+54 9 261/000', limit: 50 });
    const url = lastUrl();
    expect(url).toContain('/api/monitoring/conversations/thread?');
    expect(url).not.toContain('+54');
    const params = paramsOf(url);
    expect(params.get('user_id')).toBe('+54 9 261/000');
    expect(params.get('channel')).toBe('whatsapp');
  });

  it('thread: cursor para cargar mensajes anteriores', async () => {
    await monitoringApi.thread({ channel: 'telegram', userId: '123', before: 'cur' });
    expect(paramsOf(lastUrl()).get('before')).toBe('cur');
  });

  it('workflows: lista de workflows de n8n', async () => {
    await monitoringApi.workflows();
    expect(lastUrl()).toBe('/api/monitoring/workflows');
    expect(fetchMock.mock.calls[0][1]?.method).toBe('GET');
  });

  it('workflowGraph: el id va en el path, codificado', async () => {
    await monitoringApi.workflowGraph('797bI0eXTmiaSmvJ');
    expect(lastUrl()).toBe('/api/monitoring/workflows/797bI0eXTmiaSmvJ/graph');

    await monitoringApi.workflowGraph('a/b c');
    expect(lastUrl()).toBe('/api/monitoring/workflows/a%2Fb%20c/graph');
  });

  it('executions: filtros por estado y workflow, y cursor numerico `before`', async () => {
    await monitoringApi.executions();
    expect(lastUrl()).toBe('/api/monitoring/executions');

    await monitoringApi.executions({ limit: 20, status: 'error', workflowId: 'wf1', before: 15 });
    const params = paramsOf(lastUrl());
    expect(params.get('limit')).toBe('20');
    expect(params.get('status')).toBe('error');
    expect(params.get('workflow_id')).toBe('wf1');
    expect(params.get('before')).toBe('15');
  });

  it('executions: un filtro vacío no se manda', async () => {
    await monitoringApi.executions({ status: '', workflowId: undefined });
    expect(lastUrl()).toBe('/api/monitoring/executions');
  });

  it('execution: el detalle va por id numerico', async () => {
    await monitoringApi.execution(15);
    expect(lastUrl()).toBe('/api/monitoring/executions/15');
  });
});
