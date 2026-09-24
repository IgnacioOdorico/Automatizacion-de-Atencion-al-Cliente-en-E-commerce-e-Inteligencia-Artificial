import { describe, expect, it } from 'vitest';

import {
  BASE_STEP_MS,
  SPEEDS,
  initialPlayback,
  overlayReveal,
  playbackCaption,
  playbackReducer,
  stepDelayMs,
  type Playback,
} from '@/lib/playback';

const idle = (total: number): Playback => initialPlayback(total);

describe('stepDelayMs (velocidad de la reproducción)', () => {
  it('1× es el paso base; 2× lo divide y 0,5× lo duplica', () => {
    expect(stepDelayMs(1)).toBe(BASE_STEP_MS);
    expect(stepDelayMs(2)).toBe(BASE_STEP_MS / 2);
    expect(stepDelayMs(0.5)).toBe(BASE_STEP_MS * 2);
  });

  it('ofrece 0,5×, 1× y 2×', () => {
    expect([...SPEEDS]).toEqual([0.5, 1, 2]);
  });

  it('una velocidad inválida cae en la base', () => {
    expect(stepDelayMs(0)).toBe(BASE_STEP_MS);
    expect(stepDelayMs(-1)).toBe(BASE_STEP_MS);
    expect(stepDelayMs(Number.NaN)).toBe(BASE_STEP_MS);
  });
});

describe('initialPlayback y overlayReveal', () => {
  it('arranca en reposo con el resultado final a la vista', () => {
    const state = idle(6);
    expect(state).toEqual({ mode: 'idle', revealed: 6, total: 6 });
    expect(overlayReveal(state)).toBeNull();
  });

  it('reproduciendo o en pausa, se ven solo los pasos revelados', () => {
    expect(overlayReveal({ mode: 'playing', revealed: 2, total: 6 })).toBe(2);
    expect(overlayReveal({ mode: 'paused', revealed: 4, total: 6 })).toBe(4);
  });
});

describe('playbackReducer', () => {
  it('play desde el reposo empieza por el primer nodo', () => {
    expect(playbackReducer(idle(5), { type: 'play' })).toEqual({ mode: 'playing', revealed: 1, total: 5 });
  });

  it('cada tick revela un nodo más y al llegar al último vuelve al reposo con todo a la vista', () => {
    let state = playbackReducer(idle(3), { type: 'play' });
    state = playbackReducer(state, { type: 'tick' });
    expect(state).toEqual({ mode: 'playing', revealed: 2, total: 3 });
    state = playbackReducer(state, { type: 'tick' });
    expect(state).toEqual({ mode: 'idle', revealed: 3, total: 3 });
  });

  it('pausa congela el paso y play retoma desde donde estaba', () => {
    let state = playbackReducer(idle(5), { type: 'play' });
    state = playbackReducer(state, { type: 'tick' });
    state = playbackReducer(state, { type: 'pause' });
    expect(state).toEqual({ mode: 'paused', revealed: 2, total: 5 });
    expect(playbackReducer(state, { type: 'tick' })).toBe(state);
    expect(playbackReducer(state, { type: 'play' })).toEqual({ mode: 'playing', revealed: 2, total: 5 });
  });

  it('reiniciar vuelve al primer nodo y reproduce, esté como esté', () => {
    for (const from of [idle(4), { mode: 'paused', revealed: 3, total: 4 } as Playback, { mode: 'playing', revealed: 2, total: 4 } as Playback]) {
      expect(playbackReducer(from, { type: 'restart' })).toEqual({ mode: 'playing', revealed: 1, total: 4 });
    }
  });

  it('"mostrar resultado" salta al final', () => {
    expect(playbackReducer({ mode: 'playing', revealed: 2, total: 5 }, { type: 'showAll' })).toEqual(idle(5));
  });

  it('cargar otra ejecución reinicia todo con el nuevo largo', () => {
    expect(playbackReducer({ mode: 'playing', revealed: 2, total: 5 }, { type: 'load', total: 8 })).toEqual(idle(8));
  });

  it('un tick fuera de la reproducción no hace nada', () => {
    const state = idle(3);
    expect(playbackReducer(state, { type: 'tick' })).toBe(state);
  });

  it('play mientras ya reproduce, o pausa en reposo, no cambian nada', () => {
    const playing: Playback = { mode: 'playing', revealed: 2, total: 5 };
    expect(playbackReducer(playing, { type: 'play' })).toBe(playing);
    expect(playbackReducer(idle(5), { type: 'pause' })).toEqual(idle(5));
  });

  it('con un solo nodo o ninguno no hay nada que animar', () => {
    expect(playbackReducer(idle(0), { type: 'play' })).toEqual(idle(0));
    expect(playbackReducer(idle(1), { type: 'play' })).toEqual(idle(1));
    expect(playbackReducer(idle(0), { type: 'restart' })).toEqual(idle(0));
  });
});

describe('playbackCaption (el texto "Paso 3 de 10")', () => {
  const path = ['Webhook', 'Registrar Orden', 'Verificar Stock'];

  it('en reposo no hay leyenda', () => {
    expect(playbackCaption(initialPlayback(3), path)).toBeNull();
  });

  it('reproduciendo dice el paso y el nodo en el que está', () => {
    expect(playbackCaption({ mode: 'playing', revealed: 2, total: 3 }, path)).toEqual({
      step: 'Paso 2 de 3',
      node: 'Registrar Orden',
    });
  });

  it('en pausa también, y lo aclara', () => {
    expect(playbackCaption({ mode: 'paused', revealed: 1, total: 3 }, path)).toEqual({
      step: 'Paso 1 de 3 (en pausa)',
      node: 'Webhook',
    });
  });

  it('si el camino no alcanza (datos inconsistentes) no inventa un nodo', () => {
    expect(playbackCaption({ mode: 'playing', revealed: 5, total: 3 }, path)?.node).toBeNull();
  });
});
