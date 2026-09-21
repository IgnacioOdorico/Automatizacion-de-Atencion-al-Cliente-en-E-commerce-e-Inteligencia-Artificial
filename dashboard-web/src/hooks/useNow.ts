import { useEffect, useState } from 'react';

/** Reloj que se actualiza solo (por defecto, cada segundo) para textos como "hace 12 s". */
export function useNow(intervalMs = 1000): number {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs]);

  return now;
}
