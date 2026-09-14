# E6 v1 — Diagnóstico del instrumento de tres niveles

Fecha: 2026-09-14. Datos: `e6_maximo_muguruza.csv` y `e6_joaquin_maya.csv` (tercera
corrida de Joaquín; las dos anteriores están en `descartadas/`). Salida completa del
análisis: `analisis_v1.txt`.

## Resultado

| | Máximo Muguruza | Joaquín Maya |
|---|---|---|
| Mediana por ítem | 10,0 s | 8,8 s (mitades: 9,0 y 8,4) |
| Control de validez (≥ 8 s) | válido | válido |
| A / B / C | 31 / 9 / 5 | 30 / 12 / 3 |

- Acuerdo observado: 27 de 45 (Po = 0,600). Acuerdo esperado: Pe = 0,520.
- **κ de Cohen = 0,167 — leve** (Landis y Koch, 1977).
- Ninguna respuesta recibió C de los dos evaluadores.

Con ese acuerdo el instrumento **no produce una cifra reportable** de respuestas
correctas. Lo que sigue explica por qué y motiva el rediseño (`preparar_e6_v2.py`).

## Lo que no se hace con este resultado

- No se descarta la corrida de Joaquín: cumplió el criterio de validez fijado antes
  de ver los datos.
- No se modifica el umbral de 8 s.
- No se reemplaza el κ por otro coeficiente de acuerdo (AC1, PABAK) elegido después
  de ver el resultado.
- Este resultado se reporta en la tesis como la causa del rediseño, no se omite.

## Causas

La lectura que sigue es del equipo, contrastando cada respuesta con las 23 entradas de
`faq_responses`. **No es una etiqueta de referencia** ni reemplaza a los evaluadores:
sirve para entender por qué el instrumento falló. Los números de entrada siguen el
orden del Anexo D (1 a 6 son los id 1 a 6 de la base; 7 a 23 son los id 58 a 74).

### 1. Errores de atención sobre respuestas que copian una entrada (11 de 18 desacuerdos)

| id | Consulta | Máximo | Joaquín | La respuesta reproduce |
|---|---|---|---|---|
| 239 | puedo pagar en cuotas? | C | A | entrada 7 |
| 291 | hasta cuantas cuotas sin interes hay? | C | A | entrada 7 |
| 246 | tienen garantia los productos? | A | B | entrada 4 |
| 269 | hacen envios internacionales? | A | B | entrada 11 |
| 273 | es seguro pagar con tarjeta en la web? | A | B | entrada 8 |
| 277 | tienen local fisico para retirar? | B | A | entrada 18 |
| 305 | la garantia la cubre la marca o ustedes? | A | B | entradas 4 y 15 |
| 319 | si el producto no me gusta lo puedo devolver? | A | C | entrada 3 |
| 357 | se puede cancelar un pedido ya pagado? | B | C | entrada 22 |
| 365 | cuando estiman que llega el pedido a mendoza? | B | A | entrada 2 |
| 370 | cuanto tiempo de garantia tienen las notebooks? | C | B | entrada 4 |

Máximo se aparta de la entrada en 6 de estos casos; Joaquín, en 7. El error no es de un
evaluador: es de la tarea, que no obliga a localizar la entrada antes de juzgar.

### 2. Categorías que se superponen (casos frontera)

La rúbrica no dice qué nivel corresponde cuando una respuesta combina una parte que la
base respalda con una afirmación que la base no contiene. Esa respuesta cabe en A
(coincide) y en C (inventa una política). Una política genérica inventada cabe en B
(genérica) y en C (inventa). No hay regla de precedencia.

| id | Consulta | Máximo | Joaquín | Parte respaldada | Parte que la base no contiene |
|---|---|---|---|---|---|
| 298 | cambiar la direccion despues de comprar? | A | B | cancelar dentro del plazo (22) | "no es posible cambiar la dirección" |
| 309 | descuento por pago en efectivo? | C | B | cuotas (7) | "no ofrecemos descuentos por efectivo" |
| 326 | cual es el horario de atencion? | C | B | — | "lunes a viernes de 9 a 18 hs", frente a "te asiste 24/7" (5) |
| 330 | emiten factura B? | B | A | factura electrónica (6), tipo de comprobante en el checkout (20) | "factura B" no se nombra |
| 334 | los envios son con seguro? | B | C | — | "podés agregar un seguro en el checkout" |
| 359 | pedir que lo dejen con el portero? | A | B | — | "especificalo en las observaciones", "comunicate con el transportista" |
| 374 | como se calcula el costo de envio? | B | A | código postal (9) | "y el peso del paquete" |

### 3. Artefacto de doble clic

El ítem 326 figura con B en **0,1 s** para Joaquín, el mismo nivel que eligió en el ítem
anterior (273, B, 7,0 s). No es un juicio: el segundo clic cayó sobre el ítem siguiente.
Excluirlo deja κ en 0,164; la conclusión no cambia.

## El acuerdo tampoco garantiza corrección

Ambos evaluadores asignaron A a respuestas con afirmaciones que la base no contiene:

| id | Consulta | Afirmación ausente de la base |
|---|---|---|
| 312 | envio si compro mas de un producto? | "peso total", "puede que se aplique un solo costo de envío" |
| 316 | puedo retirar por sucursal? | "no contamos con opciones de retiro en sucursal"; la entrada 12 prevé el retiro en sucursal del transporte |
| 345 | envio gratis a partir de cierto monto? | "no ofrecemos envíos gratis a partir de un monto" |
| 352 | si pago con transferencia cuando despachan? | "suele tardar unas 24 horas hábiles" (la entrada 14 usa ese plazo para otra cosa) |

## Lo que el resultado sí muestra

Cuando la consulta está cubierta por una entrada, la respuesta la reproduce casi
textualmente. Cuando no lo está, el modelo completa con políticas plausibles que la
tienda no tiene, y en al menos un caso contradice la base (326). Es un hallazgo sobre
alucinación fuera de cobertura que el rediseño tiene que poder medir con acuerdo.

## Qué cambia en v2

1. Se descompone el juicio en tres preguntas verificables: qué entrada responde la
   consulta; si la respuesta afirma algo que la tabla no dice (y en qué frase); si algo
   choca con la tabla (con qué entrada y en qué frase).
2. El nivel no lo elige el evaluador: lo deriva una regla fija.
3. Las entradas se muestran numeradas y se seleccionan por número, lo que obliga a
   localizarlas y deja rastro auditable.
4. Cuatro ítems de práctica con devolución, construidos sobre temas que no aparecen
   en la muestra evaluada.
5. Se ignoran los clics que llegan en los 400 ms posteriores a mostrar un ítem.
