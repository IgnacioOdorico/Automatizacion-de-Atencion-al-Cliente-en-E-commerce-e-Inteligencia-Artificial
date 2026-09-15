# -*- coding: utf-8 -*-
"""Dictamen del 14/09, obligatorias 6 y 7: pregunta, hipótesis, objetivos y encuadre.

  - §1.4.1: la reducción se pregunta solo para las órdenes, que son las que
    tienen baseline; el chatbot se contrasta contra umbrales absolutos.
  - H1 operacionalizada (un orden de magnitud), H2a con el alcance del
    contraste, H2b con la regla del límite inferior; se declara cuándo se
    adoptó cada criterio.
  - «H2» a secas y «precisión» por exactitud.
  - Objetivos: lo incorporado durante la investigación; «en tiempo real».
  - §3.2: caso instrumental según Stake (1995) y por qué Yin en un entorno
    simulado. §3.3: desarrollo iterativo.

NO es idempotente: aborta si H1 ya dice «al menos un orden de magnitud».
Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
if 'al menos un orden de magnitud' in k.par('H1:').text:
    sys.exit('ERROR: este guion ya se aplicó.')

# ============================================================ §1.4.1
q = k.reescribir('¿En qué medida la implementación de un pipeline',
    '¿En qué medida un pipeline de automatización orquestado con n8n reduce el tiempo de procesamiento de órdenes del '
    'ciclo post-venta de un e-commerce simulado respecto del procesamiento manual, medido a través de las métricas MTTD '
    '(tiempo de detección y procesamiento de órdenes) y MTTR (tiempo de resolución y notificación), y con qué tiempo de '
    'respuesta (TMR) y exactitud de clasificación atiende las consultas de los clientes un chatbot integrado al mismo '
    'sistema?')
k.insertar_despues(q, 'Las tres hipótesis se contrastan en el Capítulo 5',
    'La pregunta distingue dos términos porque solo el primero admite una comparación medida. Para el procesamiento de '
    'órdenes se cronometró un baseline manual (Sección 3.5.5), y la reducción se estima contra él. Para la atención '
    'conversacional no se midió un proceso manual equivalente, de modo que su desempeño se contrasta contra umbrales '
    'absolutos fijados por el equipo (Sección 1.4.2) y no se expresa como reducción.')

# ============================================================ §1.4.2
k.reescribir('H1:',
    'H1: El pipeline automatizado de procesamiento de órdenes reduce en al menos un orden de magnitud el tiempo que '
    'insume procesar una orden, respecto del tiempo que insume la misma tarea de forma manual, medido como baseline '
    'propio según el protocolo de la Sección 3.5.5. La hipótesis se contrasta estimando el factor de reducción con su '
    'intervalo de confianza al 95 %, y se sostiene si el límite inferior de ese intervalo es igual o mayor que 10. La '
    'formulación original calificaba la reducción de «sustancial» sin operacionalizarla; el criterio de un orden de '
    'magnitud se fijó en la revisión del trabajo, con el resultado ya conocido, y se declara así. Como criterio '
    'operativo secundario se fija que el tiempo end-to-end del pipeline se mantenga por debajo de 30 segundos.',
    etiqueta='H1:')
k.reescribir('H2a:',
    'H2a: El chatbot basado en GPT-4o-mini responde al cliente con un tiempo medio de respuesta (TMR) inferior a 10 '
    'segundos en cada una de las cuatro categorías de intención. La formulación original restringía la hipótesis a las '
    'consultas de tipo FAQ, estado de pedido y generales; se la extiende a las cuatro categorías porque el contraste '
    'siempre se ejecutó sobre los 150 mensajes del corpus, reclamos incluidos, y la extensión vuelve la hipótesis más '
    'exigente, no menos.',
    etiqueta='H2a:')
k.reescribir('H2b:',
    'H2b: El chatbot clasifica correctamente la intención del mensaje con una exactitud de al menos el 85 %. La '
    'hipótesis se sostiene si el límite inferior del intervalo de confianza de Wilson al 95 % de esa exactitud es igual '
    'o mayor que el 85 %. A lo largo del trabajo se reserva «exactitud (accuracy)» para esta métrica global y '
    '«precisión» para la métrica por clase de la Tabla 5.9, conforme la terminología de Jurafsky y Martin (2024). El '
    'umbral se fija como criterio del equipo —no deriva de un estándar publicado ni de un requerimiento de negocio '
    'externo— y se justifica en la Sección 2.2.3. La formulación original fijaba el umbral sin precisar si se '
    'contrastaba el valor puntual o el intervalo; la regla del límite inferior se explicitó en la revisión del trabajo, '
    'con la corrida del corpus ya ejecutada, y el diseño factorial de la Sección 5.2.4 la fijó por escrito antes de '
    'medir.',
    etiqueta='H2b:')
k.reemplazo('a partir de los datos recolectados durante las pruebas funcionales, la corrida de carga secuencial y la '
            'prueba de concurrencia.',
            'a partir de los datos recolectados durante la corrida de carga secuencial, la medición del baseline manual '
            'y las corridas del corpus del chatbot.')

# ============================================================ §1.5.2
k.reemplazo('y que la precisión de clasificación supere el 85 % (H2a y H2b).',
            'y que la exactitud de clasificación alcance el 85 % (H2a y H2b).')
k.reemplazo('para visualizar MTTD, MTTR y TMR en tiempo real.',
            'para visualizar MTTD, MTTR y TMR a partir de las vistas de métricas.')
k.insertar_despues('Validar el funcionamiento del sistema mediante pruebas funcionales', 'Las tres hipótesis se contrastan',
    'Tres componentes del trabajo no figuraban entre los objetivos específicos formulados al inicio y se incorporaron '
    'durante la investigación, a partir de las revisiones del documento: la medición del baseline de atención manual '
    '(Sección 3.5.5), sin la cual la hipótesis H1 no tenía término de comparación; el diseño factorial sobre el prompt '
    'del clasificador (Sección 3.5.6); y la evaluación del contenido de las respuestas (Sección 3.5.7). Se los reporta '
    'como ampliaciones del alcance y no como objetivos cumplidos, y la Tabla 6.1 no los computa.')

# ============================================================ «en tiempo real»
t61 = k.tabla(['Obj.', 'Enunciado', 'Resultado', 'Estado'])
f = k.fila(t61, 'OE4')
assert 'en tiempo real' in t61.rows[f].cells[1].text
k.celda(t61, f, 1, 'Dashboards Grafana con MTTD, MTTR y TMR')
k.reemplazo('Dashboard de métricas en tiempo real', 'Dashboards de métricas operativas')
k.reemplazo('permiten verificar en tiempo real que el sistema opera dentro de los rangos esperados',
            'permiten verificar, con la frecuencia de actualización de cada tablero, que el sistema opera dentro de '
            'los rangos esperados')
k.reemplazo('y trece paneles repartidos en dos tableros las visualizan en tiempo real.',
            'y trece paneles repartidos en dos tableros las visualizan a partir de consultas sobre la base, con '
            'excepción del panel de exactitud, que muestra un valor constante (Tabla 4.8).')

# ============================================================ «H2» a secas y «precisión»
k.reemplazo('contra las hipótesis H1 y H2.', 'contra las hipótesis H1, H2a y H2b.')
k.reemplazo('El umbral de aceptación es 85% (H2), criterio', 'El umbral de aceptación es 85 % (H2b), criterio')
k.reemplazo('lo que supera el umbral mínimo de 85% establecido en H2.', 'lo que supera el umbral del 85 % establecido en H2b.')
k.reescribir('2.2.3 Precisión en clasificación de intents', '2.2.3 Exactitud en clasificación de intents')
k.reemplazo('La evaluación de la precisión de clasificación de intenciones en chatbots',
            'La evaluación de la clasificación de intenciones en chatbots')
k.reemplazo('La precisión de clasificación del chatbot se evalúa mediante accuracy',
            'La exactitud de clasificación del chatbot se evalúa mediante accuracy')
t33 = k.tabla(['Dato', 'Fuente', 'Método de recolección'])
k.celda(t33, k.fila(t33, 'Precisión de clasificación'), 0, 'Exactitud de clasificación')
k.reescribir('5.2.3 Precisión de clasificación de intents', '5.2.3 Exactitud de clasificación de intents')
k.reemplazo('Se evaluó la precisión de clasificación comparando', 'Se evaluó la exactitud de clasificación comparando')
k.reemplazo('con el TMR promedio, la precisión de clasificación y la distribución',
            'con el TMR promedio, la exactitud de clasificación y la distribución', n=3)
t48 = k.tabla(['#', 'Panel', 'Tipo', 'Fuente de datos', 'Descripción'])
f = k.fila(t48, '9')
assert t48.rows[f].cells[1].text.strip() == 'Precisión (accuracy)'
k.celda(t48, f, 1, 'Exactitud (rotulado «Precisión (accuracy)» en el panel)')

# ============================================================ §3.2
k.reemplazo('es un e-commerce simulado que opera con el pipeline automatizado propuesto.',
    'es un e-commerce simulado que opera con el pipeline automatizado propuesto. La definición supone un contexto real, '
    'y el de este trabajo es un entorno de laboratorio. Se adopta igualmente el marco de Yin por dos razones. La '
    'primera es que aporta los criterios con que el trabajo se evalúa a sí mismo —validez de constructo, interna y '
    'externa, confiabilidad y triangulación de fuentes—, que la Sección 3.6 aplica. La segunda es que el artefacto sí '
    'es real, aunque los datos que procesa sean simulados. La consecuencia se asume: lo que el caso permite generalizar '
    'es el comportamiento del artefacto bajo las condiciones declaradas, no el de una organización (Sección 3.6.3). La '
    'investigación en ciencia del diseño, que Hevner et al. (2004) caracterizan como la construcción y evaluación de '
    'artefactos, habría sido un encuadre igualmente defendible; se la menciona para que el lector pueda situar la '
    'elección, que se tomó cuando el trabajo ya estaba estructurado como estudio de caso.')
k.reemplazo('Siguiendo la tipología de Yin (2018), se trata de un ', 'En la tipología de Stake (1995), se trata de un ')

# ============================================================ §3.3
k.reemplazo('El desarrollo se organizó en 6 etapas secuenciales, cada una', 'El desarrollo se organizó en 6 etapas, cada una')
k.reemplazo('reduce el riesgo de defectos acumulados y facilita el aislamiento de causas ante fallas.',
    'reduce el riesgo de defectos acumulados y facilita el aislamiento de causas ante fallas. La secuencia describe el '
    'orden en que cada capa quedó establecida, no un proceso lineal. El desarrollo fue iterativo, y varias etapas se '
    'reabrieron a partir de lo que mostraban las posteriores y las revisiones del documento: el esquema incorporó la '
    'tabla de alertas de stock y la columna que separa los datos medidos de los precargados después de las primeras '
    'corridas; el Flujo 2 pasó de catorce a dieciocho nodos con la incorporación de Telegram; y varias mediciones del '
    'Capítulo 5 se repitieron o ampliaron cuando se detectaron defectos de instrumentación. El historial del '
    'repositorio conserva esa secuencia.')

k.guardar()
