# Guía de instalación desde cero

**Proyecto:** Automatización del ciclo post-venta en e-commerce con IA y N8N  
**UTN FRM — Trabajo Final de Grado**  
**Autores:** Santiago Sordi, Ignacio Odorico, Juan Cruz Ana

---

## Requisitos previos

Instalar antes de empezar:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — incluye Docker y Docker Compose
- [Git](https://git-scm.com/) — para clonar el repositorio

Verificar que estén instalados:
```powershell
docker --version
docker compose version
```

---

## Paso 1 — Clonar el repositorio

```powershell
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd Pipeline-de-automatización-del-ciclo-post-venta
```

---

## Paso 2 — Levantar los servicios

```powershell
docker compose up -d
```

Esto descarga las imágenes y levanta 4 contenedores:

| Contenedor | URL | Para qué |
|---|---|---|
| n8n | http://localhost:5678 | Motor de workflows |
| PostgreSQL | localhost:5432 | Base de datos |
| Mailpit | http://localhost:8025 | Bandeja de emails |
| Grafana | http://localhost:3000 | Dashboards de métricas |

Esperá 30 segundos hasta que todos estén healthy:
```powershell
docker ps
```
Todos deben mostrar `Up` en la columna STATUS.

---

## Paso 3 — Crear la estructura de la base de datos

```powershell
Get-Content init_simple.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
```

Esto crea las 5 tablas (`orders`, `products`, `interactions`, `tickets`, `faq_responses`) y las 5 vistas de métricas.

---

## Paso 4 — Cargar los datos de prueba

```powershell
Get-Content seed_expand.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
```

Esto carga:
- 20 productos en 8 categorías
- 22 FAQs para el chatbot
- Órdenes e interacciones históricas para las métricas

Verificar que los datos están:
```powershell
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "SELECT COUNT(*) FROM products; SELECT COUNT(*) FROM faq_responses;"
```
Debe mostrar 20 productos y 22 FAQs.

---

## Paso 5 — Importar los workflows en N8N

1. Abrí **http://localhost:5678**
2. Usuario: `admin@tesis.local` | Contraseña: `Admin123!`
3. Para cada archivo en la carpeta `workflows/`:
   - Menú izquierdo → **Workflows**
   - Botón **"..."** arriba a la derecha → **"Import from file"**
   - Seleccioná el archivo y click **Import**

Importar en este orden:
1. `Flujo 1 - Pipeline de Procesamiento de Órdenes SIMPLE.json` ← activar ✅
2. `Flujo 2 - Chatbot Omnicanal IA.json` ← activar ✅
3. `Flujo 1 - Pipeline de Procesamiento de Órdenes PRODUCCION.json` ← dejar inactivo
4. `Flujo 2 - Chatbot Omnicanal IA PRODUCCION.json` ← dejar inactivo

---

## Paso 6 — Configurar las credenciales en N8N

Ir a **http://localhost:5678** → **Credentials** → editar cada una:

### PostgreSQL
| Campo | Valor |
|---|---|
| Host | `postgres` |
| Port | `5432` |
| Database | `ecommerce_tesis` |
| User | `n8n_user` |
| Password | `n8n_pass` |
| SSL | `disabled` |

### SMTP (Mailpit)
| Campo | Valor |
|---|---|
| Host | `mailpit` |
| Port | `1025` |
| User | *(vacío)* |
| Password | *(vacío)* |
| SSL/TLS | `None` |

### OpenAI
| Campo | Valor |
|---|---|
| API Key | `sk-...` *(tu clave de OpenAI)* |

> Obtener API Key en: https://platform.openai.com → API Keys → Create new secret key

---

## Paso 7 — Configurar Grafana

1. Abrí **http://localhost:3000**
2. Usuario: `admin` | Contraseña: `admin`
3. Ir a **Connections → Data sources → Add data source**
4. Seleccioná **PostgreSQL**
5. Completar:

| Campo | Valor |
|---|---|
| Host | `postgres:5432` |
| Database | `ecommerce_tesis` |
| User | `n8n_user` |
| Password | `n8n_pass` |
| SSL Mode | `disable` |
| Version | `15` |

6. Click **"Save & test"** → debe decir "Database Connection OK"

Los dashboards se recrean automáticamente al correr el script de setup (ver abajo).

---

## Paso 8 — Verificar que todo funciona

Probá el Flujo 1 enviando una orden de prueba:

```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook/orden-nueva" -Method POST -ContentType "application/json" -Body '{"product_id": 1, "quantity": 1, "customer_email": "test@test.com", "customer_name": "Test User", "total_amount": 100}'
```

Debe responder con `status: confirmed` o `status: no_stock`.

Verificar el email en **http://localhost:8025** — debe aparecer el email de confirmación.

---

## Comandos útiles

```powershell
# Levantar todo
docker compose up -d

# Detener todo (sin borrar datos)
docker compose down

# Ver logs de n8n
docker compose logs -f n8n

# Hacer backup
.\backup.ps1

# Restaurar desde backup
.\restore.ps1

# Reiniciar solo n8n
docker compose restart n8n
```

---

## Estructura del proyecto

```
├── docker-compose.yml        ← Levanta los 4 servicios
├── init_simple.sql           ← Crea tablas y vistas en PostgreSQL
├── seed_expand.sql           ← Carga datos de prueba
├── backup.ps1                ← Script de backup
├── restore.ps1               ← Script de restauración
├── CREDENCIALES.example.md   ← Guía de credenciales
├── workflows/                ← Los 4 workflows de n8n
│   ├── Flujo 1 ... SIMPLE.json
│   ├── Flujo 1 ... PRODUCCION.json
│   ├── Flujo 2 ... SIMPLE.json
│   └── Flujo 2 ... PRODUCCION.json
├── docs/
│   ├── TESIS_COMPLETA.md     ← Fuente de la tesis
│   ├── TESIS_FINAL_UTN_v3.docx ← Word final para entregar
│   ├── SPEC_FLUJO1_*.md      ← Especificación técnica Flujo 1
│   └── SPEC_FLUJO2_*.md      ← Especificación técnica Flujo 2
└── imagenes/                 ← Capturas del proyecto
```

---

## Problemas frecuentes

**Docker no arranca:**
→ Verificar que Docker Desktop esté corriendo (ícono en la barra de tareas)

**PostgreSQL no conecta:**
→ Esperar 30 segundos después de `docker compose up -d` y reintentar

**N8N muestra error en los nodos:**
→ Verificar que las credenciales estén configuradas (Paso 6)

**Grafana muestra "No data":**
→ Verificar que el datasource PostgreSQL esté configurado y muestre "Connection OK"

**Workflows no activos:**
→ En n8n, abrir cada workflow y activar el toggle arriba a la derecha
