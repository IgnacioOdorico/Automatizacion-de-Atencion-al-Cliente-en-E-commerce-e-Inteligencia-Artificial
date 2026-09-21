# ODD — Monitoreo del bot (portal del comercio, un solo comercio)

**Rama:** `feature/dashboard-cliente` · **Origen:** pedido del usuario (2026-09-21): plan cambiado, seguimos con UN comercio simulado con el bot conectado (multi-bot/admin quedan como trabajo futuro); agregar un apartado de monitoreo real: "ver todo lo que está haciendo el bot al pie de la letra" para explicarlo en video.
**TDD:** activo · **Runners:** `pytest` (dashboard-api, contra `ecommerce_tesis_test`), `npm test` + `npm run build` (dashboard-web).
**Alcance:** solo lectura. NO se tocan Flujos 1/2, `init_simple.sql` ni datos de la BD `ecommerce_tesis` (evidencia medida de la tesis). Los tests corren en `ecommerce_tesis_test`.

## Diseño (tres capas, en orden)
1. **En vivo**: línea de tiempo unificada derivada de las tablas de negocio (`orders`, `interactions`, `tickets`, `stock_alerts`): pedido recibido / procesado / notificado, mensaje del cliente, respuesta exacta del bot (intent, TMR, urgencia), ticket creado, alerta de stock. Polling 3 s, filtros por tipo y canal, pausa, detalle con textos exactos.
2. **Conversaciones**: hilos por canal + usuario, estilo chat (mensaje del cliente → respuesta del bot), con intent, TMR y pedido/ticket vinculado.
3. **Workflow en vivo (foco del video: explicar la tesis = el workflow)**: el workflow de n8n **dibujado en nuestra UI** (SVG, sin dependencias nuevas) a partir de `workflow_entity`/`execution_data.workflowData` (solo nombre, tipo, posición y conexiones de cada nodo: NUNCA `parameters`), con el camino de la última ejecución iluminado (nodo por nodo: ok / error / no ejecutado, duración, ramas del IF "con stock / sin stock"), y una lista de ejecuciones (workflow, estado, duración, error). Al hacer clic en un nodo: estado, duración, cantidad de items y vista previa de salida acotada y **redactada** (tokens, claves, cookies). Las métricas de la tesis (MTTD/MTTR/TMR) se explican sobre el mismo diagrama. Acoplamiento a tablas internas de n8n 2.12.2: degradar con gracia (`available:false`) si no existen o no hay workflows.
Fuera de alcance: modificar workflows, exponer credenciales o `parameters` de nodos, editar/reintentar ejecuciones, multi-tenant, admin.

## Dependencia del usuario
`interactions` está vacía y solo el Flujo 1 está importado en esta instancia de n8n: los datos de chat reales aparecen cuando el usuario importe el Flujo 2 y cargue sus credenciales (OpenAI, Telegram/SMTP, Postgres). Sin eso el monitoreo muestra pedidos, tickets y ejecuciones (incluidos errores) pero no chat.

## Tareas
- [x] M1 Backend: `GET /monitoring/summary` y `GET /monitoring/events` (feed unificado con cursor + `since` para polling)
- [x] M2 Backend: `GET /monitoring/conversations` y hilo por canal+usuario
- [x] M3 Backend: `GET /monitoring/workflows`, `GET /monitoring/workflows/{id}/graph` (grafo sanitizado), `GET /monitoring/executions` y `GET /monitoring/executions/{id}` (traza por nodo, redacción, degradación)
- [x] M4a Frontend: sección Monitoreo con nav y pestañas En vivo + Conversaciones (polling, estados, detalle, pausa)
  - [x] M4a-1 lib pura del monitoreo: tipos, cliente `monitoringApi`, formatos, descripción de eventos, KPIs y estado del bot (`ec49f0b`)
  - [x] M4a-2 lib pura del feed (trozos + cursores + tope + pausa) y de los hilos (unión de ventana + historia, días, URL) (`d71e19b`)
  - [x] M4a-3 nav, rutas y pestañas accesibles (`36f3050`)
  - [x] M4a-4 pestaña En vivo (`65772b3`)
  - [x] M4a-5 pestaña Conversaciones (`c00848f`)
  - [x] M4a-6 revisión visual (1280 y 375 px contra una API de mentira), correcciones y cierre
- [ ] M4b Frontend: pestaña Workflow: diagrama SVG del workflow con el camino de la ejecución iluminado, lista de ejecuciones y detalle por nodo; leyenda de MTTD/MTTR/TMR
  - [x] M4b-1 lib pura + tipos + cliente API: layout del grafo, viewport (pan/zoom), estado por nodo/arista desde la traza, reproducción, seguir en vivo, ejecuciones, métricas de la tesis
  - [ ] M4b-2 lienzo SVG con pan/zoom (mouse, rueda con Ctrl, pinch, teclado), selector de workflow y estados
  - [ ] M4b-3 overlay de la ejecución + reproducir camino
  - [ ] M4b-4 lista de ejecuciones, seguir en vivo y detalle de nodo
  - [ ] M4b-5 tarjeta de métricas de la tesis, leyenda, ruta y pestaña
  - [ ] M4b-6 revisión visual (1280 y 375 px contra una API de mentira) y cierre
- [ ] M5 Reconstruir stack, smoke autenticado, docs (SPEC §1/§5/§10, README, CLAUDE.md), pausa de polling y a11y

## Ruta por tarea
M1–M3: delegated direct (un writer backend). M4: delegated direct (un writer front, después del contrato de la API). M5: delegated direct.

## Progreso / Evidencia
- **M1** (`130cf7e`): RED `pytest tests/test_cursors.py` = error de colección (módulo inexistente); RED `test_monitoring_events.py test_monitoring_summary.py` = 39 failed (404). GREEN: 12 + 39 passed. Mutación (cursor keyset sin `rk`/`pk`) hace fallar el test de empates. Suite: 282 passed.
- **M2** (`80decc9`): RED `test_monitoring_conversations.py` = 27 failed (404). GREEN: 27 passed. Suite: 309 passed.
- **M3** (`8b98463`): RED por módulo (colección) en flatted, redaction, graph, trace; RED `test_monitoring_workflows.py` = 36 failed. GREEN: flatted 17, redaction 99, graph 17, trace 24, workflows 36. Suite completa: 502 passed. Smoke SOLO LECTURA contra las tablas reales de n8n de `ecommerce_tesis` (dependencia JWT sobrescrita, sin escrituras): `/monitoring/workflows` (Flujo 1, 15 nodos / 15 aristas), `/monitoring/executions` y traza de la ejecución 1 (Webhook success, Registrar Orden error) OK.
- **Docs** (`1a0db4c`): `docs/API_MONITOREO.md` (contratos), SPEC §1/§5/§10.
- **M4a-1**: RED (5 archivos, 22 tests fallidos + 2 errores de colección por módulos inexistentes). GREEN: 96 tests (format, domain, monitoring, monitoringSummary, monitoringApi).
- **M4a-2**: RED (2 archivos: módulos inexistentes). GREEN: 44 tests (eventFeed 25, conversations 19). Mutación (sacar la protección de trozos `manual` del tope) hace fallar el test correspondiente. Suite: 344 passed; `tsc --noEmit` limpio.
- **M4a-3**: RED (2 archivos por módulos inexistentes + 2 tests de CSS por reglas inexistentes). GREEN: 21 tests (tabs 12, layout 7, estilos 2). Suite: 365 passed; `npm run build` OK (286 kB de JS).
- **M4a-4**: RED 33 tests fallidos de `monitoringLive` + 7 de helpers (`formatEventClock`, `isScrolledAway`) + 8 de CSS. GREEN: `monitoringLive` 36 tests (feed, polling `since`, pausa, pestaña oculta, filtros, `before`, estados, KPIs, detalle, scroll). Mutaciones: forzar `paused=false` rompe 4 tests de pausa; ignorar `visibilityState` rompe el de pestaña oculta.
- **M4a-5**: RED 24 tests fallidos de `monitoringChats`. GREEN: 25 tests (lista, búsqueda con debounce, filtro, hilo en la URL, burbujas, días, pendiente, pedido/ticket, polling, historia, 404, error) + contraste de las burbujas. Mutación (el poll reemplaza en vez de unir) rompe 3 tests.
- **Cierre M4a**: `npm test` 451 passed (29 archivos, base 238/19); `tsc --noEmit` limpio; `npm run build` OK (323 kB de JS, 35 kB de CSS). Revisión visual: ver el reporte del writer (API de mentira local, fuera del repo; 1280 px y 375 px).
- **M4b-1**: RED (8 archivos por módulos inexistentes: viewport, workflowGraph, workflowTrace, nodeKinds, playback, followLive, executions, thesisMetrics; + 4 de `formatMs` y 5 de `monitoringApi.workflows/workflowGraph/executions/execution`). GREEN: 37 archivos, 618 tests. Mutaciones: cambiar la regla de arista recorrida a "siempre" rompe 3 tests de `workflowTrace`; sacar `relieveOverlaps` del layout rompe el test de tarjetas que se pisan en los Flujos 1 y 2 reales. `tsc --noEmit` limpio.
- Pendiente de verificar: formato de ejecuciones EXITOSAS reales (solo existe la ejecución 1, con error; el resto de los fixtures exitosos se armaron con el formato observado) y del Flujo 2 (no está importado en n8n). Front (M4) y reconstrucción del stack (M5) sin hacer.

## Decisiones de M4a (front)
- El feed guarda la lista en "trozos" (una página de la API cada uno) porque los cursores son opacos: al descartar por el tope (~300) se tiran trozos enteros del final y el "Cargar más" sigue partiendo del cursor del último trozo que quedó, sin saltos. Lo que el usuario pidió con "Cargar más" no se descarta.
- Pausa doble: manual (botón) y automática cuando el usuario está leyendo más abajo (`isScrolledAway`): lo nuevo espera en el contador ("N eventos nuevos" + "Ver ahora", flotante si se está más abajo) para que la lista no salte en ningún navegador.
- El polling del feed se detiene con la pestaña del navegador oculta y se pone al día apenas vuelve; verificado en el navegador real (el panel de pruebas reporta `hidden` en reposo y no consulta).
- "Bot activo" solo si el último evento real es de hace <= 5 min; ámbar hasta 60 min; gris después; sin datos o sin respuesta del servidor no se afirma nada.
- El hilo abierto vive en la URL (`?canal=&usuario=`, codificado); la ventana reciente del hilo se une a lo ya cargado por `interaction_id` (lo nuevo pisa: el bot puede responder después).
- La pestaña se declara en `lib/monitoringTabs.ts` (+ un `<Route>` en `App.tsx`): M4b suma "Workflow" sin refactor.

## Decisiones no obvias
- Cursores opacos `(ts con µs, rango por tipo, pk)`; `since` devuelve los `limit` más viejos posteriores para que el polling no pierda eventos.
- Parser `flatted` propio, iterativo, con tope (2 MB de texto / 200k posiciones); redacción por clave y por valor ANTES de truncar (para no filtrar prefijos de tokens).
- El grafo es una lista blanca (nunca `parameters`/`credentials`); notas adhesivas excluidas; aristas `ai_*` con `kind`.

## Próximo paso
M4b (pestaña Workflow: diagrama SVG con el camino de la ejecución iluminado, lista de ejecuciones y detalle por nodo); luego M5 (reconstruir el stack, smoke autenticado con datos reales, docs, a11y).
