import { tokenStorage } from '@/auth/tokenStorage';

/**
 * Cliente de fetch tipado con:
 *  - base `/api` (dev: proxy de Vite a :8000, prod: proxy de nginx a dashboard-api)
 *  - Authorization Bearer automático
 *  - manejo de 401: un solo refresh en vuelo, se rehace la request original;
 *    si el refresh falla -> se limpia la sesión y se notifica al AuthProvider.
 */

const BASE_URL = '/api';

export class ApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }

  static async fromResponse(res: Response): Promise<ApiError> {
    let detail: string | undefined;
    try {
      const body = (await res.json()) as { detail?: unknown };
      // FastAPI puede devolver detail como array (errores 422 de pydantic).
      if (typeof body.detail === 'string') detail = body.detail;
    } catch {
      // cuerpo no JSON: usamos el status text
    }
    const message = detail ?? `${res.status} ${res.statusText}`.trim();
    return new ApiError(res.status, message, detail);
  }
}

type SessionExpiredHandler = () => void;

let inFlightRefresh: Promise<boolean> | null = null;
let onSessionExpired: SessionExpiredHandler | null = null;

export function setSessionExpiredHandler(handler: SessionExpiredHandler): void {
  onSessionExpired = handler;
}

export function clearSessionExpiredHandler(): void {
  onSessionExpired = null;
}

async function performRefresh(): Promise<boolean> {
  const refresh = tokenStorage.getRefreshToken();
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const tokens = (await res.json()) as {
      access_token: string;
      refresh_token: string;
    };
    tokenStorage.setTokens(tokens);
    return true;
  } catch {
    return false;
  }
}

/** Un solo refresh en vuelo: N requests con 401 comparten la misma promesa. */
function refreshTokens(): Promise<boolean> {
  if (!inFlightRefresh) {
    inFlightRefresh = performRefresh().finally(() => {
      inFlightRefresh = null;
    });
  }
  return inFlightRefresh;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  auth?: boolean;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = 'GET', body, headers: extraHeaders = {}, auth = true } = options;
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...extraHeaders,
  };
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  const send = (withAuth: boolean): Promise<Response> => {
    const authHeaders = { ...headers };
    if (withAuth) {
      const token = tokenStorage.getAccessToken();
      if (token) authHeaders.Authorization = `Bearer ${token}`;
    }
    return fetch(`${BASE_URL}${path}`, {
      method,
      headers: authHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  };

  let res = await send(auth);

  if (res.status === 401 && auth) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      res = await send(true);
    } else {
      tokenStorage.clear();
      onSessionExpired?.();
      throw new ApiError(401, 'La sesión expiró. Volvé a iniciar sesión.');
    }
  }

  if (!res.ok) throw await ApiError.fromResponse(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}