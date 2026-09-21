/**
 * Pestañas de la sección Monitoreo. Cada una es una sub-ruta de /monitoreo (el
 * estado vive en la URL). Para sumar una pestaña alcanza con agregarla acá y
 * declarar su <Route> en App.tsx.
 */

export interface MonitoringTab {
  /** Segmento de la URL bajo /monitoreo. */
  path: string;
  label: string;
}

export const MONITORING_TABS: readonly MonitoringTab[] = [
  { path: 'en-vivo', label: 'En vivo' },
  { path: 'conversaciones', label: 'Conversaciones' },
];

export const DEFAULT_TAB_PATH = MONITORING_TABS[0].path;

export const MONITORING_BASE_PATH = '/monitoreo';

export function tabHref(tab: MonitoringTab): string {
  return `${MONITORING_BASE_PATH}/${tab.path}`;
}

/** La pestaña que corresponde a la URL; /monitoreo a secas o una sub-ruta desconocida cae en la primera. */
export function tabForPathname(pathname: string): MonitoringTab {
  const segments = pathname.split('/').filter(Boolean);
  const segment = segments[0] === MONITORING_BASE_PATH.slice(1) ? segments[1] : undefined;
  return MONITORING_TABS.find((tab) => tab.path === segment) ?? MONITORING_TABS[0];
}

/**
 * Teclado del tablist (patrón WAI-ARIA con activación automática): flechas
 * izquierda/derecha con vuelta, Inicio y Fin. `null` = la tecla no es de navegación.
 */
export function nextTabIndex(current: number, key: string, count: number): number | null {
  if (count <= 0) return null;
  switch (key) {
    case 'ArrowRight':
      return (current + 1) % count;
    case 'ArrowLeft':
      return (current - 1 + count) % count;
    case 'Home':
      return 0;
    case 'End':
      return count - 1;
    default:
      return null;
  }
}
