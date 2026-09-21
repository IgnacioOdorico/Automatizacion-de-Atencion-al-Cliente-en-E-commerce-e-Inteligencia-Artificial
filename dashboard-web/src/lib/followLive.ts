/**
 * Modo "Seguir en vivo": cuando llega una ejecución más nueva que la última
 * vista, se elige sola. Lógica pura; el polling lo hace la página.
 */

export interface FollowResult {
  /** Ejecución a seleccionar, o `null` si no hay que cambiar nada. */
  selectId: number | null;
  /** Lo más nuevo que ya se vio (para la próxima vuelta). */
  seenId: number | null;
  /** Llegó una ejecución nueva después de la primera carga (para animarla). */
  isNew: boolean;
}

export function followStep(lastSeenId: number | null, newestId: number | null): FollowResult {
  if (newestId === null) return { selectId: null, seenId: lastSeenId, isNew: false };
  if (lastSeenId === null) return { selectId: newestId, seenId: newestId, isNew: false };
  if (newestId > lastSeenId) return { selectId: newestId, seenId: newestId, isNew: true };
  return { selectId: null, seenId: lastSeenId, isNew: false };
}
