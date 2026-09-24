import { describe, expect, it } from 'vitest';

import { axisTickIndices, isoDateShortLabel } from '@/lib/chartAxis';

describe('isoDateShortLabel: fecha calendario UTC ("YYYY-MM-DD") a "dd/mm" sin pasar por Date', () => {
  it('formatea sin conversión de zona horaria (la fecha ya es un día calendario UTC)', () => {
    expect(isoDateShortLabel('2026-09-14')).toBe('14/09');
    expect(isoDateShortLabel('2026-01-01')).toBe('01/01');
    expect(isoDateShortLabel('2026-12-31')).toBe('31/12');
  });

  it('una fecha inválida no rompe: se muestra tal cual', () => {
    expect(isoDateShortLabel('')).toBe('—');
    expect(isoDateShortLabel('no-es-fecha')).toBe('no-es-fecha');
  });
});

describe('axisTickIndices: qué índices del eje mostrar como etiqueta sin amontonarse', () => {
  it('con pocos puntos, muestra todos', () => {
    expect(axisTickIndices(1, 6)).toEqual([0]);
    expect(axisTickIndices(2, 6)).toEqual([0, 1]);
    expect(axisTickIndices(6, 6)).toEqual([0, 1, 2, 3, 4, 5]);
  });

  it('con más puntos que el máximo, siempre incluye el primero y el último', () => {
    const idx = axisTickIndices(31, 6);
    expect(idx[0]).toBe(0);
    expect(idx[idx.length - 1]).toBe(30);
    expect(idx.length).toBeLessThanOrEqual(6);
  });

  it('los índices están ordenados y sin repetidos', () => {
    const idx = axisTickIndices(90, 6);
    const sorted = [...idx].sort((a, b) => a - b);
    expect(idx).toEqual(sorted);
    expect(new Set(idx).size).toBe(idx.length);
  });

  it('con 0 puntos no rompe', () => {
    expect(axisTickIndices(0, 6)).toEqual([]);
  });
});
