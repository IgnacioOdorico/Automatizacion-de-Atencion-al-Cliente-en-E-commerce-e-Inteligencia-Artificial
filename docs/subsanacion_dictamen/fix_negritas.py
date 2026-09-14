# -*- coding: utf-8 -*-
"""Negrita desbordada: la etiqueta vuelve a ser lo único en negrita.

Defecto introducido por reescrituras anteriores: al volcar el texto completo de
un párrafo en su primer run, que era la etiqueta en negrita ("H1:", "(d) ...:",
"Sobre la ...:"), el párrafo entero quedaba en negrita. La convención del
documento es la de sus párrafos sanos: etiqueta hasta los dos puntos en negrita
y el resto en redonda.

Regla, sobre párrafos que no son encabezados y cuyo primer run está en negrita
con dos puntos dentro de los primeros 80 caracteres:
  - el run que contiene la etiqueta se parte en los dos puntos; lo que sigue
    pasa a redonda, con el resto de su formato intacto;
  - un run posterior en negrita de más de 100 caracteres también pasa a
    redonda (continuación del volcado); los énfasis breves se conservan, como
    "(i) alucinación" en §5.4.1 (a).

Además, H2a recibe la etiqueta en negrita que tienen H1 y H2b, y (c-bis) la que
tienen los demás ítems de §5.4.1.

NO es idempotente. Se corre después de fix_e6_contenido.py.
Solo toca formato: el texto de cada párrafo queda idéntico, y se verifica.
"""
import sys
import os
import copy

from docx import Document
from docx.oxml.ns import qn
from docx.text.run import Run

if any(f.startswith('~$') for f in os.listdir('docs')):
    sys.exit('ERROR: Word tiene abierto un documento en docs/.')

RUTA = 'docs/TESIS_FINAL_UTN_v6.docx'
d = Document(RUTA)


def sin_negrita(rPr):
    for tag in ('w:b', 'w:bCs'):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)


tocados = []
for p in d.paragraphs:
    if p.style.name.startswith('Heading') or not p.runs or not p.runs[0].bold:
        continue
    texto_antes = p.text
    dos_puntos = texto_antes.find(':')
    if not 0 <= dos_puntos <= 80:
        continue
    corte = dos_puntos + 1
    cambios = 0
    pos = 0
    for r in list(p.runs):
        ini, fin = pos, pos + len(r.text)
        pos = fin
        if not r.bold or fin <= corte:
            continue
        if ini < corte:
            resto = r.text[corte - ini:]
            if len(resto) <= 40:
                continue
            nuevo = copy.deepcopy(r._r)
            r.text = r.text[:corte - ini]
            nuevo_run = Run(nuevo, p)
            nuevo_run.text = resto
            if nuevo.rPr is not None:
                sin_negrita(nuevo.rPr)
            r._r.addnext(nuevo)
            cambios += 1
        elif len(r.text) > 100:
            if r._r.rPr is not None:
                sin_negrita(r._r.rPr)
            cambios += 1
    if cambios:
        assert p.text == texto_antes, 'cambió el texto de: %r' % texto_antes[:40]
        tocados.append(texto_antes.strip()[:60])

h2a = [p for p in d.paragraphs if p.text.strip().startswith('H2a: El chatbot basado en GPT-4o-mini')]
assert len(h2a) == 1
p = h2a[0]
assert not any(r.bold for r in p.runs)
r0 = p.runs[0]
etiqueta = 'H2a:'
assert r0.text.startswith(etiqueta)
nuevo = copy.deepcopy(r0._r)
Run(nuevo, p).text = r0.text[len(etiqueta):]
r0.text = etiqueta
r0.bold = True
r0._r.addnext(nuevo)
assert p.text.startswith('H2a: El chatbot')
tocados.append('H2a: (etiqueta en negrita, como H1 y H2b)')

for inicio in ('(c-bis) Ventana temporal de la corrida del chatbot:',):
    ps = [q for q in d.paragraphs if q.text.strip().startswith(inicio)]
    assert len(ps) == 1
    p = ps[0]
    antes = p.text
    r0 = p.runs[0]
    assert r0.text.startswith(inicio) and not any(r.bold for r in p.runs)
    nuevo = copy.deepcopy(r0._r)
    Run(nuevo, p).text = r0.text[len(inicio):]
    r0.text = inicio
    r0.bold = True
    r0._r.addnext(nuevo)
    assert p.text == antes
    tocados.append(inicio + ' (única etiqueta de §5.4.1 sin negrita)')

d.save(RUTA)
print('párrafos corregidos: %d' % len(tocados))
for t in tocados:
    print('  - ' + t)
