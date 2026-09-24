# Guion del video — índice y montaje

**Duración objetivo:** 6 a 7 minutos · **Formato:** captura de pantalla 1920×1080 + voz en off
**Audiencia:** el tribunal de la defensa, y cualquiera a quien después le pasen el link
**Tono:** presentación de producto. Nada de jerga técnica, nada de código, nada del motor por dentro.

El guion está partido en tres por una razón práctica: **quien graba una pantalla que pide
credenciales tiene que tener esas credenciales**. Todo lo que no las pide se reparte.

| Quién | Qué graba | ¿Necesita credenciales? | Su guion |
|---|---|---|---|
| **Juan Cruz** | Apertura, el problema, qué hace el producto, cierre | No | [GUION_JUANCRUZ.md](GUION_JUANCRUZ.md) |
| **Ignacio** | La landing en vivo (pedido + chat) y las placas de resultados y límites | No | [GUION_IGNACIO.md](GUION_IGNACIO.md) |
| **Santiago** | El portal del cliente por dentro | **Sí** (cuenta demo) | [GUION_SANTIAGO.md](GUION_SANTIAGO.md) |

### Para que cada uno arme su máquina

Juan Cruz e Ignacio no tienen el sistema corriendo. Cada uno tiene una guía pensada para
pasarle a su asistente de IA, que lo deja listo sin que tengan que entender la instalación:

- [PARA_TU_CLAUDE_JUANCRUZ.md](PARA_TU_CLAUDE_JUANCRUZ.md)
- [PARA_TU_CLAUDE_IGNACIO.md](PARA_TU_CLAUDE_IGNACIO.md)

Y para comprobar si una máquina puede grabar, desde cualquiera de las tres:

```powershell
video/verificar_entorno.ps1                      # contra esta máquina
video/verificar_entorno.ps1 -Host 192.168.1.2    # contra la de Santiago
video/verificar_entorno.ps1 -Completo            # además dispara un pedido y una consulta
```

---

## Cómo se arma el video

| # | Minuto | Quién | Escena |
|---|---|---|---|
| 1 | 0:00 – 0:25 | Juan Cruz | Apertura (placa) |
| 2 | 0:25 – 1:00 | Juan Cruz | El problema (landing) |
| 3 | 1:00 – 1:40 | Juan Cruz | Qué hace el producto (landing) |
| 4 | 1:40 – 2:50 | **Ignacio** | Un pedido real, en vivo (landing) |
| 5 | 2:50 – 3:50 | **Ignacio** | El asistente responde (landing) |
| 6 | 3:50 – 5:20 | **Santiago** | El portal del cliente |
| 7 | 5:20 – 6:20 | **Ignacio** | Resultados y límites (placas) |
| 8 | 6:20 – 6:50 | Juan Cruz | Cierre (placa) |

Las escenas 2 y 3 son la misma pasada de scroll por la landing: Juan Cruz puede grabarlas
de corrido y cortar en edición.

---

## Lo único que hace falta coordinar

**La landing en vivo necesita el sistema corriendo.** Las secciones de texto son HTML y se
ven siempre, pero los contadores del encabezado, el botón de pedido y el chat le hablan a
la API, al motor de automatización y a la base. Eso hoy corre **solo en la máquina de
Santiago**.

Tres formas de resolverlo, de más simple a menos:

1. **Graban los tres en la máquina de Santiago**, en momentos distintos. Cero configuración.
2. **Desde la red local**: con el sistema levantado en la máquina de Santiago, Juan Cruz e
   Ignacio abren `http://192.168.1.2:3001` desde su propia computadora y graban ahí. Misma
   red, mismo Wi-Fi. Los botones del portal se reescriben solos a esa dirección.
3. **Levantar el sistema en otra máquina**: posible, pero hay que cargar credenciales del
   motor y restaurar la base. Es el camino largo.

> La opción 2 es la más cómoda: cada uno graba en su computadora, con su micrófono, y
> nadie toca configuración.

---

## Reglas que valen para los tres

**Grabá a 1920×1080.** Si el texto queda chico, subí el zoom del navegador (110 % anda
bien), no bajes la resolución.

**Navegador limpio.** Sin barra de marcadores, sin extensiones a la vista, una sola pestaña
por ventana, notificaciones del sistema en silencio.

**No cortes las esperas reales.** El asistente tarda entre 1,5 y 3,5 segundos. Esa espera es
la prueba de que no está grabado. Narrá encima en vez de cortar.

**El cursor se mueve despacio y decidido.** Nada de buscar con el mouse.

### Qué NO muestra nadie

- **Monitoreo → Workflow** en el portal: dibuja el motor de automatización por dentro.
- El selector de **Origen del dato** en Métricas, en cualquier valor que no sea el que viene.
- Una consulta de **«estado de pedido»** en el chat de la landing (motivo en
  [`../landing/README.md`](../landing/README.md)).
- La consola del navegador, la terminal, Docker, el editor de código.
- `localhost:5678` ni ninguna pantalla del motor de automatización.

El detalle de cada pantalla —qué dice y si es cierto— está en [PANTALLAS.md](PANTALLAS.md).

---

## Después de grabar

Corré esto una vez, cuando terminaron todos:

```powershell
video/limpiar_demo.ps1
```

Borra los pedidos y las conversaciones que generaron los ensayos y repone el stock
descontado. No toca nada de las corridas de la tesis.

---

## Notas de edición

| Qué | Cómo |
|---|---|
| Música | Instrumental suave, por debajo de −22 dB. A −30 dB cuando hay voz. |
| Cortes | Ninguno durante las esperas reales del asistente ni del pedido. |
| Zoom | Acercar (escala 1,15) cuando se marca un tiempo en pantalla o llega una respuesta. |
| Subtítulos | Sí. Muchos lo van a ver sin audio. |
| Transiciones | Corte seco entre escenas de distinta persona. Nada de barridos. |
