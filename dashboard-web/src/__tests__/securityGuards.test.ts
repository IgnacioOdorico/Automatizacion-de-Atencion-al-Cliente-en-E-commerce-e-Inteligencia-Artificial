import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

// Guardas estáticas de la Fase 8 sobre el código de producción del front: tokens solo
// donde corresponde, sin logs, sin sinks de XSS. (vitest corre con cwd en dashboard-web/)
const SRC = resolve(process.cwd(), 'src');

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return name === '__tests__' ? [] : walk(path);
    return /\.(ts|tsx)$/.test(name) ? [path] : [];
  });
}

// Sin comentarios: nombrar `localStorage` en un comentario no es usarlo.
const stripComments = (code: string) =>
  code.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');

const files = walk(SRC).map((path) => ({
  name: relative(SRC, path).replace(/\\/g, '/'),
  text: stripComments(readFileSync(path, 'utf8')),
}));

const withText = (pattern: RegExp) => files.filter((f) => pattern.test(f.text)).map((f) => f.name);

describe('front: guardas de seguridad sobre el código de producción', () => {
  it('encuentra el código a auditar', () => {
    expect(files.length).toBeGreaterThan(20);
  });

  it('nunca escribe a la consola (un log podría filtrar tokens o datos de clientes)', () => {
    expect(withText(/\bconsole\s*\./)).toEqual([]);
  });

  it('solo tokenStorage toca localStorage/sessionStorage/cookies', () => {
    expect(withText(/\b(localStorage|sessionStorage)\b/)).toEqual(['auth/tokenStorage.ts']);
    expect(withText(/document\s*\.\s*cookie/)).toEqual([]);
  });

  it('los nombres de token solo aparecen en la capa de auth/API', () => {
    expect(withText(/\b(access_token|refresh_token)\b/).sort()).toEqual([
      'api/client.ts',
      'auth/tokenStorage.ts',
      'types/api.ts',
    ]);
  });

  it('el token viaja solo en el header Authorization o en el body, nunca en una URL', () => {
    for (const f of files) {
      expect(f.text, f.name).not.toMatch(/[?&](access_token|refresh_token|token)=/);
    }
    const client = files.find((f) => f.name === 'api/client.ts')!;
    expect(client.text).toMatch(/Authorization = `Bearer \$\{token\}`/);
  });

  it('sin sinks de XSS: innerHTML, dangerouslySetInnerHTML, eval, new Function, document.write', () => {
    expect(withText(/dangerouslySetInnerHTML|\.innerHTML\s*=|\.outerHTML\s*=|insertAdjacentHTML/)).toEqual([]);
    expect(withText(/\beval\s*\(|new\s+Function\s*\(|document\s*\.\s*write/)).toEqual([]);
  });

  it('la única navegación fuera del SPA es la del consentimiento de Gmail', () => {
    expect(withText(/window\s*\.\s*location\s*\.\s*(assign|replace|href\s*=)/)).toEqual([
      'components/connections/GmailCard.tsx',
    ]);
  });
});
