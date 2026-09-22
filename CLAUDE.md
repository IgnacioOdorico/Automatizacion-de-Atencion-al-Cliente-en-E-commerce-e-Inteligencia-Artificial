# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este proyecto

Trabajo Final de Grado (UTN FRM 2026) — sistema de automatización del ciclo post-venta de un e-commerce, **orquestado con n8n**. La lógica de negocio del ciclo post-venta vive dentro de n8n, exportada como **workflows JSON** en `workflows/` (esa parte no tiene build ni test runner). Encima hay un **portal web del cliente** (`dashboard-web/` + `dashboard-api/`) que sí tiene build y tests propios (ver "Dashboard del cliente"). Lo que se versiona en este repo es:

- **Workflows n8n** (`workflows/*.json`) — la lógica real, se importa desde la UI de n8n.
- **Schema SQL** (`init_simple.sql`, `seed_expand.sql`) — tablas, vistas de métricas y datos seed.
- **Infra** (`docker-compose.yml`) — levanta 6 servicios: n8n, PostgreSQL, Mailpit, Grafana, `dashboard-api` y `dashboard-web`. Con `--profile tunnel` suma `webhook-gateway` (nginx, allowlist solo `POST /webhook/<uuid>/webhook`, config en `webhook-gateway/`) y `ngrok` para la URL pública de Telegram: `docs/TUNEL_TELEGRAM.md`. El Flujo 3 usa credenciales de n8n, no `$env` (bloqueado en n8n 2.x).
- **Dashboard del cliente** — `dashboard-api/` (FastAPI, pytest), `dashboard-web/` (React + Vite + TS, vitest), `migracion_dashboard_cliente.sql` y `seed_dashboard.sql` (tablas y cuenta demo), `demo_en_vivo.ps1` (dispara una orden en vivo), `SPEC_DASHBOARD_CLIENTE.md` (spec; su §10 lista los desvíos reales) y `openspec/` (propuesta, diseño y tareas).
- **Scripts de operación** (`backup.ps1`, `restore.ps1`) — PowerShell.
- **Docs** (`docs/`) — specs técnicas y la tesis.

Idioma del proyecto: español rioplatense (voseo). Mantenerlo en todo lo que se escriba.

## Arquitectura — dos flujos sobre una BD compartida

Todo corre en n8n (`tesis_n8n`) contra una única PostgreSQL (`ecommerce_tesis`). Ambos flujos comparten la misma BD, y ahí está el acoplamiento clave entre ellos:

**Flujo 1 — Pipeline de Órdenes** (`POST /webhook/orden-nueva`): webhook → registra orden → verifica stock → rama con stock (descuenta, confirma, email de confirmación) o sin stock (marca `no_stock`, email de aviso) → responde al webhook. Captura timestamps `received_at`/`processed_at`/`notified_at` en `orders` para calcular **MTTD** y **MTTR**.

**Flujo 2 — Chatbot Omnicanal IA** (triggers WhatsApp `/webhook/whatsapp`, Telegram, Gmail poll): normaliza el mensaje → inyecta FAQ como contexto → GPT-4o-mini clasifica intent (`FAQ`/`ESTADO_PEDIDO`/`RECLAMO`/`GENERAL`) y genera respuesta → enruta por intent (busca en `orders` o crea `ticket`) → responde por el mismo canal → registra en `interactions`. Captura `received_at`/`responded_at` para el **TMR**.

**Punto de unión:** cuando el chatbot recibe `ESTADO_PEDIDO`, consulta la tabla `orders` que escribe el Flujo 1. Una métrica (MTTD/MTTR/TMR) es el eje de la tesis y se visualiza en Grafana sobre las 6 vistas `v_*` (`v_metrics_summary`, `v_order_processing_time`, `v_chatbot_response_time`, `v_daily_order_summary`, `v_daily_chatbot_summary`, `v_chatbot_corpus`).

**Dashboard del cliente** (rama `feature/dashboard-cliente`): `dashboard-web` (nginx, `:8080`) → `/api` → `dashboard-api` (FastAPI, `:8000`) → la **misma** PostgreSQL. Lee `orders`, `tickets`, `products` y las vistas sin modificarlas, y agrega dos tablas propias: `client_accounts` y `channel_connections` (PK `SERIAL`; el canal Gmail se guarda como `email`). Ojo: `orders`/`tickets`/`products` **no tienen `client_account_id`** (un comercio por instalación), así que todas las cuentas ven los mismos pedidos; solo perfil y conexiones son por cuenta. El vínculo de Telegram usa un workflow aislado (`Flujo 3 — Telegram Vínculo de Cuenta.json`) con un bot dedicado que llama a `POST /connections/telegram/confirm` con el header `X-N8N-SECRET`.

## Variantes SIMPLE vs PRODUCCION

Cada flujo tiene dos archivos JSON:

- **SIMPLE / (sin sufijo)** — para demo local. Usa Mailpit como SMTP, sin APIs externas reales. **Son los que se activan** para presentar.
- **PRODUCCION** — usa OpenAI real, WhatsApp Business Cloud API, Telegram Bot, Gmail OAuth. Se importan pero **se dejan inactivos** (tienen placeholders como `PHONE_ID`, `TU_CHAT_ID` que hay que configurar).

Al editar lógica de un flujo, verificá si el cambio aplica a una variante o a ambas.

## Gotcha crítico: las specs describen un schema más rico que el desplegado

`docs/SPEC_FLUJO1_*.md` y `SPEC_FLUJO2_*.md` referencian columnas y tablas que **NO existen en el schema activo** (`init_simple.sql`):

| Las specs asumen | La realidad en `init_simple.sql` |
|---|---|
| Tabla `pipeline_events` (bitácora de eventos) | **No existe** |
| `interactions.metadata` (JSONB) | **No existe** (`orders.raw_payload` JSONB **sí** existe y lo puebla el Flujo 1) |
| `TIMESTAMPTZ` | `init_simple.sql` ya usa `TIMESTAMPTZ`; una instancia vieja pudo quedar con `TIMESTAMP` (`migracion_a12.sql`): la API serializa ISO 8601 UTC igual |
| Índices, extensiones, COMMENTs | No están |

`init_simple.sql` es la versión simplificada para la demo (lo dice su cabecera). Es la que monta `docker-compose.yml` (`/docker-entrypoint-initdb.d/01_init.sql`). El `init.sql` del README **ya no existe como archivo** (quedó un directorio vacío). **Antes de tocar SQL o un nodo que escriba a la BD, mirá `init_simple.sql`, no la spec** — si seguís la spec vas a referenciar `pipeline_events` y va a explotar.

## Conexiones dentro de Docker

n8n se comunica con los otros servicios por **nombre de servicio Docker**, no por `localhost`:
- PostgreSQL: host `postgres` (no `localhost`), puerto `5432`, BD `ecommerce_tesis`, user `n8n_user` / `n8n_pass`.
- SMTP (Mailpit): host `mailpit`, puerto `1025`, sin auth, sin TLS.
- `dashboard-api` es `dashboard-api:8000` y el portal `dashboard-web` (nginx) lo alcanza por ahí. Desde el host, PostgreSQL se publica en **`localhost:5433`** (no 5432), la API en `:8000` y el portal en `:8080`.

`localhost:5432`, `localhost:8025`, etc. son solo para acceder desde la máquina host (Grafana datasource, psql, navegador).

## Comandos

```powershell
# Levantar / detener todo
docker compose up -d
docker compose up -d --build dashboard-api dashboard-web   # tras cambiar código del dashboard
docker compose down                      # NO borra datos (volúmenes persisten)
docker compose logs -f n8n

# Crear schema (init_simple.sql también se auto-ejecuta en el primer arranque del volumen)
Get-Content init_simple.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
Get-Content seed_expand.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis

# Consola SQL
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis

# Backup / restore (incluye workflows y credenciales de n8n desde la BD)
.\backup.ps1                             # genera backups\<fecha>\
.\restore.ps1

# Ver métricas
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "SELECT * FROM v_metrics_summary;"
```

| Servicio | URL host | Credenciales |
|---|---|---|
| n8n | http://localhost:5678 | admin / admin123 |
| Grafana | http://localhost:3000 | admin / admin |
| Dashboard del cliente | http://localhost:8080 | cuenta demo del seed (ver `dashboard-web/README.md`) |
| Dashboard API | http://localhost:8000 | `/health`; `/docs` apagado (`DASHBOARD_ENABLE_DOCS=true`) |
| Mailpit (inbox) | http://localhost:8025 | — |
| PostgreSQL | localhost:5432 | n8n_user / n8n_pass |

## Dashboard del cliente — build, tests y seguridad

```powershell
cd dashboard-api; .venv\Scripts\python -m pytest -q     # integración contra la BD ecommerce_tesis_test (localhost:5433); se saltea si no está
cd dashboard-web; npm test; npm run build               # vitest + tsc --noEmit + vite build
cd dashboard-web; npm run dev                           # Vite en :5173 (proxy /api -> :8000)
```

- **La API es fail-closed**: sin `DASHBOARD_JWT_SECRET`, `DASHBOARD_N8N_SECRET` y `DASHBOARD_ENC_KEY` válidos en `.env` (>= 32 caracteres, no de ejemplo; la clave de cifrado debe ser una clave Fernet) no arranca. Los tests fijan valores propios en `tests/conftest.py`. Nunca commitear ni imprimir valores de `.env`.
- Variables nuevas por nombre: ver `.env.example` y la sección "Dashboard del cliente" del `README.md`.
- Los tests `pytest` truncan tablas: solo corren contra `ecommerce_tesis_test`, **nunca** contra `ecommerce_tesis` (ahí `orders`/`tickets` son evidencia medida de la tesis).
- `nginx.conf` + `security-headers.conf` mandan la CSP y demás headers: si el front pasa a cargar algo externo, ampliar la CSP a propósito (`nginxConf.test.ts` la guarda).
- **Monitoreo** (`/monitoreo`, API `/monitoring/*`, contratos en `docs/API_MONITOREO.md`): todo es de solo lectura. Lee `orders`/`interactions`/`tickets`/`stock_alerts` y, para la pestaña Workflow, las tablas **internas de n8n** (`workflow_entity`, `execution_entity`, `execution_data`, esquema de n8n 2.12.2; degrada con `available:false` si faltan). El grafo nunca devuelve `parameters`/`credentials` y la vista previa de salida se redacta. Los tests crean esas tablas de n8n solo en `ecommerce_tesis_test`; jamás escribas en la BD viva.
- **Métricas** (`/metricas`, API `/metrics/orders` y `/metrics/chatbot`, contratos en `docs/API_METRICAS.md`): reemplazo en vivo de los paneles de `grafana/dashboards/*.json`, calculado sobre `orders`/`interactions` en el momento en que se pide. **Nunca usa `v_chatbot_corpus`** (ventana congelada del 12/08 para el corpus del experimento, no algo "en vivo") ni replica el panel "Precisión (accuracy) 92.7%" de Grafana, que es un literal fijo en la consulta SQL, no una métrica calculada — se omite a propósito, decisión explícita del usuario.

## Testing del pipeline — es manual, disparando webhooks

Los Flujos 1 y 2 no tienen suite automatizada. Se prueban enviando requests a los webhooks y verificando BD + Mailpit:

```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook/orden-nueva" -Method POST `
  -ContentType "application/json" `
  -Body '{"order_number":"ORD-TEST-001","customer_name":"Test","customer_email":"t@t.com","customer_phone":"549...","product_sku":"PROD-001","quantity":1}'
```

El payload del Flujo 2 imita la estructura de la WhatsApp Cloud API (`entry[].changes[].value.messages[]`). Para forzar la rama "sin stock" del Flujo 1, pedí más unidades de las que hay en stock. El README tiene el catálogo de SKUs de prueba y ejemplos en PowerShell, curl y Postman.

## Flujo de trabajo al cambiar un workflow

1. Editás en la UI de n8n (http://localhost:5678), no el JSON a mano salvo cambios triviales.
2. Exportás el workflow actualizado a `workflows/` (Download / Export from file).
3. Para persistir credenciales/workflows fuera de la UI, corré `.\backup.ps1` (los lee desde las tablas `workflow_entity` / `credentials_entity` de la BD de n8n).

Las credenciales reales de n8n NO se versionan; `CREDENCIALES.example.md` es la guía de qué configurar.
