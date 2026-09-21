import { useEffect, useRef, type ReactNode } from 'react';

import { FOCUSABLE_SELECTOR, trapFocusTarget } from '@/lib/focus';

interface ModalProps {
  /** Nombre accesible del diálogo (si no hay un título visible al que apuntar). */
  label?: string;
  /** id del título visible, alternativa a `label`. */
  labelledBy?: string;
  role?: 'dialog' | 'alertdialog';
  size?: 'md' | 'sm';
  onClose: () => void;
  /** false mientras hay una acción en curso: Esc y clic afuera no cierran. */
  dismissible?: boolean;
  children: ReactNode;
}

/**
 * Diálogo modal accesible: Esc cierra, Tab queda atrapado adentro, el foco entra
 * al abrir y vuelve a quien lo abrió al cerrar, y la página de fondo no scrollea.
 * Lo usan el detalle de pedido y la confirmación de desconexión.
 */
export function Modal({
  label,
  labelledBy,
  role = 'dialog',
  size = 'md',
  onClose,
  dismissible = true,
  children,
}: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  // El listener se registra una sola vez: lee siempre lo último desde estas refs.
  const onCloseRef = useRef(onClose);
  const dismissibleRef = useRef(dismissible);
  useEffect(() => {
    onCloseRef.current = onClose;
    dismissibleRef.current = dismissible;
  });

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const focusables = () =>
      Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));

    // Un `autoFocus` del contenido ya movió el foco adentro: se respeta.
    if (!dialog.contains(document.activeElement)) {
      (focusables()[0] ?? dialog).focus();
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (dismissibleRef.current) {
          event.preventDefault();
          onCloseRef.current();
        }
        return;
      }
      if (event.key !== 'Tab') return;

      const items = focusables();
      const target = trapFocusTarget({
        count: items.length,
        activeIndex: items.indexOf(document.activeElement as HTMLElement),
        shift: event.shiftKey,
      });
      if (target === null) return;
      event.preventDefault();
      (target === -1 ? dialog : items[target]).focus();
    };

    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
      if (opener?.isConnected) opener.focus();
    };
  }, []);

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && dismissible) onClose();
      }}
    >
      <div
        ref={dialogRef}
        className={`modal${size === 'sm' ? ' modal--sm' : ''}`}
        role={role}
        aria-modal="true"
        aria-label={label}
        aria-labelledby={labelledBy}
        tabIndex={-1}
      >
        {children}
      </div>
    </div>
  );
}
