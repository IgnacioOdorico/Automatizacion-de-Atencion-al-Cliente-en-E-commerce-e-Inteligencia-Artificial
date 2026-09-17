# -*- coding: utf-8 -*-
"""Revisión de estructura del 17/09/2026: portada.

La portada imprimía el rótulo interno «PORTADA» y repetía el título, los autores y la
fecha (esta última en otro formato) debajo del bloque principal. Quedan el título,
los autores y la fecha una sola vez, y los datos institucionales que no se repiten.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
i_decl = next(i for i, p in enumerate(d.paragraphs) if p.text.strip() == 'DECLARACIÓN DE ORIGINALIDAD')
portada = d.paragraphs[:i_decl]
for p in portada:
    t = p.text.strip()
    if t == 'PORTADA' or t.startswith(('Título:', 'Autores:')) or t == 'Mendoza – Argentina, 2026':
        k.eliminar(p)
assert k.hechos == 4, k.hechos
k.guardar()
