import { useQuery } from '@tanstack/react-query';
import { NavLink, Outlet, useLocation } from 'react-router-dom';

import { authApi } from '@/api/endpoints';
import { useAuth } from '@/auth/AuthContext';
import { Brand } from '@/components/Brand';
import { LogoutIcon } from '@/components/icons';
import { initials } from '@/lib/format';
import { NAV_ITEMS, navItemForPath } from '@/lib/nav';

/**
 * Shell con sidebar fija a la izquierda + contenido.
 * La identidad (GET /me) la resuelve TanStack Query; si el access expiró, el
 * cliente lo renueva solo y rehace la request (ver api/client.ts).
 */
export function Shell() {
  const { logout } = useAuth();
  const { pathname } = useLocation();

  const { data: me, isPending } = useQuery({
    queryKey: ['me'],
    queryFn: authApi.me,
    staleTime: 60_000,
  });

  const current = navItemForPath(pathname);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <Brand />
        </div>

        <nav className="sidebar__nav" aria-label="Navegación principal">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <item.icon aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__foot">
          <div className="user-card">
            <div className="user-card__avatar">
              {me?.business_name ? initials(me.business_name) : '?'}
            </div>
            <div className="user-card__meta">
              {isPending ? (
                <>
                  <span className="skeleton" style={{ height: 13, width: 110 }} />
                  <span className="skeleton" style={{ height: 12, width: 150, marginTop: 5 }} />
                </>
              ) : (
                <>
                  <span className="user-card__name">{me?.business_name}</span>
                  <span className="user-card__email">{me?.email}</span>
                </>
              )}
            </div>
          </div>
          <button type="button" className="btn-logout" onClick={logout}>
            <LogoutIcon aria-hidden="true" />
            Cerrar sesión
          </button>
        </div>
      </aside>

      <main className="shell__main">
        <header className="topbar">
          <div className="topbar__title">{current?.label ?? 'Portal'}</div>
        </header>
        <div className="shell__content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}