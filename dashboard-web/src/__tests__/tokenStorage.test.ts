import { beforeEach, describe, expect, it } from 'vitest';

import { tokenStorage } from '@/auth/tokenStorage';

function b64url(json: string): string {
  return btoa(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** JWT trucho con only exp (el resto del payload no interesa). */
function fakeToken(expEpochSec: number): string {
  return `hdr.${b64url(JSON.stringify({ exp: expEpochSec }))}.sig`;
}

const MINUTE = 60;

describe('tokenStorage', () => {
  beforeEach(() => tokenStorage.clear());

  it('arranca sin tokens', () => {
    expect(tokenStorage.getAccessToken()).toBeNull();
    expect(tokenStorage.getRefreshToken()).toBeNull();
  });

  it('persiste y limpia tokens', () => {
    tokenStorage.setTokens({ access_token: 'acc', refresh_token: 'ref' });
    expect(tokenStorage.getAccessToken()).toBe('acc');
    expect(tokenStorage.getRefreshToken()).toBe('ref');

    tokenStorage.clear();
    expect(tokenStorage.getAccessToken()).toBeNull();
    expect(tokenStorage.getRefreshToken()).toBeNull();
  });

  it('sin token: se considera expirado', () => {
    expect(tokenStorage.isExpired()).toBe(true);
  });

  it('token vencido -> expirado', () => {
    localStorage.setItem('tesis_dashboard.access_token', fakeToken(Math.floor(Date.now() / 1000) - 5 * MINUTE));
    expect(tokenStorage.isExpired(15)).toBe(true);
  });

  it('token vigente -> no expirado', () => {
    localStorage.setItem('tesis_dashboard.access_token', fakeToken(Math.floor(Date.now() / 1000) + 60 * MINUTE));
    expect(tokenStorage.isExpired(15)).toBe(false);
  });

  it('token malformado -> expirado (fuerza refresh)', () => {
    localStorage.setItem('tesis_dashboard.access_token', 'no.es-un.jwt');
    expect(tokenStorage.isExpired()).toBe(true);
  });
});