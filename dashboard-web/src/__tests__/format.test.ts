import { describe, expect, it } from 'vitest';

import { formatCurrency, formatDuration, formatDateTime } from '@/lib/format';

describe('formatDuration', () => {
  it('formatea segundos sueltos', () => {
    expect(formatDuration(0)).toBe('0s');
    expect(formatDuration(12)).toBe('12s');
    expect(formatDuration(59)).toBe('59s');
  });

  it('formatea minutos con resto de segundos', () => {
    expect(formatDuration(60)).toBe('1m');
    expect(formatDuration(90)).toBe('1m 30s');
    expect(formatDuration(3599)).toBe('59m 59s');
  });

  it('formatea horas con resto de minutos', () => {
    expect(formatDuration(3600)).toBe('1h');
    expect(formatDuration(3661)).toBe('1h 1m');
    expect(formatDuration(86399)).toBe('23h 59m');
  });

  it('formatea días con resto de horas', () => {
    expect(formatDuration(86400)).toBe('1d');
    expect(formatDuration(90000)).toBe('1d 1h');
  });

  it('redondea fracciones y maneja valores no numéricos', () => {
    expect(formatDuration(12.7)).toBe('13s');
    expect(formatDuration(null)).toBe('—');
    expect(formatDuration(undefined)).toBe('—');
  });

  it('acepta strings numéricos (la API serializa DECIMAL/numeric como string)', () => {
    expect(formatDuration('90')).toBe('1m 30s');
    expect(formatDuration('3660.9')).toBe('1h 1m');
    expect(formatDuration('no-num')).toBe('—');
  });
});

describe('formatCurrency', () => {
  it('formatea con $ y 2 decimales en es-AR', () => {
    expect(formatCurrency(349.99)).toBe('$349,99');
    expect(formatCurrency('24.99')).toBe('$24,99');
    expect(formatCurrency(0)).toBe('$0,00');
  });

  it('agrupa miles', () => {
    expect(formatCurrency(1599.5)).toBe('$1.599,50');
  });

  it('maneja valores ausentes o no numéricos', () => {
    expect(formatCurrency(null)).toBe('—');
    expect(formatCurrency(undefined)).toBe('—');
    expect(formatCurrency('abc')).toBe('—');
  });
});

describe('formatDateTime', () => {
  it('devuelve em dash para valores nulos (resolved_at puede ser NULL)', () => {
    expect(formatDateTime(null)).toBe('—');
    expect(formatDateTime(undefined)).toBe('—');
  });
});