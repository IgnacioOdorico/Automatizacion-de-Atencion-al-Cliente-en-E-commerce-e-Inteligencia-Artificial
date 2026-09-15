# -*- coding: utf-8 -*-
"""Dictamen del 14/09, recomendada «reordenar y depurar»: movimientos entre capítulos.

  1. §2.4 (infraestructura y elección del stack) pasa a §3.4.1–3.4.3; el
     Capítulo 2 se renumera (2.5 → 2.4, 2.6 → 2.5) con sus remisiones.
  2. El diseño de las pruebas de §4.6.1 y §4.6.2 pasa a una §3.5.8 nueva; las
     Tablas 4.9 y 4.10 pasan a ser 3.4 y 3.5. §4.6 queda como entorno y evidencia.
  3. La discusión de por qué no son comparables los dos canales pasa de §4.6 a
     §5.2.2, donde se reportan.
  4. La narración del error de auditoría de §4.4.3 pasa a §3.6.4 como amenaza a
     la confiabilidad; §4.4.3 conserva la historia de versiones.
  5. §7.1 queda con recomendaciones de producción; las de medición pasan a §7.2,
     que se renombra. Protección de datos y Tiendanube pasan a §7.1, y se agrega
     la alineación de las reglas del prompt con la base.
  6. §6.1 no repite las salvedades del factor 780×.

NO es idempotente: aborta si ya existe §3.4.1.
Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402
from docx.text.paragraph import Paragraph  # noqa: E402

d = abrir()
k = Kit(d)
if k.pars('3.4.1 '):
    sys.exit('ERROR: este guion ya se aplicó.')


def entre(inicio_el, fin_el):
    """Elementos del cuerpo estrictamente entre dos elementos hermanos."""
    out, e = [], inicio_el.getnext()
    while e is not None and e is not fin_el:
        out.append(e)
        e = e.getnext()
    assert e is fin_el, 'el fin no sigue al inicio'
    return out


def mover_tras(ancla_el, elementos):
    for e in elementos:
        ancla_el.addnext(e)
        ancla_el = e
    k.hechos += 1
    return ancla_el


def tabla_tras(epigrafe):
    el = k.par(epigrafe)._p.getnext()
    assert el.tag.endswith('}tbl'), 'no hay tabla debajo de %r' % epigrafe
    return el


# ============================================================ 1. §2.4 → §3.4
h24 = k.par('2.4 Infraestructura: fundamentos conceptuales')
h25 = k.par('2.5 Estado del arte')
infra = entre(h24._p, h25._p)
intro24 = k.par('Corresponde declarar de antemano la función de esta sección')._p
assert infra[0] is intro24
infra = infra[1:]
assert sum(1 for e in infra if e.tag.endswith('}p') and ''.join(e.itertext()).strip()) == 6, 'se esperaban tres subsecciones con un párrafo cada una'
ancla = tabla_tras('Tabla 3.2: Herramientas y tecnologías utilizadas.')
mover_tras(ancla, infra)
for e in (intro24, h24._p):
    e.getparent().remove(e)
for viejo, nuevo in [('2.4.1 Contenedores Docker y reproducibilidad', '3.4.1 Contenedores Docker y reproducibilidad'),
                     ('2.4.2 PostgreSQL como base de datos de métricas', '3.4.2 PostgreSQL como base de datos de métricas'),
                     ('2.4.3 Grafana para observabilidad operativa', '3.4.3 Grafana para observabilidad operativa')]:
    k.reescribir(viejo, nuevo)
k.reemplazo('Las herramientas empleadas y la justificación de cada elección se detallan en la Tabla 3.2.',
            'Las herramientas empleadas y la justificación de cada elección se detallan en la Tabla 3.2. Las Secciones '
            '3.4.1 a 3.4.3 desarrollan los fundamentos de las tres decisiones de infraestructura que condicionan la '
            'medición: la reproducibilidad del entorno, el modelo relacional de las métricas y su observabilidad.')
for viejo, nuevo in [('2.5 Estado del arte', '2.4 Estado del arte'),
                     ('2.5.1 Chatbots en la atención al cliente', '2.4.1 Chatbots en la atención al cliente de comercio electrónico'),
                     ('2.5.2 Clasificación de intenciones', '2.4.2 Clasificación de intenciones con modelos de lenguaje'),
                     ('2.5.3 Automatización de procesos en pequeñas', '2.4.4 Automatización de procesos en pequeñas y medianas empresas'),
                     ('2.5.4 Antecedentes latinoamericanos', '2.4.5 Antecedentes latinoamericanos y del caso argentino'),
                     ('2.5.5 Vacío identificado', '2.4.6 Contribución de este trabajo'),
                     ('2.6 Tratamiento de datos personales', '2.5 Tratamiento de datos personales y marco legal aplicable')]:
    k.reescribir(viejo, nuevo)
k.reemplazo('La literatura revisada en la Sección 2.5 muestra', 'La literatura revisada en la Sección 2.4 muestra')
k.reemplazo('la revisión de antecedentes de la Sección 2.5 no identificó', 'la revisión de antecedentes de la Sección 2.4 no identificó')
k.reemplazo('la literatura revisada en la Sección 2.5.2 permite', 'la literatura revisada en la Sección 2.4.2 permite')
k.reemplazo('analizada en la Sección 2.6', 'analizada en la Sección 2.5', n=2)
lst = k.tabla(['Tabla', 'Descripción', 'Sección'])
k.celda(lst, k.fila(lst, 'Tabla 2.1'), 2, '2.4.6')

# ============================================================ 2. diseño de pruebas → §3.5.8
h36 = k.par('3.6 Amenazas a la validez')
h357 = k.par('3.5.7 Evaluación del contenido de las respuestas')
previo = h36._p.getprevious()
assert previo.tag.endswith('}p')
h358 = k.insertar_despues(Paragraph(previo, h36._parent), h357, '3.5.8 Diseño de las pruebas funcionales, de carga y de concurrencia')
h461 = k.par('4.6.1 Pruebas funcionales')
h462 = k.par('4.6.2 Pruebas de carga y de concurrencia')
correos = k.par('Los correos de confirmación y de aviso de stock insuficiente generados durante ambas corridas')
funcionales = entre(h461._p, h462._p)
carga = entre(h462._p, correos._p)
assert sum(1 for e in funcionales if e.tag.endswith('}tbl')) == 2 and 'Tabla 4.10:' in ''.join(''.join(e.itertext()) for e in funcionales)
assert sum(1 for e in carga if ''.join(e.itertext()).strip()) == 4, len(carga)
ultimo = mover_tras(h358._p, funcionales)
mover_tras(ultimo, carga)
for e in (h461._p, h462._p):
    e.getparent().remove(e)
k.reescribir('4.6 Testing', '4.6 Entorno y evidencia de las pruebas')
k.reescribir('Tabla 4.9: Pruebas funcionales del Flujo 1.', 'Tabla 3.4: Pruebas funcionales del Flujo 1.')
k.reescribir('Tabla 4.10: Pruebas funcionales del Flujo 2.', 'Tabla 3.5: Pruebas funcionales del Flujo 2.')
k.reemplazo('se ejecutaron 10 pruebas funcionales sobre los escenarios principales de ambos flujos: (ver Tabla 4.9) (ver Tabla 4.10)',
            'se diseñaron 10 pruebas funcionales sobre los escenarios principales de ambos flujos (Tablas 3.4 y 3.5); sus '
            'resultados se reportan en las Secciones 5.1.1 y 5.2.1.')
k.reemplazo('Los correos de confirmación y de aviso de stock insuficiente generados durante ambas corridas se verifican',
            'Los correos de confirmación y de aviso de stock insuficiente que genera el Flujo 1 se verifican')
k.reemplazo('que fijaba la Tabla 4.9.', 'que fijaba la Tabla 3.4.')
k.reemplazo('Su diseño se detalla en la Tabla 4.10;', 'Su diseño se detalla en la Tabla 3.5;')
k.reemplazo('con su diseño en las Tablas 4.9 y 4.10', 'con su diseño en las Tablas 3.4 y 3.5')
f49, f410, f33 = k.fila(lst, 'Tabla 4.9'), k.fila(lst, 'Tabla 4.10'), k.fila(lst, 'Tabla 3.3')
tr49, tr410, tr33 = lst.rows[f49]._tr, lst.rows[f410]._tr, lst.rows[f33]._tr
tr33.addnext(tr49)
tr49.addnext(tr410)
k.celda(lst, k.fila(lst, 'Tabla 4.9'), 2, '3.5.8')
k.celda(lst, k.fila(lst, 'Tabla 4.10'), 2, '3.5.8')
k.celda(lst, k.fila(lst, 'Tabla 4.9'), 0, 'Tabla 3.4')
k.celda(lst, k.fila(lst, 'Tabla 4.10'), 0, 'Tabla 3.5')
figs = [t for t in d.tables if [c.text.strip() for c in t.rows[0].cells] == ['Figura', 'Descripción', 'Sección']]
assert len(figs) == 2
for t in figs:
    k.celda(t, k.fila(t, 'Figura 8'), 2, '4.6')

# ============================================================ 3. no comparabilidad entre canales → §5.2.2
entorno = k.par('Las pruebas se ejecutaron sobre una notebook con procesador Intel Core i5')
corte = 'El TMR observado se ubica entre 1,47 s sobre el canal con entrega local'
texto = entorno.text
assert texto.count(corte) == 1
k.reescribir(entorno, texto[:texto.index(corte)].rstrip())
tele = k.par('El TMR global del canal Telegram fue de 3,07 s')
k.reemplazo('(1,47 s), diferencia que no se atribuye a la red porque las dos series no son apareadas (Sección 4.6), pero '
            'holgadamente', '(1,47 s), pero holgadamente')
k.insertar_despues(tele, tele,
    'La diferencia de 1,6 s entre ambos canales no acota el componente atribuible a la red, porque las dos series no son '
    'apareadas: provienen de conjuntos distintos —150 mensajes del corpus etiquetado y 45 interacciones de Telegram, '
    'adicionales y no un subconjunto— que difieren en composición de intenciones, en longitud de los mensajes, en '
    'momento de ejecución y en el prompt con que corrieron. Los tres primeros factores inciden sobre el tiempo de '
    'inferencia; el cuarto apenas, porque en el diseño factorial prompts de 1154 y de 6338 caracteres produjeron tiempos '
    'medios de 1,55 s y 1,57 s (Sección 5.2.4). La diferencia se reporta por lo tanto como observación entre dos '
    'condiciones de medición y no como descomposición del tiempo; aislar el componente de red exigiría enviar un mismo '
    'subconjunto de mensajes por ambos canales (Capítulo 7).')
k.reemplazo('y no a la composición de la muestra (Sección 4.6).', 'y no a la composición de la muestra (Sección 5.2.2).')

# ============================================================ 4. narración de la auditoría → §3.6.4
k.reescribir('La historia de versiones de este nodo se declara porque',
    'El corpus del Capítulo 5 corrió el 12 de agosto sobre el workflow de catorce nodos, con el prompt de 6338 caracteres '
    'descripto arriba: el historial de versiones del motor de flujos registra que esa versión se publicó cuatro minutos '
    'antes de la corrida, y su prompt coincide byte a byte con el del commit f68da9d del repositorio. El 25 de agosto se '
    'incorporó el workflow de dieciocho nodos, que suma el canal de Telegram, con un prompt reducido de 1032 caracteres '
    'que no inyecta la base de conocimiento ni contiene reglas ni ejemplos. Con ese prompt corrieron las 45 interacciones '
    'de Telegram de la Sección 5.2.2 y la ablación E7, y ese workflow fue el vigente hasta el 15 de septiembre, cuando el '
    'diseño factorial restituyó en él el prompt de la configuración principal. La reconstrucción, consultada sobre el '
    'historial de versiones y de publicaciones del motor de flujos, se versiona en '
    'experiments/E8/resultados/trazabilidad_versiones.txt. El error de documentación que esta historia originó se trata '
    'como amenaza a la confiabilidad en la Sección 3.6.4.')
am = k.par('Amenaza: La clasificación depende de un modelo invocado por un alias')
mi = k.par('Mitigación: El diseño factorial repite cada condición tres veces')
a = k.insertar_despues(mi, am,
    'Amenaza: Trazabilidad del artefacto medido. Una afirmación sobre cómo se obtuvo una medición puede verificarse '
    'contra una versión del artefacto distinta de la que corrió. Ocurrió en este trabajo: al documentar el prompt se '
    'auditó el workflow vigente en ese momento, de dieciocho nodos y con el prompt reducido, y se concluyó que el '
    'clasificador operaba en régimen zero-shot, cuando el corpus había corrido el 12 de agosto sobre el workflow de '
    'catorce nodos, con base de conocimiento, reglas y ejemplos (Sección 4.4.3). La auditoría fue correcta en su método y '
    'se aplicó al artefacto equivocado.')
k.insertar_despues(a, mi,
    'Mitigación: Toda afirmación sobre el artefacto medido se verifica contra la versión que corrió en la fecha de la '
    'medición, en el historial de versiones y de publicaciones del motor de flujos y en la copia del workflow que este '
    'guarda con cada ejecución. Desde el diseño factorial, cada bloque exporta además la huella del prompt con que corrió '
    'cada ejecución (Sección 3.5.6).')

# ============================================================ 5. §7.1 producción / §7.2 investigación
h72 = k.par('7.2 Líneas futuras')
inst = [k.par(x)._p for x in ('Capturar la marca de recepción en la capa HTTP', 'Homogeneizar el filtro de procedencia',
                             'Aislar el componente de red del tiempo de respuesta')]
intro72 = k.insertar_despues(h72, 'Para llevar el sistema a producción se recomienda adicionalmente:',
    'Las recomendaciones que siguen se dirigen a futuras mediciones y extensiones del trabajo, no a su puesta en '
    'producción. Las tres primeras corrigen la instrumentación de este estudio; las demás son líneas de investigación que '
    'los resultados reclaman.')
mover_tras(intro72._p, inst)
k.reescribir('7.2 Líneas futuras', '7.2 Recomendaciones para la investigación y líneas futuras')
validar = k.par('Validar la etiqueta del modelo antes de registrar la interacción')
alinear = k.insertar_despues(validar, validar,
    'Alinear las reglas del prompt con el contenido de la base de conocimiento: las reglas enumeran «horarios de atención» '
    'entre los temas de consulta frecuente, pero la base no tiene esa entrada, y ante esa consulta el modelo inventó un '
    'horario (Sección 5.2.5). Cada tema que las reglas nombran debería tener su entrada en la base, o una instrucción '
    'explícita de derivarlo al equipo; y el incumplimiento de esa instrucción de derivar debería monitorearse como un error '
    'de producción.')
datos = k.par('Cumplimiento del régimen de protección de datos personales')
tienda = k.par('Integración con Tiendanube, una de las plataformas')
k.reescribir(tienda,
    'Integrar Tiendanube en la variante de producción del Flujo 1: los workflows de producción contemplan WooCommerce, '
    'Shopify y MercadoLibre, pero no la plataforma que la Sección 1.1 menciona primero entre las que usan las PyMEs '
    'argentinas.')
mover_tras(alinear._p, [datos._p, tienda._p])

# ============================================================ 6. §6.1
k.reemplazo('bajo las condiciones del laboratorio y no como una cota: los sesgos conocidos de sus dos términos operan en '
            'direcciones opuestas.', 'bajo las condiciones del laboratorio y no como una cota.')

k.guardar()
