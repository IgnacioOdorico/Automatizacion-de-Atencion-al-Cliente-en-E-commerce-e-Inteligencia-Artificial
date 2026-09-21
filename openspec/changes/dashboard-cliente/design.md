# Diseño — Dashboard Cliente + Conexiones

## Context

Los Flujos 1 y 2 de n8n ya escriben sus datos en una única PostgreSQL (`ecommerce_tesis`, host `postgres:5432` dentro de `tesis_network`; publicado en el host como `localhost:5433`). El schema real (`init_simple.sql`) tiene **7 tablas** (`products, orders, order_items, stock_alerts, interactions, tickets, faq_responses`) y **6 vistas** de métricas (`v_metrics_summary`, `v_daily_order_summary`, `v_order_processing_time`, `v_chatbot_response_time`, `v_daily_chatbot_summary`, `v_chatbot_corpus`). Nada de esto se modifica: solo se **agrega** el layer de dashboard.

Convenciones del repo que gobiernan el diseño (verificadas en `init_simple.sql` y `docker-compose.yml`):
- **PK con `SERIAL INTEGER`** (no UUID) en todas las tablas.
- **`TIMESTAMPTZ`** como tipo canónico de marcas temporales (la instancia desplegada pre-auditoría puede ser `TIMESTAMP`; se verifica en Fase 2 y se maneja serializando ISO string).
- Dominio de canales **`('whatsapp','telegram','email')`** (CHECK en `interactions.channel` y `tickets.channel`).
- `.env` no versionado; compostes usan la forma `${VAR:-default}` para no romper el arranque de los servicios existentes.
- `seed_expand.sql` congelado; se usa `seed_catalogo.sql` para catálogo y un seed nuevo para el dashboard.
- Sin build/test runner: se valida a mano con webhooks + psql.

## Goals / Non-Goals

**Goals:**
- Cara visible tipo SaaS para el cliente PyME: login, dashboard de métricas, pedidos, tickets, catálogo, conexiones de canal, perfil.
- Backend FastAPI que lee las vistas reales (no recalcula métricas) y las tablas existentes sin tocarlas.
- Conexiones honestas: Telegram real por código de 6 dígitos, Gmail OAuth2 real, WhatsApp con flujo de solicitud que queda en `pending` (comportamiento real de Meta).
- Seguridad completa de la §6 de la spec (bcrypt, JWT+refresh, encriptado, CORS, rate limiting, secreto compartido).
- Correr dentro del mismo `docker-compose.yml` (servicios `dashboard-api` y `dashboard-web`).

**Non-Goals:**
- Rol admin de plataforma ni multi-tenant visible.
- Chat widget propio (la demo usa WhatsApp/Telegram reales).
- Suite de tests automatizada (se valida manualmente).
- Pagos/facturación.
- Modificar los workflows de n8n existentes (solo se **agrega** un workflow aislado de vinculación de Telegram).

## Decisions

### 1. Estructura de backend — FastAPI con routers y sin ORM pesado
`dashboard-api/` con FastAPI + Uvicorn, un router por recurso: `auth.py`, `dashboard.py`, `orders.py`, `tickets.py`, `products.py`, `connections.py`. Conexión a Postgres por **SQLAlchemy 2.0 (engine) + queries `text()`** para las vistas y tablas de lectura; las dos tablas nuevas se manejan con SQLAlchemy Core (o `text()` directo) — no se necesita ORM completo para un dashboard de lectura. Se eligió SQLAlchemy sobre psycopg puro para parametrizar queries sin concatenar strings (seguridad, inyección SQL), y sobre ORM pesado porque el modelo ya vive en SQL (las vistas son la fuente de verdad de métricas).
- **Alternativas descartadas**: ORM completo (el schema ya está definido, duplicaría el modelo y agrega migraciones), psycopg a pelo (sin parametrización cómoda).

### 2. Estructura de frontend — React Vite + TS, servido por nginx
`dashboard-web/` con Vite + TypeScript. `react-router-dom` para el ruteo (ruta protegida wrapper), **TanStack Query** para las lecturas y el polling (elige `refetchInterval` de 4s en dashboard/pedidos en vez de timers manuales). Estilos: CSS modules + variables CSS para la paleta (1 color de marca + escala de grises, tipografía Inter). Build de producción → `vite build` → servido por **nginx alpine**; en dev se corre Vite standalone (`localhost:5173`) contra el API en `localhost:8000`.
- nginx (imagen de producción) **proxy-reverse `/api/` → `dashboard-api:8000`**: elimina CORS en la ruta servida. En dev la API igualmente respeta whitelist CORS (`http://localhost:5173`).

### 3. `docker-compose.yml` — dos servicios nuevos, cero rompimiento
- `dashboard-api`: build `./dashboard-api`, `container_name: tesis_dashboard_api`, puerto `8000:8000`, en `tesis_network` (ve `postgres:5432` interno), env desde `.env` con defaults `${VAR:-...}`.
- `dashboard-web`: build `./dashboard-web`, `container_name: tesis_dashboard_web`, puerto `8080:80` (Grafana ya usa 3000; n8n 5678), nginx sirve el build estático + proxya `/api`.
- Todo secret con `${VAR:?definir en .env}` o `${VAR:-default}`; **nada hardcodeado**. `.env.example` se amplía con las nuevas variables documentadas.
- Se agrega `STACK_*` no; se mantienen los nombres sin prefijo (`tesis_network`) para no perder la red existente.

### 4. Tablas nuevas — convenciones del repo (NO la forma de la spec)
Se agrega `migracion_dashboard_cliente.sql` con:

```sql
CREATE TABLE IF NOT EXISTS client_accounts (
    id              SERIAL PRIMARY KEY,
    business_name   TEXT            NOT NULL,
    email           TEXT            UNIQUE NOT NULL,
    password_hash   TEXT            NOT NULL,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS channel_connections (
    id                  SERIAL PRIMARY KEY,
    client_account_id   INTEGER NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    channel             VARCHAR(20) NOT NULL
                        CHECK (channel IN ('whatsapp', 'telegram', 'email')),
    status              VARCHAR(20) NOT NULL DEFAULT 'disconnected'
                        CHECK (status IN ('disconnected', 'pending', 'connected', 'error')),
    external_reference  TEXT,
    connected_at        TIMESTAMPTZ,
    encrypted_credentials TEXT,
    UNIQUE (client_account_id, channel)
);
CREATE INDEX IF NOT EXISTS idx_channel_connections_account ON channel_connections (client_account_id);
```

**Desvíos respecto a la §3 de la spec (documentados):** PK `SERIAL` en vez de UUID (convención del repo y de los FKs que referencian `client_accounts`), `TIMESTAMPTZ` (canónico del repo), `channel IN ('whatsapp','telegram','email')` en vez de `'gmail'` (ver decisión 5). `gen_random_uuid()` no se usa; siguen el patrón de `orders`/`interactions`.

### 5. Dominio de canales: BD `email`, etiqueta UI "Gmail" — DECISIÓN CLAVE
Unificar el dominio al valor que ya existe: **en BD se guarda `'email'`** en `channel_connections.channel` (mismo dominio que los CHECK de `interactions.channel` y `tickets.channel`). La UI mapea `email → etiqueta "Gmail"` (y su ícono/color). Rationale: un solo dominio de canal en toda la BD, sin capa de mapeo en las queries que cruzan `orders`/`tickets/interactions` con las conexiones, y consistencia con los datos que ya escriben los flujos (que registran `email`). La alternativa (agregar `'gmail'` al CHECK) crea dos valores equivalentes para el mismo canal y obliga a un mapeo en todo el dashboard.
- El "canal Gmail" del dashboard es una **capacidad nueva**: los flujos actuales NO tienen nodo Gmail (responden por Telegram node + SMTP/Mailpit, por eso `interactions.channel='email'`). La conexión Gmail OAuth2 habilita a futuro enviar por Gmail real, pero la lectura de interacciones ya existentes sigue viendo `email`.

### 6. Autenticación — JWT corto + refresh, bcrypt, rate limiting
- Passwords con **bcrypt** (`passlib[bcrypt]`), nunca plano.
- **Access token JWT 2h** (spec §6) y **refresh token 7 días** (rotativo) firmados con secreto de `.env` (`DASHBOARD_JWT_SECRET`). Se devuelven por los endpoints `/auth/*`; el refresh se envía en cookie HttpOnly (`secure` detrás de HTTPS) y se renueva en `/auth/refresh`. Todas las rutas menos `/auth/*`, `/connections/telegram/confirm` y `/connections/gmail/callback` exigen Bearer JWT y **filtrar por `client_account_id` del token** (nunca cruzar datos entre cuentas).
- **Rate limiting** en `/auth/login`: middleware simple en memoria (por IP combinada con email fallido, ventana deslizante ~5 intentos/5 min). Suficiente porque hay una sola instancia; `slowapi` como alternativa si hace falta más.
- **Encriptado de `encrypted_credentials`** con **Fernet** (`cryptography`), clave `DASHBOARD_ENC_KEY` en `.env` (base64, 32 bytes). Nunca se escriben tokens en claro; getters decriptan solo en memoria al momento de usar la conexión.

### 7. CORS y secreto compartido del webhook
- CORS: whitelist explícita de orígenes (`http://localhost:5173` dev, `http://localhost:8080` prod), nunca `*`.
- `/connections/telegram/confirm` y `/connections/gmail/callback`: el primero valida header `X-N8N-SECRET: <DASHBOARD_N8N_SECRET>`; el segundo valida el `state` OAuth y los codes de Google. Nada de estos secretos hardcodeado.

### 8. Flujo Telegram — código de 6 dígitos con workflow n8n AISLADO
- `POST /connections/telegram/start` (JWT): genera código de 6 dígitos, lo guarda **en memoria** (`{code, client_account_id, expira 15 min}`) y lo muestra al usuario.
- El cliente envía el código por chat al **bot de Telegram de vínculo** (dedicated: workflow n8n nuevo "Telegram — Vínculo de cuenta" con su propio `telegramTrigger` y su propio bot token `DASHBOARD_BOT_TOKEN_VINCULO`).
  - **Por qué un bot token dedicado**: un bot de Telegram solo admite **un** webhook a la vez. Un segundo `telegramTrigger` con el mismo token del Flujo 2 le pisaría el webhook y rompería el bot principal — exactamente lo que la spec prohíbe ("no tocar el Flujo 2"). Con un bot de vínculo aislado no hay conflicto y el workflow nuevo es 100 % independiente e importable.
- El workflow valida `^\d{6}$` y llama `POST /connections/telegram/confirm` (JWT NO requerido) con header `X-N8N-SECRET` y body `{code, chat_id}`. El endpoint valida secreto + vigencia (15 min) y marca `status='connected'` con `external_reference=chat_id`.
- `chat_id` → `external_reference`: es exactamente el uso que la spec pensó para esa columna (DESVIOS §2.11).

### 9. Flujo Gmail — OAuth2 real (testing mode)
- `GET /connections/gmail/oauth-url` (JWT): genera URL de consent de Google con `state` firmado (liga la cuenta) → `GET /connections/gmail/callback` recibe `code`, canjea por **refresh token** y lo guarda **encriptado** (Fernet) en `encrypted_credentials`, `external_reference` = email autorizado, `status='connected'`.
- Google Cloud Console en modo testing alcanza para la demo (dominios de prueba + refresh tokens en la ventana de testing). Se documenta en `.env.example` que para duración extendida hay que publicar el consent screen (fuera de alcance del video).

### 10. Flujo WhatsApp — solicitud honesta en `pending`
- `POST /connections/whatsapp/request-approval` (JWT): valida el número y crea/actualiza `channel_connections` con `status='pending'`, `external_reference` = número en formato E.164. Mensaje tipo "Meta aprueba en 1-3 días hábiles". No hay llamada real a la Cloud API (la aprobación es off-band y tarda días) — comportamiento legítimo de producción, se documenta en la defensa.
- Para el video se **seed un `connected` de WhatsApp** (dato semilla) en `seed_dashboard.sql` y se muestra el estado conectado; se deja el flujo de solicitud real funcional para demostrar el `pending`.

### 11. Lectura de datos — vistas reales, no recálculo
- `GET /dashboard/summary`: **`v_metrics_summary`** (MTTD/MTTR/TMR ya promediados) + complementos con `orders` (pedidos de hoy por `received_at >= date_trunc('day', now())`) y `tickets` (abiertos: `status IN ('open','in_progress')`). Filtro opcional `data_source='measured'` para métricas honestas.
- `GET /orders`: `JOIN` simple a `products` vía `orders.product_id` (equivalente hoy a `order_items`, mono-producto) o detalle vía `order_items` para el ítem. Status/paginado.
- `GET /tickets`: leer `tickets`; "resuelto" = `status='resolved'` (**no confiar en `resolved_at`**, siempre NULL porque el workflow no lo toca — DESVIOS §2.4/§4.4).
- `GET /products`: búsqueda por `sku`/`name` (`ILIKE`) + paginado.
- **Timestamps**: se serializan como ISO 8601 con `AT TIME ZONE 'UTC'` explícito (instancia puede ser `TIMESTAMP` o `TIMESTAMPTZ`); el front formatea a hora local. Antes de la demo, `\d orders` para confirmar el tipo real.
- `orders.raw_payload` (JSONB) existe: se devuelve tal cual en `GET /orders/{id}` (trazabilidad del webhook).

### 12. Polling 3-5s
- Dashboard y Pedidos: TanStack Query con `refetchInterval: 4000` (4s, dentro de la ventana 3-5s de la spec). Tickets/Catálogo/Conexiones: refetch manual (pull-to-refresh o botón) + invalidación al mutar.

### 13. Seeds y rama
- Migración: `migracion_dashboard_cliente.sql` (solo `CREATE TABLE IF NOT EXISTS` + índice). Seed: **`seed_dashboard.sql`** nuevo (cuenta demo realista + conexiones en distintos estados: `connected` de WhatsApp, `connected` de Telegram con `external_reference`, `disconnected` de email). **No toca `seed_expand.sql` ni `seed_catalogo.sql`** (el catálogo se siembra con `seed_catalogo.sql` cuando haga falta).
- Rama `feature/dashboard-cliente` se crea desde `main` recién en la Fase 1.

## Risks / Trade-offs

- **[Dos `telegramTrigger` con el mismo bot] → Mitigación**: bot dedicado de vínculo (decisión 8). Sin esto se pisa el webhook del Flujo 2.
- **[Instancia desplegada con `TIMESTAMP` en vez de `TIMESTAMPTZ`] → Mitigación**: `AT TIME ZONE` explícito + ISO string; verificar `\d orders` en Fase 2.
- **[ngrok/WEBHOOK_URL pública necesaria para el Telegram Trigger] → Mitigación**: el enrutamiento de vínculo usa el mismo mecanismo que el Flujo 2 ya documenta (ngrok). Deja de ser showstopper porque el vínculo no es parte de la demo en vivo obligatoria (se puede preregistrar con seed).
- **[Google OAuth modo testing: refresh tokens expiran ~7 días] → Mitigación**: alcanza para la entrega; se documenta el paso de publicar el consent screen.
- **[WhatsApp `pending` no demuestra envío real] → Mitigación**: seed `connected` para el video + la explicación honesta en la defensa (comportamiento real de producción).
- **[Fernet: rotar clave invalida credenciales guardadas] → Mitigación**: fuera de alcance; se documenta que rotar `DASHBOARD_ENC_KEY` exige re-vincular canales.
- **[Métricas "medias" si se mezcla `synthetic` y `measured`] → Mitigación**: filtro `data_source='measured'` disponible como query param; la demo muestra todo pero el endpoint lo soporta.
- **[Paginado simple (OFFSET)] → Trade-off aceptado**: volumen de demo es bajo; no se justifica keyset pagination.

## Migration Plan

1. Fase 1: crear rama `feature/dashboard-cliente` desde `main`. Aplicar `migracion_dashboard_cliente.sql` contra la BD del volumen (`docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis < migracion_dashboard_cliente.sql`) y `seed_dashboard.sql`. **Rollback**: `DROP TABLE channel_connections, client_accounts` — no afecta ninguna tabla de los flujos.
2. Fase 2/3: editar `docker-compose.yml` sumando `dashboard-api` y `dashboard-web` con `${VAR:-default}`; `docker compose up -d ` arranca los servicios viejos igual (sin romper n8n/grafana/mailpit).
3. Fase 3: crear/importar (vía UI de n8n) el workflow aislado "Telegram — Vínculo de cuenta" y persistir con `.\backup.ps1`.

## Open Questions

- **Bot de vínculo**: el bot dedicado simplifica el aislamiento pero suma una pieza de setup (crear bot con BotFather, nuevo token). Alternativa descartada por riesgo de romper el webhook del Flujo 2. Confirmar durante la Fase 3 que el `telegramTrigger` del workflow aislado registra bien su webhook con el token propio.
- **Puerto `8080`** para `dashboard-web`: libre en el host actual; si un ambiente tiene ocupado el 8080, cambiar el mapping host a `8081:80`.
- **`POST /products` y `PATCH /products/{id}`** (alta manual, "opcional si da el tiempo", §5): se planifican como opcionales en Fase 5; si el tiempo no alcanza quedan como Open Question resuelta en la demora de la demo.
- **N8N de la demo ya activo**: el workflow de vínculo de Telegram se importa con `"active": false` (mismo patrón que los existentes) y se activa en la UI en la Fase 3.