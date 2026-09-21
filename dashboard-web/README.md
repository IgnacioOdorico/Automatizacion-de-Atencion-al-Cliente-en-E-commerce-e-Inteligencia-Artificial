# dashboard-web — Portal del cliente (React + Vite + TS)

Frontend del panel del cliente PyME. Consume `dashboard-api` (`:8000`) siempre por el path `/api`:

- **Dev**: `vite` en `localhost:5173` proxya `/api` → `http://localhost:8000` (mismo path que prod).
- **Prod**: nginx sirve `dist/` y proxya `/api` → `dashboard-api:8000` (rewrite `/api` → `/`).

## Scripts

```bash
npm install        # instala dependencias
npm run dev        # dev server en http://localhost:5173
npm run build      # tsc --noEmit + vite build -> dist/
npm run preview    # sirve el build localmente
npm test           # vitest run (lógica pura, render de componentes en jsdom y contraste/accesibilidad del CSS)
```

## Demo

Cuenta seed (la que ya siembra `seed_dashboard.sql`):

- Email: `ventas@tecnoshopmza.com.ar`
- Password: `Demo2026!`

## Demo en vivo (grabación)

`demo_en_vivo.ps1` (en la raíz del repo) dispara **una orden nueva** contra n8n mientras se filma el dashboard: en Pedidos y Dashboard aparece sola en menos de 4 s (polling), con la fila resaltada unos segundos.

> **Advertencia: el script ESCRIBE en la base de datos compartida** (`ecommerce_tesis`, la misma que usan Grafana y las métricas medidas de la tesis). La orden queda en `orders` y, si hay stock, se descuenta de `products`; con `-ConChatbot` además se registra una fila en `interactions` (y puede crearse un ticket). No se borran solas: ejecutalo solo cuando quieras que esos datos existan.

```powershell
.\demo_en_vivo.ps1                                # 1 orden con stock (PROD-001), pide confirmación
.\demo_en_vivo.ps1 -Sku PROD-005 -Cantidad 2      # otro producto / cantidad
.\demo_en_vivo.ps1 -SinStock                      # pide más unidades que el stock (rama "sin stock")
.\demo_en_vivo.ps1 -ConChatbot                    # además manda un mensaje al chatbot
.\demo_en_vivo.ps1 -ConChatbot -Mensaje "Necesito hacer un reclamo por mi pedido"
.\demo_en_vivo.ps1 -Si                            # sin pedir confirmación
```

- El `order_number` es único (`ORD-DEMO-<yyyyMMddHHmmss>`), así que se puede repetir sin choques.
- Verifica que n8n responda (`/healthz`) antes de enviar y muestra el resultado del Flujo 1 (`status`, `total_amount`, `message`). Si n8n responde 200 **sin cuerpo**, la ejecución falló en n8n (típico: credenciales de Postgres/SMTP sin cargar): el script lo avisa y sale con error.
- El mensaje al chatbot va a `POST /webhook/whatsapp-business` con el payload **plano** `{from, text: {body}, name}` (no la envoltura de la Cloud API; ver `docs/DESVIOS_SPEC.md` §2.4). Ese webhook no devuelve la respuesta del bot.
- Requiere `docker compose up -d` y, en n8n, el Flujo 1 (y el Flujo 2 si usás `-ConChatbot`) **activos y con sus credenciales cargadas**.
- Para limpiar lo que dejó (revisá antes de correr): `DELETE FROM orders WHERE order_number LIKE 'ORD-DEMO-%';` y reponé el stock descontado.

## Docker

```bash
docker compose up -d --build dashboard-web   # http://localhost:8080
```

`Dockerfile` es multi-stage: `node:22-alpine` corre `npm ci && vite build`, y `nginx:1.27-alpine` sirve `dist/` con SPA fallback y el proxy `/api/` hacia `dashboard-api:8000`. Ver `nginx.conf`.

## Flujo de tokens (decisión + trade-off)

El backend (`dashboard-api`) emite `{access_token (2h), refresh_token (7d), token_type}` en el body de `/auth/login` y `/auth/refresh`, y además setea el refresh en cookie **HttpOnly** (`secure=False` en local).

El front persiste **ambos tokens en `localStorage`** y el cliente de fetch:

1. Adjunta `Authorization: Bearer <access>`.
2. Si recibe **401** (o el access ya venció por `exp`), pide `/auth/refresh` con el refresh del body — **un solo refresh en vuelo** compartido entre requests simultáneas — y **rehace la request original**.
3. Si el refresh falla: limpia tokens, invalida el query cache y redirige a `/login` (spec `client-dashboard/auth`, escenario "Sesión vencida").

**Trade-off documentado (aceptado para la demo):** `localStorage` es vulnerable a XSS; una cookie HttpOnly no lo es pero exige manejo de CSRF y complica la rotación del refresh. Para un portfolio/tesis la persistencia de sesión entre recargas (AC de la tarea 5.3) pesa más que el riesgo teórico de XSS en un entorno de demo sin terceros. En producción se recomienda: access en memoria, refresh solo en cookie HttpOnly `SameSite=Lax` + estado de rotación en BD (los endpoints ya soportan ambas vías: `/auth/refresh` acepta el body o la cookie). El refresh del body se persiste así la cookie que setea el backend queda como refuerzo, no como dependencia.

## Nota prod: redirect del Gmail callback

El callback de Gmail redirige a `DASHBOARD_FRONTEND_URL` (env de `dashboard-api`, default `http://localhost:5173`). Para la demo servida desde nginx (`:8080`) conviene setear en `.env`:

```
DASHBOARD_FRONTEND_URL=http://localhost:8080
```

## Estructura

```
src/
  api/client.ts        cliente fetch con refresh automático + retry
  api/endpoints.ts     endpoints tipados (auth + Fases 5-6)
  auth/                tokenStorage (localStorage) + AuthContext
  components/          Shell (sidebar fija; barra superior en móvil), QueryView (contrato
                       cargando/vacío/error/listo), Modal accesible, ui/*
  hooks/               vínculo de Telegram, vuelta de Gmail, filas nuevas del polling
  lib/                 validación, formatos es-AR (hora de Mendoza), estados de vista,
                       detalle de pedido, foco, nav, mensajes
  pages/               login, registro, dashboard, pedidos, tickets, catálogo,
                       conexiones y perfil
  styles/              tokens.css (paleta dark + brand, AA) + global.css
```