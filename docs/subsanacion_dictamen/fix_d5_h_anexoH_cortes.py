# -*- coding: utf-8 -*-
"""Anexo H: los dos prompts transcriptos cortan línea por palabra.

El estilo Source Code declara wordWrap=0, que en Word permite cortar en cualquier
carácter («garant ía», «amabl emente»). Los prompts son prosa: se les fija
wordWrap=1 a nivel de párrafo, sin tocar el estilo ni el texto transcripto.

Idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

d = abrir()
k = Kit(d)
prompts = [p for p in d.paragraphs if p.style.name == 'Source Code' and p.text.startswith(('=# --- START', '# --- START'))]
assert len(prompts) == 2, 'se esperaban los dos prompts del Anexo H'
for p in prompts:
    pPr = p._p.get_or_add_pPr()
    ww = pPr.find(qn('w:wordWrap'))
    if ww is None:
        ww = pPr.makeelement(qn('w:wordWrap'), {})
        pPr.append(ww)
    ww.set(qn('w:val'), '1')
    k.hechos += 1
k.guardar()
