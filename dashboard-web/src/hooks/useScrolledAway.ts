import { useEffect, useState, type RefObject } from 'react';

import { isScrolledAway } from '@/lib/eventFeed';

/**
 * true mientras el inicio del elemento quedó bien arriba de la pantalla (se
 * está leyendo más abajo). Solo re-renderiza cuando el valor cambia.
 */
export function useScrolledAway(ref: RefObject<HTMLElement>): boolean {
  const [away, setAway] = useState(false);

  useEffect(() => {
    const check = () => {
      const el = ref.current;
      if (el) setAway(isScrolledAway(el.getBoundingClientRect().top));
    };
    window.addEventListener('scroll', check, { passive: true });
    window.addEventListener('resize', check);
    return () => {
      window.removeEventListener('scroll', check);
      window.removeEventListener('resize', check);
    };
  }, [ref]);

  return away;
}
