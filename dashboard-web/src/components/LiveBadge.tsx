interface LiveBadgeProps {
  /** El polling está fallando: se muestra apagado en vez de "En vivo". */
  paused?: boolean;
}

/** Indicador del polling automático (Dashboard y Pedidos). */
export function LiveBadge({ paused }: LiveBadgeProps) {
  return (
    <span
      className={`live-badge${paused ? ' live-badge--paused' : ''}`}
      role="status"
      aria-live="polite"
    >
      <span className="live-badge__dot" aria-hidden="true" />
      {paused ? 'Sin actualizar' : 'En vivo'}
    </span>
  );
}
