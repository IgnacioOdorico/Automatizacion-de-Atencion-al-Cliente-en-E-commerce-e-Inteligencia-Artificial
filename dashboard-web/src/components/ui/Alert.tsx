import type { ReactNode } from 'react';

interface AlertProps {
  variant: 'error' | 'success';
  children: ReactNode;
  role?: 'alert';
}

export function Alert({ variant, children, role }: AlertProps) {
  return (
    <div className={`alert alert--${variant}`} role={role}>
      {children}
    </div>
  );
}