import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  apiRequest,
  clearSessionExpiredHandler,
  setSessionExpiredHandler,
  ApiError,
} from '@/api/client';
import { tokenStorage } from '@/auth/tokenStorage';

const MINUTE = 60;

function b64url(json: string): string {
  return btoa(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** Access token con exp futura (parece vigente; el 401 lo decide el server). */
function futureAccessToken(): string {
  const exp = Math.floor(Date.now() / 1000) + 60 * MINUTE;
  return `hdr.${b64url(JSON.stringify({ sub: '1', type: 'access', exp }))}.sig`;
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
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
  clearSessionExpiredHandler();
});

describe('apiRequest — renovación automática (spec auth)', () => {
  it('ante un 401, refresca una sola vez y rehace la request original con el token nuevo', async () => {
    tokenStorage.setTokens({
      access_token: futureAccessToken(),
      refresh_token: 'good-refresh',
    });

    fetchMock
      .mockResolvedValueOnce(fakeRes(401, { detail: 'Token inválido o vencido' }))
      .mockImplementationOnce(async (url, init) => {
        expect(url).toBe('/api/auth/refresh');
        const body = JSON.parse(String(init?.body));
        expect(body.refresh_token).toBe('good-refresh');
        return fakeRes(200, {
          access_token: 'new-access',
          refresh_token: 'new-refresh',
          token_type: 'bearer',
        });
      })
      .mockImplementationOnce(async (_url, init) => {
        const headers = (init?.headers ?? {}) as Record<string, string>;
        expect(headers.Authorization).toBe('Bearer new-access');
        return fakeRes(200, { ok: true });
      });

    const data = await apiRequest<{ ok: boolean }>('/me');
    expect(data).toEqual({ ok: true });
    expect(tokenStorage.getAccessToken()).toBe('new-access');
    expect(tokenStorage.getRefreshToken()).toBe('new-refresh');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('N requests con 401 comparten un único refresh en vuelo', async () => {
    tokenStorage.setTokens({
      access_token: futureAccessToken(),
      refresh_token: 'good-refresh',
    });

    fetchMock
      .mockResolvedValueOnce(fakeRes(401, {}))
      .mockResolvedValueOnce(fakeRes(401, {}))
      .mockImplementationOnce(async (url) => {
        expect(url).toBe('/api/auth/refresh');
        return fakeRes(200, {
          access_token: 'new-access',
          refresh_token: 'new-refresh',
          token_type: 'bearer',
        });
      })
      .mockImplementation(async () => fakeRes(200, { done: true }));

    const [a, b] = await Promise.all([
      apiRequest('/a').catch(() => null),
      apiRequest('/b').catch(() => null),
    ]);
    expect(a).toEqual({ done: true });
    expect(b).toEqual({ done: true });

    let refreshCalls = 0;
    for (const call of fetchMock.mock.calls) {
      if (call[0] === '/api/auth/refresh') refreshCalls += 1;
    }
    expect(refreshCalls).toBe(1);
  });

  it('si el refresh falla, limpia la sesión y notifica (logout + redirect)', async () => {
    tokenStorage.setTokens({
      access_token: futureAccessToken(),
      refresh_token: 'bad-refresh',
    });
    const onExpired = vi.fn();
    setSessionExpiredHandler(onExpired);

    fetchMock
      .mockResolvedValueOnce(fakeRes(401, {}))
      .mockResolvedValueOnce(fakeRes(401, { detail: 'Refresh token inválido o vencido' }));

    await expect(apiRequest('/me')).rejects.toBeInstanceOf(ApiError);
    expect(tokenStorage.getAccessToken()).toBeNull();
    expect(tokenStorage.getRefreshToken()).toBeNull();
    expect(onExpired).toHaveBeenCalledTimes(1);
  });

  it('NO refresca en endpoints públicos (401 del login se propaga tal cual)', async () => {
    fetchMock.mockResolvedValueOnce(fakeRes(401, { detail: 'Email o contraseña incorrectos' }));
    await expect(
      apiRequest('/auth/login', {
        method: 'POST',
        body: { email: 'x@x.com', password: 'nope' },
        auth: false,
      }),
    ).rejects.toMatchObject({ status: 401 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});