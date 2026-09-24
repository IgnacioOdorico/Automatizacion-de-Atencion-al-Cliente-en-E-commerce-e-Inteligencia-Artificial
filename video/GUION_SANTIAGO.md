# Guion — Santiago

**Tu parte:** el portal del cliente por dentro. Todo lo que pide credenciales.
**Tiempo total:** un minuto y medio, en un solo tramo.
**Credenciales:** sí. Sos el único que se loguea.

También sos el que tiene el sistema corriendo, así que sobre vos caen dos cosas más:
dejarlo levantado para que graben los otros dos, y correr la limpieza al final.

---

## Lo que necesitás abierto

| Qué | Dónde | Credenciales |
|---|---|---|
| Portal | `http://localhost:8080` | `ventas@techstore.com.ar` / `Demo2026!` |

**Antes de grabar:**

1. Levantá todo: `docker compose up -d` y esperá a que los siete servicios estén arriba.
2. Entrá al portal y dejá la sesión iniciada **antes** de grabar. En el video no se ve el
   login: arrancás ya adentro.
3. Andá a **Métricas** y comprobá que el selector «Origen del dato» diga **«Procesado por
   el sistema»**. Es el valor que viene por defecto; si alguien lo movió, volvelo ahí.

> **Por qué importa ese selector:** si está en «Todos los orígenes», el MTTD promedio salta
> a 16,77 segundos, porque mezcla los pedidos automáticos con el proceso manual
> cronometrado. El documento dice 0,009 segundos. Un jurado con el papel al lado te lo
> pregunta. Con el filtro correcto muestra 56 milisegundos, que es coherente.

---

## Escena 6 — El portal del cliente · 3:50 a 5:20

Esta va **después** de la parte de Ignacio con el chat.

**En pantalla:** el portal, ya logueado. Recorrés cinco secciones del menú de la izquierda:
Inicio → Pedidos → Casos → Métricas → Conexiones.

**Decís:**

> Este es el panel del dueño de la tienda.
>
> **Inicio.** Los pedidos de hoy, los casos abiertos y los tiempos. Se actualiza solo.
>
> *(clic en Pedidos)*
>
> **Pedidos.** Cada venta con su estado y su detalle. *(señalás la fila resaltada)* Ahí está
> el pedido que metimos hace un minuto.
>
> *(clic en Casos)*
>
> **Casos.** Y acá está el reclamo que abrió el asistente, con el canal por el que entró y
> su nivel de urgencia. Nadie lo cargó a mano.
>
> *(clic en Métricas)*
>
> **Métricas.** Los tiempos de procesamiento, la distribución de estados de los pedidos, y
> qué tipo de consultas llegan con cuánto tarda el asistente en cada una.
>
> *(clic en Conexiones)*
>
> **Conexiones.** Desde acá el comercio conecta sus canales, sin tocar nada técnico.
> Telegram está conectado. WhatsApp figura pendiente porque un número de negocio lo aprueba
> Meta, y eso tarda de uno a tres días hábiles: no depende de nosotros. Gmail requiere que
> el comercio autorice su cuenta.

> **Ese último párrafo es el más valioso de tu parte.** No lo pases rápido. Estás
> explicando por qué hay un solo tilde verde, y la explicación es verdad. Es mucho más
> sólido que fingir tres conexiones.

---

## Dos advertencias

**Pedidos tiene 51 en «Pendiente».** No es una falla: vienen de las corridas de
concurrencia (38 % en una, 43 % en la otra). Es exactamente el 40,8 % que el trabajo
documenta como límite, y en la corrida secuencial hay cero.

Tenés dos opciones, las dos válidas:

- **Filtrar por «Confirmados»** antes de grabar, y dejar los pendientes para la placa de
  límites que muestra Ignacio.
- **Mostrarlos y nombrarlos**, agregando una frase: *«esos pendientes son pedidos que se
  perdieron bajo ráfaga; lo medimos y lo declaramos como límite»*.

La segunda es más valiente y queda mejor, si te sentís cómodo.

**No entres a Monitoreo → Workflow.** Esa pestaña dibuja el motor de automatización por
dentro: nodos, ejecuciones, trazas. Es correcta y es útil, pero es justo lo que no va en una
presentación comercial. Las otras dos pestañas de Monitoreo —**En vivo** y
**Conversaciones**— sí se pueden mostrar y quedan muy bien, si te sobra tiempo.

---

## Lo que además te toca a vos

**Antes de que graben los otros dos:** dejá el sistema levantado. Si graban desde sus
computadoras, pasales `http://192.168.1.2:3001` y confirmá que están en la misma red.

**Cuando terminaron todos:** corré la limpieza una vez.

```powershell
video/limpiar_demo.ps1
```

Borra los pedidos y las conversaciones que generaron los ensayos y repone el stock
descontado. No toca nada de las corridas de la tesis. Con `-Simular` te muestra qué
borraría sin borrar.

---

## Antes de mandar tu grabación

- [ ] Grabado a 1920×1080
- [ ] Sesión ya iniciada: el login no se ve
- [ ] El selector de Métricas en **«Procesado por el sistema»**
- [ ] No entraste a Monitoreo → Workflow
- [ ] Sin barra de marcadores ni extensiones a la vista
- [ ] Notificaciones en silencio
