import { describe, expect, it } from 'vitest';

import {
  EVENT_TYPE_OPTIONS,
  describeEvent,
  eventTypeMeta,
  severityMeta,
} from '@/lib/monitoring';

import { makeEvent } from './helpers/monitoringFixtures';

describe('EVENT_TYPE_OPTIONS (filtros por tipo)', () => {
  it('cubre los 7 tipos de la API, en el orden del ciclo del pedido y del chat', () => {
    expect(EVENT_TYPE_OPTIONS.map((o) => o.value)).toEqual([
      'order_received',
      'order_processed',
      'order_notified',
      'chat_message',
      'bot_reply',
      'ticket_created',
      'stock_alert',
    ]);
  });

  it('las etiquetas están en español y sin jerga interna', () => {
    expect(EVENT_TYPE_OPTIONS.map((o) => o.label)).toEqual([
      'Pedido recibido',
      'Pedido procesado',
      'Cliente notificado',
      'Mensaje del cliente',
      'Respuesta del bot',
      'Ticket creado',
      'Alerta de stock bajo',
    ]);
  });
});

describe('eventTypeMeta', () => {
  it('cada tipo tiene etiqueta e ícono', () => {
    for (const { value } of EVENT_TYPE_OPTIONS) {
      const meta = eventTypeMeta(value);
      expect(meta.label, value).toBeTruthy();
      expect(meta.icon, value).toBeTruthy();
    }
  });

  it('un tipo nuevo de la API no rompe la pantalla', () => {
    expect(eventTypeMeta('workflow_paused')).toEqual({ label: 'Evento', icon: 'activity' });
  });
});

describe('severityMeta (color + ícono + texto, nunca solo color)', () => {
  it('mapea las cuatro severidades', () => {
    expect(severityMeta('info')).toEqual({ label: 'Info', tone: 'brand', icon: 'info' });
    expect(severityMeta('success')).toEqual({ label: 'Correcto', tone: 'success', icon: 'check' });
    expect(severityMeta('warning')).toEqual({ label: 'Atención', tone: 'warning', icon: 'warning' });
    expect(severityMeta('error')).toEqual({ label: 'Error', tone: 'danger', icon: 'error' });
  });

  it('una severidad desconocida cae en info', () => {
    expect(severityMeta('critical').label).toBe('Info');
  });
});

describe('describeEvent: pedidos', () => {
  const received = makeEvent(
    'order_received',
    7,
    {
      order_number: 'ORD-2026-0007',
      customer_name: 'Ana Pérez',
      customer_email: 'ana@example.com',
      quantity: 2,
      total_amount: 349.99,
      product_sku: 'PROD-001',
      product_name: 'Notebook 14"',
    },
    { severity: 'info', refs: { order_id: 7, order_number: 'ORD-2026-0007' } },
  );

  it('pedido recibido: título, cliente y detalle del producto', () => {
    const view = describeEvent(received);
    expect(view.typeLabel).toBe('Pedido recibido');
    expect(view.icon).toBe('package');
    expect(view.headline).toBe('ORD-2026-0007 · Ana Pérez');
    expect(view.detail).toBe('2 × Notebook 14" · $349,99');
    expect(view.quote).toBeNull();
  });

  it('pedido recibido: el detalle lista todos los datos exactos', () => {
    const facts = Object.fromEntries(describeEvent(received).facts.map((f) => [f.label, f.value]));
    expect(facts['Fecha y hora']).toBe('21/09/2026 11:03:22');
    expect(facts['Pedido']).toBe('ORD-2026-0007');
    expect(facts['Cliente']).toBe('Ana Pérez');
    expect(facts['Email']).toBe('ana@example.com');
    expect(facts['Producto']).toBe('Notebook 14" (PROD-001)');
    expect(facts['Cantidad']).toBe('2');
    expect(facts['Total']).toBe('$349,99');
    expect(facts['Canal']).toBeUndefined();
  });

  it('pedido procesado: estado actual y tiempo MTTD', () => {
    const view = describeEvent(
      makeEvent(
        'order_processed',
        7,
        { order_number: 'ORD-2026-0007', status: 'confirmed', total_amount: 349.99, mttd_seconds: 0.435 },
        { severity: 'success' },
      ),
    );
    expect(view.typeLabel).toBe('Pedido procesado');
    expect(view.headline).toBe('ORD-2026-0007 · Confirmado');
    expect(view.detail).toBe('Procesado en 435 ms (MTTD)');
    expect(view.chips).toContainEqual({ text: 'Confirmado', tone: 'success' });
  });

  it('pedido sin stock: chip de advertencia con texto', () => {
    const view = describeEvent(
      makeEvent(
        'order_processed',
        8,
        { order_number: 'ORD-2026-0008', status: 'no_stock', total_amount: 100, mttd_seconds: null },
        { severity: 'warning' },
      ),
    );
    expect(view.chips).toContainEqual({ text: 'Sin stock', tone: 'warning' });
    expect(view.detail).toBeNull();
  });

  it('cliente notificado: tiempo MTTR', () => {
    const view = describeEvent(
      makeEvent(
        'order_notified',
        7,
        { order_number: 'ORD-2026-0007', status: 'confirmed', mttr_seconds: 1.234 },
        { severity: 'success' },
      ),
    );
    expect(view.typeLabel).toBe('Cliente notificado');
    expect(view.icon).toBe('mail');
    expect(view.detail).toBe('Avisado en 1,2 s (MTTR)');
  });
});

describe('describeEvent: chat y bot (el texto va tal cual)', () => {
  const message = '  ¿Dónde está mi pedido <b>ORD-2026-0007</b>?\nGracias  ';
  const chat = makeEvent(
    'chat_message',
    41,
    { user_id: '5492610000000', message },
    { channel: 'whatsapp', severity: 'info' },
  );

  it('mensaje del cliente: canal, contacto y texto exacto', () => {
    const view = describeEvent(chat);
    expect(view.typeLabel).toBe('Mensaje del cliente');
    expect(view.icon).toBe('message');
    expect(view.headline).toBe('+54 9 2610000000');
    expect(view.quote).toBe(message);
  });

  it('mensaje del cliente: el detalle lo muestra sin tocar (espacios, saltos y HTML incluidos)', () => {
    const byLabel = Object.fromEntries(describeEvent(chat).facts.map((f) => [f.label, f]));
    expect(byLabel['Mensaje'].value).toBe(message);
    expect(byLabel['Mensaje'].block).toBe(true);
    expect(byLabel['Canal'].value).toBe('WhatsApp');
    expect(byLabel['Usuario'].value).toBe('5492610000000');
  });

  it('respuesta del bot: intent, urgencia y TMR como chips con texto', () => {
    const view = describeEvent(
      makeEvent(
        'bot_reply',
        41,
        {
          user_id: '5492610000000',
          ai_response: 'Tu pedido está confirmado y en preparación.',
          intent: 'RECLAMO',
          is_urgent: true,
          tmr_seconds: 3.918,
        },
        { channel: 'telegram', severity: 'warning' },
      ),
    );
    expect(view.typeLabel).toBe('Respuesta del bot');
    expect(view.icon).toBe('bot');
    expect(view.quote).toBe('Tu pedido está confirmado y en preparación.');
    expect(view.chips).toEqual([
      { text: 'Reclamo', tone: 'warning' },
      { text: 'Urgente', tone: 'danger' },
      { text: 'TMR 3,9 s', tone: 'neutral' },
    ]);
    expect(view.headline).toBe('Chat 5492610000000');
  });

  it('respuesta no urgente y sin TMR: no inventa chips', () => {
    const view = describeEvent(
      makeEvent(
        'bot_reply',
        42,
        { user_id: 'u', ai_response: 'Hola', intent: 'GENERAL', is_urgent: false, tmr_seconds: null },
        { channel: 'email' },
      ),
    );
    expect(view.chips).toEqual([{ text: 'Consulta general', tone: 'neutral' }]);
  });
});

describe('describeEvent: tickets y stock', () => {
  it('ticket creado: asunto, prioridad y estado', () => {
    const view = describeEvent(
      makeEvent(
        'ticket_created',
        3,
        { user_id: '5492610000000', subject: 'Reclamo por demora', priority: 'high', status: 'open' },
        { channel: 'whatsapp', severity: 'warning', refs: { ticket_id: 3 } },
      ),
    );
    expect(view.typeLabel).toBe('Ticket creado');
    expect(view.icon).toBe('ticket');
    expect(view.headline).toBe('Reclamo por demora');
    expect(view.detail).toBe('+54 9 2610000000');
    expect(view.chips).toEqual([
      { text: 'Prioridad alta', tone: 'warning' },
      { text: 'Abierto', tone: 'brand' },
    ]);
  });

  it('ticket sin asunto', () => {
    const view = describeEvent(
      makeEvent('ticket_created', 4, { user_id: 'x', subject: null, priority: 'low', status: 'open' }),
    );
    expect(view.headline).toBe('Ticket sin asunto');
  });

  it('alerta de stock: cuántas unidades quedan', () => {
    const low = describeEvent(
      makeEvent(
        'stock_alert',
        1,
        { sku: 'PROD-002', product_name: 'Mouse', stock_actual: 2, stock_min: 5 },
        { severity: 'warning' },
      ),
    );
    expect(low.typeLabel).toBe('Alerta de stock bajo');
    expect(low.headline).toBe('Mouse (PROD-002)');
    expect(low.detail).toBe('Quedan 2 unidades · mínimo 5');

    const last = describeEvent(
      makeEvent('stock_alert', 2, { sku: 'PROD-002', product_name: 'Mouse', stock_actual: 1, stock_min: 5 }),
    );
    expect(last.detail).toBe('Queda 1 unidad · mínimo 5');

    const none = describeEvent(
      makeEvent(
        'stock_alert',
        3,
        { sku: 'PROD-002', product_name: 'Mouse', stock_actual: 0, stock_min: 5 },
        { severity: 'error' },
      ),
    );
    expect(none.detail).toBe('Sin stock · mínimo 5');
  });
});

describe('describeEvent: robustez ante datos faltantes o de tipo inesperado', () => {
  it('un evento con `data` vacío no rompe y muestra guiones', () => {
    const view = describeEvent(makeEvent('order_received', 1, {}));
    expect(view.headline).toBe('—');
    expect(view.detail).toBeNull();
    expect(view.facts.find((f) => f.label === 'Cliente')?.value).toBe('—');
  });

  it('cantidad y monto como texto ("349.99"), como serializa la BD', () => {
    const view = describeEvent(
      makeEvent('order_received', 1, {
        order_number: 'A',
        customer_name: 'B',
        quantity: '3',
        total_amount: '349.99',
        product_name: 'P',
      }),
    );
    expect(view.detail).toBe('3 × P · $349,99');
  });

  it('tipo desconocido: etiqueta genérica y datos como pares clave/valor', () => {
    const view = describeEvent(makeEvent('workflow_paused', 1, { reason: 'manual', count: 3 }));
    expect(view.typeLabel).toBe('Evento');
    const pairs = view.facts.map((f) => [f.label, f.value]);
    expect(pairs).toContainEqual(['reason', 'manual']);
    expect(pairs).toContainEqual(['count', '3']);
  });

  it('objetos anidados en un evento desconocido se muestran como texto plano', () => {
    const view = describeEvent(makeEvent('x', 1, { payload: { a: '<script>alert(1)</script>' } }));
    expect(view.facts.find((f) => f.label === 'payload')?.value).toBe(
      '{"a":"<script>alert(1)</script>"}',
    );
  });
});
