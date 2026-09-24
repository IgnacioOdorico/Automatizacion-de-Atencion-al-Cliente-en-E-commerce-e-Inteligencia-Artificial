import { describe, expect, it } from 'vitest';

import { trapFocusTarget } from '@/lib/focus';

describe('trapFocusTarget (foco atrapado dentro de un modal)', () => {
  it('Tab en el medio deja que el navegador avance solo', () => {
    expect(trapFocusTarget({ count: 4, activeIndex: 1, shift: false })).toBeNull();
    expect(trapFocusTarget({ count: 4, activeIndex: 2, shift: true })).toBeNull();
  });

  it('Tab en el último elemento vuelve al primero', () => {
    expect(trapFocusTarget({ count: 4, activeIndex: 3, shift: false })).toBe(0);
  });

  it('Shift+Tab en el primer elemento salta al último', () => {
    expect(trapFocusTarget({ count: 4, activeIndex: 0, shift: true })).toBe(3);
  });

  it('con el foco fuera del modal, Tab entra por el primero y Shift+Tab por el último', () => {
    expect(trapFocusTarget({ count: 3, activeIndex: -1, shift: false })).toBe(0);
    expect(trapFocusTarget({ count: 3, activeIndex: -1, shift: true })).toBe(2);
  });

  it('un solo elemento enfocable: el foco se queda ahí', () => {
    expect(trapFocusTarget({ count: 1, activeIndex: 0, shift: false })).toBe(0);
    expect(trapFocusTarget({ count: 1, activeIndex: 0, shift: true })).toBe(0);
  });

  it('sin elementos enfocables el foco va al contenedor del modal (-1)', () => {
    expect(trapFocusTarget({ count: 0, activeIndex: -1, shift: false })).toBe(-1);
  });
});
