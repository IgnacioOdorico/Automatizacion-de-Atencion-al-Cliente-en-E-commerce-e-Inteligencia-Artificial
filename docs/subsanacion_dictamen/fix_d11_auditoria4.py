# -*- coding: utf-8 -*-
"""Auditoría de cuarta instancia (18/09): los siete hallazgos de edición e inventario.

  M-01  PF-06 y PC-06 entran al inventario de pruebas (Tablas 3.4, 3.5 y 5.1, §§5.1.1 y
        5.2.1) y el recuento pasa a doce (Tabla 3.1, §3.5.8, celda de OE5).
  M-02  la comprobación del camino completo con las consultas parametrizadas se cita en la
        §5.5 (j) y en el Anexo L.
  B-01  PF-06 (Flujo 1) y PC-06 (Flujo 2) se distinguen.
  B-03  la etiqueta citada pasa a entrega-2026-09-r6.
  B-04  el recuento de vistas es uniforme.
  B-05  la §3.5.1 describe cómo se selecciona cada corrida y la §4.3.3 distingue la vista
        que define la métrica de la consulta que produjo cada valor.

(B-02 se resuelve en la evidencia del repositorio, no en el documento.)

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import copy
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)


# ------------------------------------------------------------------ M-01: tablas
t34 = [t for t in d.tables if [c.text.strip() for c in t.rows[0].cells][:4] == ['#', 'Prueba', 'Entrada', 'Resultado esperado']]
assert len(t34) == 2, len(t34)
for t, vals in (
        (t34[0], ['PF-06', 'Apóstrofo en el dato del cliente',
                  'POST con customer_name «Mar O\'Brien, S.A.» y un order_number ya registrado',
                  'La sentencia es válida: la orden la rechaza la restricción de unicidad, no un error de sintaxis']),
        (t34[1], ['PC-06', 'Reclamo con apóstrofos',
                  '“I haven\'t received my order yet, and it\'s been two weeks. I\'d like a refund, please.”',
                  'Ticket creado con el texto íntegro + interacción registrada + respuesta al cliente'])):
    assert t.rows[1].cells[0].text.strip() in ('PF-01', 'PC-01')
    nueva = copy.deepcopy(t.rows[-1]._tr)
    t.rows[-1]._tr.addnext(nueva)
    for j, v in enumerate(vals):
        k.celda(t, len(t.rows) - 1, j, v)
t51 = k.tabla(['Prueba', 'Escenario', 'Resultado'])
nueva = copy.deepcopy(t51.rows[-1]._tr)
t51.rows[-1]._tr.addnext(nueva)
for j, v in enumerate(['PF-06', 'Apóstrofo en el dato del cliente',
                       'APROBADA — con la consulta parametrizada la orden la rechaza la restricción de unicidad y no '
                       'la sintaxis; la sentencia anterior, con el mismo valor, falla por error de sintaxis']):
    k.celda(t51, len(t51.rows) - 1, j, v)

# ------------------------------------------------------------------ M-01: recuentos y resultados
k.reemplazo('se diseñaron 10 pruebas funcionales sobre los escenarios principales de ambos flujos (Tablas 3.4 y 3.5); '
            'sus resultados se reportan en las Secciones 5.1.1 y 5.2.1.',
            'se diseñaron 12 pruebas funcionales sobre ambos flujos (Tablas 3.4 y 3.5); sus resultados se reportan en '
            'las Secciones 5.1.1 y 5.2.1. Diez cubren los escenarios principales. Las dos restantes, PF-06 y PC-06, son '
            'posteriores a las mediciones: se agregaron al parametrizar las consultas (Sección 5.5 (j)) y se '
            'ejecutaron sobre el artefacto ya parametrizado, que es precisamente lo que verifican.')
t31 = k.tabla(['Etapa'])
i = k.fila(t31, '6. Testing')
k.celda(t31, i, 1, '12 pruebas funcionales, 1 corrida de carga y 1 prueba de concurrencia')
t61 = k.tabla(['Obj.', 'Enunciado', 'Resultado', 'Estado'])
i = k.fila(t61, 'OE5')
celda = t61.rows[i].cells[2].text.strip()
assert celda.startswith('10 pruebas funcionales (5 por flujo),')
k.celda(t61, i, 2, celda.replace('10 pruebas funcionales (5 por flujo),',
                                 '12 pruebas funcionales (6 por flujo, dos de ellas posteriores a las mediciones),', 1))
k.reemplazo('Versiones anteriores informaban las diez pruebas funcionales como aprobadas, sin evidencia versionada.',
            'Versiones anteriores informaban como aprobadas, sin evidencia versionada, las diez pruebas que el trabajo '
            'tenía entonces.')
k.reemplazo('Se ejecutaron cinco pruebas funcionales sobre el pipeline de procesamiento de órdenes.',
            'Se ejecutaron seis pruebas funcionales sobre el pipeline de procesamiento de órdenes.')
k.reemplazo('es el mismo patrón que la Sección 5.1.3 documenta bajo concurrencia.',
            'es el mismo patrón que la Sección 5.1.3 documenta bajo concurrencia. PF-06, posterior a las mediciones, '
            'verifica las consultas parametrizadas: una orden con un apellido que lleva apóstrofo y un número ya '
            'registrado la rechaza la restricción de unicidad, como en PF-05, y no un error de sintaxis, que es lo que '
            'le ocurre a la sentencia anterior con el mismo valor.')
k.reemplazo('Se ejecutaron cinco pruebas funcionales sobre el Flujo 2',
            'Se ejecutaron seis pruebas funcionales sobre el Flujo 2')
k.reemplazo('y la evidencia se versiona en experiments/PF junto con el guion. Cuatro se aprobaron.',
            'y la evidencia se versiona en experiments/PF junto con el guion. De las cinco primeras, cuatro se '
            'aprobaron.')
k.reemplazo('La Tabla 3.5 cita para PC-02 un pedido de la carga inicial (Anexo L).',
            'La Tabla 3.5 cita para PC-02 un pedido de la carga inicial (Anexo L). PC-06, posterior a las mediciones y '
            'ejecutada sobre el workflow ya parametrizado, envió un reclamo en inglés con dos contracciones y dos '
            'comas: se clasificó como RECLAMO con marca de urgencia, generó un ticket con el texto íntegro y el '
            'cliente recibió la respuesta. Se aprobó.')

# ------------------------------------------------------------------ M-02 y B-01
k.reemplazo('la prueba PF-06 deja constancia del comportamiento con un apóstrofo antes y después del cambio, y la '
            'recomendación correspondiente está en la Sección 7.1.',
            'las pruebas PF-06, sobre el Flujo 1, y PC-06, sobre el Flujo 2, dejan constancia del comportamiento con un '
            'apóstrofo antes y después del cambio. Una comprobación del camino completo del Flujo 1 con las consultas '
            'parametrizadas —registro, verificación y descuento del stock, confirmación y notificación, con las tres '
            'marcas temporales escritas— muestra además que el cambio no alteró el comportamiento '
            '(experiments/PF/verificar_camino_completo.py); su orden de prueba se borra al terminar y no integra los '
            'totales del Capítulo 5. La recomendación correspondiente está en la Sección 7.1.')
k.reemplazo('La prueba PF-06 deja constancia de las dos situaciones: la sentencia anterior, con un apellido que lleva '
            'apóstrofo, la rechaza PostgreSQL por un error de sintaxis; con la sentencia parametrizada el mismo valor '
            'llega como dato, y un reclamo en inglés con dos contracciones se clasifica, genera su ticket con el texto '
            'íntegro y recibe respuesta.',
            'Las pruebas PF-06 y PC-06 dejan constancia de las dos situaciones. En PF-06, sobre el Flujo 1, la '
            'sentencia anterior con un apellido que lleva apóstrofo la rechaza PostgreSQL por un error de sintaxis, y '
            'con la sentencia parametrizada el mismo valor llega como dato; en PC-06, sobre el Flujo 2, un reclamo en '
            'inglés con dos contracciones se clasifica, genera su ticket con el texto íntegro y recibe respuesta. Una '
            'comprobación posterior recorrió el camino completo del Flujo 1 con las consultas parametrizadas: la orden '
            'se registró, se confirmó, descontó el stock y escribió las tres marcas temporales, con tiempos del mismo '
            'orden que los del Capítulo 5 (experiments/PF/verificar_camino_completo.py). Su orden de prueba se borró '
            'al terminar y el stock se repuso, de modo que no integra los totales del Capítulo 5.')

# ------------------------------------------------------------------ B-03
k.reemplazo('entrega-2026-09-r5', 'entrega-2026-09-r6', n=2)

# ------------------------------------------------------------------ B-04
k.reemplazo('Las cinco vistas de métricas llevaban entonces la restricción por procedencia,',
            'Las cinco vistas del bloque de métricas operativas llevaban entonces la restricción por procedencia —la '
            'sexta, la del corpus, se creó con ella—,')
k.reemplazo('las cinco vistas de métricas restringen por data_source (Anexo A)',
            'las seis vistas de métricas restringen por data_source (Anexo A)')

# ------------------------------------------------------------------ B-05
k.reemplazo('Ambas métricas se calculan en la vista v_order_processing_time a partir de las tres marcas temporales de '
            'la tabla orders.',
            'Ambas métricas se definen en la vista v_order_processing_time a partir de las tres marcas temporales de '
            'la tabla orders. Las cifras que informa el Capítulo 5 no se leen de esa vista, sino de consultas que '
            'aplican la misma definición sobre cada corrida, seleccionada por el prefijo de su número de orden '
            '(experiments/E1/analizar_e1.sql; Sección 3.5.1).')
ancla = k.par('La recolección de datos se realizó de forma automatizada mediante el propio sistema.')
p = k.insertar_despues(
    ancla, ancla,
    'Selección de cada corrida. Las tablas reciben registros de más de un origen —la carga inicial, el baseline '
    'manual, las corridas de medición y las pruebas funcionales—, y las cifras del Capítulo 5 no se calculan sobre '
    'las vistas de los tableros sino con consultas propias que seleccionan cada corrida por su identificador. Las '
    'órdenes de la carga secuencial y de la prueba de concurrencia se seleccionan por el prefijo de su número de '
    'orden, ORD-E1A- y ORD-E1B, en el guion experiments/E1/analizar_e1.sql; las del baseline manual, por el prefijo '
    'ORD-E4- y su marca de procedencia e4_manual. Las interacciones del corpus se seleccionan por los identificadores '
    'de usuario del corpus en la corrida de las 20:45 del 12 de agosto, consolidada con sus etiquetas en '
    'experiments/E2/resultados/e2_corrida2_clasificaciones.csv, y las del diseño factorial, por el prefijo '
    'E8-<condición>-<repetición>- de su identificador de usuario. Las pruebas funcionales usan prefijos propios, de '
    'modo que ninguna corrida se superpone con otra.')
# el párrafo va después de la Tabla 3.3, no entre la introducción y su epígrafe
siguiente = k.par('3.5.2 Justificación del tamaño de muestra')
siguiente._p.addprevious(p._p)

k.guardar()
