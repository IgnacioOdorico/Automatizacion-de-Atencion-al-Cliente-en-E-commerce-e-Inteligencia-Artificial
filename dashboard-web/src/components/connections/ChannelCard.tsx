import type { FC, ReactNode, SVGProps } from 'react';

import { MailIcon, MessengerIcon, SendIcon } from '@/components/icons';
import { Badge } from '@/components/ui/Badge';
import type { ChannelCardModel } from '@/lib/connections';
import { formatDateTime } from '@/lib/format';
import type { Channel } from '@/types/api';

const CHANNEL_ICONS: Record<Channel, FC<SVGProps<SVGSVGElement>>> = {
  whatsapp: MessengerIcon,
  telegram: SendIcon,
  email: MailIcon,
};

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
  /** Botones de la card (conectar / desconectar). */
  actions?: ReactNode;
}

/** Marco común de las cards de canal: cabecera, estado, referencia y acciones. */
export function ChannelCard({ model, children, actions }: ChannelCardProps) {
  const Icon = CHANNEL_ICONS[model.channel];

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

      {actions && <div className="conn-card__actions">{actions}</div>}
    </article>
  );
}
