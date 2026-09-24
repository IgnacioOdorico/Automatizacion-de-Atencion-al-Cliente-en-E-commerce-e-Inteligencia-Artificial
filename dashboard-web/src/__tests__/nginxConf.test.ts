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

// ---------------------------------------------------------------------------
// Headers de seguridad y proxy de confianza (Fase 8 / SPEC §6 + hardening).
// ---------------------------------------------------------------------------
const headersConf = readFileSync(resolve(process.cwd(), 'security-headers.conf'), 'utf8');

/** Directivas de la CSP como mapa `directiva -> fuentes`. */
function parseCsp(): Record<string, string[]> {
  const match = headersConf.match(/add_header\s+Content-Security-Policy\s+"([^"]+)"\s+always\s*;/);
  expect(match, 'falta add_header Content-Security-Policy ... always').not.toBeNull();
  const directives: Record<string, string[]> = {};
  for (const part of match![1].split(';')) {
    const [name, ...sources] = part.trim().split(/\s+/);
    if (name) directives[name] = sources;
  }
  return directives;
}

/** Cuerpo de cada bloque `location`, por su ruta. */
function locationBlocks(): Record<string, string> {
  const blocks: Record<string, string> = {};
  for (const m of conf.matchAll(/location\s+([^\s{]+)\s*\{([^}]*)\}/g)) blocks[m[1]] = m[2];
  return blocks;
}

describe('nginx.conf: headers de seguridad', () => {
  it('manda nosniff, DENY, Referrer-Policy estricta y Permissions-Policy (siempre)', () => {
    expect(headersConf).toMatch(/add_header\s+X-Content-Type-Options\s+"nosniff"\s+always\s*;/);
    expect(headersConf).toMatch(/add_header\s+X-Frame-Options\s+"DENY"\s+always\s*;/);
    expect(headersConf).toMatch(
      /add_header\s+Referrer-Policy\s+"strict-origin-when-cross-origin"\s+always\s*;/,
    );
    expect(headersConf).toMatch(/add_header\s+Permissions-Policy\s+"[^"]*camera=\(\)[^"]*"\s+always\s*;/);
  });

  it('la CSP prohíbe embeberse, plugins y cambiar <base>', () => {
    const csp = parseCsp();
    expect(csp['frame-ancestors']).toEqual(["'none'"]);
    expect(csp['object-src']).toEqual(["'none'"]);
    expect(csp['base-uri']).toEqual(["'self'"]);
    expect(csp['form-action']).toEqual(["'self'"]);
    expect(csp['default-src']).toEqual(["'self'"]);
  });

  it('la CSP solo ejecuta scripts propios: sin unsafe-inline, unsafe-eval ni comodines', () => {
    const csp = parseCsp();
    expect(csp['script-src']).toEqual(["'self'"]);
    for (const [name, sources] of Object.entries(csp)) {
      expect(sources, name).not.toContain("'unsafe-eval'");
      expect(sources, name).not.toContain('*');
      expect(sources, name).not.toContain('http:');
      expect(sources, name).not.toContain('https:');
    }
    expect(csp['script-src']).not.toContain("'unsafe-inline'");
  });

  it('la CSP deja hablar solo con el mismo origen (la API va por /api)', () => {
    expect(parseCsp()['connect-src']).toEqual(["'self'"]);
  });

  it('la CSP permite Google Fonts (Inter) y nada más externo', () => {
    const csp = parseCsp();
    expect(csp['style-src']).toContain('https://fonts.googleapis.com');
    expect(csp['font-src']).toContain('https://fonts.gstatic.com');
    expect(csp['img-src']).toEqual(["'self'", 'data:']);
  });

  it('el server incluye los headers y todo location con add_header los repite', () => {
    // nginx: un add_header dentro de un location descarta los del nivel server.
    expect(conf).toMatch(/^\s{4}include\s+\/etc\/nginx\/snippets\/security-headers\.conf\s*;/m);
    for (const [path, body] of Object.entries(locationBlocks())) {
      if (/add_header/.test(body)) {
        expect(body, `location ${path}`).toMatch(
          /include\s+\/etc\/nginx\/snippets\/security-headers\.conf\s*;/,
        );
      }
    }
  });

  it('no revela la versión de nginx', () => {
    expect(conf).toMatch(/^\s*server_tokens\s+off\s*;/m);
  });

  it('el Dockerfile copia el snippet donde el include lo busca', () => {
    const dockerfile = readFileSync(resolve(process.cwd(), 'Dockerfile'), 'utf8');
    expect(dockerfile).toMatch(/COPY\s+security-headers\.conf\s+\/etc\/nginx\/snippets\/security-headers\.conf/);
  });
});

describe('nginx.conf: cliente real hacia la API (rate limit por IP)', () => {
  const api = locationBlocks()['/api/'];

  it('pasa la IP que ve nginx en X-Real-IP', () => {
    expect(api).toMatch(/proxy_set_header\s+X-Real-IP\s+\$remote_addr\s*;/);
  });

  it('pisa X-Forwarded-For (no concatena lo que mande el cliente, es spoofeable)', () => {
    expect(api).toMatch(/proxy_set_header\s+X-Forwarded-For\s+\$remote_addr\s*;/);
    expect(api).not.toMatch(/proxy_add_x_forwarded_for/);
  });

  it('limita el tamaño del body que llega a la API', () => {
    expect(conf).toMatch(/^\s*client_max_body_size\s+\d+[kKmM]\s*;/m);
  });
});
