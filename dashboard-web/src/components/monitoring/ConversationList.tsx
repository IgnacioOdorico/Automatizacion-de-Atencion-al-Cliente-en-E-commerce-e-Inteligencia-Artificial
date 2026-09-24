import { CHANNEL_ICONS } from '@/components/channelIcons';
import { AlertIcon } from '@/components/icons';
import { Badge } from '@/components/ui/Badge';
import { intentMeta } from '@/lib/domain';
import { CHANNEL_LABELS, formatContact, formatRelative } from '@/lib/format';
import { sameConversation, type ConversationRef } from '@/lib/conversations';
import type { ConversationSummary } from '@/types/monitoring';

interface ConversationListProps {
  rows: readonly ConversationSummary[];
  selected: ConversationRef | null;
  nowMs: number;
  onSelect: (conversation: ConversationRef) => void;
}

const plural = (n: number, one: string, many: string): string => `${n} ${n === 1 ? one : many}`;

/**
 * Lista de hilos (un hilo = canal + usuario): contacto, vista previa del último
 * mensaje del cliente, cuándo fue, cuántos mensajes tiene y si hay algo urgente
 * o tickets abiertos. Cada hilo es un botón; el elegido lleva aria-current.
 */
export function ConversationList({ rows, selected, nowMs, onSelect }: ConversationListProps) {
  return (
    <ul className="mon-convs" aria-label="Conversaciones, la más reciente primero">
      {rows.map((row) => {
        const ref: ConversationRef = { channel: row.channel, userId: row.user_id };
        const isSelected = sameConversation(selected, ref);
        const ChannelIcon = CHANNEL_ICONS[row.channel];
        const intent = row.last_intent ? intentMeta(row.last_intent) : null;

        return (
          <li key={`${row.channel}:${row.user_id}`}>
            <button
              type="button"
              className={`mon-conv${isSelected ? ' mon-conv--selected' : ''}`}
              aria-current={isSelected ? 'true' : undefined}
              onClick={() => onSelect(ref)}
            >
              <span className="mon-conv__avatar" aria-hidden="true">
                <ChannelIcon width={18} height={18} />
              </span>
              <span className="mon-conv__main">
                <span className="mon-conv__top">
                  <span className="mon-conv__name">{formatContact(row.channel, row.user_id)}</span>
                  <span className="mon-conv__time">{formatRelative(row.last_at, nowMs)}</span>
                </span>
                <span className="mon-conv__preview" dir="auto">
                  {row.last_message_preview ?? '—'}
                </span>
                <span className="mon-conv__meta">
                  {CHANNEL_LABELS[row.channel] ?? row.channel} ·{' '}
                  {plural(row.messages, 'mensaje', 'mensajes')}
                </span>
                {(row.has_urgent || row.open_tickets > 0 || intent) && (
                  <span className="mon-conv__badges">
                    {row.has_urgent && (
                      <Badge tone="danger">
                        <AlertIcon width={12} height={12} aria-hidden="true" />
                        Urgente
                      </Badge>
                    )}
                    {row.open_tickets > 0 && (
                      <Badge tone="warning">
                        {plural(row.open_tickets, 'ticket abierto', 'tickets abiertos')}
                      </Badge>
                    )}
                    {intent && <Badge tone={intent.tone}>{intent.label}</Badge>}
                  </span>
                )}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
