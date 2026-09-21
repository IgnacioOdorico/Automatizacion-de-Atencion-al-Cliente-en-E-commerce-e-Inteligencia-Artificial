import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

// nginx resuelve el host del upstream UNA vez al cargar la config. Si el contenedor
// dashboard-api se recrea (rebuild, reinicio de Docker) y cambia de IP, un
// `proxy_pass http://dashboard-api:8000/` fijo queda apuntando a la IP vieja y
// /api responde 502 hasta reiniciar el web. Estos tests fijan la config que evita eso.
// (vitest corre con cwd en dashboard-web/; jsdom no soporta URLs file: de import.meta.url)
const conf = readFileSync(resolve(process.cwd(), 'nginx.conf'), 'utf8');

describe('nginx.conf: proxy /api hacia dashboard-api', () => {
  it('usa el DNS embebido de Docker para re-resolver el upstream', () => {
    expect(conf).toMatch(/^\s*resolver\s+127\.0\.0\.11\b/m);
  });

  it('el proxy_pass usa una variable (nginx la resuelve en cada request)', () => {
    expect(conf).toMatch(/^\s*set\s+\$\w+\s+http:\/\/dashboard-api:8000\s*;/m);
    expect(conf).toMatch(/^\s*proxy_pass\s+\$\w+\s*;/m);
  });

  it('quita el prefijo /api antes de pasar al backend', () => {
    expect(conf).toMatch(/^\s*rewrite\s+\^\/api\/\(\.\*\)\$\s+\/\$1\s+break\s*;/m);
  });

  it('no deja un proxy_pass con host fijo (resolución estática)', () => {
    expect(conf).not.toMatch(/proxy_pass\s+http:\/\/dashboard-api/);
  });

  it('mantiene el fallback SPA', () => {
    expect(conf).toMatch(/try_files\s+\$uri\s+\$uri\/\s+\/index\.html\s*;/);
  });
});
