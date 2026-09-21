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

/**
 * Guardas del CSS de la sección Monitoreo sobre el archivo real: contraste AA
 * de lo que se agrega y movimiento reducido. Se completa a medida que se suman
 * pestañas (ver cada describe).
 */

const AA = 4.5;
const tokens = readStyle('tokens.css');
const css = readStyle('global.css');

const surfaces: Record<string, Rgb> = {
  'bg-canvas': parseColor(token(tokens, 'bg-canvas')),
  'bg-surface': parseColor(token(tokens, 'bg-surface')),
  'bg-surface-2': parseColor(token(tokens, 'bg-surface-2')),
};

const color = (selector: string, prop: string) =>
  parseColor(resolveVars(declaration(css, selector, prop), tokens));

describe('Pestañas del monitoreo (contraste AA)', () => {
  it('pestaña inactiva: texto sobre el riel', () => {
    const text = color('.mon-tab', 'color');
    expect(contrastRatio(text, surfaces['bg-surface'])).toBeGreaterThanOrEqual(AA);
  });

  it('pestaña activa: texto sobre su fondo de marca translúcido', () => {
    const selector = ".mon-tab[aria-selected='true']";
    const text = color(selector, 'color');
    const bg = color(selector, 'background');
    expect(contrastRatio(text, over(bg, surfaces['bg-surface']))).toBeGreaterThanOrEqual(AA);
  });
});
