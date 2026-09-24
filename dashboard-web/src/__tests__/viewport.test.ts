import { describe, expect, it } from 'vitest';

import {
  FOLLOW_SCALE,
  MAX_SCALE,
  MIN_SCALE,
  COMPACT_SCALE,
  COMPACT_WIDTH,
  centerOn,
  clampScale,
  fitView,
  initialView,
  isInView,
  keyboardAction,
  panBy,
  pinchView,
  preferredHeight,
  toScreen,
  toWorld,
  viewCss,
  wheelZoomFactor,
  zoomAt,
} from '@/lib/viewport';

const bounds = { minX: 0, minY: 0, maxX: 1000, maxY: 200 };

describe('fitView (ajustar a pantalla)', () => {
  it('escala para que entre todo el diagrama y lo centra', () => {
    const view = fitView(bounds, { width: 500, height: 300 }, { padding: 0 });
    expect(view.k).toBeCloseTo(0.5);
    expect(view.x).toBeCloseTo(0);
    // el diagrama mide 100 de alto ya escalado: queda centrado en los 300 del lienzo
    expect(view.y).toBeCloseTo(100);
  });

  it('respeta el margen', () => {
    const view = fitView(bounds, { width: 500, height: 300 }, { padding: 20 });
    expect(view.k).toBeCloseTo((500 - 40) / 1000);
    expect(view.x).toBeCloseTo(20);
  });

  it('un diagrama chico no se agranda más del tope', () => {
    const view = fitView({ minX: 0, minY: 0, maxX: 100, maxY: 50 }, { width: 1000, height: 1000 }, {
      padding: 0,
      maxScale: 1.2,
    });
    expect(view.k).toBeCloseTo(1.2);
  });

  it('el alto también limita: gana el lado más ajustado', () => {
    const view = fitView({ minX: 0, minY: 0, maxX: 100, maxY: 1000 }, { width: 1000, height: 500 }, { padding: 0 });
    expect(view.k).toBeCloseTo(0.5);
  });

  it('centra un diagrama que no arranca en el origen', () => {
    const view = fitView({ minX: 200, minY: 100, maxX: 600, maxY: 300 }, { width: 400, height: 200 }, { padding: 0, maxScale: 1 });
    // el centro del diagrama (400, 200) cae en el centro del lienzo (200, 100)
    const center = toScreen(view, { x: 400, y: 200 });
    expect(center.x).toBeCloseTo(200);
    expect(center.y).toBeCloseTo(100);
  });

  it('un lienzo sin tamaño (todavía no se midió) deja la vista neutra', () => {
    expect(fitView(bounds, { width: 0, height: 0 })).toEqual({ x: 0, y: 0, k: 1 });
  });

  it('un diagrama de un solo punto no divide por cero', () => {
    const view = fitView({ minX: 5, minY: 5, maxX: 5, maxY: 5 }, { width: 400, height: 300 });
    expect(Number.isFinite(view.k)).toBe(true);
    expect(Number.isFinite(view.x)).toBe(true);
  });

  it('nunca baja del mínimo', () => {
    const view = fitView({ minX: 0, minY: 0, maxX: 1_000_000, maxY: 10 }, { width: 300, height: 300 });
    expect(view.k).toBeGreaterThanOrEqual(MIN_SCALE);
  });
});

describe('zoomAt (zoom hacia el cursor)', () => {
  it('el punto del mundo bajo el cursor no se mueve', () => {
    const view = { x: 40, y: -20, k: 0.8 };
    const cursor = { x: 300, y: 180 };
    const before = toWorld(view, cursor);
    const next = zoomAt(view, 1.5, cursor);
    expect(next.k).toBeCloseTo(1.2);
    const after = toWorld(next, cursor);
    expect(after.x).toBeCloseTo(before.x);
    expect(after.y).toBeCloseTo(before.y);
  });

  it('respeta el tope y sigue anclado al cursor', () => {
    const view = { x: 0, y: 0, k: 2.5 };
    const cursor = { x: 100, y: 50 };
    const before = toWorld(view, cursor);
    const next = zoomAt(view, 10, cursor);
    expect(next.k).toBe(MAX_SCALE);
    const after = toWorld(next, cursor);
    expect(after.x).toBeCloseTo(before.x);
    expect(after.y).toBeCloseTo(before.y);
  });

  it('respeta el mínimo', () => {
    expect(zoomAt({ x: 0, y: 0, k: 0.12 }, 0.1, { x: 0, y: 0 }).k).toBe(MIN_SCALE);
  });
});

describe('clampScale y conversiones', () => {
  it('acota la escala', () => {
    expect(clampScale(50)).toBe(MAX_SCALE);
    expect(clampScale(0.0001)).toBe(MIN_SCALE);
    expect(clampScale(1)).toBe(1);
  });

  it('toScreen y toWorld son inversas', () => {
    const view = { x: 12, y: 34, k: 0.7 };
    const p = { x: 210, y: -55 };
    const back = toWorld(view, toScreen(view, p));
    expect(back.x).toBeCloseTo(p.x);
    expect(back.y).toBeCloseTo(p.y);
  });

  it('viewCss arma el transform CSS del grupo que se mueve', () => {
    expect(viewCss({ x: 10, y: -5, k: 0.5 })).toBe('translate(10px, -5px) scale(0.5)');
  });
});

describe('panBy (arrastrar)', () => {
  it('desplaza sin tocar la escala', () => {
    expect(panBy({ x: 10, y: 20, k: 0.6 }, -4, 7)).toEqual({ x: 6, y: 27, k: 0.6 });
  });
});

describe('wheelZoomFactor (Ctrl + rueda o pellizco del trackpad)', () => {
  it('rueda hacia arriba acerca y hacia abajo aleja', () => {
    expect(wheelZoomFactor(-100)).toBeGreaterThan(1);
    expect(wheelZoomFactor(100)).toBeLessThan(1);
    expect(wheelZoomFactor(0)).toBe(1);
  });

  it('es simétrico: acercar y alejar lo mismo vuelve al punto de partida', () => {
    expect(wheelZoomFactor(80) * wheelZoomFactor(-80)).toBeCloseTo(1);
  });

  it('una rueda por líneas (deltaMode 1) pesa más que por píxeles', () => {
    expect(wheelZoomFactor(-3, 1)).toBeGreaterThan(wheelZoomFactor(-3, 0));
  });

  it('un gesto enorme no dispara el zoom', () => {
    expect(wheelZoomFactor(-100000)).toBeLessThanOrEqual(2);
    expect(wheelZoomFactor(100000)).toBeGreaterThanOrEqual(0.5);
  });
});

describe('pinchView (dos dedos)', () => {
  it('con el mismo centro, separar los dedos acerca alrededor de ese centro', () => {
    const view = { x: 0, y: 0, k: 1 };
    const mid = { x: 200, y: 100 };
    const before = toWorld(view, mid);
    const next = pinchView(view, { mid, dist: 100 }, { mid, dist: 200 });
    expect(next.k).toBeCloseTo(2);
    const after = toWorld(next, mid);
    expect(after.x).toBeCloseTo(before.x);
    expect(after.y).toBeCloseTo(before.y);
  });

  it('mover el centro sin cambiar la distancia solo desplaza', () => {
    const next = pinchView(
      { x: 0, y: 0, k: 1 },
      { mid: { x: 100, y: 100 }, dist: 80 },
      { mid: { x: 130, y: 90 }, dist: 80 },
    );
    expect(next.k).toBeCloseTo(1);
    expect(next.x).toBeCloseTo(30);
    expect(next.y).toBeCloseTo(-10);
  });

  it('con los dedos superpuestos (distancia 0) no rompe', () => {
    const next = pinchView({ x: 0, y: 0, k: 1 }, { mid: { x: 0, y: 0 }, dist: 0 }, { mid: { x: 0, y: 0 }, dist: 10 });
    expect(Number.isFinite(next.k)).toBe(true);
  });
});

describe('keyboardAction (flechas, +, -, 0)', () => {
  it('las flechas mueven la vista hacia donde apuntan', () => {
    const right = keyboardAction('ArrowRight');
    expect(right).toMatchObject({ type: 'pan' });
    expect(right && right.type === 'pan' && right.dx).toBeLessThan(0);
    const up = keyboardAction('ArrowUp');
    expect(up && up.type === 'pan' && up.dy).toBeGreaterThan(0);
    const left = keyboardAction('ArrowLeft');
    expect(left && left.type === 'pan' && left.dx).toBeGreaterThan(0);
    const down = keyboardAction('ArrowDown');
    expect(down && down.type === 'pan' && down.dy).toBeLessThan(0);
  });

  it('+ y = acercan, - aleja, 0 ajusta a pantalla', () => {
    const plus = keyboardAction('+');
    expect(plus && plus.type === 'zoom' && plus.factor).toBeGreaterThan(1);
    expect(keyboardAction('=')).toEqual(keyboardAction('+'));
    const minus = keyboardAction('-');
    expect(minus && minus.type === 'zoom' && minus.factor).toBeLessThan(1);
    expect(keyboardAction('0')).toEqual({ type: 'fit' });
  });

  it('otras teclas no hacen nada', () => {
    expect(keyboardAction('Enter')).toBeNull();
    expect(keyboardAction('a')).toBeNull();
    expect(keyboardAction('Tab')).toBeNull();
  });
});

describe('initialView (con qué vista se abre el diagrama)', () => {
  const wide = { minX: 0, minY: 0, maxX: 2200, maxY: 400 };

  it('en un lienzo ancho es el ajuste a pantalla de siempre', () => {
    const size = { width: 1000, height: 400 };
    expect(initialView(wide, size)).toEqual(fitView(wide, size));
    const edge = { width: COMPACT_WIDTH, height: 400 };
    expect(initialView(wide, edge)).toEqual(fitView(wide, edge));
  });

  it('un diagrama que entero ya se lee en un lienzo angosto tampoco se toca', () => {
    const small = { minX: 0, minY: 0, maxX: 300, maxY: 200 };
    const size = { width: 340, height: 300 };
    expect(initialView(small, size)).toEqual(fitView(small, size));
  });

  it('en un lienzo angosto, donde entero quedaría ilegible, se abre acercado desde el principio del flujo', () => {
    const size = { width: 340, height: 300 };
    const view = initialView(wide, size, { padding: 20 });
    expect(view.k).toBe(COMPACT_SCALE);
    // el borde izquierdo del diagrama queda a un margen del borde izquierdo del lienzo
    expect(toScreen(view, { x: wide.minX, y: 0 }).x).toBeCloseTo(20);
    // y en vertical queda centrado
    expect(toScreen(view, { x: 0, y: (wide.minY + wide.maxY) / 2 }).y).toBeCloseTo(150);
  });

  it('sin tamaño de lienzo, la vista neutra', () => {
    expect(initialView(wide, { width: 0, height: 0 })).toEqual({ x: 0, y: 0, k: 1 });
  });
});

describe('preferredHeight (el lienzo no deja aire de sobra alrededor de un diagrama chato)', () => {
  const wide = { minX: 0, minY: 0, maxX: 2000, maxY: 400 };

  it('alto del dibujo ya escalado, más los márgenes y el lugar de los controles', () => {
    const height = preferredHeight(wide, 1000, { padding: 32, reserve: 88, min: 100, max: 900 });
    const k = (1000 - 64) / 2000;
    expect(height).toBe(Math.round(400 * k + 64 + 88));
  });

  it('nunca baja del mínimo ni pasa del máximo', () => {
    expect(preferredHeight(wide, 1000, { min: 500, max: 900 })).toBe(500);
    expect(preferredHeight({ minX: 0, minY: 0, maxX: 100, maxY: 5000 }, 1000, { min: 300, max: 580 })).toBe(580);
  });

  it('un diagrama chico no se agranda de más para calcular el alto', () => {
    const tiny = { minX: 0, minY: 0, maxX: 100, maxY: 50 };
    const height = preferredHeight(tiny, 1000, { padding: 0, reserve: 0, min: 0, max: 900, maxScale: 1.25 });
    expect(height).toBe(Math.round(50 * 1.25));
  });

  it('sin ancho medido no opina', () => {
    expect(preferredHeight(wide, 0)).toBeNull();
  });
});

describe('centerOn (llevar la cámara a un nodo)', () => {
  const size = { width: 800, height: 400 };
  const box = { x: 1000, y: 200, w: 150, h: 100 };

  it('el centro del nodo queda en el centro del lienzo', () => {
    const view = centerOn({ x: 0, y: 0, k: 1 }, size, box);
    const c = toScreen(view, { x: box.x + box.w / 2, y: box.y + box.h / 2 });
    expect(c.x).toBeCloseTo(400);
    expect(c.y).toBeCloseTo(200);
  });

  it('si el zoom actual es menor al legible, sube hasta el legible', () => {
    expect(centerOn({ x: 0, y: 0, k: 0.3 }, size, box).k).toBe(FOLLOW_SCALE);
  });

  it('si ya se lee, conserva el zoom (aunque sea mayor)', () => {
    expect(centerOn({ x: 0, y: 0, k: 1.4 }, size, box).k).toBe(1.4);
  });

  it('un mínimo propio pisa al legible', () => {
    expect(centerOn({ x: 0, y: 0, k: 0.2 }, size, box, { minScale: 0.5 }).k).toBe(0.5);
  });
});

describe('isInView (¿el nodo se ve entero?)', () => {
  const size = { width: 800, height: 400 };
  const box = { x: 100, y: 100, w: 150, h: 100 };

  it('dentro del lienzo, con margen', () => {
    expect(isInView({ x: 0, y: 0, k: 1 }, size, box)).toBe(true);
  });

  it('cortado por un borde o afuera, no', () => {
    expect(isInView({ x: -200, y: 0, k: 1 }, size, box)).toBe(false);
    expect(isInView({ x: 0, y: 350, k: 1 }, size, box)).toBe(false);
    expect(isInView({ x: 5000, y: 0, k: 1 }, size, box)).toBe(false);
  });

  it('pegado al borde (dentro del margen) tampoco cuenta como visible', () => {
    expect(isInView({ x: -90, y: 0, k: 1 }, size, box, 24)).toBe(false);
    expect(isInView({ x: -90, y: 0, k: 1 }, size, box, 0)).toBe(true);
  });
});
