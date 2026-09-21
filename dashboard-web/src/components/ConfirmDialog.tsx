import { useEffect } from 'react';

import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel: string;
  /** Falla de la acción confirmada; se muestra dentro del diálogo. */
  error?: string | null;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Confirmación modal de una acción destructiva (mismo patrón que OrderDetailModal). */
export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  error,
  loading,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loading) onCancel();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [loading, onCancel]);

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !loading) onCancel();
      }}
    >
      <div className="modal modal--sm" role="alertdialog" aria-modal="true" aria-label={title}>
        <header className="modal__head">
          <h3>{title}</h3>
        </header>
        <div className="modal__body">
          <p className="modal__text">{message}</p>
          {error && (
            <Alert variant="error" role="alert">
              {error}
            </Alert>
          )}
          <div className="modal__actions">
            <Button variant="ghost" onClick={onCancel} disabled={loading} autoFocus>
              Volver
            </Button>
            <Button onClick={onConfirm} loading={loading}>
              {confirmLabel}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
