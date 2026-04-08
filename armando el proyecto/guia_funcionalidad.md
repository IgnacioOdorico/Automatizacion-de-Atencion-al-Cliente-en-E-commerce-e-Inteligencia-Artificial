# Guía Funcional: Automatización de Atención al Cliente IA

## 1. Descripción General
Este sistema automatiza la gestión de consultas de E-commerce integrando **n8n** como orquestador y modelos de **Inteligencia Artificial** (OpenAI/Anthropic) como motor de decisión. El objetivo es centralizar la atención de WhatsApp, Telegram y Correo Electrónico en un único flujo inteligente.

## 2. Arquitectura de Decisión
A diferencia de los bots tradicionales basados en botones o menús rígidos, este sistema utiliza un **AI Agent**. 
- **Interpretación**: La IA analiza el texto del cliente y clasifica la intención (FAQ, Pedido, Soporte).
- **Herramientas (Tools)**: El agente tiene "superpoderes" para interactuar con el mundo exterior:
    - **SQL Tool**: Consulta el estado de pedidos en tiempo real.
    - **Ticketing Tool**: Registra incidencias en la base de datos cuando la IA no puede resolver el problema por sí sola.
- **Memoria**: El sistema mantiene el hilo de la conversación para responder de forma coherente.

## 3. Canales Integrados
- **WhatsApp**: Utiliza la API oficial de Meta. Permite recibir texto, imágenes y responder de forma estructurada.
- **Telegram**: Bot directo vinculado por Token.
- **Gmail**: Monitoreo de bandeja de entrada para responder consultas por correo.

## 4. Lógica de Negocio (Entrenamiento)
La IA ha sido instruida bajo las reglas de tu tesis:
- **Tono**: Formal (Uso de 'Usted', 'Estimado') pero Amigable.
- **FAQs**: Maneja respuestas sobre medios de pago, tiempos de envío (3-5 días) y políticas de la empresa.
- **Escalación**: Si detecta un reclamo serio o una duda técnica compleja, genera automáticamente un **Ticket de Soporte** en la base de datos MySQL.

## 5. Registro de Interacciones
Cada mensaje y cada respuesta de la IA se guarda en la tabla `interacciones` de MySQL, permitiendo auditoría y análisis de datos (Data Analytics) para la tesis.
