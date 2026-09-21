import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { monitoringApi } from '@/api/endpoints';
import {
  applyInitial,
  applyNewer,
  applyOlder,
  feedItems,
  initialFeed,
  newestFeedTs,
  olderCursor,
  pendingCount,
  resumeFeed,
  sinceCursor,
  type FeedState,
} from '@/lib/eventFeed';
import { detectNewIds } from '@/lib/liveRows';
import type { Channel } from '@/types/api';
import type { EventsPage, EventsParams, MonitoringEvent } from '@/types/monitoring';

/** Cada cuánto se pregunta por eventos nuevos. */
export const FEED_POLL_MS = 3000;
/** Cuánto dura el resaltado de un evento recién llegado. */
const FRESH_MS = 3200;
const INITIAL_LIMIT = 50;
const POLL_LIMIT = 100;
const OLDER_LIMIT = 50;
/** Páginas seguidas que se piden para ponerse al día si el server avisa que hay más. */
const MAX_CATCHUP = 5;

interface Options {
  types: readonly string[];
  channel?: Channel;
  /** Mientras es true, lo nuevo se acumula aparte y la lista visible no se mueve. */
  paused: boolean;
}

/** Parámetros sin claves vacías (una clave con `undefined` igual "existe"). */
function params(values: EventsParams): EventsParams {
  const out: EventsParams = {};
  if (values.limit !== undefined) out.limit = values.limit;
  if (values.since) out.since = values.since;
  if (values.before) out.before = values.before;
  if (values.types && values.types.length > 0) out.types = values.types;
  if (values.channel) out.channel = values.channel;
  return out;
}

/**
 * Feed en vivo: primera página, polling incremental con `since` cada 3 s,
 * pausa con eventos pendientes, historia hacia atrás con `before` y resaltado
 * de lo recién llegado. El polling se detiene mientras la pestaña del navegador
 * está oculta y se pone al día apenas vuelve. Las respuestas se procesan con
 * las funciones puras de lib/eventFeed.
 */
export function useEventFeed({ types, channel, paused }: Options) {
  const [state, setState] = useState<FeedState>(initialFeed);
  const [error, setError] = useState<unknown>(null);
  const [fetching, setFetching] = useState(false);
  const [fresh, setFresh] = useState<ReadonlySet<string>>(() => new Set());
  const [loadingMore, setLoadingMore] = useState(false);
  const [moreError, setMoreError] = useState<unknown>(null);

  const stateRef = useRef(state);
  const pausedRef = useRef(paused);
  const filtersRef = useRef({ types, channel });
  const generation = useRef(0);
  const refetchRef = useRef<() => void>(() => {});
  const freshTimers = useRef<number[]>([]);
  const wasPaused = useRef(paused);

  filtersRef.current = { types, channel };
  const filterKey = `${[...types].sort().join(',')}|${channel ?? ''}`;

  const commit = useCallback((next: FeedState) => {
    stateRef.current = next;
    setState(next);
  }, []);

  /** Resalta unos segundos lo que se agregó arriba entre `before` y `after`. */
  const markFresh = useCallback((before: FeedState, after: FeedState) => {
    const seen = new Set(feedItems(before).map((e) => e.id));
    const added = detectNewIds(seen, feedItems(after).map((e) => e.id));
    if (added.length === 0) return;
    setFresh((prev) => new Set([...prev, ...added]));
    freshTimers.current.push(
      window.setTimeout(() => {
        setFresh((prev) => {
          const next = new Set(prev);
          for (const id of added) next.delete(id);
          return next;
        });
      }, FRESH_MS),
    );
  }, []);

  const flush = useCallback(() => {
    const before = stateRef.current;
    const after = resumeFeed(before);
    if (after === before) return;
    commit(after);
    markFresh(before, after);
  }, [commit, markFresh]);

  // Al salir de la pausa, lo acumulado entra arriba.
  useEffect(() => {
    pausedRef.current = paused;
    if (wasPaused.current && !paused) flush();
    wasPaused.current = paused;
  }, [paused, flush]);

  // Polling: se reinicia entero al cambiar los filtros.
  useEffect(() => {
    generation.current += 1;
    let cancelled = false;
    let running = false;
    let timer: number | undefined;

    commit(initialFeed());
    setError(null);
    setFetching(false);
    setFresh(new Set());
    setLoadingMore(false);
    setMoreError(null);

    const schedule = () => {
      timer = window.setTimeout(run, FEED_POLL_MS);
    };

    const receive = (page: EventsPage, wasLoaded: boolean) => {
      const before = stateRef.current;
      if (!wasLoaded) {
        commit(applyInitial(before, page));
        return;
      }
      const after = applyNewer(before, page, pausedRef.current);
      commit(after);
      markFresh(before, after);
    };

    async function run() {
      if (cancelled || running) return;
      // Con la pestaña oculta no se consulta (salvo la primera carga): se retoma al volver.
      if (document.visibilityState === 'hidden' && stateRef.current.loaded) {
        schedule();
        return;
      }
      running = true;
      setFetching(true);
      try {
        for (let round = 0; round < MAX_CATCHUP; round += 1) {
          const wasLoaded = stateRef.current.loaded;
          const cursor = sinceCursor(stateRef.current);
          const filters = filtersRef.current;
          const page = await monitoringApi.events(
            params({
              limit: wasLoaded ? POLL_LIMIT : INITIAL_LIMIT,
              since: cursor ?? undefined,
              types: filters.types,
              channel: filters.channel,
            }),
          );
          if (cancelled) return;
          receive(page, wasLoaded);
          if (!(cursor && page.has_more)) break;
        }
        setError(null);
      } catch (e) {
        if (!cancelled) setError(e);
      } finally {
        running = false;
        if (!cancelled) {
          setFetching(false);
          schedule();
        }
      }
    }

    const runNow = () => {
      window.clearTimeout(timer);
      void run();
    };
    refetchRef.current = runNow;

    const onVisibility = () => {
      if (document.visibilityState === 'visible') runNow();
    };
    document.addEventListener('visibilitychange', onVisibility);

    void run();

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [filterKey, commit, markFresh]);

  useEffect(() => {
    const timers = freshTimers.current;
    return () => timers.forEach((t) => window.clearTimeout(t));
  }, []);

  const loadMore = useCallback(async () => {
    const cursor = olderCursor(stateRef.current);
    if (!cursor) return;
    const gen = generation.current;
    setLoadingMore(true);
    setMoreError(null);
    try {
      const filters = filtersRef.current;
      const page = await monitoringApi.events(
        params({ limit: OLDER_LIMIT, before: cursor, types: filters.types, channel: filters.channel }),
      );
      if (gen !== generation.current) return;
      commit(applyOlder(stateRef.current, page));
    } catch (e) {
      if (gen === generation.current) setMoreError(e);
    } finally {
      if (gen === generation.current) setLoadingMore(false);
    }
  }, [commit]);

  const items: MonitoringEvent[] = useMemo(() => feedItems(state), [state]);
  const refetch = useCallback(() => refetchRef.current(), []);

  return {
    /** Forma que espera QueryView: sin datos hasta que llega la primera página. */
    query: {
      data: state.loaded ? items : undefined,
      isError: error !== null,
      error,
      isFetching: fetching,
      refetch,
    },
    items,
    pending: pendingCount(state),
    hasMore: state.hasMore && olderCursor(state) !== null,
    newestTs: newestFeedTs(state),
    fresh,
    loadMore,
    loadingMore,
    moreError,
    flush,
    /** Hubo un fallo de red al actualizar (la lista sigue mostrando lo último que se tuvo). */
    failing: error !== null,
  };
}
