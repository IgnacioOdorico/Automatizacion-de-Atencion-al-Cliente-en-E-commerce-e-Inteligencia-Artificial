import { useState } from 'react';

import { ChannelCard } from '@/components/connections/ChannelCard';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import type { TelegramLink } from '@/hooks/useTelegramLink';
import { channelActions, type ChannelCardModel } from '@/lib/connections';
import { formatCountdown } from '@/lib/telegramLink';

interface TelegramCardProps {
  model: ChannelCardModel;
  link: TelegramLink;
  onDisconnect: () => void;
}

function CodePanel({ link }: { link: TelegramLink }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    if (!link.code) return;
    try {
      await navigator.clipboard.writeText(link.code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Sin permiso de portapapeles: el código sigue visible para copiarlo a mano.
    }
  };

  return (
    <div className="link-panel">
      <div className="link-panel__code-row">
        <span className="link-panel__code" aria-label={`Código de vinculación ${link.code}`}>
          {link.code}
        </span>
        <Button variant="ghost" onClick={copy} disabled={link.expired}>
          {copied ? 'Copiado' : 'Copiar'}
        </Button>
      </div>

      {link.expired ? (
        <Alert variant="error" role="alert">
          El código venció. Generá uno nuevo para continuar.
        </Alert>
      ) : (
        <>
          <p className="link-panel__timer">
            Vence en <strong>{formatCountdown(link.secondsLeft)}</strong>
          </p>
          <ol className="link-panel__steps">
            <li>Abrí Telegram y escribile al bot de vinculación de la plataforma.</li>
            <li>Enviale el código de 6 dígitos tal cual, sin espacios ni texto extra.</li>
            <li>Esta tarjeta se actualiza sola cuando el bot confirme el vínculo.</li>
          </ol>
          <p className="link-panel__waiting" role="status">
            <Spinner size={14} />
            Esperando tu mensaje en Telegram…
          </p>
        </>
      )}
    </div>
  );
}

export function TelegramCard({ model, link, onDisconnect }: TelegramCardProps) {
  const { canConnect } = channelActions(model.channel, model.status);
  const showLinkedNotice = link.linked && model.status === 'connected';

  return (
    <ChannelCard
      model={model}
      onDisconnect={onDisconnect}
      actions={
        link.hasCode ? (
          <>
            {link.expired && (
              <Button onClick={link.start} loading={link.starting}>
                Generar código nuevo
              </Button>
            )}
            <Button variant="ghost" onClick={link.dismiss}>
              {link.expired ? 'Cerrar' : 'Cancelar'}
            </Button>
          </>
        ) : canConnect ? (
          <Button onClick={link.start} loading={link.starting}>
            Conectar Telegram
          </Button>
        ) : null
      }
    >
      {showLinkedNotice && (
        <Alert variant="success" role="status">
          Listo, tu chat de Telegram quedó vinculado.
        </Alert>
      )}
      {link.error && (
        <Alert variant="error" role="alert">
          {link.error}
        </Alert>
      )}
      {link.hasCode && <CodePanel link={link} />}
    </ChannelCard>
  );
}
