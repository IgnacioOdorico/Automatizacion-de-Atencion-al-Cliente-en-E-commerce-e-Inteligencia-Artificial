import { DATA_SOURCE_OPTIONS, HOURS_OPTIONS } from '@/lib/metricsFilters';
import { Select } from '@/components/ui/Select';

interface MetricsFiltersProps {
  hours: string;
  onHoursChange: (value: string) => void;
  dataSource: string;
  onDataSourceChange: (value: string) => void;
  updatedLabel?: string;
}

/**
 * Filtros compartidos por los dos bloques (Pedidos y Chatbot): ventana de
 * tiempo y origen del dato. El dominio de `data_source` difiere entre los dos
 * endpoints (ver docs/API_METRICAS.md) — con un solo selector, "Carga manual"
 * sigue funcionando en Pedidos y se ignora en Chatbot (avisado en ese bloque,
 * no acá: el aviso depende de si el bloque de Chatbot está visible).
 */
export function MetricsFilters({ hours, onHoursChange, dataSource, onDataSourceChange, updatedLabel }: MetricsFiltersProps) {
  return (
    <div className="metrics-filters">
      <Select
        label="Ventana de tiempo"
        value={hours}
        options={HOURS_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
        onChange={(e) => onHoursChange(e.target.value)}
      />
      <Select
        label="Origen del dato"
        value={dataSource}
        options={DATA_SOURCE_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
        onChange={(e) => onDataSourceChange(e.target.value)}
      />
      {updatedLabel && <span className="metrics-updated">{updatedLabel}</span>}
    </div>
  );
}
