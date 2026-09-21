import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { connectionsApi } from '@/api/endpoints';
import { ChannelCard } from '@/components/connections/ChannelCard';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import {
  channelActions,
  connectionActionError,
  isGoogleConsentUrl,
  type ChannelCardModel,
  type ConnectionNotice,
} from '@/lib/connections';

interface GmailCardProps {
  model: ChannelCardModel;
  /** Aviso al volver de Google (email autorizado o fallo). */
  notice: ConnectionNotice | null;
  onNoticeDismiss: () => void;
  onDisconnect: () => void;
}

/**
 * Gmail (OAuth2): pide la URL de consentimiento al backend y redirige a Google.
 * Al terminar, el backend devuelve al usuario a /connections?gmail=connected
 * (el alias de App.tsx lo lleva a /conexiones).
 */
export function GmailCard({ model, notice, onNoticeDismiss, onDisconnect }: GmailCardProps) {
  const [redirecting, setRedirecting] = useState(false);
  const [urlError, setUrlError] = useState<string | null>(null);
  const { canConnect } = channelActions(model.channel, model.status);

  const oauth = useMutation({
    mutationFn: connectionsApi.gmailOAuthUrl,
    onSuccess: ({ url }) => {
      if (!isGoogleConsentUrl(url)) {
        setUrlError('El servidor devolvió una dirección de autorización inesperada. Reintentá.');
        return;
      }
      setRedirecting(true);
      window.location.assign(url);
    },
  });

  const connect = () => {
    setUrlError(null);
    onNoticeDismiss();
    oauth.mutate();
  };

  const errorText = urlError ?? (oauth.isError ? connectionActionError(oauth.error, 'gmail-connect') : null);

  return (
    <ChannelCard
      model={model}
      onDisconnect={() => {
        onNoticeDismiss();
        onDisconnect();
      }}
      actions={
        canConnect ? (
          <Button onClick={connect} loading={oauth.isPending || redirecting}>
            {redirecting ? 'Redirigiendo a Google…' : 'Conectar Gmail'}
          </Button>
        ) : null
      }
    >
      {notice && (
        <Alert variant={notice.tone} role={notice.tone === 'error' ? 'alert' : 'status'}>
          {notice.text}
        </Alert>
      )}
      {errorText && (
        <Alert variant="error" role="alert">
          {errorText}
        </Alert>
      )}
    </ChannelCard>
  );
}
