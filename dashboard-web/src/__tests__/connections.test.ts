import { describe, expect, it } from 'vitest';

import { ApiError } from '@/api/client';
import {
  buildChannelCards,
  channelActions,
  connectionActionError,
  connectionsAliasPath,
  disconnectCopy,
  gmailReturnNotice,
  isGoogleConsentUrl,
  parseGmailReturn,
  whatsappStatusNote,
} from '@/lib/connections';
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
    expect(msg).toContain('No pudimos comunicarnos con el servidor');
  });
});

describe('connectionActionError — Gmail', () => {
  it('503 (faltan credenciales de Google en el server) da un mensaje claro y accionable', () => {
    const msg = connectionActionError(
      new ApiError(
        503,
        'Google OAuth no configurado (DASHBOARD_GOOGLE_CLIENT_ID / DASHBOARD_GOOGLE_REDIRECT_URI)',
        'Google OAuth no configurado (DASHBOARD_GOOGLE_CLIENT_ID / DASHBOARD_GOOGLE_REDIRECT_URI)',
      ),
      'gmail-connect',
    );
    expect(msg).toContain('Gmail todavía no está configurado');
    expect(msg).toContain('credenciales de Google');
    expect(msg).not.toContain('DASHBOARD_');
  });

  it('502 avisa que Google no respondió', () => {
    const msg = connectionActionError(
      new ApiError(502, 'Error al contactar los servicios de Google', 'Error al contactar los servicios de Google'),
      'gmail-connect',
    );
    expect(msg).toContain('Google no respondió');
  });

  it('otro error sin detalle usa el mensaje propio de Gmail', () => {
    const msg = connectionActionError(new ApiError(500, '500 Internal Server Error'), 'gmail-connect');
    expect(msg).toBe('No pudimos iniciar la conexión con Gmail. Reintentá en unos segundos.');
  });
});

describe('isGoogleConsentUrl', () => {
  it('acepta la URL de consentimiento de Google', () => {
    expect(
      isGoogleConsentUrl('https://accounts.google.com/o/oauth2/v2/auth?client_id=abc&state=xyz'),
    ).toBe(true);
  });

  it('rechaza otros hosts, http y valores no URL (no redirigir a cualquier lado)', () => {
    expect(isGoogleConsentUrl('https://evil.example.com/o/oauth2/v2/auth')).toBe(false);
    expect(isGoogleConsentUrl('https://accounts.google.com.evil.example.com/auth')).toBe(false);
    expect(isGoogleConsentUrl('http://accounts.google.com/o/oauth2/v2/auth')).toBe(false);
    expect(isGoogleConsentUrl('javascript:alert(1)')).toBe(false);
    expect(isGoogleConsentUrl('')).toBe(false);
    expect(isGoogleConsentUrl(undefined)).toBe(false);
  });
});

describe('parseGmailReturn', () => {
  it('reconoce el retorno exitoso del callback', () => {
    expect(parseGmailReturn('?gmail=connected')).toEqual({ result: 'connected' });
    expect(parseGmailReturn('gmail=connected')).toEqual({ result: 'connected' });
  });

  it('reconoce un retorno con error y su código de motivo', () => {
    expect(parseGmailReturn('?gmail=error&reason=denied')).toEqual({
      result: 'error',
      reason: 'denied',
    });
    for (const reason of [
      'denied',
      'google_error',
      'invalid_state',
      'missing_code',
      'exchange_failed',
      'upstream',
      'no_email',
      'no_refresh',
      'internal',
    ]) {
      expect(parseGmailReturn(`?gmail=error&reason=${reason}`)).toEqual({
        result: 'error',
        reason,
      });
    }
  });

  it('un error sin motivo o con motivo desconocido queda sin código (nunca se refleja el valor crudo)', () => {
    expect(parseGmailReturn('?gmail=error')).toEqual({ result: 'error', reason: null });
    expect(parseGmailReturn('?gmail=error&reason=<script>alert(1)</script>')).toEqual({
      result: 'error',
      reason: null,
    });
    expect(parseGmailReturn('?gmail=error&reason=DENIED')).toEqual({
      result: 'error',
      reason: null,
    });
  });

  it('ignora query ausente, vacío o con valores desconocidos', () => {
    expect(parseGmailReturn('')).toBeNull();
    expect(parseGmailReturn('?otra=1')).toBeNull();
    expect(parseGmailReturn('?gmail=hackeado')).toBeNull();
    expect(parseGmailReturn('?reason=denied')).toBeNull();
  });

  it('convive con otros parámetros', () => {
    expect(parseGmailReturn('?x=1&gmail=connected')).toEqual({ result: 'connected' });
  });
});

describe('gmailReturnNotice', () => {
  const connected = buildChannelCards([
    conn({ channel: 'email', status: 'connected', external_reference: 'ventas@tienda.com' }),
  ])[2];
  const disconnected = buildChannelCards([])[2];

  it('sin retorno de Google no hay aviso', () => {
    expect(gmailReturnNotice(null, connected, true)).toBeNull();
  });

  it('muestra el email autorizado al volver conectado', () => {
    expect(gmailReturnNotice({ result: 'connected' }, connected, true)).toEqual({
      tone: 'success',
      text: 'Gmail conectado. Cuenta autorizada: ventas@tienda.com.',
    });
  });

  it('espera a tener los datos antes de decidir', () => {
    expect(gmailReturnNotice({ result: 'connected' }, disconnected, false)).toBeNull();
  });

  it('si el server no confirma la conexión avisa en vez de mostrar éxito', () => {
    const notice = gmailReturnNotice({ result: 'connected' }, disconnected, true);
    expect(notice?.tone).toBe('error');
    expect(notice?.text).toContain('no figura como conectado');
  });

  it('un retorno con error sin motivo muestra el mensaje genérico', () => {
    const notice = gmailReturnNotice({ result: 'error', reason: null }, disconnected, true);
    expect(notice?.tone).toBe('error');
    expect(notice?.text).toContain('Google no completó la autorización');
  });

  it('un error no espera a los datos: se avisa enseguida', () => {
    const notice = gmailReturnNotice({ result: 'error', reason: 'denied' }, disconnected, false);
    expect(notice?.tone).toBe('error');
  });

  it('cada motivo tiene su mensaje claro en voseo, distinto entre sí', () => {
    const reasons = [
      'denied',
      'google_error',
      'invalid_state',
      'missing_code',
      'exchange_failed',
      'upstream',
      'no_email',
      'no_refresh',
      'internal',
    ] as const;
    const texts = reasons.map((reason) => {
      const notice = gmailReturnNotice({ result: 'error', reason }, disconnected, true);
      expect(notice?.tone).toBe('error');
      expect(notice?.text.length).toBeGreaterThan(20);
      return notice?.text;
    });
    expect(new Set(texts).size).toBe(reasons.length);
  });

  it('cancelar en Google se explica como una cancelación del usuario', () => {
    const notice = gmailReturnNotice({ result: 'error', reason: 'denied' }, disconnected, true);
    expect(notice?.text).toContain('Cancelaste');
    expect(notice?.text).toContain('Reintentá');
  });

  it('state vencido invita a iniciar la conexión de nuevo', () => {
    const notice = gmailReturnNotice({ result: 'error', reason: 'invalid_state' }, disconnected, true);
    expect(notice?.text).toContain('Iniciá la conexión');
  });

  it('un motivo que no está en el catálogo cae al genérico sin reflejarlo en pantalla', () => {
    const forged = { result: 'error', reason: '<img src=x onerror=alert(1)>' } as never;
    const notice = gmailReturnNotice(forged, disconnected, true);
    expect(notice?.text).toContain('Google no completó la autorización');
    expect(notice?.text).not.toContain('<img');
    expect(notice?.text).not.toContain('onerror');
  });
});

describe('connectionsAliasPath', () => {
  it('redirige /connections (backend) a /conexiones (front) preservando el query', () => {
    expect(connectionsAliasPath('?gmail=connected')).toBe('/conexiones?gmail=connected');
  });

  it('sin query o con query vacío deja la ruta limpia', () => {
    expect(connectionsAliasPath('')).toBe('/conexiones');
    expect(connectionsAliasPath('?')).toBe('/conexiones');
  });
});

describe('connectionActionError — WhatsApp', () => {
  it('422 (número rechazado por el server) explica el formato', () => {
    const msg = connectionActionError(new ApiError(422, '422 Unprocessable Entity'), 'whatsapp-request');
    expect(msg).toContain('formato internacional');
  });

  it('respeta el detalle de otros errores del server', () => {
    const msg = connectionActionError(new ApiError(400, 'x', 'Número inválido'), 'whatsapp-request');
    expect(msg).toBe('Número inválido');
  });

  it('sin detalle usa el mensaje propio de la solicitud', () => {
    const msg = connectionActionError(new ApiError(500, '500 Internal Server Error'), 'whatsapp-request');
    expect(msg).toBe('No pudimos enviar la solicitud de aprobación. Reintentá en unos segundos.');
  });
});

describe('whatsappStatusNote', () => {
  it('pendiente: explica que Meta aprueba en 1-3 días hábiles', () => {
    expect(whatsappStatusNote('pending')).toContain('Meta aprueba en 1-3 días hábiles');
  });

  it('conectado (cuenta seed): se ve como aprobado por Meta', () => {
    expect(whatsappStatusNote('connected')).toContain('aprobado por Meta');
  });

  it('error: sugiere reenviar la solicitud o desconectar', () => {
    expect(whatsappStatusNote('error')).toContain('Reenviá');
  });

  it('desconectado: sin nota', () => {
    expect(whatsappStatusNote('disconnected')).toBeNull();
  });
});

describe('connectionActionError — desconexión', () => {
  it('sin detalle usa el mensaje propio de la desconexión', () => {
    const msg = connectionActionError(new ApiError(500, '500 Internal Server Error'), 'disconnect');
    expect(msg).toBe('No pudimos desconectar el canal. Reintentá en unos segundos.');
  });
});

describe('disconnectCopy', () => {
  const cards = buildChannelCards([
    conn({ channel: 'telegram', status: 'connected', external_reference: '998877' }),
    conn({ channel: 'whatsapp', status: 'pending', external_reference: '+5492615551234' }),
    conn({ channel: 'email', status: 'error' }),
  ]);
  const [whatsapp, telegram, gmail] = cards;

  it('canal conectado: pide confirmar y nombra el canal y su referencia', () => {
    const copy = disconnectCopy(telegram);
    expect(copy.title).toBe('Desconectar Telegram');
    expect(copy.message).toContain('998877');
    expect(copy.confirmLabel).toBe('Desconectar');
    expect(copy.triggerLabel).toBe('Desconectar');
  });

  it('WhatsApp pendiente: es cancelar la solicitud, no desconectar', () => {
    const copy = disconnectCopy(whatsapp);
    expect(copy.title).toBe('Cancelar solicitud de WhatsApp');
    expect(copy.message).toContain('+5492615551234');
    expect(copy.confirmLabel).toBe('Cancelar solicitud');
    expect(copy.triggerLabel).toBe('Cancelar solicitud');
  });

  it('usa la etiqueta visual "Gmail" para el canal email y tolera la falta de referencia', () => {
    const copy = disconnectCopy(gmail);
    expect(copy.title).toBe('Desconectar Gmail');
    expect(copy.message).not.toContain('null');
    expect(copy.message).not.toContain('()');
  });
});

describe('connectionActionError — cancelar código de Telegram', () => {
  it('sin detalle usa un mensaje propio que aclara que el código sigue vigente', () => {
    const msg = connectionActionError(new ApiError(500, '500 Internal Server Error'), 'telegram-cancel');
    expect(msg).toBe(
      'No pudimos cancelar el código de vinculación: sigue vigente hasta que venza. Reintentá en unos segundos.',
    );
  });

  it('respeta el detalle que manda el server', () => {
    const msg = connectionActionError(new ApiError(400, 'x', 'Algo pasó'), 'telegram-cancel');
    expect(msg).toBe('Algo pasó');
  });

  it('un error de red (no ApiError) también termina en un texto claro', () => {
    const msg = connectionActionError(new TypeError('Failed to fetch'), 'telegram-cancel');
    expect(msg.length).toBeGreaterThan(10);
    expect(msg).not.toContain('Failed to fetch');
  });
});
