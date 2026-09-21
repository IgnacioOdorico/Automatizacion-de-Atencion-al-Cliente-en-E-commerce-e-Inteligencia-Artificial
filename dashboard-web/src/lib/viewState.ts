import { ApiError } from '@/api/client';

/**
 * Lógica pura de los estados de una pantalla que carga datos (sin React):
 * qué mostrar (cargando / error / vacío / listo) y con qué texto explicar un
 * error de la API. La red caída y la sesión vencida se distinguen: no son lo
 * mismo ni se resuelven igual.
 */

export type ErrorKind = 'network' | 'session' | 'server' | 'client';

/** `fetch` rechaza con TypeError si no hay red: cualquier no-ApiError es "sin conexión". */
export function errorKind(error: unknown): ErrorKind {
  if (!(error instanceof ApiError)) return 'network';
  if (error.status === 401) return 'session';
  if (error.status >= 500) return 'server';
  return 'client';
}

export interface ErrorCopy {
  kind: ErrorKind;
  title: string;
  message: string;
}

/** Texto en pantalla para un error de carga (nunca el status crudo de HTTP). */
export function queryErrorCopy(error: unknown): ErrorCopy {
  const kind = errorKind(error);
  switch (kind) {
    case 'network':
      return {
        kind,
        title: 'Sin conexión con el servidor',
        message:
          'No pudimos comunicarnos con el servidor. Revisá que esté en línea y reintentá.',
      };
    case 'session':
      return {
        kind,
        title: 'Tu sesión expiró',
        message: 'Volvé a iniciar sesión para seguir usando el portal.',
      };
    case 'server':
      return {
        kind,
        title: 'El servidor tuvo un problema',
        message: 'Ocurrió un error de nuestro lado. Reintentá en unos segundos.',
      };
    default:
      return {
        kind,
        title: 'No pudimos cargar los datos',
        message: (error instanceof ApiError && error.detail) || 'Reintentá en unos segundos.',
      };
  }
}

export type ViewState = 'loading' | 'error' | 'empty' | 'ready';

export interface ViewInput {
  /** Hay una respuesta previa (aunque un refetch posterior haya fallado). */
  hasData: boolean;
  isError: boolean;
  /** Solo se evalúa si hay datos: la respuesta no trae ítems. */
  isEmpty: boolean;
}

export interface ResolvedView {
  view: ViewState;
  /** El último refetch falló pero hay datos viejos que se siguen mostrando. */
  refreshFailed: boolean;
}

/**
 * Decide qué se dibuja. Un refetch fallido (polling cada 4 s) con datos ya
 * cargados NO reemplaza la pantalla por un error: mantiene los datos y avisa.
 */
export function resolveViewState({ hasData, isError, isEmpty }: ViewInput): ResolvedView {
  if (!hasData) {
    return { view: isError ? 'error' : 'loading', refreshFailed: false };
  }
  return { view: isEmpty ? 'empty' : 'ready', refreshFailed: isError };
}
