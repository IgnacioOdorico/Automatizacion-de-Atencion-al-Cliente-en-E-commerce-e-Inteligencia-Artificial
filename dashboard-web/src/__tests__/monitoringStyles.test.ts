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

describe('Franja de estado y KPIs de En vivo (contraste AA)', () => {
  it('título y detalle del estado del bot sobre la tarjeta', () => {
    expect(contrastRatio(color('.mon-bot__title', 'color'), surfaces['bg-surface'])).toBeGreaterThanOrEqual(AA);
    expect(contrastRatio(color('.mon-bot__detail', 'color'), surfaces['bg-surface'])).toBeGreaterThanOrEqual(AA);
  });

  it('etiqueta, valor y ayuda de cada KPI', () => {
    for (const selector of ['.mon-kpi__label', '.mon-kpi__value', '.mon-kpi__hint']) {
      expect(contrastRatio(color(selector, 'color'), surfaces['bg-surface']), selector).toBeGreaterThanOrEqual(AA);
    }
  });

  it('el valor con tono (urgentes, errores) sigue siendo legible', () => {
    for (const selector of ['.mon-kpi--warning .mon-kpi__value', '.mon-kpi__part--danger']) {
      expect(contrastRatio(color(selector, 'color'), surfaces['bg-surface']), selector).toBeGreaterThanOrEqual(AA);
    }
  });
});

describe('Feed de eventos (contraste AA)', () => {
  it('texto de la tarjeta: tipo, hora, detalle y texto exacto del cliente o del bot', () => {
    for (const selector of ['.mon-event__type', '.mon-event__time', '.mon-event__detail']) {
      expect(contrastRatio(color(selector, 'color'), surfaces['bg-surface']), selector).toBeGreaterThanOrEqual(AA);
    }
    const quote = color('.mon-quote', 'color');
    const quoteBg = color('.mon-quote', 'background');
    expect(contrastRatio(quote, over(quoteBg, surfaces['bg-surface']))).toBeGreaterThanOrEqual(AA);
  });

  it('chips de filtro, apagados y encendidos', () => {
    expect(contrastRatio(color('.mon-chip', 'color'), surfaces['bg-surface'])).toBeGreaterThanOrEqual(AA);
    const selector = ".mon-chip[aria-pressed='true']";
    const bg = color(selector, 'background');
    expect(contrastRatio(color(selector, 'color'), over(bg, surfaces['bg-surface']))).toBeGreaterThanOrEqual(AA);
  });

  it('el aviso de eventos nuevos en pausa', () => {
    const bg = color('.mon-pending', 'background');
    expect(contrastRatio(color('.mon-pending', 'color'), over(bg, surfaces['bg-canvas']))).toBeGreaterThanOrEqual(AA);
  });
});

/** Cuerpo de TODOS los bloques `@media (prefers-reduced-motion: reduce) { ... }` (llaves anidadas). */
function reducedMotionBlocks(source: string): string {
  const marker = '@media (prefers-reduced-motion: reduce)';
  let out = '';
  let from = 0;
  for (;;) {
    const start = source.indexOf(marker, from);
    if (start === -1) return out;
    const open = source.indexOf('{', start);
    let depth = 0;
    let i = open;
    for (; i < source.length; i += 1) {
      if (source[i] === '{') depth += 1;
      if (source[i] === '}') {
        depth -= 1;
        if (depth === 0) break;
      }
    }
    out += source.slice(open + 1, i);
    from = i + 1;
  }
}

describe('Movimiento reducido en el feed', () => {
  const block = reducedMotionBlocks(css);

  it('sin animación, el evento nuevo queda marcado de forma estática', () => {
    expect(block).toMatch(/\.mon-event--fresh[^{]*\{[^}]*background/);
  });

  it('el punto pulsante del estado del bot se queda quieto', () => {
    expect(block).toMatch(/\.mon-bot__dot[^{]*\{[^}]*animation:\s*none/);
  });
});

