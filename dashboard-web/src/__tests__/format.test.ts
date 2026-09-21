import { describe, expect, it } from 'vitest';

import {
  dataSourceLabel,
  formatContact,
  formatCurrency,
  formatDate,
  formatDateTime,
  formatDateTimeSeconds,
  formatDuration,
  formatEventClock,
  formatMetricDuration,
  formatMs,
  formatRelative,
  formatTime,
  formatTmr,
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

describe('formatMetricDuration', () => {
  it('sin muestras no hay promedio: un guion en vez de un "0s" engañoso', () => {
    expect(formatMetricDuration(0, 0)).toBe('—');
    expect(formatMetricDuration('0.00', 0)).toBe('—');
  });

  it('con muestras formatea la duración', () => {
    expect(formatMetricDuration('76.38', 22)).toBe('1m 16s');
    expect(formatMetricDuration(0, 3)).toBe('0s');
  });

  it('un valor ausente sigue siendo guion', () => {
    expect(formatMetricDuration(null, 5)).toBe('—');
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


describe('formatRelative (hora relativa del feed en vivo)', () => {
  const now = Date.parse('2026-09-21T14:00:00.000Z');
  const ago = (ms: number) => new Date(now - ms).toISOString();

  it('lo de hace un instante es "ahora"', () => {
    expect(formatRelative(ago(0), now)).toBe('ahora');
    expect(formatRelative(ago(4_000), now)).toBe('ahora');
  });

  it('segundos, minutos, horas y días', () => {
    expect(formatRelative(ago(5_000), now)).toBe('hace 5 s');
    expect(formatRelative(ago(59_000), now)).toBe('hace 59 s');
    expect(formatRelative(ago(60_000), now)).toBe('hace 1 min');
    expect(formatRelative(ago(25 * 60_000), now)).toBe('hace 25 min');
    expect(formatRelative(ago(3 * 3_600_000), now)).toBe('hace 3 h');
    expect(formatRelative(ago(2 * 86_400_000), now)).toBe('hace 2 d');
  });

  it('una marca en el futuro (reloj desfasado) no muestra números negativos', () => {
    expect(formatRelative(ago(-30_000), now)).toBe('ahora');
  });

  it('sin dato o fecha inválida', () => {
    expect(formatRelative(null, now)).toBe('—');
    expect(formatRelative('no-es-fecha', now)).toBe('—');
  });
});

describe('formatDateTimeSeconds / formatTime (hora de Mendoza)', () => {
  it('agrega los segundos a la fecha del negocio (UTC-3)', () => {
    expect(formatDateTimeSeconds('2026-09-21T14:03:22.418Z')).toBe('21/09/2026 11:03:22');
  });

  it('formatTime da solo hh:mm', () => {
    expect(formatTime('2026-09-21T14:03:22.418Z')).toBe('11:03');
    expect(formatTime('2026-09-21T02:59:59.000Z')).toBe('23:59');
  });

  it('sin dato', () => {
    expect(formatDateTimeSeconds(null)).toBe('—');
    expect(formatTime('basura')).toBe('—');
  });
});

describe('formatTmr (tiempos cortos del bot y del pipeline)', () => {
  it('menos de un segundo, en milisegundos', () => {
    expect(formatTmr(0.435)).toBe('435 ms');
    expect(formatTmr(0)).toBe('0 ms');
  });

  it('hasta un minuto, con un decimal y coma', () => {
    expect(formatTmr(3.918)).toBe('3,9 s');
    expect(formatTmr(12)).toBe('12,0 s');
  });

  it('desde un minuto reutiliza formatDuration', () => {
    expect(formatTmr(90)).toBe('1m 30s');
  });

  it('sin dato', () => {
    expect(formatTmr(null)).toBe('—');
    expect(formatTmr(undefined)).toBe('—');
    expect(formatTmr(Number.NaN)).toBe('—');
  });
});

describe('formatEventClock (hora absoluta en la tarjeta del feed)', () => {
  const now = Date.parse('2026-09-21T14:10:00.000Z'); // 21/09 11:10 en Mendoza

  it('el mismo día: solo hh:mm:ss', () => {
    expect(formatEventClock('2026-09-21T14:03:22.418Z', now)).toBe('11:03:22');
  });

  it('otro día: con día y mes, para no confundir "ayer a las 11" con "hoy a las 11"', () => {
    expect(formatEventClock('2026-09-20T14:03:22.418Z', now)).toBe('20/09 11:03:22');
  });

  it('el día se corta en la medianoche de Mendoza, no en la de UTC', () => {
    // 22/09 01:30Z = 21/09 22:30 en Mendoza: sigue siendo hoy.
    expect(formatEventClock('2026-09-22T01:30:00.000Z', now)).toBe('22:30:00');
  });

  it('sin dato', () => {
    expect(formatEventClock(null, now)).toBe('—');
  });
});


describe('formatMs (duración de un nodo o de una ejecución de n8n)', () => {
  it('menos de un milisegundo no es cero', () => {
    expect(formatMs(0)).toBe('<1 ms');
    expect(formatMs(0.4)).toBe('<1 ms');
  });

  it('milisegundos enteros por debajo del segundo', () => {
    expect(formatMs(1)).toBe('1 ms');
    expect(formatMs(435)).toBe('435 ms');
    expect(formatMs(999.4)).toBe('999 ms');
  });

  it('desde el segundo, con un decimal (formato del portal)', () => {
    expect(formatMs(1000)).toBe('1,0 s');
    expect(formatMs(1400)).toBe('1,4 s');
    expect(formatMs(65_000)).toBe('1m 5s');
  });

  it('sin dato es un guion', () => {
    expect(formatMs(null)).toBe('—');
    expect(formatMs(undefined)).toBe('—');
    expect(formatMs(Number.NaN)).toBe('—');
  });
});
