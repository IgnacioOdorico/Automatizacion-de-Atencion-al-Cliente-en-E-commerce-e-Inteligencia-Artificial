/**
 * Filas nuevas de un listado que se actualiza solo (polling): sirven para
 * resaltar un momento el pedido que acaba de entrar y que se note en cámara.
 */

/**
 * Ids (numéricos o de texto, como los de eventos) presentes en `ids` que no se habían visto antes, en el orden de la lista.
 * `seen === null` es la primera carga: nada se resalta.
 */
export function detectNewIds<T extends string | number>(
  seen: ReadonlySet<T> | null,
  ids: readonly T[],
): T[] {
  if (seen === null) return [];
  return ids.filter((id) => !seen.has(id));
}
