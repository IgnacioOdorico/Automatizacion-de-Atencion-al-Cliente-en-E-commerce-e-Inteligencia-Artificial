# Guion del video de presentación — Atendo

**Duración objetivo:** 6 a 7 minutos
**Formato:** captura de pantalla 1920×1080 a 60 fps + voz en off
**Audiencia:** el tribunal de la defensa, y cualquiera a quien después le pasen el link
**Tono:** presentación de producto. Nada de jerga técnica, nada de código, nada de n8n.

---

## Antes de grabar — lista de control

Esto no es opcional: si algo de acá falla, se nota en cámara.

- [ ] Docker corriendo y los seis servicios arriba (`docker compose ps`)
- [ ] `http://localhost:3001` (landing) abre y el contador de actividad dice **En vivo**
- [ ] `http://localhost:8080` (panel) abre y entrás con `ventas@techstore.com.ar` / `Demo2026!`
- [ ] `http://localhost:8025` (bandeja de correo) abre
- [ ] Sesión del navegador ya iniciada en el panel, en otra pestaña, lista para pasar
- [ ] Navegador sin barras de extensiones, sin marcadores a la vista, pestaña única por ventana
- [ ] Notificaciones del sistema en silencio
- [ ] Zoom del navegador al 100 % (o 110 % si grabás en 1080p: el texto entra mejor)
- [ ] Probar una vez el botón «Comprar una unidad» y una consulta al asistente, **y después
      limpiar** (ver `video/limpiar_demo.ps1`)

> **El asistente tarda entre 1,5 y 4 segundos en responder.** No es un problema:
> es el tiempo real. Aprovechá esos segundos para narrar, no los cortes en la edición.
> Que se vea la espera es lo que prueba que no está grabado.

---

## Escena 1 — Apertura (0:00 – 0:25)

**En pantalla:** placa de apertura (`video/placas.html`, sección 1). Logo, título, autores.

**Voz en off:**

> Una PyME que vende por internet recibe un pedido. Alguien lo abre, revisa si hay stock,
> lo descuenta de una planilla, confirma la venta y le escribe al cliente.
> Después llega un mensaje preguntando cuándo llega el envío. Y otro. Y otro.
>
> Nosotros medimos cuánto lleva todo eso. Cuarenta y nueve segundos por pedido.
> Y las consultas no esperan a que sea horario de oficina.
>
> Esto es Atendo.

---

## Escena 2 — Qué es y qué resuelve (0:25 – 1:15)

**En pantalla:** la landing, `http://localhost:3001`. Scroll lento desde el hero hasta
la sección «Qué hace Atendo». Detenerse en las tres tarjetas.

**Voz en off:**

> Atendo se ocupa del post-venta de una tienda online. Hace tres cosas.
>
> **Procesa cada pedido**: lo registra, verifica el stock, lo descuenta, confirma la venta
> y le manda el correo al cliente. Si no hay stock, avisa en vez de vender de más.
>
> **Atiende a los clientes**: un asistente entiende qué está preguntando la persona
> —una duda, el estado de un pedido, un reclamo— y responde con la información real de
> la tienda. Un reclamo no lo improvisa: le abre un caso al comercio.
>
> **Y muestra todo**: un panel donde el dueño ve lo que está pasando, sin planillas.
>
> Estos números de acá arriba no son de adorno. Son los datos del sistema corriendo
> ahora mismo: doscientos dieciocho pedidos, más de dos mil quinientas consultas atendidas.

---

## Escena 3 — Un pedido de verdad, en vivo (1:15 – 2:30)

**En pantalla:** bajar a «Probalo», bloque 1. Apretar **Comprar una unidad**.
Dejar que el recorrido se marque paso por paso. Que se lea el recibo.

**Voz en off:**

> No se los voy a contar. Lo hacemos.
>
> *(apretar el botón)*
>
> Ese botón acaba de meter un pedido real en el sistema. No es una animación preparada:
> entró por el mismo camino que usaría la tienda.
>
> Lo registró. Verificó el stock y lo descontó. Confirmó la venta. Y le mandó el correo
> al cliente.
>
> *(señalar el tiempo)*
>
> Ochenta milisegundos, de punta a punta. El mismo trabajo, cronometrado a mano,
> nos llevó cuarenta y nueve segundos.

**En pantalla:** apretar **Pedir más de lo que hay**.

**Voz en off:**

> Ahora lo interesante. Pido más unidades de las que hay en stock.
>
> *(los dos pasos del medio quedan en ámbar)*
>
> El sistema no vendió. Frenó la venta y le avisó al cliente. Esto, que parece un detalle,
> es la diferencia entre una operación sana y un reembolso con un cliente enojado.
> En la prueba de concurrencia, con veinte pedidos casi simultáneos sobre el mismo
> producto, no hubo una sola sobreventa.

**Opcional (suma 20 s):** pasar a la pestaña de la bandeja de correo (`localhost:8025`)
y mostrar los dos correos recién llegados: el de confirmación y el de sin stock.

---

## Escena 4 — El asistente (2:30 – 3:45)

**En pantalla:** bajar al bloque 2. Escribir a mano (no pegar) una consulta.
Dejar que se vea el indicador de «escribiendo».

**Voz en off:**

> Lo mismo con el asistente. Le escribo como le escribiría un cliente por WhatsApp.
>
> *(escribir: «¿Hacen envíos a Mendoza?»)*
>
> *(mientras piensa)* Esa consulta ya salió del navegador, entró al sistema, el asistente
> la clasificó y está armando la respuesta con el catálogo y las políticas de la tienda.
>
> *(llega la respuesta)*
>
> Ahí está. Y abajo dice qué tipo de consulta era y cuánto tardó.
>
> *(clic en «Mi pedido llegó fallado, quiero un cambio»)*
>
> Este caso es distinto. No es una duda: es un reclamo. El asistente lo reconoce,
> responde con criterio, y además le abre un caso al comercio. Lo vamos a ver en el panel
> en un segundo.

---

## Escena 5 — El panel (3:45 – 5:15)

**En pantalla:** pasar a la pestaña del panel ya logueado, `http://localhost:8080`.
Recorrer: Dashboard → Pedidos → Tickets → Métricas → Conexiones.

**Voz en off:**

> Este es el panel del dueño de la tienda.
>
> **Inicio.** Los pedidos de hoy, los casos abiertos y los tiempos. Se actualiza solo.
>
> **Pedidos.** *(señalar la fila resaltada)* Ahí está el pedido que metimos hace un minuto,
> con su estado y su detalle.
>
> **Casos.** Y acá está el reclamo que abrió el asistente, con el canal por el que entró
> y su nivel de urgencia. Nadie lo cargó a mano.
>
> **Métricas.** Los tiempos de procesamiento, la distribución de estados, qué tipo de
> consultas llegan y cuánto tarda el asistente en cada una.
>
> **Conexiones.** Y desde acá el comercio conecta sus canales. WhatsApp, Telegram, correo.
> Sin tocar nada técnico.

> **Nota para quien graba:** no entres a *Monitoreo → Workflow*. Esa pestaña muestra el
> motor de automatización por dentro. Es correcta y es útil, pero no es lo que se muestra
> en una presentación comercial. Las otras dos pestañas de Monitoreo —En vivo y
> Conversaciones— sí se pueden mostrar y quedan muy bien.

---

## Escena 6 — Los resultados (5:15 – 6:15)

**En pantalla:** placas animadas (`video/placas.html`, secciones 2 a 4). Una cifra por placa.

**Voz en off:**

> Todo esto está medido, no estimado.
>
> **Cero coma cero seis tres segundos** de punta a punta, sobre cincuenta pedidos.
> Contra cuarenta y nueve segundos del proceso manual. Un factor cercano a
> setecientos ochenta, con un intervalo de confianza del noventa y cinco por ciento
> entre seiscientos ochenta y seis y ochocientos setenta y cinco.
>
> Y lo decimos como lo dice el trabajo: es un orden de magnitud de laboratorio,
> no una promesa de producción.
>
> **Un segundo y medio** tarda el asistente en responder.
>
> **Noventa y dos coma siete por ciento** de exactitud clasificando la consulta,
> con intervalo entre ochenta y siete y noventa y seis.
>
> Pero también medimos lo que no funciona. Bajo veinte pedidos casi simultáneos,
> el cuarenta por ciento quedó sin procesar. La corrección del contenido de las respuestas
> no quedó establecida: dos evaluadores no llegaron a un acuerdo suficiente.
> Y la exactitud depende mucho más de cómo está escrito el prompt que de la base de
> conocimiento de la tienda.
>
> Decimos las dos cosas porque un prototipo que solo cuenta lo que le sale bien
> no sirve para decidir nada.

---

## Escena 7 — Cierre (6:15 – 6:45)

**En pantalla:** placa de cierre (`video/placas.html`, sección 5).

**Voz en off:**

> Atendo es el prototipo de un Trabajo Integrador de la Tecnicatura Universitaria en
> Programación de la UTN, Facultad Regional Mendoza.
>
> Todo lo que vieron corre hoy, y todas las cifras son recalculables: los guiones de
> medición y los datos crudos están en el repositorio del trabajo.
>
> Lo que sigue es lo que la medición dejó marcado: resolver la pérdida bajo ráfaga,
> fijar un instrumento reproducible para evaluar el contenido de las respuestas,
> y llevarlo a varias tiendas sobre la misma instalación.
>
> Gracias.

---

## Notas de edición

| Qué | Cómo |
|---|---|
| Música | Instrumental suave, por debajo de −22 dB. Bajarla a −30 dB cuando hay voz. |
| Cortes | Ninguno durante las esperas reales del asistente ni del pedido. Son la prueba. |
| Zoom | Acercar (escala 1,15) cuando se marca un tiempo en pantalla o llega una respuesta. |
| Cursor | Movimientos lentos y decididos. Nada de buscar con el mouse. |
| Subtítulos | Sí. Muchos los van a ver sin audio. |
| Resolución | Grabar a 1920×1080. Si el texto queda chico, subir el zoom del navegador, no la resolución. |

## Qué NO mostrar

- La pestaña **Monitoreo → Workflow** (muestra el motor por dentro).
- La consola del navegador, la terminal, Docker Desktop, el editor de código.
- La URL `localhost:5678` ni ninguna pantalla del motor de automatización.
- Una consulta de tipo «estado de pedido» en el chat de la landing: el asistente la
  atiende, pero el registro guarda solo su primera línea y en pantalla queda coja
  (ver `landing/README.md`).
