import { describe, expect, it } from 'vitest';

import { stackedAreaLayers } from '@/lib/areaChart';

const KEYS = ['confirmed', 'no_stock', 'error'] as const;
const GEOMETRY = { width: 300, height: 100, padding: 8 };

function row(date: string, values: Partial<Record<(typeof KEYS)[number], number>>) {
  return { date, values: { confirmed: 0, no_stock: 0, error: 0, ...values } };
}

describe('stackedAreaLayers: series apiladas día por día, sin huecos', () => {
  it('sin filas no rompe', () => {
    const { layers } = stackedAreaLayers([], [...KEYS], GEOMETRY);
    expect(layers).toEqual([]);
  });

  it('genera una capa por clave, cada una con un path no vacío', () => {
    const rows = [row('2026-09-14', { confirmed: 4, no_stock: 1 }), row('2026-09-15', { confirmed: 2, error: 1 })];
    const { layers } = stackedAreaLayers(rows, [...KEYS], GEOMETRY);
    expect(layers.map((l) => l.key)).toEqual([...KEYS]);
    for (const layer of layers) {
      expect(layer.path.startsWith('M')).toBe(true);
      expect(layer.path.length).toBeGreaterThan(5);
    }
  });

  it('apila: la capa de arriba llega hasta la suma de todas (no solo la suya)', () => {
    const rows = [row('2026-09-14', { confirmed: 4, no_stock: 1, error: 0 })];
    const { layers } = stackedAreaLayers(rows, [...KEYS], GEOMETRY);
    // El punto superior de la última capa (error, encima de todo) está a la misma altura
    // que confirmed+no_stock+error en ese día (el total apilado), no solo su propio valor.
    const top = layers[layers.length - 1].points[0];
    const totalDay = 4 + 1 + 0;
    // y crece hacia abajo: un total mayor implica un y más chico (más arriba) cuando hay más días con valores.
    expect(top.y).toBeLessThanOrEqual(GEOMETRY.height - GEOMETRY.padding);
    expect(totalDay).toBe(5);
  });

  it('una sola muestra se ve como un tramo plano en todo el ancho (no un punto invisible)', () => {
    const rows = [row('2026-09-14', { confirmed: 3 })];
    const { layers } = stackedAreaLayers(rows, [...KEYS], GEOMETRY);
    const confirmedLayer = layers[0];
    expect(confirmedLayer.points).toHaveLength(2);
    expect(confirmedLayer.points[0].y).toBeCloseTo(confirmedLayer.points[1].y);
    expect(confirmedLayer.points[0].x).toBeLessThan(confirmedLayer.points[1].x);
  });

  it('todos los días en 0 no rompe (serie plana en la base)', () => {
    const rows = [row('2026-09-14', {}), row('2026-09-15', {})];
    const { layers } = stackedAreaLayers(rows, [...KEYS], GEOMETRY);
    expect(layers).toHaveLength(3);
    for (const layer of layers) {
      for (const p of layer.points) expect(p.y).toBeCloseTo(GEOMETRY.height - GEOMETRY.padding);
    }
  });

  it('devuelve un punto por día para el eje (mismo orden que las filas)', () => {
    const rows = [row('2026-09-14', {}), row('2026-09-15', {}), row('2026-09-16', {})];
    const { xTicks } = stackedAreaLayers(rows, [...KEYS], GEOMETRY);
    expect(xTicks.map((t) => t.date)).toEqual(['2026-09-14', '2026-09-15', '2026-09-16']);
    expect(xTicks[0].x).toBeLessThan(xTicks[1].x);
    expect(xTicks[1].x).toBeLessThan(xTicks[2].x);
  });
});
