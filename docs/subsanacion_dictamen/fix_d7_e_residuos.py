# -*- coding: utf-8 -*-
"""Dictamen del 15/09: inconsistencias remanentes de la tabla final y etiqueta de versión.

  B1. Tabla 3.1: el Flujo 2 tiene 18 nodos, 17 en uso (el trigger de Gmail no está activado).
  B2. «casi simultáneas» en §3.5.2, Tabla 5.3 y Anexo E, como en §3.5.8.
  B4. Citas en el texto con «y» en lugar de «&».
  B5. §3.6: la cursiva de las amenazas y mitigaciones agregadas alcanza solo al rótulo.
  C5. El documento cita la etiqueta entrega-2026-09-r2: la etiqueta entrega-2026-09
      queda fija en la versión que evaluó el dictamen del 15/09 y no se mueve.
(El título de la Tabla 5.10, B3, lo corrige fix_d7_d.)

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ B1
t31 = k.tabla(('Etapa', 'Descripción', 'Entregable'))
k.celda(t31, k.fila(t31, '4. Flujo 2 — Chatbot'), 1,
        'Workflow de 18 nodos, 17 en uso —el trigger de Gmail queda diseñado y sin activar—: dos canales (WhatsApp '
        'simulado y Telegram real), IA, tickets')

# ------------------------------------------------------------------ B2
k.reemplazo('El segundo disparó 20 solicitudes simultáneas', 'El segundo disparó 20 solicitudes casi simultáneas')
k.reemplazo('Rondas × solicitudes simultáneas', 'Rondas × solicitudes casi simultáneas')
k.reemplazo('20 solicitudes simultáneas por ronda', '20 solicitudes casi simultáneas por ronda')

# ------------------------------------------------------------------ B4
for autores, n in [('Jurafsky', 2), ('Laudon', 1), ('Womack', 1), ('Perez', 2)]:
    pares = {'Jurafsky': ('Jurafsky & Martin, 2024', 'Jurafsky y Martin, 2024'),
             'Laudon': ('Laudon & Traver, 2021', 'Laudon y Traver, 2021'),
             'Womack': ('Womack & Jones, 2003', 'Womack y Jones, 2003'),
             'Perez': ('Perez & Ribeiro, 2022', 'Perez y Ribeiro, 2022')}
    k.reemplazo(*pares[autores], n=n)

# ------------------------------------------------------------------ B5
arreglados = 0
for p in d.paragraphs:
    t = p.text
    for rotulo in ('Amenaza:', 'Mitigación:'):
        if t.startswith(rotulo) and p.runs and all(r.italic for r in p.runs if r.text.strip()):
            k.reescribir(p, t, etiqueta=rotulo)
            p.runs[0].italic = True
            p.runs[1].italic = None
            arreglados += 1
assert arreglados == 11, 'se esperaban 11 párrafos íntegramente en cursiva, hay %d' % arreglados

# ------------------------------------------------------------------ C5
k.reemplazo('se identifica con la etiqueta entrega-2026-09 (Anexo J)', 'se identifica con la etiqueta entrega-2026-09-r2 (Anexo J)')
k.reemplazo('La etiqueta entrega-2026-09 identifica', 'La etiqueta entrega-2026-09-r2 identifica')

k.guardar()
