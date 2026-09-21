import { formatDateTimeSeconds, formatMs } from '@/lib/format';
import { branchLabel } from '@/lib/workflowGraph';
import type { NodeOverlay } from '@/lib/workflowTrace';

/**
 * Lo que se muestra en el panel de detalle de un nodo: datos de la ejecución y
 * la salida como texto. Lógica pura (sin React). La salida ya viene redactada
 * por el backend: acá nunca se intenta des-redactar ni completar nada.
 */

export interface DetailFact {
  label: string;
  value: string;
}

function itemsText(count: number): string {
  return count === 1 ? '1 ítem' : `${count} ítems`;
}

/**
 * Cuántos items salieron por cada rama ("Sí: 1 · No: 0"). Un nodo con una sola
 * salida no necesita desglose; sin datos de salida, tampoco.
 */
export function outputsSummary(shortType: string | null, outputs: readonly number[]): string | null {
  if (outputs.length === 0) return null;
  if (outputs.length === 1 && shortType !== 'if') return null;
  return outputs
    .map((count, index) => `${branchLabel(shortType, index) ?? `Salida ${index + 1}`}: ${count}`)
    .join(' · ');
}

/**
 * La salida de un nodo como texto para el bloque monoespaciado: una lista JSON
 * se indenta; el peor caso (un texto ya recortado por la API) pasa tal cual.
 * `null` si el nodo no produjo salida.
 */
export function previewText(preview: unknown): string | null {
  if (preview === null || preview === undefined) return null;
  if (typeof preview === 'string') return preview;
  try {
    return JSON.stringify(preview, null, 2) ?? String(preview);
  } catch {
    return String(preview);
  }
}

/** Datos del nodo en la ejecución elegida (vacío si el nodo no corrió o no hay ejecución). */
export function nodeDetailFacts(overlay: NodeOverlay, shortType: string | null): DetailFact[] {
  const { visual, trace } = overlay;
  if (!trace || (visual !== 'success' && visual !== 'error' && visual !== 'running' && visual !== 'waiting' && visual !== 'canceled')) {
    return [];
  }
  const facts: DetailFact[] = [];
  if (trace.started_at) facts.push({ label: 'Inicio', value: formatDateTimeSeconds(trace.started_at) });
  facts.push({ label: 'Duración', value: formatMs(trace.duration_ms) });
  if (visual === 'success') {
    facts.push({ label: 'Items de salida', value: itemsText(trace.items_out) });
    if (trace.runs > 1) facts.push({ label: 'Corridas (la duración las suma)', value: String(trace.runs) });
    const outputs = outputsSummary(shortType, trace.outputs);
    if (outputs) facts.push({ label: 'Por cada salida', value: outputs });
  }
  return facts;
}
