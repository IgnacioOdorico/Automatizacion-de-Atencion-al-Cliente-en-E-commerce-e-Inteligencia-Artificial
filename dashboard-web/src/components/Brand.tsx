export function Brand({ variant = 'full' }: { variant?: 'full' | 'mark' }) {
  return (
    <span className="brand">
      <span className="brand__mark" style={{ width: 32, height: 32 }}>
        <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M6 19V5h2.6l6.8 8V5H18v14h-2.6L8.6 11v8z" />
        </svg>
      </span>
      {variant === 'full' && (
        <span className="brand__name">
          TechStore
          <small>Portal de Atención al Cliente</small>
        </span>
      )}
    </span>
  );
}