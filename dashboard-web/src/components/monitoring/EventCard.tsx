import { memo, useMemo } from 'react';

import { CHANNEL_ICONS } from '@/components/channelIcons';
import { EVENT_ICONS, SEVERITY_ICONS } from '@/components/monitoring/eventIcons';
import { Badge } from '@/components/ui/Badge';
import { CHANNEL_LABELS, formatDateTimeSeconds, formatEventClock, formatRelative } from '@/lib/format';
import { describeEvent, severityMeta } from '@/lib/monitoring';
import type { MonitoringEvent } from '@/types/monitoring';

/** Clase CSS de cada severidad (la tonalidad de la tarjeta). */
const SEVERITY_CLASS = { brand: 'info', success: 'success', warning: 'warning', danger: 'error' } as const;

interface EventCardProps {
  event: MonitoringEvent;
  /** Reloj con el que se calcula la hora relativa (ver cardTick: solo cambia cuando hace falta). */
  tick: number;
  fresh: boolean;
  onOpen: (event: MonitoringEvent) => void;
}

/**
 * Una tarjeta del feed. El texto del cliente y del bot va como texto de React
 * (nunca como HTML) y con `dir="auto"`. Todo el recuadro abre el detalle: el
 * botón del título se estira sobre la tarjeta.
 */
export const EventCard = memo(function EventCard({ event, tick, fresh, onOpen }: EventCardProps) {
  const view = useMemo(() => describeEvent(event), [event]);
  const severity = severityMeta(event.severity);
  const TypeIcon = EVENT_ICONS[view.icon];
  const SeverityIcon = SEVERITY_ICONS[severity.icon];
  const ChannelIcon = event.channel ? CHANNEL_ICONS[event.channel] : null;

  const classes = ['mon-event', `mon-event--${SEVERITY_CLASS[severity.tone as keyof typeof SEVERITY_CLASS] ?? 'info'}`];
  if (fresh) classes.push('mon-event--fresh');

  return (
    <li className={classes.join(' ')}>
      <div className="mon-event__icon" aria-hidden="true">
        <TypeIcon width={20} height={20} />
      </div>
      <div className="mon-event__body">
        <div className="mon-event__head">
          <span className="mon-event__type">{view.typeLabel}</span>
          {event.channel && ChannelIcon && (
            <Badge tone="neutral">
              <ChannelIcon width={12} height={12} aria-hidden="true" />
              {CHANNEL_LABELS[event.channel] ?? event.channel}
            </Badge>
          )}
          <Badge tone={severity.tone}>
            <SeverityIcon width={12} height={12} aria-hidden="true" />
            {severity.label}
          </Badge>
          <time
            className="mon-event__time"
            dateTime={event.ts}
            title={formatDateTimeSeconds(event.ts)}
          >
            {formatRelative(event.ts, tick)} · {formatEventClock(event.ts, tick)}
          </time>
        </div>

        <button
          type="button"
          className="mon-event__headline"
          aria-label={`${view.typeLabel}: ${view.headline}. Ver detalle`}
          onClick={() => onOpen(event)}
        >
          {view.headline}
        </button>

        {view.detail && <p className="mon-event__detail">{view.detail}</p>}

        {view.quote !== null && (
          <p
            className={`mon-quote mon-quote--clamp${event.type === 'bot_reply' ? ' mon-quote--bot' : ''}`}
            dir="auto"
          >
            {view.quote}
          </p>
        )}

        {view.chips.length > 0 && (
          <div className="mon-event__chips">
            {view.chips.map((chip) => (
              <Badge key={chip.text} tone={chip.tone}>
                {chip.text}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </li>
  );
});
