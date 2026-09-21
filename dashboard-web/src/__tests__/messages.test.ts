import { describe, expect, it } from 'vitest';

import { ApiError } from '@/api/client';
import { friendlyApiError } from '@/lib/messages';

describe('friendlyApiError (formularios de login/registro)', () => {
  it('la red caída y las credenciales inválidas dicen cosas distintas', () => {
    const network = friendlyApiError(new TypeError('Failed to fetch'));
    const credentials = friendlyApiError(new ApiError(401, 'x'));
    expect(network).toMatch(/servidor/i);
    expect(credentials).toMatch(/contraseña/i);
    expect(network).not.toBe(credentials);
  });

  it('usa el detalle del backend cuando lo hay', () => {
    expect(friendlyApiError(new ApiError(409, 'x', 'Ese email ya está registrado.'))).toBe(
      'Ese email ya está registrado.',
    );
  });

  it('un 5xx no muestra el status crudo ni el texto del proxy', () => {
    const text = friendlyApiError(new ApiError(502, '502 Bad Gateway'));
    expect(text).toMatch(/servidor/i);
    expect(text).not.toMatch(/502|Bad Gateway/);
  });

  it('el texto de red no habla de "verificar que esté corriendo" (jerga de desarrollo)', () => {
    expect(friendlyApiError(new TypeError('Failed to fetch'))).not.toMatch(/corriendo/i);
  });
});
