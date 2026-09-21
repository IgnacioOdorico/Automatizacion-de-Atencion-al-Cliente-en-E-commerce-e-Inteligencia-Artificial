import { useId } from 'react';

import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';

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

/** Confirmación modal de una acción destructiva (foco en "Volver": lo seguro es lo primero). */
export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  error,
  loading,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const titleId = useId();

  return (
    <Modal
      role="alertdialog"
      size="sm"
      labelledBy={titleId}
      onClose={onCancel}
      dismissible={!loading}
    >
      <header className="modal__head">
        <h3 id={titleId}>{title}</h3>
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
    </Modal>
  );
}
