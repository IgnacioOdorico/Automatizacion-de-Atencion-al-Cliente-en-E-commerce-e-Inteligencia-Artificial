# Instrucciones para el asistente de Ignacio

> **Ignacio:** pasale este archivo entero a tu Claude y decile «seguí esto».
> Él se encarga de dejarte todo listo.

---

## Contexto

Ignacio es uno de los tres autores de un Trabajo Integrador de la UTN Facultad Regional
Mendoza, ya aprobado, y el que construyó el portal del cliente (`dashboard-api/` y
`dashboard-web/`). Ahora tienen que grabar un **video de presentación del producto** para la
defensa, repartido entre los tres.

**La parte de Ignacio** son dos tramos, unos tres minutos: las dos demostraciones en vivo de
la landing (un pedido real y una conversación con el asistente), y las placas de resultados
y límites. **No necesita credenciales**: no se loguea en ningún lado.

Su guion, con el texto exacto a narrar, está en
[`video/GUION_IGNACIO.md`](GUION_IGNACIO.md). Tu trabajo es dejarle el entorno listo.

> **Lo importante de su parte:** las dos demostraciones son **reales**. Un botón mete un
> pedido de verdad al sistema y muestra los tiempos de *ese* pedido; el chat le habla al
> asistente de verdad. Eso es lo que hace creíble el video, y por eso su parte es la que más
> depende de que el sistema esté vivo.

---

## Paso 1 — Traer el proyecto

```bash
git fetch origin
git checkout feature/landing-demo
git pull
```

Esa rama sale de `feature/dashboard-cliente` (la de Ignacio) y le agrega la landing, los
guiones y las placas. Su trabajo del portal está intacto adentro.

**Verificá que existan** `video/GUION_IGNACIO.md`, `video/placas.html` y la carpeta
`landing/`.

---

## Paso 2 — Lo que no depende de nadie: las placas

El segundo tramo de Ignacio (resultados y límites) usa las **placas**: una presentación
animada en un HTML suelto, **sin dependencias ni servidor**.

```bash
start video/placas.html          # Windows
open video/placas.html           # macOS
```

Comprobá que `F` la ponga en pantalla completa, que `→` avance, y que el cartelito de ayuda
de abajo desaparezca solo a los ~2,6 segundos. Ignacio usa las placas **2, 3, 4 y 5**.

Con esto ya puede grabar la escena 7. **El otro tramo sí necesita el sistema.**

---

## Paso 3 — El sistema en vivo: la decisión importante

Las escenas 4 y 5 necesitan, además de la landing, **la API, el motor de automatización, la
base de datos con los datos reales y una credencial de un servicio de IA**. Eso corre hoy
**solo en la máquina de Santiago**.

### Escenario A — Ignacio está en la misma red que Santiago (recomendado)

Pedile a Santiago que tenga el sistema levantado y que le pase su IP local (al escribir
esto, `192.168.1.2`). Después:

```powershell
video\verificar_entorno.ps1 -Host 192.168.1.2 -Completo
```

Con `-Completo` dispara **un pedido y una consulta de verdad**, que es exactamente lo que
Ignacio va a hacer en cámara. Si los dos dan OK, está listo.

> Ese `-Completo` deja un pedido y una conversación en la base. **Avisale a Santiago** para
> que corra `video/limpiar_demo.ps1` antes de la toma buena.

Sin PowerShell (macOS/Linux):

```bash
curl -s http://192.168.1.2:3001/api/demo/stats
curl -s -X POST http://192.168.1.2:3001/api/demo/order \
     -H 'Content-Type: application/json' \
     -d '{"session":"pruebaignacio1","scenario":"con_stock"}'
```

El segundo tiene que devolver un JSON con `"status":"confirmed"` y los tiempos.

### Escenario B — Ignacio NO está en la red de Santiago

Acá hay que decidir, y **la decisión no es tuya ni de Ignacio**:

**Opción 1 — grabar en la máquina de Santiago.** Es lo más simple y lo que recomiendo.

**Opción 2 — montar el sistema completo en la máquina de Ignacio.** Es posible, pero
necesita cosas que Ignacio no tiene y que **solo Santiago puede decidir compartir**:

| Qué falta | Por qué es de Santiago |
|---|---|
| `.env` con la clave de cifrado del motor, la contraseña de la base y los tres secretos del portal | Son secretos de esa instalación. Sin la clave de cifrado exacta, las credenciales cargadas en el motor quedan ilegibles. |
| Credenciales dentro del motor: base de datos, correo y **un servicio de IA** | La del servicio de IA **se paga por uso**. Compartirla es una decisión de Santiago, no un paso técnico. |
| Una copia de la base con los datos reales | 218 pedidos, 2540 conversaciones, 638 casos. Sin eso, los contadores muestran una tienda vacía y el video pierde fuerza. |

**Si Santiago decide compartirlo**, el camino es: `docker compose up -d`, restaurar el
volcado de la base, cargar las credenciales en la interfaz del motor, y recién ahí correr el
verificador. Es una tarde de trabajo. **No lo empieces sin que Santiago lo confirme
explícitamente.**

**Opción 3 — grabar solo el tramo de las placas** (escena 7) y que las escenas 4 y 5 las
grabe otro, o Ignacio mismo cuando esté con Santiago.

---

## Paso 4 — Ensayar antes de la toma buena

La parte de Ignacio tiene un detalle que conviene ensayar: **los tiempos que salen en
pantalla son reales y cambian en cada corrida**. Su guion dice «ochenta milisegundos», pero
lo que salga puede ser 70, 90 o 130. **Tiene que decir el que ve**, no el del guion. Ese es
el punto de toda la escena.

Hacele ensayar una vez:
1. Apretar «Comprar una unidad» y ver cuánto da.
2. Apretar «Pedir más de lo que hay» y ver los dos pasos en ámbar.
3. Escribir una consulta en el chat y cronometrar mentalmente la espera (1,5 a 3,5 s).

Y después **avisá que ensayaron**, para que Santiago limpie antes de la toma buena.

---

## Paso 5 — Dejarlo listo para grabar

- [ ] Grabadora a **1920×1080** (OBS).
- [ ] Navegador **sin marcadores ni extensiones a la vista**, una sola pestaña.
- [ ] **Notificaciones en silencio.**
- [ ] La tarjeta «Actividad del sistema» diciendo **En vivo**.
- [ ] Ensayado el pedido y el chat al menos una vez.

Y que abra [`video/GUION_IGNACIO.md`](GUION_IGNACIO.md).

---

## Reglas que no se rompen

- **No cortar las esperas reales en la edición.** El asistente tarda entre 1,5 y 3,5
  segundos. Esa espera es la prueba de que no está grabado. Se narra encima.
- **No usar la consulta de «estado de pedido»** en el chat. El asistente la atiende, pero el
  registro guarda solo su primera línea y en pantalla queda coja. El motivo completo está en
  [`../landing/README.md`](../landing/README.md). Usar las dos consultas sugeridas.
- **No entrar al portal** (`:8080`). Esa parte la graba Santiago.
- **No grabar las secciones de texto de la landing** (el problema, qué hace el producto):
  son de Juan Cruz.
- **No mostrar** `localhost:5678`, la consola del navegador, la terminal, Docker ni el
  editor. El video es una presentación de producto.
- **No hacer commits ni push** desde esta máquina salvo que Ignacio lo pida expresamente.

---

## Si algo falla

| Síntoma | Qué pasa | Qué hacer |
|---|---|---|
| «Sin conexión» en la tarjeta de actividad | El sistema no está levantado o no llegás por red | Que Santiago corra `docker compose up -d`; confirmá la IP |
| El botón de pedido da error | El motor de automatización no responde | Que Santiago revise que el motor esté arriba y el flujo de pedidos activo |
| El chat responde «El asistente no está disponible» | Falta la credencial del servicio de IA en el motor, o el flujo del chat está inactivo | Es del lado de Santiago |
| El chat tarda y devuelve «tardó más de lo esperado» | El servicio de IA está lento | Reintentá. Si pasa siempre, avisá a Santiago |
| «Muchas consultas seguidas» | Hay un freno de 12 acciones cada 5 minutos, por sesión y por IP | Esperá cinco minutos. Es a propósito: el endpoint es público |
| Los acentos salen rotos al probar por consola | La terminal manda mal el UTF-8; **no es la aplicación** | Probá desde el navegador, que manda bien. Si necesitás consola, mandá el cuerpo desde un archivo |
| Las placas sin la tipografía buena | Sin internet, la fuente de Google Fonts no carga | Con internet se arregla solo |
