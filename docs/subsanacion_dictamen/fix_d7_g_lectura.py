# -*- coding: utf-8 -*-
"""Ajuste de la lectura de control del dictamen del 15/09.

  §5.4: base, reglas y ejemplos son cuatro bloques del prompt, no tres; se nombran.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
k.reemplazo('el prompt de E7, igualmente sin esos tres bloques pero con el mensaje del cliente presentado de otra forma,',
            'el prompt de E7, igualmente sin base, reglas ni ejemplos, pero con el mensaje del cliente presentado de otra forma,')
k.guardar()
