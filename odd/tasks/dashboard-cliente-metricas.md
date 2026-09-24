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
- [x] K3 Frontend: página Métricas con los 4 tipos de gráfico en SVG propio, polling, estados, nav
- [x] K4 Reconstruir stack, smoke autenticado con datos reales, docs (README, SPEC, `docs/API_METRICAS.md`)

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

### K3 Frontend (cerrado)

- **Ruta elegida**: página nueva `dashboard-web/src/pages/MetricasPage.tsx` (`/metricas`, nav propio) con dos secciones independientes — `components/metrics/OrdersMetricsSection.tsx` y `ChatbotMetricsSection.tsx` — cada una con su propio `useQuery` (polling 10 s) contra `metricsApi.orders`/`metricsApi.chatbot` (`api/endpoints.ts`). Filtros compartidos (`components/metrics/MetricsFilters.tsx`): ventana de tiempo y origen del dato.
- **Gráficos SVG propios**, sin librería, mismo criterio que el diagrama de Workflow: `DonutChart`, `BarChart`, `StackedAreaChart` (`components/metrics/`), cada uno sobre lógica pura testeada aparte (`lib/donutChart.ts`, `lib/barChart.ts`, `lib/areaChart.ts`, `lib/chartAxis.ts`).
- **TDD real, RED→GREEN observado** (lógica pura antes del código):
  - `metricsFilters.test.ts`, `chartAxis.test.ts`, `donutChart.test.ts`, `barChart.test.ts`, `areaChart.test.ts`, `metricsApi.test.ts`: RED → `npx vitest run <esos 6 archivos>` → `6 failed` (módulos/exports inexistentes) → implementación → GREEN → `36 passed`.
  - `chartColors.test.ts` (paleta categórica + contraste): GREEN a la primera tras crear `lib/chartColors.ts` + tokens `--chart-1..8` → `21 passed`.
  - Componentes (`donutChartComponent`, `barChartComponent`, `stackedAreaChartComponent`, `metricasPage`): tests escritos y corridos después de cada componente (no antes) — GREEN a la primera en todos, salvo un bug real encontrado en la revisión visual (ver abajo).
  - Suite completa: `npm test` → `56 archivos, 889 passed, 0 failed`. `npm run build` → `tsc --noEmit && vite build` OK (`193 modules transformed`, sin errores de tipos).
- **Bug real encontrado y corregido en la revisión visual** (no por un test, por mirar la pantalla): las etiquetas de dos palabras del eje de `BarChart` ("Pregunta frecuente", "Estado de pedido") se superponían con la barra de al lado en el ancho real de la tarjeta. Se agregó `lib/barChart.ts#wrapBarLabel` (con test RED→GREEN, `barChart.test.ts`) que corta la etiqueta en el espacio más cercano a la mitad, y `BarChart.tsx` la dibuja en 2 líneas con `<tspan>`. Confirmado corregido en una nueva revisión visual (capturas: labels en 2 líneas, sin pisarse, en 1280 px y 375 px).
- **Decisiones no obvias**:
  - `data_source` compartido entre los dos bloques con dominios distintos (ver `docs/API_METRICAS.md`): un solo selector en la página; `lib/metricsFilters.ts` resuelve el parámetro por endpoint (`ordersDataSourceParam` pasa cualquier valor, `chatbotDataSourceParam` solo deja pasar `measured|synthetic`). Elegir "Carga manual" sigue funcionando en Pedidos y en Chatbot se omite el filtro (histórico sin filtrar) con un aviso visible en ese bloque (`chatbotDataSourceIgnored`) en vez de romper o mandar un valor que la API rechazaría con 422.
  - Eje de fechas (`lib/chartAxis.ts#isoDateShortLabel`) nunca pasa la fecha por `new Date()`/zona horaria: `daily[].date` es "fecha calendario UTC" (no un instante); convertirla a la hora de negocio (Mendoza, UTC-3) como hace el resto de `lib/format.ts` correría el día mostrado un día para atrás a la medianoche. Se formatea con un split de texto puro.
  - Paleta categórica nueva (`lib/chartColors.ts`, tokens `--chart-1..8`): el sistema de diseño solo tenía brand + 3 colores de feedback (insuficiente para 8 estados de orden sin repetir color en una dona). Se agregaron 8 tonos, verificados con los mismos helpers de contraste del resto del front pero contra el umbral correcto (`>= 3:1`, WCAG 1.4.11: es color de gráfico, no texto — no 4.5:1).
  - Accesibilidad de los 3 gráficos: SVG con `role="img"` + `<title>`/`<desc>` con el desglose exacto (etiqueta, valor, %) como fuente accesible; la leyenda/eje visible es la misma información para quien mira la pantalla y se marca `aria-hidden` para no duplicar el anuncio en un lector de pantalla (se eligió esta opción, no una tabla oculta aparte, documentado en el comentario de cada componente).
  - `BarChart`: un intent sin respuestas (`avg_tmr_seconds: null`) se dibuja como un hueco punteado con "Sin respuestas", nunca como una barra en 0 (se leería como "responde instantáneo" — requisito explícito del usuario). Una barra con dato real tiene un alto mínimo visible aunque el promedio sea 0s exactos.
  - `usePrefersReducedMotion()` (ya existente) gatea las clases `--animated` de los 3 gráficos; además el bloque global `@media (prefers-reduced-motion: reduce)` de `global.css` ya apaga cualquier animación/transición del sitio entero (doble cobertura, mismo patrón que `WorkflowCanvas`).
  - Polling: 10 s en los dos bloques (vs. 3 s del feed de Monitoreo), sin manejo manual de "pestaña oculta" — se apoya en el comportamiento por defecto de TanStack Query (`refetchIntervalInBackground: false`), mismo criterio ya usado en `MonitoreoWorkflowPage`.
- **No implementado / fuera de alcance de K3**: no se persisten los filtros (ventana/origen) entre navegaciones ni en la URL — quedan en estado local de la página. No se agregó ningún panel de "precisión/accuracy" (decisión explícita del usuario, ver cabecera de este archivo).
- **Revisión visual**: servido el build (`vite build` → `dist/`) con un servidor Node mínimo fuera del repo (`%TEMP%\...\scratchpad\mock-server.js`, sin dependencias) que sirve `dist/` y mockea `GET /api/me`, `GET /api/metrics/orders` y `GET /api/metrics/chatbot` con datos realistas que varían según `hours` (24 → sin datos, 168 → un solo día, sin `hours` → 21 días con intents sin respuestas y los 8 estados de orden). Revisado en 1280 px y 375 px: estado con datos (dona de 8 estados, área apilada de 21 días, barras con un intent en "Sin respuestas"), los dos vacíos ("Todavía no hay pedidos/interacciones para este período"), la serie de una sola muestra (tramo plano a todo el ancho, confirmado visualmente) y el aviso de "Carga manual" ignorado en Chatbot. Sin cuenta demo real (token de mentira inyectado por el mock). Servidor cerrado al terminar (`TaskStop`).
- **Commits** (rama `feature/dashboard-cliente`, sin push): `3524088` (lib+tipos+cliente API), `539d2a2` (dona), `c503f20` (barras), `3d82869` (área apilada), `007afb8` (bloque Pedidos), `5f10719` (bloque Chatbot + página), `beca05a` (nav/ruta).

## Evidencia de K4 (verificada por el orquestador)
- `docker compose up -d --build dashboard-api dashboard-web`: ambos `Up`/`healthy`. `/`, `/metricas` y `/monitoreo` responden 200 (fallback SPA).
- Smoke real por `http://localhost:8080/api` con cuenta e2e descartable (borrada al terminar; conteo de `client_accounts` idéntico antes/después: 1):
  - `GET /metrics/orders`: `avg_mttd_seconds=90.0`, `avg_mttr_seconds=120.0`, `avg_end_to_end_seconds=210.0`, `total_orders=22`, `by_status` con las 8 claves reales, `daily` con 91 días sin huecos.
  - `GET /metrics/chatbot`: todo en `null`/0 (coherente: `interactions` sigue vacía porque el Flujo 2 no está corriendo — ver `odd/tasks/dashboard-cliente-monitoreo.md`).
  - `hours` fuera de rango → 422; `data_source=e4_manual` en `/metrics/chatbot` → 422; sin JWT → 401.
- Suites completas: `pytest` 527 passed; `npm test` 892 passed en 56 archivos; `npm run build` OK.
- Docs: `docs/API_METRICAS.md` ya cerrado por K1/K2; `SPEC_DASHBOARD_CLIENTE.md` §1/§5/§10 ya actualizado por K1/K2. README y CLAUDE.md: sección "Métricas" agregada.

### No verificado
Cómo se ve `/metricas` con sesión real en el navegador (no me logueo con la cuenta demo), y los gráficos de Chatbot con datos reales (dependen del Flujo 2, ver el recordatorio de abajo).

## Próximo paso
Que el usuario revise `/metricas` a ojo con la cuenta demo, y cargue las credenciales de n8n (ver "Recordatorio pendiente" arriba) para que el bloque Chatbot deje de estar vacío. Push de la rama según decisión del usuario.
