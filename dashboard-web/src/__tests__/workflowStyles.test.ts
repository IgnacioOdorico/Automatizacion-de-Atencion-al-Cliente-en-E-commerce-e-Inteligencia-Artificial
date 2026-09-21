import { describe, expect, it } from 'vitest';

import { contrastRatio, declaration, over, parseColor, readStyle, resolveVars, token, type Rgb } from './helpers/contrast';

/**
 * Guardas del CSS de la pestaña Workflow sobre el archivo real: contraste del
 * texto de las tarjetas en cada estado, de las conexiones y de los controles, y
 * movimiento reducido.
 */

const AA = 4.5;
const GRAPHIC = 3;
const tokens = readStyle('tokens.css');
const css = readStyle('global.css');

const surface = (name: string): Rgb => parseColor(token(tokens, name));
const canvas = surface('bg-canvas');

const value = (selector: string, prop: string) => resolveVars(declaration(css, selector, prop), tokens);
const color = (selector: string, prop: string) => parseColor(value(selector, prop));

/** Color de un trazo o relleno (puede ser translúcido) ya pintado sobre el lienzo. */
const onCanvas = (selector: string, prop: string) => over(color(selector, prop), canvas);

describe('Texto de las tarjetas de nodo (contraste AA)', () => {
  it('nombre y datos sobre la tarjeta normal', () => {
    const card = over(color('.wf-node__card', 'fill'), canvas);
    expect(contrastRatio(color('.wf-node__name', 'fill'), card)).toBeGreaterThanOrEqual(AA);
    expect(contrastRatio(color('.wf-node__meta', 'fill'), card)).toBeGreaterThanOrEqual(AA);
  });

  it('nombre y datos sobre las tarjetas de nodo correcto y de nodo con error', () => {
    for (const state of ['success', 'error']) {
      const card = over(color(`.wf-node--${state} .wf-node__card`, 'fill'), canvas);
      expect(contrastRatio(color('.wf-node__name', 'fill'), card), state).toBeGreaterThanOrEqual(AA);
      expect(contrastRatio(color('.wf-node__meta', 'fill'), card), state).toBeGreaterThanOrEqual(AA);
    }
  });

  it('lo que no se ejecutó está apagado pero sigue siendo legible', () => {
    const card = over(color('.wf-node--dim .wf-node__card', 'fill'), canvas);
    expect(contrastRatio(color('.wf-node--dim .wf-node__name', 'fill'), card)).toBeGreaterThanOrEqual(AA);
    expect(contrastRatio(color('.wf-node--dim .wf-node__meta', 'fill'), card)).toBeGreaterThanOrEqual(AA);
  });

  it('la etiqueta "Deshabilitado" sobre su tarjeta', () => {
    const card = over(color('.wf-node--dim .wf-node__card', 'fill'), canvas);
    expect(contrastRatio(color('.wf-node--dim .wf-node__tag', 'fill'), card)).toBeGreaterThanOrEqual(AA);
  });
});

describe('Rótulos de rama (contraste AA)', () => {
  it('"Sí" / "No" normales, iluminados y apagados', () => {
    const normal = over(color('.wf-elabel rect', 'fill'), canvas);
    expect(contrastRatio(color('.wf-elabel text', 'fill'), normal)).toBeGreaterThanOrEqual(AA);
    const active = over(color('.wf-elabel--active rect', 'fill'), canvas);
    expect(contrastRatio(color('.wf-elabel--active text', 'fill'), active)).toBeGreaterThanOrEqual(AA);
    expect(contrastRatio(color('.wf-elabel--inactive text', 'fill'), normal)).toBeGreaterThanOrEqual(AA);
  });
});

describe('Elementos gráficos (contraste 3:1 contra el lienzo)', () => {
  it('las conexiones normales y las del camino recorrido se distinguen del fondo', () => {
    expect(contrastRatio(onCanvas('.wf-edge', 'stroke'), canvas)).toBeGreaterThanOrEqual(GRAPHIC);
    expect(contrastRatio(onCanvas('.wf-edge--active', 'stroke'), canvas)).toBeGreaterThanOrEqual(GRAPHIC);
    expect(contrastRatio(onCanvas('.wf-arrow--idle', 'fill'), canvas)).toBeGreaterThanOrEqual(GRAPHIC);
  });

  it('el borde de un nodo correcto, con error o en curso', () => {
    for (const selector of [
      '.wf-node--success .wf-node__card',
      '.wf-node--error .wf-node__card',
      '.wf-node--running .wf-node__card',
    ]) {
      expect(contrastRatio(onCanvas(selector, 'stroke'), canvas), selector).toBeGreaterThanOrEqual(GRAPHIC);
    }
  });

  it('el foco del teclado sobre un nodo', () => {
    expect(contrastRatio(onCanvas('.wf-node:focus-visible .wf-node__card', 'stroke'), canvas)).toBeGreaterThanOrEqual(
      GRAPHIC,
    );
  });

  it('las insignias de estado (ícono en la esquina)', () => {
    for (const state of ['success', 'error', 'running', 'waiting']) {
      const badge = over(parseColor(value(`.wf-node--${state} .wf-node__badge`, 'color')), canvas);
      expect(contrastRatio(badge, canvas), state).toBeGreaterThanOrEqual(GRAPHIC);
    }
  });
});

describe('Controles del lienzo (contraste AA)', () => {
  it('nivel de zoom y botones sobre su barra', () => {
    const bar = over(color('.wf-controls', 'background'), canvas);
    expect(contrastRatio(color('.wf-zoom__level', 'color'), bar)).toBeGreaterThanOrEqual(AA);
    expect(contrastRatio(color('.wf-controls__btn', 'color'), bar)).toBeGreaterThanOrEqual(AA);
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

describe('Movimiento reducido en el diagrama', () => {
  const block = reducedMotionBlocks(css);

  it('la conexión que "fluye" queda quieta y continua', () => {
    expect(block).toMatch(/\.wf-edge--flowing[^{]*\{[^}]*animation:\s*none/);
  });

  it('el nodo actual de la reproducción no pulsa: queda marcado con un trazo fijo', () => {
    expect(block).toMatch(/\.wf-node--current[^{]*\{[^}]*animation:\s*none/);
    expect(block).toMatch(/\.wf-node--current[^{]*\{[^}]*stroke-width/);
  });
});

describe('Lienzo', () => {
  it('captura los gestos táctiles (si no, el navegador scrollea en vez de mover el diagrama)', () => {
    expect(declaration(css, '.wf-canvas', 'touch-action')).toBe('none');
  });

  it('no deja seleccionar texto al arrastrar', () => {
    expect(declaration(css, '.wf-canvas', 'user-select')).toBe('none');
  });
});
