import { ApiError } from '@/api/client';

/**
 * Traduce errores de la API (y de red) a mensajes amigables en español para los
 * formularios (login/registro). El 401 acá significa "credenciales inválidas";
 * para el error de carga de una pantalla ya autenticada ver `queryErrorCopy`.
 */
export function friendlyApiError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'No pudimos comunicarnos con el servidor. Revisá tu conexión y reintentá.';
  }
  switch (error.status) {
    case 401:
      return error.detail ?? 'Email o contraseña incorrectos.';
    case 409:
      return error.detail ?? 'Ese email ya está registrado.';
    case 429:
      return 'Demasiados intentos. Reintentá en unos minutos.';
    default:
      if (error.status >= 500) {
        return 'El servidor tuvo un problema. Reintentá en unos segundos.';
      }
      return error.detail ?? 'Ocurrió un error inesperado. Reintentá.';
  }
}
