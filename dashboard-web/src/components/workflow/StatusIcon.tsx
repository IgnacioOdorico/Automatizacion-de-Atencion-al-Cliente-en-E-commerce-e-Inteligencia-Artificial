import { CheckCircleIcon, InfoIcon, XCircleIcon } from '@/components/icons';
import type { StatusIconKey } from '@/lib/executions';

interface StatusIconProps {
  name: StatusIconKey;
  size?: number;
}

/** Ícono de un estado (ejecución o nodo): el color nunca es lo único que lo distingue. Decorativo. */
export function StatusIcon({ name, size = 13 }: StatusIconProps) {
  const props = { width: size, height: size, 'aria-hidden': true as const };
  switch (name) {
    case 'check':
      return <CheckCircleIcon {...props} />;
    case 'error':
      return <XCircleIcon {...props} />;
    case 'clock':
      return (
        <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </svg>
      );
    case 'skip':
      return (
        <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M8 12h8" />
        </svg>
      );
    default:
      return <InfoIcon {...props} />;
  }
}
