import { useLayoutEffect, useState, type RefObject } from 'react';

import type { Size } from '@/lib/viewport';

/**
 * Tamaño en píxeles de un elemento, que se actualiza solo cuando cambia (el
 * lienzo del diagrama se ajusta a su caja). Sin ResizeObserver (navegadores muy
 * viejos, jsdom) queda con la medida inicial y la de los cambios de ventana.
 */
export function useElementSize(ref: RefObject<HTMLElement>): Size {
  const [size, setSize] = useState<Size>({ width: 0, height: 0 });

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return undefined;

    const update = (width: number, height: number) => {
      const next = { width: Math.round(width), height: Math.round(height) };
      setSize((prev) => (prev.width === next.width && prev.height === next.height ? prev : next));
    };
    const measure = () => {
      const rect = el.getBoundingClientRect();
      update(rect.width, rect.height);
    };

    if (typeof ResizeObserver === 'undefined') {
      measure();
      window.addEventListener('resize', measure);
      return () => window.removeEventListener('resize', measure);
    }

    const observer = new ResizeObserver((entries) => {
      const entry = entries[entries.length - 1];
      if (entry) update(entry.contentRect.width, entry.contentRect.height);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);

  return size;
}
