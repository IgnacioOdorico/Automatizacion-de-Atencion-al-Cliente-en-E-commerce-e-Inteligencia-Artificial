# -*- coding: utf-8 -*-
"""Ajustes de redacción encontrados en la lectura de control de la segunda pasada.

  1. §4.4.3: la base se lee en cada llamada; «recuperado» sugería RAG (§2.2.4).
  2. §2.4.1: la afirmación sobre el giro de la literatura se acota a lo que
     sostienen las dos fuentes citadas.
  3. §2.4.1: el argumento de Air Canada, sin la repetición «respondiera… respuestas».

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
k.reemplazo('en el que se inyecta el contenido de la tabla faq_responses recuperado en tiempo de ejecución,',
            'en el que se inserta el contenido completo de la tabla faq_responses, leído en cada llamada,')
k.reemplazo('La literatura posterior a la difusión de los modelos de lenguaje de gran escala desplaza la pregunta de la '
            'utilidad a la confiabilidad.',
            'Con la difusión de los modelos de lenguaje de gran escala aparece una pregunta distinta, la de la confiabilidad '
            'de lo que el asistente afirma.')
k.reemplazo('y rechazó el argumento de que el asistente respondiera por sí mismo de sus respuestas.',
            'y rechazó el argumento de que el asistente fuera responsable de su propia información.')
k.guardar()
