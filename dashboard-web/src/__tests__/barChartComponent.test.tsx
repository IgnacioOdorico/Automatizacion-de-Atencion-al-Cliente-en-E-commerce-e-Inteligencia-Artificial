import { act, type ReactElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { BarChart } from '@/components/metrics/BarChart';

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

describe('BarChart', () => {
  it('dibuja una barra real por intent con dato, con su label y conteo', () => {
    render(
      <BarChart
        title="TMR promedio por intent"
        entries={[
          { key: 'FAQ', label: 'Pregunta frecuente', value: 3.2, color: '#818cf8', count: 15 },
          { key: 'GENERAL', label: 'Consulta general', value: 2.9, color: '#94a3b8', count: 4 },
        ]}
      />,
    );
    const svg = container.querySelector('svg[role="img"]');
    expect(svg?.querySelectorAll('.chart-bar__rect:not(.chart-bar__rect--empty)')).toHaveLength(2);
    expect(container.textContent).toContain('(15)');
    expect(container.textContent).toContain('Pregunta frecuente');
  });

  it('un intent sin respuestas (value null) se dibuja como hueco, no como barra en 0', () => {
    render(
      <BarChart
        title="TMR promedio por intent"
        entries={[{ key: 'RECLAMO', label: 'Reclamo', value: null, color: '#f0878b', count: 0 }]}
      />,
    );
    const svg = container.querySelector('svg[role="img"]');
    expect(svg?.querySelectorAll('.chart-bar__rect--empty')).toHaveLength(1);
    expect(container.textContent).toContain('Sin respuestas');
    expect(svg?.querySelector('desc')?.textContent).toContain('sin respuestas todavía');
  });
});
