import { useEffect, useRef, useState } from 'react';

import { detectNewIds } from '@/lib/liveRows';

/** Cuánto dura el resaltado de una fila nueva (la animación CSS dura un poco menos). */
const FRESH_MS = 3200;

/**
 * Ids de filas que aparecieron entre dos polls consecutivos, durante unos
 * segundos: la fila recién llegada se resalta y se nota el efecto "en vivo".
 *
 * - `scope` identifica la vista (filtro + página): al cambiarla se vuelve a
 *   tomar la lista como "ya vista" en vez de marcar todo como nuevo.
 * - `ids` debe ser `undefined` mientras se muestran datos de relleno de otra vista.
 */
export function useFreshRows(scope: string, ids: readonly number[] | undefined): ReadonlySet<number> {
  const seen = useRef<Set<number> | null>(null);
  const seenScope = useRef(scope);
  const timers = useRef<number[]>([]);
  const [fresh, setFresh] = useState<ReadonlySet<number>>(() => new Set());

  const signature = ids ? ids.join(',') : null;

  useEffect(() => {
    if (!ids) return;

    if (seenScope.current !== scope) {
      seenScope.current = scope;
      seen.current = null;
      setFresh(new Set());
    }

    const added = detectNewIds(seen.current, ids);
    seen.current = new Set([...(seen.current ?? []), ...ids]);
    if (added.length === 0) return;

    setFresh((prev) => new Set([...prev, ...added]));
    timers.current.push(
      window.setTimeout(() => {
        setFresh((prev) => {
          const next = new Set(prev);
          for (const id of added) next.delete(id);
          return next;
        });
      }, FRESH_MS),
    );
    // `ids` se representa por su firma: un array nuevo con los mismos ids no re-dispara.
  }, [scope, signature]);

  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach((t) => window.clearTimeout(t));
  }, []);

  return fresh;
}
