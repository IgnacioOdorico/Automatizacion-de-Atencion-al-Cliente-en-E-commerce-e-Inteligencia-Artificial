# SPEC — Dashboard Cliente + Conexiones (Frontend/Backend para demo de tesis)

**Estado:** implementado en `feature/dashboard-cliente` (ver §10 para los desvíos)
**Rama:** `feature/dashboard-cliente` (crear desde `main`/`master`, confirmar cuál es la rama base antes de empezar)
**Depende de:** Flujo 1 (pipeline de órdenes) y Flujo 2 (chatbot omnicanal) — **ya implementados y NO se modifican**
**Deadline:** ajustado — priorizar lo que se ve en cámara sobre lo que no

---

## 0. Instrucciones para el agente (leer antes de tocar código)

Este documento es el punto de entrada. Antes de escribir una sola línea:

1. **Explorar el repo de punta a punta.** Leer, en este orden:
   - `README.md` y `CLAUDE.md` (o `AGENTS.md`) en la raíz, si existen
   - `docs/SPEC_FLUJO1_PIPELINE_ORDENES.md` (o equivalente)
   - `docs/SPEC_FLUJO2_CHATBOT_OMNICANAL.md` (o equivalente)
   - `docs/PROMPT_IA_CHATBOT.md`
   - Los JSON de los workflows de N8N (carpeta `workflows/` o similar) — entender nodos, webhooks expuestos, nombres exactos de paths (`/webhook/...`), formato de payload esperado en cada uno
   - `init_simple.sql` / `seed_expand.sql` / cualquier script de schema — entender tablas reales: `orders`, `tickets`, `interactions`, `products`, vistas de métricas (`v_metrics_summary`, `v_daily_order_summary`, etc.)
   - `docker-compose.yml` — servicios existentes, puertos, redes, credenciales de Postgres
2. **No asumir nombres de campos ni de endpoints.** Si algo en este spec no coincide con lo que el agente encuentra en el repo real, el repo real manda — actualizar este documento (sección "Desvíos del spec") en vez de forzar el código a calzar con el spec.
3. **Crear la rama** `feature/dashboard-cliente` antes del primer commit de código. Todo el trabajo de este spec vive ahí hasta el merge final.
4. **No tocar** los workflows de N8N, sus JSON, ni las tablas `orders`/`tickets`/`interactions`/`products` en su forma actual. Solo se permite **agregar** tablas/columnas nuevas (ver sección 3), nunca modificar lo que ya usan los Flujos 1 y 2.
5. Seguir fases en orden. Cada fase termina en un estado demostrable (aunque sea parcial) — no avanzar a la fase N+1 con la fase N rota.
6. Cualquier decisión de seguridad (sección 6) es no negociable, incluso si "para la demo no hace falta". Es una tesis con evaluación estricta: un agujero de seguridad visible en el código resta más que una feature de menos.

---

## 1. Qué estamos construyendo (contexto de negocio)

El bot (Flujos 1 y 2) ya funciona. Lo que falta es la **cara visible del producto**: convertirlo de "un conjunto de workflows de N8N" a "un SaaS que una PyME de e-commerce podría contratar hoy".

Referencia directa: el proyecto de tesis "Aura Group" (compañeros de cátedra, ya aprobado) construyó exactamente este tipo de capa para su propio bot de marketing — un dashboard tipo SaaS (Next.js en Vercel) con secciones de Conexiones, Métricas, Perfil, y usa **WhatsApp/Telegram reales** (no un chat simulado) para la demo en vivo. Mismo enfoque acá, con estilo propio y adaptado a e-commerce.

**La app tiene un solo rol por ahora: el cliente PyME** (el dueño del e-commerce que contrata el servicio). No hay necesidad de un rol "admin de la plataforma" separado para esta demo — se puede dejar el modelo de datos preparado para eso a futuro, pero no se construye UI de admin ahora (recortar alcance).

Páginas necesarias:

| Página | Qué muestra | De dónde sale la data |
|---|---|---|
| **Login / Registro** | Acceso del cliente PyME a su cuenta | Tabla nueva `client_accounts` |
| **Dashboard (home)** | Resumen: pedidos hoy, tickets abiertos, MTTD/MTTR/TMR del período | Vistas de métricas existentes + `orders`/`tickets` |
| **Pedidos** | Lista de órdenes procesadas por el Flujo 1, estado, stock afectado | Tabla `orders` |
| **Tickets** | Reclamos/casos generados por el Flujo 2 | Tabla `tickets` / `interactions` |
| **Catálogo** | Productos que el bot conoce (para justificar de dónde sale la data que usa el chatbot) | Tabla `products` |
| **Conexiones** | Estado de WhatsApp, Telegram y Gmail — conectar/desconectar cada canal | Tabla nueva `channel_connections` |
| **Perfil** | Datos de la cuenta/empresa | `client_accounts` |
| **Monitoreo** | Todo lo que hace el bot, al pie de la letra: feed en vivo de eventos (pedidos, mensajes, respuestas, tickets, alertas de stock), conversaciones por canal y usuario, y el workflow de n8n dibujado con la ejecución nodo por nodo (solo lectura) | `orders`, `interactions`, `tickets`, `stock_alerts` + tablas internas de n8n (`workflow_entity`, `execution_entity`, `execution_data`). Contrato en `docs/API_MONITOREO.md` |
| **Métricas** | Reemplazo en vivo, dentro del portal, de los paneles de los dos dashboards de Grafana: MTTD/MTTR/end-to-end, distribución de estados y serie diaria de órdenes; TMR promedio, distribución de intents y serie diaria por canal del chatbot. Se omite el panel "Precisión (accuracy) 92.7%" (literal SQL fijo, no calculado) y nunca se lee `v_chatbot_corpus` (ventana congelada del 12/08) | `orders`, `interactions` (nunca las vistas congeladas). Contrato en `docs/API_METRICAS.md` |

---

## 2. Arquitectura

```
React (Vite + TS)  ──▶  FastAPI  ──┬──▶  PostgreSQL (orders, tickets, interactions, products, + tablas nuevas)
                                     └──▶  Webhooks de N8N (solo para acciones que ya disparan los flujos, si aplica)
```

- FastAPI es dueño de: autenticación, lectura de métricas/pedidos/tickets, gestión de conexiones de canal.
- N8N sigue siendo dueño de: procesar órdenes (Flujo 1) y responder el chat (Flujo 2). El front **no reimplementa esa lógica**, solo la observa y, si corresponde, dispara acciones puntuales (ej. simular un pedido nuevo desde el catálogo para la demo).
- Todo corre en el mismo `docker-compose.yml` existente, se agrega un servicio `dashboard-api` (FastAPI) y `dashboard-web` (React, servido con `vite build` + nginx o similar, a definir según cómo se va a mostrar en el video).

---

## 3. Modelo de datos nuevo (solo tablas agregadas, no se toca nada existente)

```sql
-- Cuenta de la PyME cliente
CREATE TABLE client_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  -- bcrypt, nunca texto plano
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Estado de conexión de cada canal por cuenta
CREATE TABLE channel_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    channel TEXT NOT NULL CHECK (channel IN ('whatsapp', 'telegram', 'gmail')),
    status TEXT NOT NULL DEFAULT 'disconnected'
        CHECK (status IN ('disconnected', 'pending', 'connected', 'error')),
    external_reference TEXT,       -- ej. chat_id de Telegram, email autorizado en Gmail
    connected_at TIMESTAMPTZ,
    -- tokens/credenciales SIEMPRE encriptados a nivel de aplicación antes de guardar, nunca plano
    encrypted_credentials TEXT,
    UNIQUE (client_account_id, channel)
);
```

> Si el schema real usa otro motor de IDs (serial en vez de UUID) o convenciones distintas, seguir la convención del repo existente en vez de esto.

---

## 4. Conexión de canales — cómo se resuelve cada uno (realista, no una promesa vacía)

Esto es lo que más peso académico tiene si el jurado pregunta "¿esto funciona de verdad o es humo?". Resolverlo de forma honesta suma puntos, fingir que es trivial resta.

- **Telegram** → 100% real y rápido de implementar, igual que hizo Aura: la cuenta genera un código de 6 dígitos (`POST /connections/telegram/start`), el cliente lo manda por chat al bot de Telegram existente, un endpoint recibe la confirmación desde N8N (webhook nuevo y aislado, no toca el Flujo 2) y marca `status = connected`. Válido por 15 minutos, igual que la referencia.
- **Gmail** → real vía OAuth2 de Google (flujo estándar, Google lo resuelve gratis para modo testing/desarrollo). El cliente hace clic en "Conectar Gmail", pasa por el consent screen de Google, y el backend guarda el refresh token encriptado.
- **WhatsApp Business Cloud API** → acá hay que ser honestos: la aprobación real de Meta para un número de negocio lleva días/semanas y no depende de nosotros. La UI muestra un flujo de solicitud real (formulario con número, verificación) que deja el estado en `pending` con un mensaje tipo "Solicitud enviada, Meta aprueba en 1-3 días hábiles" — **esto es literalmente lo que pasaría en producción**, así que no es una mentira para la demo, es el comportamiento correcto. Para el video, se puede tener una cuenta ya en estado `connected` (dato semilla) para mostrar cómo se ve una vez aprobado.

Documentar esta decisión explícitamente en el video/defensa: muestra criterio profesional, no limitación técnica.

---

## 5. Endpoints FastAPI (contrato base)

```
POST   /auth/register
POST   /auth/login                 → devuelve JWT
GET    /me                         → datos de la cuenta logueada

GET    /dashboard/summary          → pedidos hoy, tickets abiertos, MTTD/MTTR/TMR
GET    /orders?status=&page=
GET    /orders/{id}
GET    /tickets?status=&page=
GET    /tickets/{id}
GET    /products?search=&page=
POST   /products                   → alta manual (opcional, si da el tiempo)
PATCH  /products/{id}

GET    /connections
POST   /connections/telegram/start     → genera código de vinculación
POST   /connections/telegram/confirm   → llamado por N8N cuando el bot recibe el código
GET    /connections/gmail/oauth-url
GET    /connections/gmail/callback
POST   /connections/whatsapp/request-approval
DELETE /connections/{channel}          → desconectar

GET    /monitoring/summary                       → contadores del bot, pedidos, tickets y ejecuciones (ventana en horas)
GET    /monitoring/events                        → feed unificado de eventos (cursor keyset, `since` para polling)
GET    /monitoring/conversations                 → hilos por canal + usuario
GET    /monitoring/conversations/thread          → mensajes de un hilo (`channel` y `user_id` por query)
GET    /monitoring/workflows                     → workflows de n8n con contadores de 24 h
GET    /monitoring/workflows/{id}/graph          → grafo sanitizado (nodos, aristas, posiciones)
GET    /monitoring/executions                    → ejecuciones de n8n (cursor por id)
GET    /monitoring/executions/{id}               → traza nodo por nodo (redactada y acotada)

GET    /metrics/orders                           → MTTD/MTTR/end-to-end, distribución de estados y serie diaria (ventana en horas u histórico completo)
GET    /metrics/chatbot                          → TMR promedio, distribución de intents y serie diaria por canal (idem, solo sobre `interactions`)
```

Los endpoints `/monitoring/*` y `/metrics/*` son de solo lectura y su contrato exacto (campos, tipos, ejemplos) está en `docs/API_MONITOREO.md` y `docs/API_METRICAS.md` respectivamente.

Todos los endpoints (salvo `/auth/*` y `/connections/telegram/confirm`) requieren JWT válido y devuelven solo datos de la `client_account_id` del token — **nunca cruzar datos entre cuentas**.

---

## 6. Seguridad (no negociable)

- Passwords: `bcrypt`, nunca comparación ni almacenamiento en texto plano.
- JWT: expiración corta (ej. 2h) + refresh token; secreto en variable de entorno, nunca hardcodeado.
- `channel_connections.encrypted_credentials`: encriptado con una clave de app (ej. Fernet/AES) guardada en variable de entorno, nunca en el repo.
- CORS: whitelist explícita del origen del front, nunca `*`.
- Rate limiting básico en `/auth/login` (evitar fuerza bruta) — aunque sea un middleware simple.
- El endpoint `/connections/telegram/confirm` (el único que no requiere JWT porque lo llama N8N) debe validar un secreto compartido en el header, no quedar abierto.
- Nada de credenciales, tokens ni claves en el código o en `docker-compose.yml` versionado — todo por `.env` (y confirmar que `.env` está en `.gitignore`).
- Variables de entorno de ejemplo en `.env.example`, nunca los valores reales.

---

## 7. Estilo visual

Dark mode como base (igual línea que la referencia), pero con paleta e identidad propias — no clonar el morado de Aura. Sugerido: definir 1 color de marca + escala de grises, tipografía sans moderna (Inter o similar), sidebar fijo a la izquierda con las secciones de la tabla de la sección 1, cards con bordes sutiles y buen espaciado (nada de UI de tutorial). Usar el skill `frontend-design` disponible para el agente antes de escribir CSS.

---

## 8. Fases

### Fase 0 — Exploración (agente, sin escribir código de producto)
Leer todo lo listado en la sección 0. Producir un archivo `docs/DESVIOS_SPEC.md` si algo del repo real difiere de este documento (nombres de tablas, endpoints de N8N, etc.).

### Fase 1 — Rama + schema
Crear `feature/dashboard-cliente`. Migración SQL con las tablas de la sección 3. Seed de una `client_account` demo + conexiones en distintos estados (uno `connected` de WhatsApp para mostrar en video).

### Fase 2 — Backend FastAPI: auth + lectura
Endpoints de `/auth/*`, `/dashboard/summary`, `/orders`, `/tickets`, `/products` (solo lectura). Dockerizado, sumado al `docker-compose.yml`.

### Fase 3 — Backend FastAPI: conexiones
Endpoints de la sección 4 (Telegram real, Gmail OAuth real, WhatsApp con flujo de solicitud). Webhook nuevo en N8N (aislado) para confirmar Telegram — **agregar, no modificar el Flujo 2 existente**.

### Fase 4 — Frontend: auth + shell
Login/registro, layout con sidebar, ruteo protegido.

### Fase 5 — Frontend: Dashboard, Pedidos, Tickets, Catálogo
Consumen los endpoints de lectura. Polling cada 3-5s en el dashboard/pedidos para el efecto "en vivo".

### Fase 6 — Frontend: Conexiones
UI de conectar/desconectar cada canal, con los tres flujos reales de la sección 4.

### Fase 7 — Pulido para cámara
Estados de carga, vacíos, error; transiciones; datos seed que se vean bien en video (nombres reales, no "Test123"); revisar que no haya texto placeholder tipo "Lorem ipsum".

### Fase 8 — QA de seguridad
Repasar la checklist de la sección 6 una por una antes de dar por cerrada la tarea.

---

## 9. Fuera de alcance (explícito, para no perder tiempo)

- Rol de "admin de la plataforma" / gestión de múltiples clientes desde un panel superior.
- Chat widget propio — se usa WhatsApp/Telegram real en el video.
- Tests automatizados exhaustivos (si el tiempo aprieta, priorizar que funcione y se vea bien sobre cobertura de tests).
- Pagos/facturación del "SaaS" (no es el foco de la tesis).

---

## 10. Desvíos del spec

> Completada al cerrar la Fase 8 y verificada contra el código de `feature/dashboard-cliente`. Los desvíos detectados antes de escribir código (relevamiento del repo) están en `docs/DESVIOS_SPEC.md`; acá van los que aparecieron al implementar.

### 10.1 Modelo de datos

| El spec dice | Lo que hay | Por qué |
|---|---|---|
| IDs `UUID` con `gen_random_uuid()` (§3) | `SERIAL` (entero) en `client_accounts` y `channel_connections`; el `sub` del JWT es numérico | El propio spec pide seguir la convención del repo: todas las tablas de `init_simple.sql` usan `SERIAL`. |
| `channel IN ('whatsapp','telegram','gmail')` (§3) | En la BD el canal se llama `email` (`CHECK (channel IN ('whatsapp','telegram','email'))`); la UI lo muestra como "Gmail" | Es el mismo dominio que ya usan `interactions.channel` y `tickets.channel`. Un solo valor por canal en toda la BD, sin mapeos en las queries. |
| Marcas de tiempo `TIMESTAMPTZ` | Se mantiene, pero la API serializa siempre ISO 8601 en UTC (`...Z`, con `AT TIME ZONE 'UTC'`) y el front formatea a hora de Mendoza | Una instancia anterior a la auditoría A-12 podía tener `TIMESTAMP` sin zona; así el resultado no depende de eso ni de la máquina que mira. |
| Las 3 filas de `channel_connections` se crean "al pedirlas" | Se crean al registrarse (una sola sentencia con la cuenta) | Que `/me` de una cuenta nueva no devuelva `connections: []`. |

### 10.2 Aislamiento entre cuentas: un solo comercio por instalación (limitación conocida)

El §5 dice que todos los endpoints "devuelven solo datos de la `client_account_id` del token". Eso se cumple **solo para lo que pertenece a la cuenta**: perfil (`/me`), conexiones de canal, códigos de vinculación de Telegram, estado de Gmail y solicitud de WhatsApp. **No se cumple para `orders`, `tickets`, `products` ni las métricas**: esas tablas no tienen `client_account_id`, son las del e-commerce único que atienden los Flujos 1 y 2, y el §0.4 prohíbe modificarlas. Todas las cuentas de una instalación ven los mismos pedidos, tickets y catálogo (un comercio por instalación; el multi-tenant queda fuera de alcance, §9).

Consecuencia de seguridad: con el registro abierto, cualquier persona que cree una cuenta puede leer los datos de los clientes finales del comercio (nombre, email, teléfono). Por eso existe `DASHBOARD_ALLOW_REGISTRATION` (por defecto `true`, para la demo): en una instalación accesible desde internet se pone en `false`. Multi-tenant real exigiría una columna `client_account_id` en esas tablas y que n8n la escriba. Está cubierto por `dashboard-api/tests/test_isolation.py` (`test_orders_tickets_and_products_are_shared_by_design`).

### 10.3 Endpoints

- **Agregados**: `POST /auth/refresh` (refresh token rotativo con detección de reutilización) y `DELETE /connections/telegram/code` (cancela el código de vinculación pendiente). `DELETE /connections/telegram` además invalida el código pendiente de esa cuenta.
- `POST /auth/login` devuelve `access_token` (2 h) **y** `refresh_token` (7 días), no un único JWT.
- `GET /connections/gmail/callback` no responde JSON: siempre redirige (307) al front, a `{DASHBOARD_FRONTEND_URL}/conexiones?gmail=connected` o `?gmail=error&reason=<código>`, con un catálogo cerrado de motivos (nunca viajan detalles ni tokens).
- `GET /connections` devuelve `{items: [...]}` con la etiqueta de cada canal; `/me` incluye las conexiones; `/dashboard/summary` acepta `?data_source=` (`measured` para las métricas de la tesis). Paginado fijo de 20.
- **`POST /products` y `PATCH /products/{id}` NO están implementados**: el spec los marca como opcionales ("si da el tiempo") y la tarea 6.6 quedó sin hacer. El catálogo es de solo lectura.

- **Monitoreo (`/monitoring/*`, solo lectura)**: no figuraba en el spec original. El feed y las conversaciones derivan de `orders`, `interactions`, `tickets` y `stock_alerts`. La sección de workflow **lee las tablas internas de n8n 2.12.2** (`workflow_entity`, `execution_entity`, `execution_data`) que viven en la misma PostgreSQL; es un acoplamiento a un esquema que n8n no publica como API estable (el `data` de `execution_data` está en formato `flatted`, que la API decodifica con un parser propio, con tope de 2 MB). Por eso **degrada**: si las tablas no existen o el usuario no puede leerlas, `/monitoring/workflows` y `/monitoring/executions` responden `available: false` con lista vacía (nunca 500) y `/monitoring/summary` informa `executions.available: false`. El grafo se arma con una lista blanca (nombre, tipo, posición y conexiones): **nunca** salen `parameters`, `credentials`, `webhookId` ni notas, y la vista previa de la salida de cada nodo se acota a ~2 KB y se redacta por clave (`authorization`, `token`, `secret`, `password`, `cookie`, ...) y por valor (Bearer/JWT, `sk-`, tokens de bot, hex y base64 largos). Como el resto de `orders`/`tickets`, el feed no está aislado por cuenta (§10.2). Para leerlo, la API usa el mismo usuario de la BD que n8n.

- **Métricas (`/metrics/*`, solo lectura)**: tampoco figuraba en el spec original; nace de una decisión explícita del usuario de reemplazar los dos dashboards de Grafana (`grafana/dashboards/tesis-flujo1.json`, `tesis-flujo2.json`) por una vista en vivo dentro del propio portal. Tres decisiones de esa auditoría:
  - El panel "Precisión (accuracy) 92.7%" de `tesis-flujo2.json` **se omite por completo**: es `SELECT 92.7 AS "Accuracy"`, un literal SQL fijo, no una métrica calculada sobre ningún dato real.
  - `GET /metrics/chatbot` nunca lee `v_chatbot_corpus`: esa vista está filtrada a `data_source='measured'` y a la ventana fija `2026-08-12 23:00–24:00` (`docs/DESVIOS_SPEC.md` §2.12/§3.2), no es "en vivo". Tampoco se usa `v_daily_chatbot_summary` (que sí es independiente de esa ventana, pero no admite `hours`/`data_source` como parámetro ni rellena huecos de días): ambos endpoints recalculan directo sobre `orders`/`interactions` para no heredar ningún supuesto oculto de una vista.
  - `hours` es opcional; sin valor, los agregados escalares cubren el histórico completo, y solo la serie diaria se acota a 90 días (documentado en `docs/API_METRICAS.md`) para no devolver una fila por día desde el origen de los datos.

### 10.4 Conexión de canales

- **Telegram**: se usa un **bot de vínculo dedicado** (`DASHBOARD_BOT_TOKEN_VINCULO`) con un workflow aislado (`workflows/Flujo 3 — Telegram Vínculo de Cuenta.json`, versionado con `"active": false`). Un bot de Telegram admite un único webhook: reutilizar el token del Flujo 2 se lo pisaría. Los códigos de 6 dígitos (15 min) viven **en memoria** de la API: un reinicio los descarta. Para ser real necesita una URL pública HTTPS para el webhook (`WEBHOOK_URL`, p. ej. ngrok).
- **Gmail**: OAuth2 real en modo testing (scope `openid email gmail.modify`); necesita credenciales de Google del usuario. Sin ellas, `oauth-url` responde 503 controlado.
- **WhatsApp**: `request-approval` valida el número (E.164) y deja el canal en `pending` con "Meta aprueba en 1-3 días hábiles"; **no llama a Meta**. Es el comportamiento honesto del §4. La cuenta demo trae WhatsApp `connected` como dato semilla.
- Polling: Dashboard y Pedidos cada **4 s** (el spec pedía 3-5 s); el vínculo de Telegram consulta cada 3 s mientras hay un código pendiente; Tickets, Catálogo y Conexiones se refrescan a mano o al mutar.

### 10.5 Seguridad (§6): qué se hizo distinto o además

- **Tokens en `localStorage`** (access y refresh), no cookie HttpOnly para el refresh como decía el diseño original. El backend igual setea la cookie HttpOnly y `/auth/refresh` la acepta, pero el SPA usa el body. Motivo: mantener la sesión al recargar (criterio de la tarea 5.3) sin resolver CSRF. Riesgo: un XSS podría leer los tokens. **Mitigación**: nginx manda una CSP estricta (`script-src 'self'`, sin `unsafe-inline` ni `unsafe-eval`, `frame-ancestors 'none'`, `connect-src 'self'`), y hay tests que impiden `innerHTML`/`eval`/`console.*` y tokens en URLs. Para producción se recomienda access en memoria + refresh en cookie HttpOnly `Secure` con rotación persistida.
- **Fail-closed**: la API no arranca si `DASHBOARD_JWT_SECRET`, `DASHBOARD_N8N_SECRET` o `DASHBOARD_ENC_KEY` faltan, están vacíos, son cortos (< 32) o son valores de ejemplo. `docker-compose.yml` ya no trae defaults para ellos.
- **Rate limit de login** por IP y por email (5 fallos en 5 min → 429), en memoria. Detrás de nginx la IP real se toma de `X-Real-IP` solo si el peer es el proxy configurado (`DASHBOARD_TRUSTED_PROXIES`, por defecto el servicio `dashboard-web`); `X-Forwarded-For` no se usa.
- **Agregados que el spec no pedía**: `/docs`, `/redoc` y `/openapi.json` apagados por defecto (`DASHBOARD_ENABLE_DOCS`), `DASHBOARD_ALLOW_REGISTRATION`, headers de seguridad en nginx, CORS con métodos y headers explícitos, contenedor de la API sin root, topes de tamaño (login, registro, body de nginx 1 MB), login sin diferencia de tiempo entre email existente e inexistente.
- El estado de refresh tokens ya rotados, del rate limit y de los códigos de Telegram es **en memoria**: sirve para una sola instancia de la API y se pierde al reiniciarla.

### 10.6 Infra y entorno

- Puertos: PostgreSQL en el host `5433` (internamente `postgres:5432`), API `8000`, portal `8080` (nginx; el front siempre llama a `/api`, que nginx reenvía a `dashboard-api:8000`). En desarrollo, Vite en `5173`.
- `DASHBOARD_FRONTEND_URL` (adonde vuelve el navegador tras el consentimiento de Google) vale por defecto `http://localhost:8080` en el compose; con Vite se cambia a `:5173` y tiene que estar en `CORS_ORIGINS`. `DASHBOARD_GOOGLE_REDIRECT_URI` es el callback del **backend** y debe coincidir exacto con el cargado en Google Cloud Console.
- La instancia de n8n no trae credenciales: para que el Flujo 1 real escriba órdenes hay que cargar en su UI una credencial Postgres (`postgres:5432`, BD `ecommerce_tesis`) y una SMTP (`mailpit:1025`, sin auth ni TLS). Hasta entonces el dashboard se prueba con datos ya existentes o simulados por SQL.
- El §9 dejaba los tests automatizados como opcionales; igual se escribieron (pytest para la API, vitest para el front) porque el spec exige QA de seguridad verificable.
