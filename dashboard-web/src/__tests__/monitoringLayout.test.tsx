import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { MonitoreoPage } from '@/pages/MonitoreoPage';

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;

function Where() {
  return <span data-testid="where">{useLocation().pathname}</span>;
}

function mount(path: string) {
  act(() => {
    root.render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/monitoreo" element={<MonitoreoPage />}>
            <Route path="en-vivo" element={<p>Contenido en vivo</p>} />
            <Route path="conversaciones" element={<p>Contenido de conversaciones</p>} />
            <Route path="workflow" element={<p>Contenido del workflow</p>} />
          </Route>
        </Routes>
        <Where />
      </MemoryRouter>,
    );
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

const tabs = () => Array.from(container.querySelectorAll<HTMLElement>('[role="tab"]'));
const where = () => container.querySelector('[data-testid="where"]')?.textContent;

function press(target: HTMLElement, key: string) {
  act(() => {
    target.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
  });
}

describe('MonitoreoPage (título, pestañas y panel)', () => {
  it('tiene un título y un tablist con nombre accesible', () => {
    mount('/monitoreo/en-vivo');
    expect(container.querySelector('h1')?.textContent).toBe('Monitoreo');
    const list = container.querySelector('[role="tablist"]');
    expect(list?.getAttribute('aria-label')).toBeTruthy();
    expect(tabs().map((t) => t.textContent)).toEqual(['En vivo', 'Conversaciones', 'Workflow']);
  });

  it('marca la pestaña de la URL como seleccionada (y solo esa entra en el orden de tabulación)', () => {
    mount('/monitoreo/conversaciones');
    const [live, chats] = tabs();
    expect(live.getAttribute('aria-selected')).toBe('false');
    expect(live.getAttribute('tabindex')).toBe('-1');
    expect(chats.getAttribute('aria-selected')).toBe('true');
    expect(chats.getAttribute('tabindex')).toBe('0');
  });

  it('el panel muestra la sub-ruta y está rotulado por su pestaña', () => {
    mount('/monitoreo/conversaciones');
    const panel = container.querySelector('[role="tabpanel"]') as HTMLElement;
    expect(panel.textContent).toContain('Contenido de conversaciones');
    expect(panel.getAttribute('aria-labelledby')).toBe(tabs()[1].id);
    expect(tabs()[1].getAttribute('aria-controls')).toBe(panel.id);
  });

  it('la pestaña Workflow se abre desde el riel y muestra su contenido', () => {
    mount('/monitoreo/en-vivo');
    act(() => tabs()[2].click());
    expect(where()).toBe('/monitoreo/workflow');
    expect(container.querySelector('[role="tabpanel"]')?.textContent).toContain('Contenido del workflow');
    expect(tabs()[2].getAttribute('aria-selected')).toBe('true');
  });

  it('hacer clic en una pestaña cambia la URL', () => {
    mount('/monitoreo/en-vivo');
    act(() => tabs()[1].click());
    expect(where()).toBe('/monitoreo/conversaciones');
    expect(container.querySelector('[role="tabpanel"]')?.textContent).toContain('Contenido de conversaciones');
  });

  it('flecha derecha pasa a la pestaña siguiente y le da el foco', () => {
    mount('/monitoreo/en-vivo');
    tabs()[0].focus();
    press(tabs()[0], 'ArrowRight');
    expect(where()).toBe('/monitoreo/conversaciones');
    expect(document.activeElement).toBe(tabs()[1]);
  });

  it('flecha izquierda desde la primera da la vuelta a la última; Home y End saltan a los extremos', () => {
    mount('/monitoreo/en-vivo');
    press(tabs()[0], 'ArrowLeft');
    expect(where()).toBe('/monitoreo/workflow');
    press(tabs()[2], 'Home');
    expect(where()).toBe('/monitoreo/en-vivo');
    press(tabs()[0], 'End');
    expect(where()).toBe('/monitoreo/workflow');
  });

  it('una tecla cualquiera no navega', () => {
    mount('/monitoreo/en-vivo');
    press(tabs()[0], 'x');
    expect(where()).toBe('/monitoreo/en-vivo');
  });
});
