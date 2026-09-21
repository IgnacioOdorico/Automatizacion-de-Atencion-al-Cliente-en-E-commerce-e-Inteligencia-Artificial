# ODD — Dashboard cliente, Fase 6: Conexiones (frontend)

**Rama:** `feature/dashboard-cliente` · **Spec fuente:** `SPEC_DASHBOARD_CLIENTE.md` §4/§8 y `openspec/changes/dashboard-cliente/tasks.md` §7
**TDD:** activo (Strict TDD Mode de la config del usuario) · **Runner:** `npm test` (vitest run) en `dashboard-web/`
**Chequeos:** `npm test` + `npm run build` (tsc --noEmit + vite build) en `dashboard-web/`
**Estrategia de entrega:** `ask-on-risk` · forecast ≈ 450–600 líneas de código creado (revisar al cerrar)

## Objetivo
Reemplazar el placeholder de `ConexionesPage` por la UI real de los tres canales (WhatsApp, Telegram, Gmail) contra los endpoints de la Fase 3, que ya existen en el backend.

## Alcance autorizado
Solo `dashboard-web/` (páginas, componentes, `api/endpoints.ts`, `types/api.ts`, `lib/*`, estilos, tests) y el tildado de `openspec/.../tasks.md`. **No se toca** backend, workflows de n8n ni el schema salvo bug confirmado (se reporta antes).

## Tareas
- [x] T1 (7.1) Página Conexiones: cards por canal desde `GET /connections`, mapeo BD `email` → etiqueta "Gmail", estado y `external_reference`
- [x] T2 (7.2) Telegram: "Conectar" → `POST /connections/telegram/start` → código de 6 dígitos + instructivo + polling de estado hasta `connected`
- [x] T3 (7.3) Gmail: "Conectar" → `GET /connections/gmail/oauth-url` → redirect a Google → vuelta al front (`?gmail=connected`) con el email autorizado
- [x] T4 (7.4) WhatsApp: "Solicitar aprobación" con número E.164 → `POST /connections/whatsapp/request-approval` → estado `pending` con mensaje "Meta aprueba en 1-3 días hábiles"; la cuenta seed `connected` se ve como aprobada
- [ ] T5 (7.5) Desconexión por card: confirmación + `DELETE /connections/{channel}`
- [ ] T6 Corregir `openspec/.../tasks.md`: tildar sección 6 (Fase 5, ya implementada) y 7 según se cierre

## Ruta por tarea
Todas: **delegated direct**, un único writer (dispara el trigger de escritura: 2+ archivos no triviales y lectura de preparación).

## Criterios de aceptación
- Los tres canales se ven con su estado real; `email` se muestra como "Gmail".
- Telegram llega a `connected` sin recargar la página.
- Ningún flujo falla en silencio: errores del server (401/400/503/502) se muestran en pantalla.
- `npm test` y `npm run build` en verde.

## Progreso / Evidencia
Línea base: `npm test` (dashboard-web): 5 archivos, 36 tests en verde antes de empezar.
Hallazgo verificado: el backend redirige el callback de Gmail a `{DASHBOARD_FRONTEND_URL}/connections?gmail=connected` (connections.py:219-221) pero la ruta del front es `/conexiones` (App.tsx, nav.tsx); sin alias, el catch-all `*` manda a `/dashboard` y se pierde el query. Se resuelve en el front (T3), no se toca el backend.

- **T1** — `npx vitest run src/__tests__/connections.test.ts` RED (falla la resolución de `@/lib/connections`, módulo inexistente) -> GREEN 12/12 tras implementar `buildChannelCards`/`channelActions`. `npm test`: 6 archivos, 48 tests OK. `npm run build`: OK. Commit: `4972b64`.
- **T2** — `npx vitest run src/__tests__/telegramLink.test.ts` RED (módulo `@/lib/telegramLink` inexistente) -> GREEN 10/10 (`codeDeadline`, `secondsRemaining`, `formatCountdown`, `shouldPollTelegram`). `connectionActionError` ('telegram-start'): RED (3 tests, "is not a function") -> GREEN 15/15 en connections.test.ts. `npm test`: 7 archivos, 61 tests OK. `npm run build`: OK. Polling: `useQuery` con `refetchInterval` 3000ms solo mientras hay código vigente; al pasar la card a `connected` el hook descarta el código y se invalida `['me']`. Commit: `67bd593`.
- **T3** — `connections.test.ts` ampliado (`connectionActionError` gmail-connect, `isGoogleConsentUrl`, `parseGmailReturn`, `gmailReturnNotice`, `connectionsAliasPath`): RED 16 fallos de 31 -> GREEN 31/31 (un test falló una vez por mi propio texto esperado; se ajustó el mensaje de 503 a "Gmail todavía no está configurado en el servidor: faltan las credenciales de Google"). `npm test`: 7 archivos, 77 tests OK. `npm run build`: OK. Alias `/connections` -> `/conexiones` preservando el query en App.tsx (`ConnectionsAlias`). Redirect a Google solo si la URL es https://accounts.google.com. 503 de oauth-url muestra mensaje claro en la card. Commit: `28aedb1`.
- **T4** — `validate.test.ts` (`normalizePhone`, `validatePhone` E.164) + `connections.test.ts` (`connectionActionError` whatsapp-request, `whatsappStatusNote`): RED 12 fallos de 90 -> GREEN 90/90. `npm test`: 7 archivos, 90 tests OK. `npm run build`: OK. Validación E.164 estricta ("+" y 7-15 dígitos, coherente con el regex del backend `^\+?[1-9]\d{1,14}$` + min_length 8); el número se envía normalizado (sin separadores). Estado `pending` persistente con nota "Meta aprueba en 1-3 días hábiles"; `connected` (seed) se muestra como aprobado. Commit: `de4498c`.
- **T5** — `connections.test.ts` (`connectionActionError` disconnect, `disconnectCopy`): RED 4 fallos de 42 -> GREEN 42/42. `npm test`: 7 archivos, 94 tests OK. `npm run build`: OK. `ConfirmDialog` (patrón del modal de pedidos) + `DELETE /connections/{channel}`; en WhatsApp `pending` el botón es "Cancelar solicitud". Tras el DELETE se invalidan `['connections']` y `['me']` y, si es Telegram, se descarta el código en pantalla. Commit: _(se completa en el commit final de documentación)_.

## Próximo paso
Delegar el writer.
