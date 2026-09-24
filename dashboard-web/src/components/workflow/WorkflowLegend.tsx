/**
 * Cómo leer el diagrama: qué significa cada color, ícono y línea, y cómo
 * moverse. Cada estado se explica con un muestrario chico Y con texto: el color
 * nunca es lo único que distingue un estado.
 */
export function WorkflowLegend() {
  return (
    <section className="wf-legend" aria-label="Cómo leer el diagrama">
      <ul className="wf-legend__list">
        <li>
          <span className="wf-legend__swatch wf-legend__swatch--success" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round">
              <path d="m5 12 5 5 9-10" />
            </svg>
          </span>
          Correcto
        </li>
        <li>
          <span className="wf-legend__swatch wf-legend__swatch--error" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth={2.6} strokeLinecap="round">
              <path d="m6 6 12 12M18 6 6 18" />
            </svg>
          </span>
          Con error
        </li>
        <li>
          <span className="wf-legend__swatch wf-legend__swatch--skipped" aria-hidden="true" />
          No se ejecutó
        </li>
        <li>
          <span className="wf-legend__line wf-legend__line--active" aria-hidden="true" />
          Camino recorrido
        </li>
        <li>
          <span className="wf-legend__line wf-legend__line--inactive" aria-hidden="true" />
          Camino no tomado
        </li>
        <li>
          <span className="wf-legend__tag" aria-hidden="true">
            Sí / No
          </span>
          Rama de una condición
        </li>
      </ul>
      <p className="wf-legend__hint">
        Arrastrá para mover el diagrama, Ctrl + rueda (o pellizco) para acercar, y Tab con Enter para abrir un nodo.
      </p>
    </section>
  );
}
