import { describe, expect, it } from 'vitest';

import { donutArcs } from '@/lib/donutChart';

const GEOMETRY = { cx: 50, cy: 50, outerR: 40, innerR: 24 };

describe('donutArcs: ángulos y path de cada porción', () => {
  it('sin datos (todo en 0) no devuelve porciones', () => {
    expect(donutArcs([{ key: 'a', value: 0, color: '#fff' }], GEOMETRY)).toEqual([]);
    expect(donutArcs([], GEOMETRY)).toEqual([]);
  });

  it('dos valores iguales se reparten 50/50, empezando arriba (12 en punto)', () => {
    const arcs = donutArcs(
      [
        { key: 'a', value: 1, color: '#111' },
        { key: 'b', value: 1, color: '#222' },
      ],
      GEOMETRY,
    );
    expect(arcs).toHaveLength(2);
    expect(arcs[0].startAngle).toBeCloseTo(0);
    expect(arcs[0].endAngle).toBeCloseTo(180);
    expect(arcs[1].startAngle).toBeCloseTo(180);
    expect(arcs[1].endAngle).toBeCloseTo(360);
  });

  it('una porción en 0 no se dibuja (no genera un arco de ángulo 0)', () => {
    const arcs = donutArcs(
      [
        { key: 'a', value: 3, color: '#111' },
        { key: 'b', value: 0, color: '#222' },
        { key: 'c', value: 1, color: '#333' },
      ],
      GEOMETRY,
    );
    expect(arcs.map((a) => a.key)).toEqual(['a', 'c']);
  });

  it('una sola porción con el 100%: se dibuja igual (sin path degenerado)', () => {
    const arcs = donutArcs([{ key: 'a', value: 5, color: '#111' }], GEOMETRY);
    expect(arcs).toHaveLength(1);
    expect(arcs[0].endAngle - arcs[0].startAngle).toBeLessThanOrEqual(360);
    expect(arcs[0].endAngle - arcs[0].startAngle).toBeGreaterThan(359);
    expect(arcs[0].path).toMatch(/^M[\d\s.,-]+A/);
  });

  it('cada porción trae un path SVG no vacío y su porcentaje', () => {
    const arcs = donutArcs(
      [
        { key: 'a', value: 3, color: '#111' },
        { key: 'b', value: 1, color: '#222' },
      ],
      GEOMETRY,
    );
    expect(arcs[0].path.length).toBeGreaterThan(10);
    expect(arcs[0].percent).toBeCloseTo(75);
    expect(arcs[1].percent).toBeCloseTo(25);
  });
});
