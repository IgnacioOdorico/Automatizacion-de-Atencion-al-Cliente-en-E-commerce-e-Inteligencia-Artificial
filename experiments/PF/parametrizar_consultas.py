# -*- coding: utf-8 -*-
"""Parametriza las consultas SQL de los nodos de base de datos (defecto D-9).

Los nodos armaban la sentencia insertando el valor recibido dentro del texto de la
consulta. Un apóstrofo en un nombre o en un mensaje rompía la sentencia y la
ejecución terminaba sin respuesta ni registro, y un valor preparado para cerrar la
comilla podía alterar la sentencia. Cada consulta pasa a usar marcadores de posición
($1, $2, …) y la opción «Query Parameters» del nodo de PostgreSQL, que envía los
valores separados de la sentencia.

De paso cierra la parte de D-8 que quedó abierta: la variante de producción del
Flujo 2 conservaba la consulta anterior a D-7, la que no emite ningún ítem cuando el
pedido no existe y deja al cliente sin respuesta.

No es idempotente: aborta si la consulta no está en la forma previa.

    python experiments/PF/parametrizar_consultas.py --repo
    python experiments/PF/parametrizar_consultas.py entrada.json salida.json
"""
import json
import os
import sys

ORDEN = "$('Registrar Orden').item.json.order_id"
WEBHOOK = "$('Webhook - Recibir Orden').item.json.body"
PARSE = "$('Parse JSON').item.json"

CONSULTAS = {
    'Registrar Orden': ("""INSERT INTO orders (
  order_number,
  customer_name,
  customer_email,
  customer_phone,
  product_id,
  quantity,
  total_amount,
  status,
  received_at,
  raw_payload
)
SELECT
  $1,
  $2,
  $3,
  $4,
  p.id,
  $5::int,
  p.price * $5::int,
  'pending',
  NOW(),
  $6::jsonb
FROM products p
WHERE p.sku = $7
RETURNING id AS order_id, order_number, total_amount, product_id;""",
                        '={{ [$json.body.order_number, $json.body.customer_name, $json.body.customer_email, '
                        '$json.body.customer_phone, $json.body.quantity, JSON.stringify($json.body), '
                        '$json.body.product_sku] }}'),
    'Verificar Stock': ("""SELECT
  p.id AS product_id,
  p.sku,
  p.name AS product_name,
  p.price,
  p.stock AS stock_actual,
  p.stock_min,
  $1::int AS cantidad_solicitada,
  CASE
    WHEN p.stock >= $1::int THEN true
    ELSE false
  END AS stock_disponible
FROM products p
WHERE p.sku = $2;""",
                        '={{ [%s.quantity, %s.product_sku] }}' % (WEBHOOK, WEBHOOK)),
    'Actualizar Stock': ("""UPDATE products
SET stock = stock - $1::int
WHERE id = $2::int
RETURNING id AS product_id, sku, stock AS stock_nuevo, (SELECT stock_min FROM products WHERE id = $2::int) AS stock_min;""",
                         '={{ [$json.cantidad_solicitada, $json.product_id] }}'),
    'Confirmar Orden': ("""UPDATE orders
SET
  status = 'confirmed',
  processed_at = NOW()
WHERE id = $1::int
RETURNING id AS order_id, order_number, status, processed_at;""",
                        '={{ [%s] }}' % ORDEN),
    'Marcar Sin Stock': ("""UPDATE orders
SET
  status = 'no_stock',
  processed_at = NOW()
WHERE id = $1::int
RETURNING id AS order_id, order_number, status, processed_at;""",
                         '={{ [%s] }}' % ORDEN),
    'Registrar Notificación': ("""UPDATE orders
SET notified_at = NOW()
WHERE id = $1::int
RETURNING id AS order_id, notified_at;""", '={{ [%s] }}' % ORDEN),
    'Registrar Alerta Stock Bajo': ("""INSERT INTO stock_alerts (product_id, order_id, sku, stock_actual, stock_min)
VALUES (
  $1::int,
  $2::int,
  $3,
  $4::int,
  $5::int
)
RETURNING id AS alert_id, sku, stock_actual, stock_min;""",
                                    '={{ [$json.product_id, %s, $json.sku, $json.stock_nuevo, $json.stock_min] }}' % ORDEN),
    'Buscar Pedido': ("""SELECT
    o.order_number,
    o.customer_name,
    o.status,
    o.quantity,
    o.total_amount,
    o.received_at,
    o.processed_at,
    p.name AS product_name
FROM (SELECT $1::varchar AS oid) q
LEFT JOIN orders   o ON o.order_number = q.oid
LEFT JOIN products p ON o.product_id  = p.id
ORDER BY o.received_at DESC NULLS LAST
LIMIT 1;""", '={{ [$json.order_id] }}'),
    'Crear Ticket': ("""INSERT INTO tickets (channel, user_id, subject, status, priority, created_at)
VALUES (
    $1,
    $2,
    $3,
    'open',
    CASE WHEN $4::boolean THEN 'urgent' ELSE 'normal' END,
    NOW()
)
RETURNING id, status, priority, created_at;""",
                     "={{ [$json.canal, $json.user, $json.message, $json.urgente === true || $json.urgente === 'true'] }}"),
    'Registrar Interacción': ("""INSERT INTO interactions (
    channel, user_id, message, intent, ai_response,
    order_id, is_urgent, received_at, responded_at
)
VALUES (
    $1,
    $2,
    $3,
    $4,
    $5,
    (SELECT id FROM orders WHERE order_number = $6),
    $7::boolean,
    $8::timestamp,
    NOW()
);""", "={{ [%s.canal, %s.user, %s.message, %s.intent, %s.respuesta, %s.order_id, "
       "%s.urgente === true || %s.urgente === 'true', %s.received_at] }}" % ((PARSE,) * 9)),
}
# el nodo que lee la base de conocimiento no recibe ningún valor del usuario
SIN_VALORES = {'Buscar FAQ'}


def normalizar_nombres(w):
    """La variante de producción del Flujo 1 quedó con un nodo mal codificado por la
    consola desde la que se exportó. El nombre se corrige en el nodo y en las conexiones."""
    for viejo, nuevo in (('Registrar Notificaciâ”œâ”‚n', 'Registrar Notificación'),):
        for n in w['nodes']:
            if n['name'] == viejo:
                n['name'] = nuevo
        if viejo in w.get('connections', {}):
            w['connections'][nuevo] = w['connections'].pop(viejo)
        for destinos in w.get('connections', {}).values():
            for salidas in destinos.values():
                for salida in salidas:
                    for con in salida:
                        if con.get('node') == viejo:
                            con['node'] = nuevo


def parametrizar(w):
    hechos = []
    normalizar_nombres(w)
    for n in w['nodes']:
        if not n['type'].endswith('postgres'):
            continue
        nombre = n['name'].replace('Sin Stock', 'Sin Stock')
        clave = 'Registrar Notificación' if nombre.startswith('Registrar Notificación') else nombre
        if clave in SIN_VALORES:
            continue
        assert clave in CONSULTAS, 'nodo sin consulta prevista: %r' % n['name']
        q = n['parameters'].get('query', '')
        assert '{{' in q, 'la consulta de %r ya no interpola; ¿se corrió dos veces?' % n['name']
        nueva, params = CONSULTAS[clave]
        n['parameters']['query'] = nueva
        n['parameters'].setdefault('options', {})['queryReplacement'] = params
        hechos.append(n['name'])
    return hechos


def main(argv):
    if argv[:1] == ['--repo']:
        archivos = [('workflows/' + f, 'workflows/' + f) for f in sorted(os.listdir('workflows'))]
    else:
        assert len(argv) == 2, __doc__
        archivos = [(argv[0], argv[1])]
    for entrada, salida in archivos:
        with open(entrada, 'rb') as fh:
            crudo = fh.read()
        salto = '\r\n' if b'\r\n' in crudo else '\n'          # se conserva el del archivo
        w = json.loads(crudo.decode('utf-8-sig'))
        hechos = parametrizar(w[0] if isinstance(w, list) else w)   # n8n exporta una lista
        with open(salida, 'w', encoding='utf-8', newline=salto) as fh:
            json.dump(w, fh, ensure_ascii=False, indent=2)
            fh.write('\n')
        print('%s: %d consultas parametrizadas (%s)' % (os.path.basename(entrada), len(hechos), ', '.join(hechos)))


if __name__ == '__main__':
    main(sys.argv[1:])
