# -*- coding: utf-8 -*-
"""Ajustes que surgieron al correr las suites anteriores sobre el resultado de fix_d5_a..e.

  1. El resumen y el abstract recuperan el MTTD y la U de Mann-Whitney, que
     entran dentro del límite de 300 palabras.
  2. Dos frases nuevas hablaban de una «versión anterior» del documento, que la
     subsanación del primer dictamen sacó del texto expuesto (control #23). Se
     reformulan sin perder la corrección que declaran.

NO es idempotente: aborta si el resumen ya menciona el MTTD.
Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
res = k.par('Sobre 50 órdenes, el tiempo end-to-end fue de 0,063 s')
if 'MTTD' in res.text:
    sys.exit('ERROR: este guion ya se aplicó.')

k.reemplazo('Sobre 50 órdenes, el tiempo end-to-end fue de 0,063 s, frente a 49,13 s',
            'Sobre 50 órdenes, el MTTD medio fue de 0,009 s y el tiempo end-to-end de 0,063 s, frente a 49,13 s')
k.reemplazo('(IC 95 % por el teorema de Fieller: 686× a 875×), que se lee',
            '(IC 95 % por el teorema de Fieller: 686× a 875×; U de Mann-Whitney = 0, p = 2,7 × 10⁻¹¹), que se lee')
k.reemplazo('Over 50 orders, end-to-end time was 0.063 s, against 49.13 s',
            'Over 50 orders, mean MTTD was 0.009 seconds and end-to-end time 0.063 s, against 49.13 s')
k.reemplazo('(Fieller 95 % CI: 686× to 875×), read as',
            '(Fieller 95 % CI: 686× to 875×; Mann-Whitney U = 0, p = 2.7 × 10⁻¹¹), read as')
k.reemplazo('La historia de versiones de este nodo se declara porque una versión anterior de este documento la describió '
            'mal, y el error es instructivo.',
            'La historia de versiones de este nodo se declara porque en un primer momento el trabajo la reconstruyó mal, '
            'y el error es instructivo.')
k.reemplazo('El commit f297c9e, citado en una versión anterior de este anexo, guarda',
            'El commit f297c9e, que en un primer momento se citó como fuente de este prompt, guarda')

for pref, lim in (('RESUMEN', (250, 300)), ('ABSTRACT', (230, 320))):
    P = [p.text.strip() for p in d.paragraphs]
    i = P.index(pref)
    j = next(n for n, t in enumerate(P) if n > i and t.startswith(('Palabras clave', 'Keywords')))
    palabras = len(' '.join(P[i + 1:j]).split())
    assert lim[0] <= palabras <= lim[1], '%s: %d palabras' % (pref, palabras)
    print('%s: %d palabras' % (pref, palabras))

k.guardar()
