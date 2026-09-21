import { botActivity } from '@/lib/monitoringSummary';

interface BotStatusProps {
  /** Último evento real conocido (resumen o feed); null si nunca hubo actividad. */
  lastActivityAt: string | null;
  nowMs: number;
  /** Ya llegó algún dato del servidor. Antes de eso no se afirma nada ("sin actividad" sería inventar). */
  known: boolean;
  /** Ni el resumen ni el feed respondieron: se avisa en vez de quedarse "consultando" para siempre. */
  failed?: boolean;
}

/**
 * "Bot activo · último evento hace X". Solo dice "activo" si hubo un evento
 * hace poco; después pasa a ámbar y a gris. No es una región en vivo: el
 * tiempo cambia cada segundo y no debe leerse en voz alta.
 */
export function BotStatus({ lastActivityAt, nowMs, known, failed = false }: BotStatusProps) {
  if (!known) {
    return (
      <div className="mon-bot mon-bot--none">
        <span className="mon-bot__dot" aria-hidden="true" />
        <p className="mon-bot__text">
          <span className="mon-bot__title">
            {failed ? 'No pudimos consultar la actividad del bot' : 'Consultando la actividad del bot…'}
          </span>
        </p>
      </div>
    );
  }

  const activity = botActivity(lastActivityAt, nowMs);

  return (
    <div className={`mon-bot mon-bot--${activity.state}`}>
      <span className="mon-bot__dot" aria-hidden="true" />
      <p className="mon-bot__text">
        <span className="mon-bot__title">{activity.title}</span>
        <span className="mon-bot__detail">· {activity.detail}</span>
      </p>
    </div>
  );
}
