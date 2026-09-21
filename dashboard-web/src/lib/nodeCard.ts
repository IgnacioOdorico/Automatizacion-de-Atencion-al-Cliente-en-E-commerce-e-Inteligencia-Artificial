import { traceStatusMeta } from '@/lib/executions';
import { formatMs } from '@/lib/format';
import type { NodeOverlay } from '@/lib/workflowTrace';

/**
 * Los textos chicos de la tarjeta de un nodo (duración, items, estado) y su
 * nombre accesible. Lógica pura: el componente solo los dibuja.
 */

function itemsText(count: number): string {
  return count === 1 ? '1 ítem' : `${count} ítems`;
}

function durationOf(overlay: NodeOverlay): string {
  return formatMs(overlay.trace?.duration_ms);
}

/** Hasta dos líneas: lo que la tarjeta muestra a la derecha del ícono. */
export function nodeMetaLines(overlay: NodeOverlay): string[] {
  const { visual, trace } = overlay;
  switch (visual) {
    case 'plain':
    case 'pending':
      return [];
    case 'success': {
      const items = itemsText(trace?.items_out ?? 0);
      const runs = trace && trace.runs > 1 ? ` · ${trace.runs} corridas` : '';
      return [durationOf(overlay), `${items}${runs}`];
    }
    case 'error':
      return ['Con error', durationOf(overlay)];
    case 'missing':
      return ['Sin datos'];
    default:
      return [traceStatusMeta(visual).label];
  }
}

/** Nombre accesible de la tarjeta: nombre, tipo, estado con sus datos y la acción. */
export function nodeAriaLabel(
  name: string,
  kindLabel: string,
  disabled: boolean,
  overlay: NodeOverlay,
): string {
  const { visual } = overlay;
  const parts = [name, kindLabel];
  if (visual !== 'plain' && visual !== 'pending') parts.push(traceStatusMeta(visual).label);
  if (visual === 'success') parts.push(...nodeMetaLines(overlay));
  if (visual === 'error') parts.push(durationOf(overlay));
  if (disabled) parts.push('Nodo deshabilitado');
  parts.push('Abrir detalle');
  return `${parts.join('. ')}.`;
}
