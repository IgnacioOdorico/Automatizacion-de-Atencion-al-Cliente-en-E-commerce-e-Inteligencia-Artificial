import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useAuth } from '@/auth/AuthContext';
import { Spinner } from '@/components/ui/Spinner';

function FullScreenLoader() {
  return (
    <div className="fullscreen">
      <div className="fullscreen__copy">
        <Spinner size={22} />
        Cargando…
      </div>
    </div>
  );
}

/**
 * Guard de rutas internas (spec auth):
 *  - mientras restaura la sesión, un loader (evita el flash del redirect)
 *  - sin sesión -> redirect a /login recordando el origen
 */
export function ProtectedRoute() {
  const { status, hasSession } = useAuth();
  const location = useLocation();

  if (status === 'loading') return <FullScreenLoader />;
  if (!hasSession) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}