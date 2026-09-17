# -*- coding: utf-8 -*-
"""Dictamen del 15/09, grupo B: registro de revisiones en un anexo, hipótesis y objetivos.

  B1. Nuevo Anexo L («Registro de desvíos y correcciones»): formulaciones
      originales de las hipótesis, ablación E7, error de trazabilidad, cita de commit
      corregida, reclasificación de pruebas y origen del corpus. El cuerpo presenta
      el diseño final y remite al anexo (§1.4.2, §3.5.6, §3.6.4, §4.4.3, §5.2.4,
      §6.3 y Anexo H).
  B3. H1 se presenta como objetivo de estimación (Sección 2 del dictamen, obs. b);
      OE1 incorpora la comparación con el proceso manual (obs. a de la Sección 3);
      §1.2 declara que el problema de la atención fragmentada se aborda en parte
      (obs. b de la Sección 3).

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys
import copy

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit, qn, OxmlElement, Paragraph  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ B3: hipótesis
k.reescribir(
    'H1: El pipeline automatizado de procesamiento de órdenes reduce',
    'H1: El pipeline automatizado de procesamiento de órdenes reduce el tiempo que insume procesar una orden respecto '
    'del mismo procesamiento hecho de forma manual, medido como baseline propio según el protocolo de la Sección 3.5.5. '
    'Como era previsible que un proceso automatizado sobre una base local fuera más rápido que uno manual, H1 se trata '
    'como un objetivo de estimación antes que como una hipótesis que pudiera fallar: su resultado es la magnitud de la '
    'reducción, expresada como factor con su intervalo de confianza al 95 %. Como referencia descriptiva, fijada con el '
    'resultado conocido (Tabla 5.11 y Anexo L), se consigna si el límite inferior de ese intervalo alcanza un orden de '
    'magnitud, es decir 10×. Como criterio operativo secundario se fija que el tiempo end-to-end del pipeline se '
    'mantenga por debajo de 30 segundos.')
k.reescribir(
    'H2a: El chatbot basado en GPT-4o-mini',
    'H2a: El chatbot basado en GPT-4o-mini responde al cliente con un tiempo medio de respuesta (TMR) inferior a 10 '
    'segundos en cada una de las cuatro categorías de intención. La extensión a las cuatro categorías es posterior a la '
    'formulación inicial de la hipótesis (Tabla 5.11 y Anexo L).')
k.reemplazo(
    'La formulación original fijaba el umbral sin precisar si se contrastaba el valor puntual o el intervalo; la regla '
    'del límite inferior se explicitó en la revisión del trabajo, con la corrida del corpus ya ejecutada, y el diseño '
    'factorial de la Sección 5.2.4 la fijó por escrito antes de medir.',
    'La regla del límite inferior se explicitó con la corrida del corpus ya ejecutada, y el diseño factorial de la '
    'Sección 5.2.4 la aplicó fijada por escrito antes de medir (Tabla 5.11 y Anexo L).')
k.reemplazo(
    'La afirmación sustantiva y efectivamente refutable de H1 es la comparación contra el baseline de atención manual '
    'medido en este trabajo, y es en esos términos que se la somete a prueba en la Sección 5.3.',
    'Lo sustantivo de H1 es, por eso, la magnitud de la reducción respecto del baseline de atención manual medido en este '
    'trabajo, que la Sección 5.3 estima con su intervalo.')

# ------------------------------------------------------------------ B3: objetivos y problema 2
k.reemplazo('registrando MTTD y MTTR; y verificar que el tiempo end-to-end sea inferior a 30 segundos (H1).',
            'registrando MTTD y MTTR; verificar que el tiempo end-to-end sea inferior a 30 segundos; y estimar cuánto '
            'reduce el tiempo de procesamiento de una orden respecto del procesamiento manual (H1).')
k.reescribir(
    'Tres componentes del trabajo no figuraban entre los objetivos específicos',
    'Dos componentes del trabajo no figuraban entre los objetivos específicos formulados al inicio y se incorporaron '
    'durante la investigación: el diseño factorial sobre el prompt del clasificador (Sección 3.5.6) y la evaluación del '
    'contenido de las respuestas (Sección 3.5.7). Se los reporta como ampliaciones del alcance y no como objetivos '
    'cumplidos, y la Tabla 6.1 no los computa. La comparación con el proceso manual, en cambio, se incorporó a OE1 y se '
    'la evalúa como parte de ese objetivo (Anexo L).')
k.reemplazo('responde tarde o da información inconsistente.',
            'responde tarde o da información inconsistente. Este trabajo aborda el problema solo en parte: atiende dos '
            'canales con un mismo sistema, pero no conserva el contexto de un cliente entre canales (Sección 2.3.1).')

t61 = k.tabla(('Obj.', 'Enunciado', 'Resultado', 'Estado'))
i_oe1 = k.fila(t61, 'OE1')
k.celda(t61, i_oe1, 1, 'Pipeline de órdenes: end-to-end < 30 s y reducción respecto del proceso manual')
k.celda(t61, i_oe1, 2,
        'Reducción respecto del procesamiento manual: factor ≈ 780× (IC 95 %: 686× a 875×; Sección 5.3). MTTD: 0,009 s / '
        'MTTR: 0,054 s / Total: 0,063 s (n = 50, corrida E1.a). 50/50 órdenes procesadas sin errores. Bajo concurrencia '
        '(E1.b, 120 órdenes) no hubo sobreventa, porque la restricción CHECK (stock >= 0) del esquema rechazó los '
        'descuentos que la habrían producido; pero 49 de 120 órdenes (40,8 %) quedaron sin procesar, con respuesta HTTP '
        '200 y sin aviso, lo que constituye una falla de confiabilidad (Sección 5.1.3). El objetivo se da por cumplido en '
        'régimen secuencial y no en régimen concurrente.')

t511 = k.tabla(('Hipótesis', 'Criterio', 'Momento en que se fijó el criterio', 'Resultado obtenido', 'Veredicto'))
i_h1 = [i for i, r in enumerate(t511.rows) if r.cells[0].text.startswith('H1:')][0]
k.celda(t511, i_h1, 0, 'H1: Reducción respecto del proceso manual (objetivo de estimación)')
k.celda(t511, i_h1, 1, 'Factor de reducción con IC 95 %; como referencia, límite inferior ≥ 10×; end-to-end < 30 s como '
                       'criterio operativo')

# ------------------------------------------------------------------ B1: remisiones desde el cuerpo
k.reemplazo(
    'Una primera ablación (E7) comparó la configuración principal con un prompt reducido y atribuyó la diferencia a la '
    'base de conocimiento. El diseño no lo permitía, porque aquel prompt no quitaba solo la base sino cinco de los ocho '
    'bloques del prompt: las reglas de clasificación, la base de conocimiento, las reglas críticas, los ejemplos y el '
    'bloque que presenta el mensaje del cliente con su nombre y su canal. Los factores quedaban confundidos. Se la '
    'reemplazó por el diseño factorial que se describe a continuación (E8); la ablación E7 se conserva en el repositorio '
    'como antecedente.',
    'El diseño factorial que se describe a continuación (E8) reemplaza una ablación anterior (E7) cuyos factores estaban '
    'confundidos (Anexo L).')
k.reemplazo(
    'Una afirmación sobre cómo se obtuvo una medición puede verificarse contra una versión del artefacto distinta de la '
    'que corrió. Ocurrió en este trabajo: al documentar el prompt se auditó el workflow vigente en ese momento, de '
    'dieciocho nodos y con el prompt reducido, y se concluyó que el clasificador operaba en régimen zero-shot, cuando el '
    'corpus había corrido el 12 de agosto sobre el workflow de catorce nodos, con base de conocimiento, reglas y ejemplos '
    '(Sección 4.4.3). La auditoría fue correcta en su método y se aplicó al artefacto equivocado.',
    'Una afirmación sobre cómo se obtuvo una medición puede verificarse contra una versión del artefacto distinta de la '
    'que corrió, y en este trabajo ocurrió una vez, con el prompt del clasificador (Anexo L).')
k.reescribir(
    'El corpus del Capítulo 5 corrió el 12 de agosto sobre el workflow de catorce nodos',
    'El corpus del Capítulo 5 corrió el 12 de agosto con el prompt de 6338 caracteres descripto arriba, que coincide '
    'byte a byte con el del commit f68da9d del repositorio. Las 45 interacciones de Telegram de la Sección 5.2.2 y la '
    'ablación E7 corrieron, en cambio, con un prompt reducido de 1032 caracteres, sin base de conocimiento, reglas ni '
    'ejemplos (Anexo H). Qué versión del workflow corrió en cada medición, y cómo se reconstruyó, se detalla en el Anexo L.')
k.reemplazo('Este resultado corrige la interpretación que el trabajo había extraído de la ablación E7. La categoría FAQ',
            'La categoría FAQ')
k.reemplazo(' Los 6,7 puntos que E7 atribuyó a la base corresponden en realidad, sobre todo, a los bloques que aquel '
            'prompt quitaba junto con ella.', '')
k.reemplazo(' Esta conclusión corrige la que el trabajo había extraído de la ablación E7, cuyo diseño confundía los dos '
            'factores (Sección 3.5.6).', '')
k.reemplazo(' El commit f297c9e, que en un primer momento se citó como fuente de este prompt, guarda el mismo texto sin el '
            'signo «=» inicial, con el que la base de conocimiento no se habría inyectado.',
            ' Una cita anterior a otro commit se corrige en el Anexo L.')

# ------------------------------------------------------------------ B1: Anexo L
modelo_titulo = k.par('Anexo K: Verificación de datos concretos')
modelo_intro = k.par('Se transcriben todos los datos concretos que el guion de verificación extrajo')
modelo_rotulo = k.par('Construcción y congelamiento del corpus.')
tabla_k = [t for t in d.tables if t.rows[0].cells[0].text.strip() == 'Interacción'][0]._tbl

titulo = OxmlElement('w:p')
ppr = copy.deepcopy(modelo_titulo._p.pPr)
titulo.append(ppr)
tabla_k.addnext(titulo)
p_titulo = Paragraph(titulo, modelo_titulo._parent)
r = p_titulo.add_run('Anexo L: Registro de desvíos y correcciones')
if modelo_titulo.runs and modelo_titulo.runs[0]._r.rPr is not None:
    r._r.insert(0, copy.deepcopy(modelo_titulo.runs[0]._r.rPr))
k.hechos += 1

ancla = k.insertar_despues(
    p_titulo, modelo_intro,
    'Este anexo reúne la historia de las revisiones del trabajo: los criterios, diseños y afirmaciones que cambiaron entre '
    'versiones, con el motivo de cada cambio. El cuerpo del documento presenta el diseño final y remite aquí. Las '
    'versiones anteriores del documento y de los guiones se conservan en el historial del repositorio.')

secciones = [
    ('Formulación de las hipótesis y de los objetivos.',
     'La versión del trabajo registrada el 27 de abril de 2026 (commit 9dc7b44) formulaba H1 como un tiempo end-to-end '
     'inferior a 30 segundos, frente a un rango de 5 a 30 minutos atribuido al procesamiento manual, y no operacionalizaba '
     'la reducción respecto de él. Cuando se midió el baseline manual, H1 pasó a compararse contra ese baseline, y el '
     'criterio de un orden de magnitud se fijó en la revisión del trabajo, con el resultado ya conocido; por eso H1 se '
     'presenta como objetivo de estimación. La misma versión formulaba una única hipótesis H2 que restringía el tiempo de '
     'respuesta a las consultas de tipo FAQ, estado de pedido y generales; al separarla en H2a y H2b, el tiempo de '
     'respuesta se extendió a las cuatro categorías, porque el contraste siempre se ejecutó sobre los 150 mensajes del '
     'corpus, reclamos incluidos, y la extensión vuelve la hipótesis más exigente. Aquella formulación fijaba además el '
     'umbral de exactitud del 85 % sin precisar si se contrastaba el valor puntual o el intervalo: la regla del límite '
     'inferior se explicitó con la corrida del corpus ya ejecutada, y el diseño factorial la fijó por escrito antes de '
     'medir. La comparación con el proceso manual no figuraba entre los objetivos específicos iniciales y se incorporó a '
     'OE1 cuando se midió el baseline.'),
    ('Ablación E7, reemplazada por el diseño factorial.',
     'Una primera ablación (E7) comparó la configuración principal con un prompt reducido, atribuyó la diferencia, de 6,7 '
     'puntos de exactitud, a la base de conocimiento, y el trabajo concluyó en consecuencia que la base era la pieza '
     'decisiva para clasificar. El diseño no permitía esa atribución, porque aquel prompt no quitaba solo la base sino '
     'cinco de los ocho bloques del prompt: las reglas de clasificación, la base de conocimiento, las reglas críticas, los '
     'ejemplos y el bloque que presenta el mensaje del cliente con su nombre y su canal. Los factores quedaban confundidos. '
     'El diseño factorial E8 (Sección 3.5.6) los separó y mostró lo contrario: la exactitud depende de las reglas y los '
     'ejemplos, y la base no aporta nada cuando ellos están presentes. Los 6,7 puntos que E7 atribuyó a la base '
     'corresponden en realidad, sobre todo, a los bloques que aquel prompt quitaba junto con ella. La conclusión se '
     'corrigió en las Secciones 5.2.4 y 6.3, y E7 se conserva en experiments/E7.'),
    ('Trazabilidad del artefacto medido.',
     'Al documentar el prompt se auditó el workflow vigente en ese momento, de dieciocho nodos y con el prompt reducido, y '
     'se concluyó que el clasificador operaba en régimen zero-shot, cuando el corpus había corrido el 12 de agosto sobre '
     'el workflow de catorce nodos, con base de conocimiento, reglas y ejemplos. La auditoría fue correcta en su método y '
     'se aplicó al artefacto equivocado. La reconstrucción, consultada sobre el historial de versiones y de publicaciones '
     'del motor de flujos, establece la secuencia: la versión del workflow de catorce nodos con que corrió el corpus se '
     'publicó cuatro minutos antes de la corrida, y su prompt coincide byte a byte con el del commit f68da9d; el 25 de '
     'agosto se incorporó el workflow de dieciocho nodos, que suma el canal de Telegram, con un prompt reducido de 1032 '
     'caracteres, con el que corrieron las 45 interacciones de Telegram y la ablación E7; y el 15 de septiembre el diseño '
     'factorial restituyó en ese workflow el prompt de la configuración principal. La reconstrucción se versiona en '
     'experiments/E8/resultados/trazabilidad_versiones.txt. El commit f297c9e, que en un primer momento se citó como '
     'fuente del prompt de la configuración vigente, guarda el mismo texto sin el signo «=» inicial, con el que la base '
     'de conocimiento no se habría inyectado.'),
    ('Pruebas funcionales.',
     'Versiones anteriores informaban las diez pruebas funcionales como aprobadas, sin evidencia versionada. Las pruebas '
     'de rechazo del Flujo 1 se re-ejecutaron con evidencia el 15 de septiembre: PF-04 y PF-05 no producen el rechazo '
     'controlado que fijaba la Tabla 3.4, y se reclasificaron como no aprobada y parcial. Las pruebas del Flujo 2 se '
     'ejecutaron con evidencia el 17 de septiembre: PC-05 se clasificó como FAQ y no como GENERAL, y se informa como no '
     'aprobada. La Tabla 3.5 citaba para PC-02 un número de pedido que no existe en la carga inicial, y la prueba se '
     'ejecutó sobre uno que sí existe. Las evidencias y los guiones están en experiments/PF.'),
    ('Descripción del prompt y origen del corpus.',
     'Versiones anteriores describían la regla crítica 3 del prompt como una instrucción de tono, cuando ordena ocultar '
     'que el asistente es una IA (Sección 2.5), y no advertían que el ejemplo de envío a Córdoba contradice la base de '
     'conocimiento (Sección 5.2.5). Afirmaban también que el equipo había escrito los 150 mensajes del corpus; la '
     'documentación del experimento en el repositorio (experiments/E2/README.md) registra que se redactaron con '
     'asistencia de un modelo de lenguaje a partir de mensajes del equipo, y el documento se corrigió en las Secciones '
     '3.5.3, 3.6 y 6.4 y en la Declaración de originalidad.'),
]
for rotulo, texto in secciones:
    ancla = k.insertar_despues(ancla, modelo_rotulo, rotulo + ' ' + texto, etiqueta=rotulo)

k.guardar()
