import { describe, expect, it } from 'vitest';

import {
  TELEGRAM_CODE_FALLBACK_TTL_SECONDS,
  TELEGRAM_POLL_MS,
  codeDeadline,
  formatCountdown,
  secondsRemaining,
  shouldPollTelegram,
} from '@/lib/telegramLink';

const T0 = Date.UTC(2026, 4, 10, 15, 0, 0);

describe('codeDeadline', () => {
  it('usa expires_in relativo a cuándo llegó la respuesta (inmune al desfase de relojes)', () => {
    const deadline = codeDeadline(
      { expires_at: '2026-05-10T18:15:00Z', expires_in: 900 },
      T0,
    );
    expect(deadline).toBe(T0 + 900_000);
  });

  it('sin expires_in válido cae a expires_at', () => {
    const deadline = codeDeadline(
      { expires_at: '2026-05-10T15:15:00Z', expires_in: Number.NaN },
      T0,
    );
    expect(deadline).toBe(Date.UTC(2026, 4, 10, 15, 15, 0));
  });

  it('sin ninguno de los dos usa los 15 minutos de la spec', () => {
    const deadline = codeDeadline({ expires_at: 'basura', expires_in: 0 }, T0);
    expect(deadline).toBe(T0 + TELEGRAM_CODE_FALLBACK_TTL_SECONDS * 1000);
    expect(TELEGRAM_CODE_FALLBACK_TTL_SECONDS).toBe(900);
  });
});

describe('secondsRemaining', () => {
  it('redondea hacia arriba y nunca baja de 0', () => {
    const deadline = T0 + 90_000;
    expect(secondsRemaining(deadline, T0)).toBe(90);
    expect(secondsRemaining(deadline, T0 + 500)).toBe(90);
    expect(secondsRemaining(deadline, T0 + 89_001)).toBe(1);
    expect(secondsRemaining(deadline, T0 + 90_000)).toBe(0);
    expect(secondsRemaining(deadline, T0 + 120_000)).toBe(0);
  });
});

describe('formatCountdown', () => {
  it('formatea mm:ss con ceros a la izquierda', () => {
    expect(formatCountdown(900)).toBe('15:00');
    expect(formatCountdown(65)).toBe('01:05');
    expect(formatCountdown(9)).toBe('00:09');
    expect(formatCountdown(0)).toBe('00:00');
  });

  it('tolera valores negativos o no finitos', () => {
    expect(formatCountdown(-5)).toBe('00:00');
    expect(formatCountdown(Number.NaN)).toBe('00:00');
  });
});

describe('shouldPollTelegram', () => {
  it('consulta solo mientras hay un código vigente esperando el vínculo', () => {
    expect(shouldPollTelegram({ hasCode: true, expired: false })).toBe(true);
  });

  it('no consulta sin código', () => {
    expect(shouldPollTelegram({ hasCode: false, expired: false })).toBe(false);
  });

  it('deja de consultar cuando el código venció', () => {
    expect(shouldPollTelegram({ hasCode: true, expired: true })).toBe(false);
  });

  it('el intervalo queda dentro de la ventana de polling de la spec (3-5s)', () => {
    expect(TELEGRAM_POLL_MS).toBeGreaterThanOrEqual(3000);
    expect(TELEGRAM_POLL_MS).toBeLessThanOrEqual(5000);
  });
});
