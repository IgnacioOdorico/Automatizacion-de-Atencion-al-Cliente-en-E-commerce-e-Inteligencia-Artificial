/**
 * Utilidades de contraste WCAG 2.x para verificar la paleta oscura directamente
 * contra el CSS real (tokens.css / global.css), sin renderizar nada.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export interface Rgb {
  r: number;
  g: number;
  b: number;
}

export interface Rgba extends Rgb {
  a: number;
}

/** Lee el CSS real. Vitest corre desde dashboard-web/ (no se usa `new URL(.., import.meta.url)`: Vite lo trata como asset). */
export function readStyle(name: 'tokens.css' | 'global.css'): string {
  return readFileSync(resolve(process.cwd(), 'src', 'styles', name), 'utf-8');
}

/** Valor de una custom property (`--text-3`) declarada en tokens.css. */
export function token(tokensCss: string, name: string): string {
  const match = new RegExp(`--${name}:\\s*([^;]+);`).exec(tokensCss);
  if (!match) throw new Error(`No existe el token --${name}`);
  return match[1].trim();
}

/** Reemplaza `var(--x)` por su valor real. */
export function resolveVars(value: string, tokensCss: string): string {
  return value.replace(/var\(--([\w-]+)\)/g, (_, name: string) => token(tokensCss, name));
}

/** Declaración de una propiedad dentro de la regla con ese selector exacto. */
export function declaration(css: string, selector: string, prop: string): string {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const rule = new RegExp(`(?:^|\\})\\s*${escaped}\\s*\\{([^}]*)\\}`, 'm').exec(css);
  if (!rule) throw new Error(`No se encontró la regla ${selector}`);
  const decl = new RegExp(`(?:^|[\\s;])${prop}:\\s*([^;]+);`).exec(rule[1]);
  if (!decl) throw new Error(`La regla ${selector} no declara ${prop}`);
  return decl[1].trim();
}

export function parseColor(input: string): Rgba {
  const value = input.trim();
  const hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(value);
  if (hex) {
    const h =
      hex[1].length === 3
        ? hex[1]
            .split('')
            .map((c) => c + c)
            .join('')
        : hex[1];
    return {
      r: parseInt(h.slice(0, 2), 16),
      g: parseInt(h.slice(2, 4), 16),
      b: parseInt(h.slice(4, 6), 16),
      a: 1,
    };
  }
  const rgba = /^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)$/i.exec(value);
  if (rgba) {
    return { r: +rgba[1], g: +rgba[2], b: +rgba[3], a: rgba[4] === undefined ? 1 : +rgba[4] };
  }
  throw new Error(`Color no soportado: ${input}`);
}

/** Color con transparencia pintado sobre un fondo opaco. */
export function over(fg: Rgba, bg: Rgb): Rgb {
  return {
    r: fg.r * fg.a + bg.r * (1 - fg.a),
    g: fg.g * fg.a + bg.g * (1 - fg.a),
    b: fg.b * fg.a + bg.b * (1 - fg.a),
  };
}

function luminance({ r, g, b }: Rgb): number {
  const [R, G, B] = [r, g, b].map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

export function contrastRatio(a: Rgb, b: Rgb): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}
