# -*- coding: utf-8 -*-
"""Lectura de control del grupo B: en §2.5, «ese deber» quedó separado de su referente por el párrafo de Moffatt.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
k.reemplazo('El prompt medido en este trabajo contraviene ese deber, y no por una cuestión de tono.',
            'El prompt medido en este trabajo contraviene el deber de informar que el canal es automatizado, y no por una '
            'cuestión de tono.')
k.guardar()
