import { useEffect, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { ChannelCard } from '@/components/connections/ChannelCard';
import { GmailCard } from '@/components/connections/GmailCard';
import { TelegramCard } from '@/components/connections/TelegramCard';
import { PlugIcon } from '@/components/icons';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { useGmailReturn } from '@/hooks/useGmailReturn';
import { useTelegramLink } from '@/hooks/useTelegramLink';
import { buildChannelCards } from '@/lib/connections';
import { friendlyApiError } from '@/lib/messages';
import { TELEGRAM_POLL_MS } from '@/lib/telegramLink';

/**
 * Conexiones (GET /connections): una card por canal con su estado real.
 * En BD el canal de correo es `email`; la UI lo muestra como "Gmail".
 */
export function ConexionesPage() {
  const queryClient = useQueryClient();
  const telegram = useTelegramLink();

  const { data, isPending, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['connections'],
    queryFn: dashboardApi.connections,
    // Mientras hay un código de Telegram vigente se consulta el estado hasta
    // que el workflow n8n confirme el vínculo (sin recargar la página).
    refetchInterval: telegram.polling ? TELEGRAM_POLL_MS : false,
  });

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
        <Button variant="ghost" onClick={() => refetch()} loading={isFetching && !isPending}>
          Actualizar
        </Button>
      </header>

      {isError && (
        <Alert variant="error" role="alert">
          {friendlyApiError(error)}
        </Alert>
      )}

      {isPending && (
        <div className="conn-grid">
          {[0, 1, 2].map((i) => (
            <div key={i} className="skeleton" style={{ height: 210, borderRadius: 16 }} />
          ))}
        </div>
      )}

      {!isPending && !data && (
        <EmptyState
          icon={<PlugIcon width={24} height={24} />}
          title="No se pudieron cargar las conexiones"
          text="Reintentá con el botón Actualizar. Si persiste, revisá la conexión con la API."
        />
      )}

      {data && (
        <div className="conn-grid">
          {cards.map((card) => {
            switch (card.channel) {
              case 'telegram':
                return <TelegramCard key={card.channel} model={card} link={telegram} />;
              case 'email':
                return (
                  <GmailCard
                    key={card.channel}
                    model={card}
                    notice={gmailReturn.notice}
                    onNoticeDismiss={gmailReturn.dismiss}
                  />
                );
              default:
                return <ChannelCard key={card.channel} model={card} />;
            }
          })}
        </div>
      )}
    </div>
  );
}
