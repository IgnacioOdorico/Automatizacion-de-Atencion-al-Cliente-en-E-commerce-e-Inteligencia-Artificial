import { describe, expect, it } from 'vitest';

import {
  CHANNEL_COLORS,
  CHART_COLORS,
  INTENT_COLORS,
  ORDER_STATUS_COLORS,
  channelColor,
  intentColor,
  orderStatusColor,
} from '@/lib/chartColors';
import { contrastRatio, parseColor, readStyle, token } from './helpers/contrast';

const tokens = readStyle('tokens.css');

describe('CHART_COLORS: en sync con --chart-1..8 de tokens.css', () => {
  for (const [n, hex] of Object.entries(CHART_COLORS)) {
    it(`--chart-${n}`, () => {
      expect(token(tokens, `chart-${n}`).toLowerCase()).toBe(hex.toLowerCase());
    });
  }
});

describe('Contraste no-textual (WCAG 1.4.11, >= 3:1) de cada color sobre las superficies del chart', () => {
  const surfaces = [parseColor(token(tokens, 'bg-surface')), parseColor(token(tokens, 'bg-surface-2'))];

  for (const hex of Object.values(CHART_COLORS)) {
    it(`${hex}`, () => {
      const color = parseColor(hex);
      for (const bg of surfaces) {
        expect(contrastRatio(color, bg)).toBeGreaterThanOrEqual(3);
      }
    });
  }
});

describe('Un color por categoría, sin repetir dentro del mismo dominio', () => {
  it('by_status: 8 colores distintos', () => {
    expect(new Set(Object.values(ORDER_STATUS_COLORS)).size).toBe(Object.keys(ORDER_STATUS_COLORS).length);
  });

  it('by_intent: 4 colores distintos', () => {
    expect(new Set(Object.values(INTENT_COLORS)).size).toBe(Object.keys(INTENT_COLORS).length);
  });

  it('canales: 3 colores distintos', () => {
    expect(new Set(Object.values(CHANNEL_COLORS)).size).toBe(Object.keys(CHANNEL_COLORS).length);
  });
});

describe('orderStatusColor / intentColor / channelColor: un valor desconocido no rompe', () => {
  it('cae en el color neutro (chart-8)', () => {
    expect(orderStatusColor('lo-que-sea')).toBe(CHART_COLORS[8]);
    expect(intentColor(null)).toBe(CHART_COLORS[8]);
    expect(channelColor(undefined)).toBe(CHART_COLORS[8]);
  });

  it('un valor del dominio devuelve su color mapeado', () => {
    expect(orderStatusColor('confirmed')).toBe(ORDER_STATUS_COLORS.confirmed);
    expect(intentColor('FAQ')).toBe(INTENT_COLORS.FAQ);
    expect(channelColor('whatsapp')).toBe(CHANNEL_COLORS.whatsapp);
  });
});
