import { useId, useMemo, useState } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';

import { monitoringApi } from '@/api/endpoints';
import { MessengerIcon, SearchIcon } from '@/components/icons';
import { ConversationList } from '@/components/monitoring/ConversationList';
import { ConversationThread } from '@/components/monitoring/ConversationThread';
import { QueryView } from '@/components/QueryView';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Select, type SelectOption } from '@/components/ui/Select';
import { Skeleton } from '@/components/ui/Skeleton';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { useNow } from '@/hooks/useNow';
import {
  conversationSearch,
  mergeConversationPages,
  parseConversationSearch,
  type ConversationRef,
} from '@/lib/conversations';
import { CHANNEL_LABELS } from '@/lib/format';
import type { Channel } from '@/types/api';
import type { ConversationSummary } from '@/types/monitoring';

/** La lista de hilos se refresca sola cada 5 s. */
const LIST_POLL_MS = 5000;
const SEARCH_DEBOUNCE_MS = 300;
const PAGE_SIZE = 30;
const SEARCH_MAX_LENGTH = 100;

const CHANNEL_OPTIONS: SelectOption[] = [
  { value: '', label: 'Todos los canales' },
  ...(['whatsapp', 'telegram', 'email'] as const).map((value) => ({
    value,
    label: CHANNEL_LABELS[value],
  })),
];

function ListSkeleton() {
  return (
    <div className="mon-convs" aria-hidden="true">
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} className="mon-conv mon-conv--skeleton">
          <Skeleton height={36} width={36} radius={11} />
          <div style={{ flex: 1 }}>
            <Skeleton height={13} width="52%" />
            <Skeleton height={12} width="86%" style={{ marginTop: 8 }} />
            <Skeleton height={11} width="40%" style={{ marginTop: 8 }} />
          </div>
        </div>
      ))}
    </div>
  );
}

interface MoreRows {
  /** Filtros con los que se pidió: si cambian, lo cargado a pedido ya no aplica. */
  key: string;
  items: ConversationSummary[];
  cursor: string | null;
  hasMore: boolean;
}

/**
 * Monitoreo > Conversaciones: lista de hilos (canal + usuario) a la izquierda y
 * el hilo abierto, estilo chat, a la derecha. El hilo abierto vive en la URL
 * (?canal=...&usuario=...). En móvil se ve un panel por vez.
 */
export function MonitoreoConversacionesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selected = useMemo(() => parseConversationSearch(searchParams.toString()), [searchParams]);

  const [text, setText] = useState('');
  const [channel, setChannel] = useState<Channel | ''>('');
  const term = useDebouncedValue(text, SEARCH_DEBOUNCE_MS).trim();
  const searchId = useId();
  const now = useNow(5000);

  const filterKey = `${term}|${channel}`;
  const filtersActive = term !== '' || channel !== '';

  const list = useQuery({
    queryKey: ['monitoring-conversations', term, channel],
    queryFn: () =>
      monitoringApi.conversations({
        q: term || undefined,
        channel: channel || undefined,
        limit: PAGE_SIZE,
      }),
    refetchInterval: LIST_POLL_MS,
    placeholderData: keepPreviousData,
  });

  const [moreState, setMoreState] = useState<MoreRows | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [moreError, setMoreError] = useState(false);
  const more = moreState && moreState.key === filterKey ? moreState : null;

  const rows = list.data ? mergeConversationPages(list.data.items, more?.items ?? []) : [];
  const hasMore = more ? more.hasMore : (list.data?.has_more ?? false);

  const loadMore = async () => {
    const cursor = more ? more.cursor : list.data?.next_before;
    if (!cursor) return;
    setLoadingMore(true);
    setMoreError(false);
    try {
      const page = await monitoringApi.conversations({
        q: term || undefined,
        channel: channel || undefined,
        limit: PAGE_SIZE,
        before: cursor,
      });
      setMoreState({
        key: filterKey,
        items: [...(more?.items ?? []), ...page.items],
        cursor: page.next_before,
        hasMore: page.has_more,
      });
    } catch {
      setMoreError(true);
    } finally {
      setLoadingMore(false);
    }
  };

  const open = (conversation: ConversationRef) =>
    setSearchParams(new URLSearchParams(conversationSearch(conversation.channel, conversation.userId)));
  const back = () => setSearchParams(new URLSearchParams());
  const clearFilters = () => {
    setText('');
    setChannel('');
  };

  return (
    <div className="mon-chats" data-view={selected ? 'thread' : 'list'}>
      <section className="mon-chats__list card" aria-label="Lista de conversaciones">
        <div className="mon-chats__filters">
          <div className="field">
            <label className="field__label sr-only" htmlFor={searchId}>
              Buscar conversaciones
            </label>
            <div className="mon-search">
              <SearchIcon width={16} height={16} aria-hidden="true" />
              <input
                id={searchId}
                type="search"
                className="field__input"
                placeholder="Buscar por mensaje, respuesta o usuario"
                maxLength={SEARCH_MAX_LENGTH}
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>
          </div>
          <Select
            label="Canal"
            value={channel}
            options={CHANNEL_OPTIONS}
            onChange={(e) => setChannel(e.target.value as Channel | '')}
          />
        </div>

        <div className="mon-chats__scroll">
          <QueryView
            query={list}
            loading={<ListSkeleton />}
            smallError
            isEmpty={(page) => page.items.length === 0}
            empty={
              filtersActive ? (
                <EmptyState
                  icon={<SearchIcon width={22} height={22} />}
                  title="Ninguna conversación coincide"
                  text="Probá con otras palabras u otro canal."
                  action={
                    <Button variant="ghost" onClick={clearFilters}>
                      Quitar filtros
                    </Button>
                  }
                />
              ) : (
                <EmptyState
                  icon={<MessengerIcon width={22} height={22} />}
                  title="El bot todavía no atendió mensajes"
                  text="Cuando llegue el primero por WhatsApp, Telegram o email lo vas a ver acá."
                />
              )
            }
          >
            {() => (
              <>
                <ConversationList rows={rows} selected={selected} nowMs={now} onSelect={open} />
                <div className="mon-more">
                  {moreError && (
                    <p className="field__error" role="alert">
                      No pudimos cargar más conversaciones. Reintentá.
                    </p>
                  )}
                  {hasMore && (
                    <Button variant="ghost" onClick={() => void loadMore()} loading={loadingMore}>
                      Cargar más conversaciones
                    </Button>
                  )}
                </div>
              </>
            )}
          </QueryView>
        </div>
      </section>

      <section className="mon-chat card" aria-label="Conversación abierta">
        {selected ? (
          <ConversationThread
            key={`${selected.channel}:${selected.userId}`}
            conversation={selected}
            onBack={back}
          />
        ) : (
          <div className="mon-chat__body">
            <EmptyState
              icon={<MessengerIcon width={24} height={24} />}
              title="Elegí una conversación"
              text="Vas a ver cada mensaje del cliente con la respuesta del bot, su intent y cuánto tardó."
            />
          </div>
        )}
      </section>
    </div>
  );
}
