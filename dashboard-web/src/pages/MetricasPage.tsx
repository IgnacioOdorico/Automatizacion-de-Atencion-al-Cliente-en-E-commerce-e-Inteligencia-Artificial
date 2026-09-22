import { useState } from 'react';

import { ChatbotMetricsSection } from '@/components/metrics/ChatbotMetricsSection';
import { MetricsFilters } from '@/components/metrics/MetricsFilters';
import { OrdersMetricsSection } from '@/components/metrics/OrdersMetricsSection';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { ALL_HOURS_VALUE, hoursForOption } from '@/lib/metricsFilters';

/**
 * Métricas: reemplazo en vivo, dentro del portal, de los paneles de los dos
 * dashboards de Grafana (tesis-flujo1.json / tesis-flujo2.json). Distinta de
 * Monitoreo (feed de eventos y traza del workflow): esto son los KPIs y
 * gráficos agregados de negocio. No hay panel de "precisión/accuracy": es un
 * literal SQL fijo en Grafana, no una métrica calculada (decisión del
 * usuario, ver odd/tasks/dashboard-cliente-metricas.md).
 */
export function MetricasPage() {
  const [hoursValue, setHoursValue] = useState<string>(ALL_HOURS_VALUE);
  const [dataSource, setDataSource] = useState<string>('');
  const reducedMotion = usePrefersReducedMotion();
  const hours = hoursForOption(hoursValue);

  return (
    <div className="page">
      <header className="page__head">
        <h1>Métricas</h1>
        <p className="page__sub">
          Los mismos indicadores que hoy se ven en Grafana, en vivo y dentro del portal: tiempos de atención,
          distribución de estados e interacciones del chatbot.
        </p>
      </header>

      <MetricsFilters
        hours={hoursValue}
        onHoursChange={setHoursValue}
        dataSource={dataSource}
        onDataSourceChange={setDataSource}
      />

      <OrdersMetricsSection hours={hours} dataSource={dataSource} reducedMotion={reducedMotion} />
      <ChatbotMetricsSection hours={hours} dataSource={dataSource} reducedMotion={reducedMotion} />
    </div>
  );
}
