import { describe, expect, it } from 'vitest';

import { nodeKind } from '@/lib/nodeKinds';

import { flujo1Graph, flujo2Graph } from './helpers/workflowFixtures';

describe('nodeKind (ícono y tipo legible de cada nodo)', () => {
  it.each([
    ['webhook', 'webhook', 'Entrada de datos'],
    ['postgres', 'database', 'Base de datos'],
    ['if', 'branch', 'Condición'],
    ['switch', 'switch', 'Bifurcación'],
    ['emailSend', 'mail', 'email'],
    ['telegram', 'send', 'Telegram'],
    ['httpRequest', 'globe', 'HTTP'],
    ['code', 'code', 'Código'],
    ['function', 'code', 'Código'],
    ['respondToWebhook', 'reply', 'Respuesta'],
    ['set', 'edit', 'datos'],
    ['merge', 'merge', 'Unir'],
    ['wait', 'clock', 'Espera'],
    ['chainLlm', 'ai', 'IA'],
    ['lmChatOpenAi', 'ai', 'OpenAI'],
  ])('%s usa el ícono %s y su etiqueta menciona "%s"', (shortType, icon, label) => {
    const kind = nodeKind(shortType);
    expect(kind.icon).toBe(icon);
    expect(kind.label).toContain(label);
  });

  it('cualquier disparador (…Trigger) usa el ícono de disparador', () => {
    for (const t of ['telegramTrigger', 'gmailTrigger', 'scheduleTrigger', 'manualTrigger']) {
      expect(nodeKind(t).icon).toBe('trigger');
    }
    expect(nodeKind('telegramTrigger').label).toContain('Telegram');
    expect(nodeKind('gmailTrigger').label).toContain('Gmail');
    expect(nodeKind('scheduleTrigger').label).toContain('Disparador');
  });

  it('un tipo desconocido tiene ícono genérico y una etiqueta legible con su nombre', () => {
    const kind = nodeKind('slackThing');
    expect(kind.icon).toBe('node');
    expect(kind.label).toContain('slackThing');
  });

  it('un nodo que ya no existe en el workflow (tipo null) se rotula como tal', () => {
    const kind = nodeKind(null);
    expect(kind.icon).toBe('node');
    expect(kind.label.toLowerCase()).toContain('ya no existe');
  });

  it('cubre todos los tipos reales de los Flujos 1 y 2 sin caer en el genérico', () => {
    const types = new Set([...flujo1Graph.nodes, ...flujo2Graph.nodes].map((n) => n.short_type));
    for (const type of types) {
      expect(nodeKind(type).icon, String(type)).not.toBe('node');
    }
  });

  it('no se deja engañar por una clave heredada del objeto (constructor, __proto__)', () => {
    expect(nodeKind('constructor').icon).toBe('node');
    expect(nodeKind('__proto__').icon).toBe('node');
  });
});
