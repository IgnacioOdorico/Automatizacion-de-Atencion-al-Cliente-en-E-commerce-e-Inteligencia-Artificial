# -*- coding: utf-8 -*-
"""Dictamen del 15/09, grupo B: extensión y redundancia.

  §5.3: el punto de H1 queda como estimación y remite a §5.4; se retira la precisión
        sobre H2b por subcategoría, que repetía §5.2.3 y §5.4.1 (b).
  §5.4: se retira la comparación con la propagación simplificada del intervalo.
  §5.4.1 (b): sin repetir las cifras de la Tabla 5.9.
  §6.1: remite a §5.4 en lugar de repetir la salvedad del factor.
  §6.4: enumeración breve; el análisis está en §3.6 y §5.4.1.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

k.reescribir(
    '• H1 se sostiene en sus dos términos.',
    '• H1, como objetivo de estimación: el tiempo marginal de procesamiento de una orden en el pipeline (0,063 s; n = 50) '
    'resulta unas 780 veces menor que el del procesamiento manual, medido en 49,13 s por orden, con un intervalo al 95 % '
    'de 686× a 875× por el teorema de Fieller. Ambos términos miden la misma magnitud, el tiempo que insume una orden '
    'adicional (Sección 3.5.5). El límite inferior supera la referencia de un orden de magnitud, y el tiempo end-to-end '
    'representa el 0,2 % del umbral operativo de 30 segundos. El alcance del factor se discute en la Sección 5.4.')
k.eliminar('Sobre el contraste de H2b cabe una precisión metodológica adicional.')
k.reemplazo(
    ' Se consigna, por transparencia del cálculo, que la propagación simplificada —tratar el denominador automatizado como '
    'constante y arrastrar solo la incertidumbre del baseline— arroja 687× a 872×: la diferencia entre ambos '
    'procedimientos es inferior al 0,4 % porque el desvío del término automatizado (0,005 s sobre n = 50) es cuatro '
    'órdenes de magnitud menor que el del término manual.', '')

pb = k.par('(b) Desempeño por subcategoría')
etiqueta = pb.runs[0].text
assert etiqueta.startswith('(b) Desempeño por subcategoría'), etiqueta
k.reescribir(
    pb,
    etiqueta + ' ninguna clase queda por debajo del 85 % en precisión ni en exhaustividad (Tabla 5.9), pero GENERAL, '
    'definida como categoría residual, concentra los casos de frontera con FAQ: combina la exhaustividad más alta con la '
    'precisión más baja. La Sección 5.2.4 muestra que esa frontera es la más sensible a las reglas y los ejemplos del '
    'prompt, y la mitigación más directa es ampliar los ejemplos con casos de frontera entre GENERAL y FAQ, que hoy no '
    'están representados, sin requerir ajuste fino del modelo.',
    etiqueta=etiqueta)

k.reemplazo('La Sección 5.4 explica por qué ese factor se lee como una diferencia de casi tres órdenes de magnitud bajo las '
            'condiciones del laboratorio y no como una cota.',
            'Ese factor se lee como una diferencia de casi tres órdenes de magnitud en condiciones de laboratorio, no como '
            'una cota (Sección 5.4).')

k.reescribir(
    'Las limitaciones del trabajo se documentan en detalle en la Sección 5.4.1',
    'Las limitaciones se analizan en la Sección 5.4.1 y en las amenazas a la validez de la Sección 3.6; aquí se '
    'enuncian: (i) entorno de laboratorio local con datos simulados, más favorable que un despliegue productivo; (ii) '
    'baseline manual medido sobre un único operador del equipo; (iii) contraste de tiempos marginales de procesamiento, '
    'no de latencia percibida; (iv) corpus de 150 mensajes sobre cuatro categorías, redactado con asistencia de un modelo '
    'de lenguaje y con una distribución supuesta, no observada; (v) corrección del contenido no establecida: los jueces '
    'no alcanzaron un acuerdo suficiente, y la verificación automática, una cota inferior, encontró que 2 de las 18 '
    'respuestas de tipo FAQ con datos concretos afirman alguno ausente de la base; (vi) pérdida silenciosa del 40,8 % de '
    'las órdenes bajo concurrencia, de modo que el desempeño vale en régimen secuencial; (vii) dependencia de un '
    'proveedor externo de inferencia, con transferencia internacional de datos (Sección 2.5); (viii) exactitud medida '
    'con la temperatura por defecto, sobre un alias de modelo y con reglas y ejemplos escritos por el mismo equipo que '
    'preparó el corpus; y (ix) ninguno de los dos flujos advierte sus propias fallas. Estas limitaciones no invalidan '
    'las conclusiones dentro del alcance declarado, pero acotan su extrapolación a entornos de producción.')

k.guardar()
