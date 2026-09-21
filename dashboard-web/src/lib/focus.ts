/**
 * Lógica pura del manejo de foco en modales (sin DOM): a dónde mandar el foco
 * cuando se aprieta Tab para que no se escape del diálogo.
 */

/** Elementos que reciben foco con el teclado dentro de un diálogo. */
export const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  'summary',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

interface TrapInput {
  /** Cantidad de elementos enfocables dentro del diálogo. */
  count: number;
  /** Posición del elemento con foco entre ellos, o -1 si el foco está afuera. */
  activeIndex: number;
  shift: boolean;
}

/**
 * Devuelve el índice al que hay que mover el foco (cancelando el Tab), `-1` para
 * enfocar el contenedor del diálogo, o `null` si el navegador puede seguir solo.
 */
export function trapFocusTarget({ count, activeIndex, shift }: TrapInput): number | null {
  if (count === 0) return -1;
  if (activeIndex === -1) return shift ? count - 1 : 0;
  if (!shift && activeIndex === count - 1) return 0;
  if (shift && activeIndex === 0) return count - 1;
  return null;
}
