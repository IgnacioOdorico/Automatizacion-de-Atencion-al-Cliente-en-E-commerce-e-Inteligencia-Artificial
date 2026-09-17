# -*- coding: utf-8 -*-
"""Vuelve a pedir que Word recalcule el índice al abrir el documento.

Word borra w:updateFields de settings.xml cuando guarda; sin esa marca, quien abra
el .docx ve el índice con las páginas de la última generación y no con las suyas.
Se ejecuta después de cada pasada de actualizar_toc_y_pdf.ps1.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

d = abrir()
sett = d.settings.element
if sett.find(qn('w:updateFields')) is None:
    sett.append(sett.makeelement(qn('w:updateFields'), {qn('w:val'): 'true'}))
    d.save('docs/TESIS_FINAL_UTN_v6.docx')
    print('settings.xml: updateFields=true restaurado')
else:
    print('settings.xml: ya estaba')
