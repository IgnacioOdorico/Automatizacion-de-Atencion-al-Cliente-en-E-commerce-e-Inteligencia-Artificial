import { act, type ReactElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/api/client';
import { QueryView } from '@/components/QueryView';

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;

function render(element: ReactElement) {
  act(() => {
    root.render(element);
  });
}

beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

interface Q {
  data: string[] | undefined;
  isError: boolean;
  error: unknown;
  isFetching: boolean;
  refetch: () => unknown;
}

function query(overrides: Partial<Q> = {}): Q {
  return {
    data: undefined,
    isError: false,
    error: null,
    isFetching: false,
    refetch: () => undefined,
    ...overrides,
  };
}

function view(q: Q) {
  return (
    <QueryView
      query={q}
      loading={<div data-testid="skeleton" />}
      isEmpty={(items) => items.length === 0}
      empty={<p>Nada por acá todavía</p>}
    >
      {(items) => <ul>{items.map((i) => <li key={i}>{i}</li>)}</ul>}
    </QueryView>
  );
}

const retryButton = () =>
  Array.from(container.querySelectorAll('button')).find((b) => b.textContent === 'Reintentar');

describe('QueryView', () => {
  it('cargando: muestra el esqueleto y avisa a lectores de pantalla', () => {
    render(view(query()));
    expect(container.querySelector('[data-testid="skeleton"]')).not.toBeNull();
    expect(container.querySelector('[role="status"]')?.textContent).toContain('Cargando');
    expect(retryButton()).toBeUndefined();
  });

  it('con datos: los muestra', () => {
    render(view(query({ data: ['Notebook', 'Mouse'] })));
    expect(container.querySelectorAll('li')).toHaveLength(2);
    expect(container.querySelector('[role="alert"]')).toBeNull();
  });

  it('sin ítems: muestra el estado vacío diseñado, no una lista cruda', () => {
    render(view(query({ data: [] })));
    expect(container.textContent).toContain('Nada por acá todavía');
    expect(container.querySelector('ul')).toBeNull();
  });

  it('error de red: mensaje de conexión y "Reintentar" que vuelve a pedir los datos', () => {
    const refetch = vi.fn();
    render(view(query({ isError: true, error: new TypeError('Failed to fetch'), refetch })));

    const alert = container.querySelector('[role="alert"]');
    expect(alert?.textContent).toContain('Sin conexión con el servidor');
    expect(container.querySelector('[data-testid="skeleton"]')).toBeNull();

    act(() => retryButton()?.click());
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it('un 401 no se muestra como caída de red', () => {
    render(view(query({ isError: true, error: new ApiError(401, 'La sesión expiró.') })));
    const text = container.querySelector('[role="alert"]')?.textContent ?? '';
    expect(text).toContain('Tu sesión expiró');
    expect(text).not.toContain('Sin conexión');
  });

  it('un refetch fallido con datos previos: sigue mostrándolos y avisa en una franja', () => {
    const refetch = vi.fn();
    render(
      view(
        query({
          data: ['Notebook'],
          isError: true,
          error: new ApiError(502, '502 Bad Gateway'),
          refetch,
        }),
      ),
    );

    expect(container.querySelectorAll('li')).toHaveLength(1);
    const banner = container.querySelector('.error-banner');
    expect(banner?.textContent).toContain('Mostramos los últimos datos');
    expect(banner?.textContent).not.toContain('502');

    act(() => retryButton()?.click());
    expect(refetch).toHaveBeenCalledTimes(1);
  });
});
