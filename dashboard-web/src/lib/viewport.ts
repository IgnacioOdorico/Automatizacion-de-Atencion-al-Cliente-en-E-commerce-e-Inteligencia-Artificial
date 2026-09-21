/**
 * Matemática del lienzo con pan y zoom (sin React ni DOM). La vista es la
 * transformación mundo -> pantalla: `pantalla = mundo * k + (x, y)`.
 */

export interface View {
  x: number;
  y: number;
  k: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface Rect {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

export interface Size {
  width: number;
  height: number;
}

export const MIN_SCALE = 0.1;
export const MAX_SCALE = 3;

/** Un paso de los botones +/- y del teclado. */
export const ZOOM_STEP = 1.25;
/** Cuánto se mueve la vista con cada flecha, en píxeles de pantalla. */
export const KEY_PAN_PX = 60;

/** En un lienzo más angosto que esto (un celular) el diagrama entero no se lee: se abre acercado. */
export const COMPACT_WIDTH = 640;
/** Escala con la que se abre el diagrama en un lienzo angosto (el texto de las tarjetas se lee). */
export const COMPACT_SCALE = 0.7;
/** Escala mínima con la que la cámara sigue un nodo en la reproducción (el texto se lee). */
export const FOLLOW_SCALE = 0.9;

const NEUTRAL: View = { x: 0, y: 0, k: 1 };

export function clampScale(k: number): number {
  return Math.min(MAX_SCALE, Math.max(MIN_SCALE, k));
}

export function toScreen(view: View, p: Point): Point {
  return { x: p.x * view.k + view.x, y: p.y * view.k + view.y };
}

export function toWorld(view: View, p: Point): Point {
  return { x: (p.x - view.x) / view.k, y: (p.y - view.y) / view.k };
}

/** Valor de la propiedad CSS `transform` del grupo que se mueve (con CSS se puede animar la cámara). */
export function viewCss(view: View): string {
  return `translate(${view.x}px, ${view.y}px) scale(${view.k})`;
}

interface FitOptions {
  padding?: number;
  maxScale?: number;
}

/**
 * "Ajustar a pantalla": la escala más grande con la que entra todo el
 * diagrama (con margen), centrado. Un diagrama chico no se agranda más de
 * `maxScale`. Sin tamaño de lienzo (todavía no se midió) devuelve la vista neutra.
 */
export function fitView(bounds: Rect, size: Size, options: FitOptions = {}): View {
  const { padding = 32, maxScale = 1.25 } = options;
  if (size.width <= 0 || size.height <= 0) return NEUTRAL;
  const width = Math.max(bounds.maxX - bounds.minX, 1);
  const height = Math.max(bounds.maxY - bounds.minY, 1);
  const availableW = Math.max(size.width - padding * 2, 1);
  const availableH = Math.max(size.height - padding * 2, 1);
  const k = clampScale(Math.min(availableW / width, availableH / height, maxScale));
  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;
  return { k, x: size.width / 2 - centerX * k, y: size.height / 2 - centerY * k };
}

/**
 * Con qué vista se abre el diagrama: el ajuste a pantalla, salvo en un lienzo
 * angosto (un celular), donde entero quedaría ilegible: ahí se abre acercado,
 * desde el principio del flujo, y el usuario lo recorre (o toca "Ajustar").
 */
export function initialView(bounds: Rect, size: Size, options: FitOptions = {}): View {
  const fit = fitView(bounds, size, options);
  if (size.width <= 0 || size.height <= 0 || size.width >= COMPACT_WIDTH || fit.k >= COMPACT_SCALE) return fit;
  const { padding = 32 } = options;
  const k = COMPACT_SCALE;
  return {
    k,
    x: padding - bounds.minX * k,
    y: size.height / 2 - ((bounds.minY + bounds.maxY) / 2) * k,
  };
}

interface HeightOptions extends FitOptions {
  /** Lugar extra para los controles que flotan sobre el lienzo. */
  reserve?: number;
  min?: number;
  max?: number;
}

/**
 * Alto del lienzo para que un diagrama chato (como estos flujos) no deje aire
 * de sobra: lo que mide el dibujo con el ajuste a ese ancho, más márgenes y
 * lugar para los controles. `null` mientras no se conoce el ancho.
 */
export function preferredHeight(bounds: Rect, width: number, options: HeightOptions = {}): number | null {
  if (width <= 0) return null;
  const { padding = 32, maxScale = 1.25, reserve = 88, min = 400, max = 620 } = options;
  const w = Math.max(bounds.maxX - bounds.minX, 1);
  const h = Math.max(bounds.maxY - bounds.minY, 1);
  const k = clampScale(Math.min(Math.max(width - padding * 2, 1) / w, maxScale));
  return Math.min(max, Math.max(min, Math.round(h * k + padding * 2 + reserve)));
}

export interface WorldBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

/**
 * La cámara va a un nodo: su centro queda en el centro del lienzo. Si el zoom
 * actual no alcanza para leer, sube hasta `minScale` (por defecto FOLLOW_SCALE);
 * si ya se lee, lo respeta.
 */
export function centerOn(view: View, size: Size, box: WorldBox, options: { minScale?: number } = {}): View {
  const k = clampScale(Math.max(view.k, options.minScale ?? FOLLOW_SCALE));
  return {
    k,
    x: size.width / 2 - (box.x + box.w / 2) * k,
    y: size.height / 2 - (box.y + box.h / 2) * k,
  };
}

/** ¿El nodo se ve entero, dejando `margin` px de aire contra los bordes? */
export function isInView(view: View, size: Size, box: WorldBox, margin = 24): boolean {
  const left = box.x * view.k + view.x;
  const top = box.y * view.k + view.y;
  const right = (box.x + box.w) * view.k + view.x;
  const bottom = (box.y + box.h) * view.k + view.y;
  return left >= margin && top >= margin && right <= size.width - margin && bottom <= size.height - margin;
}

/** Zoom multiplicativo manteniendo quieto el punto del mundo que está bajo `point` (en pantalla). */
export function zoomAt(view: View, factor: number, point: Point): View {
  const k = clampScale(view.k * factor);
  const real = k / view.k;
  return {
    k,
    x: point.x - (point.x - view.x) * real,
    y: point.y - (point.y - view.y) * real,
  };
}

export function panBy(view: View, dx: number, dy: number): View {
  return { ...view, x: view.x + dx, y: view.y + dy };
}

const WHEEL_SENSITIVITY = 0.002;
/** Una rueda por líneas (deltaMode 1) equivale a ~16 px por línea. */
const LINE_HEIGHT_PX = 16;
const WHEEL_MAX_FACTOR = 2;

/**
 * Factor de zoom de un evento de rueda (Ctrl + rueda, o el pellizco del
 * trackpad, que el navegador manda como rueda con Ctrl). Hacia arriba acerca.
 */
export function wheelZoomFactor(deltaY: number, deltaMode = 0): number {
  const pixels = deltaMode === 1 ? deltaY * LINE_HEIGHT_PX : deltaY;
  const factor = Math.exp(-pixels * WHEEL_SENSITIVITY);
  return Math.min(WHEEL_MAX_FACTOR, Math.max(1 / WHEEL_MAX_FACTOR, factor));
}

export interface PinchSample {
  mid: Point;
  dist: number;
}

/** Pellizco de dos dedos: zoom por el cambio de distancia y pan por el desplazamiento del punto medio. */
export function pinchView(view: View, prev: PinchSample, next: PinchSample): View {
  const factor = prev.dist > 0 && next.dist > 0 ? next.dist / prev.dist : 1;
  const zoomed = zoomAt(view, factor, prev.mid);
  return panBy(zoomed, next.mid.x - prev.mid.x, next.mid.y - prev.mid.y);
}

export type KeyboardAction =
  | { type: 'pan'; dx: number; dy: number }
  | { type: 'zoom'; factor: number }
  | { type: 'fit' };

/**
 * Teclado del lienzo: las flechas mueven la vista hacia donde apuntan (el
 * contenido se corre al revés), `+`/`=` acercan, `-` aleja y `0` ajusta a pantalla.
 */
export function keyboardAction(key: string): KeyboardAction | null {
  switch (key) {
    case 'ArrowLeft':
      return { type: 'pan', dx: KEY_PAN_PX, dy: 0 };
    case 'ArrowRight':
      return { type: 'pan', dx: -KEY_PAN_PX, dy: 0 };
    case 'ArrowUp':
      return { type: 'pan', dx: 0, dy: KEY_PAN_PX };
    case 'ArrowDown':
      return { type: 'pan', dx: 0, dy: -KEY_PAN_PX };
    case '+':
    case '=':
      return { type: 'zoom', factor: ZOOM_STEP };
    case '-':
    case '_':
      return { type: 'zoom', factor: 1 / ZOOM_STEP };
    case '0':
      return { type: 'fit' };
    default:
      return null;
  }
}
