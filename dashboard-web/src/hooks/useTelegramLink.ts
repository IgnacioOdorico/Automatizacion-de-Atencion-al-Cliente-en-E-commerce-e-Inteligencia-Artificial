import { useCallback, useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { connectionsApi } from '@/api/endpoints';
import { connectionActionError } from '@/lib/connections';
import { codeDeadline, secondsRemaining, shouldPollTelegram } from '@/lib/telegramLink';

interface LinkSession {
  code: string;
  deadline: number;
}

/**
 * Sesión de vínculo de Telegram: pide el código, lleva la cuenta regresiva y
 * dice cuándo hay que consultar el estado. El código vive solo en memoria del
 * componente (nunca en localStorage): recargar la página lo descarta.
 */
export function useTelegramLink() {
  const [session, setSession] = useState<LinkSession | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [linked, setLinked] = useState(false);

  const start = useMutation({
    mutationFn: connectionsApi.telegramStart,
    onSuccess: (res) => {
      const receivedAt = Date.now();
      setNow(receivedAt);
      setSession({ code: res.code, deadline: codeDeadline(res, receivedAt) });
      setLinked(false);
    },
  });

  const secondsLeft = session ? secondsRemaining(session.deadline, now) : 0;
  const expired = session !== null && secondsLeft === 0;

  useEffect(() => {
    if (!session || expired) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [session, expired]);

  /** El workflow confirmó el vínculo: se descarta el código y se avisa. */
  const complete = useCallback(() => {
    setSession(null);
    setLinked(true);
  }, []);

  /** Descarta el código de la pantalla (el del server vence solo a los 15 min). */
  const dismiss = useCallback(() => {
    setSession(null);
    start.reset();
  }, [start]);

  return {
    code: session?.code ?? null,
    hasCode: session !== null,
    secondsLeft,
    expired,
    linked,
    /** Consultar GET /connections mientras se espera la confirmación. */
    polling: shouldPollTelegram({ hasCode: session !== null, expired }),
    starting: start.isPending,
    error: start.isError ? connectionActionError(start.error, 'telegram-start') : null,
    start: () => start.mutate(),
    complete,
    dismiss,
  };
}

export type TelegramLink = ReturnType<typeof useTelegramLink>;
