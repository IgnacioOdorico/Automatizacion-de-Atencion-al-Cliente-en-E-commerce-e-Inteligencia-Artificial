import { PauseIcon, PlayIcon, RefreshIcon } from '@/components/icons';
import { Button } from '@/components/ui/Button';
import { SPEEDS, type Playback, type PlaybackCaption } from '@/lib/playback';

interface PlaybackBarProps {
  state: Playback;
  /** Hay un camino que reproducir (una ejecución con traza). */
  canPlay: boolean;
  speed: number;
  onSpeed: (speed: number) => void;
  /** La cámara del diagrama sigue el nodo actual. */
  camera: boolean;
  onCamera: (on: boolean) => void;
  reducedMotion: boolean;
  onPlay: () => void;
  onPause: () => void;
  onRestart: () => void;
  onShowAll: () => void;
}

const SPEED_LABEL: Record<number, string> = { 0.5: '0,5×', 1: '1×', 2: '2×' };

/** Barra de la reproducción del camino: reproducir/pausar, reiniciar, ver el resultado, velocidad y cámara. */
export function PlaybackBar({
  state,
  canPlay,
  speed,
  onSpeed,
  camera,
  onCamera,
  reducedMotion,
  onPlay,
  onPause,
  onRestart,
  onShowAll,
}: PlaybackBarProps) {
  const playing = state.mode === 'playing';
  const paused = state.mode === 'paused';
  const idle = state.mode === 'idle';

  return (
    <div className="wf-playbar" role="group" aria-label="Reproducción del camino">
      <div className="wf-playbar__main">
        {playing ? (
          <Button variant="primary" onClick={onPause}>
            <PauseIcon width={16} height={16} />
            Pausar
          </Button>
        ) : (
          <Button variant="primary" onClick={onPlay} disabled={!canPlay}>
            <PlayIcon width={16} height={16} />
            {paused ? 'Continuar' : 'Reproducir camino'}
          </Button>
        )}
        <Button variant="ghost" onClick={onRestart} disabled={!canPlay || idle}>
          <RefreshIcon width={16} height={16} />
          Reiniciar
        </Button>
        <Button variant="ghost" onClick={onShowAll} disabled={!canPlay || idle}>
          Ver resultado final
        </Button>
      </div>

      <div className="wf-playbar__opts">
        <div className="wf-speed" role="group" aria-label="Velocidad de la reproducción">
          {SPEEDS.map((value) => (
            <button
              key={value}
              type="button"
              className="mon-chip"
              aria-pressed={speed === value}
              onClick={() => onSpeed(value)}
            >
              {SPEED_LABEL[value]}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="mon-chip"
          aria-pressed={camera}
          onClick={() => onCamera(!camera)}
          title="El diagrama se acerca y sigue cada nodo mientras se reproduce"
        >
          Seguir con la cámara
        </button>
      </div>

      {reducedMotion && (
        <p className="wf-playbar__note">
          Tu dispositivo pidió menos movimiento: se muestra el resultado final sin animar.
        </p>
      )}
    </div>
  );
}

/** Leyenda "Paso 3 de 10 · Verificar Stock" sobre el lienzo; se anuncia a lectores de pantalla. */
export function PlaybackCaptionPill({ caption }: { caption: PlaybackCaption }) {
  return (
    <p className="wf-caption" aria-live="polite">
      <span className="wf-caption__step">{caption.step}</span>
      {caption.node && <strong className="wf-caption__node">{caption.node}</strong>}
    </p>
  );
}
