import { useCallback, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { monitoringApi } from '@/api/endpoints';
import {
  applyThreadLatest,
  applyThreadOlder,
  initialThread,
  type ConversationRef,
  type ThreadState,
} from '@/lib/conversations';

/** Cada cuánto se refresca el hilo abierto. */
export const THREAD_POLL_MS = 5000;
const PAGE_SIZE = 50;

/**
 * Mensajes de un hilo: la ventana reciente se refresca sola cada 5 s (TanStack
 * pausa el polling con la pestaña oculta) y se une a lo ya cargado, y los
 * mensajes anteriores se piden a pedido con `before`. El componente que lo usa
 * se monta con `key` = conversación, así cada hilo arranca de cero.
 */
export function useThread(conversation: ConversationRef) {
  const { channel, userId } = conversation;

  const latest = useQuery({
    queryKey: ['monitoring-thread', channel, userId],
    queryFn: () => monitoringApi.thread({ channel, userId, limit: PAGE_SIZE }),
    refetchInterval: THREAD_POLL_MS,
    // Un hilo inexistente (404) no se arregla reintentando; el polling ya vuelve a preguntar.
    retry: false,
  });

  const [state, setState] = useState<ThreadState>(initialThread);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [olderError, setOlderError] = useState<unknown>(null);

  const page = latest.data;
  useEffect(() => {
    if (page) setState((prev) => applyThreadLatest(prev, page));
  }, [page]);

  const loadOlder = useCallback(async () => {
    if (!state.olderCursor) return;
    setLoadingOlder(true);
    setOlderError(null);
    try {
      const older = await monitoringApi.thread({
        channel,
        userId,
        limit: PAGE_SIZE,
        before: state.olderCursor,
      });
      setState((prev) => applyThreadOlder(prev, older));
    } catch (e) {
      setOlderError(e);
    } finally {
      setLoadingOlder(false);
    }
  }, [channel, userId, state.olderCursor]);

  return {
    /** Forma que espera QueryView: sin datos hasta que llega la primera respuesta. */
    query: {
      data: state.loaded ? state : undefined,
      isError: latest.isError,
      error: latest.error,
      isFetching: latest.isFetching,
      refetch: latest.refetch,
    },
    loadOlder,
    loadingOlder,
    olderError,
  };
}
