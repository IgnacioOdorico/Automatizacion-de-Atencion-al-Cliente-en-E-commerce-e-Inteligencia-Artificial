import { useCallback, useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { connectionsApi } from '@/api/endpoints';
import { connectionActionError } from '@/lib/connections';
import {
  codeDeadline,
  secondsRemaining,
  shouldCancelTelegramCode,
  shouldPollTelegram,
} from '@/lib/telegramLink';

interface LinkSession {
  code: string;
  deadline: number;
}

/**
 * Sesión de vínculo de Telegram: pide el código, lo cancela en el server cuando
 * el usuario lo descarta, lleva la cuenta regresiva y dice cuándo hay que
 * consultar el estado. El código vive solo en memoria del componente (nunca en
 * localStorage): recargar la página lo descarta.
 */
export function useTelegramLink() {
  const [session, setSession] = useState<LinkSession | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [linked, setLinked] = useState(false);

  // Cancelar invalida el código en el server. Solo si el DELETE sale bien se
  // descarta el código local; si falla, la pantalla sigue mostrando el código
  // (que en el server sigue vigente) junto con el error, para reintentar.
  const cancelCode = useMutation({
    mutationFn: connectionsApi.telegramCancelCode,
    onSuccess: () => setSession(null),
  });

  const start = useMutation({
    mutationFn: connectionsApi.telegramStart,
    onSuccess: (res) => {
      const receivedAt = Date.now();
      setNow(receivedAt);
      setSession({ code: res.code, deadline: codeDeadline(res, receivedAt) });
      setLinked(false);
      cancelCode.reset();
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

  /**
   * Descarta el código de la pantalla sin tocar el server (la desconexión del
   * canal ya lo dejó sin efecto; uno vencido tampoco sirve allá).
   */
  const dismiss = useCallback(() => {
    setSession(null);
    start.reset();
    cancelCode.reset();
  }, [start, cancelCode]);

  /** Botón "Cancelar": invalida el código pendiente en el server y lo descarta. */
  const cancel = useCallback(() => {
    if (shouldCancelTelegramCode({ hasCode: session !== null, expired })) {
      cancelCode.mutate();
    } else {
      dismiss();
    }
  }, [session, expired, cancelCode, dismiss]);

  return {
    code: session?.code ?? null,
    hasCode: session !== null,
    secondsLeft,
    expired,
    linked,
    /** Consultar GET /connections mientras se espera la confirmación. */
    polling: shouldPollTelegram({ hasCode: session !== null, expired }),
    starting: start.isPending,
    cancelling: cancelCode.isPending,
    error: start.isError
      ? connectionActionError(start.error, 'telegram-start')
      : cancelCode.isError
        ? connectionActionError(cancelCode.error, 'telegram-cancel')
        : null,
    start: () => start.mutate(),
    complete,
    dismiss,
    cancel,
  };
}

export type TelegramLink = ReturnType<typeof useTelegramLink>;
