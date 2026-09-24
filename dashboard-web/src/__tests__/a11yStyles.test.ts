import { describe, expect, it } from 'vitest';

import { contrastRatio, parseColor, readStyle, token } from './helpers/contrast';

const tokens = readStyle('tokens.css');
const css = readStyle('global.css');

/** Cuerpo de un bloque `@media (...) { ... }` (con llaves anidadas). */
function mediaBlock(source: string, query: string): string {
  const start = source.indexOf(`@media ${query}`);
  if (start === -1) return '';
  const open = source.indexOf('{', start);
  let depth = 0;
  for (let i = open; i < source.length; i += 1) {
    if (source[i] === '{') depth += 1;
    if (source[i] === '}') {
      depth -= 1;
      if (depth === 0) return source.slice(open + 1, i);
    }
  }
  return '';
}

describe('Anillo de foco (WCAG 1.4.11: 3:1 contra el fondo)', () => {
  const surfaces = ['bg-canvas', 'bg-sidebar', 'bg-surface', 'bg-surface-2'];

  for (const surface of surfaces) {
    it(`--focus-ring sobre --${surface}`, () => {
      const ring = parseColor(token(tokens, 'focus-ring'));
      const bg = parseColor(token(tokens, surface));
      expect(contrastRatio(ring, bg)).toBeGreaterThanOrEqual(3);
    });
  }

  it(':focus-visible usa ese anillo (no un color translúcido)', () => {
    const rule = /:focus-visible\s*\{([^}]*)\}/.exec(css);
    expect(rule?.[1]).toContain('var(--focus-ring)');
  });
});

describe('prefers-reduced-motion', () => {
  const block = mediaBlock(css, '(prefers-reduced-motion: reduce)');

  it('existe un bloque que respeta la preferencia', () => {
    expect(block).not.toBe('');
  });

  it('apaga animaciones y transiciones en todo el sitio', () => {
    expect(block).toMatch(/animation-duration:\s*0\.001ms\s*!important/);
    expect(block).toMatch(/transition-duration:\s*0\.001ms\s*!important/);
  });

  it('el spinner de carga sigue girando (es feedback esencial, no decoración)', () => {
    expect(block).toMatch(/\.spinner\s*\{[^}]*animation-duration:\s*1\.6s/);
  });
});
