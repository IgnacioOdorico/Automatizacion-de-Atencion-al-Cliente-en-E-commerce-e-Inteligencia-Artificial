import { act, type ReactElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DonutChart } from '@/components/metrics/DonutChart';

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

describe('DonutChart', () => {
  it('dibuja una porción por categoría con valor y el desglose accesible en <desc>', () => {
    render(
      <DonutChart
        title="Distribución de estados"
        entries={[
          { key: 'confirmed', label: 'Confirmado', value: 30, color: '#4ade80' },
          { key: 'no_stock', label: 'Sin stock', value: 3, color: '#fbbf24' },
          { key: 'pending', label: 'Pendiente', value: 0, color: '#94a3b8' },
        ]}
      />,
    );
    const svg = container.querySelector('svg[role="img"]');
    expect(svg).not.toBeNull();
    expect(svg?.querySelector('title')?.textContent).toBe('Distribución de estados');
    expect(svg?.querySelector('desc')?.textContent).toContain('Confirmado: 30 (91%)');
    expect(svg?.querySelectorAll('path')).toHaveLength(2); // pending (0) no dibuja porción

    // La categoría en 0 sigue en la leyenda visible (aunque no dibuje porción).
    const legendText = container.querySelector('.chart-donut__legend')?.textContent ?? '';
    expect(legendText).toContain('Pendiente');
    expect(legendText).toContain('Confirmado');
  });

  it('sin datos (todo en 0) muestra el anillo vacío, sin romper', () => {
    render(
      <DonutChart
        title="Distribución de intents"
        entries={[{ key: 'FAQ', label: 'Pregunta frecuente', value: 0, color: '#818cf8' }]}
      />,
    );
    const svg = container.querySelector('svg[role="img"]');
    expect(svg?.querySelectorAll('path')).toHaveLength(0);
    expect(svg?.querySelector('.chart-donut__empty-ring')).not.toBeNull();
    expect(svg?.querySelector('desc')?.textContent).toBe('Sin datos en este período.');
  });
});
