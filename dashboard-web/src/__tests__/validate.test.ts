import { describe, expect, it } from 'vitest';

import {
  validateBusinessName,
  validateEmail,
  validateLogin,
  validatePassword,
  validateRegister,
} from '@/lib/validate';

describe('validateEmail', () => {
  it('acepta emails válidos', () => {
    expect(validateEmail('a@b.com')).toBeNull();
    expect(validateEmail('ventas@tecnoshopmza.com.ar')).toBeNull();
    expect(validateEmail('cliente@tienda.com.ar')).toBeNull();
  });

  it('rechaza vacío, sin arroba y sin dominio', () => {
    expect(validateEmail('')).not.toBeNull();
    expect(validateEmail('   ')).not.toBeNull();
    expect(validateEmail('sin-arroba.com')).not.toBeNull();
    expect(validateEmail('a@b')).not.toBeNull();
  });
});

describe('validatePassword', () => {
  it('requiere mínimo 8 caracteres', () => {
    expect(validatePassword('1234567', 8)).not.toBeNull();
    expect(validatePassword('12345678', 8)).toBeNull();
  });

  it('rechaza vacía', () => {
    expect(validatePassword('', 8)).not.toBeNull();
  });
});

describe('validateBusinessName', () => {
  it('business_name es requerido', () => {
    expect(validateBusinessName('')).not.toBeNull();
    expect(validateBusinessName('  ')).not.toBeNull();
    expect(validateBusinessName('TecnoShop')).toBeNull();
  });
});

describe('validateLogin', () => {
  it('reporta los campos faltantes', () => {
    const errors = validateLogin({ email: '', password: '' });
    expect(errors.email).toBeTruthy();
    expect(errors.password).toBeTruthy();
  });

  it('sin errores cuando todo es válido', () => {
    expect(
      validateLogin({ email: 'a@b.com', password: 'secreto' }),
    ).toEqual({});
  });
});

describe('validateRegister', () => {
  it('reporta business_name, email y password inválidos', () => {
    const errors = validateRegister({ business_name: '', email: 'x', password: 'corta' });
    expect(errors.business_name).toBeTruthy();
    expect(errors.email).toBeTruthy();
    expect(errors.password).toBeTruthy();
  });

  it('sin errores con datos válidos', () => {
    expect(
      validateRegister({
        business_name: 'TecnoShop',
        email: 'ventas@tecnoshopmza.com.ar',
        password: 'Demo2026!',
      }),
    ).toEqual({});
  });
});