import { describe, expect, it } from 'vitest';

import { followStep } from '@/lib/followLive';

describe('followStep (modo "Seguir en vivo")', () => {
  it('la primera vez elige la más reciente, sin tratarla como novedad', () => {
    expect(followStep(null, 15)).toEqual({ selectId: 15, seenId: 15, isNew: false });
  });

  it('llega una ejecución nueva: se elige sola y se marca como novedad', () => {
    expect(followStep(15, 16)).toEqual({ selectId: 16, seenId: 16, isNew: true });
  });

  it('si llegaron varias juntas, elige la más nueva', () => {
    expect(followStep(15, 19)).toEqual({ selectId: 19, seenId: 19, isNew: true });
  });

  it('sin novedades no cambia nada', () => {
    expect(followStep(15, 15)).toEqual({ selectId: null, seenId: 15, isNew: false });
  });

  it('una lista más vieja que lo ya visto (otro filtro, una purga) no vuelve atrás', () => {
    expect(followStep(15, 9)).toEqual({ selectId: null, seenId: 15, isNew: false });
  });

  it('sin ejecuciones en la lista no hace nada y conserva lo visto', () => {
    expect(followStep(null, null)).toEqual({ selectId: null, seenId: null, isNew: false });
    expect(followStep(15, null)).toEqual({ selectId: null, seenId: 15, isNew: false });
  });
});
