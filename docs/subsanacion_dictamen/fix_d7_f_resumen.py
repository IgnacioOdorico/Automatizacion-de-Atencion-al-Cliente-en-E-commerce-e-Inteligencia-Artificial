# -*- coding: utf-8 -*-
"""Dictamen del 15/09: el resumen quedó en 301 palabras tras matizar las hipótesis; se recortan dos.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
k.reemplazo('Sobre un e-commerce simulado y en contenedores Docker', 'Sobre un e-commerce simulado en contenedores Docker')
k.reemplazo('leído como orden de magnitud de laboratorio y no como cota', 'leído como orden de magnitud de laboratorio, no como cota')
k.guardar()
