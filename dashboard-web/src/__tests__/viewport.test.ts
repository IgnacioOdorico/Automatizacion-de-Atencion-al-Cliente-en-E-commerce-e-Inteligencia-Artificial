import { describe, expect, it } from 'vitest';

import {
  MAX_SCALE,
  MIN_SCALE,
  clampScale,
  fitView,
  keyboardAction,
  panBy,
  pinchView,
  toScreen,
  toWorld,
  viewTransform,
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

  it('viewTransform arma el atributo transform del <g>', () => {
    expect(viewTransform({ x: 10, y: -5, k: 0.5 })).toBe('translate(10 -5) scale(0.5)');
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
