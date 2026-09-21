import type { ReactNode } from 'react';

import { ErrorState } from '@/components/ui/ErrorState';
import { resolveViewState } from '@/lib/viewState';

/** Lo mínimo que se lee de `useQuery`: sirve con cualquier query de TanStack. */
interface QueryLike<T> {
  data: T | undefined;
  isError: boolean;
  error: unknown;
  isFetching: boolean;
  refetch: () => unknown;
}

interface QueryViewProps<T> {
  query: QueryLike<T>;
  /** Esqueleto que reserva el espacio del contenido final. */
  loading: ReactNode;
  /** Estado vacío diseñado (con datos pero sin ítems). Sin esto nunca hay estado vacío. */
  empty?: ReactNode;
  isEmpty?: (data: T) => boolean;
  /** El error inicial (sin datos previos) usa la versión con menos aire, para franjas y tarjetas chicas. */
  smallError?: boolean;
  children: (data: T) => ReactNode;
}

/**
 * Contrato único de las pantallas con datos: cargando (esqueleto), error
 * (mensaje + Reintentar), vacío (EmptyState) o listo. Si un refetch falla con
 * datos ya cargados se siguen mostrando y aparece una franja de aviso.
 */
export function QueryView<T>({
  query,
  loading,
  empty,
  isEmpty,
  smallError,
  children,
}: QueryViewProps<T>) {
  const { data } = query;
  const hasData = data !== undefined;
  const { view, refreshFailed } = resolveViewState({
    hasData,
    isError: query.isError,
    isEmpty: hasData && isEmpty !== undefined ? isEmpty(data) : false,
  });

  const retry = () => void query.refetch();

  if (view === 'loading') {
    return (
      <div role="status" aria-busy="true" aria-live="polite">
        <span className="sr-only">Cargando…</span>
        {loading}
      </div>
    );
  }

  if (view === 'error') {
    return (
      <ErrorState small={smallError} error={query.error} onRetry={retry} retrying={query.isFetching} />
    );
  }

  return (
    <>
      {refreshFailed && (
        <ErrorState compact error={query.error} onRetry={retry} retrying={query.isFetching} />
      )}
      {view === 'empty' ? empty : children(data as T)}
    </>
  );
}
