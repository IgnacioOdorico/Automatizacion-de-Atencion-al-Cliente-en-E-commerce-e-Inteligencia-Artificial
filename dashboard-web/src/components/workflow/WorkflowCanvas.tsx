import { memo, useEffect, useId, useMemo, useRef, type KeyboardEvent, type ReactNode } from 'react';

import { NODE_GLYPHS } from '@/components/workflow/nodeIcons';
import { Skeleton } from '@/components/ui/Skeleton';
import { useElementSize } from '@/hooks/useElementSize';
import { usePanZoom } from '@/hooks/usePanZoom';
import { nodeAriaLabel, nodeMetaLines } from '@/lib/nodeCard';
import { nodeKind } from '@/lib/nodeKinds';
import { preferredHeight, viewCss } from '@/lib/viewport';
import { CARD_H, CARD_W, wrapLabel, type EdgeShape, type GraphLayout, type NodeBox } from '@/lib/workflowGraph';
import type { EdgeOverlay, NodeOverlay, Overlay } from '@/lib/workflowTrace';

/** Ancho de línea del nombre en la tarjeta (en caracteres) y cuántas líneas entran. */
const NAME_CHARS = 20;
const NAME_LINES = 3;

interface WorkflowCanvasProps {
  /** Nombre del workflow: título accesible del diagrama. */
  title: string;
  layout: GraphLayout;
  overlay: Overlay;
  selected: string | null;
  onSelect: (name: string) => void;
  /** Cambia con el workflow: vuelve a ajustar a pantalla. */
  resetKey: string;
  /**
   * Nodo al que la cámara tiene que ir (el actual de la reproducción). Cuando
   * pasa de un nodo a `null`, la cámara vuelve a mostrar el diagrama entero.
   */
  camera?: string | null;
  /** Controles propios de la pantalla (reproducción), pegados abajo del lienzo. */
  dock?: ReactNode;
}

const PLAIN: NodeOverlay = { visual: 'plain', trace: null };
const IDLE_EDGE: EdgeOverlay = { visual: 'idle', flowing: false };

/** Marcadores (puntas de flecha): uno por estado, porque el color viene del CSS de cada uno. */
const ARROWS = ['idle', 'inactive', 'active'] as const;

function StatusGlyph({ visual }: { visual: NodeOverlay['visual'] }) {
  switch (visual) {
    case 'success':
      return <path d="m-4 0.5 3 3 5-6" />;
    case 'error':
      return <path d="m-3.5 -3.5 7 7m0 -7 -7 7" />;
    case 'running':
    case 'waiting':
      return <path d="M0 -4v4l3 2" />;
    default:
      return <path d="M-3.5 0h7" />;
  }
}

/** Nodos que se dibujan apagados: no corrieron, no figuran en la traza o la reproducción todavía no llegó. */
const DIM_VISUALS = new Set<NodeOverlay['visual']>(['skipped', 'canceled', 'missing', 'pending']);
const BADGE_VISUALS = new Set<NodeOverlay['visual']>(['success', 'error', 'running', 'waiting', 'canceled']);

interface NodeProps {
  box: NodeBox;
  overlay: NodeOverlay;
  selected: boolean;
  current: boolean;
  clipId: string;
  onSelect: (name: string) => void;
}

const DiagramNode = memo(function DiagramNode({ box, overlay, selected, current, clipId, onSelect }: NodeProps) {
  const kind = nodeKind(box.shortType);
  const meta = nodeMetaLines(overlay);
  const lines = wrapLabel(box.name, NAME_CHARS, box.disabled ? NAME_LINES - 1 : NAME_LINES);

  const classes = ['wf-node', `wf-node--${overlay.visual}`];
  if (selected) classes.push('wf-node--selected');
  if (current) classes.push('wf-node--current');
  if (box.disabled) classes.push('wf-node--disabled');
  if (box.disabled || DIM_VISUALS.has(overlay.visual)) classes.push('wf-node--dim');

  const activate = (event: KeyboardEvent<SVGGElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(box.name);
    }
  };

  return (
    <g
      className={classes.join(' ')}
      transform={`translate(${box.x} ${box.y})`}
      role="button"
      tabIndex={0}
      aria-label={nodeAriaLabel(box.name, kind.label, box.disabled, overlay)}
      aria-pressed={selected}
      data-node={box.name}
      onClick={() => onSelect(box.name)}
      onKeyDown={activate}
    >
      <title>{box.name}</title>
      <rect className="wf-node__card" width={box.w} height={box.h} rx={14} />
      <rect className="wf-node__iconbg" x={10} y={10} width={30} height={30} rx={8} />
      <g
        className="wf-node__glyph"
        transform="translate(15 15) scale(0.8333)"
        fill="none"
        strokeWidth={1.9}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {NODE_GLYPHS[kind.icon]}
      </g>

      {meta.map((line, i) => (
        <text key={i} className={`wf-node__meta wf-node__meta--${i}`} x={box.w - 12} y={i === 0 ? 26 : 41} textAnchor="end">
          {line}
        </text>
      ))}

      <g clipPath={`url(#${clipId})`}>
        <text className="wf-node__name" x={12} y={62}>
          {lines.map((line, i) => (
            <tspan key={i} x={12} dy={i === 0 ? 0 : 15}>
              {line}
            </tspan>
          ))}
        </text>
      </g>

      {box.disabled && (
        <text className="wf-node__tag" x={12} y={box.h - 9}>
          Deshabilitado
        </text>
      )}

      {BADGE_VISUALS.has(overlay.visual) && (
        <g className="wf-node__badge" transform={`translate(${box.w - 4} 4)`} aria-hidden="true">
          <circle r={10} />
          <g fill="none" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <StatusGlyph visual={overlay.visual} />
          </g>
        </g>
      )}
    </g>
  );
});

/** Rótulo de rama sobre la conexión ("Sí", "No", "Salida 2"). */
function EdgeLabel({ edge, overlay }: { edge: EdgeShape; overlay: EdgeOverlay }) {
  const text = edge.label ?? '';
  const width = Math.max(28, text.length * 6.6 + 14);
  return (
    <g className={`wf-elabel wf-elabel--${overlay.visual}`} transform={`translate(${edge.labelX} ${edge.labelY})`}>
      <rect x={-width / 2} y={-9} width={width} height={18} rx={9} />
      <text textAnchor="middle" dominantBaseline="central">
        {text}
      </text>
    </g>
  );
}

function ZoomIcon({ children }: { children: ReactNode }) {
  return (
    <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {children}
    </svg>
  );
}

/**
 * El diagrama del workflow en SVG propio, con pan y zoom. Cada nodo es un
 * botón enfocable (Tab, Enter/Espacio abre su detalle); las conexiones del
 * camino recorrido se iluminan según `overlay`. Todo texto (nombres de nodos
 * incluidos) se dibuja como texto de React: nunca como HTML.
 */
export function WorkflowCanvas({ title, layout, overlay, selected, onSelect, resetKey, camera = null, dock }: WorkflowCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const size = useElementSize(containerRef);
  const { view, dragging, animating, fit, focusOn, zoomIn, zoomOut, handlers } = usePanZoom({
    containerRef,
    bounds: layout.bounds,
    size,
    resetKey,
  });

  // Cámara: sigue al nodo actual de la reproducción y, al terminar, vuelve a mostrar todo.
  const boxes = useMemo(() => new Map(layout.nodes.map((n) => [n.name, n])), [layout.nodes]);
  const lastCamera = useRef<string | null>(null);
  useEffect(() => {
    const previous = lastCamera.current;
    lastCamera.current = camera;
    if (camera !== null) {
      const box = boxes.get(camera);
      if (box) focusOn(box);
    } else if (previous !== null) {
      fit();
    }
    // Solo reacciona a que cambie el nodo de la cámara.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [camera]);

  // Alto del lienzo según lo que mide el dibujo, para no dejar aire de sobra en diagramas chatos.
  const height = useMemo(() => preferredHeight(layout.bounds, size.width), [layout.bounds, size.width]);

  const uid = useId().replace(/[^A-Za-z0-9_-]/g, '');
  const titleId = `wf-title-${uid}`;
  const descId = `wf-desc-${uid}`;
  const helpId = `wf-help-${uid}`;
  const clipId = `wf-clip-${uid}`;
  const arrowId = (kind: string) => `wf-arrow-${kind}-${uid}`;

  // Las conexiones iluminadas van al final para quedar por encima de las apagadas.
  const edges = useMemo(() => {
    const rank = (e: EdgeShape) => (overlay.edges.get(e.key)?.visual === 'active' ? 1 : 0);
    return [...layout.edges].sort((a, b) => rank(a) - rank(b));
  }, [layout.edges, overlay.edges]);

  const labelled = useMemo(() => edges.filter((e) => e.label !== null), [edges]);

  const nodeCount = layout.nodes.length;
  const edgeCount = layout.edges.length;

  return (
    <div
      ref={containerRef}
      className={`wf-canvas${dragging ? ' wf-canvas--dragging' : ''}`}
      style={height === null ? undefined : { height }}
      role="region"
      aria-label={`Diagrama de ${title}`}
      aria-describedby={helpId}
      tabIndex={0}
      {...handlers}
    >
      <p id={helpId} className="sr-only">
        Diagrama interactivo. Con el diagrama enfocado, las flechas lo mueven, más y menos acercan y alejan y cero lo
        ajusta a la pantalla. Con Tab recorrés los nodos y con Enter abrís su detalle.
      </p>

      <svg className="wf-svg" width="100%" height="100%" role="group" aria-labelledby={titleId} aria-describedby={descId}>
        <title id={titleId}>{title}</title>
        <desc id={descId}>{`Diagrama del workflow con ${nodeCount} nodos y ${edgeCount} conexiones.`}</desc>
        <defs>
          <clipPath id={clipId}>
            <rect width={CARD_W} height={CARD_H} rx={14} />
          </clipPath>
          {ARROWS.map((kind) => (
            <marker
              key={kind}
              id={arrowId(kind)}
              viewBox="0 0 10 10"
              refX={9}
              refY={5}
              markerWidth={9}
              markerHeight={9}
              markerUnits="userSpaceOnUse"
              orient="auto"
            >
              <path className={`wf-arrow wf-arrow--${kind}`} d="M0 0 10 5 0 10z" />
            </marker>
          ))}
        </defs>

        <g className={`wf-viewport${animating ? ' wf-viewport--animated' : ''}`} style={{ transform: viewCss(view) }}>
          <g className="wf-edges" aria-hidden="true">
            {edges.map((edge) => {
              const state = overlay.edges.get(edge.key) ?? IDLE_EDGE;
              const classes = ['wf-edge', `wf-edge--${state.visual}`];
              if (state.flowing) classes.push('wf-edge--flowing');
              if (edge.kind !== 'main') classes.push('wf-edge--ai');
              return (
                <path
                  key={edge.key}
                  className={classes.join(' ')}
                  d={edge.d}
                  markerEnd={`url(#${arrowId(state.visual)})`}
                />
              );
            })}
          </g>

          <g className="wf-elabels" aria-hidden="true">
            {labelled.map((edge) => (
              <EdgeLabel key={edge.key} edge={edge} overlay={overlay.edges.get(edge.key) ?? IDLE_EDGE} />
            ))}
          </g>

          <g className="wf-nodes">
            {layout.nodes.map((box) => (
              <DiagramNode
                key={box.name}
                box={box}
                overlay={overlay.nodes.get(box.name) ?? PLAIN}
                selected={selected === box.name}
                current={overlay.current === box.name}
                clipId={clipId}
                onSelect={onSelect}
              />
            ))}
          </g>
        </g>
      </svg>

      <div className="wf-controls" data-wf-controls>
        <button type="button" className="wf-controls__btn" aria-label="Alejar" onClick={zoomOut}>
          <ZoomIcon>
            <path d="M5 12h14" />
          </ZoomIcon>
        </button>
        <span className="wf-zoom__level">{Math.round(view.k * 100)}%</span>
        <button type="button" className="wf-controls__btn" aria-label="Acercar" onClick={zoomIn}>
          <ZoomIcon>
            <path d="M12 5v14M5 12h14" />
          </ZoomIcon>
        </button>
        <button type="button" className="wf-controls__btn" aria-label="Ajustar a pantalla" onClick={fit}>
          <ZoomIcon>
            <path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" />
          </ZoomIcon>
        </button>
      </div>

      {dock && (
        <div className="wf-dock" data-wf-controls>
          {dock}
        </div>
      )}
    </div>
  );
}

/** Esqueleto del lienzo mientras llega el grafo: mismo marco, con tarjetas fantasma en dos filas. */
export function WorkflowCanvasSkeleton() {
  return (
    <div className="wf-canvas wf-canvas--skeleton" aria-hidden="true">
      <div className="wf-skeleton">
        {[0, 1].map((row) => (
          <div key={row} className="wf-skeleton__row">
            {Array.from({ length: 5 }, (_, i) => (
              <Skeleton key={i} height={64} width={116} radius={14} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
