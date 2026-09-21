import { Navigate, Route, Routes, useLocation } from 'react-router-dom';

import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Shell } from '@/components/Shell';
import { CatalogoPage } from '@/pages/CatalogoPage';
import { ConexionesPage } from '@/pages/ConexionesPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { LoginPage } from '@/pages/LoginPage';
import { PedidosPage } from '@/pages/PedidosPage';
import { PerfilPage } from '@/pages/PerfilPage';
import { RegistroPage } from '@/pages/RegistroPage';
import { TicketsPage } from '@/pages/TicketsPage';
import { connectionsAliasPath } from '@/lib/connections';

/**
 * El callback de Gmail del backend redirige a /connections?gmail=connected,
 * pero la ruta del front es /conexiones: el alias conserva el query string.
 */
function ConnectionsAlias() {
  const { search } = useLocation();
  return <Navigate to={connectionsAliasPath(search)} replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/connections" element={<ConnectionsAlias />} />
      <Route path="/registro" element={<RegistroPage />} />

      {/* Rutas internas protegidas (spec auth): sin sesión -> /login */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Shell />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/pedidos" element={<PedidosPage />} />
          <Route path="/tickets" element={<TicketsPage />} />
          <Route path="/catalogo" element={<CatalogoPage />} />
          <Route path="/conexiones" element={<ConexionesPage />} />
          <Route path="/perfil" element={<PerfilPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}