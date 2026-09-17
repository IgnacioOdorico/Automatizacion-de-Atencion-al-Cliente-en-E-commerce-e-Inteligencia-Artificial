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
