# Guía de Credenciales — N8N

Configurar estas credenciales en: http://localhost:5678 → Credentials

---

## 1. PostgreSQL
**Nombre:** `Postgres account`  
**Nodos que la usan:** Todos los nodos de base de datos en Flujo 1 y Flujo 2

| Campo    | Valor            |
|----------|------------------|
| Host     | `postgres`       |
| Port     | `5432`           |
| Database | `ecommerce_tesis`|
| User     | `n8n_user`       |
| Password | `n8n_pass`       |
| SSL      | `disabled`       |

---

## 2. SMTP — Mailpit (desarrollo)
**Nombre:** `SMTP account`  
**Nodos que la usan:** Email Confirmación, Email Sin Stock (Flujo 1)

| Campo    | Valor      |
|----------|------------|
| Host     | `mailpit`  |
| Port     | `1025`     |
| User     | *(vacío)*  |
| Password | *(vacío)*  |
| SSL/TLS  | `None`     |

> Los emails se capturan en http://localhost:8025 — no se envían realmente.

---

## 3. OpenAI
**Nombre:** `OpenAi account`  
**Nodos que la usan:** Nodo de clasificación IA en Flujo 2

| Campo   | Valor                        |
|---------|------------------------------|
| API Key | `sk-...` *(tu clave real)*   |

> Obtener API Key: https://platform.openai.com → API Keys → Create new secret key  
> Modelo usado: `gpt-4o-mini`

---

## Cómo asignar las credenciales a los nodos

1. Abrí el workflow en http://localhost:5678
2. Click sobre cualquier nodo
3. En el campo **Credential** seleccioná la credencial correspondiente
4. Guardá el workflow

> ⚠️ Si un nodo muestra punto rojo significa que le falta la credencial.

---

## Verificar que funciona

1. Abrí **Flujo 1**
2. Click en el nodo **"Registrar Orden"** → **"Execute step"**
3. Verde = OK | Rojo = revisar credencial

---

## Para producción (opcional)

| Servicio             | Credencial necesaria         | Dónde obtenerla                        |
|----------------------|------------------------------|----------------------------------------|
| WooCommerce          | Consumer Key + Secret        | WooCommerce → Settings → API           |
| Shopify              | Access Token                 | Shopify → Apps → Custom apps           |
| Telegram Bot         | Bot Token                    | @BotFather en Telegram                 |
| WhatsApp Business    | Phone ID + Token             | Meta for Developers → WhatsApp API     |
| Gmail                | OAuth2 Client ID + Secret    | Google Cloud Console → Credentials     |
