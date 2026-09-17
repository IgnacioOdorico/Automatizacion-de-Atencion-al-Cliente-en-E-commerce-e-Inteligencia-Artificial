# -*- coding: utf-8 -*-
"""Regresiones que dejó la pasada de la auditoría del 17/09.

  - El resumen pasó de 300 palabras al incorporar el tercer caso de la §5.2.5:
    se comprime sin perder ningún dato.
  - Tres párrafos nuevos usaban «versión anterior», que las revisiones previas
    habían sacado del texto expuesto: dos hablaban de otra cosa (una cifra y un
    nombre de archivo) y el tercero, del workflow con que corrió el corpus.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ resumen dentro de las 300 palabras
k.reemplazo('Bajo 20 solicitudes casi simultáneas no hubo sobreventa, pero el 40,8 % de las órdenes quedó sin '
            'procesar y sin aviso.',
            'Bajo 20 solicitudes casi simultáneas no hubo sobreventa, pero el 40,8 % de las órdenes quedó sin '
            'procesar ni aviso.')
k.reemplazo('Un diseño factorial con tres repeticiones mostró que esa exactitud depende de las reglas y los '
            'ejemplos del prompt, que aportan 17,3 puntos, y no de la base de conocimiento, que aporta 2,0.',
            'Un diseño factorial con tres repeticiones mostró que esa exactitud depende de las reglas y los '
            'ejemplos del prompt (17,3 puntos) y no de la base de conocimiento (2,0).')
k.reemplazo('La corrección del contenido de las respuestas no quedó establecida: dos evaluadores no alcanzaron un '
            'acuerdo suficiente, y una verificación automática encontró que 2 de las 18 respuestas con datos '
            'concretos afirman alguno ausente de la base, y un tercer caso, fuera del alcance de esa regla, '
            'llevaría la proporción a 3 de 18.',
            'La corrección del contenido no quedó establecida: dos evaluadores no alcanzaron acuerdo suficiente, y '
            'una verificación automática halló 2 de 18 respuestas con datos que la base no respalda, o 3 de 18 '
            'contando un caso fuera de su alcance.')

# ------------------------------------------------------------------ «versión anterior» fuera del texto expuesto
k.reemplazo('se proyectó la exactitud que declaraba la versión anterior del trabajo, de alrededor del 90 %,',
            'se proyectó una exactitud de alrededor del 90 %, que era la que el trabajo declaraba antes de medirla,')
k.reemplazo('se ejecutó sobre una versión anterior, de catorce nodos:',
            'se ejecutó sobre el workflow de catorce nodos que estaba publicado entonces:')
k.reemplazo('El nombre del archivo conserva el rótulo «Omnicanal» de una versión anterior del trabajo y no refleja '
            'la delimitación de la Sección 2.3.1',
            'El nombre del archivo conserva el rótulo «Omnicanal» con que fue creado y no refleja la delimitación '
            'de la Sección 2.3.1')

k.guardar()
