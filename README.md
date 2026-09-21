# 🛒 Pipeline de Automatización del Ciclo Post-Venta en E-commerce con IA

**Trabajo Final de Grado — UTN FRM 2026**  
**Autores:** Santiago Sordi, Ignacio Odorico, Juan Cruz Ana  
**Tutor:** Prof. Alberto Cortez

---

## 📌 ¿Qué es este proyecto?

Sistema de automatización completo del ciclo post-venta para una PyME e-commerce argentino, implementado con **N8N** como orquestador central. El sistema reemplaza el 100% de las operaciones manuales post-venta mediante dos flujos que trabajan en paralelo:

| Flujo | Nombre | Qué hace |
|-------|--------|----------|
| **Flujo 1** | Pipeline de Procesamiento de Órdenes | Recibe órdenes, verifica stock, confirma el pedido y notifica al cliente por email — en milisegundos, sin intervención humana |
| **Flujo 2** | Chatbot Omnicanal con IA | Atiende consultas de clientes por WhatsApp, Telegram y Email 24/7 usando GPT-4o-mini |

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Network                        │
│                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   n8n    │───▶│  PostgreSQL  │◀───│   Grafana    │  │
│  │ :5678    │    │  :5432       │    │   :3000      │  │
│  │(Flujo 1) │    │ecommerce_    │    │ (Dashboards) │  │
│  │(Flujo 2) │    │tesis         │    │              │  │
│  └────┬─────┘    └──────────────┘    └──────────────┘  │
│       │                                                 │
│       ▼                                                 │
│  ┌──────────┐                                           │
│  │ Mailpit  │ ← Emails de confirmación (demo local)     │
│  │  :8025   │                                           │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘
         │
         ▼ (solo versión PRODUCCION)
  OpenAI API · WhatsApp Business · Telegram Bot · Gmail
```

### Stack tecnológico

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| **N8N** | latest | Orquestador de workflows |
| **PostgreSQL** | 15 | Base de datos unificada |
| **Docker / Docker Compose** | 3.8 | Infraestructura local |
| **Mailpit** | latest | SMTP local para testing |
| **Grafana** | latest | Dashboards de métricas |
| **OpenAI GPT-4o-mini** | vía API | Clasificación de intención y respuestas IA |
| **WhatsApp Business Cloud API** | Meta v18.0 | Canal WhatsApp (producción) |
| **Telegram Bot API** | nativo N8N | Canal Telegram |
| **Gmail OAuth2** | nativo N8N | Canal Email (producción) |

---

## 📊 Flujo 1 — Pipeline de Procesamiento de Órdenes

**Trigger:** `POST http://localhost:5678/webhook/orden-nueva`

```
Webhook → Registrar Orden → Verificar Stock
                                  │
                    ┌─────────────┴──────────────┐
                    ▼ (hay stock)                ▼ (sin stock)
             Actualizar Stock            Marcar Sin Stock
             Verificar Stock Bajo        Email Sin Stock
             Confirmar Orden
             Enviar Email Confirmación
                    │
                    ▼
             Respuesta Webhook
```

**Métricas capturadas automáticamente:**
- **MTTD** — tiempo desde que entra la orden hasta que se procesa
- **MTTR** — tiempo desde el procesamiento hasta que el cliente recibe el email

---

## 💬 Flujo 2 — Chatbot Omnicanal con IA

**Triggers:** WhatsApp webhook + Telegram Bot + Gmail (polling cada 1 min)

```
WhatsApp ──┐
Telegram ──┼──▶ Normalizar ──▶ Buscar FAQ ──▶ GPT-4o-mini
Gmail ─────┘                                       │
                                    ┌──────────────┼──────────────┐
                                    ▼              ▼              ▼
                                  FAQ        ESTADO_PEDIDO    RECLAMO
                                             Buscar en BD    Crear Ticket
                                                    │
                                                    ▼
                                          IF Urgente → Alerta Admin (Telegram)
                                                    │
                                                    ▼
                                    Responder por el mismo canal
                                                    │
                                                    ▼
                                          Registrar Interacción
```

**Métricas capturadas automáticamente:**
- **TMR** — tiempo de respuesta del chatbot de punta a punta

---

## 🗄️ Base de Datos

**5 tablas** en `ecommerce_tesis`:

| Tabla | Descripción |
|-------|-------------|
| `products` | Catálogo de productos con stock y precio |
| `orders` | Órdenes con su ciclo de vida completo |
| `interactions` | Log de conversaciones del chatbot |
| `tickets` | Reclamos creados automáticamente |
| `faq_responses` | Base de conocimiento del chatbot (editable en caliente) |

**5 vistas** para Grafana: `v_order_processing_time`, `v_daily_order_summary`, `v_chatbot_response_time`, `v_daily_chatbot_summary`, `v_metrics_summary`

---

## 🚀 Instalación y uso

### Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

Verificar instalación:
```powershell
docker --version
docker compose version
```

---

### Paso 1 — Clonar el repositorio

```powershell
git clone https://github.com/IgnacioOdorico/Automatizacion-de-Atencion-al-Cliente-en-E-commerce-e-Inteligencia-Artificial.git
cd Automatizacion-de-Atencion-al-Cliente-en-E-commerce-e-Inteligencia-Artificial
```

---

### Paso 2 — Levantar los servicios

```powershell
docker compose up -d
```

Esperá ~30 segundos y verificá que todos estén corriendo:
```powershell
docker ps
```

| Servicio | URL | Credenciales |
|---------|-----|-------------|
| **N8N** | http://localhost:5678 | admin / admin123 |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Mailpit** | http://localhost:8025 | — |
| **PostgreSQL** | localhost:5432 | n8n_user / n8n_pass |

---

### Paso 3 — Crear la base de datos

```powershell
Get-Content init_simple.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
```

---

### Paso 4 — Cargar datos de prueba

```powershell
Get-Content seed_expand.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
```

Verificar:
```powershell
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "SELECT COUNT(*) FROM products; SELECT COUNT(*) FROM faq_responses;"
```
Debe mostrar **20 productos** y **22 FAQs**.

---

### Paso 5 — Importar los workflows en N8N

1. Abrí **http://localhost:5678**
2. Ir a **Workflows → botón "..." → Import from file**
3. Importar en este orden:

| Archivo | Estado |
|---------|--------|
| `workflows/Flujo 1 - Pipeline de Procesamiento de Órdenes SIMPLE.json` | ✅ Activar |
| `workflows/Flujo 2 - Chatbot Omnicanal IA.json` | ✅ Activar |
| `workflows/Flujo 1 - ... PRODUCCION.json` | ⏸ Dejar inactivo |
| `workflows/Flujo 2 - ... PRODUCCION.json` | ⏸ Dejar inactivo |

---

### Paso 6 — Configurar credenciales en N8N

Ir a **http://localhost:5678 → Credentials**

#### PostgreSQL
| Campo | Valor |
|-------|-------|
| Host | `postgres` |
| Port | `5432` |
| Database | `ecommerce_tesis` |
| User | `n8n_user` |
| Password | `n8n_pass` |
| SSL | `disabled` |

#### SMTP (Mailpit — solo para demo local)
| Campo | Valor |
|-------|-------|
| Host | `mailpit` |
| Port | `1025` |
| User | *(vacío)* |
| Password | *(vacío)* |
| SSL/TLS | `None` |

#### OpenAI
| Campo | Valor |
|-------|-------|
| API Key | `sk-...` *(tu clave de https://platform.openai.com)* |

---

### Paso 7 — Configurar Grafana

1. Abrí **http://localhost:3000** → usuario `admin` / contraseña `admin`
2. Ir a **Connections → Data sources → Add data source → PostgreSQL**
3. Completar:

| Campo | Valor |
|-------|-------|
| Host | `postgres:5432` |
| Database | `ecommerce_tesis` |
| User | `n8n_user` |
| Password | `n8n_pass` |
| SSL Mode | `disable` |
| Version | `15` |

4. Click **"Save & test"** → debe decir *"Database Connection OK"*

---

## 🧪 Cómo enviar datos manualmente a N8N

Podés disparar los workflows de tres formas distintas. Elegí la que más te resulte cómoda:

---

### 🔵 Opción 1 — PowerShell (recomendado en Windows)

#### ▶ Flujo 1 — Enviar una orden nueva

```powershell
# Orden confirmada (producto con stock) — Notebook Lenovo IdeaPad 15
Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/orden-nueva" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "order_number": "ORD-2026-0101",
    "customer_name": "Martina Lopez",
    "customer_email": "martina@gmail.com",
    "customer_phone": "5492614001001",
    "product_sku": "PROD-001",
    "quantity": 1
  }'
```

```powershell
# Orden sin stock — Monitor LG 27" 4K (stock bajo, se agota fácil)
Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/orden-nueva" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "order_number": "ORD-2026-0102",
    "customer_name": "Lucas Fernandez",
    "customer_email": "lucas@outlook.com",
    "customer_phone": "5492614006006",
    "product_sku": "PROD-014",
    "quantity": 10
  }'
```

#### ▶ Flujo 2 — Simular mensajes al chatbot

```powershell
# Consulta de estado de pedido via WhatsApp
Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/whatsapp" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5492614002002",
            "text": { "body": "Hola! quiero saber el estado de mi pedido ORD-HIST-002" }
          }],
          "contacts": [{ "profile": { "name": "Facundo Rios" } }]
        }
      }]
    }]
  }'
```

```powershell
# Pregunta frecuente via WhatsApp
Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/whatsapp" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5492614005005",
            "text": { "body": "Buenas, ¿puedo pagar en cuotas con Visa?" }
          }],
          "contacts": [{ "profile": { "name": "Valentina Cruz" } }]
        }
      }]
    }]
  }'
```

```powershell
# Reclamo urgente via WhatsApp (activa alerta al admin)
Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/whatsapp" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5492614006006",
            "text": { "body": "Me llegó el producto roto y si no me lo reemplazan hoy voy a defensa del consumidor" }
          }],
          "contacts": [{ "profile": { "name": "Lucas Fernandez" } }]
        }
      }]
    }]
  }'
```

---

### 🟠 Opción 2 — curl (desde Git Bash, WSL o Linux/Mac)

#### ▶ Flujo 1 — Enviar una orden nueva

```bash
# Orden confirmada — Teclado Mecánico Redragon K552
curl -X POST http://localhost:5678/webhook/orden-nueva \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORD-2026-0103",
    "customer_name": "Agustina Moreno",
    "customer_email": "agus@gmail.com",
    "customer_phone": "5492614007007",
    "product_sku": "PROD-003",
    "quantity": 2
  }'
```

```bash
# Orden sin stock — forzar el camino alternativo
curl -X POST http://localhost:5678/webhook/orden-nueva \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORD-2026-0104",
    "customer_name": "Bruno Herrera",
    "customer_email": "bruno@gmail.com",
    "customer_phone": "5492614010010",
    "product_sku": "PROD-013",
    "quantity": 99
  }'
```

#### ▶ Flujo 2 — Simular mensajes al chatbot

```bash
# Consulta de estado de pedido
curl -X POST http://localhost:5678/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{"from": "5492614003003", "text": {"body": "Hola, me llegó el producto equivocado, pedí auriculares negros y me mandaron blancos"}}],
          "contacts": [{"profile": {"name": "Camila Suarez"}}]
        }
      }]
    }]
  }'
```

---

### 🟣 Opción 3 — Postman o Insomnia (interfaz gráfica)

1. Crear nueva request **POST**
2. URL: `http://localhost:5678/webhook/orden-nueva`
3. Headers: `Content-Type: application/json`
4. Body → **raw → JSON**, pegar uno de estos ejemplos:

```json
{
  "order_number": "ORD-2026-0105",
  "customer_name": "Tomás Gutierrez",
  "customer_email": "tomas@gmail.com",
  "customer_phone": "5492614008008",
  "product_sku": "PROD-018",
  "quantity": 5
}
```

**Para el chatbot** usar URL: `http://localhost:5678/webhook/whatsapp` con este body:
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{"from": "5492614009009", "text": {"body": "Quiero cancelar mi pedido ORD-HIST-009, cambié de opinión"}}],
        "contacts": [{"profile": {"name": "Micaela Vargas"}}]
      }
    }]
  }]
}
```

---

### 🟢 Opción 4 — Desde N8N directamente (ver nodo por nodo)

Esta opción es ideal para **debugging** y ver qué hace cada nodo en detalle:

1. Abrí el workflow en **http://localhost:5678**
2. Click en el nodo **Webhook** (el primero del flujo)
3. Click en **"Listen for test event"** — N8N queda esperando
4. Enviá cualquier request de las opciones 1, 2 o 3
5. El workflow se pausa en cada nodo y podés ver los datos que pasan

---

### 📦 Catálogo de productos disponibles para pruebas

| SKU | Producto | Precio | Stock |
|-----|---------|--------|-------|
| `PROD-001` | Notebook Lenovo IdeaPad 15 | $599.99 | Alto |
| `PROD-002` | Mouse Logitech MX Master 3 | $79.99 | Alto |
| `PROD-003` | Teclado Mecánico Redragon K552 | $49.99 | Alto |
| `PROD-004` | Webcam Logitech C920 HD Pro | $129.99 | Alto |
| `PROD-005` | Monitor Samsung 27" FHD | $349.99 | Alto |
| `PROD-013` | Notebook HP Victus 15 Gaming | $799.99 | Bajo (5 unidades) |
| `PROD-014` | Monitor LG 27" 4K UltraFine | $449.99 | Muy bajo (3 unidades) |
| `PROD-018` | Pendrive Kingston 64GB USB 3.2 | $9.99 | Muy alto (80 unidades) |

> 💡 **Tip:** Para forzar el camino de **sin stock**, pedí más de 50 unidades de cualquier producto o más de 10 del `PROD-014`.

---

### 💬 Mensajes de prueba para el chatbot (Flujo 2)

| Tipo de consulta | Mensaje de ejemplo | Intent esperado |
|-----------------|-------------------|----------------|
| Pregunta frecuente | `"¿Puedo pagar en cuotas?"` | `FAQ` |
| Estado de pedido | `"¿Dónde está mi pedido ORD-HIST-001?"` | `ESTADO_PEDIDO` |
| Reclamo normal | `"Me llegó el producto equivocado"` | `RECLAMO` |
| Reclamo urgente | `"Voy a defensa del consumidor si no me responden"` | `RECLAMO` + urgente |
| Consulta general | `"¿Tienen local físico en Mendoza?"` | `GENERAL` |
| En inglés | `"Hi, I need help with my order"` | `GENERAL` (responde en inglés) |

---

## 🖥️ Dashboard del cliente

Portal web para el dueño del e-commerce: métricas en vivo (pedidos de hoy, tickets abiertos, MTTD/MTTR/TMR), pedidos, tickets, catálogo, conexión de canales (WhatsApp, Telegram, Gmail) y perfil. **Lee la misma BD que los Flujos 1 y 2 sin modificarlos**; solo agrega las tablas `client_accounts` y `channel_connections`.

| Servicio | URL |
|---|---|
| Portal (React + nginx) | http://localhost:8080 |
| API (FastAPI) | http://localhost:8000 (`/health`; `/docs` viene apagado) |

### Levantarlo

1. Completá en `.env` las variables `DASHBOARD_*` (ver abajo). Sin las tres obligatorias la API **no arranca** a propósito (fail-closed).
2. `docker compose up -d --build`
3. La primera vez sobre una BD existente, aplicá la migración y el seed (son idempotentes):

```powershell
Get-Content migracion_dashboard_cliente.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
Get-Content seed_dashboard.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
```

Cuenta demo del seed: `ventas@tecnoshopmza.com.ar` / `Demo2026!` (solo para la demo: no cargues `seed_dashboard.sql` en una instalación real).

### Variables de `.env`

| Variable | Para qué |
|---|---|
| `DASHBOARD_JWT_SECRET`, `DASHBOARD_N8N_SECRET`, `DASHBOARD_ENC_KEY` | **Obligatorias.** Firma de JWT, secreto compartido con n8n (header `X-N8N-SECRET`) y clave Fernet que cifra las credenciales de canales. |
| `DASHBOARD_BOT_TOKEN_VINCULO` | Token del bot de Telegram dedicado al vínculo (lo lee n8n). |
| `DASHBOARD_GOOGLE_CLIENT_ID`, `DASHBOARD_GOOGLE_CLIENT_SECRET`, `DASHBOARD_GOOGLE_REDIRECT_URI` | Conexión de Gmail (OAuth2). |
| `DASHBOARD_FRONTEND_URL` | Adonde vuelve el navegador tras Google. Default `http://localhost:8080`; con Vite, `http://localhost:5173`. |
| `CORS_ORIGINS`, `DASHBOARD_TRUSTED_PROXIES` | Orígenes permitidos (nunca `*`) y proxy en el que se confía para la IP del cliente. |
| `DASHBOARD_ENABLE_DOCS`, `DASHBOARD_ALLOW_REGISTRATION` | Prender `/docs` (dev) y cerrar el alta de cuentas (instalación pública). |

Generar los secretos (usá valores distintos para cada uno; el segundo necesita `pip install cryptography`):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"                                  # DASHBOARD_JWT_SECRET y DASHBOARD_N8N_SECRET
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"     # DASHBOARD_ENC_KEY
```

### Credenciales que te tocan a vos

- **Gmail**: en Google Cloud Console creá un cliente OAuth (Web) en modo testing con tu cuenta como usuario de prueba, y cargá como URI de redirección **exactamente** el valor de `DASHBOARD_GOOGLE_REDIRECT_URI` (`http://localhost:8000/connections/gmail/callback`).
- **Telegram**: creá un bot nuevo con @BotFather (no reutilices el del Flujo 2), poné su token en `DASHBOARD_BOT_TOKEN_VINCULO`, importá `workflows/Flujo 3 — Telegram Vínculo de Cuenta.json`, cargale la credencial y activalo.

### Límites honestos

- Gmail y Telegram **reales** requieren esas credenciales; sin ellas la pantalla de Conexiones responde con un error controlado (Gmail) o el código nunca se confirma (Telegram).
- El webhook de Telegram necesita una **URL pública HTTPS** (`WEBHOOK_URL`, por ejemplo con ngrok).
- WhatsApp queda en `pending` por diseño ("Meta aprueba en 1-3 días hábiles"); no llama a Meta.
- Pedidos, tickets y catálogo son **globales**: todas las cuentas ven los mismos datos (un comercio por instalación). Detalle y demás desvíos: `SPEC_DASHBOARD_CLIENTE.md` §10.
- Para que el Flujo 1 real escriba órdenes, la instancia de n8n necesita sus credenciales de Postgres (`postgres:5432`) y SMTP (`mailpit:1025`).

Tests: `cd dashboard-api; .venv\Scripts\python -m pytest -q` (los de integración usan una BD aparte, `ecommerce_tesis_test` en `localhost:5433`, y se saltean si no está) y `cd dashboard-web; npm test; npm run build`. Más detalle del front y de la demo en vivo en `dashboard-web/README.md`.

---

## 📁 Estructura del proyecto

```
├── docker-compose.yml              ← Levanta los servicios (n8n, PostgreSQL, Mailpit, Grafana, dashboard-api, dashboard-web)
├── init_simple.sql                 ← Crea tablas y vistas en PostgreSQL
├── seed_expand.sql                 ← Carga productos, FAQs y datos históricos
├── migracion_dashboard_cliente.sql ← Tablas del dashboard (client_accounts, channel_connections)
├── seed_dashboard.sql              ← Cuenta demo del dashboard
├── demo_en_vivo.ps1                ← Dispara una orden en vivo contra n8n (para filmar)
├── backup.ps1                      ← Backup completo (BD + workflows)
├── restore.ps1                     ← Restaurar desde backup
├── CREDENCIALES.example.md         ← Guía detallada de credenciales
├── SETUP.md                        ← Guía de instalación extendida
│
├── workflows/
│   ├── Flujo 1 - Pipeline de Procesamiento de Órdenes SIMPLE.json
│   ├── Flujo 1 - Pipeline de Procesamiento de Órdenes PRODUCCION.json
│   ├── Flujo 2 - Chatbot Omnicanal IA.json
│   └── Flujo 2 - Chatbot Omnicanal IA PRODUCCION.json
│
├── dashboard-api/                  ← Backend FastAPI del portal (pytest)
├── dashboard-web/                  ← Frontend React + Vite servido por nginx (vitest)
├── SPEC_DASHBOARD_CLIENTE.md       ← Spec del dashboard; §10 lista los desvíos reales
│
├── docs/
│   ├── TESIS_FINAL_UTN_v3.pdf      ← Documento final de tesis
│   ├── SPEC_FLUJO1_PIPELINE_ORDENES.md
│   ├── SPEC_FLUJO2_CHATBOT_OMNICANAL.md
│   └── PROMPT_IA_CHATBOT.md        ← Prompt de GPT-4o-mini documentado
│
└── imagenes/                       ← Capturas de pantalla del sistema
```

---

## 🔧 Comandos útiles

```powershell
# Levantar todo
docker compose up -d

# Detener todo (sin borrar datos)
docker compose down

# Ver logs en tiempo real
docker compose logs -f n8n

# Reiniciar solo N8N
docker compose restart n8n

# Hacer backup completo
.\backup.ps1

# Restaurar desde backup
.\restore.ps1

# Acceder a la BD directamente
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis

# Ver todas las órdenes
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "SELECT * FROM orders ORDER BY received_at DESC LIMIT 10;"

# Ver métricas resumidas
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "SELECT * FROM v_metrics_summary;"
```

---

## ❗ Problemas frecuentes

| Problema | Solución |
|---------|---------|
| Docker no arranca | Verificar que Docker Desktop esté corriendo (ícono en la barra de tareas) |
| PostgreSQL no conecta | Esperar 30 segundos después de `docker compose up -d` y reintentar |
| N8N muestra error en nodos | Verificar que las credenciales estén configuradas (Paso 6) |
| Grafana muestra "No data" | Verificar que el datasource PostgreSQL esté configurado y muestre "Connection OK" |
| Workflows no activos | En N8N, abrir cada workflow y activar el toggle arriba a la derecha |
| Webhook no responde | Verificar que el workflow esté activo y que la URL sea correcta |

---

## 📄 Licencia

Proyecto académico — UTN FRM 2026. Uso educativo.
