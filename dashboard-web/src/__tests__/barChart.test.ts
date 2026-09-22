import { describe, expect, it } from 'vitest';

import { barLayout } from '@/lib/barChart';

const GEOMETRY = { width: 200, height: 100, gap: 4 };

describe('barLayout: escala de valores a coordenadas SVG', () => {
  it('sin barras no rompe', () => {
    expect(barLayout([], GEOMETRY)).toEqual([]);
  });

  it('la barra más alta llega al techo (height completo); las demás son proporcionales', () => {
    const bars = barLayout(
      [
        { key: 'a', value: 10 },
        { key: 'b', value: 5 },
      ],
      GEOMETRY,
    );
    expect(bars[0].height).toBeCloseTo(100);
    expect(bars[1].height).toBeCloseTo(50);
    // y = height del lienzo - height de la barra (el origen SVG es arriba a la izquierda)
    expect(bars[0].y).toBeCloseTo(0);
    expect(bars[1].y).toBeCloseTo(50);
  });

  it('todas las barras en 0 (o null) no dividen por cero: quedan aplanadas y marcadas sin dato', () => {
    const bars = barLayout(
      [
        { key: 'a', value: null },
        { key: 'b', value: 0 },
      ],
      GEOMETRY,
    );
    expect(bars[0].height).toBe(0);
    expect(bars[0].hasData).toBe(false);
    expect(bars[1].height).toBe(0);
    expect(bars[1].hasData).toBe(true); // 0 es un dato real (huboa respuestas con 0s); null es "sin dato"
  });

  it('reparte el ancho entre todas las barras con el gap pedido, en orden', () => {
    const bars = barLayout(
      [
        { key: 'a', value: 1 },
        { key: 'b', value: 2 },
        { key: 'c', value: 3 },
      ],
      GEOMETRY,
    );
    expect(bars).toHaveLength(3);
    expect(bars[0].x).toBeLessThan(bars[1].x);
    expect(bars[1].x).toBeLessThan(bars[2].x);
    const totalGap = GEOMETRY.gap * (bars.length - 1);
    const eachWidth = (GEOMETRY.width - totalGap) / bars.length;
    expect(bars[0].width).toBeCloseTo(eachWidth);
  });

  it('acepta un maxValue explícito (para compartir escala entre gráficos)', () => {
    const bars = barLayout([{ key: 'a', value: 5 }], { ...GEOMETRY, maxValue: 10 });
    expect(bars[0].height).toBeCloseTo(50);
  });
});
