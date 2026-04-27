<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:1a7f5a,100:2dd4bf&height=220&section=header&text=🛒%20Pipeline%20Post-Venta%20IA&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Automatización%20completa%20del%20ciclo%20post-venta%20en%20E-commerce&descSize=16&descColor=a3e4d7&descAlignY=55"/>

<div align="center">

<img src="docs/imagenes/robot_heart.png" width="180" alt="Bot Mascota del Proyecto"/>

<br/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&duration=3000&pause=1000&color=2DD4BF&center=true&vCenter=true&multiline=true&repeat=true&width=700&height=140&lines=🤖+Sistema+de+Automatización+Post-Venta+con+IA;📦+Procesamiento+de+Órdenes+en+Milisegundos;💬+Chatbot+Omnicanal+24%2F7+con+GPT-4o-mini;📊+Métricas+en+Tiempo+Real+con+Grafana)](https://git.io/typing-svg)

<br/>

![N8N](https://img.shields.io/badge/N8N-Orquestador-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_15-Base_de_Datos-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Infraestructura-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![OpenAI](https://img.shields.io/badge/GPT--4o--mini-IA-412991?style=for-the-badge&logo=openai&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-Dashboards-F46800?style=for-the-badge&logo=grafana&logoColor=white)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Canal-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Canal-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![Gmail](https://img.shields.io/badge/Gmail-Canal-EA4335?style=for-the-badge&logo=gmail&logoColor=white)

<br/>

> **Trabajo Final de Grado — UTN FRM 2026**

</div>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## <img src="https://media.giphy.com/media/iY8CRBdQXODJSCERIr/giphy.gif" width="30"> ¿Qué es este proyecto?

Sistema de automatización completo del ciclo post-venta para una **PyME e-commerce argentino**, implementado con **N8N** como orquestador central. El sistema reemplaza el **100% de las operaciones manuales** post-venta mediante dos flujos que trabajan en paralelo:

<table>
<tr>
<td align="center"><b>⚡ Flujo</b></td>
<td align="center"><b>📛 Nombre</b></td>
<td align="center"><b>🎯 Qué hace</b></td>
</tr>
<tr>
<td align="center"><b>Flujo 1</b></td>
<td>🔄 Pipeline de Procesamiento de Órdenes</td>
<td>Recibe órdenes, verifica stock, confirma el pedido y notifica al cliente por email — <b>en milisegundos</b>, sin intervención humana</td>
</tr>
<tr>
<td align="center"><b>Flujo 2</b></td>
<td>🤖 Chatbot Omnicanal con IA</td>
<td>Atiende consultas de clientes por WhatsApp, Telegram y Email <b>24/7</b> usando GPT-4o-mini</td>
</tr>
</table>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## <img src="https://media.giphy.com/media/QssGEmpkyEOhBCb7e1/giphy.gif" width="30"> Arquitectura

<div align="center">

```
┌──────────────────────────────────────────────────────────────┐
│                     🐳 Docker Network                        │
│                                                              │
│   ┌──────────┐    ┌──────────────┐    ┌──────────────┐      │
│   │   n8n    │───▶│  PostgreSQL  │◀───│   Grafana    │      │
│   │  :5678   │    │    :5432     │    │    :3000     │      │
│   │(Flujo 1) │    │ ecommerce_  │    │ (Dashboards) │      │
│   │(Flujo 2) │    │   tesis     │    │              │      │
│   └────┬─────┘    └──────────────┘    └──────────────┘      │
│        │                                                     │
│        ▼                                                     │
│   ┌──────────┐                                               │
│   │ Mailpit  │ ← Emails de confirmación (demo local)        │
│   │  :8025   │                                               │
│   └──────────┘                                               │
└──────────────────────────────────────────────────────────────┘
         │
         ▼ (solo versión PRODUCCION)
  OpenAI API · WhatsApp Business · Telegram Bot · Gmail
```

</div>

### 🛠️ Stack Tecnológico

<table>
<tr>
<td align="center"><b>🔧 Tecnología</b></td>
<td align="center"><b>📌 Versión</b></td>
<td align="center"><b>🎯 Rol</b></td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/N8N-EA4B71?style=flat-square&logo=n8n&logoColor=white"/> <b>N8N</b></td>
<td><code>latest</code></td>
<td>Orquestador de workflows</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white"/> <b>PostgreSQL</b></td>
<td><code>15</code></td>
<td>Base de datos unificada</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white"/> <b>Docker / Docker Compose</b></td>
<td><code>3.8</code></td>
<td>Infraestructura local</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Mailpit-16A394?style=flat-square&logo=maildotru&logoColor=white"/> <b>Mailpit</b></td>
<td><code>latest</code></td>
<td>SMTP local para testing</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Grafana-F46800?style=flat-square&logo=grafana&logoColor=white"/> <b>Grafana</b></td>
<td><code>latest</code></td>
<td>Dashboards de métricas</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white"/> <b>GPT-4o-mini</b></td>
<td><code>vía API</code></td>
<td>Clasificación de intención y respuestas IA</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/WhatsApp-25D366?style=flat-square&logo=whatsapp&logoColor=white"/> <b>WhatsApp Business Cloud API</b></td>
<td><code>Meta v18.0</code></td>
<td>Canal WhatsApp (producción)</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Telegram-26A5E4?style=flat-square&logo=telegram&logoColor=white"/> <b>Telegram Bot API</b></td>
<td><code>nativo N8N</code></td>
<td>Canal Telegram</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Gmail-EA4335?style=flat-square&logo=gmail&logoColor=white"/> <b>Gmail OAuth2</b></td>
<td><code>nativo N8N</code></td>
<td>Canal Email (producción)</td>
</tr>
</table>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## <img src="https://media.giphy.com/media/W5eoZHPpUx9sapR0eu/giphy.gif" width="30"> Flujo 1 — Pipeline de Procesamiento de Órdenes

> **Trigger:** `POST http://localhost:5678/webhook/orden-nueva`

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

<details>
<summary><b>📈 Métricas capturadas automáticamente</b></summary>
<br/>

| Métrica | Descripción |
|---------|-------------|
| ⏱️ **MTTD** | Tiempo desde que entra la orden hasta que se procesa |
| 📬 **MTTR** | Tiempo desde el procesamiento hasta que el cliente recibe el email |

</details>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## <img src="https://media.giphy.com/media/LnQjpWaON8nhr21vNW/giphy.gif" width="30"> Flujo 2 — Chatbot Omnicanal con IA

> **Triggers:** WhatsApp webhook + Telegram Bot + Gmail (polling cada 1 min)

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

<details>
<summary><b>📈 Métricas capturadas automáticamente</b></summary>
<br/>

| Métrica | Descripción |
|---------|-------------|
| ⏱️ **TMR** | Tiempo de respuesta del chatbot de punta a punta |

</details>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## <img src="https://media.giphy.com/media/fYSnHlufseco8Fh93Z/giphy.gif" width="30"> Base de Datos

**5 tablas** en `ecommerce_tesis`:

<table>
<tr>
<td align="center"><b>📋 Tabla</b></td>
<td align="center"><b>📝 Descripción</b></td>
</tr>
<tr><td><code>products</code></td><td>Catálogo de productos con stock y precio</td></tr>
<tr><td><code>orders</code></td><td>Órdenes con su ciclo de vida completo</td></tr>
<tr><td><code>interactions</code></td><td>Log de conversaciones del chatbot</td></tr>
<tr><td><code>tickets</code></td><td>Reclamos creados automáticamente</td></tr>
<tr><td><code>faq_responses</code></td><td>Base de conocimiento del chatbot (editable en caliente)</td></tr>
</table>

**5 vistas** para Grafana: `v_order_processing_time`, `v_daily_order_summary`, `v_chatbot_response_time`, `v_daily_chatbot_summary`, `v_metrics_summary`

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## <img src="https://media.giphy.com/media/WUlplcMpOCEmTGBtBW/giphy.gif" width="30"> Instalación y Uso

### 📋 Requisitos previos

<div align="center">

![Docker](https://img.shields.io/badge/Docker_Desktop-Requerido-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Git](https://img.shields.io/badge/Git-Requerido-F05032?style=for-the-badge&logo=git&logoColor=white)

</div>

Verificar instalación:
```powershell
docker --version
docker compose version
```

---

<details>
<summary><h3>📦 Paso 1 — Clonar el repositorio</h3></summary>

```powershell
git clone https://github.com/IgnacioOdorico/Pipeline-de-automatizacion-del-ciclo-post-venta.git
cd Pipeline-de-automatización-del-ciclo-post-venta
```

</details>

<details>
<summary><h3>🐳 Paso 2 — Levantar los servicios</h3></summary>

```powershell
docker compose up -d
```

Esperá ~30 segundos y verificá que todos estén corriendo:
```powershell
docker ps
```

| Servicio | URL | Credenciales |
|---------|-----|-------------|
| **N8N** | http://localhost:5678 | `admin` / `admin123` |
| **Grafana** | http://localhost:3000 | `admin` / `admin` |
| **Mailpit** | http://localhost:8025 | — |
| **PostgreSQL** | localhost:5432 | `n8n_user` / `n8n_pass` |

</details>

<details>
<summary><h3>🗄️ Paso 3 — Crear la base de datos</h3></summary>

```powershell
Get-Content init_simple.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
```

</details>

<details>
<summary><h3>🌱 Paso 4 — Cargar datos de prueba</h3></summary>

```powershell
Get-Content seed_expand.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
```

Verificar:
```powershell
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "SELECT COUNT(*) FROM products; SELECT COUNT(*) FROM faq_responses;"
```
> ✅ Debe mostrar **20 productos** y **22 FAQs**.

</details>

<details>
<summary><h3>📥 Paso 5 — Importar los workflows en N8N</h3></summary>

1. Abrí **http://localhost:5678**
2. Ir a **Workflows → botón "..." → Import from file**
3. Importar en este orden:

| Archivo | Estado |
|---------|--------|
| `workflows/Flujo 1 - Pipeline de Procesamiento de Órdenes SIMPLE.json` | ✅ Activar |
| `workflows/Flujo 2 - Chatbot Omnicanal IA.json` | ✅ Activar |
| `workflows/Flujo 1 - ... PRODUCCION.json` | ⏸ Dejar inactivo |
| `workflows/Flujo 2 - ... PRODUCCION.json` | ⏸ Dejar inactivo |

</details>

<details>
<summary><h3>🔑 Paso 6 — Configurar credenciales en N8N</h3></summary>

Ir a **http://localhost:5678 → Credentials**

#### 🐘 PostgreSQL
| Campo | Valor |
|-------|-------|
| Host | `postgres` |
| Port | `5432` |
| Database | `ecommerce_tesis` |
| User | `n8n_user` |
| Password | `n8n_pass` |
| SSL | `disabled` |

#### 📧 SMTP (Mailpit — solo para demo local)
| Campo | Valor |
|-------|-------|
| Host | `mailpit` |
| Port | `1025` |
| User | *(vacío)* |
| Password | *(vacío)* |
| SSL/TLS | `None` |

#### 🧠 OpenAI
| Campo | Valor |
|-------|-------|
| API Key | `sk-...` *(tu clave de https://platform.openai.com)* |

</details>

<details>
<summary><h3>📊 Paso 7 — Configurar Grafana</h3></summary>

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

</details>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## <img src="https://media.giphy.com/media/VgCDAzcKvsR6OM0uWg/giphy.gif" width="30"> Cómo enviar datos manualmente a N8N

<details>
<summary><b>⚡ Opción 1 — PowerShell (recomendado en Windows)</b></summary>

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/orden-nueva" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "order_number": "ORD-2026-0099",
    "customer_name": "Juan Pérez",
    "customer_email": "juan@test.com",
    "customer_phone": "+5492615001234",
    "product_sku": "PROD-001",
    "quantity": 2
  }'
```

</details>

<details>
<summary><b>🐧 Opción 2 — curl (desde cualquier terminal)</b></summary>

```bash
curl -X POST http://localhost:5678/webhook/orden-nueva \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORD-2026-0099",
    "customer_name": "Juan Pérez",
    "customer_email": "juan@test.com",
    "customer_phone": "+5492615001234",
    "product_sku": "PROD-001",
    "quantity": 2
  }'
```

</details>

<details>
<summary><b>🔧 Opción 3 — Postman o Insomnia (interfaz gráfica)</b></summary>

1. Crear nueva request **POST**
2. URL: `http://localhost:5678/webhook/orden-nueva`
3. Body → **raw → JSON**
4. Pegar el JSON y click **Send**

</details>

<details>
<summary><b>🤖 Opción 4 — Probar el chatbot manualmente</b></summary>

Para simular un mensaje de WhatsApp/Telegram al Flujo 2:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:5678/webhook/whatsapp" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5492615001234",
            "text": { "body": "Hola, ¿cuál es el estado de mi pedido ORD-2026-0001?" }
          }],
          "contacts": [{ "profile": { "name": "Juan Pérez" } }]
        }
      }]
    }]
  }'
```

</details>

<details>
<summary><b>🖥️ Opción 5 — Desde N8N directamente (sin HTTP)</b></summary>

1. Abrí el workflow en **http://localhost:5678**
2. Click en el nodo **Webhook**
3. Click en **"Listen for test event"**
4. Enviá el request desde PowerShell/Postman
5. El workflow se ejecuta y podés ver el resultado en cada nodo

</details>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 📁 Estructura del proyecto

```
├── docker-compose.yml              ← Levanta los 4 servicios
├── init_simple.sql                 ← Crea tablas y vistas en PostgreSQL
├── seed_expand.sql                 ← Carga productos, FAQs y datos históricos
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
├── docs/
│   ├── TESIS_FINAL_UTN_v3.pdf      ← Documento final de tesis
│   ├── SPEC_FLUJO1_PIPELINE_ORDENES.md
│   ├── SPEC_FLUJO2_CHATBOT_OMNICANAL.md
│   └── PROMPT_IA_CHATBOT.md        ← Prompt de GPT-4o-mini documentado
│
└── imagenes/                       ← Capturas de pantalla del sistema
```

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🔧 Comandos útiles

```powershell
# 🚀 Levantar todo
docker compose up -d

# ⏹️ Detener todo (sin borrar datos)
docker compose down

# 📋 Ver logs en tiempo real
docker compose logs -f n8n

# 🔄 Reiniciar solo N8N
docker compose restart n8n

# 💾 Hacer backup completo
.\backup.ps1

# ♻️ Restaurar desde backup
.\restore.ps1

# 🗄️ Acceder a la BD directamente
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis

# 📦 Ver todas las órdenes
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "SELECT * FROM orders ORDER BY received_at DESC LIMIT 10;"

# 📊 Ver métricas resumidas
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "SELECT * FROM v_metrics_summary;"
```

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## ❗ Problemas frecuentes

| Problema | Solución |
|---------|---------|
| 🐳 Docker no arranca | Verificar que Docker Desktop esté corriendo (ícono en la barra de tareas) |
| 🐘 PostgreSQL no conecta | Esperar 30 segundos después de `docker compose up -d` y reintentar |
| ⚠️ N8N muestra error en nodos | Verificar que las credenciales estén configuradas (Paso 6) |
| 📊 Grafana muestra "No data" | Verificar que el datasource PostgreSQL esté configurado y muestre "Connection OK" |
| 🔴 Workflows no activos | En N8N, abrir cada workflow y activar el toggle arriba a la derecha |
| 🔗 Webhook no responde | Verificar que el workflow esté activo y que la URL sea correcta |

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<div align="center">

## 👥 Equipo

<img src="docs/imagenes/robot_team.png" width="220" alt="Equipo del Proyecto"/>

<br/><br/>

| 👤 Integrante | 🎓 Rol |
|:---:|:---:|
| **Ignacio Odorico** | Desarrollador |
| **Santiago Sordi** | Desarrollador |
| **Juan Cruz Ana** | Desarrollador |

<br/>

**Tutor:** Prof. Alberto Cortez

<br/>

</div>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<div align="center">

## 📄 Licencia

Proyecto académico — **UTN FRM 2026**. Uso educativo.

<br/>

![Made with Love](https://img.shields.io/badge/Hecho_con-❤️-FF0000?style=for-the-badge)
![UTN FRM](https://img.shields.io/badge/UTN-FRM_2026-1a7f5a?style=for-the-badge)
![Status](https://img.shields.io/badge/Estado-En_Desarrollo-2DD4BF?style=for-the-badge)

</div>

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:1a7f5a,100:2dd4bf&height=120&section=footer"/>
