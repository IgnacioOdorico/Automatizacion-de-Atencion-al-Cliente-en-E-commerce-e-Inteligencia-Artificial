# SPEC — Dashboard Cliente + Conexiones (Frontend/Backend para demo de tesis)

**Estado:** propuesto
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
```

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

*(el agente completa esta sección a medida que encuentra diferencias entre este documento y el repo real)*
