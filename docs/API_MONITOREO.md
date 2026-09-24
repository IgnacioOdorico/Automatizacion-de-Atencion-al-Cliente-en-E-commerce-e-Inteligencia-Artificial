# API de Monitoreo (`/monitoring/*`)

Contrato de los endpoints de la sección "Monitoreo" del portal. Todos son **GET, de solo lectura**, y requieren `Authorization: Bearer <JWT>` (sin token: `401`). La API devuelve datos **estructurados**: las etiquetas en español las pone el front. Los ejemplos están anonimizados.

Código: `dashboard-api/app/routers/monitoring_*.py` y `dashboard-api/app/core/`. Tests: `dashboard-api/tests/test_monitoring_*.py`.

## Convenciones

- **Fechas**: ISO 8601 en UTC con milisegundos y `Z` (`"2026-09-21T14:03:22.418Z"`).
- **Errores**: `{"detail": "<mensaje en español>"}`. `422` parámetro inválido (incluye cursores rotos y valores fuera de dominio), `404` recurso inexistente. Las tablas de n8n ausentes **no** dan 500: ver "Degradación".
- **Dominios cerrados**: `channel` = `whatsapp | telegram | email`; `data_source` = `measured | synthetic | e4_manual`; `intent` = `FAQ | ESTADO_PEDIDO | RECLAMO | GENERAL`; `severity` = `info | success | warning | error`.
- **`limit`**: entero de 1 a 100 (el default se indica en cada endpoint).
- **Cursores**: cadenas opacas (base64 url-safe). El front las guarda y las devuelve tal cual; no las interpreta. Un cursor de otro endpoint o alterado da `422`.
- **Un comercio por instalación**: como `orders`/`tickets`, el monitoreo no filtra por cuenta.
- **Degradación (n8n)**: las tablas `workflow_entity`, `execution_entity` y `execution_data` son internas de n8n 2.12.2. Si no existen o no se pueden leer, los endpoints de workflows/ejecuciones responden `200` con `available: false` y listas vacías (el grafo y la traza dan `404`).
- **Seguridad de los datos de n8n**: nunca se devuelven `parameters`, `credentials`, `webhookId`, notas, `stack` ni binarios. Todo texto que viene de n8n pasa por redacción: el valor de claves sensibles (`authorization`, `token`, `secret`, `password`, `api_key`, `cookie`, `set-cookie`, `x-n8n-secret`, `access_token`, `refresh_token`, `client_secret`, ..., sin distinguir mayúsculas y a cualquier profundidad) y todo lo que tenga forma de credencial (Bearer/Basic, JWT, `sk-…`, tokens de bot, hex/base64 largos) se reemplaza por `"[REDACTADO]"`.

---

## 1. Resumen — `GET /monitoring/summary`

Query: `hours` (1..168, default 24), `data_source` (opcional).

```json
{
  "window_hours": 24,
  "generated_at": "2026-09-21T14:05:00.120Z",
  "data_source": "all",
  "last_activity_at": "2026-09-21T14:03:22.418Z",
  "bot": {
    "interactions": 12,
    "avg_tmr_seconds": 3.42,
    "urgent": 1,
    "by_intent": { "FAQ": 5, "ESTADO_PEDIDO": 4, "RECLAMO": 2, "GENERAL": 1 },
    "by_channel": { "whatsapp": 7, "telegram": 5, "email": 0 }
  },
  "orders": {
    "total": 9,
    "by_status": { "pending": 0, "processing": 0, "confirmed": 7, "shipped": 0,
                   "delivered": 0, "no_stock": 2, "cancelled": 0, "error": 0 }
  },
  "tickets": { "created": 2, "open": 3,
               "by_priority": { "low": 0, "normal": 1, "high": 1, "urgent": 0 } },
  "stock_alerts": 1,
  "executions": { "available": true, "total": 21, "success": 19, "error": 2,
                  "last_error_at": "2026-09-21T13:40:01.000Z" }
}
```

- Se cuentan en la ventana: `bot.*` (por `received_at`), `orders.*` (por `received_at`), `tickets.created` y `tickets.by_priority` (por `created_at`) y `stock_alerts`. `tickets.open` es el **estado actual** (`open` + `in_progress`), sin ventana.
- `bot.avg_tmr_seconds`: `null` si no hubo respuestas. `by_intent`, `by_channel`, `by_status` y `by_priority` traen **siempre** todas las claves (con 0).
- `last_activity_at`: el evento más reciente de cualquier tabla de negocio, sin ventana (`null` si no hay datos). Coincide con el `ts` del primer evento del feed.
- `executions`: ejecuciones de n8n no borradas cuya fecha de inicio cae en la ventana; `error` cuenta `error` y `crashed`; `last_error_at` es la última falla **de siempre**. Sin tablas de n8n: `{"available": false, "total": 0, "success": 0, "error": 0, "last_error_at": null}`.

## 2. Feed de eventos — `GET /monitoring/events`

Query: `limit` (default 50), `before`, `since`, `types` (lista separada por comas), `channel`, `data_source`. `before` y `since` no se combinan (`422`).

```json
{
  "items": [ /* eventos, del más nuevo al más viejo */ ],
  "has_more": true,
  "newest_cursor": "eyJ…",
  "oldest_cursor": "eyJ…"
}
```

**Paginación (dos modos)**

- **Historial**: sin cursor devuelve los `limit` eventos más nuevos. Para ir hacia atrás, `before=<oldest_cursor>`. `has_more` = quedan eventos más viejos.
- **Polling incremental**: `since=<newest_cursor>` devuelve solo lo **posterior**, y si hay más de `limit` devuelve los `limit` **más viejos** posteriores (así nunca se salta uno). `has_more: true` = pedir de nuevo enseguida con el nuevo `newest_cursor`. Sin novedades: `items: []`, `has_more: false` y `newest_cursor` = el mismo `since` recibido.
- El orden es estable con timestamps empatados (desempata por tipo y por id): sin duplicados ni saltos.
- `newest_cursor`/`oldest_cursor` son `null` si no hay `items` (salvo el `since` de vuelta).

**Evento**

```json
{
  "id": "bot_reply:41",
  "type": "bot_reply",
  "ts": "2026-09-21T14:03:22.418Z",
  "channel": "telegram",
  "severity": "success",
  "data": { },
  "refs": { "order_id": 7, "order_number": "ORD-2026-0007", "interaction_id": 41, "ticket_id": null }
}
```

`id` = `<type>:<pk de la fila>` (único; sirve de key de React). `channel` es `null` en los eventos de pedidos y de stock. `refs` trae siempre las 4 claves (`null` si no aplica). Con `channel=` solo salen `chat_message`, `bot_reply` y `ticket_created` (los demás no tienen canal).

| `type` | `ts` | `data` | `severity` |
|---|---|---|---|
| `order_received` | `orders.received_at` | `order_number`, `customer_name`, `customer_email`, `quantity`, `total_amount` (número), `product_sku`, `product_name` | `info` |
| `order_processed` | `orders.processed_at` | `order_number`, `status` (estado actual de la orden), `total_amount`, `mttd_seconds` | `error` si `status=error`; `warning` si `no_stock`/`cancelled`; si no `success` |
| `order_notified` | `orders.notified_at` | `order_number`, `status`, `mttr_seconds` | `warning` si `no_stock`/`cancelled`/`error`; si no `success` |
| `chat_message` | `interactions.received_at` | `user_id`, `message` (texto exacto del cliente) | `info` |
| `bot_reply` | `interactions.responded_at` | `user_id`, `ai_response` (texto exacto), `intent`, `is_urgent`, `tmr_seconds` | `warning` si `is_urgent`; si no `success` |
| `ticket_created` | `tickets.created_at` | `user_id`, `subject`, `priority`, `status` | `error` si `urgent`; `warning` si `high`; si no `info` |
| `stock_alert` | `stock_alerts.created_at` | `sku`, `product_name`, `stock_actual`, `stock_min` | `error` si `stock_actual=0`; si no `warning` |

- Si `responded_at` es `NULL` no hay evento `bot_reply` (solo el `chat_message`). `mttd_seconds`/`mttr_seconds`/`tmr_seconds` son segundos con 3 decimales (`null` si falta alguna marca).
- `refs.ticket_id` de un mensaje/respuesta es el primer ticket asociado a esa interacción.

## 3. Conversaciones

### 3.1 `GET /monitoring/conversations`

Query: `limit` (default 20), `before`, `channel`, `q` (texto, máx. 100; busca sin distinguir mayúsculas en el mensaje, la respuesta y el `user_id`; `%` y `_` valen como texto literal), `data_source`.

```json
{
  "items": [
    {
      "channel": "whatsapp",
      "user_id": "5492610000000",
      "last_at": "2026-09-21T14:03:20.001Z",
      "messages": 4,
      "last_intent": "ESTADO_PEDIDO",
      "last_message_preview": "¿Dónde está mi pedido ORD-2026-0007?",
      "has_urgent": false,
      "open_tickets": 1
    }
  ],
  "has_more": false,
  "next_before": null
}
```

Un hilo = `(channel, user_id)`. Orden: `last_at` desc (con desempate estable). `last_at`, `last_intent` y `last_message_preview` son del mensaje **más reciente** del cliente; el preview se corta a 120 caracteres (119 + `…`). `open_tickets`: tickets `open`/`in_progress` del mismo canal y usuario. Siguiente página: `before=<next_before>` (`next_before` es `null` cuando `has_more` es `false`).

### 3.2 `GET /monitoring/conversations/thread`

Query: `channel` (obligatorio), `user_id` (obligatorio, 1..200; **por query**, puede traer `+`, `/`, espacios), `limit` (default 50), `before`. `404` (`"Conversación no encontrada"`) si ese canal + usuario no tiene mensajes.

```json
{
  "channel": "whatsapp",
  "user_id": "5492610000000",
  "items": [
    {
      "interaction_id": 41,
      "received_at": "2026-09-21T14:03:18.500Z",
      "message": "¿Dónde está mi pedido ORD-2026-0007?",
      "responded_at": "2026-09-21T14:03:22.418Z",
      "ai_response": "Tu pedido está confirmado y en preparación.",
      "intent": "ESTADO_PEDIDO",
      "is_urgent": false,
      "tmr_seconds": 3.918,
      "order": { "id": 7, "order_number": "ORD-2026-0007", "status": "confirmed" },
      "ticket": null
    }
  ],
  "has_more": true,
  "next_before": "eyJ…"
}
```

Sin cursor devuelve los `limit` mensajes **más nuevos**; `items` sale en **orden cronológico** (viejo → nuevo). Para cargar historia, `before=<next_before>` devuelve los `limit` anteriores (también en orden cronológico); `has_more` = quedan más viejos. `responded_at`, `tmr_seconds` son `null` si el bot aún no respondió. `order` y `ticket` son `null` si no hay vínculo.

## 4. Workflows de n8n

### 4.1 `GET /monitoring/workflows`

```json
{
  "available": true,
  "items": [
    {
      "id": "797bI0eXTmiaSmvJ",
      "name": "Flujo 1 — Pipeline de Procesamiento de Órdenes",
      "active": true,
      "updated_at": "2026-09-21T01:06:00.678Z",
      "executions_24h": 12,
      "errors_24h": 1,
      "last_execution": { "id": 15, "status": "success", "started_at": "2026-09-21T14:03:20.000Z", "duration_ms": 435 }
    }
  ]
}
```

Orden por nombre; sin workflows archivados. `errors_24h` cuenta `error` y `crashed`. `last_execution` es `null` si nunca corrió; `duration_ms` es `null` si no terminó. Sin tablas de n8n: `{"available": false, "items": []}`.

### 4.2 `GET /monitoring/workflows/{id}/graph`

`{id}`: hasta 36 caracteres `[A-Za-z0-9_-]` (`422` si no). `404` (`"Workflow no encontrado"`) si no existe o si n8n no está disponible.

```json
{
  "id": "797bI0eXTmiaSmvJ",
  "name": "Flujo 1 — Pipeline de Procesamiento de Órdenes",
  "active": true,
  "nodes": [
    { "name": "Webhook - Recibir Orden", "type": "n8n-nodes-base.webhook",
      "short_type": "webhook", "position": [-960, 144], "disabled": false }
  ],
  "edges": [
    { "from": "IF Stock Disponible", "to": "Actualizar Stock",
      "output_index": 0, "input_index": 0, "kind": "main" },
    { "from": "IF Stock Disponible", "to": "Marcar Sin Stock",
      "output_index": 1, "input_index": 0, "kind": "main" }
  ],
  "bounds": { "min_x": -960, "min_y": 0, "max_x": 1440, "max_y": 304 }
}
```

- `nodes[].position` son las coordenadas de n8n (pueden ser negativas); `bounds` es el rectángulo que las contiene (para el `viewBox`). `short_type` es la última parte de `type` (`webhook`, `postgres`, `if`, `emailSend`, `respondToWebhook`, `telegram`, `switch`, `chainLlm`, ...).
- `edges[].output_index` respeta las ramas: en un `if`, **0 = verdadero, 1 = falso**; en un `switch`, el índice de la regla. `kind` es `main` para el flujo de datos; los nodos de IA se enlazan con `ai_languageModel` u otros `ai_*` (la arista va del sub-nodo al nodo que lo usa).
- Las notas adhesivas (`stickyNote`) no aparecen.

### 4.3 `GET /monitoring/executions`

Query: `limit` (default 20), `before` (id de ejecución, entero ≥ 1: devuelve las de id menor), `status` (`canceled | crashed | error | new | running | success | unknown | waiting`), `workflow_id`. Se excluyen las ejecuciones borradas.

```json
{
  "available": true,
  "items": [
    {
      "id": 1,
      "workflow_id": "797bI0eXTmiaSmvJ",
      "workflow_name": "Flujo 1 — Pipeline de Procesamiento de Órdenes",
      "status": "error",
      "mode": "webhook",
      "started_at": "2026-09-21T01:06:41.028Z",
      "stopped_at": "2026-09-21T01:06:41.077Z",
      "duration_ms": 49,
      "error_message": "Credential with ID \"…\" does not exist for type \"postgres\"."
    }
  ],
  "has_more": false,
  "next_before": null
}
```

Orden por `id` desc. `next_before` es el `id` del último ítem cuando `has_more` es `true`. `error_message` solo se calcula para `error`/`crashed` (redactado, ≤ 300 caracteres); es `null` si no hay datos legibles o pesan más de 500 KB. `stopped_at`/`duration_ms` son `null` si no terminó. Sin tablas de n8n: `{"available": false, "items": [], "has_more": false, "next_before": null}`.

### 4.4 `GET /monitoring/executions/{id}`

`404` (`"Ejecución no encontrada"`) si no existe, fue borrada o n8n no está disponible.

```json
{
  "execution": { "id": 15, "workflow_id": "797bI0eXTmiaSmvJ", "workflow_name": "…", "status": "success",
                 "mode": "webhook", "started_at": "…", "stopped_at": "…", "duration_ms": 435, "error_message": null },
  "workflow_id": "797bI0eXTmiaSmvJ",
  "nodes": [
    {
      "name": "IF Stock Disponible",
      "short_type": "if",
      "status": "success",
      "started_at": "2026-09-21T14:03:20.055Z",
      "duration_ms": 1,
      "items_out": 1,
      "outputs": [1, 0],
      "runs": 1,
      "error": null,
      "output_preview": [ { "stock": 10 } ],
      "output_truncated": false
    },
    { "name": "Marcar Sin Stock", "short_type": "postgres", "status": "skipped",
      "started_at": null, "duration_ms": null, "items_out": 0, "outputs": [], "runs": 0,
      "error": null, "output_preview": null, "output_truncated": false }
  ],
  "path": ["Webhook - Recibir Orden", "Registrar Orden", "Verificar Stock", "IF Stock Disponible", "Actualizar Stock"],
  "last_node_executed": "Actualizar Stock",
  "truncated": false,
  "error": null
}
```

- **`nodes`**: todos los nodos del workflow **tal como estaba al ejecutarse** (si n8n no guardó esa instantánea, se usa el workflow actual), en el orden del workflow, más los que aparezcan en la ejecución y ya no existan en él (`short_type: null`). Se cruzan por `name` con el grafo de 4.2.
- **`status`**: `success | error | skipped` (`skipped` = no aparece en `runData`, o sea que esa rama no se ejecutó). Excepcionalmente `running | waiting | canceled` si la ejecución quedó a medias en ese nodo.
- **`outputs`**: cantidad de items por salida (`output_index`) de la **última corrida**; sirve para iluminar la rama: en el `if` de arriba `[1, 0]` = salió por la verdadera. `items_out` es la suma. `runs` = cuántas veces corrió el nodo (bucles); `duration_ms` suma todas las corridas y `started_at` es el de la primera.
- **`error`**: `{"message": "...", "description": "..." | null}` (redactado; `message` ≤ 500 y `description` ≤ 1000 caracteres). Nunca `stack`.
- **`output_preview`**: los `json` de los primeros items de salida, redactados y acotados a ~2 KB (`null` si el nodo no produjo salida). Normalmente es una lista JSON; en el peor caso de tamaño es un **texto** recortado que termina en `…`. `output_truncated: true` indica que se recortó (menos items, textos largos cortados en `…`, listas u objetos truncados).
- **`path`**: nombres de los nodos ejecutados, en orden de ejecución (por `executionIndex`).
- **`execution.error_message`**: el error a nivel de ejecución (o el del primer nodo que falló), redactado, ≤ 300 caracteres.
- **Casos límite** (siempre `200`):
  - `execution_data` con más de 2 MB: no se parsea. `truncated: true`, `nodes: []`, `path: []`.
  - JSON corrupto o sin fila en `execution_data`: `nodes: []`, `path: []` y `error` con un texto legible (`"No se pudo leer el detalle de la ejecución: los datos están corruptos"` / `"La ejecución no tiene datos de traza (¿fueron purgados?)"`).
  - Sin `runData`: todos los nodos `skipped` y `path: []` (`last_node_executed` es `null` salvo que n8n lo haya guardado).

## 5. Nota para el front

- Polling sugerido: `events?since=` cada 3 s; `summary` y `executions` cada 5–10 s; el grafo se pide una vez por workflow.
- Para iluminar el camino: para cada arista `e` del grafo, está recorrida si `trace.nodes[e.from].outputs[e.output_index] > 0` y el nodo `e.to` no es `skipped`.
- Las etiquetas humanas (por ejemplo "con stock" / "sin stock" para `output_index` 0/1 de `IF Stock Disponible`, o "TMR", "MTTD", "MTTR") son del front; la API solo entrega códigos y números.
