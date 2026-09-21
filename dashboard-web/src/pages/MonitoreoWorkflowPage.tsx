import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { monitoringApi } from '@/api/endpoints';
import { ActivityIcon } from '@/components/icons';
import { QueryView } from '@/components/QueryView';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Select } from '@/components/ui/Select';
import { Skeleton } from '@/components/ui/Skeleton';
import { ExecutionHeader } from '@/components/workflow/ExecutionHeader';
import { PlaybackBar, PlaybackCaptionPill } from '@/components/workflow/PlaybackBar';
import { WorkflowCanvas, WorkflowCanvasSkeleton } from '@/components/workflow/WorkflowCanvas';
import { useNow } from '@/hooks/useNow';
import { usePlayback } from '@/hooks/usePlayback';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { pickDefaultWorkflow, workflowStats } from '@/lib/executions';
import { playbackCaption } from '@/lib/playback';
import { layoutGraph } from '@/lib/workflowGraph';
import { buildOverlay, effectivePath, traceNoticeMessages, traceNotes } from '@/lib/workflowTrace';

/** La lista de workflows (con sus contadores de 24 h) se refresca sola. */
const WORKFLOWS_POLL_MS = 10_000;
/** El grafo casi no cambia: se pide una vez por workflow. */
const GRAPH_STALE_MS = 30_000;
/** Las ejecuciones se refrescan solas. */
const EXECUTIONS_POLL_MS = 10_000;
const EXECUTIONS_LIMIT = 20;
/** Una ejecución que todavía corre se vuelve a pedir seguido, hasta que termine. */
const RUNNING_POLL_MS = 2000;

const LIVE_STATUSES = new Set(['running', 'new', 'waiting']);

function PageSkeleton() {
  return (
    <div aria-hidden="true">
      <Skeleton height={44} width={320} radius={10} style={{ marginBottom: 16 }} />
      <WorkflowCanvasSkeleton />
    </div>
  );
}

/** Por qué no hay nada que dibujar: n8n no responde, o todavía no tiene workflows. */
function NoWorkflows({ available }: { available: boolean }) {
  return available ? (
    <EmptyState
      icon={<ActivityIcon width={24} height={24} />}
      title="Todavía no hay workflows en n8n"
      text="Importá el workflow del pipeline de órdenes (y el del chatbot) en n8n y activalo: cuando esté, lo vas a ver dibujado acá con el camino de cada ejecución."
    />
  ) : (
    <EmptyState
      icon={<ActivityIcon width={24} height={24} />}
      title="No pudimos leer los workflows de n8n"
      text="Para ver el diagrama, n8n tiene que estar en línea y con el workflow importado. Revisá que n8n esté corriendo y volvé a esta pestaña."
    />
  );
}

/**
 * Monitoreo > Workflow: el workflow real de n8n dibujado en el portal, con el
 * camino de una ejecución iluminado nodo por nodo, para explicar paso a paso
 * qué hace el bot.
 */
export function MonitoreoWorkflowPage() {
  const now = useNow(5000);
  const reducedMotion = usePrefersReducedMotion();

  const workflows = useQuery({
    queryKey: ['monitoring-workflows'],
    queryFn: () => monitoringApi.workflows(),
    refetchInterval: WORKFLOWS_POLL_MS,
  });

  const [chosenId, setChosenId] = useState<string | null>(null);
  const items = useMemo(() => workflows.data?.items ?? [], [workflows.data]);
  const workflowId =
    chosenId !== null && items.some((w) => w.id === chosenId) ? chosenId : pickDefaultWorkflow(items);
  const workflow = items.find((w) => w.id === workflowId) ?? null;

  const graph = useQuery({
    queryKey: ['monitoring-graph', workflowId],
    queryFn: () => monitoringApi.workflowGraph(workflowId as string),
    enabled: workflowId !== null,
    staleTime: GRAPH_STALE_MS,
  });
  const layout = useMemo(() => (graph.data ? layoutGraph(graph.data) : null), [graph.data]);

  // Ejecuciones del workflow: por defecto se ve la más reciente.
  const executions = useQuery({
    queryKey: ['monitoring-executions', workflowId],
    queryFn: () => monitoringApi.executions({ workflowId: workflowId as string, limit: EXECUTIONS_LIMIT }),
    enabled: workflowId !== null,
    refetchInterval: EXECUTIONS_POLL_MS,
  });
  const executionItems = useMemo(() => executions.data?.items ?? [], [executions.data]);
  const executionId = executionItems[0]?.id ?? null;

  const detail = useQuery({
    queryKey: ['monitoring-execution', executionId],
    queryFn: () => monitoringApi.execution(executionId as number),
    enabled: executionId !== null,
    refetchInterval: (query) =>
      LIVE_STATUSES.has(query.state.data?.execution.status ?? '') ? RUNNING_POLL_MS : false,
  });
  const detailData = detail.data ?? null;

  // Reproducción del camino.
  const path = useMemo(() => effectivePath(detailData), [detailData]);
  const [speed, setSpeed] = useState(1);
  const [camera, setCamera] = useState(true);
  const playback = usePlayback({ executionKey: executionId, total: path.length, speed, reducedMotion });

  const overlay = useMemo(
    () => (graph.data ? buildOverlay(graph.data, detailData, { revealed: playback.reveal }) : null),
    [graph.data, detailData, playback.reveal],
  );
  const notices = useMemo(
    () => (graph.data ? traceNoticeMessages(traceNotes(graph.data, detailData)) : []),
    [graph.data, detailData],
  );
  const caption = playbackCaption(playback.state, path);
  const cameraTarget = camera && playback.state.mode !== 'idle' ? (overlay?.current ?? null) : null;

  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  useEffect(() => setSelectedNode(null), [workflowId]);

  return (
    <div className="wf">
      <QueryView
        query={workflows}
        loading={<PageSkeleton />}
        isEmpty={(data) => !data.available || data.items.length === 0}
        empty={<NoWorkflows available={workflows.data?.available ?? false} />}
      >
        {() => (
          <>
            <div className="wf-top">
              <Select
                label="Workflow"
                value={workflowId ?? ''}
                options={items.map((w) => ({ value: w.id, label: w.name }))}
                onChange={(e) => setChosenId(e.target.value)}
              />
              {workflow && (
                <p className="wf-top__stats">
                  <Badge tone={workflow.active ? 'success' : 'neutral'}>
                    {workflow.active ? 'Activo' : 'Inactivo'}
                  </Badge>
                  <span>{workflowStats(workflow)}</span>
                </p>
              )}
            </div>

            {detailData ? (
              <ExecutionHeader execution={detailData.execution} nowMs={now} />
            ) : executions.isError ? (
              <p className="wf-notice" role="alert">
                No pudimos leer las ejecuciones de este workflow.
                <Button variant="ghost" onClick={() => void executions.refetch()}>
                  Reintentar
                </Button>
              </p>
            ) : executions.data && executionItems.length === 0 ? (
              <p className="wf-notice">
                Todavía no hay ejecuciones de este workflow. Cuando llegue una, vas a ver por dónde pasó.
              </p>
            ) : null}

            {executionId !== null && detail.isPending && (
              <p className="wf-notice" role="status">
                Cargando el recorrido de la ejecución…
              </p>
            )}
            {detail.isError && (
              <p className="wf-notice" role="alert">
                No pudimos cargar el detalle de esta ejecución.
                <Button variant="ghost" onClick={() => void detail.refetch()}>
                  Reintentar
                </Button>
              </p>
            )}
            <QueryView
              query={graph}
              loading={<WorkflowCanvasSkeleton />}
              isEmpty={(g) => g.nodes.length === 0}
              empty={
                <EmptyState
                  icon={<ActivityIcon width={24} height={24} />}
                  title="Este workflow todavía no tiene nodos"
                  text="Agregá nodos en n8n y vas a verlos dibujados acá."
                />
              }
            >
              {(g) =>
                layout && overlay ? (
                  <>
                    <WorkflowCanvas
                      title={g.name}
                      layout={layout}
                      overlay={overlay}
                      selected={selectedNode}
                      onSelect={setSelectedNode}
                      resetKey={g.id}
                      camera={cameraTarget}
                      dock={caption ? <PlaybackCaptionPill caption={caption} /> : null}
                    />
                    <PlaybackBar
                      state={playback.state}
                      canPlay={path.length > 1}
                      speed={speed}
                      onSpeed={setSpeed}
                      camera={camera}
                      onCamera={setCamera}
                      reducedMotion={reducedMotion}
                      onPlay={playback.play}
                      onPause={playback.pause}
                      onRestart={playback.restart}
                      onShowAll={playback.showAll}
                    />
                  </>
                ) : null
              }
            </QueryView>

            {notices.length > 0 && (
              <ul className="wf-notices">
                {notices.map((notice) => (
                  <li key={notice.id}>{notice.text}</li>
                ))}
              </ul>
            )}
          </>
        )}
      </QueryView>
    </div>
  );
}
