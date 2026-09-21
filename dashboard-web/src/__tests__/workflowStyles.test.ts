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

describe('Lista de ejecuciones (contraste AA)', () => {
  const card = surface('bg-surface');
  const selected = over(color(".wf-run[aria-current='true']", 'background'), card);

  it('número, estado, hora, duración y error de cada fila, normal y elegida', () => {
    for (const selector of ['.wf-run', '.wf-run__id', '.wf-run__dur', '.wf-run__meta', '.wf-run__error']) {
      const text = color(selector, 'color');
      expect(contrastRatio(text, card), selector).toBeGreaterThanOrEqual(AA);
      expect(contrastRatio(text, selected), `${selector} elegida`).toBeGreaterThanOrEqual(AA);
    }
  });

  it('el aviso de ejecución nueva pasa por colores legibles durante toda la animación', () => {
    const block = /@keyframes wf-run-fresh\s*\{([\s\S]*?)\n\}/.exec(css)?.[1] ?? '';
    expect(block).not.toBe('');
    for (const bg of block.match(/background:\s*[^;]+;/g) ?? []) {
      const value = resolveVars(bg.replace(/^background:\s*/, '').replace(/;$/, ''), tokens);
      if (value === 'transparent') continue;
      expect(contrastRatio(color('.wf-run__id', 'color'), over(parseColor(value), card)), value).toBeGreaterThanOrEqual(AA);
    }
  });
});

describe('Seguir en vivo y leyenda de la reproducción (contraste AA)', () => {
  it('el interruptor, apagado y encendido, sobre el fondo de la página', () => {
    expect(contrastRatio(color('.wf-follow', 'color'), canvas)).toBeGreaterThanOrEqual(AA);
    const on = over(color(".wf-follow[aria-checked='true']", 'background'), canvas);
    expect(contrastRatio(color(".wf-follow[aria-checked='true']", 'color'), on)).toBeGreaterThanOrEqual(AA);
  });

  it('el estado del interruptor no depende solo del color: el punto encendido y apagado se distinguen del fondo', () => {
    expect(contrastRatio(color('.wf-follow__dot', 'background'), canvas)).toBeGreaterThanOrEqual(GRAPHIC);
    expect(contrastRatio(color(".wf-follow[aria-checked='true'] .wf-follow__dot", 'background'), canvas)).toBeGreaterThanOrEqual(GRAPHIC);
  });

  it('paso y nodo actual de la reproducción sobre su leyenda', () => {
    const bg = over(color('.wf-caption', 'background'), canvas);
    expect(contrastRatio(color('.wf-caption', 'color'), bg)).toBeGreaterThanOrEqual(AA);
    expect(contrastRatio(color('.wf-caption__node', 'color'), bg)).toBeGreaterThanOrEqual(AA);
  });
});

describe('Panel de detalle del nodo (contraste AA)', () => {
  const panel = surface('bg-surface');

  it('título, tipo, notas y datos sobre el panel', () => {
    for (const selector of [
      '.wf-detail__title h3',
      '.wf-detail__title p',
      '.wf-detail__note',
      '.wf-detail__facts dt',
      '.wf-detail__facts dd',
      '.wf-detail__out h4',
    ]) {
      expect(contrastRatio(color(selector, 'color'), panel), selector).toBeGreaterThanOrEqual(AA);
    }
  });

  it('el error del nodo sobre su recuadro', () => {
    const bg = over(color('.wf-detail__error', 'background'), panel);
    expect(contrastRatio(color('.wf-detail__error', 'color'), bg)).toBeGreaterThanOrEqual(AA);
  });

  it('la vista previa de la salida sobre su bloque', () => {
    const bg = color('.wf-preview', 'background');
    expect(contrastRatio(color('.wf-preview', 'color'), over(bg, panel))).toBeGreaterThanOrEqual(AA);
  });

  it('la vista previa es monoespaciada, scrolleable y parte las líneas largas', () => {
    expect(declaration(css, '.wf-preview', 'font-family')).toContain('monospace');
    expect(declaration(css, '.wf-preview', 'overflow')).toBe('auto');
    expect(declaration(css, '.wf-preview', 'white-space')).toBe('pre-wrap');
  });
});

describe('Ejecución encabezado y avisos (contraste AA)', () => {
  const card = surface('bg-surface');

  it('encabezado de la ejecución y avisos sobre su tarjeta', () => {
    for (const selector of ['.wf-exec__row', '.wf-exec__title', '.wf-exec__error', '.wf-notice', '.wf-notices']) {
      expect(contrastRatio(color(selector, 'color'), card), selector).toBeGreaterThanOrEqual(AA);
    }
  });
});

describe('Métricas de la tesis y leyenda (contraste AA)', () => {
  const card = surface('bg-surface');
  const inner = surface('bg-surface-2');

  it('título e introducción sobre la tarjeta', () => {
    expect(contrastRatio(color('.wf-metrics__intro', 'color'), card)).toBeGreaterThanOrEqual(AA);
  });

  it('cada métrica: sigla, flujo, valor, nombre, definición, fórmula y muestras sobre su bloque', () => {
    for (const selector of [
      '.wf-metric__short',
      '.wf-metric__flow',
      '.wf-metric__value',
      '.wf-metric__name',
      '.wf-metric__measures',
      '.wf-metric__sample',
    ]) {
      expect(contrastRatio(color(selector, 'color'), inner), selector).toBeGreaterThanOrEqual(AA);
    }
    const formulaBg = color('.wf-metric__formula code', 'background');
    expect(contrastRatio(color('.wf-metric__formula code', 'color'), over(formulaBg, inner))).toBeGreaterThanOrEqual(AA);
  });

  it('la leyenda: textos sobre el fondo de la página y muestras que se distinguen', () => {
    expect(contrastRatio(color('.wf-legend__list', 'color'), canvas)).toBeGreaterThanOrEqual(AA);
    expect(contrastRatio(color('.wf-legend__hint', 'color'), canvas)).toBeGreaterThanOrEqual(AA);
    const tagBg = over(color('.wf-legend__tag', 'background'), canvas);
    expect(contrastRatio(color('.wf-legend__tag', 'color'), tagBg)).toBeGreaterThanOrEqual(AA);
    expect(contrastRatio(color('.wf-legend__swatch--success', 'color'), over(color('.wf-legend__swatch--success', 'background'), canvas))).toBeGreaterThanOrEqual(GRAPHIC);
    expect(contrastRatio(color('.wf-legend__swatch--error', 'color'), over(color('.wf-legend__swatch--error', 'background'), canvas))).toBeGreaterThanOrEqual(GRAPHIC);
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

  it('el indicador de "Seguir en vivo" y la ejecución nueva de la lista quedan quietos', () => {
    expect(block).toMatch(/\.wf-follow\[aria-checked='true'\] \.wf-follow__dot[^{]*\{[^}]*animation:\s*none/);
    expect(block).toMatch(/\.wf-run--fresh[^{]*\{[^}]*animation:\s*none/);
    expect(block).toMatch(/\.wf-run--fresh[^{]*\{[^}]*background/);
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
