/**
 * Reproducción del camino de una ejecución, nodo por nodo (didáctica para
 * explicar el workflow en cámara). Máquina de estados pura: el hook solo
 * dispara `tick` con un temporizador.
 *
 * `idle` es el reposo: el resultado final está a la vista (todos los nodos
 * revelados). `playing`/`paused` muestran solo los primeros `revealed` nodos.
 */

export const SPEEDS = [0.5, 1, 2] as const;
export type Speed = (typeof SPEEDS)[number];

/** Cuánto se queda cada nodo antes de pasar al siguiente, a velocidad 1×. */
export const BASE_STEP_MS = 900;

export function stepDelayMs(speed: number): number {
  if (!Number.isFinite(speed) || speed <= 0) return BASE_STEP_MS;
  return Math.round(BASE_STEP_MS / speed);
}

export interface Playback {
  mode: 'idle' | 'playing' | 'paused';
  revealed: number;
  total: number;
}

export type PlaybackAction =
  | { type: 'load'; total: number }
  | { type: 'play' }
  | { type: 'pause' }
  | { type: 'restart' }
  | { type: 'showAll' }
  | { type: 'tick' };

export function initialPlayback(total: number): Playback {
  return { mode: 'idle', revealed: total, total };
}

/** Cuántos nodos mostrar en el diagrama; `null` = todo (vista final). */
export function overlayReveal(state: Playback): number | null {
  return state.mode === 'idle' ? null : state.revealed;
}

function start(state: Playback): Playback {
  if (state.total <= 1) return initialPlayback(state.total);
  return { mode: 'playing', revealed: 1, total: state.total };
}

export function playbackReducer(state: Playback, action: PlaybackAction): Playback {
  switch (action.type) {
    case 'load':
      return initialPlayback(action.total);
    case 'showAll':
      return initialPlayback(state.total);
    case 'restart':
      return start(state);
    case 'play':
      if (state.mode === 'playing') return state;
      if (state.mode === 'paused') return { ...state, mode: 'playing' };
      return start(state);
    case 'pause':
      return state.mode === 'playing' ? { ...state, mode: 'paused' } : state;
    case 'tick': {
      if (state.mode !== 'playing') return state;
      const revealed = state.revealed + 1;
      return revealed >= state.total ? initialPlayback(state.total) : { ...state, revealed };
    }
  }
}

export interface PlaybackCaption {
  step: string;
  /** El nodo en el que está la reproducción (`null` si el camino no lo trae). */
  node: string | null;
}

/** Leyenda de la reproducción ("Paso 3 de 10" + nodo actual); `null` en reposo. */
export function playbackCaption(state: Playback, path: readonly string[]): PlaybackCaption | null {
  if (state.mode === 'idle') return null;
  const paused = state.mode === 'paused' ? ' (en pausa)' : '';
  return {
    step: `Paso ${state.revealed} de ${state.total}${paused}`,
    node: path[state.revealed - 1] ?? null,
  };
}
