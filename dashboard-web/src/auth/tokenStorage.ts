const ACCESS_KEY = 'tesis_dashboard.access_token';
const REFRESH_KEY = 'tesis_dashboard.refresh_token';

function decodePayload(token: string): Record<string, unknown> | null {
  try {
    const part = token.split('.')[1];
    if (!part) return null;
    const base64 = part.replace(/-/g, '+').replace(/_/g, '/');
    const json = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
        .join(''),
    );
    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

/**
 * Storage de tokens para la demo.
 *
 * Trade-off documentado (ver dashboard-web/README.md): el access token vive
 * en localStorage. El backend además setea el refresh en cookie HttpOnly
 * (defensa en profundidad, SPA lo ignora), y acá se persiste también en
 * localStorage el refresh del body para poder rotar sin depender de cookies
 * (dev por Vite proxy y prod por nginx son same-origin, así que ambas vías
 * funcionan). Riesgo XSS <-> riesgo de sesión muerta en cada reload: para la
 * demo se eligió persistencia.
 */
export const tokenStorage = {
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },
  setTokens(tokens: { access_token: string; refresh_token: string }): void {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  },
  clear(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },

  /** ¿El access token ya venció (o está por vencer en `bufferSeconds`)? */
  isExpired(bufferSeconds = 15): boolean {
    const token = this.getAccessToken();
    if (!token) return true;
    const payload = decodePayload(token);
    if (!payload || typeof payload.exp !== 'number') return true;
    return payload.exp * 1000 - bufferSeconds * 1000 <= Date.now();
  },
};