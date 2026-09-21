import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
  type RefObject,
} from 'react';

import {
  FOLLOW_SCALE,
  ZOOM_STEP,
  centerOn,
  fitView,
  initialView,
  isInView,
  keyboardAction,
  panBy,
  pinchView,
  wheelZoomFactor,
  zoomAt,
  type PinchSample,
  type Point,
  type Rect,
  type Size,
  type View,
  type WorldBox,
} from '@/lib/viewport';

/** Cuánto hay que mover el mouse (px) para que un clic pase a ser un arrastre. */
const DRAG_THRESHOLD_PX = 4;
/** Cuánto dura el movimiento suave de la cámara (ajustar, seguir un nodo). */
const CAMERA_MS = 550;

interface Options {
  containerRef: RefObject<HTMLElement>;
  bounds: Rect;
  size: Size;
  /** Cambia con el workflow: fuerza a ajustar de nuevo aunque se haya movido la vista. */
  resetKey: string;
}

interface DragState {
  startX: number;
  startY: number;
  active: boolean;
}

const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);
const midpoint = (a: Point, b: Point): Point => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });

/**
 * Pan y zoom del lienzo: arrastrar, Ctrl + rueda (o pellizco del trackpad),
 * dos dedos, teclado y botones. Arranca ajustado a pantalla y se reajusta si el
 * tamaño cambia mientras el usuario no haya movido la vista. La matemática está
 * en lib/viewport; acá solo se conectan los eventos.
 */
export function usePanZoom({ containerRef, bounds, size, resetKey }: Options) {
  const [view, setView] = useState<View>({ x: 0, y: 0, k: 1 });
  const [dragging, setDragging] = useState(false);
  const [animating, setAnimating] = useState(false);
  const animTimer = useRef<number | undefined>(undefined);
  const viewRef = useRef(view);
  viewRef.current = view;

  const moved = useRef(false);
  const lastKey = useRef(resetKey);
  const pointers = useRef(new Map<number, Point>());
  const drag = useRef<DragState | null>(null);
  const pinch = useRef<PinchSample | null>(null);
  const sizeRef = useRef(size);
  sizeRef.current = size;

  const { minX, minY, maxX, maxY } = bounds;

  // Ajuste automático (antes de pintar, para que no se vea un destello sin ajustar).
  useLayoutEffect(() => {
    if (lastKey.current !== resetKey) {
      lastKey.current = resetKey;
      moved.current = false;
    }
    if (size.width > 0 && size.height > 0 && !moved.current) {
      setView(initialView({ minX, minY, maxX, maxY }, size));
    }
  }, [resetKey, minX, minY, maxX, maxY, size.width, size.height]);

  useEffect(() => () => window.clearTimeout(animTimer.current), []);

  /** La cámara se mueve con transición un rato; arrastrar o hacer zoom a mano la corta enseguida. */
  const animate = useCallback(() => {
    window.clearTimeout(animTimer.current);
    setAnimating(true);
    animTimer.current = window.setTimeout(() => setAnimating(false), CAMERA_MS + 50);
  }, []);
  const stopAnimation = useCallback(() => {
    window.clearTimeout(animTimer.current);
    setAnimating(false);
  }, []);

  const fit = useCallback(() => {
    moved.current = false;
    animate();
    setView(fitView({ minX, minY, maxX, maxY }, sizeRef.current));
  }, [minX, minY, maxX, maxY, animate]);

  /** Lleva la cámara a un nodo (lo centra y, si no se lee, acerca). Si ya se lee y se ve entero, no se mueve. */
  const focusOn = useCallback(
    (box: WorldBox) => {
      const current = viewRef.current;
      const size = sizeRef.current;
      if (size.width <= 0) return;
      if (current.k >= FOLLOW_SCALE && isInView(current, size, box)) return;
      moved.current = true;
      animate();
      setView(centerOn(current, size, box));
    },
    [animate],
  );

  const zoomBy = useCallback((factor: number, at?: Point) => {
    moved.current = true;
    const { width, height } = sizeRef.current;
    const center = at ?? { x: width / 2, y: height / 2 };
    setView((v) => zoomAt(v, factor, center));
  }, []);

  const local = useCallback(
    (clientX: number, clientY: number): Point => {
      const rect = containerRef.current?.getBoundingClientRect();
      return { x: clientX - (rect?.left ?? 0), y: clientY - (rect?.top ?? 0) };
    },
    [containerRef],
  );

  // Ctrl/Cmd + rueda: zoom hacia el cursor. Listener nativo no pasivo para poder
  // frenar el zoom de la página; la rueda sola no se toca (la página scrollea).
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;
    const onWheel = (event: WheelEvent) => {
      if (!event.ctrlKey && !event.metaKey) return;
      event.preventDefault();
      stopAnimation();
      moved.current = true;
      const at = local(event.clientX, event.clientY);
      setView((v) => zoomAt(v, wheelZoomFactor(event.deltaY, event.deltaMode), at));
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [containerRef, local, stopAnimation]);

  const capture = (event: ReactPointerEvent) => {
    try {
      containerRef.current?.setPointerCapture?.(event.pointerId);
    } catch {
      // el puntero ya no está activo: no pasa nada
    }
  };

  const onPointerDown = (event: ReactPointerEvent<HTMLElement>) => {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    if ((event.target as Element).closest?.('[data-wf-controls]')) return;
    const point = local(event.clientX, event.clientY);
    stopAnimation();
    pointers.current.set(event.pointerId, point);
    if (pointers.current.size === 1) {
      drag.current = { startX: point.x, startY: point.y, active: false };
    } else if (pointers.current.size === 2) {
      const [a, b] = [...pointers.current.values()];
      pinch.current = { mid: midpoint(a, b), dist: distance(a, b) };
      drag.current = { startX: point.x, startY: point.y, active: true };
      capture(event);
      setDragging(true);
    }
  };

  const onPointerMove = (event: ReactPointerEvent<HTMLElement>) => {
    const previous = pointers.current.get(event.pointerId);
    if (!previous) return;
    const point = local(event.clientX, event.clientY);
    pointers.current.set(event.pointerId, point);

    if (pointers.current.size >= 2) {
      const [a, b] = [...pointers.current.values()];
      const next: PinchSample = { mid: midpoint(a, b), dist: distance(a, b) };
      const before = pinch.current;
      pinch.current = next;
      if (before) {
        moved.current = true;
        setView((v) => pinchView(v, before, next));
      }
      return;
    }

    const state = drag.current;
    if (!state) return;
    if (!state.active) {
      if (Math.hypot(point.x - state.startX, point.y - state.startY) < DRAG_THRESHOLD_PX) return;
      state.active = true;
      capture(event);
      setDragging(true);
      // El primer tramo (hasta pasar el umbral) también cuenta, para que el diagrama no "salte".
      moved.current = true;
      setView((v) => panBy(v, point.x - state.startX, point.y - state.startY));
      return;
    }
    moved.current = true;
    setView((v) => panBy(v, point.x - previous.x, point.y - previous.y));
  };

  const release = (event: ReactPointerEvent<HTMLElement>) => {
    if (!pointers.current.delete(event.pointerId)) return;
    if (pointers.current.size < 2) pinch.current = null;
    if (pointers.current.size === 0) {
      drag.current = null;
      setDragging(false);
    } else if (pointers.current.size === 1) {
      // Quedó un dedo tras el pellizco: sigue arrastrando desde donde está, sin saltos.
      const [rest] = [...pointers.current.values()];
      drag.current = { startX: rest.x, startY: rest.y, active: true };
    }
  };

  const onKeyDown = (event: ReactKeyboardEvent<HTMLElement>) => {
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    if ((event.target as Element).closest?.('[data-wf-controls]')) return;
    const action = keyboardAction(event.key);
    if (!action) return;
    event.preventDefault();
    if (action.type === 'fit') {
      fit();
      return;
    }
    stopAnimation();
    moved.current = true;
    if (action.type === 'zoom') zoomBy(action.factor);
    else setView((v) => panBy(v, action.dx, action.dy));
  };

  return {
    view,
    dragging,
    animating,
    fit,
    focusOn,
    zoomIn: () => {
      animate();
      zoomBy(ZOOM_STEP);
    },
    zoomOut: () => {
      animate();
      zoomBy(1 / ZOOM_STEP);
    },
    handlers: {
      onPointerDown,
      onPointerMove,
      onPointerUp: release,
      onPointerCancel: release,
      onKeyDown,
    },
  };
}
