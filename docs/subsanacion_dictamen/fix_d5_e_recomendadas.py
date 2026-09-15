# -*- coding: utf-8 -*-
"""Dictamen del 14/09: obligatorias 3 y 5 (resto) y recomendadas sin reestructurar.

  - Resumen de 250 a 300 palabras y abstract espejo, con el factorial.
  - Referencias verificadas: métodos estadísticos (Wilson, McNemar, Holm,
    Mann y Whitney, Welch, Fieller, Cohen), corpus (CLINC150, Banking77,
    SNIPS), Stake (1995) y Hevner et al. (2004).
  - APA: et al. desde la primera cita con tres o más autores; «y» en citas
    narrativas.
  - §3.6 ampliada: independencia prompt-corpus (cronología, similitud,
    sensibilidad), temperatura y alias del modelo, operador único.
  - E6 (§3.5.7 y §5.2.5): sin prueba piloto, alcance de la evaluación,
    horarios en las reglas y desobediencia a «consultar con el equipo».
  - Capítulo 7: validar la etiqueta del modelo; líneas futuras nuevas.
  - Declaración y Anexo J: URL del repositorio y etiqueta de la versión.

NO es idempotente: aborta si la lista de referencias ya incluye a Wilson (1927).
Se ejecuta desde la raíz del repositorio.
"""
import sys
import copy

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
if k.pars('Wilson, E. B. (1927)'):
    sys.exit('ERROR: este guion ya se aplicó.')

URL = 'https://github.com/IgnacioOdorico/Automatizacion-de-Atencion-al-Cliente-en-E-commerce-e-Inteligencia-Artificial'
ETIQUETA = 'entrega-2026-09'

# ============================================================ resumen y abstract
RES = [
    'El trabajo aborda el procesamiento manual del ciclo post-venta en PyMEs argentinas de comercio electrónico. Se '
    'pregunta en qué medida un pipeline orquestado con n8n reduce el tiempo de procesamiento de órdenes respecto del '
    'proceso manual, y con qué tiempo de respuesta y exactitud atiende consultas un chatbot integrado.',
    'Sobre un e-commerce simulado y en contenedores Docker se implementaron un pipeline de órdenes de quince nodos y un '
    'chatbot sobre dos canales —uno simulado con entrega SMTP local y Telegram real— que clasifica intenciones con '
    'GPT-4o-mini. El diseño es un estudio de caso instrumental con métricas registradas automáticamente.',
    'Sobre 50 órdenes, el tiempo end-to-end fue de 0,063 s, frente a 49,13 s por orden cronometrados en el proceso '
    'manual: un factor cercano a 780× (IC 95 % por el teorema de Fieller: 686× a 875×), que se lee como orden de '
    'magnitud bajo condiciones de laboratorio y no como cota. Bajo 20 solicitudes simultáneas no hubo sobreventa, pero '
    'el 40,8 % de las órdenes quedó sin procesar y sin aviso. El chatbot respondió en 1,47 s de media y clasificó con '
    'una exactitud del 92,7 % (IC 95 % de Wilson: 87,3 % a 95,9 %). Un diseño factorial con tres repeticiones mostró que '
    'esa exactitud depende de las reglas y los ejemplos del prompt, que aportan 17,3 puntos, y no de la base de '
    'conocimiento de la tienda, que aporta 2,0. La corrección del contenido de las respuestas no quedó establecida: dos '
    'evaluadores no alcanzaron un acuerdo suficiente, y una verificación automática encontró que 2 de las 18 respuestas '
    'con datos concretos afirman alguno ausente de la base. Las tres hipótesis se sostienen dentro de los alcances '
    'declarados.',
]
ABS = [
    'This work addresses the manual handling of the post-sale cycle in Argentine e-commerce SMEs. It asks to what '
    'extent a pipeline orchestrated with n8n reduces order-processing time with respect to the manual process, and with '
    'what response time and accuracy an integrated chatbot handles customer queries.',
    'On a simulated store deployed in Docker containers, an order pipeline of fifteen nodes and a chatbot over two '
    'channels —a simulated one with local SMTP delivery, and real Telegram— were implemented, the chatbot classifying '
    'intents with GPT-4o-mini. The design is an instrumental case study with automatically recorded metrics.',
    'Over 50 orders, end-to-end time was 0.063 s, against 49.13 s per order timed for the manual process: a factor '
    'close to 780× (Fieller 95 % CI: 686× to 875×), read as an order of magnitude under laboratory conditions and not '
    'as a bound. Under 20 simultaneous requests there was no overselling, but 40.8 % of the orders were left '
    'unprocessed and without warning. The chatbot replied in 1.47 s on average and classified intents with an accuracy '
    'of 92.7 % (Wilson 95 % CI: 87.3 % to 95.9 %). A factorial design with three repetitions showed that this accuracy '
    'depends on the rules and examples in the prompt, which contribute 17.3 points, and not on the store knowledge base, '
    'which contributes 2.0. The correctness of the replies’ content was not established: two raters did not reach '
    'sufficient agreement, and an automatic check found that 2 of the 18 replies containing concrete data state at '
    'least one that is absent from the knowledge base. The three hypotheses hold within the declared scope.',
]
nres = sum(len(x.split()) for x in RES)
nabs = sum(len(x.split()) for x in ABS)
assert 250 <= nres <= 300, 'resumen: %d palabras' % nres
assert 230 <= nabs <= 320, 'abstract: %d palabras' % nabs
for pref, texto in zip(['El presente trabajo aborda el problema del procesamiento manual',
                        'Se diseñó e implementó una solución compuesta por dos flujos',
                        'Los resultados obtenidos muestran un MTTD promedio'], RES):
    k.reescribir(pref, texto)
for pref, texto in zip(['This work addresses the manual handling of the post-sale cycle',
                        'A solution was designed and implemented as two workflows',
                        'The results show a mean MTTD'], ABS):
    k.reescribir(pref, texto)
print('resumen: %d palabras · abstract: %d palabras' % (nres, nabs))

# ============================================================ referencias
MODELO_REF = k.par('Parikh, S., Tiwari, M.')
assert MODELO_REF.runs[1].italic and not MODELO_REF.runs[0].italic


def referencia(despues_de, partes):
    """partes: lista de (texto, cursiva). Párrafo nuevo con el formato de Parikh et al."""
    ancla = k.par(despues_de)
    p = k.insertar_despues(ancla, MODELO_REF, partes[0][0])
    p.runs[0].italic = partes[0][1] or None
    for texto, cursiva in partes[1:]:
        r = p.add_run(texto)
        if MODELO_REF.runs[0]._r.rPr is not None:
            r._r.insert(0, copy.deepcopy(MODELO_REF.runs[0]._r.rPr))
        r.italic = True if cursiva else None
    return p


referencia('Cámara Argentina de Comercio Electrónico. (2025).', [
    ('Casanueva, I., Temčinas, T., Gerz, D., Henderson, M., & Vulić, I. (2020). Efficient intent detection with dual '
     'sentence encoders. En ', False),
    ('Proceedings of the 2nd Workshop on Natural Language Processing for Conversational AI', True),
    (' (pp. 38–45). Association for Computational Linguistics. https://doi.org/10.18653/v1/2020.nlp4convai-1.5', False)])
cohen = referencia('Cochran, W. G. (1977).', [
    ('Cohen, J. (1960). A coefficient of agreement for nominal scales. ', False),
    ('Educational and Psychological Measurement, 20', True),
    ('(1), 37–46. https://doi.org/10.1177/001316446002000104', False)])
referencia('Cohen, J. (1960).', [
    ('Coucke, A., Saade, A., Ball, A., Bluche, T., Caltagirone, F., Lavril, T., Primet, M., & Dureau, J. (2018). ', False),
    ('Snips Voice Platform: An embedded spoken language understanding system for private-by-design voice interfaces', True),
    (' (arXiv:1805.10190). arXiv. https://arxiv.org/abs/1805.10190', False)])
referencia('Dumas, M., La Rosa, M.', [
    ('Fieller, E. C. (1954). Some problems in interval estimation. ', False),
    ('Journal of the Royal Statistical Society: Series B (Methodological), 16', True),
    ('(2), 175–185. https://doi.org/10.1111/j.2517-6161.1954.tb00159.x', False)])
referencia('Hernández Sampieri, R.', [
    ('Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. ', False),
    ('MIS Quarterly, 28', True),
    ('(1), 75–106. https://doi.org/10.2307/25148625', False)])
referencia('Hevner, A. R.', [
    ('Holm, S. (1979). A simple sequentially rejective multiple test procedure. ', False),
    ('Scandinavian Journal of Statistics, 6', True),
    (', 65–70. https://www.jstor.org/stable/4615733', False)])
referencia('Landis, J. R., & Koch, G. G. (1977).', [
    ('Larson, S., Mahendran, A., Peper, J. J., Clarke, C., Lee, A., Hill, P., Kummerfeld, J. K., Leach, K., Laurenzano, '
     'M. A., Tang, L., & Mars, J. (2019). An evaluation dataset for intent classification and out-of-scope prediction. '
     'En ', False),
    ('Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International '
     'Joint Conference on Natural Language Processing (EMNLP-IJCNLP)', True),
    (' (pp. 1311–1316). Association for Computational Linguistics. https://doi.org/10.18653/v1/D19-1131', False)])
referencia('Luo, H., Liu, P., & Esping, S. (2023).', [
    ('Mann, H. B., & Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger '
     'than the other. ', False),
    ('The Annals of Mathematical Statistics, 18', True),
    ('(1), 50–60. https://doi.org/10.1214/aoms/1177730491', False)])
referencia('Mann, H. B., & Whitney, D. R. (1947).', [
    ('McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. ',
     False),
    ('Psychometrika, 12', True),
    ('(2), 153–157. https://doi.org/10.1007/BF02295996', False)])
referencia('Ramos De Santis, P. (2024).', [
    ('Stake, R. E. (1995). ', False),
    ('The art of case study research', True),
    ('. SAGE Publications.', False)])
referencia('Verhoef, P. C., Kannan, P. K.', [
    ('Welch, B. L. (1947). The generalization of ‘Student’s’ problem when several different population variances are '
     'involved. ', False),
    ('Biometrika, 34', True),
    ('(1–2), 28–35. https://doi.org/10.1093/biomet/34.1-2.28', False)])
referencia('WhatsApp LLC. (2025).', [
    ('Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. ', False),
    ('Journal of the American Statistical Association, 22', True),
    ('(158), 209–212. https://doi.org/10.1080/01621459.1927.10502953', False)])

# ============================================================ APA
k.reemplazo('Alderete, Jones y Motta (2017) estiman', 'Alderete et al. (2017) estiman')
k.reemplazo('Fondevila-Gascón, Huamanchumo, Martín-Guart y Gutiérrez-Aragón (2024), publicados',
            'Fondevila-Gascón et al. (2024), publicados')
k.reemplazo('Pachas-Santos, Calderón-Vilca y Cárdenas-Mariño (2023) construyen', 'Pachas-Santos et al. (2023) construyen')
k.reemplazo('Bravo Maruri, Ramírez Reina, Orozco Lara y Espinoza Martínez (2025) documentan',
            'Bravo Maruri et al. (2025) documentan')
k.reemplazo('documentada por Womack & Jones (2003)', 'documentada por Womack y Jones (2003)')

# ============================================================ §3.6
AM1 = k.par('Amenaza: Las métricas MTTD, MTTR y TMR fueron adaptadas')
MI1 = k.par('Mitigación: Se operacionalizaron explícitamente')


def par_amenaza(despues_de, amenaza, mitigacion):
    a = k.insertar_despues(despues_de, AM1, amenaza)
    return k.insertar_despues(a, MI1, mitigacion)


par_amenaza(MI1,
    'Amenaza: La exactitud se mide contra etiquetas de referencia construidas por el mismo equipo que escribió el '
    'prompt, y la corrección del contenido de las respuestas no quedó medida, de modo que clasificar bien y responder '
    'bien no coinciden.',
    'Mitigación: El etiquetado se congeló antes de ejecutar el modelo y un evaluador independiente lo contrastó sobre '
    'una submuestra (κ = 0,919, Sección 3.5.3). La corrección del contenido se declara como no establecida en las '
    'Secciones 5.2.5 y 6.4, y el alcance semántico de las métricas de tiempo se acota en la Sección 4.3.3.')
par_amenaza(k.par('Mitigación: Se especifican las condiciones del entorno de prueba'),
    'Amenaza: Independencia entre el prompt y el corpus. El mismo equipo escribió las reglas y los ejemplos del prompt y '
    'los 150 mensajes del corpus, y un corpus redactado a la medida de las reglas inflaría la exactitud.',
    'Mitigación: La cronología está registrada en el repositorio. Las reglas de clasificación, las reglas críticas y los '
    'ejemplos del prompt medido son idénticos a los del commit ebbd17c, del 22 de abril de 2026, y el corpus se congeló '
    'el 10 de agosto (commit 77a5a04), 110 días después. La similitud máxima entre un ejemplo del prompt y un mensaje '
    'del corpus es de 0,89, en un único par —«cuánto tarda el envío a córdoba?» frente a «cuanto sale el envio a '
    'cordoba?»—, y la siguiente es de 0,66; el análisis de sensibilidad de la Sección 5.2.4 excluye ese mensaje y '
    'ninguna conclusión cambia. La cronología no descarta que el equipo haya redactado el corpus con las categorías del '
    'prompt en mente, y esa parte de la amenaza queda sin mitigar.')
par_amenaza(k.par('Mitigación: El sistema y su metodología de prueba son reproducibles'),
    'Amenaza: El baseline manual se midió sobre un único operador que conocía el procedimiento, y el corpus, las reglas '
    'del prompt y la base de conocimiento los escribió el propio equipo: ninguno representa a una PyME real.',
    'Mitigación: Ambas condiciones se declaran como limitaciones (Secciones 5.4.1 y 6.4), y la replicación con varios '
    'operadores y con el tráfico de una tienda en operación se plantea en el Capítulo 7.')
par_amenaza(k.par('Mitigación: Todas las pruebas se realizaron en una ventana de tiempo acotada'),
    'Amenaza: La clasificación depende de un modelo invocado por un alias, que el proveedor puede asociar a otra '
    'versión, y de la temperatura por defecto de la API, que es 1, de modo que una corrida no se reproduce exactamente.',
    'Mitigación: El diseño factorial repite cada condición tres veces y reporta la variabilidad entre repeticiones '
    '(Sección 5.2.4); los guiones, los manifiestos y la huella de cada prompt se versionan en el repositorio. La versión '
    'del modelo detrás del alias no queda registrada, y esa parte se declara como limitación (Sección 5.4.1).')

# ============================================================ E6
k.reemplazo('y, cuando un mismo evaluador tiene dos corridas válidas, su acuerdo consigo mismo.',
    'y, cuando un mismo evaluador tiene dos corridas válidas, su acuerdo consigo mismo. La rúbrica se aplicó sin una '
    'prueba piloto previa, omisión a la que se atribuye en parte el bajo acuerdo que reporta la Sección 5.2.5. La '
    'evaluación se limitó a las respuestas de tipo FAQ, porque son las únicas que el prompt instruye a basar en la base '
    'de conocimiento; las respuestas a las demás categorías, que el modelo también redacta —solas en GENERAL y '
    'acompañadas de los datos del pedido o del ticket en ESTADO_PEDIDO y RECLAMO—, no se evaluaron.')
k.reemplazo('el horario de atención y el plazo de reintegro. La inyección del contexto no impide',
    'el horario de atención y el plazo de reintegro. Los dos casos tienen además una explicación en el propio prompt '
    '(Anexo H). Las reglas de clasificación enumeran «horarios de atención» entre los temas de consulta frecuente, pero '
    'la base no tiene ninguna entrada sobre horarios; y el bloque de la base instruye al modelo a decir que va a '
    'consultar con el equipo cuando la pregunta no está cubierta, instrucción que en los dos casos no cumplió. La '
    'inyección del contexto no impide')

# ============================================================ Capítulo 7
k.insertar_despues('Aislar el componente de red del tiempo de respuesta:', 'Aislar el componente de red del tiempo de respuesta:',
    'Validar la etiqueta del modelo antes de registrar la interacción: si el clasificador devuelve una categoría fuera '
    'del vocabulario admitido, el flujo debería derivar el mensaje a revisión humana y registrar el caso, en lugar de '
    'dejar que la restricción de integridad rechace la escritura sin aviso (Sección 5.2.4). La misma regla vale para el '
    'Flujo 1: toda ejecución que termine sin una respuesta explícita debería devolver un error al emisor y marcar la '
    'orden, en lugar de responder HTTP 200 sin cuerpo (Secciones 5.1.1 y 5.1.3).')
k.reescribir('Fine-tuning del modelo de IA con datos reales de conversaciones de clientes',
    'Ajuste fino del modelo con conversaciones reales de clientes, solo si crece el número de categorías o cambia el '
    'dominio: con cuatro categorías, el prompt con reglas y ejemplos ya alcanza entre 93 % y 94 % de exactitud (Sección '
    '5.2.4), de modo que la primera línea de mejora no es el ajuste fino sino separar el aporte de cada bloque de reglas '
    'y ejemplos.')
k.reemplazo('Aplicado a las respuestas de las dos condiciones de la Sección 5.2.4, ese instrumento permitiría establecer '
            'si el contexto mejora también la corrección de lo que el cliente recibe, y no solo la clasificación de lo que '
            'pregunta.',
            'Aplicado a las respuestas de las condiciones con y sin base de conocimiento de la Sección 5.2.4, ese '
            'instrumento permitiría establecer si la base mejora la corrección de lo que el cliente recibe, que es la '
            'función que el diseño factorial no mide.')
ultimo = k.par('Evaluación de la corrección del contenido de las respuestas con un instrumento')
for texto in [
        'Descomposición del factor de reglas y ejemplos: un diseño que separe las reglas de clasificación, las reglas '
        'críticas y los ejemplos permitiría establecer cuál produce el efecto de 17,3 puntos de la Sección 5.2.4, y '
        'verificar la hipótesis, surgida de la comparación con la ablación E7, de que la forma de presentar el mensaje del '
        'cliente también incide en la clasificación.',
        'Piloto en una PyME real: desplegar el sistema sobre el tráfico de una tienda en operación, con su catálogo, su '
        'base de conocimiento y mensajes de clientes reales, para medir las métricas fuera del laboratorio y contrastar '
        'la distribución de intenciones que la Sección 3.5.2 declara como supuesto.',
        'Baseline conversacional: medir el tiempo de respuesta y la exactitud de una atención manual por chat sobre el '
        'mismo corpus, de modo que el TMR del chatbot tenga un término de comparación medido, como lo tiene el '
        'procesamiento de órdenes.',
        'Implementación alternativa: construir el mismo sistema en código convencional o sobre otro orquestador y '
        'comparar el esfuerzo de desarrollo, el mantenimiento y el manejo de fallas, que es la forma de poner a prueba la '
        'afirmación de la Sección 6.3 sobre la barrera de adopción de n8n.',
        'Pruebas de inyección de instrucciones: someter al chatbot a un conjunto de mensajes diseñados para alterar sus '
        'instrucciones (Perez & Ribeiro, 2022) y medir con qué frecuencia responde fuera de su rol o de la política de la '
        'tienda.',
        'Integración con Tiendanube, una de las plataformas que la Sección 1.1 menciona entre las que usan las PyMEs '
        'argentinas y que la variante de producción del Capítulo 7 no contempla.']:
    ultimo = k.insertar_despues(ultimo, 'Análisis de sentimiento sobre los mensajes de RECLAMO', texto)

# ============================================================ repositorio
k.reemplazo('de modo que toda cifra publicada pueda ser recalculada de forma independiente.',
    'de modo que toda cifra publicada pueda ser recalculada de forma independiente. El repositorio es público y está '
    'disponible en %s; la versión que corresponde a este documento se identifica con la etiqueta %s (Anexo J).'
    % (URL, ETIQUETA))
k.reemplazo('acredita el carácter ciego del procedimiento descripto en la Sección 3.5.3.',
    'acredita el carácter ciego del procedimiento descripto en la Sección 3.5.3. El repositorio está disponible en %s. '
    'La etiqueta %s identifica la versión de los datos, los guiones y los workflows que corresponde a este documento, '
    'y cada experimento se encuentra en su propio directorio bajo experiments (E1 a E8 y PF).' % (URL, ETIQUETA))

k.guardar()
