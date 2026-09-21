# Spec — client-dashboard/connections

## ADDED Requirements

### Requirement: Tabla de conexiones de canal por cuenta
El sistema SHALL persistir el estado de cada canal (`whatsapp`, `telegram`, `email`) por cuenta en la tabla nueva `channel_connections`, con `status` en (`disconnected`, `pending`, `connected`, `error`), `external_reference` opcional (chat_id de Telegram, email autorizado en Gmail), `connected_at` y `encrypted_credentials`. El par (`client_account_id`, `channel`) SHALL ser único. En BD el dominio de canal SHALL usar `email` (valor existente en `interactions.channel` y `tickets.channel`); la etiqueta visual en la UI será "Gmail".

#### Scenario: Alta de estados iniciales por cuenta
- **WHEN** se registra una cuenta de cliente
- **THEN** el sistema crea una fila de `channel_connections` en `disconnected` para cada uno de los tres canales

#### Scenario: Unicidad de canal por cuenta
- **WHEN** se intenta registrar un canal ya existente para la misma cuenta
- **THEN** el sistema actualiza la fila existente, no crea una duplicada

### Requirement: Encriptado de credenciales de canal
El sistema SHALL guardar en `channel_connections.encrypted_credentials` cualquier token o credencial (p. ej. refresh token de Gmail) encriptado con Fernet/AES usando una clave de aplicación de variable de entorno (`DASHBOARD_ENC_KEY`), nunca en texto plano ni en el repo.

#### Scenario: Guardado de refresh token de Gmail
- **WHEN** el sistema almacena el refresh token obtenido de Google
- **THEN** la columna `encrypted_credentials` contiene el valor encriptado y ningún log ni respuesta API expone el token en claro

### Requirement: Vínculo de Telegram por código de 6 dígitos
El sistema SHALL implementar `POST /connections/telegram/start` (JWT): genera un código numérico de 6 dígitos válido por 15 minutos, asociado a la cuenta autenticada, y lo muestra al usuario. El vínculo SHALL confirmarse con `POST /connections/telegram/confirm`, llamado por el workflow n8n aislado "Telegram — Vínculo de cuenta" cuando el cliente envía el código por chat al bot de vínculo. Este endpoint NO exige JWT pero SHALL validar un secreto compartido en el header (`X-N8N-SECRET`) y la vigencia del código; al confirmar, `status='connected'` y `external_reference=chat_id`.

#### Scenario: Generación de código válido
- **WHEN** se llama `POST /connections/telegram/start` con JWT válido
- **THEN** el sistema responde 200 con un código de 6 dígitos y su vencimiento (15 min) y almacena la asociación código → cuenta

#### Scenario: Confirmación con código y secreto correctos
- **WHEN** el workflow aislado llama `POST /connections/telegram/confirm` con `X-N8N-SECRET` válido, un código vigente y el `chat_id`
- **THEN** el sistema marca esa `channel_connections` del canal telegram como `connected`, guarda el `chat_id` en `external_reference` y responde 200

#### Scenario: Confirmación con secreto inválido
- **WHEN** se llama `POST /connections/telegram/confirm` sin el header `X-N8N-SECRET` esperado
- **THEN** el sistema responde 401 y no cambia ningún estado

#### Scenario: Código vencido o inexistente
- **WHEN** se confirma con un código vencido (más de 15 min) o inexistente
- **THEN** el sistema responde 400 y la conexión permanece en su estado anterior

### Requirement: Flujo aislado de n8n para el vínculo de Telegram
El sistema SHALL proveer (importable, sin modificaciones a Flujo 2) un workflow n8n aislado que escuche mensajes del bot de vínculo de Telegram (bot token propio `DASHBOARD_BOT_TOKEN_VINCULO`), detecte mensajes con formato de 6 dígitos y los remita a `/connections/telegram/confirm` con el secreto compartido. El workflow SHALL usar un bot dedicado para no pisar el `telegramTrigger` del Flujo 2 existente.

#### Scenario: Mensaje con código al bot de vínculo
- **WHEN** un cliente envía un mensaje de 6 dígitos al bot de vínculo
- **THEN** el workflow llama `POST /connections/telegram/confirm` con el `chat_id` y el código, y el endpoint marca la conexión como `connected`

#### Scenario: El Flujo 2 queda intacto
- **WHEN** se importa y activa el workflow de vínculo
- **THEN** el webhook Telegram del Flujo 2 continúa registrado y respondiendo con su bot original

### Requirement: Flujo Gmail OAuth2
El sistema SHALL implementar `GET /connections/gmail/oauth-url` (JWT) que genera la URL de consentimiento de Google (OAuth2) con `state` firmado que identifica la cuenta, y `GET /connections/gmail/callback` que canjea el `code`, valida el `state`, guarda el refresh token encriptado y marca el canal como `connected` con `external_reference` = email autorizado.

#### Scenario: Consentimiento completado
- **WHEN** el usuario autoriza la app en el consent screen de Google y Google redirige a `/connections/gmail/callback` con `state` válido y `code`
- **THEN** el sistema intercambia el código por token, encripta el refresh token, marca `email` como `connected` y responde con redirección al front

#### Scenario: Fallo de autorización de Google
- **WHEN** Google devuelve un error de autorización (usuario rechaza o `state` inválido)
- **THEN** el sistema no persiste ninguna credencial y deja el canal en su estado anterior

### Requirement: Solicitud de aprobación de WhatsApp
El sistema SHALL implementar `POST /connections/whatsapp/request-approval` (JWT) que valide el número (E.164) y deje el canal whatsapp en `status='pending'` con `external_reference` = número, informando que la aprobación la resuelve Meta en 1-3 días hábiles. No se simula una conexión real: el estado `pending` ES el comportamiento correcto de producción.

#### Scenario: Solicitud de aprobación
- **WHEN** el cliente registra su número de WhatsApp desde la UI
- **THEN** el sistema deja `channel_connections.whatsapp` en `pending` y muestra el mensaje de aprobación de Meta

#### Scenario: Cuenta seed conectada
- **WHEN** la demo muestra la cuenta con el dato semilla de WhatsApp aprobado
- **THEN** la UI muestra el estado `connected` sin pasar por la solicitud (fila sembrada en `seed_dashboard.sql`)

### Requirement: Desconexión de canal
El sistema SHALL exponer `DELETE /connections/{channel}` (JWT) que marque la conexión como `disconnected`, limpie `external_reference`, `encrypted_credentials` y `connected_at`. El sistema SHALL soportar desconectar un canal en cualquier estado.

#### Scenario: Desconexión de un canal conectado
- **WHEN** el cliente desconecta un canal conectado
- **THEN** el sistema limpia las credenciales y referencias, queda `status='disconnected'` y la UI refleja el cambio