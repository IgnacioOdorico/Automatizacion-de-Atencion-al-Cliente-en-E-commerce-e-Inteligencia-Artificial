# -*- coding: utf-8 -*-
"""Últimos dos residuos de la pasada de la auditoría del 17/09.

  - §3.5.2: quedaba una segunda mención a la «versión anterior», que las revisiones
    previas habían sacado del texto expuesto.
  - Resumen: al comprimirlo se perdió la forma «2 de las 18», que es la que usa el
    abstract y con la que el resultado se lee igual en los dos idiomas.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
k.reemplazo('la exactitud de la versión anterior se calculaba sobre etiquetas escritas a mano en la carga inicial '
            'de la base, que ningún modelo había producido (Anexo L).',
            'esa cifra se calculaba sobre etiquetas escritas a mano en la carga inicial de la base, que ningún '
            'modelo había producido (Anexo L).')
k.reemplazo('una verificación automática halló 2 de 18 respuestas con datos que la base no respalda,',
            'una verificación automática halló 2 de las 18 respuestas con datos que la base no respalda,')
k.guardar()
