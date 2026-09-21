import { useCallback, useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { connectionsApi, dashboardApi } from '@/api/endpoints';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { GmailCard } from '@/components/connections/GmailCard';
import { TelegramCard } from '@/components/connections/TelegramCard';
import { WhatsAppCard } from '@/components/connections/WhatsAppCard';
import { QueryView } from '@/components/QueryView';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { useGmailReturn } from '@/hooks/useGmailReturn';
import { useTelegramLink } from '@/hooks/useTelegramLink';
import {
  buildChannelCards,
  connectionActionError,
  disconnectCopy,
  type ChannelCardModel,
} from '@/lib/connections';
import { TELEGRAM_POLL_MS } from '@/lib/telegramLink';

function ConnectionsSkeleton() {
  return (
    <div className="conn-grid" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <div key={i} className="card conn-card conn-card--skeleton">
          <div className="conn-card__head">
            <Skeleton height={40} width={40} radius={11} />
            <Skeleton height={16} width="38%" />
          </div>
          <Skeleton height={13} />
          <Skeleton height={13} width="70%" />
          <Skeleton height={40} width={150} radius={8} />
        </div>
      ))}
    </div>
  );
}

/**
 * Conexiones (GET /connections): una card por canal con su estado real.
 * En BD el canal de correo es `email`; la UI lo muestra como "Gmail".
 */
export function ConexionesPage() {
  const queryClient = useQueryClient();
  const telegram = useTelegramLink();

  const query = useQuery({
    queryKey: ['connections'],
    queryFn: dashboardApi.connections,
    // Mientras hay un código de Telegram vigente se consulta el estado hasta
    // que el workflow n8n confirme el vínculo (sin recargar la página).
    refetchInterval: telegram.polling ? TELEGRAM_POLL_MS : false,
  });
  const { data, refetch, isFetching } = query;

  /** Tras mutar un canal: releer la lista y /me (Perfil y sidebar leen los canales de ahí). */
  const refreshConnections = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ['connections'] });
    void queryClient.invalidateQueries({ queryKey: ['me'] });
  }, [queryClient]);

  // Desconexión: confirmación por card + DELETE /connections/{channel}.
  const [disconnecting, setDisconnecting] = useState<ChannelCardModel | null>(null);
  const disconnect = useMutation({
    mutationFn: connectionsApi.disconnect,
    onSuccess: (_res, channel) => {
      if (channel === 'telegram') telegram.dismiss();
      setDisconnecting(null);
      refreshConnections();
    },
  });
  const { reset: resetDisconnect } = disconnect;
  const askDisconnect = (card: ChannelCardModel) => {
    resetDisconnect();
    setDisconnecting(card);
  };
  const cancelDisconnect = useCallback(() => {
    setDisconnecting(null);
    resetDisconnect();
  }, [resetDisconnect]);

  const cards = useMemo(() => buildChannelCards(data?.items), [data]);
  const telegramStatus = cards.find((card) => card.channel === 'telegram')?.status;
  const gmailCard = cards.find((card) => card.channel === 'email') ?? cards[cards.length - 1];
  const gmailReturn = useGmailReturn(gmailCard, Boolean(data));

  const { hasCode, complete } = telegram;
  useEffect(() => {
    if (hasCode && telegramStatus === 'connected') {
      complete();
      // Perfil y sidebar leen los canales desde /me.
      void queryClient.invalidateQueries({ queryKey: ['me'] });
    }
  }, [hasCode, telegramStatus, complete, queryClient]);

  return (
    <div className="page">
      <header className="page__head page__head--row">
        <div>
          <h1>Conexiones</h1>
          <p className="page__sub">
            Los canales por los que atendés a tus clientes. Conectá, revisá o desconectá cada uno
            desde acá.
          </p>
        </div>
        <Button variant="ghost" onClick={() => refetch()} loading={isFetching}>
          Actualizar
        </Button>
      </header>

      <QueryView query={query} loading={<ConnectionsSkeleton />}>
        {() => (
          <div className="conn-grid">
            {cards.map((card) => {
              switch (card.channel) {
                case 'telegram':
                  return (
                    <TelegramCard
                      key={card.channel}
                      model={card}
                      link={telegram}
                      onDisconnect={() => askDisconnect(card)}
                    />
                  );
                case 'email':
                  return (
                    <GmailCard
                      key={card.channel}
                      model={card}
                      notice={gmailReturn.notice}
                      onNoticeDismiss={gmailReturn.dismiss}
                      onDisconnect={() => askDisconnect(card)}
                    />
                  );
                default:
                  return (
                    <WhatsAppCard
                      key={card.channel}
                      model={card}
                      onChanged={refreshConnections}
                      onDisconnect={() => askDisconnect(card)}
                    />
                  );
              }
            })}
          </div>
        )}
      </QueryView>

      {disconnecting && (
        <ConfirmDialog
          {...disconnectCopy(disconnecting)}
          loading={disconnect.isPending}
          error={disconnect.isError ? connectionActionError(disconnect.error, 'disconnect') : null}
          onConfirm={() => disconnect.mutate(disconnecting.channel)}
          onCancel={cancelDisconnect}
        />
      )}
    </div>
  );
}
