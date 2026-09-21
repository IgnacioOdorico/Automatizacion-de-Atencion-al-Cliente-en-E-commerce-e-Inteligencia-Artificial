import { useQuery } from '@tanstack/react-query';

import { authApi } from '@/api/endpoints';
import { CHANNEL_ICONS } from '@/components/channelIcons';
import { QueryView } from '@/components/QueryView';
import { MessengerIcon } from '@/components/icons';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  CHANNEL_LABELS,
  CONNECTION_STATUS,
  formatDate,
  initials,
} from '@/lib/format';

function ProfileSkeleton() {
  return (
    <div className="grid grid--profile" aria-hidden="true">
      <div className="card profile-card">
        <div className="profile-card__top">
          <Skeleton height={52} width={52} radius={14} />
          <div style={{ flex: 1 }}>
            <Skeleton height={17} width="55%" />
            <Skeleton height={13} width="75%" style={{ marginTop: 8 }} />
          </div>
        </div>
        <div className="profile-card__meta">
          <Skeleton height={34} />
          <Skeleton height={34} />
        </div>
      </div>
      <div className="card profile-card">
        <Skeleton height={15} width={150} style={{ marginBottom: 16 }} />
        <div className="channel-list">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} height={60} radius={12} />
          ))}
        </div>
      </div>
    </div>
  );
}

/** Perfil: datos de la cuenta (GET /me) y estado de sus canales de atención. */
export function PerfilPage() {
  const query = useQuery({
    queryKey: ['me'],
    queryFn: authApi.me,
    staleTime: 60_000,
  });

  return (
    <div className="page">
      <header className="page__head">
        <h1>Perfil</h1>
        <p className="page__sub">
          Los datos de tu cuenta y el estado de los canales de atención.
        </p>
      </header>

      <QueryView query={query} loading={<ProfileSkeleton />}>
        {(me) => {
          const channels = me.connections ?? [];
          return (
            <div className="grid grid--profile">
              <div className="card profile-card">
                <div className="profile-card__top">
                  <div className="profile-card__avatar">{initials(me.business_name)}</div>
                  <div>
                    <div className="profile-card__name">{me.business_name}</div>
                    <div className="profile-card__email">{me.email}</div>
                  </div>
                </div>
                <div className="profile-card__meta">
                  <div>
                    <div className="profile-card__meta-label">Alta del portal</div>
                    <div className="profile-card__meta-value">{formatDate(me.created_at)}</div>
                  </div>
                  <div>
                    <div className="profile-card__meta-label">ID de cuenta</div>
                    <div className="profile-card__meta-value">#{me.id}</div>
                  </div>
                </div>
              </div>

              <div className="card profile-card">
                <h3 style={{ fontSize: 15, marginBottom: 16 }}>Canales de atención</h3>
                {channels.length === 0 ? (
                  <EmptyState
                    icon={<MessengerIcon width={20} height={20} />}
                    title="Sin canales conectados"
                    text="Los canales de contacto aparecen acá cuando los vincules."
                  />
                ) : (
                  <div className="channel-list">
                    {channels.map((connection) => {
                      const status = CONNECTION_STATUS[connection.status] ?? {
                        label: connection.status,
                        tone: 'neutral' as const,
                      };
                      const Icon = CHANNEL_ICONS[connection.channel] ?? MessengerIcon;
                      return (
                        <div key={connection.channel} className="channel-row">
                          <div className="channel-row__icon">
                            <Icon width={17} height={17} />
                          </div>
                          <div>
                            <div className="channel-row__name">
                              {CHANNEL_LABELS[connection.channel] ?? connection.channel}
                            </div>
                            {connection.external_reference && (
                              <div className="channel-row__ref">
                                {connection.external_reference}
                              </div>
                            )}
                          </div>
                          <Badge tone={status.tone}>{status.label}</Badge>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          );
        }}
      </QueryView>
    </div>
  );
}
