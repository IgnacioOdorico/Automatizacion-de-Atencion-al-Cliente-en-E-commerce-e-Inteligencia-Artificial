import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/api/client';
import { connectionsApi } from '@/api/endpoints';
import { tokenStorage } from '@/auth/tokenStorage';

function b64url(json: string): string {
  return btoa(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function fakeRes(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  localStorage.clear();
  const exp = Math.floor(Date.now() / 1000) + 3600;
  tokenStorage.setTokens({
    access_token: `hdr.${b64url(JSON.stringify({ sub: '1', type: 'access', exp }))}.sig`,
    refresh_token: 'refresh',
  });
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('connectionsApi.telegramCancelCode', () => {
  it('hace DELETE /connections/telegram/code con el JWT y devuelve la respuesta', async () => {
    fetchMock.mockResolvedValueOnce(fakeRes(200, { cancelled: true }));

    const res = await connectionsApi.telegramCancelCode();

    expect(res).toEqual({ cancelled: true });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/connections/telegram/code');
    expect(init?.method).toBe('DELETE');
    const headers = (init?.headers ?? {}) as Record<string, string>;
    expect(headers.Authorization).toMatch(/^Bearer /);
  });

  it('no confunde el código con el canal: nunca pega a DELETE /connections/telegram', async () => {
    fetchMock.mockResolvedValueOnce(fakeRes(200, { cancelled: false }));
    await connectionsApi.telegramCancelCode();
    expect(fetchMock.mock.calls[0][0]).not.toBe('/api/connections/telegram');
  });

  it('propaga el fallo del server como ApiError (la UI lo muestra, no lo traga)', async () => {
    fetchMock.mockResolvedValueOnce(fakeRes(500, { detail: 'Error interno' }));
    await expect(connectionsApi.telegramCancelCode()).rejects.toBeInstanceOf(ApiError);
  });
});
