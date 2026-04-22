# Especificación Técnica — Flujo 2: Chatbot Omnicanal con IA

> **Proyecto**: Automatización del ciclo post-venta en e-commerce: pipeline de procesamiento de órdenes y atención al cliente omnicanal con IA, implementado con n8n
>
> **Autores**: Santiago Sordi, Ignacio Odorico, Juan Cruz Ana — UTN FRM
>
> **Tutor**: Prof. Alberto Cortez
>
> **Workflow n8n**: `workflows/Atencion Cliente OMNICANAL IA PRO TESIS.json`
>
> **Tipo de cambio**: FIX / UPGRADE del workflow existente

---

## 1. Overview

El Flujo 2 implementa un chatbot omnicanal de atención al cliente con inteligencia artificial. Recibe mensajes desde tres canales (WhatsApp, Telegram, Email), los normaliza a un formato común, los envía a un modelo de IA (GPT-4o-mini) que clasifica la intención del mensaje y genera una respuesta, y luego enruta la respuesta de vuelta al canal de origen.

**Canales soportados**: WhatsApp (vía API Cloud), Telegram (vía Bot API), Email (vía Gmail)

**Intenciones clasificadas por la IA**:
| Intent | Descripción | Acción |
|---|---|---|
| `FAQ` | Pregunta frecuente | Responder con IA (enriquecida desde `faq_responses`) |
| `ESTADO_PEDIDO` | Consulta estado de un pedido | Buscar en tabla `orders` y responder con datos reales |
| `RECLAMO` | Queja o reclamo | Crear ticket en tabla `tickets`, confirmar recepción |
| `GENERAL` | Otro tipo de mensaje | Responder con IA directamente |

**Conexión con Flujo 1**: El chatbot consulta la tabla `orders` (creada y gestionada por el Flujo 1) cuando el intent es `ESTADO_PEDIDO`. Ambos flujos comparten la misma base de datos PostgreSQL (`ecommerce_tesis`).

**Métricas**: Cada interacción se registra en la tabla `interactions` con timestamps `received_at` y `responded_at` para calcular el TMR (Tiempo Medio de Respuesta), visualizado en Grafana.

---

## 2. Current State vs Target State

| Nodo | Estado Actual | Problema | Estado Objetivo |
|---|---|---|---|
| **Switch Intent** | `leftValue` y `rightValue` vacíos | No enruta nada — todos los mensajes caen al default | 4 rutas: FAQ, ESTADO_PEDIDO, RECLAMO, GENERAL |
| **Buscar Pedido** | Tipo MySQL, tabla vacía, desconectado del Switch | No busca nada, BD incorrecta | Tipo PostgreSQL, SELECT de `orders`, conectado a salida ESTADO_PEDIDO del Switch |
| **Crear Ticket** | Tipo Google Sheets, doc vacío, desconectado del Switch | No crea nada, destino incorrecto | Tipo PostgreSQL, INSERT en `tickets`, conectado a salida RECLAMO del Switch |
| **Router Canal** | `leftValue` y `rightValue` vacíos | No enruta a ningún canal de salida | 3 rutas: whatsapp → Enviar WhatsApp, telegram → Enviar Telegram, email → Enviar Gmail |
| **Merge Canales** | passThrough con 3 inputs | OK — solo uno de los tres canales dispara a la vez | Sin cambios |
| **Notificar Admin** | `chatId` = `"TU_CHAT_ID"` | Placeholder, no funciona | Configurar con chat_id real del admin |
| **Enviar WhatsApp** | URL con `PHONE_ID` placeholder | No envía nada | Configurar con Phone ID real de WhatsApp Business API |
| **Registrar Interacción** | **NO EXISTE** | No se loguea ninguna interacción → no hay datos de TMR | NUEVO nodo: PostgreSQL INSERT en `interactions` |
| **Buscar FAQ** | **NO EXISTE** | El chatbot no consulta las FAQ predefinidas | NUEVO nodo: PostgreSQL SELECT de `faq_responses` para enriquecer el prompt |
| **IA - Motor Decision** | Prompt básico sin contexto | No tiene info de FAQ ni de pedidos | Prompt mejorado con contexto de FAQ y datos del cliente |
| **Parse JSON** | Parsea `$json.choices[0].message.content` | No propaga `received_at` | Agregar `received_at: new Date().toISOString()` al output |
| **Normalizar WhatsApp/Telegram/Gmail** | No registran timestamp de recepción | Falta `received_at` para TMR | Agregar `received_at: new Date().toISOString()` |

---

## 3. Node-by-Node Specification

### 3.1 Webhook WhatsApp (SIN CAMBIOS)

- **Tipo**: `n8n-nodes-base.webhook` v2.1
- **Método**: POST
- **Path**: `/whatsapp`
- **URL completa**: `http://localhost:5678/webhook/whatsapp`
- **Notas**: Recibe el payload de la API de WhatsApp Cloud. No requiere cambios.

### 3.2 Telegram Trigger (SIN CAMBIOS)

- **Tipo**: `n8n-nodes-base.telegramTrigger` v1.2
- **Notas**: Requiere credencial de Bot API configurada en n8n. No requiere cambios en el nodo.

### 3.3 Gmail Trigger (SIN CAMBIOS)

- **Tipo**: `n8n-nodes-base.gmailTrigger` v1.3
- **Poll**: Cada minuto
- **Notas**: Requiere credencial OAuth de Gmail configurada en n8n.

### 3.4 Normalizar WhatsApp (MODIFICAR)

- **Tipo**: `n8n-nodes-base.function` v1
- **Cambio**: Agregar `received_at` al output

```javascript
const msg = $json.entry[0].changes[0].value.messages[0];
return [{
  user: msg.from,
  message: msg.text.body,
  canal: 'whatsapp',
  received_at: new Date().toISOString()
}];
```

### 3.5 Normalizar Telegram (MODIFICAR)

- **Tipo**: `n8n-nodes-base.function` v1
- **Cambio**: Agregar `received_at` al output

```javascript
return [{
  user: String($json.message.chat.id),
  message: $json.message.text,
  canal: 'telegram',
  received_at: new Date().toISOString()
}];
```

### 3.6 Normalizar Gmail (MODIFICAR)

- **Tipo**: `n8n-nodes-base.function` v1
- **Cambio**: Agregar `received_at` al output

```javascript
return [{
  user: $json.from,
  message: $json.text || $json.snippet || $json.body,
  canal: 'email',
  received_at: new Date().toISOString()
}];
```

### 3.7 Merge Canales (SIN CAMBIOS)

- **Tipo**: `n8n-nodes-base.merge` v3.2
- **Mode**: passThrough
- **Notas**: Correcto para el caso de uso. Solo un canal dispara a la vez; el merge simplemente pasa el dato al siguiente nodo.

### 3.8 Buscar FAQ (NUEVO NODO)

- **Tipo**: `n8n-nodes-base.postgres`
- **Operación**: Execute Query
- **Credencial**: PostgreSQL (ecommerce_tesis)
- **Posición**: Entre "Merge Canales" y "IA - Motor Decision"
- **Propósito**: Obtener las FAQ habilitadas para inyectarlas como contexto en el prompt de IA

**SQL**:
```sql
SELECT question, answer, category
FROM faq_responses
WHERE enabled = TRUE
ORDER BY category, id;
```

**Código del nodo Function después de Buscar FAQ** (para combinar FAQ con el mensaje original):

El resultado de este nodo se pasa como contexto adicional al prompt. Ver sección 7 para el prompt completo.

### 3.9 IA - Motor Decision (MODIFICAR)

- **Tipo**: `n8n-nodes-base.openAi` v1.1
- **Modelo**: `gpt-4o-mini`
- **Cambio**: Prompt mejorado con contexto FAQ (ver sección 7)
- **Prompt**: Ver sección 7 "Enhanced AI Prompt"

### 3.10 Parse JSON (MODIFICAR)

- **Tipo**: `n8n-nodes-base.function` v1
- **Cambio**: Propagar `canal`, `user`, `received_at` y manejar errores de parseo

```javascript
try {
  const raw = $json.choices[0].message.content;
  // Extraer JSON del contenido (puede venir envuelto en markdown)
  const jsonMatch = raw.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error('No JSON found in AI response');
  const data = JSON.parse(jsonMatch[0]);

  return [{
    intent: data.intent || 'GENERAL',
    order_id: data.order_id || null,
    urgente: data.urgente || false,
    respuesta: data.respuesta || 'No pude procesar tu consulta. Intentá de nuevo.',
    canal: $json.canal,
    user: $json.user,
    message: $json.message,
    received_at: $json.received_at
  }];
} catch (e) {
  return [{
    intent: 'GENERAL',
    order_id: null,
    urgente: false,
    respuesta: 'Disculpá, hubo un error procesando tu mensaje. ¿Podés reformularlo?',
    canal: $json.canal,
    user: $json.user,
    message: $json.message,
    received_at: $json.received_at,
    _parse_error: e.message
  }];
}
```

### 3.11 Switch Intent (CORREGIR — CRÍTICO)

- **Tipo**: `n8n-nodes-base.switch` v3.4
- **Cambio**: Configurar 4 rutas basadas en el campo `intent`

**Configuración de rutas**:

| Output | Condición | Destino |
|---|---|---|
| Output 0 | `{{ $json.intent }}` equals `"FAQ"` | → Preparar Respuesta FAQ |
| Output 1 | `{{ $json.intent }}` equals `"ESTADO_PEDIDO"` | → Buscar Pedido |
| Output 2 | `{{ $json.intent }}` equals `"RECLAMO"` | → Crear Ticket |
| Output 3 (fallback/default) | Cualquier otro valor | → IF Urgente (ruta GENERAL) |

**Parámetros n8n del Switch**:
```json
{
  "rules": {
    "values": [
      {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "typeValidation": "strict",
            "version": 3
          },
          "conditions": [
            {
              "leftValue": "={{ $json.intent }}",
              "rightValue": "FAQ",
              "operator": {
                "type": "string",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        }
      },
      {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "typeValidation": "strict",
            "version": 3
          },
          "conditions": [
            {
              "leftValue": "={{ $json.intent }}",
              "rightValue": "ESTADO_PEDIDO",
              "operator": {
                "type": "string",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        }
      },
      {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "typeValidation": "strict",
            "version": 3
          },
          "conditions": [
            {
              "leftValue": "={{ $json.intent }}",
              "rightValue": "RECLAMO",
              "operator": {
                "type": "string",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        }
      }
    ]
  },
  "options": {
    "fallbackOutput": "extra"
  }
}
```

### 3.12 Buscar Pedido (CORREGIR — CRÍTICO)

- **Tipo actual**: `n8n-nodes-base.mySql` v2.5 → **CAMBIAR A**: `n8n-nodes-base.postgres`
- **Operación**: Execute Query
- **Credencial**: PostgreSQL (ecommerce_tesis)
- **Conexión de entrada**: Output 1 del Switch Intent (ESTADO_PEDIDO)
- **Conexión de salida**: → Preparar Respuesta Pedido (Function) → IF Urgente

**SQL**:
```sql
SELECT
    o.order_number,
    o.customer_name,
    o.customer_email,
    o.customer_phone,
    o.status,
    o.quantity,
    o.total_amount,
    o.received_at,
    o.processed_at,
    o.notified_at,
    p.name AS product_name
FROM orders o
LEFT JOIN products p ON o.product_id = p.id
WHERE
    o.order_number = '{{ $json.order_id }}'
    OR o.customer_phone LIKE '%{{ $json.user }}%'
    OR o.customer_email = '{{ $json.user }}'
ORDER BY o.received_at DESC
LIMIT 5;
```

**Notas**:
- Busca por `order_id` (si la IA lo extrajo del mensaje) O por el identificador del usuario (teléfono o email)
- Retorna hasta 5 pedidos más recientes del cliente
- El LEFT JOIN con `products` trae el nombre del producto

### 3.13 Preparar Respuesta Pedido (NUEVO NODO)

- **Tipo**: `n8n-nodes-base.function` v1
- **Posición**: Entre "Buscar Pedido" y "IF Urgente"
- **Propósito**: Formatear los datos del pedido como respuesta legible

```javascript
const pedidos = $input.all();
const originalData = $('Parse JSON').first().json;

if (!pedidos || pedidos.length === 0 || !pedidos[0].json.order_number) {
  return [{
    ...originalData,
    respuesta: 'No encontré pedidos asociados a tu cuenta. ¿Podés indicarme tu número de pedido? (Ejemplo: ORD-001)'
  }];
}

let respuesta = '';
if (pedidos.length === 1) {
  const p = pedidos[0].json;
  const statusMap = {
    'pending': '⏳ Pendiente de procesamiento',
    'processing': '🔄 En procesamiento',
    'confirmed': '✅ Confirmado',
    'shipped': '🚚 Enviado',
    'delivered': '📦 Entregado',
    'no_stock': '❌ Sin stock',
    'cancelled': '🚫 Cancelado',
    'error': '⚠️ Error en procesamiento'
  };
  respuesta = `Tu pedido ${p.order_number}:\n`
    + `• Producto: ${p.product_name}\n`
    + `• Cantidad: ${p.quantity}\n`
    + `• Total: $${p.total_amount}\n`
    + `• Estado: ${statusMap[p.status] || p.status}\n`
    + `• Fecha: ${new Date(p.received_at).toLocaleDateString('es-AR')}`;
} else {
  respuesta = `Encontré ${pedidos.length} pedidos asociados a tu cuenta:\n\n`;
  for (const item of pedidos) {
    const p = item.json;
    respuesta += `• ${p.order_number} — ${p.product_name} — Estado: ${p.status}\n`;
  }
  respuesta += '\n¿Sobre cuál querés más detalle?';
}

return [{
  ...originalData,
  respuesta: respuesta,
  order_id_found: pedidos[0].json.order_number ? pedidos[0].json.id : null
}];
```

### 3.14 Crear Ticket (CORREGIR — CRÍTICO)

- **Tipo actual**: `n8n-nodes-base.googleSheets` v4.7 → **CAMBIAR A**: `n8n-nodes-base.postgres`
- **Operación**: Execute Query
- **Credencial**: PostgreSQL (ecommerce_tesis)
- **Conexión de entrada**: Output 2 del Switch Intent (RECLAMO)
- **Conexión de salida**: → Preparar Respuesta Ticket (Function) → IF Urgente

**SQL**:
```sql
INSERT INTO tickets (channel, user_id, subject, status, priority, created_at)
VALUES (
    '{{ $json.canal }}',
    '{{ $json.user }}',
    '{{ $json.message }}',
    'open',
    CASE WHEN {{ $json.urgente }} THEN 'urgent' ELSE 'normal' END,
    NOW()
)
RETURNING id, status, priority, created_at;
```

**Notas**:
- `interaction_id` y `order_id` se dejan NULL por ahora (se podrían actualizar después de registrar la interacción)
- El `RETURNING` permite incluir el ID del ticket en la respuesta al cliente

### 3.15 Preparar Respuesta Ticket (NUEVO NODO)

- **Tipo**: `n8n-nodes-base.function` v1
- **Posición**: Entre "Crear Ticket" y "IF Urgente"
- **Propósito**: Formatear confirmación de ticket

```javascript
const ticket = $json;
const originalData = $('Parse JSON').first().json;

return [{
  ...originalData,
  respuesta: `Tu reclamo fue registrado correctamente.\n`
    + `• Ticket #${ticket.id}\n`
    + `• Estado: Abierto\n`
    + `• Prioridad: ${ticket.priority}\n\n`
    + `Nuestro equipo lo revisará a la brevedad. `
    + `Te contactaremos por este mismo canal con novedades.`,
  ticket_id: ticket.id
}];
```

### 3.16 IF Urgente (MODIFICAR LEVE)

- **Tipo**: `n8n-nodes-base.if` v2.3
- **Condición**: `{{ $json.urgente }}` is true
- **Output true**: → Notificar Admin → Router Canal → (canal correspondiente) → Registrar Interacción
- **Output false**: → Router Canal → (canal correspondiente) → Registrar Interacción
- **Cambio**: La condición está bien. Solo verificar que llegan los datos correctos de los nodos anteriores.

### 3.17 Notificar Admin (CONFIGURAR)

- **Tipo**: `n8n-nodes-base.telegram` v1.2
- **Cambio**: Reemplazar `"TU_CHAT_ID"` con el chat_id real del administrador

**Configuración**:
```json
{
  "chatId": "ADMIN_TELEGRAM_CHAT_ID",
  "text": "⚠️ CASO URGENTE detectado\n\n• Canal: {{ $json.canal }}\n• Usuario: {{ $json.user }}\n• Intent: {{ $json.intent }}\n• Mensaje: {{ $json.message }}\n• Respuesta IA: {{ $json.respuesta }}",
  "additionalFields": {}
}
```

**Para obtener el chat_id del admin**:
1. Crear un bot en Telegram con @BotFather
2. Enviar un mensaje al bot
3. Hacer GET a `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. El `chat.id` del mensaje es el valor a usar

### 3.18 Router Canal (CORREGIR — CRÍTICO)

- **Tipo**: `n8n-nodes-base.switch` v3.4
- **Cambio**: Configurar 3 rutas basadas en el campo `canal`

**Configuración de rutas**:

| Output | Condición | Destino |
|---|---|---|
| Output 0 | `{{ $json.canal }}` equals `"whatsapp"` | → Enviar WhatsApp |
| Output 1 | `{{ $json.canal }}` equals `"telegram"` | → Enviar Telegram |
| Output 2 | `{{ $json.canal }}` equals `"email"` | → Enviar Gmail |

**Parámetros n8n del Switch**:
```json
{
  "rules": {
    "values": [
      {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "typeValidation": "strict",
            "version": 3
          },
          "conditions": [
            {
              "leftValue": "={{ $json.canal }}",
              "rightValue": "whatsapp",
              "operator": {
                "type": "string",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        }
      },
      {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "typeValidation": "strict",
            "version": 3
          },
          "conditions": [
            {
              "leftValue": "={{ $json.canal }}",
              "rightValue": "telegram",
              "operator": {
                "type": "string",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        }
      },
      {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "typeValidation": "strict",
            "version": 3
          },
          "conditions": [
            {
              "leftValue": "={{ $json.canal }}",
              "rightValue": "email",
              "operator": {
                "type": "string",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        }
      }
    ]
  },
  "options": {}
}
```

### 3.19 Enviar WhatsApp (CONFIGURAR)

- **Tipo**: `n8n-nodes-base.httpRequest` v4.4
- **Método**: POST
- **Cambio**: Configurar URL y body correctos

**URL**: `https://graph.facebook.com/v18.0/{{PHONE_ID}}/messages`

> Reemplazar `{{PHONE_ID}}` con el Phone Number ID de la cuenta de WhatsApp Business.

**Headers**:
```
Authorization: Bearer {{WHATSAPP_ACCESS_TOKEN}}
Content-Type: application/json
```

**Body (JSON)**:
```json
{
  "messaging_product": "whatsapp",
  "to": "{{ $json.user }}",
  "type": "text",
  "text": {
    "body": "{{ $json.respuesta }}"
  }
}
```

### 3.20 Enviar Telegram (SIN CAMBIOS FUNCIONALES)

- **Tipo**: `n8n-nodes-base.telegram` v1.2
- **chatId**: `={{ $json.user }}`
- **text**: `={{ $json.respuesta }}`
- **Notas**: Configuración correcta. Solo requiere credencial de bot configurada.

### 3.21 Enviar Gmail (MODIFICAR LEVE)

- **Tipo**: `n8n-nodes-base.gmail` v2.2
- **Cambio**: Agregar destinatario dinámico

**Configuración**:
```json
{
  "sendTo": "={{ $json.user }}",
  "subject": "Respuesta a tu consulta — Soporte e-commerce",
  "message": "={{ $json.respuesta }}",
  "options": {}
}
```

### 3.22 Registrar Interacción (NUEVO NODO — CRÍTICO)

- **Tipo**: `n8n-nodes-base.postgres`
- **Operación**: Execute Query
- **Credencial**: PostgreSQL (ecommerce_tesis)
- **Posición**: Después de CADA nodo de envío (Enviar WhatsApp, Enviar Telegram, Enviar Gmail)
- **Propósito**: Loguear la interacción completa con timestamps para TMR

**Conexiones de entrada**: Enviar WhatsApp → Registrar Interacción, Enviar Telegram → Registrar Interacción, Enviar Gmail → Registrar Interacción

Se puede usar un único nodo "Registrar Interacción" conectado desde los tres canales de envío (funciona como merge implícito — solo uno dispara por ejecución).

**SQL**:
```sql
INSERT INTO interactions (
    channel,
    user_id,
    message,
    intent,
    ai_response,
    order_id,
    is_urgent,
    received_at,
    responded_at,
    metadata
)
VALUES (
    '{{ $json.canal }}',
    '{{ $json.user }}',
    '{{ $json.message }}',
    '{{ $json.intent }}',
    '{{ $json.respuesta }}',
    {{ $json.order_id_found ? $json.order_id_found : 'NULL' }},
    {{ $json.urgente }},
    '{{ $json.received_at }}'::TIMESTAMPTZ,
    NOW(),
    '{"workflow_execution_id": "{{ $execution.id }}", "ticket_id": {{ $json.ticket_id || 'null' }} }'::JSONB
)
RETURNING id, received_at, responded_at,
    EXTRACT(EPOCH FROM (responded_at - received_at)) AS tmr_seconds;
```

**Notas**:
- `received_at` viene desde el nodo Normalizar (momento en que llegó el mensaje)
- `responded_at` es `NOW()` (momento en que se registra, justo después de enviar)
- La diferencia entre ambos es el TMR de esa interacción
- `metadata` incluye el ID de ejecución de n8n para trazabilidad

---

## 4. Flow Diagram

```
                    ┌──────────────────┐
                    │ Webhook WhatsApp │
                    │  POST /whatsapp  │
                    └────────┬─────────┘
                             │
                    ┌────────▼──────────┐
                    │Normalizar WhatsApp│
                    │ + received_at     │
                    └────────┬──────────┘
                             │
┌──────────────────┐         │         ┌─────────────────┐
│ Telegram Trigger │         │         │  Gmail Trigger   │
└────────┬─────────┘         │         │  (poll 1 min)    │
         │                   │         └────────┬─────────┘
┌────────▼──────────┐        │        ┌─────────▼─────────┐
│Normalizar Telegram│        │        │  Normalizar Gmail  │
│ + received_at     │        │        │  + received_at     │
└────────┬──────────┘        │        └─────────┬──────────┘
         │                   │                  │
         └───────────┬───────┘──────────────────┘
                     │
            ┌────────▼────────┐
            │  Merge Canales  │
            │  (passThrough)  │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │   Buscar FAQ    │  ← NUEVO: SELECT faq_responses
            │   (PostgreSQL)  │
            └────────┬────────┘
                     │
            ┌────────▼─────────────┐
            │  IA - Motor Decision │
            │  (GPT-4o-mini)       │
            │  Prompt mejorado     │
            └────────┬─────────────┘
                     │
            ┌────────▼────────┐
            │   Parse JSON    │
            │ + error handling│
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  Switch Intent  │
            └──┬───┬───┬───┬──┘
               │   │   │   │
    ┌──────────┘   │   │   └──────────────┐
    │ FAQ          │   │ RECLAMO         │ GENERAL
    │         ESTADO_PEDIDO              │ (default)
    │              │   │                 │
    │     ┌────────▼────────┐            │
    │     │  Buscar Pedido  │            │
    │     │  (PostgreSQL)   │            │
    │     └────────┬────────┘            │
    │     ┌────────▼─────────────┐       │
    │     │Preparar Resp. Pedido │       │
    │     └────────┬─────────────┘       │
    │              │   │                 │
    │              │   ┌────────▼──────────┐
    │              │   │  Crear Ticket     │
    │              │   │  (PostgreSQL)     │
    │              │   └────────┬──────────┘
    │              │   ┌────────▼──────────────┐
    │              │   │Preparar Resp. Ticket  │
    │              │   └────────┬──────────────┘
    │              │            │             │
    └──────┬───────┘────────────┘─────────────┘
           │
    ┌──────▼──────┐
    │ IF Urgente  │
    └──┬──────┬───┘
       │true  │false
  ┌────▼─────┐  │
  │Notificar │  │
  │  Admin   │  │
  └────┬─────┘  │
       └────┬───┘
            │
    ┌───────▼────────┐
    │  Router Canal   │
    └──┬─────┬─────┬──┘
       │     │     │
  whatsapp telegram email
       │     │     │
  ┌────▼──┐ ┌▼────┐ ┌▼───────┐
  │Enviar │ │Enviar│ │ Enviar │
  │WhatsApp│ │Telegr│ │ Gmail  │
  └────┬──┘ └──┬──┘ └───┬────┘
       │       │         │
       └───────┼─────────┘
               │
    ┌──────────▼───────────┐
    │ Registrar Interacción│  ← NUEVO
    │ INSERT interactions  │
    │ (con TMR)            │
    └──────────────────────┘
```

---

## 5. Intent Routing Logic

### 5.1 FAQ

**Trigger**: La IA clasifica el mensaje como `intent: "FAQ"`

**Flujo**:
1. Switch Intent → Output 0 (FAQ)
2. La respuesta ya viene generada por la IA (enriquecida con datos de `faq_responses` que se inyectaron en el prompt)
3. → IF Urgente → Router Canal → Enviar por canal → Registrar Interacción

**No requiere consulta adicional a BD** — la info de FAQ ya fue inyectada en el prompt antes de la clasificación.

### 5.2 ESTADO_PEDIDO

**Trigger**: La IA clasifica como `intent: "ESTADO_PEDIDO"` y opcionalmente extrae `order_id`

**Flujo**:
1. Switch Intent → Output 1 (ESTADO_PEDIDO)
2. → **Buscar Pedido** (PostgreSQL): busca por order_id O por user (teléfono/email)
3. → **Preparar Respuesta Pedido** (Function): formatea los datos como texto legible
4. → IF Urgente → Router Canal → Enviar por canal → Registrar Interacción

**Caso sin resultados**: Si no se encuentra ningún pedido, se responde pidiendo el número de pedido.

### 5.3 RECLAMO

**Trigger**: La IA clasifica como `intent: "RECLAMO"`

**Flujo**:
1. Switch Intent → Output 2 (RECLAMO)
2. → **Crear Ticket** (PostgreSQL): INSERT en `tickets` con prioridad automática (urgent si `urgente=true`)
3. → **Preparar Respuesta Ticket** (Function): genera mensaje de confirmación con número de ticket
4. → IF Urgente → Router Canal → Enviar por canal → Registrar Interacción

### 5.4 GENERAL

**Trigger**: La IA clasifica como `intent: "GENERAL"` o cualquier otro valor no reconocido (fallback del Switch)

**Flujo**:
1. Switch Intent → Output 3 (default/fallback)
2. La respuesta ya viene generada por la IA
3. → IF Urgente → Router Canal → Enviar por canal → Registrar Interacción

---

## 6. Interaction Logging

Cada interacción se registra en la tabla `interactions` al final del flujo, independientemente del intent o canal.

### INSERT completo

```sql
INSERT INTO interactions (
    channel,
    user_id,
    message,
    intent,
    ai_response,
    order_id,
    is_urgent,
    received_at,
    responded_at,
    metadata
)
VALUES (
    '{{ $json.canal }}',
    '{{ $json.user }}',
    '{{ $json.message }}',
    '{{ $json.intent }}',
    '{{ $json.respuesta }}',
    {{ $json.order_id_found ? $json.order_id_found : 'NULL' }},
    {{ $json.urgente }},
    '{{ $json.received_at }}'::TIMESTAMPTZ,
    NOW(),
    '{
      "workflow_execution_id": "{{ $execution.id }}",
      "ticket_id": {{ $json.ticket_id || 'null' }}
    }'::JSONB
)
RETURNING id, received_at, responded_at,
    EXTRACT(EPOCH FROM (responded_at - received_at)) AS tmr_seconds;
```

### Campos clave para TMR

| Campo | Valor | Origen |
|---|---|---|
| `received_at` | Timestamp ISO del nodo Normalizar | Se setea en el momento de recepción del mensaje |
| `responded_at` | `NOW()` en el INSERT | Se setea después de enviar la respuesta por el canal |
| TMR | `responded_at - received_at` | Calculado por la vista `v_chatbot_response_time` |

### Datos propagados por el pipeline

El campo `$json` al llegar a "Registrar Interacción" debe contener:

```json
{
  "canal": "whatsapp|telegram|email",
  "user": "phone_number|chat_id|email",
  "message": "mensaje original del cliente",
  "intent": "FAQ|ESTADO_PEDIDO|RECLAMO|GENERAL",
  "respuesta": "respuesta final enviada al cliente",
  "urgente": true|false,
  "received_at": "2026-04-15T10:30:00.000Z",
  "order_id_found": null|integer,
  "ticket_id": null|integer
}
```

---

## 7. Enhanced AI Prompt

El prompt se construye dinámicamente incluyendo las FAQ como contexto. En el nodo "IA - Motor Decision", el prompt debe ser:

```
Sos un asistente virtual de atención al cliente de un e-commerce.

## Tu tarea
Analizá el mensaje del cliente, clasificá su intención y generá una respuesta útil.
Respondé SIEMPRE en formato JSON válido, sin texto adicional fuera del JSON.

## Formato de respuesta (JSON estricto)
{
  "intent": "FAQ | ESTADO_PEDIDO | RECLAMO | GENERAL",
  "order_id": null,
  "urgente": false,
  "respuesta": "texto claro y amable para el cliente"
}

## Reglas de clasificación
- **FAQ**: Preguntas sobre métodos de pago, envíos, devoluciones, garantía, soporte, facturación u otras preguntas generales sobre el servicio.
- **ESTADO_PEDIDO**: El cliente pregunta por el estado de un pedido, envío o compra. Extraé el número de pedido si lo menciona (formato ORD-XXX) y ponelo en "order_id".
- **RECLAMO**: El cliente expresa una queja, insatisfacción, problema con un producto o servicio. Marcá "urgente": true si el tono es muy molesto o menciona acción legal.
- **GENERAL**: Cualquier otro mensaje (saludos, agradecimientos, consultas que no encajan en las categorías anteriores).

## Base de conocimiento FAQ
Usá esta información para responder preguntas frecuentes:

{{ $json.faq_context }}

## Reglas de respuesta
1. Respondé siempre en español argentino (vos, tenés, etc.)
2. Sé conciso pero amable
3. Si es ESTADO_PEDIDO y no mencionan número de pedido, pedilo amablemente
4. Si es RECLAMO, mostrá empatía y asegurá que se va a resolver
5. Nunca inventés datos de pedidos — si no tenés info, decí que lo vas a consultar
6. El campo "urgente" solo es true para reclamos graves o clientes muy molestos

## Mensaje del cliente
Canal: {{ $json.canal }}
Mensaje: {{ $json.message }}
```

### Construcción del contexto FAQ

Entre "Buscar FAQ" y "IA - Motor Decision", un nodo Function debe formatear las FAQ:

```javascript
const faqs = $input.all();
const originalData = $('Merge Canales').first().json;

let faqContext = '';
if (faqs && faqs.length > 0 && faqs[0].json.question) {
  faqContext = faqs.map(f =>
    `P: ${f.json.question}\nR: ${f.json.answer}`
  ).join('\n\n');
} else {
  faqContext = '(No hay FAQ disponibles en este momento)';
}

return [{
  ...originalData,
  faq_context: faqContext
}];
```

---

## 8. Channel Routing

### Router Canal — Lógica de enrutamiento

| Canal | Condición | Nodo destino | Notas |
|---|---|---|---|
| `whatsapp` | `$json.canal === "whatsapp"` | Enviar WhatsApp | HTTP Request a WhatsApp Cloud API |
| `telegram` | `$json.canal === "telegram"` | Enviar Telegram | Nodo nativo de n8n con Bot Token |
| `email` | `$json.canal === "email"` | Enviar Gmail | Nodo nativo de n8n con OAuth Gmail |

### Datos requeridos por cada nodo de envío

**Enviar WhatsApp**:
- `$json.user` → número de teléfono del destinatario (formato internacional, ej: `5492614123456`)
- `$json.respuesta` → texto de la respuesta

**Enviar Telegram**:
- `$json.user` → chat_id del destinatario (numérico)
- `$json.respuesta` → texto de la respuesta

**Enviar Gmail**:
- `$json.user` → email del destinatario
- `$json.respuesta` → cuerpo del email

---

## 9. Metrics — TMR (Tiempo Medio de Respuesta)

### Definición

**TMR** = Tiempo transcurrido desde que el mensaje del cliente es recibido (`received_at`) hasta que la respuesta es enviada (`responded_at`).

### Cómo se mide

1. **received_at**: Se registra en el nodo Normalizar del canal correspondiente (`new Date().toISOString()`)
2. **responded_at**: Se registra como `NOW()` en el INSERT de "Registrar Interacción", que se ejecuta inmediatamente después de enviar la respuesta
3. **TMR por interacción**: `EXTRACT(EPOCH FROM (responded_at - received_at))` en segundos

### Vista de Grafana

La vista `v_chatbot_response_time` ya está creada en el schema:

```sql
-- Ya existe en init.sql
SELECT
    i.id,
    i.channel,
    i.user_id,
    i.intent,
    i.received_at,
    i.responded_at,
    EXTRACT(EPOCH FROM (i.responded_at - i.received_at)) AS tmr_seconds,
    i.is_urgent
FROM interactions i
WHERE i.responded_at IS NOT NULL;
```

### Consultas útiles para Grafana

**TMR promedio general**:
```sql
SELECT
    ROUND(AVG(tmr_seconds)::NUMERIC, 2) AS avg_tmr_seg
FROM v_chatbot_response_time;
```

**TMR promedio por canal**:
```sql
SELECT
    channel,
    ROUND(AVG(tmr_seconds)::NUMERIC, 2) AS avg_tmr_seg,
    COUNT(*) AS total
FROM v_chatbot_response_time
GROUP BY channel;
```

**TMR promedio por intent**:
```sql
SELECT
    intent,
    ROUND(AVG(tmr_seconds)::NUMERIC, 2) AS avg_tmr_seg,
    COUNT(*) AS total
FROM v_chatbot_response_time
GROUP BY intent;
```

**Resumen diario** (vista ya existente):
```sql
SELECT * FROM v_daily_chatbot_summary ORDER BY fecha DESC LIMIT 30;
```

---

## 10. Testing Instructions

### 10.1 Prerequisites

```bash
# Levantar la infraestructura
docker compose up -d

# Verificar que todo corra
docker compose ps

# Verificar que las tablas existen
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "\dt"

# Verificar FAQ cargadas
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis \
  -c "SELECT id, category, LEFT(question, 50) FROM faq_responses;"
```

### 10.2 Test via Webhook (simula WhatsApp)

**Test FAQ**:
```bash
curl -X POST http://localhost:5678/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5492614000001",
            "text": { "body": "¿Cuáles son los métodos de pago?" }
          }]
        }
      }]
    }]
  }'
```

**Test ESTADO_PEDIDO**:
```bash
curl -X POST http://localhost:5678/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5492614000001",
            "text": { "body": "Quiero saber el estado de mi pedido ORD-001" }
          }]
        }
      }]
    }]
  }'
```

**Test RECLAMO**:
```bash
curl -X POST http://localhost:5678/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5492614000001",
            "text": { "body": "Estoy muy enojado, me llegó el producto roto y nadie me responde" }
          }]
        }
      }]
    }]
  }'
```

**Test GENERAL**:
```bash
curl -X POST http://localhost:5678/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5492614000001",
            "text": { "body": "Hola, buenas tardes" }
          }]
        }
      }]
    }]
  }'
```

### 10.3 Test via Telegram

1. Buscar el bot en Telegram (nombre configurado en BotFather)
2. Enviar mensajes de prueba:
   - `¿Cuánto tarda el envío?` → Esperar intent FAQ
   - `Estado de mi pedido ORD-001` → Esperar intent ESTADO_PEDIDO
   - `Quiero hacer un reclamo, el producto llegó dañado` → Esperar intent RECLAMO
   - `Hola` → Esperar intent GENERAL

### 10.4 Verify in Database

**Verificar interacciones registradas**:
```bash
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis \
  -c "SELECT id, channel, intent, LEFT(message, 40), tmr_seconds FROM v_chatbot_response_time ORDER BY id DESC LIMIT 10;"
```

**Verificar tickets creados**:
```bash
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis \
  -c "SELECT id, channel, user_id, status, priority, created_at FROM tickets ORDER BY id DESC LIMIT 5;"
```

**Verificar métricas**:
```bash
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis \
  -c "SELECT * FROM v_metrics_summary;"
```

---

## 11. Nodes to Add (Summary)

### 11.1 Buscar FAQ

| Propiedad | Valor |
|---|---|
| **Nombre** | Buscar FAQ |
| **Tipo** | `n8n-nodes-base.postgres` |
| **Operación** | Execute Query |
| **Posición** | Entre Merge Canales y un Function que prepara contexto |
| **SQL** | `SELECT question, answer, category FROM faq_responses WHERE enabled = TRUE ORDER BY category, id;` |
| **Conexión entrada** | Merge Canales → Buscar FAQ |
| **Conexión salida** | Buscar FAQ → Preparar Contexto FAQ (Function) → IA - Motor Decision |

### 11.2 Preparar Contexto FAQ

| Propiedad | Valor |
|---|---|
| **Nombre** | Preparar Contexto FAQ |
| **Tipo** | `n8n-nodes-base.function` v1 |
| **Posición** | Entre Buscar FAQ y IA - Motor Decision |
| **Código** | Ver sección 7 |
| **Conexión entrada** | Buscar FAQ → Preparar Contexto FAQ |
| **Conexión salida** | Preparar Contexto FAQ → IA - Motor Decision |

### 11.3 Preparar Respuesta Pedido

| Propiedad | Valor |
|---|---|
| **Nombre** | Preparar Respuesta Pedido |
| **Tipo** | `n8n-nodes-base.function` v1 |
| **Posición** | Entre Buscar Pedido y IF Urgente |
| **Código** | Ver sección 3.13 |
| **Conexión entrada** | Buscar Pedido → Preparar Respuesta Pedido |
| **Conexión salida** | Preparar Respuesta Pedido → IF Urgente |

### 11.4 Preparar Respuesta Ticket

| Propiedad | Valor |
|---|---|
| **Nombre** | Preparar Respuesta Ticket |
| **Tipo** | `n8n-nodes-base.function` v1 |
| **Posición** | Entre Crear Ticket y IF Urgente |
| **Código** | Ver sección 3.15 |
| **Conexión entrada** | Crear Ticket → Preparar Respuesta Ticket |
| **Conexión salida** | Preparar Respuesta Ticket → IF Urgente |

### 11.5 Registrar Interacción

| Propiedad | Valor |
|---|---|
| **Nombre** | Registrar Interacción |
| **Tipo** | `n8n-nodes-base.postgres` |
| **Operación** | Execute Query |
| **Posición** | Después de los tres nodos de envío (WhatsApp, Telegram, Gmail) |
| **SQL** | Ver sección 6 |
| **Conexión entrada** | Enviar WhatsApp → Registrar Interacción, Enviar Telegram → Registrar Interacción, Enviar Gmail → Registrar Interacción |
| **Conexión salida** | Fin del flujo |

### 11.6 Buscar Pedido (FIX — reemplaza nodo existente)

| Propiedad | Valor |
|---|---|
| **Nombre** | Buscar Pedido |
| **Tipo actual** | `n8n-nodes-base.mySql` v2.5 |
| **Tipo nuevo** | `n8n-nodes-base.postgres` |
| **Operación** | Execute Query |
| **SQL** | Ver sección 3.12 |
| **Conexión entrada** | Switch Intent Output 1 → Buscar Pedido |
| **Conexión salida** | Buscar Pedido → Preparar Respuesta Pedido → IF Urgente |

### 11.7 Crear Ticket (FIX — reemplaza nodo existente)

| Propiedad | Valor |
|---|---|
| **Nombre** | Crear Ticket |
| **Tipo actual** | `n8n-nodes-base.googleSheets` v4.7 |
| **Tipo nuevo** | `n8n-nodes-base.postgres` |
| **Operación** | Execute Query |
| **SQL** | Ver sección 3.14 |
| **Conexión entrada** | Switch Intent Output 2 → Crear Ticket |
| **Conexión salida** | Crear Ticket → Preparar Respuesta Ticket → IF Urgente |

---

## Appendix: Complete Connection Map

```
Webhook WhatsApp       → Normalizar WhatsApp
Telegram Trigger       → Normalizar Telegram
Gmail Trigger          → Normalizar Gmail
Normalizar WhatsApp    → Merge Canales (input 0)
Normalizar Telegram    → Merge Canales (input 1)
Normalizar Gmail       → Merge Canales (input 2)
Merge Canales          → Buscar FAQ                    ← NUEVO
Buscar FAQ             → Preparar Contexto FAQ         ← NUEVO
Preparar Contexto FAQ  → IA - Motor Decision           ← NUEVO
IA - Motor Decision    → Parse JSON
Parse JSON             → Switch Intent
Switch Intent [0:FAQ]          → IF Urgente            (respuesta ya lista)
Switch Intent [1:ESTADO_PEDIDO]→ Buscar Pedido         ← FIX conexión
Buscar Pedido          → Preparar Respuesta Pedido     ← NUEVO
Preparar Respuesta Pedido → IF Urgente
Switch Intent [2:RECLAMO]     → Crear Ticket           ← FIX conexión
Crear Ticket           → Preparar Respuesta Ticket     ← NUEVO
Preparar Respuesta Ticket → IF Urgente
Switch Intent [3:default]     → IF Urgente             (respuesta ya lista)
IF Urgente [true]      → Notificar Admin → Router Canal
IF Urgente [false]     → Router Canal
Router Canal [0:whatsapp]  → Enviar WhatsApp
Router Canal [1:telegram]  → Enviar Telegram
Router Canal [2:email]     → Enviar Gmail
Enviar WhatsApp        → Registrar Interacción         ← NUEVO
Enviar Telegram        → Registrar Interacción         ← NUEVO
Enviar Gmail           → Registrar Interacción         ← NUEVO
```
