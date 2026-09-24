import { useQuery } from '@tanstack/react-query';

import { metricsApi } from '@/api/endpoints';
import { QueryView } from '@/components/QueryView';
import { BotIcon } from '@/components/icons';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { StatCards } from '@/components/metrics/StatCards';
import { DonutChart } from '@/components/metrics/DonutChart';
import { BarChart } from '@/components/metrics/BarChart';
import { StackedAreaChart } from '@/components/metrics/StackedAreaChart';
import { INTENTS, intentMeta } from '@/lib/domain';
import { CHANNEL_LABELS, formatRelative, formatTmr } from '@/lib/format';
import { chatbotDataSourceIgnored, chatbotDataSourceParam, chatbotIsEmpty } from '@/lib/metricsFilters';
import { channelColor, intentColor } from '@/lib/chartColors';
import { useNow } from '@/hooks/useNow';
import type { ChatbotChannelDailyPoint, ChatbotMetrics } from '@/types/metrics';

const POLL_MS = 10_000;
const CHANNEL_KEYS = ['whatsapp', 'telegram', 'email'] as const;

function ChatbotSkeleton() {
  return (
    <div aria-hidden="true">
      <div className="stat-grid">
        {Array.from({ length: 2 }, (_, i) => (
          <div key={i} className="card stat-card stat-card--skeleton">
            <Skeleton height={11} width="46%" />
            <Skeleton height={26} width="38%" style={{ marginTop: 10 }} />
          </div>
        ))}
      </div>
      <div className="metrics-charts">
        <div className="metrics-chart-card chart-skeleton" />
        <div className="metrics-chart-card chart-skeleton" />
        <div className="metrics-chart-card metrics-chart-card--wide chart-skeleton" />
      </div>
    </div>
  );
}

/** Los 3 canales de `by_channel_daily`, como mapa clave→valor (lo que pide StackedAreaChart). */
function channelValues(d: ChatbotChannelDailyPoint): Record<string, number> {
  return { whatsapp: d.whatsapp, telegram: d.telegram, email: d.email };
}

function buildStatCards(data: ChatbotMetrics) {
  return [
    { id: 'tmr', label: 'TMR promedio', value: formatTmr(data.avg_tmr_seconds), hint: 'Mensaje recibido → bot responde.' },
    { id: 'total', label: 'Interacciones totales', value: data.total_interactions.toLocaleString('es-AR') },
  ];
}

interface ChatbotMetricsSectionProps {
  hours?: number;
  dataSource: string;
  reducedMotion: boolean;
}

/** Bloque "Chatbot": reemplazo en vivo de TMR, distribución de intents e interacciones por día y canal. */
export function ChatbotMetricsSection({ hours, dataSource, reducedMotion }: ChatbotMetricsSectionProps) {
  const now = useNow(1000);
  const ignored = chatbotDataSourceIgnored(dataSource);
  const query = useQuery({
    queryKey: ['metrics-chatbot', hours, dataSource],
    queryFn: () => metricsApi.chatbot({ hours, data_source: chatbotDataSourceParam(dataSource) }),
    refetchInterval: POLL_MS,
  });

  return (
    <section className="card metrics-block" aria-labelledby="metrics-chatbot-title">
      <div className="metrics-block__head">
        <h2 className="metrics-block__title" id="metrics-chatbot-title">
          Chatbot
        </h2>
        {query.dataUpdatedAt > 0 && (
          <span className="metrics-updated">Actualizado {formatRelative(new Date(query.dataUpdatedAt).toISOString(), now)}</span>
        )}
      </div>

      {ignored && (
        <p className="metrics-filters__note" role="status">
          "Carga manual" no existe como origen de las interacciones del chatbot: este bloque muestra todos los
          orígenes.
        </p>
      )}

      <QueryView
        query={query}
        loading={<ChatbotSkeleton />}
        isEmpty={chatbotIsEmpty}
        empty={
          <EmptyState
            icon={<BotIcon width={24} height={24} />}
            title="Todavía no hay interacciones para este período"
            text="Probá una ventana más amplia o esperá a que lleguen mensajes nuevos: el bloque se actualiza solo."
          />
        }
      >
        {(data) => (
          <>
            <StatCards cards={buildStatCards(data)} />
            <div className="metrics-charts">
              <div className="metrics-chart-card">
                <h3 className="metrics-chart-card__title">TMR promedio por intent</h3>
                <BarChart
                  title="TMR promedio por intent"
                  entries={INTENTS.map((intent) => ({
                    key: intent,
                    label: intentMeta(intent).label,
                    value: data.by_intent[intent]?.avg_tmr_seconds ?? null,
                    color: intentColor(intent),
                    count: data.by_intent[intent]?.count ?? 0,
                  }))}
                  reducedMotion={reducedMotion}
                />
              </div>
              <div className="metrics-chart-card">
                <h3 className="metrics-chart-card__title">Distribución de intents</h3>
                <DonutChart
                  title="Distribución de intents"
                  entries={INTENTS.map((intent) => ({
                    key: intent,
                    label: intentMeta(intent).label,
                    value: data.by_intent[intent]?.count ?? 0,
                    color: intentColor(intent),
                  }))}
                  centerValue={data.total_interactions.toLocaleString('es-AR')}
                  centerLabel="interacciones"
                  reducedMotion={reducedMotion}
                />
              </div>
              <div className="metrics-chart-card metrics-chart-card--wide">
                <h3 className="metrics-chart-card__title">Interacciones por día y canal</h3>
                <StackedAreaChart
                  title="Interacciones por día, por canal"
                  rows={data.by_channel_daily.map((d) => ({ date: d.date, values: channelValues(d) }))}
                  series={CHANNEL_KEYS.map((key) => ({
                    key,
                    label: CHANNEL_LABELS[key],
                    color: channelColor(key),
                  }))}
                  reducedMotion={reducedMotion}
                />
              </div>
            </div>
          </>
        )}
      </QueryView>
    </section>
  );
}
