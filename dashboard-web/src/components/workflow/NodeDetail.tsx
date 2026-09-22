import { forwardRef, type KeyboardEvent } from 'react';

import { NodeIcon } from '@/components/workflow/nodeIcons';
import { StatusIcon } from '@/components/workflow/StatusIcon';
import { Badge } from '@/components/ui/Badge';
import { traceStatusMeta } from '@/lib/executions';
import { nodeKind } from '@/lib/nodeKinds';
import { nodeDetailFacts, previewText } from '@/lib/nodeDetail';
import type { NodeOverlay } from '@/lib/workflowTrace';

interface NodeDetailProps {
  name: string;
  shortType: string | null;
  disabled: boolean;
  overlay: NodeOverlay;
  /**
   * Qué se sabe de la ejecución elegida: `none` (no hay ninguna), `no-trace` (hay, pero sin
   * detalle por nodo: purgada, demasiado grande) o `trace`.
   */
  execution: 'none' | 'no-trace' | 'trace';
  onClose: () => void;
}

/**
 * Detalle de un nodo: qué es, cómo le fue en la ejecución elegida y su salida.
 * La vista previa (ya redactada por el backend) se dibuja SOLO como texto en un
 * bloque monoespaciado: nunca como HTML. Es una región con foco programático:
 * al abrirla desde el teclado el foco pasa acá, y Escape la cierra.
 */
export const NodeDetail = forwardRef<HTMLElement, NodeDetailProps>(function NodeDetail(
  { name, shortType, disabled, overlay, execution, onClose },
  ref,
) {
  const kind = nodeKind(shortType);
  const { visual, trace } = overlay;
  const status = traceStatusMeta(visual === 'plain' || visual === 'pending' ? 'skipped' : visual);
  const facts = nodeDetailFacts(overlay, shortType);
  const preview = trace ? previewText(trace.output_preview) : null;
  const ran = visual === 'success' || visual === 'error' || visual === 'running' || visual === 'waiting';

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === 'Escape') {
      event.stopPropagation();
      onClose();
    }
  };

  return (
    <aside
      ref={ref}
      className="wf-detail"
      role="region"
      aria-label={`Detalle del nodo ${name}`}
      tabIndex={-1}
      onKeyDown={onKeyDown}
    >
      <header className="wf-detail__head">
        <span className="wf-detail__icon">
          <NodeIcon name={kind.icon} size={20} />
        </span>
        <div className="wf-detail__title">
          <h3>{name}</h3>
          <p>{kind.label}</p>
        </div>
        <button type="button" className="wf-detail__close" aria-label="Cerrar detalle" onClick={onClose}>
          <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" aria-hidden="true">
            <path d="m6 6 12 12M18 6 6 18" />
          </svg>
        </button>
      </header>

      <div className="wf-detail__body">
        {disabled && <p className="wf-detail__note">Este paso está deshabilitado: el proceso lo saltea.</p>}

        {execution === 'none' ? (
          <p className="wf-detail__note">
            Cuando haya una ejecución de este workflow, acá vas a ver qué hizo este nodo: cuánto tardó, cuántos items
            produjo y su salida.
          </p>
        ) : execution === 'no-trace' ? (
          <p className="wf-detail__note">
            La ejecución elegida no tiene detalle por nodo, así que no hay datos de este nodo. Probá con otra ejecución.
          </p>
        ) : visual === 'missing' ? (
          <p className="wf-detail__note">
            Este nodo no figura en la ejecución elegida (el workflow cambió después de que corrió).
          </p>
        ) : (
          <>
            <Badge tone={status.tone}>
              <StatusIcon name={status.icon} />
              {status.label}
            </Badge>
            {visual === 'skipped' && (
              <p className="wf-detail__note">
                Este nodo no se ejecutó en esta ejecución: el camino siguió por otra rama.
              </p>
            )}
            {facts.length > 0 && (
              <dl className="wf-detail__facts">
                {facts.map((fact) => (
                  <div key={fact.label}>
                    <dt>{fact.label}</dt>
                    <dd>{fact.value}</dd>
                  </div>
                ))}
              </dl>
            )}

            {trace?.error && (
              <div className="wf-detail__error" role="group" aria-label="Error del nodo">
                <p className="wf-detail__error-title">{trace.error.message}</p>
                {trace.error.description && <p>{trace.error.description}</p>}
              </div>
            )}

            {ran && (
              <div className="wf-detail__out">
                <h4>Salida</h4>
                {preview === null ? (
                  <p className="wf-detail__note">Sin salida registrada.</p>
                ) : (
                  <>
                    <pre className="wf-preview" tabIndex={0} aria-label={`Vista previa de la salida de ${name}`}>
                      {preview}
                    </pre>
                    {trace?.output_truncated && (
                      <p className="wf-detail__note">
                        Es una vista previa recortada: se muestran los primeros items y los textos largos se cortan.
                        Los datos sensibles se ocultan como [REDACTADO].
                      </p>
                    )}
                  </>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </aside>
  );
});
