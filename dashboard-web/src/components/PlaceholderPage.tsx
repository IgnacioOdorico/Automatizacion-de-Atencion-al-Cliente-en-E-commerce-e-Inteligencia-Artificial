import { AlertIcon } from '@/components/icons';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import type { NavItem } from '@/lib/nav';

/** Página genérica de las secciones que llegan en Fases 5-6. */
export function PlaceholderPage({ item }: { item: NavItem }) {
  return (
    <div className="page">
      <header className="page__head">
        <h1>{item.label}</h1>
        <p className="page__sub">{item.description}</p>
      </header>
      <EmptyState
        icon={<AlertIcon width={24} height={24} />}
        title={`${item.label} — próximamente`}
        text="Esta sección se integra en la próxima entrega del portal. La navegación, la sesión y la protección de rutas ya están operativas."
        action={<Badge tone="brand">En desarrollo</Badge>}
      />
    </div>
  );
}