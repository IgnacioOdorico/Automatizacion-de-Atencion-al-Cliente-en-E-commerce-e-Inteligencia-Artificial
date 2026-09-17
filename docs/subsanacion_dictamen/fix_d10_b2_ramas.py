# -*- coding: utf-8 -*-
"""Ajuste de A-02: nombrar la rama en la que se produjo la pérdida.

La §5.5 (h) y la §6.3 describían el mecanismo sin decir qué rama del flujo se
perdió, que es el dato que hace verificable la afirmación.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
k.reemplazo('La forma más severa de este patrón se observó en la primera corrida del corpus: cuando el número de '
            'pedido citado no existía, el nodo que lo busca no emitía ningún ítem',
            'La forma más severa de este patrón se observó en la primera corrida del corpus, y afectó a la rama '
            'ESTADO_PEDIDO completa: cuando el número de pedido citado no existía, el nodo que lo busca no emitía '
            'ningún ítem')
k.reemplazo('y la del 23 % de los mensajes de la primera corrida del corpus, cuando un nodo no emitió ningún ítem y '
            'el subgrafo siguiente no llegó a ejecutarse (Sección 5.2.3)',
            'y la del 23 % de los mensajes de la primera corrida del corpus —toda la rama ESTADO_PEDIDO—, cuando un '
            'nodo no emitió ningún ítem y el subgrafo siguiente no llegó a ejecutarse (Sección 5.2.3)')
k.guardar()
