import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  text?: string;
  action?: ReactNode;
}

/** Estado vacío reutilizable para las páginas placeholder (Fases 5-6). */
export function EmptyState({ icon, title, text, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">{icon}</div>
      <div>
        <p className="empty-state__title">{title}</p>
        {text && <p className="empty-state__text">{text}</p>}
      </div>
      {action}
    </div>
  );
}