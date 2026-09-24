# API de Métricas (`/metrics/*`)

Contrato de los endpoints de la sección "Métricas" del portal: reemplazo **en vivo**, dentro del propio dashboard, de los paneles de los dos tableros de Grafana (`grafana/dashboards/tesis-flujo1.json` y `tesis-flujo2.json`). Todos son **GET, de solo lectura**, y requieren `Authorization: Bearer <JWT>` (sin token: `401`). La API devuelve datos **estructurados**: las etiquetas en español las pone el front.

Código: `dashboard-api/app/routers/metrics.py` y `dashboard-api/app/core/metrics.py`. Tests: `dashboard-api/tests/test_metrics_orders.py` y `test_metrics_chatbot.py`.

Distinción con Monitoreo (`docs/API_MONITOREO.md`): Monitoreo es el feed de eventos y la traza de ejecución del workflow (operación, "qué está pasando ahora"); Métricas son los KPIs agregados de la tesis (MTTD/MTTR/TMR, distribuciones, series diarias — "cómo viene funcionando el sistema").

## Convenciones

- **Fechas**: `generated_at` es ISO 8601 en UTC con milisegundos y `Z` (`"2026-09-21T14:05:00.120Z"`), igual que el resto de la API. Las fechas de las series diarias (`daily[].date`, `by_channel_daily[].date`) son **fecha calendario en UTC**, sin hora (`"2026-09-21"`), calculadas con `(columna AT TIME ZONE 'UTC')::date` para no depender del `timezone` de sesión de PostgreSQL.
- **Errores**: `{"detail": "<mensaje en español>"}`. `422` para `hours` fuera de rango o `data_source` fuera de dominio.
- **`hours`**: entero opcional, `1..8760` (365 días). **Si se omite, es histórico completo**: los agregados escalares (promedios, totales, distribuciones) no se acotan por fecha. La única excepción es la **serie diaria**, que sin `hours` se acota a los últimos **90 días** (`MAX_HISTORICAL_DAYS` en `app/core/metrics.py`) para no devolver una fila por cada día desde el origen de los datos; con `hours`, la serie cubre exactamente esa ventana.
- **`data_source`**: opcional.
  - `GET /metrics/orders` acepta `measured | synthetic | e4_manual` (dominio de `orders.data_source`, init_simple.sql:65-66).
  - `GET /metrics/chatbot` acepta solo `measured | synthetic` (dominio de `interactions.data_source`, init_simple.sql:113-114 — **no** incluye `e4_manual`, que solo existe en `orders`). Pedir `e4_manual` en este endpoint da `422`.
- **Series diarias sin huecos**: `daily` y `by_channel_daily` siempre traen una fila por cada día de la ventana, incluso en 0, para que un gráfico de líneas no salte. Nunca es una lista vacía salvo un caso degenerado de ventana de 0 días (no alcanzable con los rangos válidos de `hours`).
- **Nunca 500 por falta de datos**: sin filas que matcheen el filtro, los promedios son `null` (nunca `0` ni error) y los contadores/distribuciones son `0`.

---

## 1. Órdenes — `GET /metrics/orders`

Reemplaza los paneles de MTTD/MTTR/End-to-end (stat), Órdenes totales (stat), Distribución de estados (pie) y Órdenes procesadas por día (timeseries) de `tesis-flujo1.json`. Misma semántica de cálculo que esos paneles (`EXTRACT(EPOCH FROM (...))`), pero recalculada en vivo sobre `orders` (no sobre `v_metrics_summary`, que es un snapshot que no acepta ventana ni filtro).

Query: `hours` (opcional, `1..8760`), `data_source` (opcional, `measured | synthetic | e4_manual`).

```json
{
  "window_hours": 168,
  "generated_at": "2026-09-21T14:05:00.120Z",
  "avg_mttd_seconds": 34.2,
  "avg_mttr_seconds": 18.7,
  "avg_end_to_end_seconds": 52.9,
  "total_orders": 42,
  "by_status": {
    "pending": 1, "processing": 0, "confirmed": 30, "shipped": 4,
    "delivered": 2, "no_stock": 3, "cancelled": 1, "error": 1
  },
  "daily": [
    { "date": "2026-09-14", "total_orders": 5, "confirmed": 4, "shipped": 0,
      "delivered": 0, "no_stock": 1, "cancelled": 0, "error": 0 },
    { "date": "2026-09-15", "total_orders": 0, "confirmed": 0, "shipped": 0,
      "delivered": 0, "no_stock": 0, "cancelled": 0, "error": 0 }
  ]
}
```

- `avg_mttd_seconds` = `AVG(processed_at - received_at)` solo sobre filas con `processed_at IS NOT NULL`. `avg_mttr_seconds` = `AVG(notified_at - processed_at)` solo con `notified_at IS NOT NULL`. `avg_end_to_end_seconds` = `AVG(notified_at - received_at)` solo con **ambos** no nulos. Cualquiera de los tres es `null` sin filas que califiquen.
- `total_orders` y `by_status` cuentan **todas** las órdenes de la ventana (con o sin `processed_at`/`notified_at`). `by_status` trae siempre las 8 claves del dominio real de `orders.status` (init_simple.sql:51-60), con `0` donde no haya filas.
- `daily`: agrupado por `received_at` (fecha calendario UTC), orden ascendente. Los campos de estado del día son un subconjunto deliberado del dominio completo (`confirmed, shipped, delivered, no_stock, cancelled, error`, sin `pending`/`processing`) para el gráfico apilado de la thesis; `by_status` arriba sigue siendo la fuente de verdad para el dominio completo.

## 2. Chatbot — `GET /metrics/chatbot`

Reemplaza TMR promedio e Interacciones totales (stat), TMR promedio por intent (bar), Distribución de intents (pie) e Interacciones por día y canal (timeseries apilado) de `tesis-flujo2.json`. **Fuente: solo `interactions`, nunca `v_chatbot_corpus`** (esa vista está congelada a `data_source='measured'` y a la ventana `2026-08-12 23:00–24:00`, ver `docs/DESVIOS_SPEC.md` §2.12/§3.2 — no es "en vivo"). El panel "Precisión (accuracy) 92.7%" de `tesis-flujo2.json` **se omite**: es un literal SQL fijo (`SELECT 92.7 AS "Accuracy"`), no una métrica calculada.

`v_daily_chatbot_summary` en sí no depende de la ventana congelada (agrupa toda la tabla `interactions` sin filtro de fecha ni de `data_source`), pero tampoco se usa: no admite `hours` ni `data_source` como parámetro, ni rellena huecos de días sin datos, así que recalcular directo sobre `interactions` evita depender de sus columnas y de cualquier supuesto oculto de la vista.

Query: `hours` (opcional, `1..8760`), `data_source` (opcional, **solo** `measured | synthetic`).

```json
{
  "window_hours": 168,
  "generated_at": "2026-09-21T14:05:00.120Z",
  "avg_tmr_seconds": 4.1,
  "total_interactions": 37,
  "by_intent": {
    "FAQ": { "count": 15, "avg_tmr_seconds": 3.2 },
    "ESTADO_PEDIDO": { "count": 12, "avg_tmr_seconds": 5.5 },
    "RECLAMO": { "count": 6, "avg_tmr_seconds": 6.8 },
    "GENERAL": { "count": 4, "avg_tmr_seconds": 2.9 }
  },
  "by_channel_daily": [
    { "date": "2026-09-14", "whatsapp": 3, "telegram": 1, "email": 0 },
    { "date": "2026-09-15", "whatsapp": 0, "telegram": 0, "email": 0 }
  ]
}
```

- `avg_tmr_seconds` (general y por intent) = `AVG(responded_at - received_at)` solo sobre filas con `responded_at IS NOT NULL`; `null` sin respuestas en la ventana.
- `total_interactions` y `by_intent[*].count` cuentan **todas** las interacciones (respondidas o no). `by_intent` trae siempre las 4 claves del dominio real de `interactions.intent` (init_simple.sql:106-107).
- `by_channel_daily`: agrupado por `received_at` (fecha calendario UTC), orden ascendente, mismas 3 claves de canal siempre presentes (`whatsapp`, `telegram`, `email` — dominio de `interactions.channel`).

## 3. Nota para el front

- Polling sugerido ~10 s (son agregaciones, no eventos puntuales — más lento que el feed de Monitoreo).
- Tickets abiertos ya existe en `GET /dashboard/summary` (`tickets.open`); no se duplica acá.
- Las etiquetas humanas ("Tiempo medio de detección", "Tiempo medio de respuesta", nombres de estado/intent/canal en español) son del front; la API solo entrega claves de dominio y números.
