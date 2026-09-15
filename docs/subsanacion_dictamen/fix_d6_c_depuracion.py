# -*- coding: utf-8 -*-
"""Dictamen del 14/09: depuración de la prosa y recomendadas que quedaban.

  - Metadiscurso defensivo: «Corresponde» + verbo, «conviene» y «se declara»
    se reescriben como afirmación directa (el dictamen contó 23, 10 y 13).
  - «Costo marginal» pasa a «tiempo marginal de procesamiento», definido en §3.5.5.
  - §2.3.2: el TMR mide capacidad de respuesta, no efectividad.
  - §3.5.2: la suficiencia del tamaño muestral se declara posterior al resultado.
  - §3.6.3: la mitigación de validez externa deja de apoyarse en la reproducibilidad.
  - §7.2: el instrumento de contenido se pilotea y se extiende a GENERAL y
    ESTADO_PEDIDO; la línea de ajuste fino considera la ambigüedad de las etiquetas.

NO es idempotente: aborta si §2.3.2 ya tiene el título nuevo.
Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
if k.pars('2.3.2 TMR y capacidad de respuesta'):
    sys.exit('ERROR: este guion ya se aplicó.')

# ============================================================ metadiscurso
for viejo, nuevo in [
    ('Corresponde señalar que esa cifra proviene de un reporte de industria', 'Esa cifra proviene de un reporte de industria'),
    ('con el resultado ya conocido, y se declara así.', 'con el resultado ya conocido.'),
    ('Corresponde señalar de antemano una precisión epistemológica: los umbrales', 'Los umbrales'),
    ('Corresponde precisar el alcance de este criterio, que no se extiende a la inferencia del Flujo 2:',
     'El criterio no se extiende a la inferencia del Flujo 2:'),
    ('y conviene explicitar el razonamiento que lo sustenta.', 'y el razonamiento que lo sustenta es el siguiente.'),
    ('Conviene distinguir con precisión dos estrategias que suelen emplearse como sinónimos y no lo son.',
     'Dos estrategias que suelen emplearse como sinónimos no lo son.'),
    ('Corresponde declarar con precisión el alcance de lo implementado en este trabajo. El sistema desarrollado es multicanal',
     'El sistema desarrollado es multicanal'),
    ('no fue implementada, y se declara como línea futura en el Capítulo 7.', 'no fue implementada y queda como línea futura en el Capítulo 7.'),
    ('Para situar la contribución de este trabajo corresponde revisar qué se ha publicado sobre el problema abordado. Se '
     'declara en primer término el procedimiento seguido, de modo que tanto el alcance de la revisión como sus omisiones '
     'resulten atribuibles.',
     'Esta sección revisa lo publicado sobre el problema abordado y empieza por el procedimiento seguido, para que tanto '
     'el alcance de la revisión como sus omisiones resulten atribuibles.'),
    ('Corresponde señalar, sin embargo, una diferencia de alcance', 'Hay, sin embargo, una diferencia de alcance'),
    ('Corresponde por lo tanto revisar la literatura arbitrada de la región', 'Por eso se revisa a continuación la literatura arbitrada de la región'),
    ('aunque con datos relevados en España —condición que corresponde consignar—, llegan', 'con datos relevados en España, llegan'),
    ('y por eso conviene marcar la diferencia de alcance:', 'y por eso importa la diferencia de alcance:'),
    ('Corresponde por lo tanto explicitar el marco legal aplicable, aun cuando', 'El marco legal aplicable se explicita aun cuando'),
    ('invocado en la Sección 2.1.2 se declara allí de manera explícita.', 'invocado en la Sección 2.1.2 se reconoce allí de manera explícita.'),
    ('Corresponde declarar con precisión qué se evaluó y qué no, porque el alcance de lo medido condiciona la lectura de todo '
     'el Capítulo 5.', 'El alcance de lo medido condiciona la lectura de todo el Capítulo 5.'),
    ('La consecuencia se declara en las Secciones 5.2.2 y 6.4,', 'La consecuencia se retoma en las Secciones 5.2.2 y 6.4,'),
    ('Corresponde precisar el origen de ese criterio: la frecuencia', 'El origen de ese criterio limita su alcance: la frecuencia'),
    ('y por lo tanto se declara como supuesto de diseño y no como dato empírico.', 'y por lo tanto es un supuesto de diseño y no un dato empírico.'),
    ('Esta precisión es determinante para la comparación del Capítulo 5 y por eso se declara aquí.',
     'La distinción es determinante para la comparación del Capítulo 5.'),
    ('La corrección del contenido se declara como no establecida', 'La corrección del contenido figura como no establecida'),
    ('y esa parte se declara como limitación (Sección 5.4.1).', 'y esa parte queda como limitación (Sección 5.4.1).'),
    ('Corresponde una salvedad sobre order_items, porque el esquema y el sistema implementado no coinciden en este punto.',
     'En la tabla order_items el esquema y el sistema implementado no coinciden.'),
    (' Se declara aquí y no solo en el comentario del script del Anexo A, porque es en el cuerpo del capítulo donde el lector lo busca.', ''),
    ('Sobre received_at corresponde una precisión que acota el alcance del MTTD.', 'Sobre received_at cabe una precisión que acota el alcance del MTTD.'),
    ('más de lo que el instrumento entrega, y así se declara.', 'más de lo que el instrumento entrega.'),
    ('Conviene distinguirlos de las marcas temporales:', 'Los estados no son marcas temporales:'),
    ('y corresponde declarar qué panel aplica cuál criterio, porque de ello depende cómo se lee cada tablero.',
     'y del criterio que aplica cada panel depende cómo se lee cada tablero.'),
    ('según se declara en la Tabla 4.8.', 'según indica la Tabla 4.8.'),
    ('La consecuencia sobre los resultados de este trabajo es nula, y conviene decir por qué:',
     'La consecuencia sobre los resultados de este trabajo es nula:'),
    ('arroja dos resultados que conviene leer juntos', 'arroja dos resultados que deben leerse juntos'),
    ('El valor admite una validación cruzada que conviene explicitar, porque proviene de un instrumento independiente del cronómetro.',
     'El valor admite una validación cruzada con un instrumento independiente del cronómetro.'),
    ('Corresponde subrayar que esta cifra no es una propiedad', 'Esta cifra no es una propiedad'),
    ('; se declara como limitación en la Sección 5.4.1.', '; es una de las limitaciones de la Sección 5.4.1.'),
    ('Corresponde una precisión sobre el alcance de estas pruebas, para que no se las confunda con la evaluación del clasificador.',
     'Estas pruebas no deben confundirse con la evaluación del clasificador.'),
    ('Corresponde precisar qué mide este indicador y qué no mide. Mide que', 'El indicador mide que'),
    ('Corresponde precisar el alcance de esta validación: las 45 interacciones', 'La validación tiene un alcance acotado: las 45 interacciones'),
    ('con alcances que conviene precisar en cada caso:', 'con los alcances siguientes:'),
    ('Corresponde una salvedad de alcance: la prueba establece', 'La prueba establece'),
    ('Corresponde precisar el alcance de esa comparación en tres puntos.', 'El alcance de esa comparación se acota en tres puntos.'),
    ('pero tiene un costo que corresponde consignar:', 'pero tiene un costo:'),
    ('Lo que ese contraste no resuelve es de otro orden y conviene separarlo en tres puntos.',
     'Lo que ese contraste no resuelve es de otro orden, y se separa en tres puntos.'),
    ('Corresponde aclarar, no obstante, que no se realizó un ensayo', 'No se realizó, no obstante, un ensayo'),
    ('tiene validez estructural pero no semántica, y conviene separar ambas cosas.', 'tiene validez estructural pero no semántica.'),
]:
    k.reemplazo(viejo, nuevo)

# ============================================================ tiempo marginal
for viejo, nuevo in [
    ('es decir el costo marginal de procesar una orden adicional.',
     'es decir el tiempo marginal de procesamiento: lo que insume procesar una orden adicional, medido como tiempo de '
     'operador.'),
    ('el costo marginal de procesar una orden en el pipeline (0,063 s; n = 50)',
     'el tiempo marginal de procesamiento de una orden en el pipeline (0,063 s; n = 50)'),
    ('La reducción del costo marginal de procesamiento de una orden', 'La reducción del tiempo marginal de procesamiento de una orden'),
    ('el costo marginal de procesar una orden en el pipeline (0,063 s end-to-end; n = 50)',
     'el tiempo marginal de procesamiento de una orden en el pipeline (0,063 s end-to-end; n = 50)'),
    ('como comparación de costos marginales,', 'como comparación de tiempos marginales de procesamiento,'),
    ('que miden costo marginal de procesamiento y no latencia percibida', 'que miden tiempo marginal de procesamiento y no latencia percibida'),
]:
    k.reemplazo(viejo, nuevo)

# ============================================================ §2.3.2, §3.5.2, §3.6.3
k.reescribir('2.3.2 TMR como métrica de efectividad', '2.3.2 TMR y capacidad de respuesta')
k.reemplazo('El TMR (Tiempo Medio de Respuesta) es la métrica operativa central para evaluar la efectividad de un sistema de '
            'atención.',
            'El TMR (Tiempo Medio de Respuesta) mide la capacidad de respuesta de un sistema de atención, no su efectividad: '
            'la rapidez es una dimensión de la calidad de servicio y no garantiza que la respuesta sea correcta, como muestra '
            'la Sección 5.2.5.')
k.reemplazo('Lo que habilita el contraste no es el margen nominal sino la precisión efectivamente alcanzada:',
            'El argumento que sigue es posterior al resultado, porque usa la proporción observada: lo que habilita el '
            'contraste no es el margen nominal sino la precisión efectivamente alcanzada:')
k.reemplazo('El tamaño muestral es, por lo tanto, suficiente para el contraste que el trabajo se propone, y así se reporta.',
            'El tamaño muestral resultó suficiente para el contraste, pero esa suficiencia se estableció después de medir y no '
            'mediante un cálculo previo.')
k.reescribir('Mitigación: El sistema y su metodología de prueba son reproducibles',
    'Mitigación: Parcial. La reproducibilidad del entorno permite replicar el estudio sobre datos reales, pero no convierte '
    'los resultados en generalizables. Lo que el trabajo hace es acotar sus conclusiones al comportamiento del artefacto '
    'bajo las condiciones declaradas (Sección 3.2) y plantear un piloto en una PyME real como línea futura (Capítulo 7). Los '
    'escenarios de prueba cubren los casos límite más relevantes —órdenes con stock y sin stock, entradas inválidas y '
    'mensajes ambiguos—, lo que fortalece la validez interna de las pruebas y no la externa.', etiqueta='Mitigación:')

# ============================================================ §7.2
k.reemplazo('que es la función que el diseño factorial no mide.',
            'que es la función que el diseño factorial no mide. Antes de aplicarse, el instrumento debería pilotearse sobre '
            'una submuestra, y extenderse a las respuestas de las categorías GENERAL y ESTADO_PEDIDO, que la evaluación de la '
            'Sección 3.5.7 dejó fuera.')
k.reemplazo('sino separar el aporte de cada bloque de reglas y ejemplos.',
            'sino separar el aporte de cada bloque de reglas y ejemplos. Además, los errores del clasificador se concentran en '
            'las mismas fronteras en que el evaluador independiente discrepó de las etiquetas de referencia (Sección 5.2.3), '
            'lo que sugiere un techo impuesto por la ambigüedad de las etiquetas más que por la capacidad del modelo.')

k.guardar()
