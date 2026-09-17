import { ApiError } from '@/api/client';

/** Traduce errores de la API (y de red) a mensajes amigables en español. */
export function friendlyApiError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'No se pudo conectar con el servidor. Verificá que esté corriendo y reintentá.';
  }
  switch (error.status) {
    case 401:
      return error.detail ?? 'Email o contraseña incorrectos.';
    case 409:
      return error.detail ?? 'Ese email ya está registrado.';
    case 429:
      return 'Demasiados intentos. Reintentá en unos minutos.';
    default:
      return error.detail ?? 'Ocurrió un error inesperado. Reintentá.';
  }
}