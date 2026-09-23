# Mapa de pantallas — qué se ve, qué dice y si es verdad

Inventario de todo lo que puede aparecer en cámara, con una columna que importa más
que las otras: **¿es cierto lo que dice la pantalla?** Un jurado puede preguntar por
cualquiera de estas cosas.

Acompaña a [`GUION.md`](GUION.md), que dice en qué orden mostrarlas.

---

## Landing — http://localhost:3001

| Bloque | Qué muestra | ¿Verdad? |
|---|---|---|
| Actividad del sistema | Pedidos, consultas, casos y productos, leídos en vivo cada 10 s | **Sí.** Son los totales reales de esta instalación. |
| «49 segundos por pedido» | El costo del proceso manual | **Sí.** Suma de tres fases cronometradas sobre 10 órdenes válidas (`experiments/E4/`). |
| Botón «Comprar una unidad» | Mete un pedido real y muestra sus tiempos | **Sí.** Entra por el mismo webhook que usaría la tienda. |
| Botón «Pedir más de lo que hay» | El sistema frena la venta | **Sí.** El pipeline marca `no_stock` y avisa. |
| Chat | Responde el asistente | **Sí.** Mismo webhook que WhatsApp; la respuesta sale de `interactions`. |
| Resultados medidos | 0,063 s / 1,47 s / 92,7 % / 0 sobreventas | **Sí**, con sus intervalos. Salen del documento. |
| ≈780× | Razón contra el proceso manual | **Sí**, y la página aclara que es orden de magnitud de laboratorio. |
| Alcance y límites | 40,8 % perdido, 2 de 18, prompt vs. base | **Sí.** Está en el resumen de la tesis. |

**Nada que esconder en la landing.**

---

## Portal — http://localhost:8080 · `ventas@techstore.com.ar` / `Demo2026!`

### Inicio

| Qué se ve | ¿Verdad? | Nota |
|---|---|---|
| Pedidos de hoy, casos abiertos, tiempos | Sí | Se actualiza solo cada 4 s. |

### Pedidos

| Qué se ve | ¿Verdad? | Nota |
|---|---|---|
| 220 pedidos, 51 en **Pendiente** | Sí | **Los pendientes no son un defecto.** Vienen de las corridas de concurrencia: E1B 23/60 y E1B2 26/60. Es el 40,8 % que la tesis documenta como límite. Cero pendientes en la corrida secuencial. |
| Leyenda bajo la tabla | Sí | Explica qué es «Pendiente» y qué es «Sin stock». |

> **En cámara:** mostrá la lista filtrada por *Confirmados* y dejá los pendientes para
> cuando llegues a la placa de límites. Ahí sí, señalalos: es una medición, no una falla.

### Casos (Tickets)

| Qué se ve | ¿Verdad? | Nota |
|---|---|---|
| 638 casos: 628 WhatsApp, 10 Telegram | Sí, con matiz | 2115 de las interacciones de WhatsApp tienen identificador `@whatsapp.sim`: son del canal **simulado**, y la tesis lo declara así. Si preguntan, se dice. |

### Catálogo

| Qué se ve | ¿Verdad? | Nota |
|---|---|---|
| Stock y «mínimo N» | Sí | El mínimo es el punto de reposición: al llegar a ese número el producto se marca «Stock bajo» y el sistema avisa. Hay una leyenda bajo la tabla. |

### Métricas

| Qué se ve | ¿Verdad? | Nota |
|---|---|---|
| MTTD 56 ms · MTTR 81 ms · extremo a extremo 137 ms · 176 órdenes | Sí | **Abre filtrado en «Procesado por el sistema».** Es el valor por defecto a propósito. |

> **Cuidado con el selector de origen.** Si lo pasás a:
> - **«Todos los orígenes»** → MTTD salta a **16,77 s**, porque promedia el pipeline
>   automático con el proceso manual cronometrado. Ese número no describe a ninguno
>   de los dos y contradice el documento.
> - **«Proceso manual»** → muestra **313 s** de extremo a extremo, y el documento dice
>   **49,13 s**. No se contradicen: los 49,13 s son la suma de tres fases cronometradas;
>   los 313 s son reloj de pared entre marcas de tiempo. Si no querés explicar eso,
>   no toques ese filtro.
>
> **Dejá el selector como viene.**

### Conexiones

| Canal | Estado en pantalla | ¿Verdad? |
|---|---|---|
| WhatsApp | **Pendiente de aprobación** | **Sí.** Un número de WhatsApp Business lo aprueba Meta en 1-3 días hábiles. Es el estado correcto. |
| Telegram | **Conectado** | **Sí**, con el túnel levantado. Es el canal real del video. |
| Gmail | **Desconectado** | **Sí.** Faltan las credenciales de Google. |

> Ese **pendiente** de WhatsApp era un `conectado` sembrado. Se cambió: la pantalla
> ahora dice la verdad, y además es el comportamiento correcto en producción.

### Perfil

Datos de la cuenta. Sin observaciones.

### Monitoreo

Tres pestañas. **Dos se pueden mostrar, una no.**

| Pestaña | ¿Mostrar? | Por qué |
|---|---|---|
| En vivo | **Sí** | Feed de eventos: pedidos, mensajes, casos, alertas. Queda muy bien. |
| Conversaciones | **Sí** | Los hilos por canal y usuario, en formato chat. |
| **Workflow** | **No** | Dibuja el motor de automatización por dentro: nodos, ejecuciones, trazas. Es correcto y es útil, pero es exactamente lo que no va en una presentación comercial. |

---

## Qué NO mostrar, en una lista

- **Monitoreo → Workflow** (el motor por dentro).
- El selector de origen de **Métricas** en cualquier valor que no sea el que viene.
- Una consulta de **«estado de pedido»** en el chat de la landing: el asistente la
  atiende, pero el registro guarda solo su primera línea y en pantalla queda coja
  (motivo en [`../landing/README.md`](../landing/README.md)).
- La consola del navegador, la terminal, Docker, el editor.
- `localhost:5678` y cualquier pantalla del motor de automatización.

---

## El canal de Telegram: levantado

Telegram es el **único canal real** del video, y funciona. El bot es
`@tesis_postventa_bot`. Alguien le escribe desde su teléfono y el asistente contesta;
la conversación aparece en Monitoreo → Conversaciones.

Para que ande, el motor de automatización necesita una URL pública: la da el perfil
`tunnel` del compose (ngrok + un portero nginx con lista blanca).

```powershell
docker compose --profile tunnel up -d
```

Verificado el 23/09/2026: el túnel publica, Telegram tiene registrada la URL del túnel,
cero mensajes pendientes y ningún error. Desde internet **solo** pasa el webhook del
chatbot: la raíz, `/rest/login`, `/webhook/orden-nueva` y todo lo demás dan 404.

> **El túnel es una pieza más que se puede caer.** Si ngrok se corta en mitad de la
> grabación, se cae el canal de Telegram. El chat de la landing es la red de seguridad:
> corre local y no depende de internet.

**Antes de grabar**, comprobá que el túnel esté arriba:

```bash
curl -s -I https://envy-abruptly-grievance.ngrok-free.dev/
```

La primera línea tiene que decir **404**. Eso significa que el túnel publica y el portero bloquea lo que
no corresponde. Si da 502 o no responde, el túnel está caído.
