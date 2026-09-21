/**
 * jsdom no mide nada ni trae ResizeObserver: este doble le da al lienzo del
 * diagrama un tamaño conocido y permite simular un cambio de tamaño.
 */
import { act } from 'react';
import { vi } from 'vitest';

type Callback = (entries: Array<{ target: Element; contentRect: { width: number; height: number } }>) => void;

interface Entry {
  cb: Callback;
  el: Element | null;
}

let observers: Entry[] = [];
let size = { width: 900, height: 400 };

class FakeResizeObserver {
  private entry: Entry;
  constructor(cb: Callback) {
    this.entry = { cb, el: null };
    observers.push(this.entry);
  }
  observe(el: Element) {
    this.entry.el = el;
    this.entry.cb([{ target: el, contentRect: { ...size } }]);
  }
  unobserve() {}
  disconnect() {
    observers = observers.filter((o) => o !== this.entry);
  }
}

export function installFakeResizeObserver(initial = { width: 900, height: 400 }) {
  observers = [];
  size = { ...initial };
  vi.stubGlobal('ResizeObserver', FakeResizeObserver);
}

export function resizeCanvas(width: number, height: number) {
  size = { width, height };
  act(() => {
    for (const o of observers) if (o.el) o.cb([{ target: o.el, contentRect: { width, height } }]);
  });
}
