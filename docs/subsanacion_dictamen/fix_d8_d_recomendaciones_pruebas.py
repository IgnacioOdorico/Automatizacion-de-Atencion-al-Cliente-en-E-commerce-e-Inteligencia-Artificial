# -*- coding: utf-8 -*-
"""Dictamen del 15/09, grupo B: prompt y modelo, líneas futuras, pruebas del Flujo 2 y versión.

  B6. §7.1: llevar el mensaje del cliente al rol de usuario; §7.2: fijar temperatura y
      versión fechada del modelo, y probar el formato como factor. Se retiran las
      líneas genéricas sin vínculo con los resultados (Redis, sentimiento, ERP/CRM,
      tracking).
  B7. PC-01 a PC-05 ejecutadas con evidencia el 17/09 (experiments/PF): §5.2.1,
      Tabla 3.5 (PC-02 con un pedido existente), Tabla 6.1 y §6.2.
  B8. El documento cita la etiqueta entrega-2026-09-r3.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit, qn  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ B6
k.eliminar('Implementar caché Redis')
regla3 = k.par('Eliminar la regla crítica 3 del prompt')
k.insertar_despues(
    regla3, regla3,
    'Presentar el mensaje del cliente como mensaje del usuario y no dentro del prompt de sistema: el bloque MENSAJE DEL '
    'CLIENTE lo inserta hoy entre las instrucciones (Anexo H), lo que lo expone más a la inyección de instrucciones '
    '(Sección 5.4.1) y, según la comparación con la ablación E7, podría incidir también en la clasificación (Sección '
    '5.2.4).')
k.reemplazo('Las tres primeras corrigen la instrumentación de este estudio;',
            'Las cuatro primeras corrigen la instrumentación de este estudio;')
red = k.par('Aislar el componente de red del tiempo de respuesta')
k.insertar_despues(
    red, red,
    'Fijar la temperatura y una versión fechada del modelo en las mediciones: el nodo del modelo no fija la temperatura y '
    'lo invoca por un alias que el proveedor puede asociar a otra versión (Sección 5.4.1). Fijar ambos parámetros, y '
    'registrar la versión que respondió en cada ejecución, vuelve reproducible una corrida y separa la variación del '
    'modelo de la que introduce el prompt.')
for pref in ('Análisis de sentimiento sobre los mensajes de RECLAMO', 'Integración con sistemas ERP/CRM',
             'Extensión del pipeline a envíos y logística'):
    k.eliminar(pref)
k.reemplazo(
    'y verificar la hipótesis, surgida de la comparación con la ablación E7, de que la forma de presentar el mensaje del '
    'cliente también incide en la clasificación.',
    'y probar como factor la forma de presentar el mensaje del cliente —dentro del prompt de sistema o como mensaje del '
    'usuario—, que la comparación con la ablación E7 señala como posible causa de una diferencia de doce puntos (Sección '
    '5.2.4).')

# ------------------------------------------------------------------ B7
# las Tablas 3.4 y 3.5 comparten encabezado: se toma la que contiene PC-02
t35 = [t for t in d.tables if [c.text.strip() for c in t.rows[0].cells] == ['#', 'Prueba', 'Entrada', 'Resultado esperado']
       and any(r.cells[0].text.strip() == 'PC-02' for r in t.rows)]
assert len(t35) == 1
k.celda(t35[0], k.fila(t35[0], 'PC-02'), 2, '“¿Dónde está mi pedido ORD-HIST-001?”')

k.reescribir(
    'Se ejecutaron cinco pruebas funcionales sobre el Flujo 2',
    'Se ejecutaron cinco pruebas funcionales sobre el Flujo 2, con el mismo criterio que las del Flujo 1: se verificó la '
    'respuesta entregada por el canal, el estado de la base de datos y los artefactos generados. Su diseño se detalla en '
    'la Tabla 3.5; se ejecutaron el 17 de septiembre sobre el workflow vigente, por el canal simulado, y la evidencia se '
    'versiona en experiments/PF junto con el guion. Cuatro se aprobaron. PC-01 se clasificó como FAQ y recibió los medios '
    'de pago que registra la base. PC-02 se clasificó como ESTADO_PEDIDO, quedó asociada al pedido citado y la respuesta '
    'entregada incluye su estado. PC-03 se clasificó como RECLAMO y generó un ticket de prioridad normal, y PC-04, '
    'redactada en términos de urgencia, se clasificó como RECLAMO con la marca de urgencia y generó un ticket de '
    'prioridad urgente; en los dos casos la respuesta informa el número de caso. PC-05 no se aprobó: la consulta sobre '
    'tiendas físicas se clasificó como FAQ y no como GENERAL, aunque la respuesta, que informa que la tienda es solo '
    'online, es la de la base. En los cinco casos la interacción quedó registrada con sus dos marcas temporales y la '
    'respuesta llegó al capturador de correo. La prueba dejó además un hallazgo: los tickets se crean sin el identificador '
    'de la interacción que los originó, de modo que la clave foránea que el esquema prevé entre ambas tablas queda vacía. '
    'La Tabla 3.5 cita para PC-02 un pedido de la carga inicial; su versión anterior citaba uno inexistente (Anexo L).')

t61 = k.tabla(('Obj.', 'Enunciado', 'Resultado', 'Estado'))
i_oe5 = k.fila(t61, 'OE5')
k.celda(t61, i_oe5, 2,
        '10 pruebas funcionales (5 por flujo), con su diseño en las Tablas 3.4 y 3.5, sus resultados en las Secciones '
        '5.1.1 y 5.2.1 y evidencia versionada; 1 corrida de carga secuencial de 50 órdenes y 1 prueba de concurrencia de '
        '6 rondas × 20 solicitudes casi simultáneas, con datos crudos y manifiesto de ejecución versionados. Tres pruebas '
        'no alcanzaron el resultado esperado: PF-04 no se aprobó y PF-05 se aprobó en parte, porque ambas responden HTTP '
        '200 sin cuerpo en lugar de un rechazo controlado (Sección 5.1.1), y PC-05 no se aprobó, porque la consulta sobre '
        'tiendas físicas se clasificó como FAQ y no como GENERAL (Sección 5.2.1).')
k.celda(t61, i_oe5, 3, 'CUMPLIDO EN PARTE (PF-04 y PC-05 no aprobadas; PF-05 parcial)')
k.reemplazo('de modo que PF-04 no se aprobó y PF-05 se aprobó en parte (Sección 5.1.1).',
            'de modo que PF-04 no se aprobó y PF-05 se aprobó en parte (Sección 5.1.1), y que en el Flujo 2 PC-05 no se '
            'aprobó (Sección 5.2.1).')

# ------------------------------------------------------------------ B8
k.reemplazo('entrega-2026-09-r2', 'entrega-2026-09-r3', n=2)

sett = d.settings.element
if sett.find(qn('w:updateFields')) is None:
    sett.append(sett.makeelement(qn('w:updateFields'), {qn('w:val'): 'true'}))

k.guardar()
