import { act, type ReactElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { Modal } from '@/components/ui/Modal';

// React 18 exige avisar que el entorno soporta act().
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;

function render(element: ReactElement) {
  act(() => {
    root.render(element);
  });
}

function press(key: string, init: KeyboardEventInit = {}): KeyboardEvent {
  const event = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true, ...init });
  act(() => {
    document.dispatchEvent(event);
  });
  return event;
}

beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  document.body.style.overflow = '';
});

function Sample({
  onClose,
  dismissible = true,
}: {
  onClose: () => void;
  dismissible?: boolean;
}) {
  return (
    <Modal label="Detalle de prueba" onClose={onClose} dismissible={dismissible}>
      <button type="button">Primero</button>
      <button type="button">Medio</button>
      <button type="button">Último</button>
    </Modal>
  );
}

function buttons(): HTMLButtonElement[] {
  return Array.from(document.querySelectorAll<HTMLButtonElement>('.modal button'));
}

describe('Modal', () => {
  it('es un diálogo modal con nombre accesible', () => {
    render(<Sample onClose={() => {}} />);
    const dialog = document.querySelector('[role="dialog"]');
    expect(dialog).not.toBeNull();
    expect(dialog?.getAttribute('aria-modal')).toBe('true');
    expect(dialog?.getAttribute('aria-label')).toBe('Detalle de prueba');
  });

  it('Esc lo cierra', () => {
    const onClose = vi.fn();
    render(<Sample onClose={onClose} />);
    press('Escape');
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('Esc no lo cierra mientras hay una acción en curso (dismissible=false)', () => {
    const onClose = vi.fn();
    render(<Sample onClose={onClose} dismissible={false} />);
    press('Escape');
    expect(onClose).not.toHaveBeenCalled();
  });

  it('al abrirse manda el foco al primer elemento enfocable', () => {
    render(<Sample onClose={() => {}} />);
    expect(document.activeElement).toBe(buttons()[0]);
  });

  it('Tab en el último elemento vuelve al primero (el foco no se escapa)', () => {
    render(<Sample onClose={() => {}} />);
    const [first, , last] = buttons();
    last.focus();
    const event = press('Tab');
    expect(event.defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(first);
  });

  it('Shift+Tab en el primer elemento salta al último', () => {
    render(<Sample onClose={() => {}} />);
    const [first, , last] = buttons();
    first.focus();
    const event = press('Tab', { shiftKey: true });
    expect(event.defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(last);
  });

  it('Tab en el medio no se intercepta', () => {
    render(<Sample onClose={() => {}} />);
    buttons()[1].focus();
    const event = press('Tab');
    expect(event.defaultPrevented).toBe(false);
  });

  it('al cerrarse devuelve el foco a quien lo abrió', () => {
    const opener = document.createElement('button');
    document.body.appendChild(opener);
    opener.focus();

    render(<Sample onClose={() => {}} />);
    expect(document.activeElement).not.toBe(opener);

    act(() => root.render(<div />));
    expect(document.activeElement).toBe(opener);
    opener.remove();
  });

  it('bloquea el scroll de la página mientras está abierto y lo restaura', () => {
    document.body.style.overflow = 'auto';
    render(<Sample onClose={() => {}} />);
    expect(document.body.style.overflow).toBe('hidden');
    act(() => root.render(<div />));
    expect(document.body.style.overflow).toBe('auto');
  });

  it('un clic en el fondo lo cierra; uno adentro no', () => {
    const onClose = vi.fn();
    render(<Sample onClose={onClose} />);
    const backdrop = document.querySelector('.modal-backdrop') as HTMLElement;
    const inside = buttons()[0];

    act(() => {
      inside.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    });
    expect(onClose).not.toHaveBeenCalled();

    act(() => {
      backdrop.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
