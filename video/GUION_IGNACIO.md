# Guion — Ignacio

**Tu parte:** las dos demostraciones en vivo de la landing, y las placas de resultados y
límites.
**Tiempo total:** unos 3 minutos, en dos tramos del video.
**Credenciales:** ninguna. No te logueás en ningún lado.

Tenés la parte que convence: sos el que muestra que el sistema funciona de verdad.

---

## Lo que necesitás abierto

| Qué | Dónde |
|---|---|
| La landing | `http://localhost:3001` — o `http://192.168.1.2:3001` si grabás desde tu computadora con el sistema corriendo en la de Santiago |
| Las placas | el archivo `video/placas.html`, abierto en el navegador |

**Antes de grabar, dos comprobaciones:**

1. En la landing, la tarjeta «Actividad del sistema» tiene que decir **En vivo** en verde.
   Si dice «Sin conexión», el sistema no está levantado: avisale a Santiago.
2. **Ensayá una vez** el botón «Comprar una unidad» y una consulta en el chat, para ver los
   tiempos. Después avisá que ensayaste, para que se corra la limpieza antes de la toma
   buena (`video/limpiar_demo.ps1`).

**Las placas:** `F` para pantalla completa, `→` para avanzar. El cartelito de ayuda se va
solo a los 2,6 segundos: esperá a que desaparezca.

---

## Escena 4 — Un pedido real, en vivo · 1:40 a 2:50

**En pantalla:** la landing, sección **«Probalo»**, bloque 1 («Meté un pedido»).

### Parte A — con stock

Apretás **«Comprar una unidad»** y dejás que el recorrido se marque paso por paso.
Son cuatro pasos y tardan menos de dos segundos en total. **No cortes.**

**Decís:**

> No se los voy a contar. Lo hacemos.
>
> *(apretás el botón)*
>
> Ese botón acaba de meter un pedido real en el sistema. No es una animación preparada:
> entró por el mismo camino que usaría la tienda.
>
> Lo registró. Verificó el stock y lo descontó. Confirmó la venta. Y le mandó el correo
> al cliente.
>
> *(señalás el tiempo del último paso)*
>
> Ochenta milisegundos, de punta a punta. El mismo trabajo, cronometrado a mano, nos llevó
> cuarenta y nueve segundos.

> **Ojo con el número.** El tiempo que salga en pantalla es el real de *ese* pedido: puede
> dar 70, 90 o 130 milisegundos. **Decí el que veas**, no el del guion. Es el punto de toda
> la escena.

### Parte B — sin stock

Ahora apretás **«Pedir más de lo que hay»**. Los dos pasos del medio quedan en ámbar.

**Decís:**

> Ahora lo interesante. Pido más unidades de las que hay en stock.
>
> *(los dos pasos del medio quedan en ámbar)*
>
> El sistema no vendió. Frenó la venta y le avisó al cliente. Esto, que parece un detalle,
> es la diferencia entre una operación sana y un reembolso con un cliente enojado.
>
> En la prueba de concurrencia, con veinte pedidos casi simultáneos sobre el mismo
> producto, no hubo una sola sobreventa.

---

## Escena 5 — El asistente responde · 2:50 a 3:50

**En pantalla:** bajás al bloque 2 («Escribile al asistente»).

**Escribí a mano, no pegues.** Que se vea tipear.

**Decís:**

> Lo mismo con el asistente. Le escribo como le escribiría un cliente por WhatsApp.
>
> *(escribís: «¿Hacen envíos a Mendoza?»)*
>
> *(mientras aparecen los puntitos)* Esa consulta ya salió del navegador, entró al sistema,
> el asistente la clasificó y está armando la respuesta con el catálogo y las políticas de
> la tienda.
>
> *(llega la respuesta)*
>
> Ahí está. Y abajo dice qué tipo de consulta era y cuánto tardó.
>
> *(hacés clic en «Mi pedido llegó fallado, quiero un cambio»)*
>
> Este caso es distinto. No es una duda: es un reclamo. El asistente lo reconoce, responde
> con criterio, y además le abre un caso al comercio. Eso se ve en el panel, que lo muestra
> Santiago en un minuto.

> **La espera es la prueba.** El asistente tarda entre 1,5 y 3,5 segundos. **No la cortes
> en edición.** Narrá encima. Si lo cortás, parece grabado.

> **No uses la consulta de «estado de pedido».** El asistente la atiende, pero el registro
> guarda solo su primera línea y en pantalla queda coja. Usá las dos que están sugeridas.

---

## Escena 7 — Resultados y límites · 5:20 a 6:20

Esta va **después** de la parte de Santiago con el portal.

**En pantalla:** las placas. Pasás por la **2**, la **3**, la **4** y la **5**, más o menos
quince segundos cada una.

### Placa 2 — la comparación

> Todo esto está medido, no estimado. Cuarenta y nueve segundos a mano, contra cero coma
> cero sesenta y tres segundos con el sistema. Sobre cincuenta pedidos.

### Placa 3 — el factor

> Un factor cercano a setecientos ochenta, con un intervalo de confianza del noventa y
> cinco por ciento entre seiscientos ochenta y seis y ochocientos setenta y cinco.
>
> Y lo decimos como lo dice el trabajo: es un orden de magnitud de laboratorio, no una
> promesa de producción. En una instalación real, la red y las APIs externas mandan.

> **Esa última frase no se saca.** Es lo que separa un dato de un chamullo, y el tribunal
> lo va a notar.

### Placa 4 — el asistente

> Un segundo y medio tarda el asistente en responder. Noventa y dos coma siete por ciento
> de exactitud clasificando la consulta, con intervalo entre ochenta y siete y noventa y
> seis. Y cero ventas sin stock con veinte pedidos casi simultáneos.

### Placa 5 — los límites

> Pero también medimos lo que no funciona.
>
> Bajo ráfaga, el cuarenta por ciento de los pedidos quedó sin procesar.
>
> La corrección del contenido de las respuestas no quedó establecida: dos evaluadores no
> llegaron a un acuerdo suficiente, y una verificación automática encontró dos de dieciocho
> respuestas con datos que la base no respalda.
>
> Y la exactitud depende mucho más de cómo está escrito el prompt que de la base de
> conocimiento de la tienda.
>
> Decimos las dos cosas porque un prototipo que solo cuenta lo que le sale bien no sirve
> para decidir nada.

> **Esta placa es la más importante del video.** No la pases rápido ni bajes la voz.
> Un jurado que escucha a alguien declarar sus propios límites deja de buscarlos.

---

## Cosas que no tenés que hacer

- **No entres al panel** (`localhost:8080`). Esa parte la graba Santiago.
- **No grabes las secciones de texto** de la landing (el problema, qué hace el producto):
  esas son de Juan Cruz.
- **No abras** `localhost:5678`, ni la consola del navegador, ni Docker.
- **No uses** la consulta de «estado de pedido» en el chat.

---

## Antes de mandar tu grabación

- [ ] Grabado a 1920×1080
- [ ] La tarjeta «Actividad del sistema» decía **En vivo**
- [ ] Dijiste los tiempos que salieron en pantalla, no los del guion
- [ ] No cortaste ninguna espera del asistente ni del pedido
- [ ] El cartelito de ayuda de las placas no aparece en ningún cuadro
- [ ] Avisaste que ensayaste, para que se corra `video/limpiar_demo.ps1`
