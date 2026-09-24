import { useCallback, useEffect, useReducer } from 'react';

import {
  initialPlayback,
  overlayReveal,
  playbackReducer,
  stepDelayMs,
  type Playback,
} from '@/lib/playback';

interface Options {
  /** Cambia con cada ejecución: la reproducción vuelve al reposo con el resultado a la vista. */
  executionKey: string | number | null;
  /** Cantidad de nodos del camino. */
  total: number;
  speed: number;
  /** Con movimiento reducido no se anima: "reproducir" muestra el resultado final. */
  reducedMotion: boolean;
}

/**
 * Reproduce el camino de una ejecución nodo por nodo. La máquina de estados es
 * pura (lib/playback); acá solo se dispara `tick` con un temporizador que
 * respeta la velocidad elegida y se corta al pausar, reiniciar o cambiar de ejecución.
 */
export function usePlayback({ executionKey, total, speed, reducedMotion }: Options) {
  const [state, dispatch] = useReducer(playbackReducer, total, initialPlayback);

  useEffect(() => {
    dispatch({ type: 'load', total });
  }, [executionKey, total]);

  useEffect(() => {
    if (state.mode !== 'playing') return undefined;
    const timer = window.setTimeout(() => dispatch({ type: 'tick' }), stepDelayMs(speed));
    return () => window.clearTimeout(timer);
  }, [state.mode, state.revealed, speed]);

  const play = useCallback(() => dispatch({ type: reducedMotion ? 'showAll' : 'play' }), [reducedMotion]);
  const restart = useCallback(() => dispatch({ type: reducedMotion ? 'showAll' : 'restart' }), [reducedMotion]);
  const pause = useCallback(() => dispatch({ type: 'pause' }), []);
  const showAll = useCallback(() => dispatch({ type: 'showAll' }), []);

  return {
    state: state as Playback,
    /** Cuántos nodos mostrar; `null` = todo. */
    reveal: overlayReveal(state),
    play,
    pause,
    restart,
    showAll,
  };
}
