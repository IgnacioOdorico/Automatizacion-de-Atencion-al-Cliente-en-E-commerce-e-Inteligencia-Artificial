import { AlertIcon } from '@/components/icons';
import { Button } from '@/components/ui/Button';
import { queryErrorCopy } from '@/lib/viewState';

interface ErrorStateProps {
  error: unknown;
  /** Vuelve a pedir los datos (refetch). */
  onRetry: () => void;
  retrying?: boolean;
  /** Franja angosta para cuando ya hay datos en pantalla y falló una actualización. */
  compact?: boolean;
  /** Versión con menos aire, para usarla dentro de un modal o una card. */
  small?: boolean;
}

/**
 * Estado de error común a todas las pantallas: explica qué pasó (red, sesión,
 * servidor) y ofrece "Reintentar". En modo compacto avisa que se están
 * mostrando los últimos datos disponibles.
 */
export function ErrorState({ error, onRetry, retrying, compact, small }: ErrorStateProps) {
  const copy = queryErrorCopy(error);

  if (compact) {
    return (
      <div className="error-banner" role="alert">
        <AlertIcon width={18} height={18} aria-hidden="true" />
        <p className="error-banner__text">
          <strong>{copy.title}.</strong> Mostramos los últimos datos que tenemos.
        </p>
        <Button variant="ghost" onClick={onRetry} loading={retrying}>
          Reintentar
        </Button>
      </div>
    );
  }

  return (
    <div className={`empty-state error-state${small ? ' error-state--sm' : ''}`} role="alert">
      <div className="empty-state__icon error-state__icon">
        <AlertIcon width={24} height={24} aria-hidden="true" />
      </div>
      <div>
        <p className="empty-state__title">{copy.title}</p>
        <p className="empty-state__text">{copy.message}</p>
      </div>
      <Button variant="ghost" onClick={onRetry} loading={retrying}>
        Reintentar
      </Button>
    </div>
  );
}
