# -*- coding: utf-8 -*-
"""Dictamen del 15/09, grupo B: estado del arte, marco legal, bibliografía, madurez y encuadre.

  B4. Antecedentes empíricos sobre n8n, verificados en arXiv: Amir y Atif (2026,
      arXiv:2602.01311) y Tang et al. (2026, arXiv:2606.29116), con sus filas en la
      Tabla 2.1 y sus referencias. Moffatt v. Air Canada pasa de §2.4.1 al marco legal
      (§2.5). Sclar et al. (2024) dialoga con el hallazgo de formato en §2.4.2. La
      afirmación sobre código cerrado de las alternativas, apoyada solo en el
      fabricante, se retira. La atribución a Turban et al. deja de citar un término.
  B5. Se retira la escala de madurez propia (§2.1.1 y §6.3) y se usa la distinción
      entre automatizar y gestionar un proceso (Dumas et al., 2018). §3.2 justifica el
      estudio de caso con razones metodológicas (caso único con unidades de análisis
      incrustadas, Yin, 2018) y presenta el diseño factorial como experimento
      controlado dentro del caso.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys
import copy

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit, qn  # noqa: E402

d = abrir()
k = Kit(d)
_reemplazo = k.reemplazo


def reemplazo(old, new, n=1):
    """Algunas citas llevan espacio duro entre «et al.» y el año: se prueban las dos variantes."""
    from kit5 import replace_everywhere
    hechos = replace_everywhere(d, old, new)
    if hechos == 0 and 'et al. (' in old:
        hechos = replace_everywhere(d, old.replace('et al. (', 'et al.' + chr(160) + '('), new)
    assert hechos == n, 'se esperaban %d reemplazos de %r, hubo %d' % (n, old[:70], hechos)
    k.hechos += 1


k.reemplazo = reemplazo

# ------------------------------------------------------------------ B4: procedimiento de búsqueda
k.reemplazo('customer service y low-code platform—', 'customer service, low-code platform y n8n—')
k.reemplazo(
    'Se admitió una excepción declarada: dos preprints sin revisión por pares —Luo et al. (2023) y Perez y Ribeiro (2022)—',
    'Se admitió una excepción declarada: cuatro preprints sin revisión por pares —Luo et al. (2023), Perez y Ribeiro '
    '(2022), Amir y Atif (2026) y Tang et al. (2026)—')
k.reemplazo(
    ' Se incluyó además una decisión judicial, Moffatt v. Air Canada (2024), por su pertinencia directa al riesgo que el '
    'trabajo examina.',
    ' La decisión judicial Moffatt v. Air Canada (2024), pertinente al riesgo que el trabajo examina, no se trata como '
    'antecedente de investigación sino en el marco legal de la Sección 2.5.')

# ------------------------------------------------------------------ B4: Moffatt al marco legal
k.reemplazo(
    ' El riesgo tiene además un correlato jurídico. En Moffatt v. Air Canada (2024), un tribunal de la Columbia Británica '
    'responsabilizó a la aerolínea por la información que su asistente conversacional dio a un cliente —que la tarifa por '
    'duelo podía solicitarse de manera retroactiva, contra la política de la empresa— y rechazó el argumento de que el '
    'asistente fuera responsable de su propia información. El caso es pertinente para este trabajo en un sentido preciso: '
    'la Sección 5.2.5 encontró respuestas que afirman una política que la base de la tienda no contiene.',
    ' El riesgo tiene además un correlato jurídico, que la Sección 2.5 trata en el marco legal.')
deber = k.par('Existe además un deber que no deriva de la Ley 25.326')
k.insertar_despues(
    deber, deber,
    'Lo que un asistente afirma tiene también un correlato jurisprudencial. En Moffatt v. Air Canada (2024), un tribunal '
    'de la Columbia Británica responsabilizó a la aerolínea por la información que su asistente conversacional dio a un '
    'cliente —que la tarifa por duelo podía solicitarse de manera retroactiva, contra la política de la empresa— y '
    'rechazó el argumento de que el asistente fuera responsable de su propia información. El caso es pertinente para este '
    'trabajo en dos sentidos: la Sección 5.2.5 encontró respuestas que afirman una política que la base de la tienda no '
    'contiene, y el prompt medido oculta el carácter automatizado del canal, como se analiza a continuación.')
k.reemplazo('El caso Moffatt v. Air Canada (2024), revisado en la Sección 2.4.1, no se pronunció', 'Ese fallo no se pronunció')

# ------------------------------------------------------------------ B4: Sclar en §2.4.2 y n8n en §2.4.4
arora = k.par('Arora et al. (2024) actualizan esa comparación')
k.insertar_despues(
    arora, arora,
    'Sclar et al. (2024) agregan una advertencia que alcanza a toda esa literatura: en modelos abiertos, cambios de '
    'formato del prompt que no alteran su contenido mueven la exactitud de manera sustancial, de modo que una cifra '
    'obtenida con una formulación describe a esa formulación y no al modelo. Este trabajo observa con GPT-4o-mini un '
    'fenómeno del mismo tipo —dos prompts sin reglas ni ejemplos que difieren sobre todo en cómo presentan el mensaje del '
    'cliente obtienen 74,0 % y 86,0 %—, que la Sección 5.2.4 trata como hipótesis y la Sección 6.3 usa para acotar el '
    'alcance de sus conclusiones.')
pyplacz = k.par('Pypłacz y Žukovskis (2023) estudian')
k.insertar_despues(
    pyplacz, arora,
    'Sobre n8n en particular, la literatura empírica es reciente y todavía no arbitrada. Amir y Atif (2026) evalúan, en '
    'el caso de una pequeña empresa, un flujo de procesamiento de contactos implementado en n8n —registro de datos, '
    'correo de confirmación y notificación— y comparan 20 ejecuciones manuales con 25 automatizadas en condiciones '
    'controladas: el tiempo medio pasa de 185,35 s a 1,23 s, una reducción de unas 151 veces, y la tasa de error, de 5 % '
    'a cero. Es el antecedente más próximo al término comparativo de este trabajo, por el diseño y por el orden de '
    'magnitud del resultado. Tang et al. (2026) analizan más de 6.000 flujos de n8n publicados que incorporan modelos de '
    'lenguaje y encuentran que los mecanismos explícitos de confiabilidad —caminos de respaldo estructurados, alertas '
    'específicas de falla y aprobación humana— son relativamente poco comunes, un resultado que dialoga con las fallas '
    'silenciosas que este trabajo documenta en sus dos flujos (Secciones 5.1.3 y 5.2.4). Ambos son preprints, incluidos '
    'por la excepción declarada al comienzo de esta sección.')

t21 = k.tabla(('Antecedente', 'Dominio', 'Enfoque técnico', 'Qué mide', 'Entorno'))
tbl = t21._tbl
trs = tbl.findall(qn('w:tr'))
zhang = [tr for tr in trs if ''.join(t.text or '' for t in tr.iter(qn('w:t'))).startswith('Zhang et al. (2021)')][0]
ancla_tr = zhang
for valores in (
        ['Amir y Atif (2026)', 'Procesos de pequeña empresa', 'Flujo de procesamiento de contactos en n8n',
         'Tiempo de ejecución manual frente a automatizado y tasa de error', 'Caso de pequeña empresa (preprint)'],
        ['Tang et al. (2026)', 'Flujos con LLM en n8n', 'Análisis de más de 6.000 flujos publicados',
         'Patrones de diseño y mecanismos de confiabilidad', 'Repositorio público de flujos (preprint)']):
    nueva = copy.deepcopy(zhang)
    for tc, texto in zip(nueva.findall(qn('w:tc')), valores):
        ts = list(tc.iter(qn('w:t')))
        ts[0].text = texto
        for t in ts[1:]:
            t.text = ''
    ancla_tr.addnext(nueva)
    ancla_tr = nueva
k.hechos += 1

k.reemplazo(
    'los trabajos sobre automatización en pequeñas y medianas empresas describen la adopción y sus barreras sin '
    'instrumentar métricas sobre un artefacto;',
    'los trabajos sobre automatización en pequeñas y medianas empresas describen la adopción y sus barreras, y los que '
    'miden flujos de n8n son preprints recientes que comparan un único flujo con su ejecución manual o analizan flujos '
    'publicados sin ejecutarlos;')
k.reemplazo('no identificó benchmarks publicados de n8n aplicados al ciclo post-venta de PyMEs argentinas',
            'no identificó mediciones arbitradas de n8n aplicadas al ciclo post-venta de PyMEs')

# ------------------------------------------------------------------ B4: referencias nuevas
modelo_ref = k.par('Ley 25.326 de Protección de los Datos Personales.')
k.insertar_despues(
    'Alderete, M. V., & Porris, M. S. (2023).', modelo_ref,
    'Amir, A. R., & Atif, S. M. (2026). Evaluating workflow automation efficiency using n8n: A small-scale business case '
    'study (arXiv:2602.01311). arXiv. https://arxiv.org/abs/2602.01311')
k.insertar_despues(
    'Stake, R. E. (1995).', modelo_ref,
    'Tang, Y., Zhou, Y., & Chen, H. (2026). Characterizing large language model agentic workflows: A study on n8n '
    'ecosystem (arXiv:2606.29116). arXiv. https://arxiv.org/abs/2606.29116')

# ------------------------------------------------------------------ B4: bibliografía
k.reemplazo(
    ', a diferencia de las plataformas comerciales equivalentes, que operan como servicios gestionados de código cerrado '
    '(n8n GmbH, 2025).',
    ' (n8n GmbH, 2025). Los tres criterios describen propiedades de n8n documentadas por su fabricante; el trabajo no '
    'evaluó las alternativas con el mismo detalle.')
k.reemplazo(
    'se enmarca dentro de lo que Turban et al. (2018) denominan fulfillment automation: la capacidad de ejecutar el ciclo '
    'completo desde la recepción del pedido hasta la notificación al cliente sin intervención humana.',
    'forma parte del cumplimiento de pedidos (order fulfillment), que la literatura de comercio electrónico no limita a '
    'entregar lo pedido en tiempo sino que extiende a los servicios al cliente asociados (Turban et al., 2018); '
    'automatizarlo es ejecutar sin intervención humana las etapas de ese ciclo que no requieren criterio.')

# ------------------------------------------------------------------ B5: escala de madurez
k.reemplazo(
    'Para situar lo que un sistema de automatización alcanza, este trabajo ordena la madurez de un proceso en cuatro '
    'niveles: documentación, automatización, optimización y gobernanza. La escala es un marco analítico propio, que el '
    'Capítulo 6 usa para ordenar la discusión, y no una clasificación tomada de la literatura de gestión de procesos '
    '(Business Process Management, BPM).',
    'Automatizar un proceso no equivale a gestionarlo: la gestión de procesos de negocio (Business Process Management, '
    'BPM) comprende un ciclo de vida que incluye, además de implementar el proceso, monitorear y controlar su ejecución '
    '(Dumas et al., 2018). El Capítulo 6 usa esa distinción para situar lo que el sistema construido alcanza.')
k.reemplazo(
    'La primera es la escala de madurez de proceso que la Sección 2.1.1 propone como marco analítico propio, en la que la '
    'automatización es un nivel intermedio entre la documentación y la gobernanza: el sistema construido alcanza el nivel '
    'de automatización —el ciclo se ejecuta sin intervención humana y queda instrumentado— pero no el de gobernanza, '
    'porque no incorpora',
    'La primera es la distinción de la Sección 2.1.1 entre automatizar un proceso y gestionarlo: el sistema construido lo '
    'automatiza —el ciclo se ejecuta sin intervención humana y queda instrumentado— pero no monitorea ni controla su '
    'ejecución, porque no incorpora')
k.reemplazo(
    'ocurrieron sin que el motor de flujos las advirtiera, y detectarlas exigió instrumentación propia.',
    'ocurrieron sin que el motor de flujos las advirtiera, y detectarlas exigió instrumentación propia. No es un rasgo '
    'aislado de este sistema: en más de 6.000 flujos de n8n publicados, los mecanismos explícitos de confiabilidad son '
    'relativamente poco comunes (Tang et al., 2026).')

# ------------------------------------------------------------------ B5: encuadre metodológico
k.reemplazo(
    'La investigación en ciencia del diseño, que Hevner et al. (2004) caracterizan como la construcción y evaluación de '
    'artefactos, habría sido un encuadre igualmente defendible; se la menciona para que el lector pueda situar la '
    'elección, que se tomó cuando el trabajo ya estaba estructurado como estudio de caso.',
    'La razón metodológica para preferir el estudio de caso es la naturaleza de la evidencia que el trabajo reúne: un '
    'único sistema evaluado por varias vías que deben leerse juntas —marcas temporales, un baseline cronometrado, un '
    'corpus etiquetado, un diseño factorial, pruebas funcionales y la verificación del contenido—, que corresponde a lo '
    'que Yin (2018) describe como un caso único con varias unidades de análisis incrustadas. Dentro de ese caso, el '
    'diseño factorial de la Sección 3.5.6 es un experimento controlado en sentido estricto: manipula dos factores, '
    'mantiene constantes el corpus, el modelo y las etiquetas, repite cada condición y fijó sus contrastes antes de '
    'medir. La comparación con el proceso manual, en cambio, no lo es, porque no asigna al azar las condiciones '
    '(Sección 5.4.1). La investigación en ciencia del diseño, que Hevner et al. (2004) caracterizan como la construcción '
    'y evaluación de artefactos, habría sido un encuadre defendible; no se la adopta porque el trabajo no se propone '
    'derivar principios de diseño transferibles a otros artefactos, sino evaluar uno instanciado bajo condiciones '
    'declaradas.')

k.guardar()
