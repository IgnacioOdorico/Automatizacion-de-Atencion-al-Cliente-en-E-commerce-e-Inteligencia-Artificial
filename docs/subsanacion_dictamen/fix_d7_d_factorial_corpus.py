# -*- coding: utf-8 -*-
"""Dictamen del 15/09, grupo A7, y origen del corpus.

  A7. §3.5.6 define la métrica de similitud (difflib.SequenceMatcher sobre textos
      normalizados, tal como la calcula experiments/E8/analizar_e8.py) y anuncia la
      exactitud media por repetición; §5.2.4 y la Tabla 5.10 la informan con su
      intervalo (experiments/E8/media_por_repeticion_e8.py); §3.5.3 describe qué
      definiciones de categoría recibieron el anotador y el evaluador independiente
      (experiments/E2/etiquetar.html y etiquetar_externo.html).
  C.  El corpus no lo escribió el equipo: experiments/E2/README.md declara que se
      redactó con un asistente basado en un modelo de lenguaje (Claude) a partir de
      los mensajes de seed_expand.sql. Se corrige en §3.5.3, §3.6.2, §3.6.3,
      §5.4.1 (e), §6.4 y la Declaración de originalidad.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys
import copy

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit, qn  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ A7: §3.5.6
k.reemplazo(
    'y un análisis de sensibilidad que excluye los mensajes del corpus cuya similitud con algún ejemplo del prompt es igual '
    'o mayor que 0,80.',
    'y un análisis de sensibilidad que excluye los mensajes del corpus cuya similitud con algún ejemplo del prompt es igual '
    'o mayor que 0,80. La similitud es el cociente de coincidencia de secuencias de la biblioteca estándar de Python '
    '(difflib.SequenceMatcher), que vale 1 para textos idénticos y 0 para textos sin caracteres en común, calculado sobre '
    'ambos textos en minúsculas, sin tildes ni signos de puntuación. Como el sistema desplegado hace una sola llamada por '
    'mensaje, se informa además la exactitud media por repetición, que estima el desempeño de esa llamada única; ese '
    'análisis no figuraba entre los fijados de antemano y no cambia ninguna regla de decisión.')

# ------------------------------------------------------------------ A7: §5.2.4 y Tabla 5.10
k.reemplazo('La exactitud por clase y por condición se sintetiza en la Tabla 5.10.',
            'La exhaustividad por clase y la exactitud de cada condición se sintetizan en la Tabla 5.10.')
k.reemplazo(
    'son el 98,0 %, el 98,7 %, el 85,3 % y el 92,0 %, respectivamente.',
    'son el 98,0 %, el 98,7 %, el 85,3 % y el 92,0 %, respectivamente. La exactitud media por repetición, que estima el '
    'desempeño de una llamada única como la que hace el sistema desplegado, es de 93,1 % en C1 (IC 95 % [89,1 %; '
    '97,2 %]), 94,2 % en C2 ([90,5 %; 97,9 %]), 76,7 % en C3 ([70,1 %; 83,3 %]) y 73,3 % en C4 ([66,3 %; 80,4 %]). La '
    'mayoría sobrestima la llamada única en 2,0 puntos en C3, la condición menos estable, y difiere en menos de un punto '
    'en las demás. Con la media por repetición, los efectos principales son de 18,7 puntos para las reglas y los ejemplos '
    'y de 1,1 para la base, en la misma dirección, y el límite inferior de C1 también supera el 85 %. Los intervalos se '
    'calculan sobre la proporción de aciertos de cada mensaje en sus tres repeticiones, y se informa el más amplio '
    'compatible con los recuentos del análisis (experiments/E8/media_por_repeticion_e8.py).')

cap = k.par('Tabla 5.10:')
nuevo_titulo = ('Exhaustividad por clase y exactitud total por mayoría de tres repeticiones, y exactitud media por '
                'repetición, por condición del diseño factorial')
k.reescribir(cap, 'Tabla 5.10: ' + nuevo_titulo + '.')
lst = k.tabla(('Tabla', 'Descripción', 'Sección'))
k.celda(lst, k.fila(lst, 'Tabla 5.10'), 1, nuevo_titulo)

t510 = k.tabla(('Clase (mensajes)',))
filas = t510._tbl.findall(qn('w:tr'))
assert ''.join(filas[-1].itertext()).startswith('Total (150)')
nueva = copy.deepcopy(filas[-1])
filas[-1].addnext(nueva)
for tc, texto in zip(nueva.findall(qn('w:tc')),
                     ['Media por repetición · IC 95 %', '93,1 % [89,1 %; 97,2 %]', '94,2 % [90,5 %; 97,9 %]',
                      '76,7 % [70,1 %; 83,3 %]', '73,3 % [66,3 %; 80,4 %]']):
    ts = list(tc.iter(qn('w:t')))
    ts[0].text = texto
    for t in ts[1:]:
        t.text = ''
k.hechos += 1

# ------------------------------------------------------------------ A7: §3.5.3, definiciones de los anotadores
k.reemplazo(
    '(FAQ, ESTADO_PEDIDO, RECLAMO, GENERAL) sin haber ejecutado el corpus contra el modelo.',
    '(FAQ, ESTADO_PEDIDO, RECLAMO, GENERAL) sin haber ejecutado el corpus contra el modelo, a partir de una definición de '
    'una línea por categoría y sin las reglas ni los ejemplos del prompt.')
k.reemplazo(
    'El acuerdo se cuantifica con el coeficiente κ de Cohen, que descuenta el acuerdo atribuible al azar.',
    'El acuerdo se cuantifica con el coeficiente κ de Cohen, que descuenta el acuerdo atribuible al azar. El evaluador no '
    'recibió las reglas ni los ejemplos del prompt. La planilla presenta una definición de una línea por categoría —FAQ, '
    '«pregunta general sobre la tienda: envíos, pagos, garantía, horarios»; ESTADO_PEDIDO, «pregunta por una compra ya '
    'hecha (suele mencionar un nº de orden)»; RECLAMO, «queja o problema: algo llegó mal, no llegó, pide reembolso»; '
    'GENERAL, «saludo, agradecimiento o mensaje que no encaja en las otras»— y una única indicación para los casos '
    'dudosos: «Si dudás entre dos, elegí la que más pese». No incluye, en particular, la regla del prompt que desempata '
    'entre consulta frecuente y reclamo a favor del reclamo. El κ mide, por lo tanto, el acuerdo sobre esas definiciones, '
    'y no sobre las convenciones que las reglas del prompt agregan.')

# ------------------------------------------------------------------ C: origen del corpus
k.reemplazo(
    'Los 150 mensajes de prueba se redactaron incluyendo deliberadamente errores ortográficos, abreviaciones y casos de '
    'frontera semántica.',
    'Los 150 mensajes de prueba se redactaron con asistencia de un modelo de lenguaje (Claude, de Anthropic), distinto del '
    'clasificador evaluado, a partir de los mensajes que el equipo había escrito para la carga inicial de la base, '
    'ampliados con errores ortográficos, abreviaciones y casos de frontera semántica incluidos deliberadamente. Las '
    'intenciones previstas al redactarlos no se registraron en ningún archivo, de modo que no existe una clave de '
    'respuestas anterior al etiquetado, y el anotador no participó de la redacción. El origen del corpus se trata como '
    'amenaza a la validez en la Sección 3.6.2.')
k.reemplazo(
    'El mismo equipo escribió las reglas y los ejemplos del prompt y los 150 mensajes del corpus, y un corpus redactado a '
    'la medida de las reglas inflaría la exactitud.',
    'El equipo escribió las reglas y los ejemplos del prompt, y el corpus se redactó con asistencia de un modelo de '
    'lenguaje a partir de mensajes escritos por el mismo equipo (Sección 3.5.3). Un corpus redactado a la medida de las '
    'reglas inflaría la exactitud, y uno redactado por un modelo de lenguaje puede ser más regular, y más fácil de '
    'clasificar para otro modelo, que los mensajes de clientes reales.')
k.reemplazo(
    'La cronología no descarta que el equipo haya redactado el corpus con las categorías del prompt en mente, y esa parte '
    'de la amenaza queda sin mitigar.',
    'La cronología no descarta que el corpus se haya redactado con las categorías del prompt en mente, ni que su '
    'regularidad facilite la clasificación, y esas dos partes de la amenaza quedan sin mitigar.')
k.reemplazo(
    ', y el corpus, las reglas del prompt y la base de conocimiento los escribió el propio equipo: ninguno representa a '
    'una PyME real.',
    '; las reglas del prompt y la base de conocimiento las escribió el propio equipo, y el corpus se redactó con un modelo '
    'de lenguaje a partir de mensajes del equipo: ninguno representa a una PyME real.')
k.reemplazo(
    ' el conjunto de 150 mensajes cubre los escenarios más comunes',
    ' el conjunto de 150 mensajes, redactado con asistencia de un modelo de lenguaje a partir de mensajes escritos por el '
    'equipo (Sección 3.5.3), cubre los escenarios más comunes')
k.reemplazo('construido por el propio equipo,',
            'redactado con asistencia de un modelo de lenguaje a partir de mensajes del propio equipo,')
k.reemplazo('escritos por el mismo equipo que construyó el corpus', 'escritos por el mismo equipo que preparó el corpus')
k.reemplazo(
    'Su empleo se limitó a tareas de asistencia:',
    'Se las empleó además para redactar los mensajes del corpus de evaluación del clasificador, a partir de mensajes '
    'escritos por el equipo, según se declara en la Sección 3.5.3. Fuera de ese uso, su empleo se limitó a tareas de '
    'asistencia:')

k.guardar()
