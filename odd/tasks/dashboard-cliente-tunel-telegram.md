# ODD — Túnel público para el vínculo de Telegram (ngrok en el compose)

**Rama:** `feature/dashboard-cliente` · **Origen:** pedido del usuario (2026-09-21): "lo del ngrok, ¿lo ponemos en el compose y qué más? resolvelo".
**TDD:** activo donde haya lógica testeable; la config de infra se verifica con evidencia observada (`docker compose config`, curl contra el gateway). No hay ngrok real en esta sesión (el authtoken es del usuario).
**Restricción de permisos:** `.env` y `.env.*` (incluye `.env.example`) están denegados por `~/.claude/settings.json` del usuario: no se leen ni se editan; las líneas para esos archivos se listan para que las cargue el usuario.

## Decisiones
1. Solo Telegram necesita URL pública HTTPS (el trigger registra su webhook en Telegram). Gmail OAuth funciona con `http://localhost` en modo testing; WhatsApp real no está implementado.
2. Servicios nuevos bajo `profiles: ["tunnel"]` para que `docker compose up -d` siga funcionando sin ngrok ni tokens:
   - `webhook-gateway` (nginx:1.27-alpine): **allowlist** estricta hacia n8n. Solo `POST /webhook/<uuid>/webhook` (el path del Telegram Trigger). Todo lo demás (editor, `/rest`, `/webhook/orden-nueva`, `/webhook/whatsapp-business`) → 404. Motivo: exponer n8n crudo publicaría el editor (basic auth débil) y el pipeline de órdenes.
   - `ngrok` (imagen oficial `ngrok/ngrok:3`): `ngrok http webhook-gateway:80 --url=$NGROK_DOMAIN` con dominio estático gratuito → `WEBHOOK_URL` estable, se carga una vez.
3. n8n detrás de 2 proxies (ngrok + gateway): `N8N_PROXY_HOPS` (default 0; 2 con túnel) y `N8N_EDITOR_BASE_URL` (default `http://localhost:5678`, si no n8n usa `WEBHOOK_URL` como base de la instancia y los links del editor apuntarían al dominio público). Nombres verificados en `@n8n/config` de la 2.12.2. `WEBHOOK_URL` se mantiene (el rename a `N8N_WEBHOOK_URL` es de 2.35).
4. "Qué más": el Flujo 3 leía `$env.DASHBOARD_N8N_SECRET` y el token del bot por `$env`; n8n 2.x lo bloquea (`N8N_BLOCK_ENV_ACCESS_IN_NODE` ≠ `false` ⇒ `ExpressionError: access to env vars denied`, verificado en `n8n-workflow` del contenedor). Decisión: credenciales de n8n (**Telegram API** para el token, **Header Auth** para `X-N8N-SECRET`), no habilitar `$env` (expondría `N8N_ENCRYPTION_KEY` y la clave de la BD a cualquier workflow). Se quitan las dos variables del servicio `n8n`. Costo: el secreto se carga en `.env` y en la credencial.

## Tareas
- [x] C8.1 Auditar `Flujo 3` y el servicio `n8n` del compose: cómo llegan token/secreto/URL al workflow; corregir lo necesario (env pass-through / credencial) sin tocar Flujos 1 y 2
- [x] C8.2 Servicios `webhook-gateway` + `ngrok` bajo perfil `tunnel`, `WEBHOOK_URL`/proxy hops/editor URL en n8n
- [x] C8.3 Verificación: `docker compose config` con y sin perfil; `up -d` por defecto intacto; allowlist del gateway probada con curl (permitido vs 404)
- [x] C8.4 Guía `docs/TUNEL_TELEGRAM.md` (pasos del usuario: cuenta ngrok, authtoken, dominio estático, BotFather, Google Cloud, variables) + enlace desde README; lista de líneas para `.env.example`

## Ruta por tarea
Delegated direct, un writer (2+ archivos no triviales: compose, config del gateway, guía).

## Progreso / Evidencia
Commits: `eaf423f` (Flujo 3), `214a958` (compose + gateway + guardas), `5f03bae` (guía + README + CLAUDE.md).

- **C8.1** Audit: el contenedor `n8n` recibía `DASHBOARD_N8N_SECRET` y `DASHBOARD_BOT_TOKEN_VINCULO` pero el workflow los leía con `$env`, bloqueado por defecto (`workflow-data-proxy-env-provider.js`: `N8N_BLOCK_ENV_ACCESS_IN_NODE !== 'false'` ⇒ error). Fix: nodo HTTP con `authentication: genericCredentialType` + `httpHeaderAuth` (credencial `PENDIENTE_HEADER_AUTH_VINCULO`), sin `$env`; `webhookId` del trigger pasó de `telegram-vinculo-webhook-001` a un UUID (`4136e4af-…`) porque el gateway exige UUID. URL de la API ya era `http://dashboard-api:8000/…`. `"active": false` intacto. Importado en un n8n 2.12.2 descartable (sqlite propia): `Successfully imported 1 workflow`, `active: false`, webhookId conservado, credenciales `telegramApi`×2 + `httpHeaderAuth`. Flujos 1 y 2 sin tocar.
- **C8.2** Ver commit `214a958`. Path del webhook verificado en el código de n8n (`getNodeWebhookPath`: `<webhookId>/<path>` con `path: 'webhook'`) y el Telegram Trigger valida `X-Telegram-Bot-Api-Secret-Token` (defensa en profundidad).
- **C8.3**
  - `docker compose config --quiet`: OK sin perfil (6 servicios) y con `--profile tunnel` (8: + `ngrok`, `webhook-gateway`); sin `ports` en el gateway; `NGROK_*` vacíos por `${VAR:-}`; `n8n` sin variables `DASHBOARD_*`.
  - `docker compose up -d --dry-run` (sin perfil): no toca gateway/ngrok; solo marca `n8n` para recrear (cambio de env, esperado). `up -d --no-recreate`: los 6 servicios siguen `Up`/healthy. **n8n NO se recreó en esta sesión** (sigue con el env viejo hasta el próximo `up -d`).
  - Gateway levantado solo (`Up (healthy)`, `read_only` + tmpfs, sin puertos publicados) y probado desde `tesis_dashboard_api` con `http.client`: 7 POST válidos llegaron a n8n (log de n8n: 7 "unknown webhook", 0 de otros métodos); GET/HEAD/PUT/DELETE/OPTIONS/PATCH, `/`, `/rest/*`, `/healthz`, `/webhook/orden-nueva`, `/webhook/whatsapp-business`, `/webhook-test/*`, subruta/barra final, query string, UUID en mayúsculas, `/WEBHOOK/`, `..`, `%2e%2e`, UUID corto/no hex, `telegram-vinculo-webhook-001` ⇒ 404 del gateway (`not found`); `%00` ⇒ 400; body 100 KB ⇒ 413; body 60 KB ⇒ llega a n8n.
  - Headers (gateway copia + backend eco, contenedores efímeros ya borrados): `Authorization`, `Proxy-Authorization`, `Cookie`, `X-N8N-API-KEY` llegan vacíos; `X-Telegram-Bot-Api-Secret-Token` pasa; XFF se agrega el peer; `X-Forwarded-Host` se pisa.
  - ngrok (contenedor descartable, sin levantar el servicio): sin variables ⇒ `exit 1` con mensaje; `NGROK_DOMAIN=https://…` ⇒ `exit 1`; token falso + dominio ⇒ flags aceptados y `ERR_NGROK_105` (el agente lee `NGROK_AUTHTOKEN` del env).
  - `POST http://dashboard-api:8000/connections/telegram/confirm` desde `tesis_n8n`: 401 sin header y 401 con secreto incorrecto.
  - Gateway bajado con `docker compose --profile tunnel rm -sf webhook-gateway`; el stack quedó en 6 servicios.
  - `nginx -t` OK también con la config en CRLF (Git en Windows con autocrlf).
  - `cd dashboard-api; .venv/Scripts/python -m pytest -q`: 231 passed (216 previos + 15 guardas nuevas en `tests/test_tunnel_guards.py`, RED observado primero por archivo faltante). No se tocó `dashboard-web`.
- **C8.4** `docs/TUNEL_TELEGRAM.md` + enlace y tabla de variables en `README.md`, línea en `CLAUDE.md`.

### No verificado (depende de cuentas del usuario)
ngrok real (authtoken/dominio propios), registro real del webhook en Telegram (`getWebhookInfo`), vínculo de punta a punta, OAuth de Google, y que la importación **por la UI** conserve el UUID del `webhookId` (la CLI sí lo conserva; el gateway acepta cualquier UUID).

## Pasos del usuario
Ver `docs/TUNEL_TELEGRAM.md` (1, 2, 3, 5 y 8) y cargar en `.env.example` / `dashboard-api/.env.example` las líneas del reporte de C8.

## Próximo paso
Que el usuario cargue cuentas y credenciales y pruebe el paso 7 de la guía; después, push/PR de la rama según su decisión.
