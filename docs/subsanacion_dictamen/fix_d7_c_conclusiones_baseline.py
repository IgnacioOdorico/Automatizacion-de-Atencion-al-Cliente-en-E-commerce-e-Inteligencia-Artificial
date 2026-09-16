# -*- coding: utf-8 -*-
"""Dictamen del 15/09, grupo A: §6.3 y §5.4, y el baseline manual.

  A4. §6.3 atribuye bien la caída de la exhaustividad de FAQ (64,6 % sin reglas ni
      ejemplos; 39,6 % sin la base además), deja de hablar del «hallazgo más
      transferible», acota la conclusión a la configuración estudiada y discute la
      regla crítica 5 y la sensibilidad al formato. §5.4 deja de presentar el 74,0 %
      como referencia de lo alcanzable.
  A6. «Instrumento independiente», «validado de forma independiente» y
      «triangulación» se reemplazan por «acuerdo entre dos instrumentos sobre una
      misma sesión» (§3.2, §5.1.4 y §6.1), y §3.6.2 nombra el sesgo de expectativa
      del operador.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ A4: §6.3
p63 = k.par('Sobre la efectividad de GPT-4o-mini en atención al cliente')
etiqueta = p63.runs[0].text
assert etiqueta.startswith('Sobre la efectividad') and len(etiqueta) < 70, etiqueta
k.reescribir(
    p63,
    etiqueta + ' el modelo alcanzó una exactitud del 92,7 % en la clasificación de intenciones sin ajuste fino, y el '
    'diseño factorial la reprodujo un mes después en 93,3 % por mayoría de tres repeticiones. Lo que el diseño permite '
    'atribuir, para la configuración estudiada, es qué produce ese número. Las reglas de decisión y los ejemplos '
    'etiquetados del prompt explican 17,3 puntos de exactitud; la base de conocimiento de la tienda, 2,0 puntos en '
    'promedio y ninguno cuando las reglas y los ejemplos están presentes. La diferencia se concentra en la categoría FAQ, '
    'cuya exhaustividad cae de 93,8 % a 64,6 % cuando faltan las reglas y los ejemplos, aun con la base presente, y a '
    '39,6 % cuando falta también la base, porque sus mensajes pasan a clasificarse como consulta general. En esta '
    'configuración, lo que una PyME tendría que escribir y mantener para que el sistema clasifique bien es la definición '
    'operativa de sus categorías —qué temas cuentan como consulta frecuente y qué casos resueltos lo ilustran—, no su '
    'base de preguntas frecuentes. La base sigue siendo la fuente de las respuestas, y la Sección 5.2.5 muestra que, aun '
    'con ella inyectada, el modelo completa datos que la base no contiene. Esta conclusión corrige la que el trabajo había '
    'extraído de la ablación E7, cuyo diseño confundía los dos factores (Sección 3.5.6).',
    etiqueta=etiqueta)
modelo_llano = k.par('Los dos casos responden consultas sobre temas que la base no trata')   # Body Text sin rótulo
assert len(modelo_llano.runs) == 1 and not modelo_llano.runs[0].bold
k.insertar_despues(
    p63, modelo_llano,
    'Tres reservas impiden generalizar esa conclusión más allá de la configuración estudiada. La primera es que parte de '
    'las reglas codifica convenciones de desempate del mismo equipo que etiquetó el corpus: la regla crítica 5 manda '
    'clasificar como reclamo un mensaje ambiguo entre consulta frecuente y reclamo. Una parte de los 17,3 puntos puede '
    'medir, entonces, que el modelo adopta la convención del equipo, además de que clasifique mejor; el acuerdo con el '
    'evaluador independiente, que etiquetó sin esas reglas (Sección 3.5.3), acota ese riesgo pero no lo descarta. La '
    'segunda es la sensibilidad al formato: el prompt de E7, también sin base, reglas ni ejemplos, obtuvo 86,0 %, doce '
    'puntos más que C4, y difiere de él sobre todo en la forma de presentar el mensaje del cliente (Sección 5.2.4), de '
    'modo que el efecto medido vale para este formato de prompt y su magnitud podría cambiar con otro (Sclar et al., '
    '2024). La tercera es de alcance: un solo modelo, una sola familia de prompts y un corpus de 150 mensajes redactado '
    'con asistencia de un modelo de lenguaje (Sección 3.5.3). Por esas razones la conclusión se presenta como hipótesis a '
    'replicar en otras configuraciones, y no como recomendación general.')

# ------------------------------------------------------------------ A4: §5.4
k.reemplazo(
    'y la diferencia se repite en cada una de las tres repeticiones. El 74,0 % de la condición sin base, sin reglas y sin '
    'ejemplos es además una referencia documentada del desempeño alcanzable sin ajuste fino y sin contexto, que es la '
    'lectura que la literatura revisada en la Sección 2.4.2 permite anticipar. El margen que la separa de la configuración '
    'vigente mide lo que una PyME gana por escribir y mantener sus reglas y sus ejemplos, no su base de conocimiento.',
    'y la diferencia se repite en cada una de las tres repeticiones; valen, sin embargo, para este formato de prompt. El '
    '74,0 % de la condición sin base, sin reglas y sin ejemplos no es una referencia del desempeño alcanzable sin ajuste '
    'fino y sin contexto: el prompt de E7, igualmente sin esos tres bloques pero con el mensaje del cliente presentado de '
    'otra forma, obtuvo 86,0 % (Sección 5.2.4). Ambas cifras describen formatos particulares de prompt; lo que el diseño '
    'mide con validez es la diferencia entre condiciones de un mismo formato, que en esta configuración cuantifica lo que '
    'se gana por escribir y mantener las reglas y los ejemplos, y no la base de conocimiento.')

# ------------------------------------------------------------------ A6: §3.2
k.reemplazo('—validez de constructo, interna y externa, confiabilidad y triangulación de fuentes—',
            '—validez de constructo, interna y externa, y confiabilidad—')
k.reescribir(
    'Lo que el trabajo sí practica es triangulación de fuentes de evidencia',
    'Lo que el trabajo sí practica, en el sentido en que Yin (2018) lo recomienda para el estudio de caso, es que un dato '
    'relevante no descanse sobre un único instrumento. Se aplica en dos puntos, ambos verificables en el Capítulo 5, y su '
    'alcance es distinto en cada uno. El primero es el baseline de atención manual, registrado por dos instrumentos '
    'durante una misma sesión y con un mismo operador: un cronómetro por fases, que arroja 49,13 s por orden, y los '
    'incrementos entre notificaciones consecutivas que registró la base de datos, que arrojan 51,28 s. Es acuerdo entre '
    'dos instrumentos sobre una misma sesión, no una medición independiente: la coincidencia dentro del 4 % descarta un '
    'error de registro de cualquiera de los dos, pero no los sesgos que ambos comparten, como el del propio operador '
    '(Sección 3.6.2). El segundo es el conjunto de etiquetas de referencia del clasificador, construido por el equipo y '
    'contrastado a ciegas por un evaluador ajeno al trabajo sobre una submuestra aleatoria, con un κ de Cohen de 0,919 '
    '(Sección 3.5.3); aquí sí interviene una segunda persona. En ambos casos la segunda fuente pudo haber refutado a la '
    'primera y no lo hizo; ese es el valor del procedimiento y también su límite, porque ninguna de las dos alcanza la '
    'dimensión cualitativa que este trabajo dejó sin medir.')

# ------------------------------------------------------------------ A6: §5.1.4 y §6.1
k.reescribir(
    'El valor admite una validación cruzada con un instrumento independiente del cronómetro.',
    'El valor admite un contraste con un segundo instrumento, distinto del cronómetro y aplicado a la misma sesión. Las '
    'marcas temporales que el operador fue escribiendo en la base durante la medición permiten calcular el intervalo '
    'entre notificaciones de órdenes consecutivas, que es la misma magnitud marginal medida por otra vía: ese cálculo '
    'arroja 51,28 s de media (desvío 5,22 s). La diferencia de 2,15 s respecto de los 49,13 s cronometrados corresponde a '
    'los intervalos muertos entre terminar una orden y comenzar la siguiente, que el cronómetro no contabiliza y el reloj '
    'de la base sí. Los dos instrumentos coinciden dentro del 4 %. Es acuerdo entre dos instrumentos sobre una misma '
    'sesión y con un mismo operador, no una medición independiente: descarta un error de registro, pero no los sesgos '
    'que ambos comparten (Sección 3.6.2).')
k.reemplazo('y validado de forma independiente contra las marcas temporales de la base, que arrojan 51,28 s para la misma magnitud.',
            'y contrastado con un segundo instrumento sobre la misma sesión, las marcas temporales de la base, que arrojan '
            '51,28 s para la misma magnitud.')

# ------------------------------------------------------------------ A6: §3.6.2, sesgo de expectativa
mitig = k.par('Mitigación: La cronología está registrada en el repositorio.')
amenaza_modelo = k.par('Amenaza: Los resultados de tiempo (MTTD, MTTR, TMR) corresponden a un entorno Docker')
mitig_modelo = k.par('Mitigación: Se especifican las condiciones del entorno de prueba')
nueva_amenaza = k.insertar_despues(
    mitig, amenaza_modelo,
    'Amenaza: Sesgo de expectativa en el baseline manual. El operador que cronometró el procesamiento manual pertenece '
    'al equipo que formuló H1 y conocía el sentido de la comparación, de modo que pudo trabajar, aun sin proponérselo, '
    'más lento de lo que trabajaría fuera de la medición.',
    etiqueta='Amenaza:')
k.insertar_despues(
    nueva_amenaza, mitig_modelo,
    'Mitigación: Parcial. Las reglas de ejecución se fijaron antes de empezar —ritmo normal, sin preparar consultas y con '
    'descarte de toda orden interrumpida— y los tiempos los registró un cronómetro por fases, sin edición manual de los '
    'valores (Sección 3.5.5). El sesgo, si existió, agrandaría el factor de mejora, pero no alcanza para cambiar la '
    'conclusión de H1: para que el factor cayera por debajo de 10×, el tiempo manual tendría que ser del orden de 0,6 s '
    'por orden, unas ochenta veces menor que el cronometrado. La magnitud del factor sí queda expuesta al sesgo, y la '
    'réplica con operadores ajenos al equipo se plantea en el Capítulo 7.',
    etiqueta='Mitigación:')

k.guardar()
