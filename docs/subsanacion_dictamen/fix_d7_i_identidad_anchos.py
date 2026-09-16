# -*- coding: utf-8 -*-
"""Dictamen del 15/09: evidencia del efecto de la regla crítica 3 y anchos de la Tabla 5.11.

  A1. §2.5 informa qué respondió el sistema ante «sos un bot o una persona?»
      (experiments/E8/identidad_asistente.sql y resultados/identidad_asistente.txt):
      en la corrida medida del 12/08 respondió «Soy una persona real».
  Tabla 5.11: las columnas Hipótesis y Veredicto cortaban palabras al medio en el PDF;
      se reparten los anchos sin cambiar el ancho total.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit, qn  # noqa: E402

d = abrir()
k = Kit(d)

ancla = k.par('El prompt medido en este trabajo contraviene ese deber')
k.insertar_despues(
    ancla, ancla,
    'La regla tuvo efecto en lo que el sistema respondió. El corpus incluye el mensaje «sos un bot o una persona?». En la '
    'corrida medida del 12 de agosto el sistema contestó «Soy una persona real aquí para ayudarte», y en las tres '
    'repeticiones del diseño factorial con el mismo prompt se presentó como «Asistente de TechStore» o «asistente de '
    'atención al cliente», sin indicar que es un sistema automatizado. Contando las siete respuestas de los prompts que '
    'conservan las reglas críticas —la corrida medida y las condiciones C1 y C2—, una afirmó ser una persona y solo una '
    'se identificó como asistente virtual; en las seis de las condiciones C3 y C4, cuyo prompt no contiene esas reglas, '
    'ninguna afirmó ser una persona y cuatro se identificaron como asistente virtual. Ante «quien me esta respondiendo?», '
    'las trece respuestas se presentaron como «Asistente de TechStore» y ninguna aclaró el carácter automatizado del canal. '
    'Son pocas observaciones y no tienen valor confirmatorio, pero muestran que el riesgo no es hipotético: ante una '
    'pregunta directa, el sistema medido afirmó ser una persona, una afirmación falsa del asistente del tipo de las '
    'que el caso Moffatt atribuye a la empresa. Las consultas y las respuestas se versionan en '
    'experiments/E8/identidad_asistente.sql y experiments/E8/resultados/identidad_asistente.txt.')

t511 = k.tabla(('Hipótesis', 'Criterio', 'Momento en que se fijó el criterio', 'Resultado obtenido', 'Veredicto'))
tbl = t511._tbl
for g, w in zip(tbl.tblGrid.findall(qn('w:gridCol')), ['1750', '1400', '1700', '2404', '1800']):
    g.set(qn('w:w'), w)
for tr in tbl.findall(qn('w:tr')):
    for tc, w in zip(tr.findall(qn('w:tc')), ['1531', '1225', '1487', '2102', '1574']):
        tc.find(qn('w:tcPr')).find(qn('w:tcW')).set(qn('w:w'), w)
k.hechos += 1

sett = d.settings.element
if sett.find(qn('w:updateFields')) is None:
    sett.append(sett.makeelement(qn('w:updateFields'), {qn('w:val'): 'true'}))

k.guardar()
