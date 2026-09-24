# Propuesta — Dashboard Cliente + Conexiones

## Why

Los Flujos 1 y 2 (pipeline de órdenes y chatbot omnicanal en n8n) ya funcionan, pero son "un conjunto de workflows" sin cara visible. Falta la capa de producto que convierta el sistema en **un SaaS que una PyME de e-commerce podría contratar hoy**: un dashboard con login del cliente, métricas reales (MTTD/MTTR/TMR ya calculadas en la BD), pedidos/tickets/catálogo y conexión honesta de canales (Telegram y Gmail reales; WhatsApp con el flujo de aprobación real de Meta). Es el mismo patrón que el proyecto de referencia "Aura Group" (ya aprobado), que mostró una demo en vivo sobre canales reales.

## What Changes

- **Dos tablas nuevas** en PostgreSQL (`client_accounts`, `channel_connections`) — solo se agregan, no se toca nada que usen los Flujos 1 y 2.
- **Backend FastAPI** (`dashboard-api`): registro/login con JWT corto + refresh, lectura de resumen/pedidos/tickets/catálogo contra las tablas y vistas reales, y gestión de conexiones de canal.
- **Frontend React (Vite + TS)** (`dashboard-web`): login, dashboard, pedidos, tickets, catálogo, conexiones, perfil — dark mode, identidad visual propia.
- **Tres flujos de conexión reales**: Telegram con código de 6 dígitos verificado por un webhook nuevo y aislado en n8n (no modifica el Flujo 2), Gmail OAuth2 real, WhatsApp con solicitud que queda en `pending` (comportamiento real de Meta, no simulación).
- **Nuevo webhook n8n aislado** `/webhook/telegram-vincular` (o path equivalente) para confirmar la vinculación de Telegram — se agrega, no se altera el Flujo 2.
- **Infra**: dos servicios nuevos en el `docker-compose.yml` existente (`dashboard-api`, `dashboard-web`), sin romper los 4 servicios actuales.
- **Seguridad obligatoria** (checklist de la spec §6): bcrypt, JWT en `.env`, credenciales encriptadas (Fernet/AES), CORS con whitelist, rate limiting en `/auth/login`, secreto compartido en header para el webhook de confirmación.

## Capabilities

### New Capabilities
- `client-dashboard/auth`: registro, login con JWT de expiración corta + refresh token, perfil (`/me`), ruteo protegido en el front, rate limiting en login.
- `client-dashboard/connections`: estado de canales (`whatsapp`/`telegram`/`email`), flujo Telegram por código de 6 dígitos con webhook n8n aislado, flujo Gmail OAuth2, flujo WhatsApp de solicitud en `pending`, desconexión, encriptado de credenciales.
- `client-dashboard/orders`: lectura de pedidos (`orders`), tickets (`tickets`) y catálogo (`products`) con paginado y filtros, aislada por cuenta.
- `client-dashboard/metrics`: resumen del dashboard (`v_metrics_summary` + pedidos hoy + tickets abiertos) y polling 3-5s en las páginas en vivo.

### Modified Capabilities
- _Ninguna_ — no existen specs previas en `openspec/specs/`; todo el dashboard son capacidades nuevas.

## Impact

- **Schema**: se agregan `client_accounts` y `channel_connections` (convención del repo: `TIMESTAMPTZ`, `gen_random_uuid()` en PG15). No se modifica ninguna tabla/vista existente.
- **Infra**: `docker-compose.yml` suma `dashboard-api` (FastAPI, alta en `tesis_network` → ve `postgres:5432` interno) y `dashboard-web` (Vite build + nginx). Host: Postgres publicado en `5433`, NO `5432`.
- **n8n**: se agrega un webhook aislado para confirmar la vinculación de Telegram. No se tocan los workflows de los Flujos 1 y 2.
- **Repos**: se agrega una migración SQL (`migracion_dashboard.sql` o similar) y se amplía `.env.example` con las nuevas variables (sin valores reales).
- **Fuera de alcance** (explicito de la spec §9): rol admin de plataforma, chat widget propio, suite de tests exhaustiva, pagos/facturación.

> **Nota de desvíos**: antes de planificar se exploró el repo de punta a punta (Fase 0) y las diferencias contra `SPEC_DASHBOARD_CLIENTE.md` quedaron documentadas en `docs/DESVIOS_SPEC.md`. Los desvíos que modelan este plan: Postgres host `5433` (nombre interno `postgres:5432`), webhook Flujo 2 real `/webhook/whatsapp-business` con payload plano, sin `pipeline_events` (alertas de stock en `stock_alerts`), `orders.raw_payload` JSONB existe, `interactions.metadata` no existe, salida real del Flujo 2 por Telegram node + SMTP/Mailpit (no Gmail node — el canal "Gmail" del dashboard será una capacidad nueva), dominio de canal `email` en BD (no `gmail`), `seed_expand.sql` congelado (usar `seed_catalogo.sql`), 7 tablas / 6 vistas reales, timestamp canónico `TIMESTAMPTZ`.