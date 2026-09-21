import { StatusIcon } from '@/components/workflow/StatusIcon';
import { Badge } from '@/components/ui/Badge';
import { executionModeLabel, executionStatusMeta } from '@/lib/executions';
import { formatDateTimeSeconds, formatEventClock, formatMs, formatRelative } from '@/lib/format';
import type { ExecutionSummary } from '@/types/monitoring';

interface ExecutionHeaderProps {
  execution: ExecutionSummary;
  /** Reloj con el que se calcula la hora relativa. */
  nowMs: number;
}

/** La ejecución que se está viendo en el diagrama: estado, cuándo pasó, cuánto tardó y el error si lo hubo. */
export function ExecutionHeader({ execution, nowMs }: ExecutionHeaderProps) {
  const status = executionStatusMeta(execution.status);
  return (
    <div className="wf-exec">
      <div className="wf-exec__row">
        <strong className="wf-exec__title">Ejecución #{execution.id}</strong>
        <Badge tone={status.tone}>
          <StatusIcon name={status.icon} />
          {status.label}
        </Badge>
        <time dateTime={execution.started_at} title={formatDateTimeSeconds(execution.started_at)}>
          {formatRelative(execution.started_at, nowMs)} · {formatEventClock(execution.started_at, nowMs)}
        </time>
        <span>Duración {formatMs(execution.duration_ms)}</span>
        <span>{executionModeLabel(execution.mode)}</span>
      </div>
      {execution.error_message && <p className="wf-exec__error">{execution.error_message}</p>}
    </div>
  );
}
