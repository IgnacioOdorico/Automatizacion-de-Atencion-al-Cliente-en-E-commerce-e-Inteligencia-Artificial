# ODD — Dashboard cliente: cierre (backend fixes, E2E, Fase 7, Fase 8, push)

**Rama:** `feature/dashboard-cliente` · **Spec fuente:** `SPEC_DASHBOARD_CLIENTE.md` §6/§8/§9
**Autorización del usuario (2026-09-20):** resolver todas las decisiones pendientes; `connections.py` y todo lo de la rama se puede modificar (nada de esto está en `main`); al terminar, push a una rama que NO sea `main`. No se toca lo que está en `main` (Flujos 1 y 2, schema existente).
**TDD:** activo · **Runners:** `npm test` + `npm run build` (dashboard-web), `pytest` (dashboard-api, venv en `dashboard-api/.venv`)
**Estrategia de entrega:** `ask-on-risk`; push de la rama de feature (sin PR salvo pedido).

## Decisiones tomadas (antes eran "necesitan decisión")
1. Ruta de callback Gmail: el backend redirige directo a `/conexiones` (fuente del error); el alias `/connections` del front queda como red de seguridad.
2. Errores del callback de Gmail: el backend redirige a `/conexiones?gmail=error&reason=<código>` en vez de devolver JSON crudo.
3. Cancelar código Telegram: endpoint nuevo `DELETE /connections/telegram/code` que invalida el código pendiente; el front lo usa al cancelar.
4. Untracked: se versionan `openspec/`, `docs/DESVIOS_SPEC.md`, `SPEC_DASHBOARD_CLIENTE.md`; se ignoran `.atl/` y `.opencode/` (tooling de agentes).

## Límites honestos
Credenciales de Google (`DASHBOARD_GOOGLE_CLIENT_ID/SECRET`) y bot de Telegram (`DASHBOARD_BOT_TOKEN_VINCULO`) están vacías en `.env` y son del usuario: no se pueden crear ni cargar. Se verifica todo lo demás; Telegram se prueba simulando el webhook de n8n con curl (criterio de la spec 4.3) y Gmail hasta el 503 controlado.

## Tareas
- [x] C1 Backend: callback Gmail redirige a `/conexiones` y ante errores a `?gmail=error&reason=...`; front mapea `reason` a mensaje (TDD pytest + vitest)
- [x] C2 Backend+front: `DELETE /connections/telegram/code` + cancelar en la card (TDD)
- [ ] C3 Housekeeping: `.gitignore` (`.atl/`, `.opencode/`) y commit de `openspec/`, `docs/DESVIOS_SPEC.md`, `SPEC_DASHBOARD_CLIENTE.md`
- [ ] C4 Docker: levantar stack completo, aplicar migración/seed, smoke de API, aislamiento entre cuentas, Telegram confirm por curl, WhatsApp pending, `orden-nueva` → dashboard en vivo; corregir lo que rompa
- [ ] C5 Fase 7 (pulido para cámara): estados carga/vacío/error, datos seed realistas, transiciones, revisión visual en navegador
- [ ] C6 Fase 8 (QA seguridad §6): checklist 9.1–9.8 con evidencia, corregir huecos
- [ ] C7 Push de la rama a GitHub (no `main`) y reporte

## Ruta por tarea
C1, C2, C5, C6: delegated direct (un writer por vez). C3, C7: inline (mecánico). C4: delegated direct.

## Progreso / Evidencia
- **C1** (commit `1fe96a7`) — Backend (`dashboard-api/app/routers/connections.py`): el callback valida primero el `state` firmado y responde SIEMPRE con redirect 307 (el que ya usaba el archivo) a `{DASHBOARD_FRONTEND_URL sin barra final}/conexiones?...`; éxito `?gmail=connected`, fallo `?gmail=error&reason=<código>` con catálogo cerrado `GmailErrorReason`: `denied` (access_denied), `google_error` (otro `error` de Google), `invalid_state` (ausente/firma mala/vencido/otro canal), `missing_code`, `exchange_failed` (Google rechaza el canje 4xx o no trae access_token), `upstream` (red/timeout/5xx/JSON inválido), `no_email`, `no_refresh`, `internal` (falla al guardar en BD; se loguea solo el nombre de la excepción). Nunca viajan detalles, tokens ni `error_description`; el destino sale de `settings`, no del request. Sin persistencia en ningún fallo. Front (`lib/connections.ts`): `parseGmailReturn` devuelve `{result, reason}` con `reason` validado contra el catálogo (`Object.hasOwn`); `gmailReturnNotice` mapea cada motivo a un mensaje en voseo y cualquier valor fuera del catálogo cae al genérico sin reflejarse. Alias `/connections` del front intacto (red de seguridad).
  - Backend RED: `pytest tests/test_gmail_oauth.py` 20 fallos / 5 OK -> GREEN 25/25. `pytest` completo: 105 passed (baseline previo 91).
  - Front RED: `vitest run src/__tests__/connections.test.ts` 10 fallos / 38 OK -> GREEN 48/48. `npm test`: 7 archivos, 100 tests OK. `npm run build`: OK.
  - No verificado: consentimiento real de Google (credenciales vacías en `.env`); el redirect se prueba con `TestClient` y Google mockeado con `httpx.MockTransport`.
- **C2** — Backend: `telegram_codes.cancel(account_id)` (bajo el lock; solo toca el código indexado por esa cuenta, idempotente, devuelve True solo si había un código vigente) y `DELETE /connections/telegram/code` (JWT; 200 `{"cancelled": bool}`). No colisiona con `DELETE /connections/{channel}`: ese path es de un solo segmento, y hay tests que verifican que cancelar el código NO desconecta el canal y que `DELETE /connections/telegram` sigue funcionando. Aislamiento entre cuentas verificado por API con una segunda cuenta registrada. Front: `connectionsApi.telegramCancelCode()`, `shouldCancelTelegramCode` (solo un código vigente pega al server; uno vencido se descarta local) y `useTelegramLink.cancel`: si el DELETE falla, el código local NO se descarta (sigue vigente en el server), se muestra el error (`telegram-cancel`) y el botón permite reintentar; `dismiss` queda como descarte local (lo usa la desconexión del canal).
  - Backend RED: `pytest tests/test_telegram_codes.py tests/test_telegram_connection.py` 11 fallos / 17 OK -> GREEN 28/28. `pytest` completo: 118 passed.
  - Front RED: `npm test` 7 fallos / 102 OK -> GREEN 109/109 (8 archivos). `npm run build`: OK.
  - No verificado: el comportamiento del hook/card en navegador (no hay React Testing Library en el repo; la lógica de decisión está en funciones puras testeadas y el cableado lo valida `tsc`).

## Próximo paso
C3 (housekeeping).
