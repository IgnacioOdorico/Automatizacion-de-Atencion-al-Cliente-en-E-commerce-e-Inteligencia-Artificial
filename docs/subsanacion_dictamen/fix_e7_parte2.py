# -*- coding: utf-8 -*-
"""E7, parte 2: protocolo, resultados, contrastacion y conclusiones.

Cifras, todas recalculadas por experiments/E7/analizar_e7.py sobre las dos
corridas y el mismo conjunto de etiquetas de referencia:

  A (con contexto + 7 ejemplos, 6338 car.)  139/150 = 92,7 %  IC [87,3 ; 95,9]
  B (ablacion zero-shot, 1032 car.)         129/150 = 86,0 %  IC [79,5 ; 90,7]
  diferencia 6,7 puntos
  McNemar apareado: b=14, c=4; chi2 de Yates 4,500 (p=0,0339); exacta p=0,0309
  por clase (aciertos sobre n):
    FAQ            48   44 (91,7 %)  ->  37 (77,1 %)   -14,6
    ESTADO_PEDIDO  35   32 (91,4 %)  ->  33 (94,3 %)    +2,9
    RECLAMO        42   38 (90,5 %)  ->  34 (81,0 %)    -9,5
    GENERAL        25   25 (100  %)  ->  25 (100  %)     0,0
"""
import sys
import os
import copy
sys.path.insert(0, 'docs/subsanacion_dictamen')
from docxkit import *
from docx import Document
from docx.oxml.ns import qn

if any(f.startswith('~$') for f in os.listdir('docs')):
    sys.exit('ERROR: Word tiene abierto un documento en docs/. Cerralo primero.')

RUTA = 'docs/TESIS_FINAL_UTN_v6.docx'
d = Document(RUTA)


def idx(pref):
    for i, p in enumerate(d.paragraphs):
        if p.text.strip().startswith(pref):
            return i
    raise KeyError(pref)


def par(pref):
    return d.paragraphs[idx(pref)]


def reescribir(pref, texto):
    p = par(pref)
    p.runs[0].text = texto
    for r in p.runs[1:]:
        r.text = ''
    return p


def estilo_de_tabla():
    for t in d.tables:
        if t.rows[0].cells[0].text.strip() == 'Clase':
            return t.style
    return d.tables[3].style


print('=' * 78)
print(' 1. Protocolo de la ablacion en el Capitulo 3')
print('=' * 78)
p355 = par('3.5.5 Medición del baseline de atención manual')
# se inserta despues del ultimo parrafo de 3.5.5
i = idx('3.5.5 Medición del baseline de atención manual')
while not d.paragraphs[i + 1].style.name.startswith('Heading'):
    i += 1
ancla = d.paragraphs[i]
bloque = [
    ('3.5.6 Ablación del contexto de la base de conocimiento', 'Heading 3'),
    ('El prompt de la configuración principal combina tres elementos que la literatura trata por '
     'separado: ejemplos etiquetados, reglas de decisión y recuperación de contexto '
     '(Sección 2.2.2). Medir el desempeño del clasificador con los tres puestos no permite '
     'atribuir el resultado a ninguno en particular, ni estimar cuánto aporta la base de '
     'conocimiento de la tienda, que es la pieza que una PyME tendría que construir y mantener. '
     'Se incorpora por eso una segunda condición de medición.', 'First Paragraph'),
    ('Diseño. Se pasa el mismo corpus de 150 mensajes por el mismo modelo, contra el mismo '
     'conjunto de etiquetas de referencia, cambiando únicamente el prompt de sistema: de los 6338 '
     'caracteres de la configuración principal a los 1032 de un prompt que enumera las cuatro '
     'categorías y fija el formato de salida, sin ejemplos, sin reglas de decisión y sin '
     'inyección de la base de conocimiento. Ambos prompts se transcriben en el Anexo H. Al no '
     'variar ni el corpus ni las etiquetas ni el modelo, la diferencia observada es atribuible al '
     'prompt y no a la muestra.', 'Body Text'),
    ('Criterio de análisis. El diseño es apareado: cada mensaje se clasifica dos veces, una por '
     'condición. El contraste que corresponde no es el de dos proporciones independientes sino la '
     'prueba de McNemar sobre los pares discordantes, esto es sobre los mensajes en los que las '
     'dos condiciones difieren. Se reporta el estadístico con corrección de continuidad de Yates '
     'y, por ser el número de discordancias reducido, también el valor p exacto de la binomial '
     'bilateral, que es el que se toma como referencia. Se acompaña del intervalo de Wilson de '
     'cada condición y del desglose por clase, porque el interés no está solo en si hay '
     'diferencia sino en dónde se concentra.', 'Body Text'),
    ('Aislamiento de las poblaciones. Las interacciones de la corrida de ablación se registran con '
     'un prefijo propio en el identificador de usuario, de modo que quedan separadas de la corrida '
     'del corpus de manera permanente y no por una ventana temporal. Ninguna cifra de la Sección '
     '5.2.3 se ve afectada. El guion de ejecución verifica, antes de enviar, que el prompt activo '
     'sea efectivamente el reducido, y aborta si detecta lo contrario; deja además un manifiesto '
     'con el nombre del workflow, su cantidad de nodos, la longitud del prompt, las marcas '
     'temporales y el commit del repositorio.', 'Body Text'),
]
for texto, est in bloque:
    ancla = insert_paragraph_after(ancla, texto, estilo=est)
print('  §3.5.6 insertada (4 parrafos)')

print()
print('=' * 78)
print(' 2. Resultados de la ablacion en el Capitulo 5')
print('=' * 78)
i = idx('5.2.3 Precisión de clasificación de intents')
while not (d.paragraphs[i + 1].style.name.startswith('Heading')
           and d.paragraphs[i + 1].text.strip().startswith('5.3')):
    i += 1
ancla = d.paragraphs[i]

bloque = [
    ('5.2.4 Ablación: cuánto aporta la base de conocimiento', 'Heading 3'),
    ('El 92,7 % de la sección anterior se obtuvo con un prompt que inyecta la base de conocimiento '
     'de la tienda y presenta siete ejemplos etiquetados. Para estimar cuánto de ese desempeño '
     'corresponde a esos dos elementos y cuánto al modelo por sí solo, se repitió la medición '
     'sobre el mismo corpus con el prompt reducido, según el protocolo de la Sección 3.5.6. El '
     'resultado se sintetiza en la Tabla 5.10.', 'First Paragraph'),
    ('Tabla 5.10: Exactitud de clasificación por clase, con y sin base de conocimiento.', 'Body Text'),
]
for texto, est in bloque:
    ancla = insert_paragraph_after(ancla, texto, estilo=est)
p_epigrafe = ancla

# --- la tabla ---
FILAS = [
    ('Clase', 'n', 'Con base de conocimiento y ejemplos', 'Sin base de conocimiento ni ejemplos', 'Diferencia'),
    ('FAQ', '48', '44 (91,7 %)', '37 (77,1 %)', '−14,6 puntos'),
    ('ESTADO_PEDIDO', '35', '32 (91,4 %)', '33 (94,3 %)', '+2,9 puntos'),
    ('RECLAMO', '42', '38 (90,5 %)', '34 (81,0 %)', '−9,5 puntos'),
    ('GENERAL', '25', '25 (100 %)', '25 (100 %)', 'sin cambio'),
    ('Total', '150', '139 (92,7 %)', '129 (86,0 %)', '−6,7 puntos'),
]
t = d.add_table(rows=len(FILAS), cols=5)
try:
    t.style = estilo_de_tabla()
except Exception:
    pass
for r, fila in enumerate(FILAS):
    for c, val in enumerate(fila):
        set_cell(t, r, c, val)
# marcar la fila 0 como encabezado repetido
trPr = t.rows[0]._tr.get_or_add_trPr()
if trPr.find(qn('w:tblHeader')) is None:
    trPr.append(trPr.makeelement(qn('w:tblHeader'), {}))
# moverla a su lugar
t._tbl.getparent().remove(t._tbl)
p_epigrafe._element.addnext(t._tbl)
print('  Tabla 5.10 creada (%d filas x %d columnas) y ubicada' % (len(FILAS), 5))

ancla = p_epigrafe
# los parrafos que siguen a la tabla
posteriores = [
    ('La exactitud global cae de 92,7 % a 86,0 %, una diferencia de 6,7 puntos porcentuales. Los '
     'intervalos de confianza de Wilson al 95 % son [87,3 %; 95,9 %] para la configuración '
     'principal y [79,5 %; 90,7 %] para la de ablación. Como el diseño es apareado, la pregunta '
     'de si esa diferencia es atribuible al azar se responde sobre los pares discordantes: de los '
     '150 mensajes, 125 se clasificaron correctamente en ambas condiciones y 7 incorrectamente en '
     'ambas; 14 solo acertaron con la base de conocimiento y 4 solo sin ella. La prueba de '
     'McNemar sobre esos 18 pares arroja un estadístico de 4,500 con corrección de Yates '
     '(p = 0,034) y un valor p exacto de la binomial bilateral de 0,031. La diferencia no es '
     'atribuible a la variación de muestreo.', 'Body Text'),
    ('El desglose por clase es más informativo que el total, y es donde está el hallazgo. La caída '
     'se concentra casi enteramente en FAQ, que pierde 14,6 puntos, y secundariamente en RECLAMO, '
     'que pierde 9,5. GENERAL se mantiene en 100 % y ESTADO_PEDIDO incluso mejora 2,9 puntos, '
     'diferencia de un solo mensaje que queda dentro de lo esperable por variación. El patrón '
     'tiene una explicación mecánica que la matriz de confusión confirma: sin la base de '
     'conocimiento, nueve de los cuarenta y ocho mensajes de tipo FAQ se clasifican como GENERAL. '
     'Son consultas del tipo «trabajan con OCA o Andreani?», «puedo retirar por sucursal?», '
     '«tienen atención telefónica?» o «aceptan transferencia bancaria?».', 'Body Text'),
    ('La interpretación es la siguiente. La categoría FAQ no se define por la forma del mensaje '
     'sino por su contenido: un mensaje es una consulta frecuente si versa sobre algo respecto de '
     'lo cual la tienda tiene una política establecida. Sin la base de conocimiento, el modelo no '
     'tiene modo de saber sobre qué tiene política esta tienda en particular, y ante la duda '
     'deriva el mensaje a la categoría residual. El contexto no mejora la clasificación por '
     'añadir información redundante: la mejora porque es lo que hace que la categoría FAQ sea '
     'decidible. Ese es, a juicio de los autores, el resultado más transferible de este trabajo, '
     'y se retoma en la Sección 6.3.', 'Body Text'),
    ('Corresponde una precisión sobre H2b, porque las dos condiciones no lo satisfacen del mismo '
     'modo. El umbral fijado es del 85 % y ambas exactitudes lo superan en su valor puntual. Pero '
     'el criterio que este trabajo adoptó en la Sección 3.5.2 no es el valor puntual sino la '
     'precisión efectivamente alcanzada, esto es el límite inferior del intervalo de confianza. '
     'Ese límite es del 87,3 % en la configuración principal, por encima del umbral, y del 79,5 % '
     'en la de ablación, por debajo. Con el criterio propio del trabajo, H2b se sostiene con base '
     'de conocimiento y no se sostiene sin ella. Se lo consigna así en la Tabla 5.11.', 'Body Text'),
    ('Los datos crudos de esta corrida —el manifiesto de ejecución con el workflow, la longitud '
     'del prompt y las marcas temporales, el registro de envíos y las clasificaciones obtenidas— '
     'se versionan en el repositorio bajo experiments/E7, junto con el guion de ejecución y el de '
     'análisis, de modo que las cifras de esta sección sean recalculables.', 'Body Text'),
]
for texto, est in posteriores:
    ancla = insert_paragraph_after(ancla, texto, estilo=est)
print('  §5.2.4 completa (5 parrafos posteriores a la tabla)')

print()
print('=' * 78)
print(' 3. Contrastacion: H2b con las dos condiciones')
print('=' * 78)
t511 = None
for t in d.tables:
    if t.rows[0].cells[0].text.strip() == 'Hipótesis':
        t511 = t
        break
f = [i for i, r in enumerate(t511.rows) if r.cells[0].text.strip().startswith('H2b')][0]
set_cell(t511, f, 2,
    '92,7 % (139/150) con base de conocimiento y ejemplos; IC 95 % de Wilson [87,3 %; 95,9 %], '
    'con el límite inferior por encima del umbral. En la condición de ablación, sin base de '
    'conocimiento ni ejemplos: 86,0 % (129/150), IC 95 % [79,5 %; 90,7 %], con el límite inferior '
    'por debajo del umbral (Sección 5.2.4).')
set_cell(t511, f, 3, 'CONFIRMADA con base de conocimiento; NO CONFIRMADA sin ella')
print('  fila H2b de la Tabla 5.11 actualizada')

n = replace_in_paragraph(par('• H2b se confirma con un accuracy global'),
    'El procedimiento de cálculo se detalla en el Anexo J.',
    'El procedimiento de cálculo se detalla en el Anexo J. Corresponde acotar el alcance de esa '
    'confirmación: vale para la configuración con base de conocimiento e ejemplos. La ablación de '
    'la Sección 5.2.4 muestra que sin esos dos elementos la exactitud baja a 86,0 % y el límite '
    'inferior de su intervalo queda por debajo del umbral, de modo que H2b no se sostendría con '
    'el criterio que el propio trabajo adoptó.')
print('  bullet de H2b en §5.3: %d' % n)

print()
print('=' * 78)
print(' 4. Discusion y conclusiones')
print('=' * 78)
reescribir('El modelo GPT-4o-mini demostró ser adecuado para la clasificación',
    'El modelo GPT-4o-mini demostró ser adecuado para la clasificación de intenciones en dominios '
    'acotados, manejando correctamente mensajes con errores ortográficos, abreviaciones y varias '
    'preguntas dentro de un mismo mensaje. El dato relevante no es el 92,7 % por sí solo sino la '
    'distancia entre las dos condiciones medidas: con la base de conocimiento de la tienda '
    'inyectada y siete ejemplos etiquetados, 92,7 %; sin ninguna de las dos cosas, 86,0 %. Los '
    '6,7 puntos de diferencia son atribuibles al prompt y no a la muestra, porque ambas '
    'condiciones corrieron sobre el mismo corpus y las mismas etiquetas (Sección 5.2.4). El '
    '86,0 % de la condición reducida funciona además como piso documentado del desempeño '
    'alcanzable sin ajuste fino, sin ejemplos y sin contexto, que es la lectura que la literatura '
    'revisada en la Sección 2.5.2 permite anticipar; y el margen que separa ambas condiciones es '
    'la medida de lo que una PyME gana por mantener su base de conocimiento en condiciones.')
print('  §5.4 reinterpretada sobre las dos condiciones')

reescribir('Sobre la efectividad de GPT-4o-mini en atención al cliente',
    'Sobre la efectividad de GPT-4o-mini en atención al cliente: el modelo alcanzó un accuracy del '
    '92,7 % en la clasificación de intenciones sin ajuste fino, con un prompt que inyecta la base '
    'de conocimiento de la tienda y presenta siete ejemplos etiquetados; y del 86,0 % con un '
    'prompt reducido que no hace ninguna de las dos cosas. El hallazgo más transferible del '
    'trabajo para una PyME no es ninguno de esos dos números sino lo que los separa, y sobre todo '
    'dónde se concentra la diferencia. Los 6,7 puntos globales se explican casi enteramente por la '
    'categoría FAQ, que pierde 14,6 puntos al quitar el contexto porque nueve de sus mensajes '
    'pasan a clasificarse como consulta general. La razón es que la categoría FAQ no se define por '
    'la forma del mensaje sino por el hecho de que la tienda tenga una política al respecto: sin '
    'la base de conocimiento el modelo no puede saber cuál es ese conjunto, y ante la duda deriva '
    'a la categoría residual. Dicho de otro modo, y esta es la conclusión práctica: lo que una '
    'PyME tiene que construir y mantener no es el prompt sino su base de preguntas frecuentes, '
    'porque es la que vuelve decidible la clasificación. El prompt se escribe una vez; la base de '
    'conocimiento es la que da el margen.')
print('  §6.3 reformulada: el hallazgo transferible es la ablacion')

print()
print('=' * 78)
print(' 5. Linea futura cumplida')
print('=' * 78)
reescribir('Incorporación de ejemplos etiquetados al prompt y cableado del contexto',
    'Evaluación de la corrección del contenido de las respuestas, que este trabajo no ejecutó '
    '(Sección 3.2). El aporte del contexto de FAQ sobre la clasificación ya está medido en la '
    'Sección 5.2.4; lo que resta medir es su efecto sobre el contenido de la respuesta entregada, '
    'que es una dimensión distinta. El procedimiento que se propone es el siguiente: extraer de la '
    'tabla interactions las respuestas efectivamente entregadas en ambas condiciones, restringir '
    'la muestra a los mensajes clasificados como FAQ, y hacerlas juzgar por dos evaluadores '
    'independientes contra las veintitrés entradas de la base de conocimiento transcriptas en el '
    'Anexo D, sobre una rúbrica de tres niveles —respuesta consistente con la política de la '
    'tienda, respuesta genérica pero no contradictoria, y respuesta que contradice la política '
    'vigente—, reportando el acuerdo entre ambos evaluadores con el mismo coeficiente κ que se '
    'empleó para el conjunto de etiquetas de referencia. Medida en las dos condiciones, esa '
    'rúbrica permitiría establecer si el contexto mejora también la corrección de lo que el '
    'cliente recibe, y no solo la clasificación de lo que pregunta.')
print('  §7.2 actualizada: la linea de la ablacion esta cumplida')

# Tabla 2.1: la fila de este trabajo
for t in d.tables:
    for i, r in enumerate(t.rows):
        if r.cells[0].text.strip() == 'Este trabajo':
            set_cell(t, i, 2, 'Orquestación con n8n y clasificación con LLM, medida con y sin '
                              'recuperación de contexto')
            set_cell(t, i, 3, 'MTTD, MTTR, TMR y exactitud en dos condiciones de prompt, contra '
                              'baseline manual medido')
            print('  fila "Este trabajo" de la Tabla 2.1 actualizada')

d.save(RUTA)
print()
print('guardado (parte 2 de 2).')
