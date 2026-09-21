import { describe, expect, it } from 'vitest';

import {
  dataSourceLabel,
  formatContact,
  formatCurrency,
  formatDate,
  formatDateTime,
  formatDuration,
} from '@/lib/format';

describe('formatDuration', () => {
  it('formatea segundos sueltos', () => {
    expect(formatDuration(0)).toBe('0s');
    expect(formatDuration(12)).toBe('12s');
    expect(formatDuration(59)).toBe('59s');
  });

  it('formatea minutos con resto de segundos', () => {
    expect(formatDuration(60)).toBe('1m');
    expect(formatDuration(90)).toBe('1m 30s');
    expect(formatDuration(3599)).toBe('59m 59s');
  });

  it('formatea horas con resto de minutos', () => {
    expect(formatDuration(3600)).toBe('1h');
    expect(formatDuration(3661)).toBe('1h 1m');
    expect(formatDuration(86399)).toBe('23h 59m');
  });

  it('formatea días con resto de horas', () => {
    expect(formatDuration(86400)).toBe('1d');
    expect(formatDuration(90000)).toBe('1d 1h');
  });

  it('redondea fracciones y maneja valores no numéricos', () => {
    expect(formatDuration(12.7)).toBe('13s');
    expect(formatDuration(null)).toBe('—');
    expect(formatDuration(undefined)).toBe('—');
  });

  it('acepta strings numéricos (la API serializa DECIMAL/numeric como string)', () => {
    expect(formatDuration('90')).toBe('1m 30s');
    expect(formatDuration('3660.9')).toBe('1h 1m');
    expect(formatDuration('no-num')).toBe('—');
  });
});

describe('formatCurrency', () => {
  it('formatea con $ y 2 decimales en es-AR', () => {
    expect(formatCurrency(349.99)).toBe('$349,99');
    expect(formatCurrency('24.99')).toBe('$24,99');
    expect(formatCurrency(0)).toBe('$0,00');
  });

  it('agrupa miles', () => {
    expect(formatCurrency(1599.5)).toBe('$1.599,50');
  });

  it('los negativos llevan el signo adelante del $', () => {
    expect(formatCurrency(-5)).toBe('-$5,00');
    expect(formatCurrency('-1599.5')).toBe('-$1.599,50');
  });

  it('siempre 2 decimales, también en montos grandes', () => {
    expect(formatCurrency(6929.01)).toBe('$6.929,01');
    expect(formatCurrency('89.9')).toBe('$89,90');
    expect(formatCurrency(1234567)).toBe('$1.234.567,00');
  });

  it('maneja valores ausentes o no numéricos', () => {
    expect(formatCurrency(null)).toBe('—');
    expect(formatCurrency(undefined)).toBe('—');
    expect(formatCurrency('abc')).toBe('—');
  });
});

describe('formatDateTime', () => {
  it('devuelve em dash para valores nulos (resolved_at puede ser NULL)', () => {
    expect(formatDateTime(null)).toBe('—');
    expect(formatDateTime(undefined)).toBe('—');
    expect(formatDateTime('no-es-fecha')).toBe('—');
  });

  it('formatea dd/mm/aaaa hh:mm en hora de Mendoza (UTC-3), sin depender de la máquina', () => {
    expect(formatDateTime('2026-09-20T17:32:00Z')).toBe('20/09/2026 14:32');
  });

  it('la medianoche es 00:xx (no 24:xx)', () => {
    expect(formatDateTime('2026-09-21T03:05:00Z')).toBe('21/09/2026 00:05');
  });

  it('pasadas las 21 hs de Mendoza sigue siendo el mismo día aunque en UTC ya cambió', () => {
    expect(formatDateTime('2026-09-21T01:30:00Z')).toBe('20/09/2026 22:30');
  });
});

describe('formatDate', () => {
  it('devuelve solo dd/mm/aaaa, con el día de Mendoza', () => {
    expect(formatDate('2026-09-20T17:32:00Z')).toBe('20/09/2026');
    expect(formatDate('2026-09-21T01:30:00Z')).toBe('20/09/2026');
  });

  it('valores ausentes', () => {
    expect(formatDate(null)).toBe('—');
    expect(formatDate('')).toBe('—');
  });
});

describe('formatContact', () => {
  it('WhatsApp: número internacional legible', () => {
    expect(formatContact('whatsapp', '5492614002002')).toBe('+54 9 2614002002');
    expect(formatContact('whatsapp', '5511999888777')).toBe('+5511999888777');
  });

  it('WhatsApp: no vuelve a anteponer + si ya viene en formato E.164', () => {
    expect(formatContact('whatsapp', '+5492614002002')).toBe('+54 9 2614002002');
  });

  it('Telegram: el identificador es un chat, no un teléfono', () => {
    expect(formatContact('telegram', '5492619888001')).toBe('Chat 5492619888001');
  });

  it('Gmail: la dirección tal cual', () => {
    expect(formatContact('email', 'cliente@mercadomza.com.ar')).toBe('cliente@mercadomza.com.ar');
  });

  it('sin dato o canal desconocido no rompe', () => {
    expect(formatContact('whatsapp', null)).toBe('—');
    expect(formatContact('email', '')).toBe('—');
    expect(formatContact('sms', 'abc')).toBe('abc');
  });
});

describe('dataSourceLabel', () => {
  it('traduce los valores del CHECK de la BD', () => {
    expect(dataSourceLabel('measured')).toBe('Medido');
    expect(dataSourceLabel('synthetic')).toBe('Sintético');
    expect(dataSourceLabel('e4_manual')).toBe('Carga manual');
  });

  it('un valor desconocido o ausente no muestra basura', () => {
    expect(dataSourceLabel(null)).toBe('—');
    expect(dataSourceLabel(undefined)).toBe('—');
    expect(dataSourceLabel('otro')).toBe('otro');
  });
});
