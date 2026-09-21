import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { ChannelCard } from '@/components/connections/ChannelCard';
import { PlugIcon } from '@/components/icons';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { buildChannelCards } from '@/lib/connections';
import { friendlyApiError } from '@/lib/messages';

const CHANNEL_DESCRIPTIONS = {
  whatsapp: 'Atención por WhatsApp Business. Meta aprueba cada número antes de operar.',
  telegram: 'Vinculá tu chat de Telegram con un código de 6 dígitos.',
  email: 'Autorizá tu cuenta de Gmail para responder consultas por correo.',
} as const;

/**
 * Conexiones (GET /connections): una card por canal con su estado real.
 * En BD el canal de correo es `email`; la UI lo muestra como "Gmail".
 */
export function ConexionesPage() {
  const { data, isPending, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['connections'],
    queryFn: dashboardApi.connections,
  });

  const cards = useMemo(() => buildChannelCards(data?.items), [data]);

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
          {cards.map((card) => (
            <ChannelCard
              key={card.channel}
              model={card}
              description={CHANNEL_DESCRIPTIONS[card.channel]}
            />
          ))}
        </div>
      )}
    </div>
  );
}
