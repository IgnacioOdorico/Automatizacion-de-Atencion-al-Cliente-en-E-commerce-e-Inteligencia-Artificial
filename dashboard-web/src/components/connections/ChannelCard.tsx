import type { ReactNode } from 'react';

import { CHANNEL_ICONS } from '@/components/channelIcons';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { channelActions, disconnectCopy, type ChannelCardModel } from '@/lib/connections';
import { formatDateTime } from '@/lib/format';
import type { Channel } from '@/types/api';

/** Qué representa `external_reference` en cada canal (spec connections). */
const REFERENCE_LABELS: Record<Channel, string> = {
  whatsapp: 'Número',
  telegram: 'Chat de Telegram',
  email: 'Cuenta autorizada',
};

const DESCRIPTIONS: Record<Channel, string> = {
  whatsapp: 'Atención por WhatsApp Business. Meta aprueba cada número antes de operar.',
  telegram: 'Vinculá tu chat de Telegram con un código de 6 dígitos.',
  email: 'Autorizá tu cuenta de Gmail para responder consultas por correo.',
};

interface ChannelCardProps {
  model: ChannelCardModel;
  /** Contenido propio del canal (código de Telegram, formulario, avisos). */
  children?: ReactNode;
  /** Botones de conexión propios del canal. */
  actions?: ReactNode;
  /** Pide confirmar la desconexión; sin esto la card no ofrece desconectar. */
  onDisconnect?: () => void;
}

/** Marco común de las cards de canal: cabecera, estado, referencia y acciones. */
export function ChannelCard({ model, children, actions, onDisconnect }: ChannelCardProps) {
  const Icon = CHANNEL_ICONS[model.channel];
  const showDisconnect =
    onDisconnect !== undefined && channelActions(model.channel, model.status).canDisconnect;

  return (
    <article className="card conn-card" data-channel={model.channel} data-status={model.status}>
      <header className="conn-card__head">
        <div className="conn-card__icon">
          <Icon width={20} height={20} />
        </div>
        <h2 className="conn-card__title">{model.label}</h2>
        <Badge tone={model.statusMeta.tone}>{model.statusMeta.label}</Badge>
      </header>

      <p className="conn-card__desc">{DESCRIPTIONS[model.channel]}</p>

      {model.externalReference && (
        <dl className="conn-card__ref">
          <div>
            <dt>{REFERENCE_LABELS[model.channel]}</dt>
            <dd>{model.externalReference}</dd>
          </div>
          {model.connectedAt && (
            <div>
              <dt>Desde</dt>
              <dd>{formatDateTime(model.connectedAt)}</dd>
            </div>
          )}
        </dl>
      )}

      {children}

      {(actions || showDisconnect) && (
        <div className="conn-card__actions">
          {actions}
          {showDisconnect && (
            <Button variant="danger" onClick={onDisconnect}>
              {disconnectCopy(model).triggerLabel}
            </Button>
          )}
        </div>
      )}
    </article>
  );
}
