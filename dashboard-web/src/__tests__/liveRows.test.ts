import { describe, expect, it } from 'vitest';

import { detectNewIds } from '@/lib/liveRows';

describe('detectNewIds (filas nuevas del listado en vivo)', () => {
  it('la primera carga no resalta nada (todo es "ya estaba")', () => {
    expect(detectNewIds(null, [3, 2, 1])).toEqual([]);
  });

  it('un pedido que aparece entre polls se marca como nuevo', () => {
    expect(detectNewIds(new Set([2, 1]), [3, 2, 1])).toEqual([3]);
  });

  it('sin cambios no hay nada nuevo', () => {
    expect(detectNewIds(new Set([2, 1]), [2, 1])).toEqual([]);
  });

  it('un pedido que ya se había visto y vuelve a aparecer no es nuevo', () => {
    expect(detectNewIds(new Set([1, 2, 3]), [3, 1])).toEqual([]);
  });

  it('varios pedidos nuevos a la vez conservan el orden de la lista', () => {
    expect(detectNewIds(new Set([1]), [5, 4, 1])).toEqual([5, 4]);
  });

  it('lista vacía', () => {
    expect(detectNewIds(new Set([1]), [])).toEqual([]);
  });
});
