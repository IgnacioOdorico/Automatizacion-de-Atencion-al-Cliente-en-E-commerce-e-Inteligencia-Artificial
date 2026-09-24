# DESVIOS_SPEC — Fase 0 de exploración del repo vs. SPEC_DASHBOARD_CLIENTE.md

> **Proyecto**: Automatización del ciclo post-venta en e-commerce con IA (n8n) — UTN FRM 2026
> **Contexto**: Preparación para el dashboard cliente (React + FastAPI). NADA de producto se escribió acá; solo se relevó el repo y se documentaron las diferencias contra las specs.
> **Rama actual**: `main` (única rama local; la spec pide crear `feature/dashboard-cliente` recién en la Fase 1, no antes).
> **Fecha del relevamiento**: 2026-09-16

---

## 1. Resumen ejecutivo

Las **specs de flujo** (`docs/SPEC_FLUJO1_*`, `docs/SPEC_FLUJO2_*`) y el **README** describen un sistema que estuvo a medio camino entre lo diseñado y lo desplegado. El **repo real mandado** está más endurecido que esas specs (auditorías A-07/A-12) pero **NO** en todo: hay columnas `metadata` que el spec escribe y el schema no tiene, hay webhook de WhatsApp que la doc llama `/webhook/whatsapp` y el JSON real lo exporta como `/webhook/whatsapp-business`, y Postgres se publica en el host por el puerto **5433** (no 5432). Todo está detallado abajo con evidencia (`archivo:línea`).

Regla de oro que salvó el relevamiento: **lo que vale es `init_simple.sql` + `docker-compose.yml` + los JSON de `workflows/`**, no las specs. El agente del dashboard tiene que leer este archivo antes de tocar código.

---

## 2. Desvíos del spec (SPEC_DASHBOARD_CLIENTE.md contra el repo real)

### 2.1 Archivo que la spec asume y NO existe

| La spec dice | Realidad | Evidencia |
|---|---|---|
| Leer `docs/PROMPT_IA_CHATBOT.md` (§0.4, y el README lo lista en su árbol de archivos) | **No existe el archivo**. No hay `PROMPT_IA_CHATBOT.md` en `docs/`. Solo existe `docs/Prompt2_v2.docx` (posición directa del prompt GPT, sin formato markdown) | Glob `docs/PROMPT*` → sin resultados; README.md:516; SPEC_DASHBOARD_CLIENTE.md:18 |

**Implicancia**: el prompt del chatbot no tiene fuente markdown versionada. Si el dashboard quiere mostrar "el prompt que usa el bot", hay que reconstruirlo desde el nodo `IA - Motor Decision` del workflow (el prompt completo vive en `workflows/Flujo 2 — Chatbot WhatsApp + Telegram.json` nodo `IA - Motor Decision`).

### 2.2 Puerto de PostgreSQL en el host: la spec dice 5432, la realidad es 5433

| La spec asume | Realidad | Evidencia |
|---|---|---|
| Postgres accesible en `localhost:5432` (README.md:168, SPEC_FLUJO1:52) | `docker-compose.yml` publica **`5433:5432`** — el 5432 del host queda libre (supuestamente porque hay un Postgres nativo de Windows). Dentro de la red Docker el host es `postgres:5432` y eso NO cambia | docker-compose.yml:93 |

**Implicancia para el dashboard**:
- Primer servidor corriendo **dentro de `docker-compose.yml`** (`dashboard-api`): conectar a `postgres:5432` (red interna), igual que n8n/Grafana.
- API corriendo **en la máquina host** (dev rápido, Vite): conectar a `localhost:5433`, NO 5432.

### 2.3 Webhooks reales de n8n (paths exactos extraídos de los JSON)

| Fuente | Path | Evidencia |
|---|---|---|
| README.md:62 y SPEC_FLUJO1:67 — Flujo 1 | `/webhook/orden-nueva` | ✅ Coincide. `path: "orden-nueva"`, `httpMethod: POST`, `webhookId: "orden-nueva"`, `responseMode: "responseNode"` (responde por `respondToWebhook`, no "Last Node") en `workflows/Flujo 1 — Pipeline de Procesamiento de Órdenes.json:11-25` (idéntico en el PRODUCCION) |
| README.md:305, SPEC_FLUJO2:60 — Flujo 2 | `/webhook/whatsapp` | ❌ **El JSON real usa `whatsapp-business`**. En AMBOS workflows de Flujo 2 (SIMPLE y PRODUCCION): `path: "whatsapp-business"`, `httpMethod: POST`, `webhookId: "whatsapp-business-prod-001"` — `workflows/Flujo 2 — Chatbot WhatsApp + Telegram.json:71-85` y `workflows/Flujo 2 — Chatbot Omnicanal IA PRODUCCION.json:71-84` |

**Implicancia**: si el dashboard simula mensajes al chatbot (feature de demo), el endpoint es `POST http://localhost:5678/webhook/whatsapp-business`, no `/webhook/whatsapp`.

### 2.4 Formato de payload que espera el webhook de WhatsApp del Flujo 2

Los payloads de prueba del README (que imitan la envoltura de la WhatsApp Cloud API: `entry[].changes[].value.messages[]`) **NO los normaliza el nodo real** `Normalizar Mensaje`:

- SIMPLE (`Flujo 2 — Chatbot WhatsApp + Telegram.json:89`): `const w = src.body || src;` después lee `w.user_id || w.from || w.phone || w.user` y `w.message || w.text?.body`. Para un body tipo `{"entry":[{"changes":[...]}]}` → `user='unknown'`, `message=''` → el bot responde a un mensaje vacío.
- PRODUCCION (`Flujo 2 — Chatbot Omnicanal IA PRODUCCION.json:102`): igual, aunque detecta `data.entry` solo para decidir canal; con la envoltura Cloud API no extrae el texto anidado.

**Payload que el workflow SÍ entiende (plano)**:
```json
{ "from": "5492614002002", "text": { "body": "Hola, quiero saber el estado de ORD-HIST-002" }, "name": "Juan" }
```
o bien `{ "phone": "...", "message": "..." }`. Para Telegram, el trigger habla por sí solo (`update.message.chat.id`). **Recomendación**: el botón "simular mensaje" del dashboard debe usar la forma plana; y el README está desactualizado en este punto (verificar en ejecución antes del video).

### 2.5 El schema real NO coincide con las specs de flujo (y CLAUDE.md está parcialmente viejo)

| CLAUDE.md / SPects asumen | Schema real (`init_simple.sql`) | Evidencia |
|---|---|---|
| `pipeline_events` como bitácora (SPEC_FLUJO1 §5) | **No existe ni en schema ni en uso**: los workflows NO escriben ninguna tabla `pipeline_events`. La alerta de stock bajo va a **`stock_alerts`** | init_simple.sql (cabecera: "Sin tabla pipeline_events"); workflows Flujo 1: nodo `Registrar Alerta Stock Bajo` inserta en `stock_alerts` (Flujo 1.json:318-337) |
| `orders.raw_payload` "no existe" (CLAUDE.md gotcha) | **Sí existe** en el schema canónico: `orders(raw_payload JSONB)` y el workflow la puebla (`'{{ JSON.stringify($json.body) }}'::jsonb` — Flujo 1.json:30) | init_simple.sql:64; workflows/Flujo 1.json:30 |
| `TIMESTAMP` sin tz (CLAUDE.md gotcha) | `init_simple.sql` canónico usa **`TIMESTAMPTZ` en todas las marcas temporales** (A-12). OJO: `migracion_a12.sql:21-24` documenta que la **instancia de demo desplegada pre-auditoría** pudo quedar con `TIMESTAMP` (las 6 vistas dependen de esas columnas). Por eso el workflow inserta `received_at AT TIMESTAMP` (Flujo 2.json:376) | init_simple.sql:38,61-63,111-112,129-130; migracion_a12.sql:21-24 |
| `interactions.metadata` (SPEC_FLUJO2 §3.22/§6 inserta metadata) | **No existe la columna `metadata`** en `interactions`. Los workflows reales insertan sin metadata. Si el dashboard quiere trazabilidad de ejecución, no hay dónde leerla sin migración | init_simple.sql:100-115; workflows/Flujo 2.json:375-392 |
| 5 tablas (README.md:114) | Son **7**: `products, orders, order_items, stock_alerts, interactions, tickets, faq_responses`. El README no lista `order_items` ni `stock_alerts` | init_simple.sql:30-142 |
| 5 vistas (README.md:124) | Son **6**: se agrega `v_chatbot_corpus` (ventana fija del 2026-08-12 23:00–24:00, `data_source='measured'`) que alimenta paneles del corpus del Flujo 2 | init_simple.sql:303-317 |

### 2.6 Nodos de salida del Flujo 2: la spec describe envíos que NO existen en los JSON exportados

SPEC_FLUJO2 §3.19/§3.21 especifica `Enviar WhatsApp` (HTTP Request a `graph.facebook.com/v18.0/{{PHONE_ID}}/messages`) y `Enviar Gmail` (nodo `gmail`). **En NINGUNO de los dos workflows exportados hay un nodo de tipo `httpRequest` ni `gmail`**. La salida real es:

- **Telegram**: nodo `Enviar Telegram` (`n8n-nodes-base.telegram`, `chatId = {{ $json.user }}`) — solo en la variante SIMPLE vía `Router Canal` (IF `canal == telegram`).
- **Todo lo demás (incluido whatsapp y email)**: nodo `Enviar Respuesta (Producción)` (`n8n-nodes-base.emailSend` → SMTP, o sea **Mailpit**), en ambas variantes.

Evidencia: árbol de nodos de ambos JSON (no hay `httpRequest`/`gmail`); SIMPLE: `Flujo 2 — Chatbot WhatsApp + Telegram.json:350-372,428-446`; PRODUCCION: `Flujo 2 — Chatbot Omnicanal IA PRODUCCION.json:361-384`.

**Implicancia**: el dashboard NO puede asumir que "responder por WhatsApp/Gmail" pase por APIs reales. Hoy responde por email (SMTP local). Si el video necesita mostrar respuesta de WhatsApp real, hay que implementarla en el dashboard (o ampliar el workflow en la Fase 3, lo cual está FUERA del Fase 0).

### 2.7 Tabla `order_items` y backfill

`migracion_a12.sql:67-88` agrega `order_items` (N ítems por orden) y hace backfill de 1 ítem por orden existente. `orders.product_id`/`quantity` se **conservan** por compatibilidad con los workflows actuales (que solo crean órdenes mono-producto). **Implicancia**: el dashboard de "Pedidos" puede mostrar productos vía `order_items` (correcto a futuro) o vía el `INNER JOIN products` por `orders.product_id` (equivalente hoy, porque el flujo es mono-producto). No romper la compatibilidad: los workflows siguen escribiendo SOLO en `orders`/`products`/`stock_alerts`/`interactions`/`tickets`.

### 2.8 Convención de canales: `email` vs `gmail`

- `interactions.channel` y `tickets.channel` tienen `CHECK (channel IN ('whatsapp','telegram','email'))` — init_simple.sql:102-103 y 121-122.
- La spec del dashboard (§3) define `channel_connections.channel CHECK IN ('whatsapp','telegram','gmail')`.

**Hay que unificar** (o mapear en la UI). Coherente con el schema real: usar `email` como valor de canal en la BD y `gmail` solo como etiqueta visual, o sumar `'email'` al CHECK de `channel_connections`.

### 2.9 Nombres de archivos de workflows: el README no coincide

El README (líneas 200-205) cita archivos que **no existen con ese nombre** (p.ej. `Flujo 1 - Pipeline de Procesamiento de Órdenes SIMPLE.json`, `Flujo 2 - Chatbot Omnicanal IA.json`). Los archivos reales en `workflows/`:

- `Flujo 1 — Pipeline de Procesamiento de Órdenes.json` (demo local, activar)
- `Flujo 1 — Pipeline de Procesamiento de Órdenes PRODUCCION.json` (inactivo; triggers WooCommerce/Shopify disabled)
- `Flujo 2 — Chatbot WhatsApp + Telegram.json` (demo local — pese al nombre, el sticky note interno dice "PRODUCCIÓN — Canales Reales"; es la variante a activar con Mailpit)
- `Flujo 2 — Chatbot Omnicanal IA PRODUCCION.json`

NOTA: los archivos exportados traen `"active": false` (Flujo 1.json:7); la activación se hace en la UI de n8n, no en el JSON.

### 2.10 Flujo 1 PRODUCCION: "Normalizar Fuente" roto en el export

El nodo `[PROD] Normalizar Fuente` (PRODUCCION.json:295-308) tiene `functionCode` con sintaxis inválida (`const raw = \;` — backslashes sueltos del export). Está `disabled: true` y su nota aclara que es "adaptar según plataforma". No afecta la demo, pero si algún día se activa PRODUCCION hay que reescribir ese nodo.

### 2.11 Modelo de datos nuevo de la spec: no existe (esperado) y un matiz

`client_accounts` y `channel_connections` aún NO existen en el schema — correcto, la spec los pide crear en la Fase 1. Matices a tener en cuenta al crearlos:

- `gen_random_uuid()` está integrado desde PG 13 (imagen `postgres:15.13-alpine`), funciona sin extensiones. ✅
- La spec usa TIMESTAMPTZ: coherente con el schema canónico. ✅
- `channel_connections.external_reference` es la columna pensada para guardar `chat_id` de Telegram / email autorizado: el endpoint `/connections/telegram/confirm` (secreto compartido en header, §6) debería escribir exactamente eso.

### 2.12 Clearning de datos sintéticos: `data_source`

`orders`, `interactions`, `tickets`, `stock_alerts` tienen `data_source` (`'measured'`, `'synthetic'`, y `'e4_manual'` solo en orders — init_simple.sql:65-66). El seed histórico sintético NO debe ejecutarse (`seed_expand.sql` está **congelado**, cabecera 2026-08-09: contiene TRUNCATE y destruiría la evidencia medida). Para reponer el catálogo (productos + FAQs) se usa **`seed_catalogo.sql`** (idempotente, solo catálogo). El dashboard, si quiere métricas "honestas", puede filtrar por `data_source='measured'`; para la demo probablemente muestre todo.

---

## 3. Hechos verificados (inventario para el dashboard)

### 3.1 Tablas disponibles (schema canónico `init_simple.sql`)

| Tabla | Columnas clave | Notas |
|---|---|---|
| `products` | `id, sku (UNIQUE), name, price DECIMAL(10,2), stock INT CHECK>=0, stock_min INT DEFAULT 5, category, created_at` | 20 productos tras `seed_catalogo.sql` (8 base + 12 extra) |
| `orders` | `id, order_number (UNIQUE), customer_name, customer_email, customer_phone (nullable), product_id (FK nullable), quantity CHECK>0, total_amount, status CHECK('pending','processing','confirmed','shipped','delivered','no_stock','cancelled','error'), received_at, processed_at, notified_at, raw_payload JSONB, data_source` | Escrita por Flujo 1. Timestamps del pipeline completos solo en órdenes procesadas |
| `order_items` | `id, order_id (FK CASCADE), product_id (FK), quantity, unit_price, subtotal (GENERATED)` | Añadida por migración A-12; backfill 1 ítem/orden |
| `stock_alerts` | `id, product_id (FK), order_id (FK SET NULL), sku, stock_actual, stock_min, created_at, data_source` | Destino de la alerta de stock bajo (donde la spec imaginaba `pipeline_events.low_stock_alert`) |
| `interactions` | `id, channel CHECK('whatsapp','telegram','email'), user_id, message, intent CHECK('FAQ','ESTADO_PEDIDO','RECLAMO','GENERAL'), ai_response, order_id (FK SET NULL), is_urgent BOOL, received_at, responded_at, data_source` | Escrita por Flujo 2. **Sin columna `metadata`** |
| `tickets` | `id, interaction_id (FK SET NULL), order_id (FK SET NULL), channel CHECK, user_id, subject, status CHECK('open','in_progress','resolved','closed'), priority CHECK('low','normal','high','urgent'), created_at, resolved_at, data_source` | Creados por Flujo 2 (intent RECLAMO). `resolved_at` sin UPDATE en el workflow (queda NULL) |
| `faq_responses` | `id, question, answer, category, enabled BOOL DEFAULT TRUE, created_at` | 22 FAQs tras seed de catálogo |

Índices existentes (todos cubren queries de las vistas y de los flujos): `idx_orders_status, idx_orders_source_received, idx_order_items_order_id, idx_order_items_product_id, idx_stock_alerts_product, idx_stock_alerts_created, idx_interactions_intent, idx_interactions_channel_received, idx_interactions_source, idx_interactions_order_id, idx_tickets_order_id, idx_tickets_status`. NO hay índices para `orders.customer_email`/`customer_phone` ni `orders.order_number` (este último es UNIQUE, implica índice).

### 3.2 Vistas disponibles (6)

| Vista | Columnas |
|---|---|
| `v_order_processing_time` | `id, order_number, customer_email, status, received_at, processed_at, notified_at, mttd_seconds, mttr_seconds, total_seconds` (solo si `processed_at IS NOT NULL`) |
| `v_daily_order_summary` | `fecha, total_ordenes, confirmadas, enviadas, entregadas, sin_stock, errores, ingresos_del_dia, avg_mttd_seg, avg_mttr_seg` |
| `v_chatbot_response_time` | `id, channel, user_id, intent, received_at, responded_at, tmr_seconds, is_urgent` (solo si `responded_at IS NOT NULL`) |
| `v_daily_chatbot_summary` | `fecha, total_interacciones, faq, estado_pedido, reclamos, general, via_whatsapp, via_telegram, via_email, avg_tmr_seg, urgentes` |
| `v_metrics_summary` | `total_orders, orders_confirmed, avg_mttd_seg, avg_mttr_seg, total_interactions, avg_tmr_seg, total_tickets, tickets_resolved` |
| `v_chatbot_corpus` | `id, channel, user_id, intent, received_at, responded_at, tmr_seconds, is_urgent` — filtrada a `data_source='measured'` y ventana `2026-08-12 23:00–24:00` |

**Para `GET /dashboard/summary` lo más simple y consistente con Grafana es leer `v_metrics_summary`** (los promedios MTTD/MTTR/TMR YA están calculados) y complementar con `orders`/`tickets` para "pedidos hoy" y "tickets abiertos".

### 3.3 Webhooks reales (paths exactos)

| Workflow | Método | Path | Respuesta |
|---|---|---|---|
| Flujo 1 (SIMPLE y PRODUCCION) | POST | `/webhook/orden-nueva` | `{success, order_number, status, total_amount, message}` (dos nodos `respondToWebhook`: "Respuesta Confirmada" / "Respuesta Sin Stock") — Flujo 1.json:189-201,248-261 |
| Flujo 2 (SIMPLE y PRODUCCION) | POST | `/webhook/whatsapp-business` | Sin `respondToWebhook`: el flujo responde por canal (Telegram node o emailSend SMTP). La PASTA del webhook responde `200` genérico de n8n |
| Flujo 2 | Telegram | trigger nativo (`telegramTrigger`) — requiere `WEBHOOK_URL` pública HTTPS (ngrok) | — |
| Flujo 2 | Gmail | trigger nativo (`gmailTrigger`, poll cada minuto) | — |

Payload de entrada del webhook Flujo 1: `{order_number, customer_name, customer_email, customer_phone, product_sku, quantity}` (Flujo 1.json nodo `Registrar Orden` lee `$json.body.*`). El nodo `Registrar Orden` hace `INSERT ... SELECT FROM products WHERE sku = ...`; si el SKU no existe, no inserta nada (sin `order_id`, el pipeline falla aguas abajo).

### 3.4 docker-compose.yml — servicios, puertos, credenciales, red

| Servicio (container_name) | Imagen | Puertos host→contenedor | Créditos/env |
|---|---|---|---|
| `n8n` (`tesis_n8n`) | `n8nio/n8n:2.12.2` | `5678:5678` | basic auth admin / `${N8N_PASSWORD:-admin123}`; BD `postgres` `5432` BD `ecommerce_tesis` user `n8n_user` pass `${POSTGRES_PASSWORD:-n8n_pass}`; SMTP `mailpit:1025` SSL=false STARTTLS=false; **requiere `N8N_ENCRYPTION_KEY`** (`${N8N_ENCRYPTION_KEY:?definir en .env}` — sin `.env` el compose NO arranca) |
| `postgres` (`tesis_postgres`) | `postgres:15.13-alpine` | **`5433:5432`** | `POSTGRES_DB=ecommerce_tesis`, `POSTGRES_USER=n8n_user`, pass `${POSTGRES_PASSWORD:-n8n_pass}`; monta `./init_simple.sql` como `/docker-entrypoint-initdb.d/01_init.sql` (se ejecuta SOLO en el primer arranque del volumen); healthcheck `pg_isready` |
| `mailpit` (`tesis_mailpit`) | `axllent/mailpit:v1.29.6` | `8025:8025` (UI web), `1025:1025` (SMTP) | sin auth |
| `grafana` (`tesis_grafana`) | `grafana/grafana:13.0.7` | `3000:3000` | `GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}`; datasource Postgres interno `postgres:5432` |

Red interna: `tesis_network` (bridge). Volúmenes: `n8n_data`, `pg_data`, `grafana_data`. **Los nombres de red/volúmenes NO llevan prefijo** → el servicio `dashboard-api` nuevo debe sumarse a `tesis_network` para ver `postgres` por nombre.

`WEBHOOK_URL` default `http://localhost:5678/` (reiniciar n8n con ngrok para Telegram). Timezone: `America/Argentina/Mendoza`.

### 3.5 Archivos seed (leer antes de poblar)

- `seed_catalogo.sql` — **el único seguro**: productos + FAQs, `ON CONFLICT DO NOTHING`, sin TRUNCATE. Resultado: 20 productos, 22 FAQs.
- `seed_expand.sql` — **CONGELADO / NO EJECUTAR** (cabecera 2026-08-09): contiene `TRUNCATE ... RESTART IDENTITY CASCADE` que destruye la evidencia medida; sus filas son sintéticas.
- migraciones: `migracion_a07.sql` (crea `stock_alerts` — ya integrada en `init_simple.sql`) y `migracion_a12.sql` (índices + `order_items` + backfill).

### 3.6 Variables de entorno

`.env` NO se versiona (`.gitignore:7-9`). Plantilla `.env.example` con: `N8N_ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, `N8N_PASSWORD`, `GRAFANA_PASSWORD`, `WEBHOOK_URL`. **Los nuevos servicios del dashboard deben sumar sus vars con default `${VAR:-valor}` para no romper el arranque de los servicios existentes**, y documentarlas en `.env.example`.

---

## 4. Recomendaciones para el dashboard

1. **Conectar a `postgres:5432` si el API corre como service de compose; `localhost:5433` si corre en el host.** Nunca `localhost:5432` (ahí está un Postgres nativo de Windows o nada).
2. **No usar `pipeline_events` para nada** (no existe). La alerta de stock bajo se lee de `stock_alerts`.
3. **Leer el resumen de métricas desde `v_metrics_summary`** (MTTD/MTTR/TMR ya promediados) en vez de recalcular promedios en FastAPI.
4. **`tickets.resolved_at` queda NULL siempre** (el workflow no lo toca). La página de Tickets no debe asumir que `resolved_at` está poblado; derivar "resuelto" de `status='resolved'`.
5. **Timestamps: el canónico es TIMESTAMPTZ, pero la instancia desplegada puede ser TIMESTAMP** (nota de `migracion_a12.sql:21-24`). Al serializar en la API, devolver ISO string y NO asumir zona horaria; si se hace aritmética de fechas en SQL, usar `AT TIME ZONE` explícito. Antes de la demo, verificar con `\d orders` qué tipo tiene la instancia real.
6. **`interactions` NO tiene `metadata`**: no prometer trazabilidad por `$execution.id`. Si la spec/demo lo exige, es una migración nueva (permitida, solo agregar).
7. **Unificar `email` vs `gmail`** en el dominio de canales (BD: `email` por el CHECK; UI: etiqueta "Gmail").
8. **Webhook de simulación del Flujo 2 → `/webhook/whatsapp-business` con payload plano** (`{from, text:{body}, name}`), no la envoltura de la Cloud API del README.
9. **`seed_expand.sql` está congelado**: para regenerar datos de orders/interactions/tickets usar los experimentos de `experiments/` (o disparar los webhooks), nunca el seed viejo. El dashboard puede filtrar `data_source='measured'` si quiere solo evidencia real.
10. **No tocar** tablas/columnas existentes; solo agregar (client_accounts, channel_connections, y lo que haga falta). Los workflows de n8n quedan intactos.
11. **Base para la rama: `main`** (confirmada como única rama local y remota). Crear `feature/dashboard-cliente` recién en la Fase 1 de la spec.

---

## 5. Fuentes consultadas

- `README.md`, `CLAUDE.md` (raíz)
- `SPEC_DASHBOARD_CLIENTE.md` (raíz) — secciones 0-8
- `docs/SPEC_FLUJO1_PIPELINE_ORDENES.md`, `docs/SPEC_FLUJO2_CHATBOT_OMNICANAL.md`
- `workflows/Flujo 1 — Pipeline de Procesamiento de Órdenes.json` y su `PRODUCCION`
- `workflows/Flujo 2 — Chatbot WhatsApp + Telegram.json` y su `Flujo 2 — Chatbot Omnicanal IA PRODUCCION.json`
- `init_simple.sql`, `seed_expand.sql`, `seed_catalogo.sql`, `migracion_a07.sql`, `migracion_a12.sql`
- `docker-compose.yml`, `.env.example`, `.gitignore`