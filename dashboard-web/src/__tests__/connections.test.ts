import { describe, expect, it } from 'vitest';

import { ApiError } from '@/api/client';
import { buildChannelCards, channelActions, connectionActionError } from '@/lib/connections';
import type { Connection } from '@/types/api';

function conn(overrides: Partial<Connection> & Pick<Connection, 'channel'>): Connection {
  return {
    id: 1,
    status: 'disconnected',
    external_reference: null,
    connected_at: null,
    ...overrides,
  };
}

describe('buildChannelCards', () => {
  it('ordena siempre WhatsApp, Telegram, Gmail sin importar el orden del server', () => {
    // El backend ordena alfabético por channel: email, telegram, whatsapp.
    const cards = buildChannelCards([
      conn({ id: 3, channel: 'email' }),
      conn({ id: 2, channel: 'telegram' }),
      conn({ id: 1, channel: 'whatsapp' }),
    ]);
    expect(cards.map((c) => c.channel)).toEqual(['whatsapp', 'telegram', 'email']);
  });

  it('mapea el canal de BD "email" a la etiqueta "Gmail"', () => {
    const [, , gmail] = buildChannelCards([
      conn({ channel: 'email', external_reference: 'ventas@tienda.com', status: 'connected' }),
    ]);
    expect(gmail.channel).toBe('email');
    expect(gmail.label).toBe('Gmail');
  });

  it('deriva la etiqueta del front aunque el server mande otra', () => {
    const cards = buildChannelCards([conn({ channel: 'email', label: 'email' })]);
    expect(cards[2].label).toBe('Gmail');
  });

  it('expone estado, referencia externa y fecha de conexión', () => {
    const [whatsapp] = buildChannelCards([
      conn({
        channel: 'whatsapp',
        status: 'connected',
        external_reference: '+5492615551234',
        connected_at: '2026-05-10T14:00:00Z',
      }),
    ]);
    expect(whatsapp.status).toBe('connected');
    expect(whatsapp.statusMeta).toEqual({ label: 'Conectado', tone: 'success' });
    expect(whatsapp.externalReference).toBe('+5492615551234');
    expect(whatsapp.connectedAt).toBe('2026-05-10T14:00:00Z');
  });

  it('completa como desconectados los canales que el server no devolvió', () => {
    const cards = buildChannelCards([conn({ channel: 'telegram', status: 'connected' })]);
    expect(cards).toHaveLength(3);
    expect(cards[0]).toMatchObject({
      channel: 'whatsapp',
      status: 'disconnected',
      externalReference: null,
    });
    expect(cards[1].status).toBe('connected');
  });

  it('sin datos devuelve las tres cards desconectadas', () => {
    expect(buildChannelCards(undefined).map((c) => c.status)).toEqual([
      'disconnected',
      'disconnected',
      'disconnected',
    ]);
  });

  it('ignora canales desconocidos', () => {
    const cards = buildChannelCards([
      { ...conn({ channel: 'whatsapp' }), channel: 'sms' as unknown as Connection['channel'] },
    ]);
    expect(cards.map((c) => c.channel)).toEqual(['whatsapp', 'telegram', 'email']);
    expect(cards[0].status).toBe('disconnected');
  });

  it('un estado desconocido cae a un fallback neutral sin romper', () => {
    const [whatsapp] = buildChannelCards([
      { ...conn({ channel: 'whatsapp' }), status: 'raro' as unknown as Connection['status'] },
    ]);
    expect(whatsapp.statusMeta).toEqual({ label: 'raro', tone: 'neutral' });
  });
});

describe('channelActions', () => {
  it('conectado: solo se puede desconectar', () => {
    expect(channelActions('telegram', 'connected')).toEqual({
      canConnect: false,
      canDisconnect: true,
    });
  });

  it('desconectado: solo se puede conectar', () => {
    expect(channelActions('email', 'disconnected')).toEqual({
      canConnect: true,
      canDisconnect: false,
    });
  });

  it('error: se puede reintentar la conexión o limpiarla', () => {
    expect(channelActions('email', 'error')).toEqual({
      canConnect: true,
      canDisconnect: true,
    });
  });

  it('WhatsApp pendiente: espera la aprobación de Meta, solo se puede cancelar', () => {
    expect(channelActions('whatsapp', 'pending')).toEqual({
      canConnect: false,
      canDisconnect: true,
    });
  });
});

describe('connectionActionError — Telegram start', () => {
  it('sin detalle del server muestra un mensaje propio de la acción', () => {
    const msg = connectionActionError(
      new ApiError(500, '500 Internal Server Error'),
      'telegram-start',
    );
    expect(msg).toBe('No pudimos generar el código de vinculación. Reintentá en unos segundos.');
  });

  it('con detalle del server lo respeta', () => {
    const msg = connectionActionError(
      new ApiError(400, 'Código inválido', 'Código inválido'),
      'telegram-start',
    );
    expect(msg).toBe('Código inválido');
  });

  it('un error de red (no ApiError) explica que no hay conexión con el servidor', () => {
    const msg = connectionActionError(new TypeError('Failed to fetch'), 'telegram-start');
    expect(msg).toContain('No se pudo conectar con el servidor');
  });
});
