import { describe, expect, it } from 'vitest';

import {
  contrastRatio,
  declaration,
  over,
  parseColor,
  readStyle,
  resolveVars,
  token,
  type Rgb,
} from './helpers/contrast';

/** WCAG AA para texto normal. */
const AA = 4.5;

const tokens = readStyle('tokens.css');
const css = readStyle('global.css');

const surfaces: Record<string, Rgb> = {
  'bg-canvas': parseColor(token(tokens, 'bg-canvas')),
  'bg-sidebar': parseColor(token(tokens, 'bg-sidebar')),
  'bg-surface': parseColor(token(tokens, 'bg-surface')),
  'bg-surface-2': parseColor(token(tokens, 'bg-surface-2')),
};

describe('Contraste del texto sobre las superficies (WCAG AA, 4.5:1)', () => {
  for (const text of ['text-1', 'text-2', 'text-3']) {
    for (const [name, bg] of Object.entries(surfaces)) {
      it(`--${text} sobre --${name}`, () => {
        const ratio = contrastRatio(parseColor(token(tokens, text)), bg);
        expect(ratio).toBeGreaterThanOrEqual(AA);
      });
    }
  }

  it('--danger (errores de campo, botón de desconexión) sobre canvas y surface', () => {
    const danger = parseColor(token(tokens, 'danger'));
    expect(contrastRatio(danger, surfaces['bg-canvas'])).toBeGreaterThanOrEqual(AA);
    expect(contrastRatio(danger, surfaces['bg-surface'])).toBeGreaterThanOrEqual(AA);
  });
});

describe('Contraste de badges y avisos (texto sobre su fondo translúcido)', () => {
  const badgeSelectors = [
    '.badge--brand',
    '.badge--neutral',
    '.badge--success',
    '.badge--warning',
    '.badge--danger',
  ];

  for (const selector of badgeSelectors) {
    it(`${selector} sobre surface y surface-2`, () => {
      const text = parseColor(resolveVars(declaration(css, selector, 'color'), tokens));
      const bg = parseColor(resolveVars(declaration(css, selector, 'background'), tokens));
      for (const base of [surfaces['bg-surface'], surfaces['bg-surface-2']]) {
        expect(contrastRatio(text, over(bg, base))).toBeGreaterThanOrEqual(AA);
      }
    });
  }

  for (const selector of ['.alert--error', '.alert--success']) {
    it(`${selector} sobre canvas y surface`, () => {
      const text = parseColor(resolveVars(declaration(css, selector, 'color'), tokens));
      const bg = parseColor(resolveVars(declaration(css, selector, 'background'), tokens));
      for (const base of [surfaces['bg-canvas'], surfaces['bg-surface']]) {
        expect(contrastRatio(text, over(bg, base))).toBeGreaterThanOrEqual(AA);
      }
    });
  }

  it('la franja de error de carga (.error-banner) es legible', () => {
    const text = parseColor(declaration(css, '.error-banner', 'color'));
    const bg = parseColor(declaration(css, '.error-banner', 'background').replace(/var\(--danger-soft\)/, token(tokens, 'danger-soft')));
    for (const base of [surfaces['bg-canvas'], surfaces['bg-surface']]) {
      expect(contrastRatio(text, over(bg, base))).toBeGreaterThanOrEqual(AA);
    }
  });
});

describe('Botón primario: texto blanco sobre todo su degradé', () => {
  const white: Rgb = { r: 255, g: 255, b: 255 };

  for (const selector of ['.btn--primary', '.btn--primary:hover:not(:disabled)']) {
    it(`${selector}`, () => {
      const background = resolveVars(declaration(css, selector, 'background'), tokens);
      const stops = background.match(/#[0-9a-f]{6}/gi) ?? [];
      expect(stops.length).toBeGreaterThanOrEqual(2);
      for (const stop of stops) {
        expect(contrastRatio(white, parseColor(stop))).toBeGreaterThanOrEqual(AA);
      }
    });
  }
});
