# Spec — client-dashboard/metrics

## ADDED Requirements

### Requirement: Resumen de métricas del dashboard
El sistema SHALL exponer `GET /dashboard/summary` (JWT) que consolide el resumen ejecutivo: **MTTD, MTTR y TMR promedio desde `v_metrics_summary`** (sin recalcular promedios en la API), "pedidos hoy" contando `orders.received_at` del día (según `date_trunc`), y "tickets abiertos" contando `tickets.status IN ('open','in_progress')` de la cuenta.

#### Scenario: Resumen con datos
- **WHEN** se envía `GET /dashboard/summary` con JWT válido y hay órdenes/interacciones en la BD
- **THEN** el sistema responde 200 con totales y promedios MTTD/MTTR/TMR, pedidos de hoy y tickets abiertos

#### Scenario: Resumen sin datos
- **WHEN** no hay órdenes ni interacciones registradas
- **THEN** el sistema responde 200 con métricas en cero y el front muestra un estado vacío

### Requirement: Filtro de calidad de datos
El resumen del dashboard SHALL aceptar un parámetro opcional que filtre por `data_source='measured'` (evidencia real) vs mostrar todo. La columna `data_source` existe en `orders`, `interactions`, `tickets` y `stock_alerts`. Por defecto el dashboard muestra todo; el parámetro queda disponible para métricas "honestas".

#### Scenario: Resumen solo medido
- **WHEN** se pide el resumen con el filtro de datos medidos activado
- **THEN** el sistema excluye filas sintéticas y semillas del conteo y los promedios

### Requirement: Cards de la página Dashboard
El front SHALL mostrar la página Dashboard con cards de resumen (pedidos hoy, tickets abiertos, MTTD, MTTR, TMR) alimentadas por `/dashboard/summary`, con formato legible (segundos → duración o días-horas minutos según magnitud).

#### Scenario: Render de cards
- **WHEN** el resumen llega al front
- **THEN** se renderizan las cards con los valores formateados y las etiquetas MTTD/MTTR/TMR explicadas

### Requirement: Polling en vivo de 3-5 segundos
Las páginas Dashboard y Pedidos SHALL refrescar sus datos en un intervalo fijo de entre 3 y 5 segundos (implementación recomendada: `refetchInterval` de 4s en TanStack Query) para dar el efecto "en vivo" durante la demo sin recargar la página. Las demás páginas SHALL refrescar manualmente o invalidando al mutar.

#### Scenario: Refresco automático del dashboard
- **WHEN** pasan 4 segundos desde la última carga del dashboard con una nueva orden confirmada por el Flujo 1
- **THEN** el dashboard muestra la nueva orden y las métricas actualizadas sin interacción del usuario

#### Scenario: Refresco automático de pedidos
- **WHEN** el Flujo 1 procesa una orden nueva mientras la página Pedidos está abierta
- **THEN** la lista se actualiza en el siguiente ciclo de polling sin recargar

### Requirement: Serialización temporal sin ambigüedad
El sistema SHALL serializar toda marca temporal como string ISO 8601 con zona horaria explícita (`AT TIME ZONE 'UTC'` antes de serializar), sin asumir el tipo de columna (la instancia desplegada puede ser `TIMESTAMP` o `TIMESTAMPTZ`). El front SHALL formatear a hora local del navegador.

#### Scenario: Timestamp con hora correcta
- **WHEN** el front recibe una marca temporal ISO con offset
- **THEN** la muestra en la hora local del navegador sin corrimiento espurio

### Requirement: Vistas de catálogo y métricas diarias disponibles
Si la UI necesita tendencias por día, el sistema SHALL leer `v_daily_order_summary` y `v_daily_chatbot_summary` (p. ej. para un gráfico simple en el dashboard) en vez de recalcular agregados en la API.

#### Scenario: Gráfico de tendencia diaria
- **WHEN** el dashboard muestra ingresos diarios o interacciones por día
- **THEN** los valores provienen de `v_daily_order_summary` / `v_daily_chatbot_summary`, no de agregados recalculados