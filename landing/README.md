# Landing de presentación — Atendo

La cara pública del producto: qué resuelve, qué mide y dos cosas que se pueden probar
ahí mismo. Es lo que se recorre en el video de presentación.

**Dónde:** http://localhost:3001 · **Servicio:** `landing` en `docker-compose.yml`

```bash
docker compose up -d --build landing
```

## Qué hay

| Sección | Qué muestra |
|---|---|
| Hero | Contadores del sistema, leídos en vivo cada 10 s de `GET /demo/stats` |
| El problema | Los 49,13 s del proceso manual cronometrado |
| Qué hace | Las tres capacidades, en palabras del cliente |
| **Probalo · pedido** | Un botón que mete un pedido **real** por el pipeline y muestra sus tiempos |
| **Probalo · chat** | Un chat contra el asistente **real**, no una grabación |
| Resultados | Las cifras del trabajo, cada una con su intervalo de confianza |
| Alcance y límites | Lo que la medición dejó abierto |
| El panel | Qué tiene el portal del cliente, con enlace a `:8080` |
| Respaldo | Autores, dirección, institución |

## Cómo está armada

HTML, CSS y un guion sin dependencias, servidos por nginx. **No hay paso de build**:
lo que se muestra en cámara tiene que levantar siempre, sin `npm install` de por medio.

```
landing/
├── Dockerfile
├── nginx.conf              sirve el sitio y reenvía /api/demo/* al portal
├── security-headers.conf   CSP estricta, sin unsafe-inline
└── site/
    ├── index.html
    ├── styles.css          mismos tokens que dashboard-web/src/styles/tokens.css
    └── app.js              contadores, chat y pedido en vivo
```

El proxy `/api/` es lo que permite que el chat hable con el asistente sin CORS: para el
navegador, la landing y la API son el mismo origen. **Solo pasan tres rutas**
(`/demo/chat`, `/demo/order`, `/demo/stats`); cualquier otra da 404 en nginx, antes de
llegar a la API.

## Los tres endpoints públicos

Viven en `dashboard-api/app/routers/demo.py` y son los únicos sin JWT fuera de `/auth/*`.
Lógica en `app/core/demo_chat.py` y `app/core/demo_order.py`; pruebas en
`tests/test_demo_chat.py` (22) y `tests/test_demo_order.py` (11).

| Ruta | Qué hace |
|---|---|
| `GET /demo/stats` | Totales del sistema y promedios. Los promedios se acotan a `data_source='measured'`: sin ese filtro se mezclaría el baseline manual y la cifra no describiría a ninguno de los dos. |
| `POST /demo/chat` | Entrega el mensaje al webhook del asistente y espera a que el flujo escriba la respuesta en `interactions`. |
| `POST /demo/order` | Dispara un pedido por el webhook del pipeline y devuelve lo que quedó registrado. |

### Cómo no se pisan con los datos de la tesis

- Cada visitante recibe un identificador propio, `demo-<sesión>@whatsapp.sim`, y la
  espera filtra por ese identificador **exacto**. No hay forma de leer la conversación de
  otro visitante ni el corpus medido, que no lleva el prefijo `demo-`.
- Los pedidos salen con el prefijo `ORD-WEB-`, que ninguna corrida de la tesis usa
  (esas van con `ORD-E1A-`, `ORD-E1B-` y `ORD-E4-`).
- El escenario «con stock» usa el producto con **más** stock, así apretar el botón muchas
  veces no deja el catálogo en cero.
- `video/limpiar_demo.ps1` borra lo que generó la landing y repone el stock descontado.

### Freno

Doce acciones cada cinco minutos, contadas por sesión **y** por IP. Está en memoria: se
pierde al reiniciar la API, igual que el resto del estado efímero del portal.

---

## Limitación conocida: «estado de pedido» en el chat

El chat muestra `interactions.ai_response`, que es lo que el flujo dejó registrado.
Para las consultas de tipo **estado de pedido** eso queda incompleto.

**Qué pasa.** En el Flujo 2, el nodo `Preparar Respuesta Pedido` busca el pedido y le
pega el detalle a la respuesta del modelo (`respuesta = ai_respuesta + detalle`). Esa es
la que recibe el cliente por su canal. Pero el nodo `Registrar Interacción` guarda
`$('Parse JSON').item.json.respuesta`, o sea lo que salió de `Parse JSON`, **no** lo que
produjo `Preparar Respuesta Pedido`. El detalle nunca llega a la base:

```sql
SELECT count(*) FROM interactions WHERE ai_response LIKE '%Detalle de tu pedido%';
-- 0, sobre 2540 interacciones
```

**Consecuencia.** Un cliente por WhatsApp recibe el estado completo de su pedido;
el registro guarda solo la primera línea del modelo («dame un segundito»). En la landing,
que lee el registro, la respuesta queda coja.

**Qué no afecta.** Las cifras de la tesis se calcularon sobre `ai_response`, que es la
salida del modelo, y la clasificación de intención es correcta. Los números publicados
no dependen de esto.

**Por eso** la landing no sugiere una consulta de estado de pedido: sugiere dos consultas
frecuentes y un reclamo, que sí se registran completas.

**El arreglo** es cambiar una expresión en `Registrar Interacción`, de
`$('Parse JSON').item.json.respuesta` a `$json.respuesta`. **No está hecho**: el Flujo 2
es el artefacto medido de la tesis y tocarlo después de la aprobación es una decisión
de los autores, no de quien escribe la landing.

---

## Cambiar la marca

El nombre «Atendo» está solo en la landing y en las placas del video. Para cambiarlo:

```bash
grep -rn "Atendo" landing/site/ video/placas.html video/GUION.md
```

El logo es un SVG en línea (una «A» en un cuadrado índigo) repetido en el `<head>`
(favicon), la barra de navegación y el pie.
