# -*- coding: utf-8 -*-
"""Dictamen del 14/09, recomendada «actualizar el estado del arte» y marco teórico (f).

  - §2.1.2: literatura académica sobre plataformas low-code.
  - §2.2.4 (nueva): inyección de contexto frente a generación aumentada por
    recuperación (Lewis et al., 2020) y alucinación.
  - §2.2.5 (nueva): evaluación de texto generado, no determinismo y acuerdo entre
    evaluadores.
  - §2.4: búsqueda actualizada; LLM en atención al cliente 2024–2026 (§2.4.1),
    intención con LLM (§2.4.2), anclaje y alucinación (§2.4.3, nueva);
    contribución de integración (§2.4.6); Tabla 2.1 con tres filas nuevas.
  - «Recuperación de contexto» pasa a «inyección de contexto».
  - Huang et al. en su versión publicada (2025).
  - §5.2.4 y §5.2.5 remiten a la literatura nueva.
  - Catorce referencias verificadas (Crossref, ACL Anthology, NeurIPS, arXiv,
    decisión del tribunal).

NO es idempotente: aborta si ya existe §2.2.4.
Se ejecuta desde la raíz del repositorio.
"""
import sys
import copy

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
if k.pars('2.2.4 '):
    sys.exit('ERROR: este guion ya se aplicó.')

H3 = k.par('2.2.3 Exactitud en clasificación de intents')
PRIMERO = k.par('Para la implementación de este proyecto se seleccionó n8n')          # First Paragraph
CUERPO = k.par('La elección de n8n sobre alternativas comerciales')                    # Body Text

# ============================================================ §2.1.2 low-code
k.insertar_despues(CUERPO, CUERPO,
    'La elección se inscribe en una categoría de herramientas que la literatura de sistemas de información estudia como '
    'plataformas de desarrollo low-code. Sahay et al. (2020) las describen como entornos visuales pensados para que '
    'personas sin formación en programación construyan sus propios sistemas, y proponen un marco conceptual para '
    'compararlas, porque elegir entre cientos de plataformas heterogéneas resulta difícil sin un soporte dedicado. Bock y '
    'Frank (2021) examinan de manera exploratoria un conjunto de plataformas disponibles en el mercado para caracterizar '
    'sus rasgos distintivos, y Rokis y Kirikova (2022) revisan la literatura sobre desarrollo low-code y no-code, '
    'identifican los desafíos propios de cada fase del desarrollo y resumen las soluciones propuestas. Esos trabajos '
    'sirven de contrapeso a la documentación del fabricante, que es la fuente de los criterios anteriores: la reducción '
    'de código que promete la categoría no elimina el código efectivamente escrito —el Flujo 2 requiere cinco nodos con '
    'JavaScript, y los dos flujos, sentencias SQL escritas a mano— y la barrera de adopción que se le atribuye no fue '
    'medida en este trabajo (Sección 6.3).')

# ============================================================ §2.2.4 y §2.2.5
ultimo_223 = k.par('La evaluación de la clasificación de intenciones en chatbots')
h224 = k.insertar_despues(ultimo_223, H3, '2.2.4 Inyección de contexto, generación aumentada por recuperación y alucinación')
p = k.insertar_despues(h224, PRIMERO,
    'Un modelo de lenguaje responde a partir de lo que aprendió en su entrenamiento. Cuando la respuesta exige datos que '
    'no están en ese conocimiento —la política de una tienda, por ejemplo—, tiende a completarla con contenido plausible '
    'pero no respaldado, fenómeno que la literatura denomina alucinación (Huang et al., 2025). La respuesta técnica más '
    'difundida es la generación aumentada por recuperación (retrieval-augmented generation, RAG), que Lewis et al. (2020) '
    'formulan como la combinación de la memoria paramétrica del modelo con una memoria no paramétrica: un recuperador '
    'selecciona, para cada consulta, los pasajes pertinentes de un índice documental, y el generador condiciona su salida '
    'en ellos. Fan et al. (2024) sistematizan las variantes de esa arquitectura en los modelos de lenguaje de gran escala.')
p = k.insertar_despues(p, CUERPO,
    'Lo que este trabajo implementa no es RAG sino inyección de contexto: en cada llamada se inserta en el prompt la tabla '
    'completa de veintitrés entradas de la base de conocimiento, sin seleccionar las pertinentes a la consulta (Sección '
    '4.4.3). La distinción tiene dos consecuencias. La primera es de escala: con una base de conocimiento de tamaño real '
    'la inyección completa deja de ser viable y exige un recuperador, que introduce su propia fuente de error. La segunda '
    'es de posición: Liu et al. (2024) muestran que el desempeño de los modelos cae cuando la información relevante queda '
    'en el medio de un contexto largo, lo que advierte que el lugar que ocupa la base dentro del prompt no es neutral. '
    'Ninguna de las dos arquitecturas elimina la alucinación: la reducen en la medida en que el modelo se atiene al '
    'contexto que recibe, y esa es la propiedad que examina la Sección 5.2.5.')
h225 = k.insertar_despues(p, H3, '2.2.5 Evaluación de texto generado, no determinismo y acuerdo entre evaluadores')
p = k.insertar_despues(h225, PRIMERO,
    'Evaluar lo que un modelo generativo responde es más difícil que evaluar lo que clasifica. La clasificación admite '
    'una etiqueta de referencia y una métrica de exactitud; el texto generado admite muchas respuestas aceptables para '
    'una misma consulta, y la literatura de generación de lenguaje natural distingue entre la evaluación mediante '
    'métricas automáticas y la basada en juicio humano, y discute los límites de ambas (Gatt y Krahmer, 2018). A esa '
    'dificultad se suma el no determinismo: en generación de código, un mismo prompt produce salidas distintas en '
    'llamadas sucesivas, y llevar la temperatura a cero lo reduce pero no lo elimina (Ouyang et al., 2025). Sclar et al. '
    '(2024) documentan además que, en modelos abiertos y con ejemplos en el prompt, cambios de formato que no alteran el '
    'contenido llegan a mover la exactitud hasta 76 puntos, y recomiendan informar el desempeño sobre varias '
    'formulaciones y no sobre una sola. Ambos hallazgos fundan dos decisiones del método: repetir cada condición del '
    'diseño factorial (Sección 3.5.6) y tratar como hipótesis, y no como resultado, el efecto de la forma de presentar el '
    'mensaje del cliente (Sección 5.2.4).')
k.insertar_despues(p, CUERPO,
    'Cuando la evaluación descansa en jueces humanos, su confiabilidad se establece por el acuerdo entre ellos. El κ de '
    'Cohen (1960) descuenta el acuerdo atribuible al azar, y la escala de Landis y Koch (1977) ofrece una lectura '
    'convencional de sus valores. Artstein y Poesio (2008) revisan los coeficientes de acuerdo entre anotadores —entre '
    'ellos el κ de Cohen, el π de Scott y el α de Krippendorff— y discuten cuál resulta apropiado según la tarea de '
    'anotación. Un acuerdo bajo informa que el esquema de categorías no se aplica de manera reproducible, y por eso un '
    'instrumento de juicio se pone a prueba antes de usarse. La evaluación de contenido de este trabajo no lo hizo: su '
    'rúbrica se aplicó sin prueba piloto y con niveles que se superponen (Sección 5.2.5).')

# ============================================================ §2.4: búsqueda
k.reemplazo('robotic process automation, SME y order fulfillment, en inglés,',
            'robotic process automation, SME y order fulfillment —y, en una actualización de septiembre de 2026, '
            'retrieval-augmented generation, hallucination, grounding, customer service y low-code platform—, en inglés,')
k.reemplazo('tres preprints sin revisión por pares —Huang et al. (2023), Luo et al. (2023) y Perez y Ribeiro (2022)—',
            'dos preprints sin revisión por pares —Luo et al. (2023) y Perez y Ribeiro (2022)—')
k.reemplazo('la lista de referencias los identifica por su repositorio.',
            'la lista de referencias los identifica por su repositorio. Se incluyó además una decisión judicial, Moffatt v. '
            'Air Canada (2024), por su pertinencia directa al riesgo que el trabajo examina.')

# ============================================================ §2.4.1, §2.4.2, §2.4.3
k.insertar_despues('Ngai et al. (2021) presentan un chatbot basado en conocimiento', CUERPO,
    'La literatura posterior a la difusión de los modelos de lenguaje de gran escala desplaza la pregunta de la utilidad '
    'a la confiabilidad. Larsen et al. (2026) proponen un marco de las alucinaciones de estos modelos adaptado a la '
    'atención al cliente y, sobre una encuesta a 274 potenciales usuarios, muestran que todos los tipos de alucinación '
    'pueden erosionar la confianza, y que las que consisten en información errónea con consecuencias para el usuario son '
    'las que se juzgan más graves. El riesgo tiene además un correlato jurídico. En Moffatt v. Air Canada (2024), un '
    'tribunal de la Columbia Británica responsabilizó a la aerolínea por la información que su asistente conversacional '
    'dio a un cliente —que la tarifa por duelo podía solicitarse de manera retroactiva, contra la política de la '
    'empresa— y rechazó el argumento de que el asistente respondiera por sí mismo de sus respuestas. El caso es pertinente '
    'para este trabajo en un sentido preciso: la Sección 5.2.5 encontró respuestas que afirman una política que la base '
    'de la tienda no contiene.')
arora = k.insertar_despues('Parikh et al. (2023) evalúan cuatro estrategias', CUERPO,
    'Arora et al. (2024) actualizan esa comparación con modelos recientes: adaptan modelos generativos mediante '
    'aprendizaje en contexto y razonamiento encadenado, los comparan con codificadores de oraciones ajustados por '
    'contraste en exactitud y latencia, y encuentran que la capacidad de detectar mensajes ajenos al conjunto de '
    'intenciones depende del alcance de las etiquetas y del tamaño del espacio de categorías. El resultado es pertinente '
    'para un clasificador de cuatro categorías con una clase residual, como el de este trabajo.')
ultimo_242 = k.par('Estos antecedentes son los que dan sentido a la comparación entre regímenes')
h243 = k.insertar_despues(ultimo_242, k.par('2.4.2 Clasificación de intenciones con modelos de lenguaje'),
                          '2.4.3 Anclaje en bases de conocimiento y alucinación')
k.insertar_despues(h243, k.par('Ngai et al. (2021) presentan un chatbot basado en conocimiento'),
    'La promesa de anclar las respuestas en una base documental —que el sistema responda con lo que la base dice y no con '
    'lo que el modelo supone— es la que motiva la inyección de contexto de este trabajo, y la evidencia reciente la '
    'matiza. Magesh et al. (2025) evaluaron, en un estudio preregistrado, las herramientas de investigación jurídica '
    'basadas en generación aumentada por recuperación de los dos principales proveedores del mercado, y encontraron que '
    'alucinan entre el 17 % y el 33 % de las veces, pese a que sus proveedores las presentaban como libres de '
    'alucinación. Huang et al. (2025) incluyen la recuperación entre las estrategias de mitigación y discuten sus límites, '
    'entre ellos que el contexto recuperado no cubra la consulta o entre en conflicto con el conocimiento del modelo. Ese '
    'es el mecanismo que observa la Sección 5.2.5: las dos respuestas con datos ausentes de la base contestan consultas '
    'sobre temas que la base no trata. Ningún antecedente revisado evalúa ese fenómeno sobre la atención post-venta de '
    'una tienda con una base de conocimiento propia, y este trabajo lo aborda solo de manera parcial.')

# ============================================================ §2.4.6 contribución de integración
k.reescribir('La revisión permite delimitar la contribución con precisión, y también su modestia.',
    'La revisión permite delimitar la contribución, y también su modestia. Los trabajos sobre clasificación de '
    'intenciones miden el componente de inteligencia artificial de manera aislada, sobre corpus normalizados; los que '
    'evalúan el anclaje de las respuestas lo hacen sobre herramientas y dominios distintos del comercio electrónico; los '
    'trabajos sobre automatización en pequeñas y medianas empresas describen la adopción y sus barreras sin instrumentar '
    'métricas sobre un artefacto; y la literatura regional mide la percepción del usuario o describe implementaciones sin '
    'término de comparación medido. Este trabajo no reclama un vacío en esa literatura: definido por la suma de '
    'condiciones —un mismo artefacto, instrumentación embebida, procesamiento de órdenes y atención conversacional, y un '
    'baseline cronometrado por los autores—, cualquier vacío quedaría vacío casi por construcción.')
k.reescribir('La Tabla 2.1 sitúa este trabajo frente a los antecedentes revisados.',
    'La contribución es de integración. La Tabla 2.1 sitúa el trabajo frente a los antecedentes revisados: no supera a '
    'ninguno en su propia métrica, cosa que no hace ni pretende, sino que articula dentro de un artefacto reproducible '
    'componentes que la literatura trata por separado, los mide con instrumentación propia contra un término de '
    'comparación medido y documenta los procedimientos, los datos y los errores de modo que cada resultado pueda '
    'auditarse.')

# ============================================================ Tabla 2.1
t21 = k.tabla(['Antecedente', 'Dominio', 'Enfoque técnico', 'Qué mide', 'Entorno'])


def fila_nueva(despues_de, celdas):
    i = k.fila(t21, despues_de)
    tr = copy.deepcopy(t21.rows[i]._tr)
    t21.rows[i]._tr.addnext(tr)
    for c, texto in enumerate(celdas):
        k.celda(t21, i + 1, c, texto)


fila_nueva('Misischia et al. (2022)', ['Larsen et al. (2026)', 'Atención al cliente con LLM', 'Marco de alucinaciones adaptado al dominio',
                                       'Gravedad percibida y confianza', 'Encuesta a 274 usuarios'])
fila_nueva('Luo et al. (2023)', ['Arora et al. (2024)', 'Clasificación de intenciones', 'LLM con aprendizaje en contexto frente a codificadores ajustados',
                                 'Exactitud, latencia y detección fuera de alcance', 'Evaluación comparativa'])
fila_nueva('Arora et al. (2024)', ['Magesh et al. (2025)', 'Investigación jurídica', 'Herramientas comerciales con generación aumentada por recuperación',
                                   'Tasa de alucinación', 'Evaluación preregistrada'])
k.celda(t21, k.fila(t21, 'Este trabajo'), 2,
        'Orquestación con n8n y clasificación con LLM con inyección de contexto; diseño factorial sobre la base de '
        'conocimiento y las reglas y ejemplos del prompt')

# ============================================================ terminología
k.reemplazo('opera en régimen few-shot con recuperación de contexto: su prompt de sistema incluye reglas de decisión por '
            'categoría, siete ejemplos etiquetados de entrada y salida y un bloque en el que se inyecta la base de '
            'conocimiento de la tienda, recuperada de la base de datos en tiempo de ejecución.',
            'opera en régimen few-shot con inyección de contexto: su prompt de sistema incluye reglas de decisión por '
            'categoría, siete ejemplos etiquetados de entrada y salida y un bloque en el que se inserta la base de '
            'conocimiento completa de la tienda, leída de la base de datos en cada llamada (Sección 2.2.4).')
k.reemplazo('ejemplos etiquetados y recuperación de contexto (Sección 2.2.2).',
            'ejemplos etiquetados e inyección de contexto (Secciones 2.2.2 y 2.2.4).')
k.reemplazo('Opera por lo tanto en régimen few-shot y con recuperación de contexto.',
            'Opera por lo tanto en régimen few-shot y con inyección de contexto: en cada llamada se inserta la tabla '
            'completa, sin seleccionar las entradas pertinentes a la consulta, lo que la distingue de la generación '
            'aumentada por recuperación (Sección 2.2.4).')

# ============================================================ Huang et al. publicado
k.reemplazo('(Huang et al., 2023)', '(Huang et al., 2025)')
MODELO_REF = k.par('Parikh, S., Tiwari, M.')


def referencia(despues_de, partes):
    p = k.insertar_despues(k.par(despues_de), MODELO_REF, partes[0][0])
    p.runs[0].italic = partes[0][1] or None
    for texto, cursiva in partes[1:]:
        r = p.add_run(texto)
        if MODELO_REF.runs[0]._r.rPr is not None:
            r._r.insert(0, copy.deepcopy(MODELO_REF.runs[0]._r.rPr))
        r.italic = True if cursiva else None
    return p


huang_viejo = k.par('Huang, L., Yu, W., Ma, W.')
assert 'arxiv.org/abs/2311.05232' in huang_viejo.text
referencia('Huang, L., Yu, W., Ma, W.', [
    ('Huang, L., Yu, W., Ma, W., Zhong, W., Feng, Z., Wang, H., Chen, Q., Peng, W., Feng, X., Qin, B., & Liu, T. (2025). '
     'A survey on hallucination in large language models: Principles, taxonomy, challenges, and open questions. ', False),
    ('ACM Transactions on Information Systems, 43', True),
    ('(2), 1–55. https://doi.org/10.1145/3703155', False)])
k.eliminar(huang_viejo)

referencia('Alderete, M. V., & Porris, M. S. (2023).', [
    ('Arora, G., Jain, S., & Merugu, S. (2024). Intent detection in the age of LLMs. En ', False),
    ('Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing: Industry Track', True),
    (' (pp. 1559–1570). Association for Computational Linguistics. https://doi.org/10.18653/v1/2024.emnlp-industry.114', False)])
referencia('Arora, G., Jain, S., & Merugu, S. (2024).', [
    ('Artstein, R., & Poesio, M. (2008). Inter-coder agreement for computational linguistics. ', False),
    ('Computational Linguistics, 34', True),
    ('(4), 555–596. https://doi.org/10.1162/coli.07-034-R2', False)])
referencia('Beyer, B., Jones, C.', [
    ('Bock, A. C., & Frank, U. (2021). Low-code platform. ', False),
    ('Business & Information Systems Engineering, 63', True),
    ('(6), 733–740. https://doi.org/10.1007/s12599-021-00726-8', False)])
referencia('Dumas, M., La Rosa, M.', [
    ('Fan, W., Ding, Y., Ning, L., Wang, S., Li, H., Yin, D., Chua, T.-S., & Li, Q. (2024). A survey on RAG meeting LLMs: '
     'Towards retrieval-augmented large language models. En ', False),
    ('Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining', True),
    (' (pp. 6491–6501). ACM. https://doi.org/10.1145/3637528.3671470', False)])
referencia('Fondevila-Gascón, J.-F.', [
    ('Gatt, A., & Krahmer, E. (2018). Survey of the state of the art in natural language generation: Core tasks, '
     'applications and evaluation. ', False),
    ('Journal of Artificial Intelligence Research, 61', True),
    (', 65–170. https://doi.org/10.1613/jair.5477', False)])
referencia('Landis, J. R., & Koch, G. G. (1977).', [
    ('Larsen, A. G., Skjuve, M. B., Følstad, A., & van As, N. (2026). LLM hallucinations in conversational AI for customer '
     'service: Framework and end-user perceptions. ', False),
    ('International Journal of Human–Computer Interaction, 42', True),
    ('(13), 9807–9828. https://doi.org/10.1080/10447318.2025.2580540', False)])
referencia('Laudon, K. C., & Traver, C. G. (2021).', [
    ('Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., '
     'Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. ',
     False),
    ('Advances in Neural Information Processing Systems, 33', True),
    (', 9459–9474.', False)])
referencia('Ley 25.326 de Protección de los Datos Personales.', [
    ('Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024). Lost in the middle: '
     'How language models use long contexts. ', False),
    ('Transactions of the Association for Computational Linguistics, 12', True),
    (', 157–173. https://doi.org/10.1162/tacl_a_00638', False)])
referencia('Luo, H., Liu, P., & Esping, S. (2023).', [
    ('Magesh, V., Surani, F., Dahl, M., Suzgun, M., Manning, C. D., & Ho, D. E. (2025). Hallucination-free? Assessing the '
     'reliability of leading AI legal research tools. ', False),
    ('Journal of Empirical Legal Studies, 22', True),
    ('(2), 216–242. https://doi.org/10.1111/jels.12413', False)])
referencia('Misischia, C. V., Pöcze, F., & Strauss, C. (2022).', [
    ('Moffatt v. Air Canada', True),
    (', 2024 BCCRT 149 (Civil Resolution Tribunal, Columbia Británica, 14 de febrero de 2024). '
     'https://www.canlii.org/en/bc/bccrt/doc/2024/2024bccrt149/2024bccrt149.html', False)])
referencia('OpenAI. (2024).', [
    ('Ouyang, S., Zhang, J. M., Harman, M., & Wang, M. (2025). An empirical study of the non-determinism of ChatGPT in code '
     'generation. ', False),
    ('ACM Transactions on Software Engineering and Methodology, 34', True),
    ('(2), 1–28. https://doi.org/10.1145/3697010', False)])
referencia('Ramos De Santis, P. (2024).', [
    ('Rokis, K., & Kirikova, M. (2022). Challenges of low-code/no-code software development: A literature review. En ', False),
    ('Perspectives in Business Informatics Research', True),
    (' (pp. 3–17). Springer. https://doi.org/10.1007/978-3-031-16947-2_1', False)])
referencia('Rokis, K., & Kirikova, M. (2022).', [
    ('Sahay, A., Indamutsa, A., Di Ruscio, D., & Pierantonio, A. (2020). Supporting the understanding and comparison of '
     'low-code development platforms. En ', False),
    ('2020 46th Euromicro Conference on Software Engineering and Advanced Applications (SEAA)', True),
    (' (pp. 171–178). IEEE. https://doi.org/10.1109/SEAA51224.2020.00036', False)])
referencia('Sahay, A., Indamutsa, A.', [
    ('Sclar, M., Choi, Y., Tsvetkov, Y., & Suhr, A. (2024). Quantifying language models’ sensitivity to spurious features in '
     'prompt design or: How I learned to start worrying about prompt formatting. En ', False),
    ('The Twelfth International Conference on Learning Representations (ICLR 2024)', True),
    ('. https://arxiv.org/abs/2310.11324', False)])

# ============================================================ §5.2.4 y §5.2.5
k.reemplazo('Si la diferencia se sostuviera, la forma de presentar el mensaje también incidiría en la clasificación.',
            'Si la diferencia se sostuviera, la forma de presentar el mensaje también incidiría en la clasificación, como '
            'documentan Sclar et al. (2024) para cambios de formato del prompt en otros modelos.')
k.reemplazo('observada aquí sobre respuestas efectivamente entregadas por el sistema.',
            'observada aquí sobre respuestas efectivamente entregadas por el sistema, y consistente con la evidencia de '
            'que ni la recuperación ni la inyección de contexto la eliminan (Magesh et al., 2025; Sección 2.4.3).')

k.guardar()
