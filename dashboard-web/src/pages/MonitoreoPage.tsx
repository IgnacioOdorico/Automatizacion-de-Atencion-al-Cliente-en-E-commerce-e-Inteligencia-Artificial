import { useRef, type KeyboardEvent } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';

import {
  MONITORING_TABS,
  nextTabIndex,
  tabForPathname,
  tabHref,
} from '@/lib/monitoringTabs';

/**
 * Sección Monitoreo: título, pestañas por sub-ruta y el panel con la pestaña
 * activa. Tablist accesible (WAI-ARIA): flechas, Inicio y Fin cambian de
 * pestaña; solo la activa entra en el orden de tabulación.
 */
export function MonitoreoPage() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const active = tabForPathname(pathname);
  const tabRefs = useRef<Array<HTMLAnchorElement | null>>([]);

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const current = MONITORING_TABS.findIndex((tab) => tab.path === active.path);
    const next = nextTabIndex(current, event.key, MONITORING_TABS.length);
    if (next === null) return;
    event.preventDefault();
    navigate(tabHref(MONITORING_TABS[next]));
    tabRefs.current[next]?.focus();
  };

  return (
    <div className="page">
      <header className="page__head">
        <h1>Monitoreo</h1>
        <p className="page__sub">
          Todo lo que hace el bot, tal cual sucede: cada evento, cada conversación y su tiempo de
          respuesta.
        </p>
      </header>

      <div
        className="mon-tabs"
        role="tablist"
        aria-label="Secciones del monitoreo"
        onKeyDown={onKeyDown}
      >
        {MONITORING_TABS.map((tab, index) => {
          const selected = tab.path === active.path;
          return (
            <Link
              key={tab.path}
              ref={(el) => {
                tabRefs.current[index] = el;
              }}
              to={tabHref(tab)}
              role="tab"
              id={`mon-tab-${tab.path}`}
              aria-selected={selected}
              aria-controls="mon-panel"
              tabIndex={selected ? 0 : -1}
              className="mon-tab"
            >
              {tab.label}
            </Link>
          );
        })}
      </div>

      <div
        className="mon-panel"
        role="tabpanel"
        id="mon-panel"
        aria-labelledby={`mon-tab-${active.path}`}
      >
        <Outlet />
      </div>
    </div>
  );
}
