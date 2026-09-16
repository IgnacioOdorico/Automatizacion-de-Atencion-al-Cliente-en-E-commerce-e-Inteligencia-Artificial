# -*- coding: utf-8 -*-
"""Dictamen del 15/09, grupo A: PF-04 y PF-05, OE5, y criterios fijados antes o después de medir.

  A3. PF-04 pasa a no aprobada y PF-05 a parcial (Tabla 5.1 y §5.1.1); OE5 se
      cumple en parte (Tabla 6.1 y §6.2).
  A5. La Tabla 5.11 suma la columna del momento en que se fijó cada criterio;
      §5.3, §6.1, el resumen y el abstract matizan la confirmación. Los umbrales
      de 30 s, 10 s y 85 % figuran en la versión del 27/04/2026 (commit 9dc7b44),
      anterior a las mediciones del Capítulo 5.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys
import copy

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit, qn  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ A3: Tabla 5.1 y §5.1.1
t51 = k.tabla(('Prueba', 'Escenario', 'Resultado'))
for fila_id, texto in [
    ('PF-01', 'APROBADA — orden confirmada, stock decrementado, email enviado'),
    ('PF-02', 'APROBADA — orden rechazada con status no_stock, email de aviso'),
    ('PF-03', 'APROBADA — orden confirmada + alerta registrada en stock_alerts'),
    ('PF-04', 'NO APROBADA — la orden no se registra, pero no hay rechazo con error controlado: el webhook '
              'responde HTTP 200 sin cuerpo y la ejecución termina como exitosa'),
    ('PF-05', 'PARCIAL — la restricción de unicidad rechaza la orden duplicada, como se esperaba, pero el webhook '
              'responde HTTP 200 sin cuerpo y el emisor no se entera del rechazo'),
]:
    k.celda(t51, k.fila(t51, fila_id), 2, texto)

k.reescribir(
    'Las tres primeras pruebas se aprobaron sin reservas',
    'Las tres primeras pruebas se aprobaron: el pipeline actualizó las marcas temporales en orders y las notificaciones '
    'se enviaron al destinatario esperado. De las dos pruebas de rechazo, con el criterio de la Tabla 3.4, PF-04 no se '
    'aprobó y PF-05 se aprobó en parte: en ambas la orden inválida o duplicada no se registra, pero ninguna produce el '
    'rechazo controlado que el emisor necesita para distinguirla de una orden atendida. Se re-ejecutaron el 15 de '
    'septiembre para dejar evidencia versionada, que se conserva en experiments/PF junto con el guion, y el mecanismo de '
    'cada una es distinto. En PF-04, la sentencia que registra la orden toma el producto del catálogo por su SKU; al no '
    'encontrarlo no inserta ninguna fila, el flujo se detiene sin llegar a un nodo de respuesta y la ejecución queda '
    'registrada como exitosa: el resultado esperado era un rechazo con error controlado, y no lo hay. En PF-05, la '
    'restricción de unicidad del número de orden rechaza la inserción, que es lo que la prueba esperaba, y la ejecución '
    'termina en error; lo que falta es comunicarlo. En los dos casos el webhook responde HTTP 200 con el cuerpo vacío, '
    'de modo que el emisor no puede distinguir un rechazo de una orden atendida: es el mismo patrón que la Sección 5.1.3 '
    'documenta bajo concurrencia.')

# ------------------------------------------------------------------ A3: Tabla 6.1 y §6.2
t61 = k.tabla(('Obj.', 'Enunciado', 'Resultado', 'Estado'))
i_oe5 = k.fila(t61, 'OE5')
k.celda(t61, i_oe5, 2,
        '10 pruebas funcionales (5 por flujo), con su diseño en las Tablas 3.4 y 3.5 y sus resultados en las Secciones '
        '5.1.1 y 5.2.1; 1 corrida de carga secuencial de 50 órdenes y 1 prueba de concurrencia de 6 rondas × 20 '
        'solicitudes casi simultáneas, con datos crudos y manifiesto de ejecución versionados. Dos pruebas de rechazo '
        'del Flujo 1 no alcanzaron el resultado esperado de la Tabla 3.4: PF-04 no se aprobó y PF-05 se aprobó en parte, '
        'porque ambas responden HTTP 200 sin cuerpo en lugar de un rechazo controlado (Sección 5.1.1).')
k.celda(t61, i_oe5, 3, 'CUMPLIDO EN PARTE (PF-04 no aprobada y PF-05 parcial)')

k.reescribir(
    'Los cinco objetivos específicos fueron cumplidos',
    'De los cinco objetivos específicos, OE3 y OE4 se cumplieron sin reservas, OE1 y OE2 se cumplieron con el alcance '
    'que precisan sus celdas y OE5 se cumplió solo en parte. OE3 y OE4 se formularon en términos cualitativos en la '
    'Sección 1.5.2 —las tablas, vistas de métricas e índices necesarios para instrumentar el ciclo, y los dashboards para '
    'visualizar MTTD, MTTR y TMR— y el sistema desplegado los satisface: siete tablas, seis vistas y doce índices '
    'sostienen el cálculo de las tres métricas sin cómputo externo, y trece paneles repartidos en dos tableros las '
    'visualizan a partir de consultas sobre la base, con excepción del panel de exactitud, que muestra un valor '
    'constante (Tabla 4.8). No se los contrasta contra una cifra comprometida de antemano porque los objetivos no la '
    'fijaron. OE1 se cumple en régimen secuencial: bajo concurrencia la restricción del esquema impide la sobreventa, '
    'pero el pipeline pierde sin aviso el 40,8 % de las órdenes, según se consigna en su propia celda y se analiza en la '
    'Sección 5.1.3. OE2 se cumplió sobre los dos canales efectivamente implementados y medidos, quedando el canal de '
    'correo como diseño documentado en el Capítulo 7. OE5 se cumplió solo en parte: la validación se ejecutó completa, '
    'pero mostró que el Flujo 1 no rechaza de manera controlada un producto inexistente ni un número de orden '
    'duplicado, de modo que PF-04 no se aprobó y PF-05 se aprobó en parte (Sección 5.1.1).')

# ------------------------------------------------------------------ A5: columna de la Tabla 5.11
t511 = k.tabla(('Hipótesis', 'Criterio', 'Resultado obtenido', 'Veredicto'))
tbl = t511._tbl
grid = tbl.tblGrid.findall(qn('w:gridCol'))
assert [g.get(qn('w:w')) for g in grid] == ['1915', '1741', '3483', '1915']
nuevo_grid = copy.deepcopy(grid[1])
grid[1].addnext(nuevo_grid)
for g, w in zip(tbl.tblGrid.findall(qn('w:gridCol')), ['1450', '1500', '1800', '2804', '1500']):
    g.set(qn('w:w'), w)
momento = {
    'Hipótesis': 'Momento en que se fijó el criterio',
    'H1': 'Umbral de 10×: después de medir, con el factor ya conocido. Criterio operativo de 30 s: antes de las '
          'mediciones del Capítulo 5.',
    'H2a': 'Umbral de 10 s para FAQ, estado de pedido y consultas generales: antes de las mediciones. Extensión a las '
           'cuatro categorías: después.',
    'H2b': 'Umbral del 85 %: antes de las mediciones. Regla del límite inferior: después de la corrida del corpus y '
           'antes de medir en el diseño factorial.',
}
for tr in tbl.findall(qn('w:tr')):
    tcs = tr.findall(qn('w:tc'))
    assert len(tcs) == 4
    nuevo = copy.deepcopy(tcs[1])
    tcs[1].addnext(nuevo)
    clave = ''.join(t.text or '' for t in tcs[0].iter(qn('w:t'))).split(':')[0]
    texto = momento[clave]
    runs = nuevo.findall('.//' + qn('w:r'))
    ts = [r.find(qn('w:t')) for r in runs]
    ts[0].text = texto
    for t in ts[1:]:
        if t is not None:
            t.text = ''
    for tc, w in zip(tr.findall(qn('w:tc')), ['1268', '1312', '1574', '2453', '1312']):
        tc.find(qn('w:tcPr')).find(qn('w:tcW')).set(qn('w:w'), w)
k.hechos += 1

# ------------------------------------------------------------------ A5: §5.3, §6.1, resumen y abstract
k.reescribir(
    'Las tres hipótesis se sostienen con los criterios fijados en la Sección 1.4.2, con los alcances siguientes:',
    'Las tres hipótesis se sostienen con los criterios fijados en la Sección 1.4.2, pero no todos esos criterios se '
    'fijaron antes de medir, y la Tabla 5.11 indica cuándo se fijó cada uno. Los umbrales de 30 s, 10 s y 85 % figuran '
    'en la versión del trabajo registrada el 27 de abril de 2026 en el repositorio (commit 9dc7b44), anterior a las '
    'mediciones del Capítulo 5. Se fijaron después, con el resultado conocido, el umbral de un orden de magnitud de H1, '
    'la extensión de H2a a las cuatro categorías y la regla del límite inferior de H2b en la corrida del corpus. Para '
    'esos criterios, «se sostiene» describe el resultado frente a un criterio y no constituye una confirmación. La '
    'contrastación prospectiva en sentido estricto es la réplica de H2b en el diseño factorial, cuya regla se versionó '
    'antes de medir. Con esa salvedad, los alcances son los siguientes:')

k.reemplazo(
    'H2a en los dos canales medidos, y H2b con la configuración vigente del prompt y no sin sus reglas y ejemplos.',
    'H2a en los dos canales medidos, y H2b con la configuración vigente del prompt y no sin sus reglas y ejemplos. Solo '
    'la réplica de H2b en el diseño factorial se contrastó con una regla fijada antes de medir; el umbral de un orden de '
    'magnitud de H1 y la extensión de H2a a las cuatro categorías se fijaron con el resultado conocido, y para ellas el '
    'veredicto describe el resultado frente al criterio, sin valor de confirmación.')

# El resumen gana 13 palabras y pierde 11, para quedar dentro de las 300.
k.reemplazo('Las tres hipótesis se sostienen dentro de los alcances declarados.',
            'Las tres hipótesis se sostienen dentro de los alcances declarados, aunque solo la de exactitud se replicó '
            'con una regla fijada antes de medir.')
k.reemplazo('Bajo 20 solicitudes simultáneas', 'Bajo 20 solicitudes casi simultáneas')
k.reemplazo('un pipeline de órdenes de quince nodos y un chatbot', 'un pipeline de órdenes y un chatbot')
k.reemplazo('que se lee como orden de magnitud bajo condiciones de laboratorio y no como cota',
            'leído como orden de magnitud de laboratorio y no como cota')
k.reemplazo('y no de la base de conocimiento de la tienda, que aporta 2,0.',
            'y no de la base de conocimiento, que aporta 2,0.')

k.reemplazo('The three hypotheses hold within the declared scope.',
            'The three hypotheses hold within the declared scope, although only the accuracy hypothesis was replicated '
            'under a rule fixed before measuring.')
k.reemplazo('Under 20 simultaneous requests', 'Under 20 near-simultaneous requests')

k.guardar()
