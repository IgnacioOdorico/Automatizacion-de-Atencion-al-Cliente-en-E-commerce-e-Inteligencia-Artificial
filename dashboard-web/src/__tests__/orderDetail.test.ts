import { describe, expect, it } from 'vitest';

import { describePayload, orderItemProduct } from '@/lib/orderDetail';

describe('describePayload', () => {
  it('sin payload registrado', () => {
    expect(describePayload(null)).toEqual({ kind: 'empty' });
    expect(describePayload(undefined)).toEqual({ kind: 'empty' });
    expect(describePayload({})).toEqual({ kind: 'empty' });
    expect(describePayload('   ')).toEqual({ kind: 'empty' });
  });

  it('un objeto plano del webhook se muestra como campos con etiquetas en español', () => {
    const view = describePayload({
      order_number: 'ORD-2026-0110',
      customer_name: 'Lucía Fernández',
      customer_email: 'lucia@example.com',
      product_sku: 'PROD-003',
      quantity: 1,
    });
    expect(view.kind).toBe('fields');
    if (view.kind !== 'fields') return;
    expect(view.fields).toEqual([
      { key: 'order_number', label: 'Nº de pedido', value: 'ORD-2026-0110' },
      { key: 'customer_name', label: 'Cliente', value: 'Lucía Fernández' },
      { key: 'customer_email', label: 'Email', value: 'lucia@example.com' },
      { key: 'product_sku', label: 'SKU', value: 'PROD-003' },
      { key: 'quantity', label: 'Cantidad', value: '1' },
    ]);
  });

  it('conserva el JSON completo indentado para verlo crudo', () => {
    const view = describePayload({ quantity: 2 });
    expect(view.kind).toBe('fields');
    if (view.kind !== 'fields') return;
    expect(view.json).toBe('{\n  "quantity": 2\n}');
  });

  it('las claves desconocidas se humanizan (sin guiones bajos crudos)', () => {
    const view = describePayload({ shipping_zone: 'Mendoza', gift: true, note: null });
    if (view.kind !== 'fields') throw new Error('se esperaban campos');
    expect(view.fields.map((f) => f.label)).toEqual(['Shipping zone', 'Gift', 'Note']);
    expect(view.fields.map((f) => f.value)).toEqual(['Mendoza', 'Sí', '—']);
  });

  it('un JSON serializado como string se interpreta igual que el objeto', () => {
    const view = describePayload('{"quantity":3}');
    expect(view.kind).toBe('fields');
  });

  it('estructuras anidadas o arreglos se muestran como JSON indentado', () => {
    expect(describePayload({ items: [{ sku: 'A' }] })).toEqual({
      kind: 'json',
      json: '{\n  "items": [\n    {\n      "sku": "A"\n    }\n  ]\n}',
    });
    expect(describePayload([1, 2]).kind).toBe('json');
  });

  it('un string que no es JSON se muestra como texto', () => {
    expect(describePayload('llegó sin formato')).toEqual({
      kind: 'text',
      text: 'llegó sin formato',
    });
  });
});

describe('orderItemProduct', () => {
  const order = { product_name: 'Teclado Mecánico Redragon', product_sku: 'PROD-003' };

  it('una orden de un solo ítem lo muestra con el producto de la orden', () => {
    expect(orderItemProduct({ product_id: 3 }, 1, order)).toBe('Teclado Mecánico Redragon');
  });

  it('con varios ítems no se adivina: se identifica por número de producto', () => {
    expect(orderItemProduct({ product_id: 3 }, 2, order)).toBe('Producto n.º 3');
  });

  it('sin nombre de producto en la orden cae al número', () => {
    expect(orderItemProduct({ product_id: 7 }, 1, { product_name: null, product_sku: null })).toBe(
      'Producto n.º 7',
    );
  });
});
