# -*- coding: utf-8 -*-
"""Revisión de estructura del 17/09/2026: el documento cita la etiqueta de su versión, entrega-2026-09-r4.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
k.reemplazo('entrega-2026-09-r3', 'entrega-2026-09-r4', n=2)
k.guardar()
