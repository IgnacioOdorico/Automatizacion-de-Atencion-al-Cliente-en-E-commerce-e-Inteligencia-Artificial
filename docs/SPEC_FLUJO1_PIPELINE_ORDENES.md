# Especificación Técnica — Flujo 1: Pipeline de Procesamiento de Órdenes

> **Proyecto**: Automatización del ciclo post-venta en e-commerce: pipeline de procesamiento de órdenes y atención al cliente omnicanal con IA, implementado con n8n
>
> **Autores**: Santiago Sordi, Ignacio Odorico, Juan Cruz Ana — UTN FRM
>
> **Tutor**: Prof. Alberto Cortez
>
> **Versión**: 1.0
>
> **Fecha**: 2026-04-15

---

## Tabla de Contenidos

1. [Overview](#1-overview)
2. [Trigger — Webhook](#2-trigger--webhook)
3. [Especificación nodo por nodo](#3-especificación-nodo-por-nodo)
4. [Diagrama de flujo del pipeline](#4-diagrama-de-flujo-del-pipeline)
5. [Event logging](#5-event-logging)
6. [Métricas — MTTD y MTTR](#6-métricas--mttd-y-mttr)
7. [Instrucciones de testing](#7-instrucciones-de-testing)
8. [Casos borde](#8-casos-borde)

---

## 1. Overview

### Qué hace este flujo

El **Flujo 1** es un pipeline de procesamiento de órdenes de e-commerce implementado como un workflow de n8n. Recibe órdenes de compra vía webhook HTTP, verifica disponibilidad de stock en la base de datos PostgreSQL, actualiza inventario, confirma la orden y envía un email de notificación al cliente a través de Mailpit (servidor SMTP local).

### Por qué es importante

Este pipeline automatiza el ciclo post-venta desde la recepción de la orden hasta la notificación al cliente, eliminando intervención manual. Cada paso del procesamiento se registra en la tabla `pipeline_events` como bitácora de auditoría, lo que permite medir:

- **MTTD** (Mean Time To Detect): tiempo desde recepción hasta que el pipeline termina de procesar.
- **MTTR** (Mean Time To Resolve): tiempo desde el procesamiento hasta la notificación al cliente.

Estas métricas son el eje central de la tesis y se visualizan en Grafana.

### Relación con el Flujo 2

El Flujo 2 (chatbot omnicanal) consulta la tabla `orders` creada por este pipeline cuando el cliente pregunta por el estado de su pedido (intent `ESTADO_PEDIDO`). Ambos flujos comparten la misma base de datos PostgreSQL (`ecommerce_tesis`).

### Infraestructura

| Servicio   | URL                     | Credenciales           |
|------------|-------------------------|------------------------|
| n8n        | `http://localhost:5678` | admin / admin123       |
| PostgreSQL | `localhost:5432`        | n8n_user / n8n_pass    |
| Mailpit    | `http://localhost:8025` (web) / `localhost:1025` (SMTP) | — |
| Grafana    | `http://localhost:3000` | admin / admin          |

**Base de datos**: `ecommerce_tesis`

**Nota sobre conexiones PostgreSQL en n8n**: Dentro de la red Docker, n8n se conecta a PostgreSQL usando el hostname `postgres` (nombre del servicio en docker-compose), no `localhost`. De la misma forma, el SMTP se conecta como `mailpit:1025`.

---

## 2. Trigger — Webhook

### Endpoint

```
POST http://localhost:5678/webhook/orden-nueva
```

El path del webhook en n8n se configura como `/orden-nueva`. n8n expone esto automáticamente bajo `/webhook/`.

### Payload esperado (JSON)

```json
{
  "order_number": "ORD-2026-0001",
  "customer_name": "María García",
  "customer_email": "maria@example.com",
  "customer_phone": "+5492614001234",
  "product_sku": "PROD-001",
  "quantity": 2
}
```

### Validación de campos

| Campo            | Tipo   | Requerido | Validación                                    |
|------------------|--------|-----------|-----------------------------------------------|
| `order_number`   | string | Sí        | No vacío. Único en la tabla `orders`.          |
| `customer_name`  | string | Sí        | No vacío.                                      |
| `customer_email` | string | Sí        | No vacío. Formato email válido.                |
| `customer_phone` | string | No        | Puede ser null o vacío.                        |
| `product_sku`    | string | Sí        | Debe existir en la tabla `products`.           |
| `quantity`       | number | Sí        | Entero mayor a 0.                              |

### Respuesta del webhook

El webhook responde sincrónicamente al final del pipeline con un JSON indicando el resultado (ver [Nodo 11: Respuesta Webhook](#nodo-11-respuesta-webhook)).

---

## 3. Especificación nodo por nodo

### Nodo 1: Webhook — Recibir Orden

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Webhook - Recibir Orden`            |
| **Tipo n8n**    | `n8n-nodes-base.webhook`             |
| **HTTP Method** | POST                                 |
| **Path**        | `orden-nueva`                        |
| **Response Mode** | `Last Node` (responde al final del pipeline) |
| **Authentication** | None                              |

**Configuración**:
- Response Mode = "Last Node" para que el webhook espere a que todo el pipeline se ejecute y devuelva la respuesta del nodo final.
- No se usa autenticación en el webhook para simplificar las pruebas.

**Output** (datos que pasa al siguiente nodo):

```json
{
  "body": {
    "order_number": "ORD-2026-0001",
    "customer_name": "María García",
    "customer_email": "maria@example.com",
    "customer_phone": "+5492614001234",
    "product_sku": "PROD-001",
    "quantity": 2
  },
  "headers": { ... },
  "params": { ... }
}
```

Los nodos posteriores acceden a los datos del payload mediante `{{ $json.body.order_number }}`, etc.

---

### Nodo 2: Registrar Orden

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Registrar Orden`                    |
| **Tipo n8n**    | `n8n-nodes-base.postgres`            |
| **Operación**   | Execute Query                        |
| **Credential**  | PostgreSQL (ecommerce_tesis)         |

**Descripción**: Busca el producto por SKU, calcula el total y registra la orden en la tabla `orders` con status `pending`. También inserta el evento `order_received` en `pipeline_events`.

**SQL Query**:

```sql
WITH producto AS (
  SELECT id, price
  FROM products
  WHERE sku = '{{ $json.body.product_sku }}'
  LIMIT 1
),
nueva_orden AS (
  INSERT INTO orders (
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
    '{{ $json.body.order_number }}',
    '{{ $json.body.customer_name }}',
    '{{ $json.body.customer_email }}',
    '{{ $json.body.customer_phone }}',
    p.id,
    {{ $json.body.quantity }},
    p.price * {{ $json.body.quantity }},
    'pending',
    NOW(),
    '{{ JSON.stringify($json.body) }}'::jsonb
  FROM producto p
  RETURNING id, order_number, total_amount, product_id, status
)
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
SELECT
  no.id,
  'order_received',
  'success',
  'Orden ' || no.order_number || ' registrada con éxito — total: $' || no.total_amount,
  jsonb_build_object(
    'order_number', no.order_number,
    'product_id', no.product_id,
    'quantity', {{ $json.body.quantity }},
    'total_amount', no.total_amount
  )
FROM nueva_orden no
RETURNING
  order_id,
  (SELECT order_number FROM nueva_orden) AS order_number,
  (SELECT total_amount FROM nueva_orden) AS total_amount,
  (SELECT product_id FROM nueva_orden) AS product_id;
```

**Output**:

```json
{
  "order_id": 1,
  "order_number": "ORD-2026-0001",
  "total_amount": 1199.98,
  "product_id": 1
}
```

**Error handling**:
- Si `product_sku` no existe en `products`, la subquery `producto` devuelve vacío. El INSERT en `orders` no inserta ninguna fila. Se debe capturar este caso (ver [Nodo 3](#nodo-3-verificar-stock)).
- Si `order_number` ya existe, PostgreSQL lanza error de constraint UNIQUE. n8n captura este error y debe retornar un mensaje de "orden duplicada" (ver [Sección 8: Casos borde](#8-casos-borde)).

**Alternativa más robusta** (dos queries separadas si el CTE causa problemas en n8n):

Si n8n no maneja bien CTEs con múltiples INSERTs en una sola query, se puede dividir en dos nodos:
1. **Nodo 2a**: Buscar producto y registrar la orden.
2. **Nodo 2b**: Insertar evento `order_received`.

**Query Nodo 2a — Registrar la orden**:

```sql
INSERT INTO orders (
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
  '{{ $json.body.order_number }}',
  '{{ $json.body.customer_name }}',
  '{{ $json.body.customer_email }}',
  '{{ $json.body.customer_phone }}',
  p.id,
  {{ $json.body.quantity }},
  p.price * {{ $json.body.quantity }},
  'pending',
  NOW(),
  '{{ JSON.stringify($json.body) }}'::jsonb
FROM products p
WHERE p.sku = '{{ $json.body.product_sku }}'
RETURNING id AS order_id, order_number, total_amount, product_id;
```

**Query Nodo 2b — Registrar evento `order_received`**:

```sql
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
VALUES (
  {{ $json.order_id }},
  'order_received',
  'success',
  'Orden {{ $json.order_number }} registrada — total: ${{ $json.total_amount }}',
  '{"order_number": "{{ $json.order_number }}", "total_amount": {{ $json.total_amount }}}'::jsonb
)
RETURNING id AS event_id;
```

---

### Nodo 3: Verificar Stock

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Verificar Stock`                    |
| **Tipo n8n**    | `n8n-nodes-base.postgres`            |
| **Operación**   | Execute Query                        |
| **Credential**  | PostgreSQL (ecommerce_tesis)         |

**Descripción**: Consulta el stock actual del producto y lo compara con la cantidad solicitada.

**SQL Query**:

```sql
SELECT
  p.id AS product_id,
  p.sku,
  p.name AS product_name,
  p.price,
  p.stock AS stock_actual,
  p.stock_min,
  {{ $json.body.quantity }} AS cantidad_solicitada,
  CASE
    WHEN p.stock >= {{ $json.body.quantity }} THEN true
    ELSE false
  END AS stock_disponible
FROM products p
WHERE p.sku = '{{ $json.body.product_sku }}';
```

**Output**:

```json
{
  "product_id": 1,
  "sku": "PROD-001",
  "product_name": "Notebook Lenovo IdeaPad 15",
  "price": 599.99,
  "stock_actual": 20,
  "stock_min": 3,
  "cantidad_solicitada": 2,
  "stock_disponible": true
}
```

**Nota**: Los datos de `order_id`, `order_number`, `total_amount` y los datos del cliente vienen del nodo anterior y deben estar disponibles en el contexto. Si n8n no los propaga automáticamente, se pueden referenciar mediante `{{ $('Registrar Orden').item.json.order_id }}` o mediante un nodo `Set` intermedio que combine ambos conjuntos de datos.

---

### Nodo 4: IF — Stock Disponible

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `IF Stock Disponible`                |
| **Tipo n8n**    | `n8n-nodes-base.if`                  |
| **Condición**   | `{{ $json.stock_disponible }}` equals `true` |

**Configuración del nodo IF**:

- **Condition**: Boolean
- **Value 1**: `{{ $json.stock_disponible }}`
- **Operation**: Equal
- **Value 2**: `true`

**Salidas**:
- **true** (rama superior): Hay stock suficiente → continúa a [Nodo 5: Actualizar Stock](#nodo-5-actualizar-stock)
- **false** (rama inferior): No hay stock → continúa a [Nodo 9: Marcar Sin Stock](#nodo-9-marcar-sin-stock)

---

### Nodo 5: Actualizar Stock (rama Stock OK)

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Actualizar Stock`                   |
| **Tipo n8n**    | `n8n-nodes-base.postgres`            |
| **Operación**   | Execute Query                        |
| **Credential**  | PostgreSQL (ecommerce_tesis)         |

**Descripción**: Descuenta el stock del producto, actualiza el status de la orden a `processing`, y registra los eventos `stock_checked` y `stock_updated`.

**SQL Query**:

```sql
-- Descontar stock del producto
UPDATE products
SET stock = stock - {{ $json.cantidad_solicitada }}
WHERE id = {{ $json.product_id }};

-- Actualizar status de la orden a 'processing'
UPDATE orders
SET status = 'processing'
WHERE id = {{ $('Registrar Orden').item.json.order_id }};

-- Registrar evento stock_checked
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
VALUES (
  {{ $('Registrar Orden').item.json.order_id }},
  'stock_checked',
  'success',
  'Stock verificado para {{ $json.sku }} — disponible: {{ $json.stock_actual }}, solicitado: {{ $json.cantidad_solicitada }}',
  jsonb_build_object(
    'sku', '{{ $json.sku }}',
    'stock_antes', {{ $json.stock_actual }},
    'cantidad_solicitada', {{ $json.cantidad_solicitada }},
    'stock_despues', {{ $json.stock_actual }} - {{ $json.cantidad_solicitada }}
  )
);

-- Registrar evento stock_updated
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
VALUES (
  {{ $('Registrar Orden').item.json.order_id }},
  'stock_updated',
  'success',
  'Stock actualizado para {{ $json.sku }} — nuevo stock: ' || ({{ $json.stock_actual }} - {{ $json.cantidad_solicitada }}),
  jsonb_build_object(
    'sku', '{{ $json.sku }}',
    'stock_anterior', {{ $json.stock_actual }},
    'stock_nuevo', {{ $json.stock_actual }} - {{ $json.cantidad_solicitada }}
  )
);

-- Devolver el stock resultante para verificar stock bajo
SELECT
  {{ $json.product_id }} AS product_id,
  '{{ $json.sku }}' AS sku,
  ({{ $json.stock_actual }} - {{ $json.cantidad_solicitada }}) AS stock_nuevo,
  {{ $json.stock_min }} AS stock_min;
```

**Output**:

```json
{
  "product_id": 1,
  "sku": "PROD-001",
  "stock_nuevo": 18,
  "stock_min": 3
}
```

**Nota sobre múltiples statements**: Si n8n no soporta múltiples statements SQL en una sola query, se debe dividir este nodo en sub-nodos individuales (uno por UPDATE/INSERT). En ese caso, encadenarlos secuencialmente.

---

### Nodo 6: Verificar Stock Bajo (rama Stock OK)

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Verificar Stock Bajo`               |
| **Tipo n8n**    | `n8n-nodes-base.if`                  |
| **Condición**   | `stock_nuevo` < `stock_min`          |

**Configuración del nodo IF**:

- **Value 1**: `{{ $json.stock_nuevo }}`
- **Operation**: Smaller
- **Value 2**: `{{ $json.stock_min }}`

**Salidas**:
- **true**: Stock bajo → se registra una alerta `low_stock_alert` y luego continúa a [Nodo 7](#nodo-7-confirmar-orden-rama-stock-ok).
- **false**: Stock normal → continúa directamente a [Nodo 7](#nodo-7-confirmar-orden-rama-stock-ok).

**Nodo auxiliar — Registrar Alerta Stock Bajo** (se ejecuta solo si la condición es true):

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Alerta Stock Bajo`                  |
| **Tipo n8n**    | `n8n-nodes-base.postgres`            |
| **Operación**   | Execute Query                        |

**SQL Query**:

```sql
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
VALUES (
  {{ $('Registrar Orden').item.json.order_id }},
  'low_stock_alert',
  'warning',
  'ALERTA: Stock bajo para {{ $json.sku }} — stock actual: {{ $json.stock_nuevo }}, mínimo: {{ $json.stock_min }}',
  jsonb_build_object(
    'sku', '{{ $json.sku }}',
    'stock_actual', {{ $json.stock_nuevo }},
    'stock_min', {{ $json.stock_min }}
  )
);
```

**Importante**: Ambas ramas del IF (stock bajo y stock normal) deben converger en el Nodo 7. En n8n esto se logra conectando ambas salidas del IF al mismo nodo siguiente. Se puede usar un nodo **Merge** (mode: `Append`) si es necesario combinar las salidas, pero generalmente basta con conectar ambas salidas al nodo "Confirmar Orden".

---

### Nodo 7: Confirmar Orden (rama Stock OK)

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Confirmar Orden`                    |
| **Tipo n8n**    | `n8n-nodes-base.postgres`            |
| **Operación**   | Execute Query                        |
| **Credential**  | PostgreSQL (ecommerce_tesis)         |

**Descripción**: Marca la orden como `confirmed`, registra el timestamp `processed_at` (usado para calcular MTTD), y registra el evento `invoice_generated`.

**SQL Query**:

```sql
-- Confirmar la orden y registrar processed_at
UPDATE orders
SET
  status = 'confirmed',
  processed_at = NOW()
WHERE id = {{ $('Registrar Orden').item.json.order_id }}
RETURNING id AS order_id, order_number, status, processed_at;
```

**Evento `invoice_generated`** (query separada o en nodo aparte):

```sql
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
VALUES (
  {{ $('Registrar Orden').item.json.order_id }},
  'invoice_generated',
  'success',
  'Orden {{ $('Registrar Orden').item.json.order_number }} confirmada — factura generada',
  jsonb_build_object(
    'order_number', '{{ $('Registrar Orden').item.json.order_number }}',
    'total_amount', {{ $('Registrar Orden').item.json.total_amount }},
    'status', 'confirmed'
  )
);
```

**Output**:

```json
{
  "order_id": 1,
  "order_number": "ORD-2026-0001",
  "status": "confirmed",
  "processed_at": "2026-04-15T14:32:10.123Z"
}
```

---

### Nodo 8: Enviar Email Confirmación (rama Stock OK)

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Enviar Email Confirmación`          |
| **Tipo n8n**    | `n8n-nodes-base.emailSend` (o `n8n-nodes-base.sendEmail`) |
| **Credential**  | SMTP (Mailpit)                       |

**Configuración SMTP**:

| Parámetro  | Valor                          |
|------------|--------------------------------|
| Host       | `mailpit` (hostname Docker)    |
| Port       | `1025`                         |
| SSL/TLS    | Deshabilitado                  |
| User       | *(vacío — Mailpit no requiere auth)* |
| Password   | *(vacío)*                      |

**Campos del email**:

| Campo   | Valor                                                        |
|---------|--------------------------------------------------------------|
| From    | `tesis@ecommerce.local`                                      |
| To      | `{{ $('Webhook - Recibir Orden').item.json.body.customer_email }}` |
| Subject | `Confirmación de Orden {{ $('Registrar Orden').item.json.order_number }}` |
| HTML    | (ver template abajo)                                         |

**Template HTML del email**:

```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #2e7d32;">¡Gracias por tu compra!</h2>

  <p>Hola <strong>{{ $('Webhook - Recibir Orden').item.json.body.customer_name }}</strong>,</p>

  <p>Tu orden ha sido confirmada exitosamente. Aquí están los detalles:</p>

  <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
    <tr style="background-color: #f5f5f5;">
      <td style="padding: 10px; border: 1px solid #ddd;"><strong>Número de orden</strong></td>
      <td style="padding: 10px; border: 1px solid #ddd;">{{ $('Registrar Orden').item.json.order_number }}</td>
    </tr>
    <tr>
      <td style="padding: 10px; border: 1px solid #ddd;"><strong>Producto</strong></td>
      <td style="padding: 10px; border: 1px solid #ddd;">{{ $('Verificar Stock').item.json.product_name }}</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
      <td style="padding: 10px; border: 1px solid #ddd;"><strong>Cantidad</strong></td>
      <td style="padding: 10px; border: 1px solid #ddd;">{{ $('Webhook - Recibir Orden').item.json.body.quantity }}</td>
    </tr>
    <tr>
      <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total</strong></td>
      <td style="padding: 10px; border: 1px solid #ddd;">${{ $('Registrar Orden').item.json.total_amount }}</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
      <td style="padding: 10px; border: 1px solid #ddd;"><strong>Estado</strong></td>
      <td style="padding: 10px; border: 1px solid #ddd;">Confirmada</td>
    </tr>
  </table>

  <p>Te notificaremos cuando tu pedido sea enviado.</p>

  <p style="color: #888; font-size: 12px;">
    Este es un email automático del sistema de e-commerce — Tesis UTN FRM 2026
  </p>
</div>
```

**Después del envío — Actualizar `notified_at`** (nodo PostgreSQL adicional o incluido en un nodo posterior):

```sql
UPDATE orders
SET notified_at = NOW()
WHERE id = {{ $('Registrar Orden').item.json.order_id }}
RETURNING id AS order_id, notified_at;
```

**Evento `email_sent`**:

```sql
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
VALUES (
  {{ $('Registrar Orden').item.json.order_id }},
  'email_sent',
  'success',
  'Email de confirmación enviado a {{ $('Webhook - Recibir Orden').item.json.body.customer_email }}',
  jsonb_build_object(
    'to', '{{ $('Webhook - Recibir Orden').item.json.body.customer_email }}',
    'subject', 'Confirmación de Orden {{ $('Registrar Orden').item.json.order_number }}',
    'order_number', '{{ $('Registrar Orden').item.json.order_number }}'
  )
);
```

---

### Nodo 9: Marcar Sin Stock (rama No Stock)

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Marcar Sin Stock`                   |
| **Tipo n8n**    | `n8n-nodes-base.postgres`            |
| **Operación**   | Execute Query                        |
| **Credential**  | PostgreSQL (ecommerce_tesis)         |

**Descripción**: Cuando no hay stock suficiente, marca la orden como `no_stock`, registra `processed_at` y registra los eventos correspondientes.

**SQL Query — Actualizar orden**:

```sql
UPDATE orders
SET
  status = 'no_stock',
  processed_at = NOW()
WHERE id = {{ $('Registrar Orden').item.json.order_id }}
RETURNING id AS order_id, order_number, status, processed_at;
```

**SQL Query — Eventos**:

```sql
-- Evento stock_checked (resultado: sin stock)
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
VALUES (
  {{ $('Registrar Orden').item.json.order_id }},
  'stock_checked',
  'warning',
  'Stock insuficiente para {{ $json.sku }} — disponible: {{ $json.stock_actual }}, solicitado: {{ $json.cantidad_solicitada }}',
  jsonb_build_object(
    'sku', '{{ $json.sku }}',
    'stock_disponible', {{ $json.stock_actual }},
    'cantidad_solicitada', {{ $json.cantidad_solicitada }}
  )
);

-- Evento no_stock_alert
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
VALUES (
  {{ $('Registrar Orden').item.json.order_id }},
  'no_stock_alert',
  'warning',
  'ALERTA: Sin stock para {{ $json.sku }} — orden {{ $('Registrar Orden').item.json.order_number }} marcada como no_stock',
  jsonb_build_object(
    'sku', '{{ $json.sku }}',
    'order_number', '{{ $('Registrar Orden').item.json.order_number }}',
    'stock_disponible', {{ $json.stock_actual }},
    'cantidad_solicitada', {{ $json.cantidad_solicitada }}
  )
);
```

---

### Nodo 10: Enviar Email Sin Stock (rama No Stock)

| Propiedad       | Valor                                |
|-----------------|--------------------------------------|
| **Nombre**      | `Enviar Email Sin Stock`             |
| **Tipo n8n**    | `n8n-nodes-base.emailSend`           |
| **Credential**  | SMTP (Mailpit)                       |

**Campos del email**:

| Campo   | Valor                                                        |
|---------|--------------------------------------------------------------|
| From    | `tesis@ecommerce.local`                                      |
| To      | `{{ $('Webhook - Recibir Orden').item.json.body.customer_email }}` |
| Subject | `Orden {{ $('Registrar Orden').item.json.order_number }} — Producto sin stock` |
| HTML    | (ver template abajo)                                         |

**Template HTML del email**:

```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #c62828;">Aviso sobre tu orden</h2>

  <p>Hola <strong>{{ $('Webhook - Recibir Orden').item.json.body.customer_name }}</strong>,</p>

  <p>Lamentamos informarte que el producto solicitado no tiene stock disponible en este momento.</p>

  <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
    <tr style="background-color: #f5f5f5;">
      <td style="padding: 10px; border: 1px solid #ddd;"><strong>Número de orden</strong></td>
      <td style="padding: 10px; border: 1px solid #ddd;">{{ $('Registrar Orden').item.json.order_number }}</td>
    </tr>
    <tr>
      <td style="padding: 10px; border: 1px solid #ddd;"><strong>Producto</strong></td>
      <td style="padding: 10px; border: 1px solid #ddd;">{{ $('Verificar Stock').item.json.product_name }}</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
      <td style="padding: 10px; border: 1px solid #ddd;"><strong>Estado</strong></td>
      <td style="padding: 10px; border: 1px solid #ddd;">Sin stock</td>
    </tr>
  </table>

  <p>Nos pondremos en contacto contigo cuando el producto esté disponible nuevamente, o podés escribirnos para buscar una alternativa.</p>

  <p style="color: #888; font-size: 12px;">
    Este es un email automático del sistema de e-commerce — Tesis UTN FRM 2026
  </p>
</div>
```

**Después del envío — Actualizar `notified_at`**:

```sql
UPDATE orders
SET notified_at = NOW()
WHERE id = {{ $('Registrar Orden').item.json.order_id }}
RETURNING id AS order_id, notified_at;
```

---

### Nodo 11: Respuesta Webhook

| Propiedad       | Valor                                            |
|-----------------|--------------------------------------------------|
| **Nombre**      | `Respuesta Webhook`                              |
| **Tipo n8n**    | `n8n-nodes-base.respondToWebhook` (o `n8n-nodes-base.set` si se usa "Last Node" response mode) |

**Descripción**: Este es el último nodo del pipeline. Como el webhook está en modo "Last Node", el output de este nodo se devuelve como respuesta HTTP al caller.

Ambas ramas (stock OK y sin stock) convergen aquí. Se debe usar un nodo **Set** o **Code** que construya la respuesta final basándose en el status de la orden.

**Alternativa A — Usar nodo `Respond to Webhook`** (si se usa "When Called by Another Workflow" response mode, o si se quiere responder explícitamente):

**Respuesta para orden confirmada** (rama stock OK):

```json
{
  "success": true,
  "order_number": "{{ $('Registrar Orden').item.json.order_number }}",
  "status": "confirmed",
  "total_amount": {{ $('Registrar Orden').item.json.total_amount }},
  "message": "Orden procesada y confirmada. Email de confirmación enviado."
}
```

**Respuesta para orden sin stock** (rama no stock):

```json
{
  "success": true,
  "order_number": "{{ $('Registrar Orden').item.json.order_number }}",
  "status": "no_stock",
  "total_amount": {{ $('Registrar Orden').item.json.total_amount }},
  "message": "Producto sin stock disponible. Se notificó al cliente."
}
```

**Alternativa B — Usar un nodo `Code` para unificar la respuesta**:

```javascript
// Nodo Code — Construir respuesta final
const orderData = $('Registrar Orden').first().json;
const stockData = $('Verificar Stock').first().json;

const isConfirmed = stockData.stock_disponible;

return [{
  json: {
    success: true,
    order_number: orderData.order_number,
    status: isConfirmed ? 'confirmed' : 'no_stock',
    total_amount: orderData.total_amount,
    product: stockData.product_name,
    message: isConfirmed
      ? 'Orden procesada y confirmada. Email de confirmación enviado.'
      : 'Producto sin stock disponible. Se notificó al cliente.'
  }
}];
```

---

## 4. Diagrama de flujo del pipeline

```
                    ┌──────────────────────┐
                    │   Webhook - Recibir   │
                    │       Orden           │
                    │  POST /orden-nueva    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Registrar Orden     │
                    │  INSERT orders        │
                    │  status = 'pending'   │
                    │  + event:             │
                    │    order_received     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Verificar Stock     │
                    │  SELECT products      │
                    │  WHERE sku = ?        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  IF Stock Disponible  │
                    │  stock >= cantidad?   │
                    └────┬────────────┬────┘
                         │            │
                   TRUE  │            │  FALSE
                         ▼            ▼
          ┌──────────────────┐   ┌──────────────────┐
          │ Actualizar Stock │   │ Marcar Sin Stock  │
          │ UPDATE products  │   │ UPDATE orders     │
          │ stock = stock-n  │   │ status='no_stock' │
          │ status=          │   │ processed_at=NOW  │
          │  'processing'    │   │ + events:         │
          │ + events:        │   │  stock_checked    │
          │  stock_checked   │   │  no_stock_alert   │
          │  stock_updated   │   └────────┬─────────┘
          └────────┬─────────┘            │
                   │                      ▼
                   ▼             ┌──────────────────┐
          ┌──────────────────┐  │ Enviar Email      │
          │ Verificar Stock  │  │ Sin Stock         │
          │ Bajo             │  │ + notified_at     │
          │ stock < stock_   │  └────────┬─────────┘
          │ min?             │           │
          └───┬─────────┬────┘           │
              │         │                │
        TRUE  │   FALSE │                │
              ▼         │                │
   ┌────────────────┐   │                │
   │ Alerta Stock   │   │                │
   │ Bajo           │   │                │
   │ + event:       │   │                │
   │ low_stock_     │   │                │
   │ alert          │   │                │
   └───────┬────────┘   │                │
           │            │                │
           └─────┬──────┘                │
                 │                       │
                 ▼                       │
          ┌──────────────────┐           │
          │ Confirmar Orden  │           │
          │ UPDATE orders    │           │
          │ status=          │           │
          │  'confirmed'     │           │
          │ processed_at=NOW │           │
          │ + event:         │           │
          │  invoice_        │           │
          │  generated       │           │
          └────────┬─────────┘           │
                   │                     │
                   ▼                     │
          ┌──────────────────┐           │
          │ Enviar Email     │           │
          │ Confirmación     │           │
          │ SMTP → Mailpit   │           │
          │ + notified_at    │           │
          │ + event:         │           │
          │  email_sent      │           │
          └────────┬─────────┘           │
                   │                     │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │  Respuesta Webhook   │
                   │  JSON con status     │
                   │  de la orden         │
                   └──────────────────────┘
```

---

## 5. Event Logging

Cada paso del pipeline registra un evento en `pipeline_events`. La siguiente tabla resume todos los eventos posibles:

| Paso del pipeline      | `event_type`        | `status`  | Condición                          |
|------------------------|---------------------|-----------|------------------------------------|
| Registrar Orden        | `order_received`    | `success` | Siempre (al recibir la orden)      |
| Verificar Stock (OK)   | `stock_checked`     | `success` | Stock >= cantidad solicitada       |
| Verificar Stock (Fail) | `stock_checked`     | `warning` | Stock < cantidad solicitada        |
| Actualizar Stock       | `stock_updated`     | `success` | Después de descontar stock         |
| Alerta Stock Bajo      | `low_stock_alert`   | `warning` | stock_nuevo < stock_min            |
| Confirmar Orden        | `invoice_generated` | `success` | Orden confirmada                   |
| Enviar Email (OK)      | `email_sent`        | `success` | Email de confirmación enviado      |
| Sin Stock              | `no_stock_alert`    | `warning` | Producto sin stock suficiente      |
| Error (cualquier paso) | `error`             | `failure` | Excepción o fallo en cualquier nodo|

### Campos de cada evento

```sql
INSERT INTO pipeline_events (
  order_id,       -- FK a orders.id
  event_type,     -- uno de los valores de arriba
  status,         -- 'success' | 'failure' | 'warning'
  duration_ms,    -- (opcional) duración del paso en ms
  message,        -- descripción legible del evento
  metadata        -- JSONB con datos extra del paso
)
```

### Convención para `message`

Los mensajes deben ser descriptivos y contener los datos relevantes:
- `"Orden ORD-2026-0001 registrada con éxito — total: $1199.98"`
- `"Stock verificado para PROD-001 — disponible: 20, solicitado: 2"`
- `"Stock actualizado para PROD-001 — nuevo stock: 18"`
- `"ALERTA: Stock bajo para PROD-005 — stock actual: 2, mínimo: 2"`
- `"Orden ORD-2026-0001 confirmada — factura generada"`
- `"Email de confirmación enviado a maria@example.com"`
- `"ALERTA: Sin stock para PROD-001 — orden ORD-2026-0001 marcada como no_stock"`

---

## 6. Métricas — MTTD y MTTR

### Definiciones

| Métrica | Nombre completo         | Cálculo                                    | Significado                                   |
|---------|-------------------------|--------------------------------------------|-----------------------------------------------|
| MTTD    | Mean Time To Detect     | `processed_at - received_at`               | Tiempo desde que llega la orden hasta que el pipeline termina de procesarla (verificar stock, actualizar, confirmar) |
| MTTR    | Mean Time To Resolve    | `notified_at - processed_at`               | Tiempo desde que se procesó hasta que se notificó al cliente por email |
| Total   | End-to-end              | `notified_at - received_at`                | Tiempo total del pipeline completo            |

### Timestamps a registrar en `orders`

| Columna        | Cuándo se establece                               | Nodo responsable      |
|----------------|----------------------------------------------------|-----------------------|
| `received_at`  | Al crear la orden (INSERT) — usa `DEFAULT NOW()`   | Nodo 2: Registrar Orden |
| `processed_at` | Al confirmar la orden O al marcarla como sin stock  | Nodo 7: Confirmar Orden / Nodo 9: Marcar Sin Stock |
| `notified_at`  | Después de enviar el email (confirmación o sin stock) | Nodo 8 / Nodo 10 (post-email UPDATE) |

### Vista que calcula MTTD/MTTR

La vista `v_order_processing_time` (ya creada en `init.sql`) calcula estas métricas automáticamente:

```sql
SELECT
  order_number,
  status,
  mttd_seconds,
  mttr_seconds,
  total_seconds
FROM v_order_processing_time
ORDER BY received_at DESC;
```

### Vista de resumen diario

La vista `v_daily_order_summary` agrega los promedios por día:

```sql
SELECT
  fecha,
  total_ordenes,
  confirmadas,
  sin_stock,
  errores,
  ingresos_del_dia,
  avg_mttd_seg,
  avg_mttr_seg
FROM v_daily_order_summary;
```

### Visualización en Grafana

Crear un datasource PostgreSQL en Grafana (`localhost:5432`, `ecommerce_tesis`, `n8n_user`/`n8n_pass`) y usar estas queries para los paneles:

**Panel 1 — MTTD promedio** (Stat):
```sql
SELECT ROUND(AVG(mttd_seconds)::NUMERIC, 2) AS avg_mttd FROM v_order_processing_time;
```

**Panel 2 — MTTR promedio** (Stat):
```sql
SELECT ROUND(AVG(mttr_seconds)::NUMERIC, 2) AS avg_mttr FROM v_order_processing_time;
```

**Panel 3 — Órdenes por estado** (Pie chart):
```sql
SELECT status, COUNT(*) AS total FROM orders GROUP BY status;
```

**Panel 4 — Evolución diaria** (Time series):
```sql
SELECT fecha AS time, total_ordenes, confirmadas, sin_stock, errores FROM v_daily_order_summary;
```

---

## 7. Instrucciones de Testing

### Prerequisitos

1. Levantar la infraestructura:
   ```bash
   docker compose up -d
   ```

2. Verificar que todos los servicios estén corriendo:
   ```bash
   docker compose ps
   ```

3. Acceder a n8n (`http://localhost:5678`), importar/crear el workflow y **activarlo**.

### Test 1 — Orden exitosa (stock suficiente)

```bash
curl -X POST http://localhost:5678/webhook/orden-nueva \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORD-TEST-001",
    "customer_name": "María García",
    "customer_email": "maria@test.com",
    "customer_phone": "+5492614001234",
    "product_sku": "PROD-001",
    "quantity": 2
  }'
```

**Respuesta esperada**:
```json
{
  "success": true,
  "order_number": "ORD-TEST-001",
  "status": "confirmed",
  "total_amount": 1199.98,
  "message": "Orden procesada y confirmada. Email de confirmación enviado."
}
```

**Verificaciones**:
- Orden creada en `orders` con status `confirmed`, `received_at`, `processed_at` y `notified_at` no nulos.
- Stock de `PROD-001` decrementado de 20 a 18.
- 4 eventos en `pipeline_events`: `order_received`, `stock_checked`, `stock_updated`, `invoice_generated`, `email_sent`.
- Email visible en Mailpit (`http://localhost:8025`).

```bash
# Verificar en la BD
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis -c \
  "SELECT order_number, status, received_at, processed_at, notified_at FROM orders WHERE order_number = 'ORD-TEST-001';"

docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis -c \
  "SELECT stock FROM products WHERE sku = 'PROD-001';"

docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis -c \
  "SELECT event_type, status, message FROM pipeline_events ORDER BY created_at DESC LIMIT 10;"
```

### Test 2 — Orden sin stock

Primero, reducir el stock de un producto a 0:
```bash
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis -c \
  "UPDATE products SET stock = 1 WHERE sku = 'PROD-005';"
```

Luego enviar una orden que excede el stock:
```bash
curl -X POST http://localhost:5678/webhook/orden-nueva \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORD-TEST-002",
    "customer_name": "Juan Pérez",
    "customer_email": "juan@test.com",
    "customer_phone": "+5492614005678",
    "product_sku": "PROD-005",
    "quantity": 5
  }'
```

**Respuesta esperada**:
```json
{
  "success": true,
  "order_number": "ORD-TEST-002",
  "status": "no_stock",
  "total_amount": 1749.95,
  "message": "Producto sin stock disponible. Se notificó al cliente."
}
```

**Verificaciones**:
- Orden creada con status `no_stock`.
- Stock de `PROD-005` **no** decrementado (sigue en 1).
- Eventos: `order_received`, `stock_checked` (warning), `no_stock_alert`.
- Email de "sin stock" visible en Mailpit.

### Test 3 — Alerta de stock bajo

```bash
# Poner stock justo por encima del mínimo
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis -c \
  "UPDATE products SET stock = 4, stock_min = 3 WHERE sku = 'PROD-004';"

curl -X POST http://localhost:5678/webhook/orden-nueva \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORD-TEST-003",
    "customer_name": "Ana López",
    "customer_email": "ana@test.com",
    "customer_phone": "+5492614009876",
    "product_sku": "PROD-004",
    "quantity": 2
  }'
```

**Verificaciones**:
- Orden confirmada (stock 4 >= 2).
- Stock de `PROD-004` decrementado a 2.
- Evento `low_stock_alert` presente (2 < 3 = stock_min).

### Test 4 — Verificar métricas MTTD/MTTR

```bash
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis -c \
  "SELECT order_number, status, mttd_seconds, mttr_seconds, total_seconds FROM v_order_processing_time;"
```

### Test 5 — Múltiples órdenes (carga)

```bash
for i in $(seq 10 30); do
  curl -s -X POST http://localhost:5678/webhook/orden-nueva \
    -H "Content-Type: application/json" \
    -d "{
      \"order_number\": \"ORD-LOAD-$(printf '%03d' $i)\",
      \"customer_name\": \"Cliente Test $i\",
      \"customer_email\": \"cliente$i@test.com\",
      \"customer_phone\": \"+549261400$i\",
      \"product_sku\": \"PROD-002\",
      \"quantity\": 1
    }" &
done
wait
echo "Carga completada"
```

Después verificar:
```bash
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis -c \
  "SELECT * FROM v_daily_order_summary;"
```

---

## 8. Casos Borde

### 8.1 Producto SKU inválido (no existe en la BD)

**Escenario**: El payload contiene un `product_sku` que no existe en la tabla `products`.

**Comportamiento esperado**:
- El nodo "Registrar Orden" (Nodo 2) usa `INSERT ... SELECT FROM products WHERE sku = ?`. Si el SKU no existe, el SELECT devuelve 0 filas y el INSERT no inserta nada.
- El nodo debe detectar que no se insertó ninguna fila (resultado vacío) y retornar un error.

**Implementación recomendada**: Agregar un nodo **IF** después de "Registrar Orden" que verifique si `order_id` existe en el output. Si no existe, devolver error al webhook:

```json
{
  "success": false,
  "error": "INVALID_SKU",
  "message": "El producto con SKU 'PROD-999' no existe en el catálogo."
}
```

**Evento a registrar**: No se registra evento porque la orden no se creó (no hay `order_id`). Si se desea registrar un evento genérico de error, se necesita un mecanismo separado o un INSERT en `pipeline_events` con `order_id = NULL` (pero la FK lo impide — considerar hacer `order_id` nullable o usar una tabla de errores separada).

### 8.2 Orden duplicada (order_number ya existe)

**Escenario**: Se envía el mismo `order_number` dos veces.

**Comportamiento esperado**:
- PostgreSQL lanza un error por la constraint UNIQUE en `orders.order_number`.
- n8n captura el error del nodo PostgreSQL.

**Implementación recomendada**: Configurar el nodo "Registrar Orden" con **Error Handling = "Continue On Fail"** en n8n. Luego agregar un nodo IF que detecte el error y retorne:

```json
{
  "success": false,
  "error": "DUPLICATE_ORDER",
  "message": "La orden 'ORD-2026-0001' ya fue registrada anteriormente."
}
```

### 8.3 Cantidad = 0 o negativa

**Escenario**: El payload envía `quantity: 0` o `quantity: -1`.

**Comportamiento esperado**:
- PostgreSQL lanza error por la constraint `CHECK (quantity > 0)` en la tabla `orders`.
- n8n captura el error.

**Respuesta**:
```json
{
  "success": false,
  "error": "INVALID_QUANTITY",
  "message": "La cantidad debe ser un número entero mayor a 0."
}
```

### 8.4 Campos requeridos faltantes

**Escenario**: El payload no incluye `customer_email`, `product_sku`, etc.

**Comportamiento esperado**: Se puede agregar un nodo de validación después del webhook (nodo **IF** o **Code**) que verifique la presencia de todos los campos obligatorios antes de intentar insertar en la BD.

**Nodo de validación (opcional pero recomendado)**:

```javascript
// Nodo Code — Validar Payload
const body = $json.body;
const required = ['order_number', 'customer_name', 'customer_email', 'product_sku', 'quantity'];
const missing = required.filter(f => !body[f] && body[f] !== 0);

if (missing.length > 0) {
  return [{
    json: {
      valid: false,
      error: 'MISSING_FIELDS',
      message: `Campos requeridos faltantes: ${missing.join(', ')}`
    }
  }];
}

if (typeof body.quantity !== 'number' || body.quantity < 1 || !Number.isInteger(body.quantity)) {
  return [{
    json: {
      valid: false,
      error: 'INVALID_QUANTITY',
      message: 'El campo quantity debe ser un entero mayor a 0.'
    }
  }];
}

return [{ json: { valid: true, ...body } }];
```

### 8.5 Condición de carrera en stock (race condition)

**Escenario**: Dos órdenes llegan simultáneamente para el mismo producto con stock = 1.

**Comportamiento esperado**: La constraint `CHECK (stock >= 0)` en la tabla `products` previene que el stock quede negativo. Si la segunda orden intenta hacer `UPDATE products SET stock = stock - 1` y el stock ya es 0, PostgreSQL lanza un error de constraint.

**Mitigación adicional (opcional)**: Usar `SELECT ... FOR UPDATE` en la verificación de stock para bloquear la fila del producto hasta que la transacción complete:

```sql
SELECT id, stock, stock_min
FROM products
WHERE sku = '{{ $json.body.product_sku }}'
FOR UPDATE;
```

**Nota**: Esto solo funciona si la verificación y el UPDATE se ejecutan dentro de la misma transacción, lo cual depende de cómo n8n maneja las conexiones. En la práctica, para la demo de la tesis con volumen bajo, el CHECK constraint es suficiente.

### 8.6 Servicio SMTP (Mailpit) no disponible

**Escenario**: Mailpit no está corriendo cuando se intenta enviar el email.

**Comportamiento esperado**:
- El nodo de envío de email falla.
- La orden ya está confirmada en la BD (status `confirmed`, `processed_at` registrado).
- El `notified_at` no se actualiza.
- Se debe registrar un evento `error` en `pipeline_events`.

**Implementación**: Configurar error handling en el nodo de email. Si falla, registrar:

```sql
INSERT INTO pipeline_events (order_id, event_type, status, message, metadata)
VALUES (
  {{ order_id }},
  'error',
  'failure',
  'Error al enviar email de confirmación — SMTP no disponible',
  '{"error": "SMTP connection refused", "step": "email_sent"}'::jsonb
);
```

El webhook aún debe responder con el status de la orden (confirmada), indicando que el email falló:

```json
{
  "success": true,
  "order_number": "ORD-2026-0001",
  "status": "confirmed",
  "total_amount": 1199.98,
  "message": "Orden confirmada pero el email de notificación no pudo enviarse.",
  "warnings": ["EMAIL_SEND_FAILED"]
}
```

### 8.7 Base de datos no disponible

**Escenario**: PostgreSQL no está corriendo.

**Comportamiento esperado**: Todos los nodos PostgreSQL fallan. El webhook debe retornar un error 500 genérico. Como no hay `order_id`, no se pueden registrar eventos.

**Respuesta**:
```json
{
  "success": false,
  "error": "DATABASE_UNAVAILABLE",
  "message": "Error interno del sistema. Intente nuevamente más tarde."
}
```

---

## Apéndice A — Credencial PostgreSQL en n8n

Crear en n8n una credential de tipo **Postgres** con:

| Campo     | Valor               |
|-----------|---------------------|
| Host      | `postgres`          |
| Port      | `5432`              |
| Database  | `ecommerce_tesis`   |
| User      | `n8n_user`          |
| Password  | `n8n_pass`          |
| SSL       | Disabled            |

**Nota**: El host es `postgres` (nombre del servicio Docker), no `localhost`, porque n8n se ejecuta dentro de la red Docker.

## Apéndice B — Credencial SMTP en n8n

Crear en n8n una credential de tipo **SMTP** con:

| Campo    | Valor                    |
|----------|--------------------------|
| Host     | `mailpit`                |
| Port     | `1025`                   |
| SSL/TLS  | Disabled                 |
| User     | *(vacío)*                |
| Password | *(vacío)*                |

## Apéndice C — Resumen de nodos del workflow

| #  | Nombre del nodo             | Tipo n8n                         | Tabla afectada     |
|----|-----------------------------|----------------------------------|--------------------|
| 1  | Webhook - Recibir Orden     | `n8n-nodes-base.webhook`         | —                  |
| 2  | Registrar Orden             | `n8n-nodes-base.postgres`        | `orders`, `pipeline_events` |
| 3  | Verificar Stock             | `n8n-nodes-base.postgres`        | `products` (SELECT) |
| 4  | IF Stock Disponible         | `n8n-nodes-base.if`              | —                  |
| 5  | Actualizar Stock            | `n8n-nodes-base.postgres`        | `products`, `orders`, `pipeline_events` |
| 6  | Verificar Stock Bajo        | `n8n-nodes-base.if`              | —                  |
| 6a | Alerta Stock Bajo           | `n8n-nodes-base.postgres`        | `pipeline_events`  |
| 7  | Confirmar Orden             | `n8n-nodes-base.postgres`        | `orders`, `pipeline_events` |
| 8  | Enviar Email Confirmación   | `n8n-nodes-base.emailSend`       | —                  |
| 8a | Actualizar Notificación     | `n8n-nodes-base.postgres`        | `orders`, `pipeline_events` |
| 9  | Marcar Sin Stock            | `n8n-nodes-base.postgres`        | `orders`, `pipeline_events` |
| 10 | Enviar Email Sin Stock      | `n8n-nodes-base.emailSend`       | —                  |
| 10a| Actualizar Notificación     | `n8n-nodes-base.postgres`        | `orders`           |
| 11 | Respuesta Webhook           | `n8n-nodes-base.respondToWebhook` | —                 |
