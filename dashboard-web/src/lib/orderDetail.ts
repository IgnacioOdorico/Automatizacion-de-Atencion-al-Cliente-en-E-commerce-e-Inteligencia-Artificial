/**
 * Lógica pura del detalle de un pedido: cómo se muestra el `raw_payload` JSONB
 * original del webhook y cómo se rotula cada ítem de la orden.
 */

export interface PayloadField {
  key: string;
  label: string;
  value: string;
}

export type PayloadView =
  | { kind: 'empty' }
  /** Objeto plano: campos legibles + el JSON completo para verlo crudo. */
  | { kind: 'fields'; fields: PayloadField[]; json: string }
  /** Estructura anidada o arreglo: solo JSON indentado. */
  | { kind: 'json'; json: string }
  | { kind: 'text'; text: string };

/** Campos del payload que envía el webhook de órdenes (Flujo 1). */
const KNOWN_LABELS: Record<string, string> = {
  order_number: 'Nº de pedido',
  customer_name: 'Cliente',
  customer_email: 'Email',
  customer_phone: 'Teléfono',
  product_sku: 'SKU',
  quantity: 'Cantidad',
};

function humanizeKey(key: string): string {
  const spaced = key.replace(/[_-]+/g, ' ').trim();
  return spaced ? spaced.charAt(0).toUpperCase() + spaced.slice(1) : key;
}

function isPrimitive(value: unknown): boolean {
  return value === null || ['string', 'number', 'boolean'].includes(typeof value);
}

function displayValue(value: unknown): string {
  if (value === null) return '—';
  if (typeof value === 'boolean') return value ? 'Sí' : 'No';
  return String(value);
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function describePayload(raw: unknown): PayloadView {
  if (raw === null || raw === undefined) return { kind: 'empty' };

  if (typeof raw === 'string') {
    const text = raw.trim();
    if (!text) return { kind: 'empty' };
    try {
      const parsed: unknown = JSON.parse(text);
      if (typeof parsed === 'object' && parsed !== null) return describePayload(parsed);
    } catch {
      // No es JSON: se muestra como texto.
    }
    return { kind: 'text', text };
  }

  if (isPlainObject(raw)) {
    const entries = Object.entries(raw);
    if (entries.length === 0) return { kind: 'empty' };
    const json = JSON.stringify(raw, null, 2);
    if (entries.every(([, value]) => isPrimitive(value))) {
      return {
        kind: 'fields',
        json,
        fields: entries.map(([key, value]) => ({
          key,
          label: KNOWN_LABELS[key] ?? humanizeKey(key),
          value: displayValue(value),
        })),
      };
    }
    return { kind: 'json', json };
  }

  if (Array.isArray(raw)) {
    return raw.length === 0 ? { kind: 'empty' } : { kind: 'json', json: JSON.stringify(raw, null, 2) };
  }

  return { kind: 'text', text: String(raw) };
}

/**
 * Nombre a mostrar de un ítem. La API devuelve solo `product_id`; el nombre que
 * conocemos es el del producto de la orden, así que solo se usa cuando la orden
 * tiene un único ítem (con varios no se adivina cuál es cuál).
 */
export function orderItemProduct(
  item: { product_id: number },
  itemCount: number,
  order: { product_name: string | null; product_sku: string | null },
): string {
  if (itemCount === 1 && order.product_name) return order.product_name;
  return `Producto n.º ${item.product_id}`;
}
