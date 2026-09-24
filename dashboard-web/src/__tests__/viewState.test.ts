import { describe, expect, it } from 'vitest';

import { ApiError } from '@/api/client';
import { errorKind, queryErrorCopy, resolveViewState } from '@/lib/viewState';

describe('errorKind', () => {
  it('un fallo de red (fetch tira TypeError) no es un 401', () => {
    expect(errorKind(new TypeError('Failed to fetch'))).toBe('network');
  });

  it('cualquier cosa que no sea ApiError se trata como red', () => {
    expect(errorKind(undefined)).toBe('network');
    expect(errorKind(null)).toBe('network');
    expect(errorKind('boom')).toBe('network');
  });

  it('401 es sesión vencida', () => {
    expect(errorKind(new ApiError(401, 'La sesión expiró.'))).toBe('session');
  });

  it('5xx es problema del servidor', () => {
    expect(errorKind(new ApiError(500, '500'))).toBe('server');
    expect(errorKind(new ApiError(502, '502 Bad Gateway'))).toBe('server');
    expect(errorKind(new ApiError(503, '503'))).toBe('server');
  });

  it('otros 4xx son error de la solicitud', () => {
    expect(errorKind(new ApiError(404, '404'))).toBe('client');
    expect(errorKind(new ApiError(422, '422'))).toBe('client');
  });
});

describe('queryErrorCopy', () => {
  it('red y 401 dicen cosas distintas', () => {
    const network = queryErrorCopy(new TypeError('Failed to fetch'));
    const session = queryErrorCopy(new ApiError(401, 'La sesión expiró.'));
    expect(network.kind).toBe('network');
    expect(session.kind).toBe('session');
    expect(network.title).not.toBe(session.title);
    expect(network.message).toMatch(/servidor/i);
    expect(session.message).toMatch(/iniciar sesión/i);
  });

  it('el 401 de una pantalla NO habla de email o contraseña (eso es solo del login)', () => {
    const copy = queryErrorCopy(new ApiError(401, 'x'));
    expect(`${copy.title} ${copy.message}`).not.toMatch(/contraseña/i);
  });

  it('5xx no expone el status crudo', () => {
    const copy = queryErrorCopy(new ApiError(502, '502 Bad Gateway'));
    expect(copy.kind).toBe('server');
    expect(`${copy.title} ${copy.message}`).not.toMatch(/502|Bad Gateway/);
  });

  it('un 4xx usa el detalle del backend cuando lo hay', () => {
    const copy = queryErrorCopy(new ApiError(404, 'Pedido no encontrado', 'Pedido no encontrado'));
    expect(copy.kind).toBe('client');
    expect(copy.message).toBe('Pedido no encontrado');
  });

  it('un 4xx sin detalle cae a un texto genérico', () => {
    const copy = queryErrorCopy(new ApiError(400, '400 Bad Request'));
    expect(copy.message).toBeTruthy();
    expect(copy.message).not.toMatch(/400|Bad Request/);
  });

  it('todos los textos están en español con voseo, sin placeholders', () => {
    const errors = [
      new TypeError('x'),
      new ApiError(401, 'x'),
      new ApiError(500, 'x'),
      new ApiError(404, 'x'),
    ];
    for (const error of errors) {
      const copy = queryErrorCopy(error);
      expect(copy.title.length).toBeGreaterThan(5);
      expect(copy.message.length).toBeGreaterThan(10);
      expect(`${copy.title} ${copy.message}`).not.toMatch(/TODO|lorem|undefined/i);
    }
  });
});

describe('resolveViewState', () => {
  it('sin datos ni error: cargando', () => {
    expect(resolveViewState({ hasData: false, isError: false, isEmpty: false })).toEqual({
      view: 'loading',
      refreshFailed: false,
    });
  });

  it('sin datos y con error: pantalla de error', () => {
    expect(resolveViewState({ hasData: false, isError: true, isEmpty: false })).toEqual({
      view: 'error',
      refreshFailed: false,
    });
  });

  it('con datos y lista vacía: estado vacío', () => {
    expect(resolveViewState({ hasData: true, isError: false, isEmpty: true }).view).toBe('empty');
  });

  it('con datos: listo', () => {
    expect(resolveViewState({ hasData: true, isError: false, isEmpty: false })).toEqual({
      view: 'ready',
      refreshFailed: false,
    });
  });

  it('un refetch fallido con datos previos NO tira la pantalla: sigue mostrando y avisa', () => {
    expect(resolveViewState({ hasData: true, isError: true, isEmpty: false })).toEqual({
      view: 'ready',
      refreshFailed: true,
    });
    expect(resolveViewState({ hasData: true, isError: true, isEmpty: true })).toEqual({
      view: 'empty',
      refreshFailed: true,
    });
  });
});
