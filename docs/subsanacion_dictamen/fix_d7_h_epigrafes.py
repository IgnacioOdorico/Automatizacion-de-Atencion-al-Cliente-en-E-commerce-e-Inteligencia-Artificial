# -*- coding: utf-8 -*-
"""Lectura del PDF del 16/09: cinco epígrafes de tabla quedaban al pie de una página y su tabla en la siguiente.

Se marca «conservar con el siguiente» en todo epígrafe de tabla que precede a su tabla.
Es idempotente, pero no hace falta volver a correrlo.
"""
import sys
import re

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
tablas = {t._tbl for t in d.tables}
n = 0
for p in d.paragraphs:
    if re.match(r'^Tabla [\dA-K]+\.\d+:', p.text.strip()):
        sig = p._p.getnext()
        assert sig in tablas, 'el epígrafe no precede a su tabla: %s' % p.text[:40]
        p.paragraph_format.keep_with_next = True
        n += 1
assert n == 29, n
k.hechos = n
k.guardar()
