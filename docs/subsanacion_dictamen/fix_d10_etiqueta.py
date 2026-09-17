# -*- coding: utf-8 -*-
"""La etiqueta que cita el documento pasa a la de esta revisión.

Cada revisión lleva su propia etiqueta inmutable; la Declaración de originalidad y
el Anexo J citan la que corresponde a la versión entregada.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
k.reemplazo('entrega-2026-09-r4', 'entrega-2026-09-r5', n=2)
k.guardar()
