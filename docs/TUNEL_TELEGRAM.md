# Túnel público para el vínculo de Telegram (y Gmail real)

Para que Telegram funcione de verdad, n8n necesita una **URL pública HTTPS**. El compose la resuelve con el perfil `tunnel`: un `webhook-gateway` (nginx) que solo deja pasar el webhook de Telegram, y `ngrok` que lo publica en tu dominio estático gratuito. Sin el perfil, `docker compose up -d` sigue andando igual que siempre (sin ngrok ni tokens).

> **Solo Telegram necesita el túnel.** Gmail usa `http://localhost` en modo testing (paso 8) y WhatsApp real no está implementado.

## Camino rápido

1. Cuenta de ngrok → authtoken + dominio estático.
2. BotFather → bot **dedicado** de vínculo → token.
3. Cargar las variables en `.env`.
4. `docker compose --profile tunnel up -d`
5. En n8n: importar `Flujo 3`, crear 2 credenciales, activarlo.
6. Verificar el webhook con `getWebhookInfo`.
7. Probar de punta a punta desde el dashboard.

Los pasos 1, 2, 5 y 8 son tuyos (cuentas y credenciales propias): no se pueden automatizar.

## 1. ngrok: authtoken y dominio estático

1. Creá una cuenta gratuita en <https://dashboard.ngrok.com/signup>.
2. Copiá tu **authtoken** (*Your Authtoken* en el panel).
3. En *Domains* creá tu dominio estático gratuito (algo como `nombre-raro.ngrok-free.dev`). Es fijo: `WEBHOOK_URL` se carga una sola vez.

## 2. Bot de Telegram

1. En Telegram, hablale a `@BotFather` → `/newbot` → elegí nombre y usuario (ej.: `tesis_vinculo_bot`).
2. Guardá el **token**. Tiene que ser un bot **nuevo**: un bot admite un solo webhook y reutilizar el del Flujo 2 se lo pisaría.

## 3. Variables de `.env`

Solo nombres y placeholders; los valores reales no se versionan.

```env
# --- Túnel (nuevas) ---
NGROK_AUTHTOKEN=<tu-authtoken-de-ngrok>
NGROK_DOMAIN=<tu-dominio>.ngrok-free.dev        # sin https:// ni barras
WEBHOOK_URL=https://<tu-dominio>.ngrok-free.dev/  # con https:// y barra final
N8N_PROXY_HOPS=2                                 # n8n queda detrás de ngrok + gateway

# --- Ya existentes (dashboard) ---
DASHBOARD_N8N_SECRET=<el-mismo-que-ya-tenias>
DASHBOARD_FRONTEND_URL=http://localhost:8080
DASHBOARD_GOOGLE_CLIENT_ID=<paso-8>
DASHBOARD_GOOGLE_CLIENT_SECRET=<paso-8>
DASHBOARD_GOOGLE_REDIRECT_URI=http://localhost:8000/connections/gmail/callback
```

`DASHBOARD_BOT_TOKEN_VINCULO` **ya no se usa**: el token del bot va solo en la credencial de n8n (paso 5).

## 4. Levantar

```powershell
docker compose --profile tunnel up -d
docker compose --profile tunnel ps          # webhook-gateway (healthy) y ngrok Up
docker compose logs ngrok                   # busca "started tunnel" / tu dominio
```

Esto recrea `n8n` (toma `WEBHOOK_URL` y `N8N_PROXY_HOPS`); los datos persisten en el volumen. Comprobá que el túnel anda **y** que no expone nada de más:

```powershell
curl.exe -i https://<tu-dominio>.ngrok-free.dev/          # esperado: 404 "not found" (el editor NO es público)
```

## 5. n8n: importar el Flujo 3 y crear las credenciales

En <http://localhost:5678> (el editor solo se abre en local):

1. *Import from file* → `workflows/Flujo 3 — Telegram Vínculo de Cuenta.json`.
2. Credencial **Telegram API**: pegá el token del bot. Asignala al trigger y al nodo *Responder Confirmación*.
3. Credencial **Header Auth**: *Name* = `X-N8N-SECRET`, *Value* = el valor de `DASHBOARD_N8N_SECRET`. Asignala al nodo *Confirmar Vínculo (API)*.
4. Guardá y **activá** el workflow (al activarlo, n8n registra el webhook en Telegram).

> **Por qué credenciales y no `$env`:** n8n 2.x bloquea `$env` por defecto. Habilitarlo (`N8N_BLOCK_ENV_ACCESS_IN_NODE=false`) dejaría que cualquier workflow lea `N8N_ENCRYPTION_KEY` y la contraseña de la BD. Las credenciales quedan cifradas por n8n. **Costo:** el secreto se carga en dos lugares (`.env` y la credencial); si lo rotás, cambialo en los dos.

## 6. Verificar el webhook registrado

Sin dejar el token en el historial de la terminal:

```powershell
$t = Read-Host "Token del bot"
Invoke-RestMethod "https://api.telegram.org/bot$t/getWebhookInfo" | Select-Object url, pending_update_count, last_error_message
```

Esperado: `url` = `https://<tu-dominio>.ngrok-free.dev/webhook/<uuid>/webhook` y `last_error_message` vacío.

## 7. Prueba de punta a punta

1. Dashboard <http://localhost:8080> → **Conexiones** → Telegram → *Conectar* → aparece un código de 6 dígitos (vale 15 min).
2. Enviale ese código al bot de vínculo.
3. El bot responde "¡Listo! …" y el canal pasa a *Conectado* en el panel.

## 8. Gmail (Google Cloud, modo testing)

1. <https://console.cloud.google.com> → creá un proyecto → *APIs y servicios* → habilitá **Gmail API**.
2. *Pantalla de consentimiento de OAuth* → tipo **Externo**, estado **Testing** → en *Usuarios de prueba* agregá **tu** Gmail.
3. Scopes que usa el backend (`core/google_oauth.py`): `openid`, `email` y `https://www.googleapis.com/auth/gmail.modify`.
4. *Credenciales* → *Crear credenciales* → **ID de cliente de OAuth** → tipo **Aplicación web**.
5. *URI de redirección autorizados*: exactamente `http://localhost:8000/connections/gmail/callback`.
6. Copiá *Client ID* y *Client secret* a `.env` (`DASHBOARD_GOOGLE_CLIENT_ID` / `DASHBOARD_GOOGLE_CLIENT_SECRET`) y aplicá: `docker compose up -d dashboard-api`.

Google va a mostrar "app no verificada": es normal en modo testing con tu usuario de prueba (*Continuar*). En testing, el refresh token vence a los 7 días: si Gmail deja de andar, reconectalo.

## 9. Seguridad: qué expone el túnel

| Expuesto públicamente | NO expuesto (404 en el gateway) |
|---|---|
| `POST /webhook/<uuid>/webhook` (Telegram Trigger), máx. 64 KB, con rate limit | Editor de n8n y `/rest/*` |
| | `/webhook/orden-nueva`, `/webhook/whatsapp-business` (pipeline) |
| | `/webhook-test/*`, `/healthz`, cualquier `GET`/`HEAD`/`PUT`… |
| | Dashboard (`:8080`), API (`:8000`), Postgres, Grafana, Mailpit |

- El gateway no reenvía `Authorization`, `Cookie` ni API keys a n8n; n8n valida además el `secret_token` que Telegram manda en cada update.
- La allowlist exige un **UUID** en la ruta. Un Telegram Trigger cuyo `webhookId` no sea UUID (p. ej. el del Flujo 2 PRODUCCION) recibe 404 hasta que se le asigne uno.
- **Si se filtra el authtoken:** panel de ngrok → *Your Authtoken* → *Reset*, actualizá `NGROK_AUTHTOKEN` en `.env` y `docker compose --profile tunnel up -d ngrok`.
- **Si se filtra el token del bot:** `/revoke` en BotFather y actualizá la credencial en n8n. **Si se filtra `DASHBOARD_N8N_SECRET`:** generá uno nuevo y cambialo en `.env` y en la credencial Header Auth.
- Apagar el túnel: `docker compose --profile tunnel rm -sf ngrok webhook-gateway`.

## Troubleshooting

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `ngrok` sale con "faltan NGROK_AUTHTOKEN y/o NGROK_DOMAIN" | Variables vacías en `.env` | Completarlas y `docker compose --profile tunnel up -d` |
| `ERR_NGROK_105` en `logs ngrok` | Authtoken mal copiado | Recopiarlo del panel |
| ngrok rechaza el dominio | No es el dominio estático de **tu** cuenta, o hay otro ngrok usándolo | Revisar *Domains*; cerrar otros agentes |
| `getWebhookInfo` muestra una URL `localhost` o vacía | `WEBHOOK_URL` no cargada o n8n sin recrear | Corregir `.env`, `up -d`, desactivar y reactivar el workflow |
| `last_error_message`: 404 | Workflow inactivo, o `webhookId` que no es UUID | Activarlo; revisar `docker compose logs webhook-gateway` |
| `last_error_message`: 403 | El `secret_token` cambió | Desactivar y reactivar el workflow |
| Enviás el código y el bot no contesta | La API rechazó la llamada (ver la ejecución en n8n) | 401: Header Auth ≠ `DASHBOARD_N8N_SECRET`. 400: código vencido o inválido, pedí uno nuevo |
| Google: `redirect_uri_mismatch` | El URI no es idéntico | Debe ser exactamente `http://localhost:8000/connections/gmail/callback` |
| Google: acceso bloqueado | Tu cuenta no es usuario de prueba | Agregarla en la pantalla de consentimiento |
| Dashboard: "Google OAuth no configurado" (503) | Variables vacías en la API | Completarlas y `docker compose up -d dashboard-api` |
| Gmail vuelve con `reason=no_refresh` | Google ya había emitido consentimiento | Quitar el acceso de la app en tu cuenta de Google y reconectar |
