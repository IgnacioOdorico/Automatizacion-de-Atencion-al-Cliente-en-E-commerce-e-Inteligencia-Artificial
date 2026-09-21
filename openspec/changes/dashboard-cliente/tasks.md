# Tasks — Dashboard Cliente + Conexiones

> Mapea las 8 fases de `SPEC_DASHBOARD_CLIENTE.md` contra `specs/` y `design.md`. Criterios de verificación en cada tarea (AC). Referencias: specs `client-dashboard/auth`, `client-dashboard/orders`, `client-dashboard/metrics`, `client-dashboard/connections`; decisiones en `design.md`.

## 1. Fase 0 — Exploración (completada)

- [x] 1.1 Relevar repo de punta a punta y producir `docs/DESVIOS_SPEC.md` (AC: el archivo existe, documenta port 5433, webhook `/webhook/whatsapp-business`, sin `pipeline_events`, `orders.raw_payload` existe, `interactions.metadata` no existe, salida por SMTP/Telegram, dominio `email` vs `gmail`, `seed_expand.sql` congelado, 7 tablas/6 vistas reales)

## 2. Fase 1 — Rama + schema

- [x] 2.1 Crear rama `feature/dashboard-cliente` desde `main` (AC: `git branch --show-current` = `feature/dashboard-cliente`)
- [x] 2.2 Escribir `migracion_dashboard_cliente.sql` con `client_accounts` y `channel_connections` según design.md §4 (SERIAL, TIMESTAMPTZ, CHECK canales `('whatsapp','telegram','email')`, UNIQUE `(client_account_id, channel)`, índice sobre `client_account_id`) (AC: DDL validado contra `init_simple.sql` de referencia; no toca tablas existentes)
- [x] 2.3 Escribir `seed_dashboard.sql` con cuenta demo realista + conexiones en estados variados: `whatsapp` `connected` (para el video), `telegram` `connected` con `external_reference`, `email` `disconnected` (AC: `ON CONFLICT DO NOTHING`; no TRUNCATE; passwords con bcrypt)
- [x] 2.4 Aplicar migración + seed contra la BD del volumen y verificar (AC: `docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis -c '\d client_accounts'` y un `SELECT` a `channel_connections`; rollback documentado: solo `DROP TABLE channel_connections, client_accounts`)
- [x] 2.5 Verificar el tipo temporal real de la instancia (`\d orders`) y dejar constancia de `TIMESTAMPTZ` vs `TIMESTAMP` (AC: la serialización de la API usa `AT TIME ZONE` explícito en coherencia con lo encontrado)

## 3. Fase 2 — Backend FastAPI: auth + lectura

- [x] 3.1 Scaffold `dashboard-api/` (FastAPI + Uvicorn, `requirements.txt`, `Dockerfile`, `app/main.py`, `app/core/config.py` con pydantic-settings y variables de `.env`) (AC: `uvicorn app.main:app` levanta y `/health` responde 200)
- [x] 3.2 Capa de BD: engine SQLAlchemy 2.0 con `postgres:5432` interno (host) — configurable por `DATABASE_URL` — y helpers `text()` parametrizados (AC: query de humo a `v_metrics_summary` responde desde el contenedor)
- [x] 3.3 Seguridad base: bcrypt (passlib), JWT 2h + refresh 7 días con `DASHBOARD_JWT_SECRET`, dependencia de auth que inyecta `client_account_id`, Fernández/Fernet helper para credenciales con `DASHBOARD_ENC_KEY` (AC: sección 6 de la spec cubierta al final de la fase; refresh rotativo probado con curl)
- [x] 3.4 Endpoints `POST /auth/register`, `POST /auth/login` (con rate limiting por IP+email, umbral 5/5min), `POST /auth/refresh`, `GET /me` (spec `client-dashboard/auth`) (AC: login OK devuelve tokens; login FAIL 401; 5 fallos → 429; register duplicado → 409)
- [x] 3.5 `GET /dashboard/summary` leyendo `v_metrics_summary` + pedidos de hoy + tickets abiertos, con filtro opcional `data_source='measured'` (spec `client-dashboard/metrics`) (AC: los promedios MTTD/MTTR/TMR coinciden con `v_metrics_summary` y no se recalculan en app)
- [x] 3.6 `GET /orders?status=&page=`, `GET /orders/{id}` (con `order_items` y `raw_payload`), `GET /tickets?status=&page=`, `GET /tickets/{id}`, `GET /products?search=&page=` — todo paginado (20) y filtrado por `client_account_id` del token (spec `client-dashboard/orders`) (AC: cada endpoint respondió datos reales vía curl con JWT; ticket `resolved_at` NULL se maneja sin error)
- [x] 3.7 Dockerizar `dashboard-api` en `docker-compose.yml` (red `tesis_network`, puerto `8000:8000`, env `${VAR:-default}`) y arrancar TODOS los servicios juntos (AC: `docker compose up -d` levanta n8n+postgres+mailpit+grafana+dashboard-api sin romper nada; la API responde y ve `postgres`, no `localhost`)

## 4. Fase 3 — Backend FastAPI: conexiones + webhook n8n aislado

- [x] 4.1 `GET /connections` y `DELETE /connections/{channel}` sobre `channel_connections` (spec `client-dashboard/connections`) (AC: la cuenta seed muestra sus 3 conexiones; desconectar limpia credenciales y deja `disconnected`)
- [x] 4.2 `POST /connections/telegram/start`: código de 6 dígitos en memoria, vigencia 15 min, asociado a la cuenta (AC: dos `start` seguidos invalidan el código anterior; vencimiento real de 15 min)
- [x] 4.3 `POST /connections/telegram/confirm` sin JWT pero con header `X-N8N-SECRET` validado: marca `connected` y guarda `chat_id` en `external_reference` (AC: sin header o con secreto malo → 401; código vencido/inexistente → 400; flujo completo probado con curl simulando el webhook)
- [x] 4.4 Workflow n8n aislado "Telegram — Vínculo de cuenta" (nuevo, **no modifica Flujo 2**): `telegramTrigger` con `DASHBOARD_BOT_TOKEN_VINCULO` (bot dedicado), detecta `^\d{6}$` y llama a `POST /connections/telegram/confirm` (spec `client-dashboard/connections`) (AC: importado en la UI, activado, y el vínculo se confirma de punta a punta; el webhook Telegram del Flujo 2 sigue vivo — bot original intacto)
- [x] 4.5 Control de cambio en el workflow: exportar el JSON del workflow nuevo a `workflows/` y correr `.\backup.ps1` para persistir (AC: el JSON versionado lleva `"active": false` como los existentes; backup generado en `backups/<fecha>/`)
- [x] 4.6 Gmail OAuth2: `GET /connections/gmail/oauth-url` (con `state` firmado) y `GET /connections/gmail/callback` (canjea `code`, encripta refresh token en `encrypted_credentials`) (AC: con credenciales de testing de Google, el flujo completo deja el canal en `connected` con `external_reference` = email; errores de Google no persisten nada)
- [x] 4.7 WhatsApp: `POST /connections/whatsapp/request-approval` valida E.164 y deja `pending` con mensaje "Meta aprueba en 1-3 días hábiles" (AC: el estado `pending` se refleja en BD y UI; la cuenta seed sigue mostrando `connected` para el video)

## 5. Fase 4 — Frontend: auth + shell

- [x] 5.1 Scaffold `dashboard-web/` (Vite + React + TS, `Dockerfile`, `nginx.conf` con proxy `/api` → `dashboard-api:8000`, `package.json`) (AC: `vite build` genera `dist/` servible por nginx; dev con `vite` en `localhost:5173`)
- [x] 5.2 Capa de API + estado: cliente de fetch, TanStack Query, manejo de 401 con refresh y logout (spec `client-dashboard/auth`) (AC: access vencido se renueva solo y la request original se rehace)
- [x] 5.3 Páginas `/login` y `/registro` (formularios con validación, estado de error del server) (AC: login/logout/registro funcionan de punta a punta; sesión persiste al recargar)
- [x] 5.4 Shell con **sidebar fija a la izquierda** (Dashboard, Pedidos, Tickets, Catálogo, Conexiones, Perfil), ruteo protegido con redirect a login, paleta dark con 1 color de marca + escala de grises + tipografía Inter (AC: sin sesión, cualquier ruta interna redirige a `/login`; navegación y logout desde el sidebar)

## 6. Fase 5 — Frontend: Dashboard, Pedidos, Tickets, Catálogo

- [x] 6.1 Página Dashboard con cards (pedidos hoy, tickets abiertos, MTTD, MTTR, TMR) y **polling `refetchInterval` 4s** (spec `client-dashboard/metrics`) (AC: al disparar un webhook de `orden-nueva`, la card de pedidos hoy cambia sola en ≤5s)
- [x] 6.2 Página Pedidos con tabla, filtro por estado y paginado + **polling 4s** (AC: una orden nueva del Flujo 1 aparece en la lista sin recargar; filtrar por `no_stock` devuelve solo ese estado)
- [x] 6.3 Detalle de pedido (modal o vista) con `order_items` y `raw_payload` visible (AC: el JSONB original del webhook se renderiza legible)
- [x] 6.4 Página Tickets con filtro por estado, sin asumir `resolved_at` (AC: tickets `resolved` sin `resolved_at` se ven normal)
- [x] 6.5 Página Catálogo con búsqueda `ILIKE` y paginado (AC: buscar "auricular" devuelve los productos que contengan el término en `name`/`sku`)
- [ ] 6.6 (Opcional, si da el tiempo) `POST /products`, `PATCH /products/{id}` y su UI de alta/edición — marcado como **no bloqueante** (AC: solo si Fases 5.1-5.5 cierran a tiempo)

## 7. Fase 6 — Frontend: Conexiones

- [x] 7.1 Página Conexiones leyendo `GET /connections` con cards por canal (WhatsApp, Telegram, Gmail) y mapeo **BD `email` → etiqueta "Gmail"** (spec `client-dashboard/connections`) (AC: se ven los tres canales con su estado real de la cuenta seed)
- [x] 7.2 UI Telegram: botón "Conectar" → muestra el código de 6 dígitos + instructivo de enviarlo al bot → polling de estado hasta `connected` (AC: el flujo de punta a punta con el workflow n8n deja la card en `connected` sin recargar la página)
- [x] 7.3 UI Gmail: botón "Conectar" → redirect al consent de Google → vuelve al front conectado; mostrar email autorizado como `external_reference` (AC: circuito completo en modo testing)
- [x] 7.4 UI WhatsApp: botón "Solicitar aprobación" con número y mensaje "Meta aprueba en 1-3 días hábiles" → estado `pending`; la cuenta `connected` semillada se muestra como aprobada (AC: el estado pendiente persiste y se explica en pantalla)
- [x] 7.5 Desconexión de canal por card (confirm + `DELETE /connections/{channel}`) (AC: la card vuelve a `disconnected` y se limpia la referencia)

## 8. Fase 7 — Pulido para cámara

- [x] 8.1 Estados de carga, vacío y error consistentes en todas las páginas (AC: sin datos, se ve un estado vacío diseñado, no una tabla cruda; error de red → mensaje + reintento)
- [x] 8.2 Datos seed realistas en pantalla: cuentas, empresas y órdenes con nombres reales, formato local de fechas y montos con 2 decimales (AC: revisión visual sin "Test123", "Usuario 1" ni "Lorem ipsum" en pantalla)
- [x] 8.3 Transiciones y micro-interacciones suaves (hover en cards, transición de estados de conexión, skeletons de carga) (AC: la demo se ve consistente, sin parpadeos ni saltos)
- [x] 8.4 Respuesta de la demo en vivo: probar disparar los webhooks (`orden-nueva` y `whatsapp-business` con payload plano según DESVIOS §2.4) desde la UI o curl mientras se filma el dashboard (AC: el efecto "en vivo" se ve en cámara con polling 4s) — script `demo_en_vivo.ps1` listo y documentado; el disparo real queda pendiente: n8n sin credenciales cargadas (ver `odd/tasks/dashboard-cliente-cierre.md`)

## 9. Fase 8 — QA de seguridad (checklist §6, una por una)

- [ ] 9.1 Passwords: bcrypt, nunca texto plano ni comparación en claro (AC: `password_hash` en BD es hash bcrypt; `grep` al repo no encuentra contraseñas planas de la demo)
- [ ] 9.2 JWT: expiración corta (2h) + refresh, secreto en `.env` nunca hardcodeado (AC: `.env` y `dashboard-api/.env.example` documentan `DASHBOARD_JWT_SECRET`; no hay secretos en git)
- [ ] 9.3 `encrypted_credentials` encriptado con Fernet y clave `DASHBOARD_ENC_KEY` de `.env` (AC: un SELECT a `channel_connections` muestra criptograma, no el refresh token)
- [ ] 9.4 CORS: whitelist explícita (`http://localhost:5173`, `http://localhost:8080`), nunca `*` (AC: request desde otro origen responde el header correcto o falla)
- [ ] 9.5 Rate limiting en `/auth/login` (AC: 6 intentos malos seguidos → 429 al sexto)
- [ ] 9.6 `/connections/telegram/confirm` valida `X-N8N-SECRET` (AC: sin header → 401; probado en 4.3)
- [ ] 9.7 Nada de credenciales/tokens/claves en código ni en `docker-compose.yml`; `.env` en `.gitignore`; `.env.example` con placeholders (AC: `git grep` de tokens/claves no encuentra valores reales; `git status` muestra `.env` sin trackear)
- [ ] 9.8 Aislamiento entre cuentas: todas las queries filtran por `client_account_id` del token (AC: dos cuentas seed no se ven datos entre sí en ningún endpoint autenticado)