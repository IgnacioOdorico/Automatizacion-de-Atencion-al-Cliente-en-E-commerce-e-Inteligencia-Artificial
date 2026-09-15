# -*- coding: utf-8 -*-
"""Costuras que dejó la pasada del dictamen del 14/09, encontradas en la lectura de control.

  1. §6.1 citaba la pregunta de investigación anterior a la reformulación de §1.4.1.
  2. El objetivo general contrastaba «los tiempos operativos» contra el proceso
     manual, cuando solo las órdenes tienen baseline.
  3. §5.3: «ese intervalo» quedaba referido a la frase del criterio operativo.
  4. §7.2: la línea de Tiendanube remitía al «Capítulo 7» desde el propio Capítulo 7.

NO es idempotente: aborta si §6.1 ya cita la pregunta vigente.
Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
pregunta = k.par('¿En qué medida un pipeline de automatización orquestado con n8n').text.strip()
if len(k.pars('La presente investigación planteó la siguiente pregunta: ¿En qué medida un pipeline')) == 1:
    sys.exit('ERROR: este guion ya se aplicó.')

k.reescribir('La presente investigación planteó la siguiente pregunta:',
             'La presente investigación planteó la siguiente pregunta: ' + pregunta)
k.reemplazo('y contrastando los resultados con la hipótesis de reducción sustancial de los tiempos operativos respecto al '
            'proceso manual.',
            'contrastando el tiempo de procesamiento de órdenes con el del proceso manual y el desempeño del chatbot con '
            'umbrales absolutos.')
k.reemplazo('El límite inferior de ese intervalo, 686×, supera holgadamente el orden de magnitud que fija el criterio.',
            'El límite inferior del intervalo del factor, 686×, supera holgadamente el orden de magnitud que fija el '
            'criterio de H1.')
k.reemplazo('y que la variante de producción del Capítulo 7 no contempla.',
            'y que la variante de producción de la Sección 7.1 no contempla.')
k.guardar()
