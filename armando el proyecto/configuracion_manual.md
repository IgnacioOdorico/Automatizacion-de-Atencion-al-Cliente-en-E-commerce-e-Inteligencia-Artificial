# Guía de Configuración Manual (Mano a la masa)

Ignacio, acá tenés los puntos donde **SÍ O SÍ** tenés que intervenir para que el .json que te pasé funcione en tu máquina.

## 1. Conexión a MySQL (Docker)
Como tu n8n está en Docker, cuando configures el nodo de **MySQL** (las credenciales), hacé esto:
- **Host**: No uses `localhost` ni `127.0.0.1`. Usá `host.docker.internal`.
- **Puerto**: `3306` (por defecto).
- **Usuario/Pass**: Los que hayas configurado en tu MySQL local.
- **Database**: `ecommerce_db`.

## 2. Nodos que requieren tu Token/API Key
En el archivo `n8n_ecommerce_ia.json`, tenés que entrar a estos nodos y "conectar" tus cuentas:

### A. WhatsApp Webhook (Meta)
- Tenés que ir a [Meta for Developers](https://developers.facebook.com/), crear una App y obtener el **Verify Token**.
- En el nodo Webhook de n8n, copiá la **Production URL** y pegala en el panel de Meta.

### B. Telegram Bot
- Hablá con [@BotFather](https://t.me/botfather) en Telegram.
- Creá un bot y obtené el **API Token**.
- Pegalo en el nodo "Telegram Trigger" y en el de respuesta.

### C. OpenAI (El Cerebro)
- El nodo "AI Agent" necesita una credencial de **OpenAI API**.
- Generá una Key en [platform.openai.com](https://platform.openai.com/).
- **IMPORTANTE**: Asegurate de tener saldo en la cuenta de OpenAI, si no, el bot te va a tirar error de "Quota Exceeded".

## 3. Webhooks y Túneles
Para que Meta y Telegram puedan "ver" tu n8n local, necesitás un túnel (si no tenés una IP pública):
- Te recomiendo usar **Ngrok** o **Cloudflare Tunnel**.
- La URL que te den ellos es la que tenés que configurar en los Webhooks de Meta y Telegram.

## 4. Pruebas de fuego
Una vez conectado todo:
1. Dale a **"Execute Workflow"** en n8n.
2. Mandale un "Hola" por WhatsApp o Telegram.
3. Fijate en la consola de n8n si el "AI Agent" está pensando (se pone una pelotita girando).
4. Si falla, revisá el nodo de MySQL; usualmente es el primer lugar donde hay problemas de red en Docker.
