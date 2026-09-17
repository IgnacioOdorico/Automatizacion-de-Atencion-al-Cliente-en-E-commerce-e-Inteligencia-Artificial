# PF — Evidencia de las pruebas funcionales de rechazo (PF-04 y PF-05)

Responde a la recomendación del dictamen del 14/09/2026 sobre las pruebas funcionales:
la tesis reportaba PF-04 y PF-05 como aprobadas, sin evidencia versionada y sin describir
el mecanismo del rechazo.

## Qué se hizo

Se re-ejecutaron el 15/09/2026 contra el Flujo 1 activo (15 nodos, con la rama de alerta).

| Prueba | Entrada | Resultado esperado (Tabla 4.9) |
|---|---|---|
| PF-04 | SKU inexistente (`PROD-999`) | Rechazo con error controlado |
| PF-05 | `order_number` ya registrado (`ORD-DEMO-01`) | Rechazo por restricción de unicidad |

Ninguna de las dos escribe filas. El guion lo comprueba contando las órdenes antes y
después.

```
powershell -File run_pf04_pf05.ps1     # deja resultados/pf04_pf05_<fecha>.txt
```

## Qué pasó

| Prueba | HTTP | Cuerpo | Ejecución en n8n |
|---|---|---|---|
| PF-04 | 200 | vacío | `success` |
| PF-05 | 200 | vacío | `error` |

**Mecanismo de PF-04.** El `INSERT ... SELECT ... FROM products WHERE sku = ...` no
encuentra el producto y no inserta nada. `Verificar Stock` tampoco devuelve filas, y el
flujo se detiene sin llegar a un nodo de respuesta.

**Mecanismo de PF-05.** La restricción `UNIQUE` de `orders.order_number` rechaza el
`INSERT` en `Registrar Orden`.

En ningún caso se registra la orden, que es lo esperado. Pero **ninguno de los dos
rechazos le llega al emisor como error**: el webhook responde HTTP 200 sin cuerpo. Además,
en PF-04 la ejecución queda registrada como exitosa, así que nada en el sistema distingue
un SKU inválido de una orden atendida.

Es el mismo patrón que la prueba de concurrencia (E1.b): las 49 órdenes que no se
procesaron también recibieron HTTP 200 sin cuerpo.

## Límites

- La corrida original de las pruebas funcionales no dejó evidencia. Esta es una
  re-ejecución sobre el workflow vigente, no una reconstrucción de aquella.
- PF-01 a PF-03 no se re-ejecutaron: escriben órdenes con `data_source = 'measured'`, y
  eso alteraría los totales del Capítulo 5.

---

# PC-01 a PC-05 — Evidencia de las pruebas funcionales del Flujo 2

Responde a la recomendación del dictamen del 15/09/2026: las pruebas del Flujo 2 no
tenían evidencia equivalente a la del Flujo 1.

## Qué se hizo

Se ejecutaron el 17/09/2026 (03:43 UTC) contra el Flujo 2 activo (`GyT06kIZgB5Kmw4P`,
WhatsApp + Telegram, con el prompt de la configuración vigente), por el canal simulado.
Cada interacción lleva el prefijo `PC-202609170043-` en `user_id`.

```
python run_pc01_pc05.py                                   # deja resultados/pc01_pc05_<fecha>.txt
python run_pc01_pc05.py --detalle PC-202609170043-        # respuesta completa, tickets y correos
```

La Tabla 3.5 citaba el pedido `ORD-001`, que no existe en la carga inicial. PC-02 usa
`ORD-HIST-001`, de la carga inicial, con estado `delivered`.

## Qué pasó

| Prueba | Esperado | Observado | Resultado |
|---|---|---|---|
| PC-01 | FAQ + respuesta | intent FAQ; medios de pago de la base; correo entregado | APROBADA |
| PC-02 | consulta a orders + estado | intent ESTADO_PEDIDO; `order_id` asociado; el correo incluye «Estado: Entregado» | APROBADA |
| PC-03 | ticket + RECLAMO | intent RECLAMO; ticket 634, prioridad normal; el correo informa el caso | APROBADA |
| PC-04 | ticket + urgente + respuesta | intent RECLAMO; `is_urgent` verdadero; ticket 635, prioridad urgent; correo entregado | APROBADA |
| PC-05 | GENERAL + respuesta | intent **FAQ**; respuesta correcta según la base (tienda 100 % online) | NO APROBADA |

**PC-05.** El resultado esperado no se cumple. La clasificación como FAQ es coherente con
las reglas del prompt («políticas de la tienda») y con la base, que tiene una entrada
sobre retiro en local físico; se informa igual como no aprobada, porque el criterio es
el de la Tabla 3.5.

**Tickets sin vínculo.** Los tickets se crean con `interaction_id` vacío: el nodo Crear
Ticket corre antes de Registrar Interacción y no completa la clave foránea. La relación
existe en el esquema, pero el flujo no la ejercita.

## Una corrida descartada

A las 03:41 UTC se corrió el guion con un `user_id` sin dominio (`PC-202609170041-…`).
El canal simulado entrega la respuesta por SMTP a ese `user_id`, y las cinco ejecuciones
terminaron en error en el nodo de envío («No recipients defined»), con HTTP 200 al
emisor y sin fila en `interactions`. Fue un error del guion, corregido antes de la
corrida válida, y su salida se descartó. Dejó en la base los tickets 632 y 633, de
PC-03 y PC-04, cuyos mensajes nunca recibieron respuesta: es otra instancia de la
pérdida silenciosa que documenta la tesis.

## Erratum sobre el resumen de PC-01 a PC-05

El archivo `resultados/pc01_pc05_2026-09-17_00-43-04.txt` informa «ticket: (ninguno)» para
PC-03 y PC-04. Es un defecto de la consulta del guion, no de la corrida: buscaba los
tickets por `interaction_id`, que el flujo deja vacío. Los tickets existen y son el 634 y
el 635, como muestra el archivo de detalle de la misma corrida y como recoge la tabla de
arriba. El guion ya busca por `user_id`; el archivo de la corrida se conserva como salió.

---

# PF-06 y PC-06 — un apóstrofo en el dato del cliente (defecto D-9)

Responde al hallazgo A-03 de la auditoría de tercera instancia: los nodos de base de datos
armaban la sentencia insertando el valor recibido dentro del texto de la consulta.

## Qué se corrigió

`parametrizar_consultas.py` pasó las diez consultas de los cuatro workflows a marcadores de
posición (`$1`, `$2`, …) con la opción «Query Parameters» del nodo de PostgreSQL, que envía
los valores separados de la sentencia. Se aplicó también a los dos workflows activos en n8n.

```
python experiments/PF/parametrizar_consultas.py --repo        # los cuatro archivos del repo
python experiments/PF/parametrizar_consultas.py in.json out.json
```

De paso cierra la parte de **D-8** que había quedado abierta: la variante de producción del
Flujo 2 conservaba la consulta anterior a D-7 —la que no emite ningún ítem cuando el pedido
no existe— y ahora usa la misma que el workflow medido. Y corrige el nombre del nodo
`Registrar Notificación` de la variante de producción del Flujo 1, que una exportación había
dejado con caracteres mal codificados.

**El artefacto publicado difiere del medido en este punto y solo en este.** Las mediciones del
Capítulo 5 se hicieron sobre las consultas por interpolación; la parametrización no cambia lo
que cada consulta escribe ni lee.

## Qué verifica la prueba

```
python run_pf06_apostrofo.py      # deja resultados/pf06_<fecha>.txt
```

| | Qué hace | Resultado |
|---|---|---|
| control | ejecuta contra la base el texto que el nodo producía antes, con el nombre «Mar O'Brien, S.A.», dentro de una transacción que se revierte | **rechazada**: `syntax error` |
| PF-06 | Flujo 1, orden con ese nombre y un número de orden ya registrado | la sentencia es válida: la rechaza la restricción de unicidad, no la sintaxis. No escribe ninguna fila |
| PC-06 | Flujo 2, reclamo en inglés con dos contracciones y dos comas, de punta a punta | intent RECLAMO, ticket 638 con el texto íntegro, respuesta entregada |

PF-06 usa un número de orden duplicado a propósito: así la prueba no escribe ninguna orden y
no altera los totales del Capítulo 5, que es la misma razón por la que PF-01 a PF-03 no se
reejecutaron.

## Dos corridas descartadas

Las dos primeras corridas (15:22) informaban mal el resultado del control, porque el guion
leía el código de salida de `psql`, que no devuelve error por una sentencia fallida, y usaban
un identificador con resolución de minutos, de modo que la segunda escribió sobre el mismo
usuario que la primera. Se corrigieron las dos cosas y se volvió a correr. Dejaron en la base
las interacciones 2543 y 2544 y los tickets 636 y 637; la corrida válida es la de las 15:23,
con la interacción 2545 y el ticket 638.

## Comprobación de humo del camino completo

PF-06 ejercita solo el primer nodo del Flujo 1: la orden se rechaza por unicidad. Para
que la parametrización no rompa la demostración, `verificar_camino_completo.py` recorre
la rama con stock de punta a punta —registrar, verificar, descontar, confirmar, notificar—
y comprueba las tres marcas temporales y el correo.

```
python verificar_camino_completo.py    # deja resultados/camino_completo_<fecha>.txt
```

La orden que escribe se borra al terminar y el stock del producto se repone: una orden con
la marca de los datos medidos alteraría los totales del Capítulo 5. El guion informa los
recuentos antes y después, de modo que si algo queda en la base se ve en su salida.
