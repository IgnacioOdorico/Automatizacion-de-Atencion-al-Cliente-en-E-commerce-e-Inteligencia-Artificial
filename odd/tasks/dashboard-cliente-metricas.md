# ODD — Métricas (reemplazo en vivo de los paneles de Grafana)

**Rama:** `feature/dashboard-cliente` · **Origen:** pedido del usuario (2026-09-21): mostrar los gráficos de Grafana dentro del propio dashboard, en tiempo real.
**Decisión del usuario:** el panel "Precisión (accuracy) 92.7%" de `grafana/dashboards/tesis-flujo2.json` es un literal SQL (`SELECT 92.7 AS "Accuracy"`), no se calcula de ningún dato real → **se omite** del dashboard en vivo (no se replica, ni como referencia fija).
**TDD:** activo. **Runners:** `pytest` (dashboard-api, contra `ecommerce_tesis_test`), `npm test` + `npm run build` (dashboard-web).
**Alcance:** solo lectura sobre `orders`, `interactions`, `tickets`, y las vistas `v_metrics_summary`/`v_daily_order_summary` (NO `v_chatbot_corpus`: es una ventana congelada del 12/08, no "en vivo" — ver `docs/DESVIOS_SPEC.md` §2.12). No se toca Grafana, sus JSON, ni Flujos/BD.

## Paneles de Grafana auditados (`grafana/dashboards/*.json`)
| Grafana (`tesis-flujo1.json`) | Reemplazo en vivo |
|---|---|
| MTTD/MTTR/End-to-end (stat) | Igual, sobre `orders` reales (no `v_metrics_summary` congelada de una corrida; recalcular con ventana configurable) |
| Órdenes totales (stat) | Igual |
| Distribución de estados (pie) | Igual |
| Órdenes procesadas por día (timeseries) | Igual |

| Grafana (`tesis-flujo2.json`) | Reemplazo en vivo |
|---|---|
| TMR promedio, Interacciones totales | Igual, pero sobre `interactions` en vivo (no `v_chatbot_corpus`) |
| **Precisión (accuracy) 92.7** | **Omitido** (decisión del usuario) |
| Tickets abiertos | Ya existe en `/dashboard/summary`; reusar |
| TMR promedio por intent (bar) | Igual, en vivo |
| Distribución de intents (pie) | Igual, en vivo |
| Interacciones por día y canal (timeseries apilado) | Igual, en vivo |

## Diseño
- Página nueva **Métricas** (`/metricas`, nav propio; distinta de Monitoreo: Métricas = KPIs y gráficos agregados de negocio/tesis, Monitoreo = feed de eventos y traza del workflow).
- Backend: endpoints nuevos de solo lectura con ventana configurable (`hours`, default todo el histórico o 24h a decidir por el writer según lo que se vea mejor en video), reusando `data_source` filter existente donde aplica.
- Frontend: gráficos propios en SVG (mismo patrón que el diagrama de Workflow: sin librería de charts nueva) — stat cards, dona, barras, línea/área apilada. Polling ~10 s (menos frecuente que el feed de Monitoreo: son agregaciones, no eventos puntuales).
- Estados de carga/vacío/error consistentes con el resto (QueryView/ErrorState).

## Tareas
- [x] K1 Backend: `GET /metrics/orders` (MTTD/MTTR/end-to-end/total, distribución de estados, serie diaria)
- [x] K2 Backend: `GET /metrics/chatbot` (TMR promedio, interacciones totales, TMR por intent, distribución de intents, serie diaria por canal) — sobre `interactions`, NUNCA `v_chatbot_corpus`
- [ ] K3 Frontend: página Métricas con los 4 tipos de gráfico en SVG propio, polling, estados, nav
- [ ] K4 Reconstruir stack, smoke autenticado con datos reales, docs (README, SPEC, `docs/API_MONITOREO.md` o uno nuevo `docs/API_METRICAS.md`)

## Ruta por tarea
K1/K2: delegated direct (un writer backend). K3: delegated direct (un writer front, después del contrato). K4: delegated direct.

## Progreso / Evidencia

### K1+K2 Backend (cerrado)

- **Ruta elegida**: router nuevo `dashboard-api/app/routers/metrics.py` (no se extendió `dashboard.py` ni `monitoring_feed.py`) con lógica en `dashboard-api/app/core/metrics.py`, siguiendo el mismo patrón que `routers/monitoring_feed.py` + `core/monitoring_summary.py` (router delgado con `Depends(get_current_account_id)` a nivel de `APIRouter`, la query real vive en `core/`). Se separa de Monitoreo a propósito: Monitoreo = feed/traza operativa, Métricas = KPIs agregados de la tesis (documentado en la cabecera de ambos módulos y en `docs/API_METRICAS.md`).
- **TDD real, RED→GREEN observado**: se escribieron `dashboard-api/tests/test_metrics_orders.py` (13 tests) y `test_metrics_chatbot.py` (12 tests) antes del código.
  - RED: `.venv/Scripts/python -m pytest tests/test_metrics_orders.py tests/test_metrics_chatbot.py -q` → `25 failed` (endpoints inexistentes, 404 donde se esperaba 200/401/422).
  - Implementación de `core/metrics.py` + `routers/metrics.py` + registro en `main.py`.
  - GREEN parcial: 23/25 pasaron a la primera; 2 fallaron porque el test asumía `daily: []`/`by_channel_daily: []` sin datos, lo cual **contradice el requisito de "sin huecos"** (la serie debe cubrir la ventana acotada en 0, nunca lista vacía) — se corrigieron los tests, no el código, y quedó GREEN: `25 passed`.
  - Suite completa: `.venv/Scripts/python -m pytest -q` → `527 passed` (502 base + 25 nuevos, sin regresiones).
  - Refactor: se extrajo `_daily_params()` para no duplicar la lógica de la ventana acotada (`MAX_HISTORICAL_DAYS`) entre `_order_daily` y `_chatbot_by_channel_daily`; se re-corrió la suite de metrics (`25 passed`) tras el refactor.
- **Commit**: `72a4904` `feat(metrics): agregar GET /metrics/orders y /metrics/chatbot en vivo (K1+K2)` (5 archivos: `main.py`, `core/metrics.py`, `routers/metrics.py`, 2 archivos de test).
- **Decisiones no obvias**:
  - `data_source` tiene dos dominios distintos a propósito: `/metrics/orders` acepta `measured|synthetic|e4_manual` (dominio real de `orders.data_source`, init_simple.sql:65-66); `/metrics/chatbot` acepta **solo** `measured|synthetic` (dominio real de `interactions.data_source`, init_simple.sql:113-114 — `e4_manual` ahí da `422`). Cubierto por `test_metrics_orders_accepts_e4_manual_data_source` y `test_metrics_chatbot_rejects_e4_manual_data_source`.
  - `v_daily_chatbot_summary` **no** depende de la ventana congelada de `v_chatbot_corpus` (no tiene filtro de fecha ni de `data_source` en su definición) — se verificó leyendo `init_simple.sql:213-229`. Aun así no se usó: no admite `hours`/`data_source` como parámetro ni rellena huecos de días sin datos, así que recalcular directo sobre `interactions` evita depender de sus columnas fijas y de cualquier supuesto oculto. Documentado en `docs/API_METRICAS.md` §2.
  - Relleno de huecos en las series diarias: un `WITH days AS (SELECT generate_series(...))` LEFT JOIN contra la agregación por día, en un solo round-trip SQL (no en Python), para que cada día de la ventana aparezca aunque no tenga filas.
  - Tope de histórico sin `hours`: los agregados escalares (promedios/totales/distribuciones) **no se acotan** (son escalares, no crecen con el volumen). Solo la serie diaria se acota a `MAX_HISTORICAL_DAYS = 90` días — constante documentada en `app/core/metrics.py` y en `docs/API_METRICAS.md`.
  - MTTD/MTTR/end-to-end usan `FILTER (WHERE ... IS NOT NULL)` explícito en vez de confiar en que `AVG()` ignora `NULL` implícitamente, para que el filtrado sea legible y no dependa de un invariante de negocio no garantizado por el schema (que `notified_at IS NOT NULL` implique `processed_at IS NOT NULL`).
  - Corte de UTC en las fechas de la serie diaria: `(columna AT TIME ZONE 'UTC')::date`, para no depender del `timezone` de sesión de PostgreSQL (mismo espíritu que la gotcha de TIMESTAMP/TIMESTAMPTZ del repo).
- **No verificado**: no se probó contra una instancia real con columnas `TIMESTAMP` (sin zona) — el schema de test (`ecommerce_tesis_test`) usa `TIMESTAMPTZ` como `init_simple.sql`. El manejo (`AT TIME ZONE 'UTC'`) sigue el mismo patrón que `to_iso()`/`monitoring_summary.py`, pero no hay un caso de prueba que ejercite específicamente una columna `TIMESTAMP` legacy.

## Recordatorio pendiente (pedido explícito del usuario)
Cuando esto quede cerrado, avisarle que falta cargar en la UI de n8n las credenciales Postgres + SMTP (Flujo 1 y 2) y, para que el chatbot responda de verdad, OpenAI + un bot de Telegram propio del Flujo 2 (distinto al de vínculo del Flujo 3). Ver `odd/tasks/dashboard-cliente-monitoreo.md` → "Próximo paso" para el detalle ya dado.

## Próximo paso
Delegar K3 (frontend), ya con el contrato de K1/K2 cerrado en `docs/API_METRICAS.md`.
