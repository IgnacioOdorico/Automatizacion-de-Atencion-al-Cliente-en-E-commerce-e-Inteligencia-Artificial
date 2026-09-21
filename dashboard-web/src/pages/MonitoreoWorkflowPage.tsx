import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { monitoringApi } from '@/api/endpoints';
import { ActivityIcon } from '@/components/icons';
import { QueryView } from '@/components/QueryView';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { Select } from '@/components/ui/Select';
import { Skeleton } from '@/components/ui/Skeleton';
import { WorkflowCanvas, WorkflowCanvasSkeleton } from '@/components/workflow/WorkflowCanvas';
import { pickDefaultWorkflow, workflowStats } from '@/lib/executions';
import { layoutGraph } from '@/lib/workflowGraph';
import { buildOverlay } from '@/lib/workflowTrace';

/** La lista de workflows (con sus contadores de 24 h) se refresca sola. */
const WORKFLOWS_POLL_MS = 10_000;
/** El grafo casi no cambia: se pide una vez por workflow. */
const GRAPH_STALE_MS = 30_000;

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
 * Monitoreo > Workflow: el workflow real de n8n dibujado en el portal, para
 * explicar paso a paso qué hace el bot. Esta primera versión muestra el
 * diagrama con zoom y desplazamiento; el camino de cada ejecución se ilumina
 * encima (ver `overlay`).
 */
export function MonitoreoWorkflowPage() {
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
  const overlay = useMemo(() => (graph.data ? buildOverlay(graph.data, null) : null), [graph.data]);

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
                  <WorkflowCanvas
                    title={g.name}
                    layout={layout}
                    overlay={overlay}
                    selected={selectedNode}
                    onSelect={setSelectedNode}
                    resetKey={g.id}
                  />
                ) : null
              }
            </QueryView>
          </>
        )}
      </QueryView>
    </div>
  );
}
