import { act, type ReactElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { StackedAreaChart } from '@/components/metrics/StackedAreaChart';

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

const SERIES = [
  { key: 'confirmed', label: 'Confirmado', color: '#4ade80' },
  { key: 'no_stock', label: 'Sin stock', color: '#fbbf24' },
];

describe('StackedAreaChart', () => {
  it('dibuja una capa por serie y los totales del período en la leyenda', () => {
    render(
      <StackedAreaChart
        title="Órdenes por día"
        rows={[
          { date: '2026-09-14', values: { confirmed: 4, no_stock: 1 } },
          { date: '2026-09-15', values: { confirmed: 2, no_stock: 0 } },
        ]}
        series={SERIES}
      />,
    );
    const svg = container.querySelector('svg[role="img"]');
    expect(svg?.querySelectorAll('.chart-area__layer')).toHaveLength(2);
    expect(container.textContent).toContain('Confirmado');
    // Total de confirmed en el período: 4 + 2 = 6.
    const legend = container.querySelector('.chart-area__legend')?.textContent ?? '';
    expect(legend).toContain('6');
  });

  it('una sola muestra se dibuja igual (sin romper) y aparece en el eje', () => {
    render(<StackedAreaChart title="Órdenes por día" rows={[{ date: '2026-09-14', values: { confirmed: 3, no_stock: 0 } }]} series={SERIES} />);
    const svg = container.querySelector('svg[role="img"]');
    expect(svg?.querySelectorAll('.chart-area__layer')).toHaveLength(2);
    expect(svg?.querySelector('.chart-area__tick')?.textContent).toBe('14/09');
  });

  it('sin filas: no rompe (el bloque vacío lo maneja la página, no este gráfico)', () => {
    render(<StackedAreaChart title="Órdenes por día" rows={[]} series={SERIES} />);
    const svg = container.querySelector('svg[role="img"]');
    expect(svg?.querySelectorAll('.chart-area__layer')).toHaveLength(0);
    expect(svg?.querySelector('desc')?.textContent).toBe('Sin datos en este período.');
  });
});
