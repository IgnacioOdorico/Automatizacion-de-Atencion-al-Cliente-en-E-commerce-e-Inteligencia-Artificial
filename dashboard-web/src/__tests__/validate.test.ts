import { describe, expect, it } from 'vitest';

import {
  normalizePhone,
  validateBusinessName,
  validateEmail,
  validateLogin,
  validatePassword,
  validatePhone,
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
describe('normalizePhone', () => {
  it('quita espacios, guiones, puntos y paréntesis', () => {
    expect(normalizePhone('+54 9 261 555-1234')).toBe('+5492615551234');
    expect(normalizePhone(' +1 (415) 555.2671 ')).toBe('+14155552671');
  });
});

describe('validatePhone (E.164 — coincide con el regex del backend)', () => {
  it('acepta números internacionales con distintos separadores', () => {
    expect(validatePhone('+54 9 261 555 1234')).toBeNull();
    expect(validatePhone('+5492615551234')).toBeNull();
    expect(validatePhone('+1 (415) 555-2671')).toBeNull();
    expect(validatePhone('+54-9-261-555-1234')).toBeNull();
  });

  it('exige el número', () => {
    expect(validatePhone('')).toBe('Ingresá el número de WhatsApp.');
    expect(validatePhone('   ')).toBe('Ingresá el número de WhatsApp.');
  });

  it('exige el + y el código de país (formato internacional)', () => {
    expect(validatePhone('5492615551234')).toContain('formato internacional');
    expect(validatePhone('0261 555 1234')).toContain('formato internacional');
  });

  it('rechaza ceros iniciales, letras y largos fuera de 7-15 dígitos', () => {
    expect(validatePhone('+0123456789')).toContain('no es válido');
    expect(validatePhone('+54abc1234567')).toContain('no es válido');
    expect(validatePhone('+123456')).toContain('no es válido');
    expect(validatePhone('+1234567890123456')).toContain('no es válido');
  });

  it('acepta los extremos válidos (7 y 15 dígitos)', () => {
    expect(validatePhone('+1234567')).toBeNull();
    expect(validatePhone('+123456789012345')).toBeNull();
  });
});
