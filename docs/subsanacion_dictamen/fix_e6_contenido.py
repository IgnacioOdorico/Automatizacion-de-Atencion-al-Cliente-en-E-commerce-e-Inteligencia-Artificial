# -*- coding: utf-8 -*-
"""E6 en la tesis: evaluación del contenido de las respuestas FAQ.

Hace cuatro cosas, en este orden:

  1. Corrige un defecto propio de la ablación E7: la Tabla 5.10 había quedado
     después de los cinco párrafos que la comentan y no debajo de su epígrafe.
  2. Corrige afirmaciones que E7 dejó falsas y que sobrevivieron en cuatro
     lugares (3.2, 5.2.2, 6.4 y Anexo D: "el contexto no llega al prompt") y la
     negación, en 4.4.3, de las reglas de decisión que el prompt medido sí tiene.
  3. Incorpora E6: protocolo (3.5.7), resultados (5.2.5), limitación (5.4.1),
     conclusiones (6.3, 6.4), línea futura (7.2), Anexo K con la Tabla K.1,
     su entrada en el listado de tablas, y resumen y abstract.
  4. Actualiza las menciones de "el contenido no se midió" (2.5, 5.2.1).

NO es idempotente: se niega a correr si la Sección 5.2.5 ya existe.
Se ejecuta desde la raíz del repositorio.
"""
import sys
import os
import io
import csv
import copy

sys.path.insert(0, 'docs/subsanacion_dictamen')
from docxkit import replace_in_paragraph, replace_everywhere, set_cell  # noqa: E402
from docx import Document  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.text.paragraph import Paragraph  # noqa: E402

if any(f.startswith('~$') for f in os.listdir('docs')):
    sys.exit('ERROR: Word tiene abierto un documento en docs/. Cerralo primero.')

RUTA = 'docs/TESIS_FINAL_UTN_v6.docx'
d = Document(RUTA)
if any(p.text.strip().startswith('5.2.5 Contenido de las respuestas') for p in d.paragraphs):
    sys.exit('ERROR: la Sección 5.2.5 ya existe. Este guion ya se aplicó; no se vuelve a correr.')


# ------------------------------------------------------------------ utilidades
def pars(pref):
    return [p for p in d.paragraphs if p.text.strip().startswith(pref)]


def par(pref):
    encontrados = pars(pref)
    assert len(encontrados) == 1, 'se esperaba 1 párrafo con %r, hay %d' % (pref, len(encontrados))
    return encontrados[0]


def reescribir(pref, texto):
    p = par(pref)
    assert 'blip' not in p._p.xml and 'w:drawing' not in p._p.xml, 'lleva imagen: %r' % pref
    p.runs[0].text = texto
    for r in p.runs[1:]:
        r.text = ''
    return p


def reemplazo_unico(old, new):
    n = replace_everywhere(d, old, new)
    assert n == 1, 'se esperaba 1 reemplazo de %r, hubo %d' % (old[:60], n)


def nuevo_parrafo(modelo, textos, ancla_el):
    """Párrafo nuevo con el pPr del modelo, insertado tras `ancla_el`.

    `textos` es una lista de (texto, run_modelo_o_None): cada run toma el rPr
    del run modelo, si lo hay. No copia marcadores ni otros hijos del modelo.
    """
    el = OxmlElement('w:p')
    if modelo._p.pPr is not None:
        pPr = copy.deepcopy(modelo._p.pPr)
        for s in pPr.findall(qn('w:sectPr')):
            pPr.remove(s)
        el.append(pPr)
    for texto, run_modelo in textos:
        r = OxmlElement('w:r')
        if run_modelo is not None and run_modelo._r.rPr is not None:
            r.append(copy.deepcopy(run_modelo._r.rPr))
        t = OxmlElement('w:t')
        t.set(qn('xml:space'), 'preserve')
        t.text = texto
        r.append(t)
        el.append(r)
    ancla_el.addnext(el)
    return Paragraph(el, modelo._parent)


def insertar(ancla_el, bloque):
    """bloque: lista de (modelo, texto). Devuelve el último párrafo creado."""
    p = None
    for modelo, texto in bloque:
        p = nuevo_parrafo(modelo, [(texto, modelo.runs[0] if modelo.runs else None)], ancla_el)
        ancla_el = p._p
    return p


H3 = par('3.5.6 Ablación del contexto de la base de conocimiento')
H2 = par('Anexo J: Corpus de evaluación')
PRIMERO = par('El prompt de la configuración principal combina tres elementos')
CUERPO = par('Diseño. Se pasa el mismo corpus de 150 mensajes')
EPIGRAFE = par('Tabla 5.10: Exactitud de clasificación por clase')
for m in (H3, H2, PRIMERO, CUERPO, EPIGRAFE):
    assert m.runs and m.runs[0]._r.rPr is None or m in (H3, H2), 'modelo con formato inesperado'

print('=' * 78)
print(' 1. La Tabla 5.10 vuelve debajo de su epígrafe')
print('=' * 78)
t510 = [t for t in d.tables if t.rows[0].cells[0].text.strip() == 'Clase'
        and 'Con base de conocimiento y ejemplos' in t.rows[0].cells[2].text]
assert len(t510) == 1
t510[0]._tbl.getparent().remove(t510[0]._tbl)
EPIGRAFE._p.addnext(t510[0]._tbl)
print('  movida')

print()
print('=' * 78)
print(' 2. Afirmaciones que E7 dejó falsas')
print('=' * 78)
reescribir('El diseño de medición es cuantitativo',
    'El diseño de medición es cuantitativo: MTTD, MTTR y TMR sobre marcas temporales registradas '
    'automáticamente, y exactitud de clasificación contra un conjunto de etiquetas de referencia. '
    'Corresponde declarar con precisión qué se evaluó y qué no, porque el alcance de lo medido '
    'condiciona la lectura de todo el Capítulo 5. La corrección del contenido de las respuestas que '
    'el chatbot entrega al cliente se abordó por dos vías, según el protocolo de la Sección 3.5.7, y '
    'ninguna de las dos permite afirmar que las respuestas sean correctas. La evaluación por jueces no '
    'alcanzó un acuerdo entre evaluadores suficiente para reportar una proporción de respuestas '
    'correctas. La verificación automática alcanza solo a los datos concretos —plazos, cantidades, '
    'porcentajes y franjas horarias—, y su resultado es una cota inferior de lo que las respuestas '
    'agregan a la política de la tienda. En consecuencia, el trabajo puede afirmar que el sistema '
    'clasifica la intención con determinada exactitud y que responde en determinado tiempo, pero no '
    'puede afirmar que la respuesta entregada sea correcta. La consecuencia se declara en las '
    'Secciones 5.2.2 y 6.4, y la evaluación del contenido con un instrumento que produzca un juicio '
    'reproducible queda planteada como línea futura en el Capítulo 7.')
print('  §3.2 reescrito')

reescribir('El nodo de GPT-4o-mini recibe un prompt de sistema',
    'El nodo de GPT-4o-mini recibe un prompt de sistema que define la identidad del asistente, la '
    'tarea de clasificación, las cuatro categorías de intención admitidas —enumeradas dentro del '
    'esquema de salida como FAQ, ESTADO_PEDIDO, RECLAMO y GENERAL— y el formato estricto de la '
    'respuesta: un objeto JSON con los campos intent, order_id, urgente y respuesta. Este trabajo '
    'midió dos versiones de ese prompt, que comparten esos elementos y difieren en lo que agregan. La '
    'de la configuración principal incorpora además reglas de decisión por categoría —entre ellas, '
    'cuándo un mensaje debe marcarse como urgente—, la base de conocimiento de la tienda y ejemplos '
    'etiquetados. La de la condición de ablación no incorpora ninguna de esas tres cosas, y en ella el '
    'modelo resuelve la categoría y la urgencia a partir del significado de las etiquetas. Ambos '
    'textos se transcriben en el Anexo H, de modo que los resultados de clasificación del Capítulo 5 '
    'sean auditables.')
print('  §4.4.3 primer párrafo reescrito')

reemplazo_unico(
    'La corrección del contenido entregado al cliente no fue evaluada en este trabajo, y la omisión es '
    'material en las consultas de tipo FAQ: como se documenta en la Sección 4.4.3, el contexto de la '
    'base de conocimiento no llega al prompt, de modo que esas respuestas provienen del conocimiento '
    'general del modelo y no de las políticas efectivamente vigentes en el comercio.',
    'La corrección del contenido entregado al cliente no quedó establecida en este trabajo, y la '
    'reserva es material en las consultas de tipo FAQ: aunque la base de conocimiento de la tienda se '
    'inyecta en el prompt (Sección 4.4.3), la Sección 5.2.5 muestra que el modelo afirma en algunas '
    'respuestas datos que esa base no contiene.')
print('  §5.2.2 corregido')

reemplazo_unico(
    '(v) no se evaluó la corrección del contenido de las respuestas entregadas al cliente, omisión que '
    'resulta material en las consultas de tipo FAQ porque el contexto de la base de conocimiento no '
    'llega al prompt;',
    '(v) no quedó establecida la corrección del contenido de las respuestas entregadas al cliente: la '
    'evaluación por jueces no alcanzó un acuerdo suficiente, y la verificación automática, que solo '
    'alcanza a los datos concretos, encontró que 2 de las 18 respuestas de tipo FAQ con datos concretos '
    'afirman alguno que la base de conocimiento no contiene, aun con esa base inyectada en el prompt;')
print('  §6.4 (v) corregido')

reemplazo_unico(
    'Conviene recordar, para leer este anexo en su justo alcance, lo establecido en la Sección 4.4.3: '
    'este contenido está cargado en la base y el flujo lo recupera, pero no llega al prompt del modelo, '
    'de modo que no intervino en las respuestas medidas en el Capítulo 5.',
    'Conviene recordar, para leer este anexo en su justo alcance, lo establecido en la Sección 4.4.3: '
    'en la configuración principal este contenido se inyecta en el prompt del modelo, de modo que '
    'intervino en las clasificaciones y en las respuestas medidas en el Capítulo 5. Es también la '
    'referencia contra la que se verifican los datos concretos de las respuestas en la Sección 5.2.5.')
print('  Anexo D corregido')

print()
print('=' * 78)
print(' 3. Menciones de "el contenido no se midió"')
print('=' * 78)
reemplazo_unico('que es precisamente la dimensión que este trabajo no midió.',
                'que es precisamente la dimensión que este trabajo solo alcanzó a medir de forma parcial '
                '(Sección 5.2.5).')
reemplazo_unico('lo segundo no se midió en este trabajo, según se declara en la Sección 3.2.',
                'lo segundo se aborda, con los alcances que allí se precisan, en la Sección 5.2.5.')
reemplazo_unico('es exactamente allí donde se ubica el riesgo declarado en la Sección 5.2.2 sobre el '
                'contenido de las respuestas de tipo FAQ.',
                'es exactamente allí donde se ubica el riesgo declarado en la Sección 5.2.2 sobre el '
                'contenido de las respuestas de tipo FAQ, que la Sección 5.2.5 dimensiona solo en parte.')
print('  §2.5, §5.2.1 y §6.3 actualizados')

reescribir('Evaluación de la corrección del contenido de las respuestas',
    'Evaluación de la corrección del contenido de las respuestas con un instrumento que produzca un '
    'juicio reproducible. La rúbrica de tres niveles aplicada en la Sección 5.2.5 no lo logró, porque '
    'sus niveles se superponen: una misma respuesta puede reproducir una entrada de la base y agregarle '
    'un dato que la base no contiene. Se propone reemplazar la elección directa de un nivel por tres '
    'preguntas verificables sobre cada respuesta —qué entrada de la base responde la consulta, si la '
    'respuesta afirma algo que la base no dice y si algo de lo que afirma la contradice—, exigir que '
    'cada respuesta afirmativa señale la frase y la entrada involucradas, y derivar el nivel mediante '
    'una regla fija en la que la contradicción prevalece sobre el agregado y el agregado sobre la '
    'coincidencia. El registro de la entrada citada permite, además, auditar cada juicio. Aplicado a '
    'las respuestas de las dos condiciones de la Sección 5.2.4, ese instrumento permitiría establecer '
    'si el contexto mejora también la corrección de lo que el cliente recibe, y no solo la '
    'clasificación de lo que pregunta.')
print('  §7.2 línea futura reescrita')

print()
print('=' * 78)
print(' 4. §3.5.7 — protocolo')
print('=' * 78)
h36 = par('3.6 Amenazas a la validez')
ancla = h36._p.getprevious()
assert ''.join(x.text or '' for x in ancla.iter(qn('w:t'))).startswith('Aislamiento de las poblaciones.')
insertar(ancla, [
    (H3, '3.5.7 Evaluación del contenido de las respuestas'),
    (PRIMERO,
     'Las métricas de las secciones anteriores establecen que el sistema clasifica la intención y '
     'responde en tiempo, pero no que lo que responde sea correcto. Para acotar esa dimensión se '
     'tomaron las 45 respuestas que el sistema entregó a los mensajes clasificados como FAQ en la '
     'corrida del corpus, generadas con la configuración principal y, por lo tanto, con la base de '
     'conocimiento inyectada en el prompt (Sección 4.4.3). La pregunta no es entonces si el modelo '
     'conoce la política de la tienda, sino si se atiene a la base que recibe. Se aplicaron dos '
     'procedimientos.'),
    (CUERPO,
     'Evaluación por jueces. Dos evaluadores ajenos al equipo juzgaron cada respuesta contra las '
     'veintitrés entradas de la base de conocimiento transcriptas en el Anexo D, sobre una rúbrica de '
     'tres niveles: consistente con la política de la tienda, genérica pero no contradictoria, y '
     'contradictoria con la política vigente. Cada evaluador trabajó con su propio instrumento, con la '
     'muestra en un orden aleatorio distinto, y el instrumento registró el tiempo empleado en cada '
     'respuesta. Se aplicó el mismo control de validez que al etiquetado de intenciones (Sección '
     '3.5.3): una corrida cuya mediana sea inferior a 8 segundos por respuesta se declara inválida y no '
     'entra en ningún cálculo, porque las respuestas promedian 235 caracteres y deben cotejarse contra '
     'la base. Sobre las corridas válidas se calcula el κ de Cohen para cada par de evaluadores '
     'distintos y, cuando un mismo evaluador tiene dos corridas válidas, su acuerdo consigo mismo.'),
    (CUERPO,
     'Verificación automática de datos concretos. Un guion extrae de cada respuesta los datos '
     'concretos, definidos como una cifra o un rango de cifras seguido de una unidad —días, días '
     'hábiles, horas, horas hábiles, meses, semanas, años, cuotas, minutos o porcentaje—, y comprueba si '
     'cada uno figura en alguna de las veintitrés entradas de la base con la misma unidad y las mismas '
     'cifras. Un dato que no figura en la base pero cuyas cifras ya estaban en el mensaje del cliente se '
     'clasifica aparte, porque repetirlo no es afirmar nada sobre la tienda. El procedimiento no requiere '
     'juicio y es reproducible, pero tiene dos límites que se declaran: no alcanza a las afirmaciones que '
     'no llevan cifra, como la mención de un servicio que la tienda no presta, y no controla el contexto '
     'en que se usa un dato que sí figura en la base. Su resultado es, por eso, una cota inferior de lo '
     'que las respuestas agregan a la política. La regla se fijó con conocimiento del corpus; se publica '
     'junto con el guion para que pueda auditarse.'),
])
print('  insertada (encabezado + 3 párrafos)')

print()
print('=' * 78)
print(' 5. §5.2.5 — resultados')
print('=' * 78)
ancla = par('Los datos crudos de esta corrida')._p
sig = ancla.getnext()
assert ''.join(x.text or '' for x in sig.iter(qn('w:t'))).startswith('5.3 Contrastación de hipótesis'), \
    'lo que sigue a §5.2.4 no es el encabezado de 5.3'
insertar(ancla, [
    (H3, '5.2.5 Contenido de las respuestas de tipo FAQ'),
    (PRIMERO,
     'El contenido de las 45 respuestas clasificadas como FAQ se evaluó por las dos vías que describe la '
     'Sección 3.5.7. La primera no produjo un resultado que pueda reportarse como proporción de '
     'respuestas correctas, y se informa igualmente, junto con la razón.'),
    (CUERPO,
     'Evaluación por jueces. Se completaron seis corridas: dos de un evaluador y cuatro del otro. Tres '
     'superaron el control de tiempos; las otras tres, todas del mismo evaluador, registraron medianas de '
     '4,0, 5,0 y 6,3 segundos por respuesta y se excluyeron. Las corridas válidas permiten dos '
     'comparaciones entre evaluadores distintos. En la primera coincidieron en 27 de las 45 respuestas '
     '(Po = 0,600; Pe = 0,520; κ = 0,167) y en la segunda en 31 (Po = 0,689; Pe = 0,516; κ = 0,358), '
     'valores que en la escala de Landis y Koch (1977) corresponden a un acuerdo leve y a uno aceptable, '
     'ambos por debajo del umbral de acuerdo moderado (0,41). El evaluador con dos corridas válidas '
     'repitió su propio juicio en 30 de las 45 respuestas (κ = 0,318).'),
    (CUERPO,
     'Que un mismo evaluador cambie de nivel en una de cada tres respuestas indica que la dispersión no '
     'se explica solo por diferencias de criterio entre personas: la rúbrica, tal como está formulada, '
     'no produce un juicio reproducible. La causa es estructural, porque sus tres niveles no son '
     'mutuamente excluyentes. Una respuesta que reproduce una entrada de la base y le agrega un dato que '
     'la base no contiene cabe a la vez en el primer nivel, porque coincide con la política, y en el '
     'tercero, porque afirma algo que la tienda no sostiene; una política genérica que la tienda no tiene '
     'cabe a la vez en el segundo y en el tercero. La rúbrica no establece cuál prevalece. Con ese '
     'acuerdo no se reporta ninguna proporción de respuestas correctas, y la corrección del instrumento '
     'se plantea en el Capítulo 7.'),
    (CUERPO,
     'Verificación automática. De las 45 respuestas, 18 afirman al menos un dato concreto, y entre todas '
     'suman 21. De esos datos, 18 figuran en la base de conocimiento, 1 repite una cifra que el propio '
     'cliente había escrito y 2 no figuran en ninguna entrada. Los dos pertenecen a respuestas distintas, '
     'de modo que 2 de las 18 respuestas con datos concretos —el 11,1 %, con un intervalo de confianza '
     'de Wilson al 95 % de 3,1 % a 32,8 %— afirman al menos uno que la base no respalda. Son un horario '
     'de atención «de lunes a viernes de 9 a 18 hs», cuando la base no fija horario alguno y, sobre la '
     'atención, solo indica que el asistente virtual asiste las veinticuatro horas; y un plazo de '
     'reintegro de las devoluciones «entre 5 y 10 días hábiles», tema sobre el que la base no dice '
     'nada. El detalle, dato por dato, se transcribe en la Tabla K.1 del Anexo K.'),
    (CUERPO,
     'Los dos casos responden consultas sobre temas que la base no trata: el horario de atención y el '
     'plazo de reintegro. La inyección del contexto no impide, entonces, que el modelo complete con datos '
     'plausibles cuando la consulta cae fuera de lo que la base contempla; es la alucinación que la '
     'Sección 5.4.1 (a) enuncia como riesgo general, observada aquí sobre respuestas efectivamente '
     'entregadas por el sistema. La cifra debe leerse como una cota inferior, por los dos límites que '
     'declara la Sección 3.5.7. El segundo tiene un ejemplo en la propia muestra: una respuesta atribuye '
     'a la confirmación de un pago por transferencia un plazo de 24 horas hábiles que la base contiene, '
     'pero referido al retiro de un producto en devolución, y la verificación lo cuenta como respaldado '
     'porque no controla el contexto en que se usa el dato.'),
    (CUERPO,
     'Las seis corridas de los evaluadores, incluidas las invalidadas por tiempo, el guion de '
     'verificación con sus pruebas y la salida de ambos análisis se versionan en el repositorio bajo '
     'experiments/E6.'),
])
print('  insertada (encabezado + 6 párrafos)')

print()
print('=' * 78)
print(' 6. §5.4.1 (a-ter) — limitación')
print('=' * 78)
abis = par('(a-bis) Desempeño por subcategoría')
nuevo_parrafo(abis, [
    ('(a-ter) Corrección del contenido de las respuestas:', abis.runs[0]),
    (' el trabajo no establece qué proporción de las respuestas entregadas es correcta. La evaluación por '
     'jueces no alcanzó un acuerdo suficiente (κ entre 0,167 y 0,358) y la verificación automática solo '
     'alcanza a los datos concretos, sobre los cuales encontró 2 de 18 respuestas con algún dato ausente '
     'de la base de conocimiento (Sección 5.2.5). El primer resultado es un límite del instrumento de '
     'juicio y no del sistema; el segundo es una cota inferior de lo que las respuestas agregan a la '
     'política de la tienda.', abis.runs[1] if len(abis.runs) > 1 else None),
], abis._p)
print('  insertada')

print()
print('=' * 78)
print(' 7. Anexo K y Tabla K.1')
print('=' * 78)
ultimo = d.paragraphs[-1]
assert ultimo.text.strip().startswith('El coeficiente κ de Cohen reportado en la Sección 5.2.3')
assert ultimo._p.getnext().tag == qn('w:sectPr')

with io.open('experiments/E6/resultados/verificacion_datos.csv', encoding='utf-8') as f:
    datos = list(csv.DictReader(f))
assert len(datos) == 21, 'se esperaban 21 datos, hay %d' % len(datos)
RESULTADO = {'respaldado': 'Respaldado', 'eco': 'Repite una cifra del cliente',
             'no respaldado': 'No figura en la base'}

epigrafe_k = insertar(ultimo._p, [
    (H2, 'Anexo K: Verificación de datos concretos en las respuestas de tipo FAQ'),
    (PRIMERO,
     'Se transcriben todos los datos concretos que el guion de verificación extrajo de las 45 respuestas '
     'de tipo FAQ, según la regla de la Sección 3.5.7, con el resultado de su contraste contra la base de '
     'conocimiento del Anexo D. Las 27 respuestas que no figuran en la tabla no contienen ningún dato '
     'concreto. La columna de la derecha indica la pregunta de la base en la que figura el dato; cuando '
     'figura en más de una, se consignan todas.'),
    (EPIGRAFE, 'Tabla K.1: Datos concretos afirmados en las respuestas de tipo FAQ y su presencia en la '
               'base de conocimiento.'),
])

modelo_i1 = None
hijos = list(d.element.body.iterchildren())
for i, el in enumerate(hijos):
    if el.tag == qn('w:p') and ''.join(x.text or '' for x in el.iter(qn('w:t'))).startswith('Tabla I.1'):
        modelo_i1 = next(t for t in d.tables if t._tbl is hijos[i + 1])
assert modelo_i1 is not None

CABECERA = ('Interacción', 'Consulta del cliente', 'Dato afirmado', 'Resultado',
            'Entrada de la base que lo contiene')
tk = d.add_table(rows=1 + len(datos), cols=len(CABECERA))
tk.style = modelo_i1.style
for c, val in enumerate(CABECERA):
    set_cell(tk, 0, c, val)
    for r in tk.rows[0].cells[c].paragraphs[0].runs:
        r.bold = True
for f, x in enumerate(datos, 1):
    fila = (x['id'], x['consulta'], x['dato'].rstrip('.'), RESULTADO[x['estado']],
            x['pregunta_entrada'] or '—')
    for c, val in enumerate(fila):
        set_cell(tk, f, c, val)
trPr = tk.rows[0]._tr.get_or_add_trPr()
if trPr.find(qn('w:tblHeader')) is None:
    trPr.append(OxmlElement('w:tblHeader'))
# anchos: con columnas iguales «Interacción» y «Respaldado» se partían a mitad de palabra
sec = d.sections[-1]
ancho = sec.page_width - sec.left_margin - sec.right_margin
PROPORCIONES = [0.17, 0.23, 0.15, 0.19, 0.26]
tk.autofit = False
for fila_t in tk.rows:
    for celda, prop in zip(fila_t.cells, PROPORCIONES):
        celda.width = int(ancho * prop)
for gc, prop in zip(tk._tbl.tblGrid.findall(qn('w:gridCol')), PROPORCIONES):
    gc.set(qn('w:w'), str(int(ancho * prop / 635)))
tk._tbl.getparent().remove(tk._tbl)
epigrafe_k._p.addnext(tk._tbl)

insertar(tk._tbl, [
    (CUERPO,
     'La verificación no controla el contexto en que se usa un dato. El plazo de 24 horas hábiles de la '
     'interacción 352, por ejemplo, figura en la base referido al retiro de un producto en devolución, y '
     'la respuesta lo aplica a la confirmación de un pago por transferencia; la tabla lo consigna como '
     'respaldado porque la regla solo comprueba la presencia del dato. El guion, sus pruebas y el archivo '
     'con este detalle se encuentran en el repositorio bajo experiments/E6.'),
])
print('  Anexo K con la Tabla K.1 (%d filas de datos)' % len(datos))

listado = [t for t in d.tables if t.rows[0].cells[0].text.strip() == 'Tabla'
           and t.rows[0].cells[2].text.strip() == 'Sección']
assert len(listado) == 1
lt = listado[0]
j = [i for i, r in enumerate(lt.rows) if r.cells[0].text.strip() == 'Tabla I.2']
assert len(j) == 1
tr = copy.deepcopy(lt.rows[j[0]]._tr)
lt.rows[j[0]]._tr.addnext(tr)
k = j[0] + 1
set_cell(lt, k, 0, 'Tabla K.1')
set_cell(lt, k, 1, 'Datos concretos afirmados en las respuestas de tipo FAQ y su presencia en la base de conocimiento')
set_cell(lt, k, 2, 'Anexo K')
print('  Tabla K.1 agregada al listado')

print()
print('=' * 78)
print(' 8. Resumen y abstract')
print('=' * 78)
res = par('Los resultados obtenidos muestran un MTTD promedio')
n = replace_in_paragraph(res, 'respecto del proceso manual de referencia.',
    'respecto del proceso manual de referencia. La corrección del contenido de las respuestas no quedó '
    'establecida: dos evaluadores independientes no alcanzaron un acuerdo suficiente sobre una rúbrica '
    'de tres niveles (κ de 0,167 y 0,358), y una verificación automática de los datos concretos encontró '
    'que 2 de las 18 respuestas de tipo FAQ que los contienen afirman alguno ausente de la base de '
    'conocimiento.')
assert n == 1
abs_ = par('The results show a mean MTTD')
n = replace_in_paragraph(abs_, 'with respect to the manual reference process.',
    'with respect to the manual reference process. The correctness of the replies’ content was not '
    'established: two independent raters did not reach sufficient agreement on a three-level rubric '
    '(κ of 0.167 and 0.358), and an automatic check of concrete data found that 2 of the 18 FAQ replies '
    'containing such data state at least one that is absent from the knowledge base.')
assert n == 1
print('  resumen y abstract actualizados')

d.save(RUTA)
print()
print('guardado.')
