# -*- coding: utf-8 -*-
"""Último ajuste de la pasada: nombrar la orden con que se verificó la alerta.

La §5.1.1 decía «la orden con la que se verificó la alerta de stock bajo» sin
identificarla, y el número de orden es el dato que hace verificable la afirmación.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
k.reemplazo('y en la orden con la que se verificó la alerta de stock bajo.',
            'y en la orden ORD-AUDIT-ALERT, con la que se verificó la alerta de stock bajo.')
k.guardar()
