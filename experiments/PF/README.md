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
