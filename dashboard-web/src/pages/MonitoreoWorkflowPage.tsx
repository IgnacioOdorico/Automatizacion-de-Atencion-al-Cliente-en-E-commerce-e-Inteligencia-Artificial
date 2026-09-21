import { useEffect, useMemo, useRef, useState } from 'react';
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
import { ExecutionList } from '@/components/workflow/ExecutionList';
import { NodeDetail } from '@/components/workflow/NodeDetail';
import { PlaybackBar, PlaybackCaptionPill } from '@/components/workflow/PlaybackBar';
import { ThesisMetricsCard } from '@/components/workflow/ThesisMetricsCard';
import { WorkflowLegend } from '@/components/workflow/WorkflowLegend';
import { WorkflowCanvas, WorkflowCanvasSkeleton } from '@/components/workflow/WorkflowCanvas';
import { useFreshRows } from '@/hooks/useFreshRows';
import { useNow } from '@/hooks/useNow';
import { usePlayback } from '@/hooks/usePlayback';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { mergeExecutionPages, pickDefaultWorkflow, workflowStats } from '@/lib/executions';
import { followStep } from '@/lib/followLive';
import { playbackCaption } from '@/lib/playback';
import { layoutGraph } from '@/lib/workflowGraph';
import type { ExecutionSummary } from '@/types/monitoring';
import { buildOverlay, effectivePath, traceNoticeMessages, traceNotes } from '@/lib/workflowTrace';

/** La lista de workflows (con sus contadores de 24 h) se refresca sola. */
const WORKFLOWS_POLL_MS = 10_000;
/** El grafo casi no cambia: se pide una vez por workflow. */
const GRAPH_STALE_MS = 30_000;
/** Con "Seguir en vivo" las ejecuciones se consultan seguido; sin él, más despacio. */
const FOLLOW_POLL_MS = 4000;
const EXECUTIONS_POLL_MS = 10_000;
const EXECUTIONS_LIMIT = 20;
/** Una ejecución que todavía corre se vuelve a pedir seguido, hasta que termine. */
const RUNNING_POLL_MS = 2000;

const LIVE_STATUSES = new Set(['running', 'new', 'waiting']);

/** Un id ligado a la lista (workflow + filtro) en la que se eligió: al cambiar de lista deja de aplicar. */
interface ScopedId {
  scope: string;
  id: number | null;
}

interface MoreRows {
  key: string;
  items: ExecutionSummary[];
  cursor: number | null;
  hasMore: boolean;
}

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

  // Ejecuciones del workflow. Todo lo que depende de "qué lista se mira" (workflow + filtro) se
  // guarda con esa clave: al cambiarla, lo elegido y lo cargado a pedido dejan de aplicar solos.
  const [statusFilter, setStatusFilter] = useState('');
  const [follow, setFollow] = useState(true);
  const scopeKey = `${workflowId ?? ''}|${statusFilter}`;

  const executions = useQuery({
    queryKey: ['monitoring-executions', workflowId, statusFilter],
    queryFn: () =>
      monitoringApi.executions({
        workflowId: workflowId as string,
        status: statusFilter || undefined,
        limit: EXECUTIONS_LIMIT,
      }),
    enabled: workflowId !== null,
    refetchInterval: follow ? FOLLOW_POLL_MS : EXECUTIONS_POLL_MS,
  });
  const executionItems = useMemo(() => executions.data?.items ?? [], [executions.data]);

  const [selection, setSelection] = useState<ScopedId>({ scope: '', id: null });
  const [autoplay, setAutoplay] = useState<ScopedId>({ scope: '', id: null });
  const selectedExecution = selection.scope === scopeKey ? selection.id : null;
  const executionId = selectedExecution ?? executionItems[0]?.id ?? null;

  // Seguir en vivo: lo más nuevo que ya se vio; si llega una ejecución más nueva se elige sola y se reproduce.
  const seen = useRef<ScopedId>({ scope: '', id: null });
  useEffect(() => {
    if (!executions.data) return;
    const newest = executionItems[0]?.id ?? null;
    const previous = seen.current.scope === scopeKey ? seen.current.id : null;
    const step = followStep(previous, newest);
    seen.current = { scope: scopeKey, id: step.seenId };
    if (step.selectId === null) return;
    const pick = step.selectId;
    setSelection((prev) =>
      follow || prev.scope !== scopeKey || prev.id === null ? { scope: scopeKey, id: pick } : prev,
    );
    if (step.isNew && follow) setAutoplay({ scope: scopeKey, id: pick });
  }, [executions.data, executionItems, follow, scopeKey]);

  const chooseExecution = (id: number) => {
    setFollow(false);
    setAutoplay({ scope: scopeKey, id: null });
    setSelection({ scope: scopeKey, id });
  };

  // "Cargar ejecuciones anteriores": se suma a la primera página, que se sigue refrescando sola.
  const [moreState, setMoreState] = useState<MoreRows | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [moreError, setMoreError] = useState(false);
  const more = moreState && moreState.key === scopeKey ? moreState : null;
  const listItems = useMemo(() => mergeExecutionPages(executionItems, more?.items ?? []), [executionItems, more]);
  const hasMore = more ? more.hasMore : (executions.data?.has_more ?? false);
  const fresh = useFreshRows(scopeKey, executions.data ? executionItems.map((e) => e.id) : undefined);

  const loadMore = async () => {
    const cursor = more ? more.cursor : (executions.data?.next_before ?? null);
    if (cursor === null || workflowId === null) return;
    setLoadingMore(true);
    setMoreError(false);
    try {
      const page = await monitoringApi.executions({
        workflowId,
        status: statusFilter || undefined,
        limit: EXECUTIONS_LIMIT,
        before: cursor,
      });
      setMoreState({
        key: scopeKey,
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
  // Una ejecución que llegó "en vivo" arranca reproduciendo su camino apenas se conoce.
  useEffect(() => {
    const armed = autoplay.scope === scopeKey && autoplay.id !== null;
    if (armed && detailData?.execution.id === autoplay.id && path.length > 1) {
      playback.restart();
      setAutoplay({ scope: scopeKey, id: null });
    }
    // `playback.restart` cambia solo con el movimiento reducido: no hace falta re-disparar por eso.
  }, [autoplay, detailData, path.length, scopeKey]);

  // El panel de un nodo muestra su resultado final aunque la reproducción todavía no haya llegado.
  const finalOverlay = useMemo(
    () => (graph.data ? buildOverlay(graph.data, detailData) : null),
    [graph.data, detailData],
  );
  const caption = playbackCaption(playback.state, path);
  const cameraTarget = camera && playback.state.mode !== 'idle' ? (overlay?.current ?? null) : null;

  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  useEffect(() => setSelectedNode(null), [workflowId]);
  const stageRef = useRef<HTMLDivElement>(null);
  const detailRef = useRef<HTMLElement>(null);
  const restoreFocusTo = useRef<string | null>(null);

  // Al abrir el detalle el foco pasa al panel; al cerrarlo vuelve al nodo (teclado y lectores de pantalla).
  useEffect(() => {
    if (selectedNode !== null) {
      detailRef.current?.focus();
    } else if (restoreFocusTo.current !== null) {
      const name = restoreFocusTo.current;
      restoreFocusTo.current = null;
      const cards = Array.from(stageRef.current?.querySelectorAll<SVGGElement>('.wf-node') ?? []);
      cards.find((n) => n.getAttribute('data-node') === name)?.focus();
    }
  }, [selectedNode]);
  const closeDetail = () => {
    restoreFocusTo.current = selectedNode;
    setSelectedNode(null);
  };
  const graphNode = graph.data?.nodes.find((n) => n.name === selectedNode) ?? null;

  return (
    <div className="wf">
      <QueryView
        query={workflows}
        loading={<PageSkeleton />}
        isEmpty={(data) => !data.available || data.items.length === 0}
        empty={
          <>
            <NoWorkflows available={workflows.data?.available ?? false} />
            <div className="wf-below">
              <ThesisMetricsCard />
            </div>
          </>
        }
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
              <button
                type="button"
                role="switch"
                aria-checked={follow}
                className="wf-follow"
                onClick={() => setFollow((on) => !on)}
                title="Cuando llega una ejecución nueva, se elige sola y se reproduce su camino"
              >
                <span className="wf-follow__dot" aria-hidden="true" />
                Seguir en vivo
              </button>
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
                    <div className="wf-stage" ref={stageRef}>
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
                      {selectedNode !== null && graphNode && (
                        <NodeDetail
                          ref={detailRef}
                          name={graphNode.name}
                          shortType={graphNode.short_type}
                          disabled={graphNode.disabled}
                          overlay={finalOverlay?.nodes.get(graphNode.name) ?? { visual: 'plain', trace: null }}
                          execution={detailData === null ? 'none' : finalOverlay?.hasTrace ? 'trace' : 'no-trace'}
                          onClose={closeDetail}
                        />
                      )}
                    </div>
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
                    <WorkflowLegend />
                  </>
                ) : null
              }
            </QueryView>

            <div className="wf-below">
              <ExecutionList
                items={listItems}
                selectedId={executionId}
                onSelect={chooseExecution}
                fresh={fresh}
                nowMs={now}
                status={statusFilter}
                onStatusChange={setStatusFilter}
                hasMore={hasMore}
                onLoadMore={() => void loadMore()}
                loadingMore={loadingMore}
                moreError={moreError}
              />
              <ThesisMetricsCard />
            </div>

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
