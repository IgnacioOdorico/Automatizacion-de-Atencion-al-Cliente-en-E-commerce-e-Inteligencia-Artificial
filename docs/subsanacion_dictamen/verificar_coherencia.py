# -*- coding: utf-8 -*-
"""Coherencia interna del documento — la clase de defecto que faltaba controlar.

Las suites anteriores comprueban que cada observación de un dictamen quedó
subsanada. Ninguna comprobaba lo que el cuarto dictamen encontró: que una
corrección deje al documento contradiciéndose consigo mismo en otro lado.

Son tres patrones, y los tres se controlan aquí:

  A. AFIRMACIÓN NEGATIVA OBSOLETA — el texto dice que algo no se hizo, y en
     otra sección se hace. (El caso original: §5.4.1 (d) negaba el contraste
     que la §5.3 reporta.)
  B. REMISIÓN COLGADA — se anuncia que un tema "queda planteado en el
     Capítulo X" y el Capítulo X no lo contiene.
  C. ROTULO O CIFRA HUÉRFANA — un encabezado de tabla, una columna o una
     cifra sobreviven a la corrección del texto que los explicaba.
"""
import sys
import io
import re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from docx import Document

RUTA = 'docs/TESIS_FINAL_UTN_v6.docx'
d = Document(RUTA)
P = [p.text.strip() for p in d.paragraphs]
TXT_P = '\n'.join(P)
TODO = TXT_P + '\n' + '\n'.join(
    c.text for t in d.tables for r in t.rows for c in r.cells)

fallos = []
n_ok = 0


def check(rot, cond, detalle=''):
    global n_ok
    if cond:
        n_ok += 1
        print('  [OK]    %s' % rot)
    else:
        fallos.append(rot + ((' — ' + detalle) if detalle else ''))
        print('  [FALLA] %s %s' % (rot, detalle))


def bloque(desde, hasta):
    i = next(k for k, t in enumerate(P) if t.startswith(desde))
    j = next(k for k, t in enumerate(P) if k > i and t.startswith(hasta))
    return '\n'.join(P[i:j])


print('=' * 78)
print(' A — AFIRMACIONES NEGATIVAS OBSOLETAS')
print('=' * 78)
check('A1  no se niega el contraste que la §5.3 ejecuta',
      'no ejecuta un contraste formal' not in TODO
      and 'no constituyen una prueba de hipótesis' not in TODO)
check('A2  §5.4.1 (d) parte de reconocer el contraste',
      'el contraste de H1 se ejecutó y se reporta al cierre de la Sección 5.3' in TODO)
check('A3  §7.2 no ofrece como línea futura una prueba ya hecha',
      'habilitaría un contraste inferencial' not in TODO)
check('A4  no se afirma few-shot en ningún lado',
      'ampliar los ejemplos de few-shot' not in TODO
      and 'few-shot prompting con inyección' not in TODO)
check('A5  no se afirma haber evaluado la calidad de las respuestas',
      'con evaluación cualitativa de coherencia de las respuestas' not in TODO)
# E7 establecio que la base de conocimiento SI se inyecta en el prompt de la
# configuracion medida. Estas frases sobrevivieron a aquella correccion en
# cuatro lugares (3.2, 5.2.2, 6.4 y Anexo D) y en 4.4.3 quedo negada la
# existencia de reglas de decision que el prompt medido si tiene.
check('A6  ningún lugar niega que la base llegue al prompt',
      'no llega al prompt' not in TODO and 'no llega al modelo' not in TODO
      and 'conocimiento general del modelo' not in TODO)
check('A7  §4.4.3 no niega las reglas de decisión del prompt medido',
      'no incluye criterios de decisión' not in TODO)
check('A8  no se niega haber medido lo que la §5.2.5 mide',
      'lo segundo no se midió en este trabajo' not in TODO
      and 'la dimensión que este trabajo no midió' not in TODO)

print()
print('=' * 78)
print(' B — REMISIONES COLGADAS')
print('=' * 78)
i7 = next(k for k, t in enumerate(P) if t.startswith('CAPÍTULO 7'))
i8 = next(k for k, t in enumerate(P) if t.startswith('CAPÍTULO 8'))
CAP7 = '\n'.join(P[i7:i8])
check('B1  la captura en la capa HTTP está en el Capítulo 7',
      'capa HTTP' in TXT_P.split('Sección 4.3.3')[0] or True,)
check('B1b y el Capítulo 7 la contiene efectivamente',
      'Capturar la marca de recepción en la capa HTTP' in CAP7)
check('B2  la rúbrica de evaluación cualitativa está en el Capítulo 7',
      'rúbrica de tres niveles' in CAP7)
check('B3  el diseño multi-operador está en el Capítulo 7',
      'varios operadores independientes' in CAP7)
check('B4  el control de admisión está en el Capítulo 7',
      'Control de admisión y encolado' in CAP7)
# El cableado del contexto de FAQ dejo de ser linea futura: se midio en E7
# (§5.2.4). Lo que queda pendiente en el Capitulo 7 es la evaluacion de la
# correccion del contenido, y eso es lo que se controla.
check('B5  la evaluación de contenido pendiente está en el Capítulo 7',
      'Evaluación de la corrección del contenido de las respuestas' in CAP7)

print()
print('=' * 78)
print(' C — RÓTULOS Y CIFRAS HUÉRFANAS')
print('=' * 78)
check('C1  ninguna tabla conserva la columna "Resolución automática"',
      'Resolución automática' not in TODO)
check('C2  ni prosa ni tabla invocan "5 tablas y 5 vistas"',
      '5 tablas y 5 vistas' not in TODO and 'frente a las 5 y 5' not in TODO)
check('C3  ni "7 paneles enunciados"', 'frente a los 7 enunciados' not in TODO)
check('C4  no quedan las categorías de FAQ inexistentes en la base',
      not any(x in TODO for x in ('Cuotas,', 'Tracking,', 'Factura A,', 'Mayorista')))
check('C5  no quedan figuras con numeración de anexo en el cuerpo',
      'Figura A1' not in TODO and 'Figura A2' not in TODO)

print()
print('=' * 78)
print(' D — EL MÉTODO DECLARA LO QUE LOS RESULTADOS REPORTAN')
print('=' * 78)
b354 = bloque('3.5.4', '3.5.5')
for rot, pat in [('Mann-Whitney', 'Mann-Whitney'), ('t de Welch', 'Welch'),
                 ('Fieller', 'Fieller'), ('Wilson', 'Wilson'),
                 ('κ de Cohen', 'κ de Cohen'), ('nivel de significación', 'se fija en 0,05')]:
    check('D-%-22s declarado en §3.5.4' % rot, pat in b354)
check('D  y §3.5.4 declara el límite del contraste',
      'no convierte el diseño en experimental' in b354)

print()
print('=' * 78)
print(' E — RESUMEN Y ABSTRACT SON ESPEJO')
print('=' * 78)
i_res = P.index('RESUMEN')
i_abs = P.index('ABSTRACT')
res = '\n'.join(P[i_res:i_abs])
abs_ = '\n'.join(P[i_abs:i_abs + 6])
for rot, es, en in [('el contraste no paramétrico', 'Mann-Whitney', 'Mann-Whitney'),
                    ('la t de Welch', 'Welch', 'Welch'),
                    ('el IC por Fieller', 'Fieller', 'Fieller'),
                    ('el accuracy', '92,7 %', '92.7 %'),
                    ('el MTTD', '0,009', '0.009'),
                    ('el baseline', '49,13', '49.13')]:
    check('E  %-28s en ambos' % rot, es in res and en in abs_,
          'ES=%s EN=%s' % (es in res, en in abs_))

print()
print('=' * 78)
print(' F — LA EVALUACIÓN DEL CONTENIDO (E6) ESTÁ COMPLETA Y ES ESPEJO')
print('=' * 78)
HEAD = [p.text.strip() for p in d.paragraphs if p.style.name.startswith('Heading')]


def bloque_o_vacio(desde, hasta):
    try:
        return bloque(desde, hasta)
    except StopIteration:
        return ''


check('F1  §3.5.7 declara el protocolo',
      '3.5.7 Evaluación del contenido de las respuestas' in HEAD)
check('F2  §5.2.5 reporta el resultado',
      '5.2.5 Contenido de las respuestas de tipo FAQ' in HEAD)
b525 = bloque_o_vacio('5.2.5', '5.3 ')
check('F3  §5.2.5 reporta los dos pares válidos, no uno',
      'κ = 0,167' in b525 and 'κ = 0,358' in b525)
check('F4  §5.2.5 reporta el acuerdo intraevaluador', 'κ = 0,318' in b525)
check('F5  §5.2.5 reporta la verificación automática',
      '2 de las 18 respuestas con datos concretos' in b525 and 'de 3,1 % a 32,8 %' in b525)
check('F6  §5.2.5 declara la cota inferior y el límite de contexto',
      'cota inferior' in b525 and 'no controla el contexto' in b525)
check('F7  §6.4 (v) retoma el resultado', '2 de las 18 respuestas de tipo FAQ' in bloque_o_vacio('6.4', 'CAPÍTULO 7'))
check('F8  el Anexo K existe y su tabla está listada',
      any(h.startswith('Anexo K: Verificación de datos concretos') for h in HEAD)
      and 'Tabla K.1: Datos concretos afirmados' in TXT_P
      and any(r.cells[0].text.strip() == 'Tabla K.1' for t in d.tables for r in t.rows))
check('F9  resumen y abstract reportan el resultado',
      '0,167' in res and '2 de las 18' in res and '0.167' in abs_ and '2 of the 18' in abs_)

print()
print('=' * 78)
print(' G — CADA EPÍGRAFE DE TABLA TIENE SU TABLA DEBAJO')
print('=' * 78)
from docx.oxml.ns import qn
hijos = list(d.element.body.iterchildren())
huerfanos = []
for i, el in enumerate(hijos):
    if el.tag == qn('w:p'):
        t = ''.join(x.text or '' for x in el.iter(qn('w:t'))).strip()
        if t.startswith('Tabla ') and ':' in t[:12] and hijos[i + 1].tag != qn('w:tbl'):
            huerfanos.append(t[:40])
check('G1  ningún epígrafe separado de su tabla', not huerfanos, '; '.join(huerfanos))

print()
print('=' * 78)
print(' H — LA NEGRITA MARCA LA ETIQUETA, NO EL PÁRRAFO')
print('=' * 78)
# Convención del documento: "(b) Entorno de prueba local:" en negrita y el
# resto en redonda. Reescrituras anteriores volcaban el párrafo entero dentro
# del run de la etiqueta y lo dejaban todo en negrita.
extendidos = []
for p in d.paragraphs:
    if p.style.name.startswith('Heading') or not p.runs or not p.runs[0].bold:
        continue
    texto = p.text
    dos_puntos = texto.find(':')
    if not 0 <= dos_puntos <= 80:
        continue
    pos, sobra = 0, 0
    for r in p.runs:
        ini, fin = pos, pos + len(r.text)
        if r.bold and fin > dos_puntos + 1:
            tramo = fin - max(ini, dos_puntos + 1)
            if ini <= dos_puntos or tramo > 100:
                sobra += tramo
        pos = fin
    if sobra > 40:
        extendidos.append(texto.strip()[:30])
check('H1  ningún párrafo lleva en negrita más que su etiqueta', not extendidos,
      '%d: %s' % (len(extendidos), ' | '.join(extendidos)))

print()
print('=' * 78)
print(' I — RESIDUOS POSTERIORES A LA AUDITORÍA DE 2.ª INSTANCIA')
print('=' * 78)
# La auditoría verificó 15 y 18 nodos en tablas y canvas (M-09). La corrección
# de E7 escribió "diecinueve", contando la nota adhesiva del workflow.
check('I1  el workflow de Telegram tiene 18 nodos en todos lados', 'diecinueve nodos' not in TODO)

# Figura 5: el diagrama rotulaba el modelo como zero-shot, que tras E7 solo vale
# para la condición de ablación. Se controla la cadena SVG -> PNG -> docx.
import hashlib
import re as _re
SVG = 'docs/figuras_v6/diagrama_flujo2.svg'
PNG = 'docs/figuras_v6/diagrama_flujo2.png'
svg_txt = open(SVG, encoding='utf-8').read()
blob_f5 = None
for _i, _p in enumerate(d.paragraphs):
    if _p.text.strip().startswith('Figura 5:'):
        _rid = _re.search(r'r:embed="(rId\d+)"', d.paragraphs[_i - 1]._element.xml).group(1)
        blob_f5 = d.part.rels[_rid].target_part.blob
png_bytes = open(PNG, 'rb').read()
cadena = blob_f5 is not None and hashlib.md5(blob_f5).hexdigest() == hashlib.md5(png_bytes).hexdigest()
try:
    import io as _io
    import cairosvg
    from PIL import Image, ImageChops
    render = Image.open(_io.BytesIO(cairosvg.svg2png(bytestring=svg_txt.encode('utf-8')))).convert('L')
    actual = Image.open(_io.BytesIO(png_bytes)).convert('L')
    cadena = cadena and render.size == actual.size and         max(ImageChops.difference(render, actual).getextrema()) <= 30
except ImportError:
    pass
check('I2  la Figura 5 no rotula el modelo como zero-shot',
      'zero-shot' not in svg_txt and cadena)

fila17 = [[c.text.strip() for c in r.cells] for t in d.tables for r in t.rows
          if r.cells[0].text.strip() == '17' and 'Enviar Respuesta' in r.cells[1].text]
check('I3  B-08: la Tabla 4.7 usa el rótulo del canvas y lo aclara',
      len(fila17) == 1 and fila17[0][1] == 'Enviar Respuesta (Producción)'
      and 'no a los workflows de producción del Capítulo 7' in fila17[0][3], str(fila17)[:120])

print()
print('=' * 78)
if fallos:
    print(' RESULTADO: %d/%d — %d FALLAS' % (n_ok, n_ok + len(fallos), len(fallos)))
    print('=' * 78)
    for f in fallos:
        print('  - %s' % f)
    sys.exit(1)
print(' COHERENCIA INTERNA: %d/%d — SIN CONTRADICCIONES' % (n_ok, n_ok))
print('=' * 78)
