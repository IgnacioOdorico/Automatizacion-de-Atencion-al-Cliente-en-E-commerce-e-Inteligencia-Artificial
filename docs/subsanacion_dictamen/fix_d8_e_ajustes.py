# -*- coding: utf-8 -*-
"""Ajustes tras el grupo B del dictamen del 15/09.

  - H1 y H2a quedaron íntegramente en negrita al reescribirse: vuelve la negrita solo al rótulo.
  - Anexo L: sin la cifra vieja del rango manual y sin «H2» a secas; usa «formulación original».
  - §5.2.1: sin «versión anterior» en el cuerpo (la historia está en el Anexo L).

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

for rotulo in ('H1:', 'H2a:'):
    p = k.par(rotulo + ' El pipeline' if rotulo == 'H1:' else rotulo + ' El chatbot')
    texto = p.text
    # el texto quedó entero en el primer run, en negrita; los demás runs están vacíos
    assert p.runs[0].text == texto and p.runs[0].bold, [(r.text[:10], r.bold) for r in p.runs]
    k.reescribir(p, texto, etiqueta=rotulo)
    assert p.runs[1].text == texto[len(rotulo):] and not p.runs[1].bold

k.reemplazo(
    'La versión del trabajo registrada el 27 de abril de 2026 (commit 9dc7b44) formulaba H1 como un tiempo end-to-end '
    'inferior a 30 segundos, frente a un rango de 5 a 30 minutos atribuido al procesamiento manual, y no operacionalizaba '
    'la reducción respecto de él.',
    'En su formulación original, registrada en la versión del trabajo del 27 de abril de 2026 (commit 9dc7b44), H1 fijaba '
    'un tiempo end-to-end inferior a 30 segundos frente a un rango de tiempos manuales que no había sido medido, y no '
    'operacionalizaba la reducción respecto del proceso manual.')
k.reemplazo('La misma versión formulaba una única hipótesis H2 que restringía',
            'La misma versión formulaba una única hipótesis sobre el chatbot, que restringía')
k.reemplazo(' La Tabla 3.5 cita para PC-02 un pedido de la carga inicial; su versión anterior citaba uno inexistente '
            '(Anexo L).',
            ' La Tabla 3.5 cita para PC-02 un pedido de la carga inicial (Anexo L).')
k.guardar()
