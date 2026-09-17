# -*- coding: utf-8 -*-
"""B-01 a B-09 de la auditoría del 17/09, más dos residuos del propio barrido.

  B-01  los cinco preprints con el mismo formato APA y la versión consultada de Tang et al.
  B-02  el intervalo exacto de la exactitud media por repetición.
  B-03  el resultado del test-retest y los tiempos del anotador del ground truth.
  B-04  PF-01 a PF-03 no se reejecutaron.
  B-05  el título de los metadatos y el rótulo «Omnicanal» en el nombre de los archivos.
  B-06  los disparadores que la variante de producción del Flujo 1 tiene.
  B-07  el nodo que escribe processed_at en la rama sin stock y el MTTD por rama.
  B-08  la corrida descartada de las pruebas del Flujo 2, en el Anexo L.
  B-09  la corrida válida de un juez es su tercera lectura.
  X-01  el sesgo de expectativa del operador, en la lectura del factor.
  X-02  el defecto del guion de conciliación del corpus, en el Anexo L.

Incluye tres ajustes de redacción sobre lo escrito en esta misma pasada: el término
«interpolación» en la §5.5 (j) y en la §6.4, y «3 de 18» en la §5.2.5.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import copy
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)


def ref_apa(pref, antes, cursiva, despues):
    """Reescribe una referencia con el título en cursiva, como pide APA para un preprint."""
    p = k.par(pref)
    base = p.runs[0]._r.rPr
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    for texto, cur in ((antes, False), (cursiva, True), (despues, False)):
        r = p.add_run(texto)
        if base is not None:
            r._r.insert(0, copy.deepcopy(base))
        r.italic = cur
    k.hechos += 1


# ------------------------------------------------------------------ B-01
ref_apa('Amir, A. R., & Atif, S. M.', 'Amir, A. R., & Atif, S. M. (2026). ',
        'Evaluating workflow automation efficiency using n8n: A small-scale business case study',
        ' (arXiv:2602.01311). arXiv. https://arxiv.org/abs/2602.01311')
ref_apa('Luo, H., Liu, P., & Esping, S.', 'Luo, H., Liu, P., & Esping, S. (2023). ',
        'Towards data-efficient customer intent recognition with prompt-based learning paradigm',
        ' (arXiv:2309.14779). arXiv. https://arxiv.org/abs/2309.14779')
ref_apa('Perez, F., & Ribeiro, I.', 'Perez, F., & Ribeiro, I. (2022). ',
        'Ignore previous prompt: Attack techniques for language models',
        ' (arXiv:2211.09527). arXiv. https://arxiv.org/abs/2211.09527')
ref_apa('Tang, Y., Zhou, Y., & Chen, H.', 'Tang, Y., Zhou, Y., & Chen, H. (2026). ',
        'Characterizing large language model agentic workflows: A study on n8n ecosystem',
        ' (arXiv:2606.29116v2). arXiv. https://arxiv.org/abs/2606.29116v2')

# ------------------------------------------------------------------ B-02
t = k.tabla(['Clase (mensajes)'])
i = k.fila(t, 'Media por repetición · IC 95 %')
k.celda(t, i, 3, '76,7 % [70,4 %; 83,0 %]')
k.celda(t, i, 4, '73,3 % [66,5 %; 80,2 %]')
k.reemplazo('76,7 % en C3 ([70,1 %; 83,3 %]) y 73,3 % en C4 ([66,3 %; 80,4 %])',
            '76,7 % en C3 ([70,4 %; 83,0 %]) y 73,3 % en C4 ([66,5 %; 80,2 %])')
k.reemplazo('Los intervalos se calculan sobre la proporción de aciertos de cada mensaje en sus tres repeticiones, y '
            'se informa el más amplio compatible con los recuentos del análisis '
            '(experiments/E8/media_por_repeticion_e8.py).',
            'Los intervalos se calculan con la t de Student sobre la proporción de aciertos de cada mensaje en sus '
            'tres repeticiones, a partir de las predicciones versionadas; el guion comprueba además que ese '
            'intervalo caiga dentro del más amplio compatible con los recuentos publicados, que puede calcularse '
            'sin acceso a la base (experiments/E8/media_por_repeticion_e8.py).')

# ------------------------------------------------------------------ B-03
k.reescribir(
    'Control de estabilidad (test-retest).',
    'Control de estabilidad (test-retest). El mismo anotador re-etiquetó una submuestra de 50 mensajes en orden '
    'aleatorizado y reprodujo sus 50 decisiones (κ = 1,000). Ese resultado no valida el etiquetado: un acuerdo '
    'perfecto consigo mismo es tan compatible con un criterio estable como con el recuerdo de la respuesta '
    'anterior, y la mediana de 2,8 segundos por ítem de la primera ronda —con dos ítems por debajo de 1 segundo— '
    'no permite distinguir entre las dos lecturas. El control verifica la consistencia interna del criterio, no el '
    'acuerdo entre evaluadores, y por eso el trabajo suma el evaluador independiente del punto siguiente.',
    etiqueta='Control de estabilidad (test-retest).')

# ------------------------------------------------------------------ B-04
k.reemplazo('Se re-ejecutaron el 15 de septiembre para dejar evidencia versionada, que se conserva en experiments/PF '
            'junto con el guion, y el mecanismo de cada una es distinto.',
            'Se re-ejecutaron el 15 de septiembre para dejar evidencia versionada, que se conserva en experiments/PF '
            'junto con el guion, y el mecanismo de cada una es distinto. Las tres primeras no se reejecutaron: su '
            'aprobación se apoya en la corrida de carga de 50 órdenes, que recorrió ambas ramas con sus marcas '
            'temporales completas, y en la orden con la que se verificó la alerta de stock bajo. Repetirlas '
            'escribiría órdenes con la marca de los datos medidos y alteraría los totales de este capítulo.')

# ------------------------------------------------------------------ B-05
d.core_properties.title = ('Automatización del ciclo post-venta en e-commerce: pipeline de procesamiento de órdenes '
                           'y atención al cliente con IA, implementado con n8n')
k.hechos += 1
k.reemplazo('con un nodo Merge que unifica los tres canales en un flujo único de procesamiento.',
            'con un nodo Merge que unifica los tres canales en un flujo único de procesamiento. El nombre del '
            'archivo conserva el rótulo «Omnicanal» de una versión anterior del trabajo y no refleja la '
            'delimitación de la Sección 2.3.1, según la cual el sistema es multicanal: se lo mantiene para no '
            'romper las referencias del repositorio.')

# ------------------------------------------------------------------ B-06
k.reemplazo('extiende el webhook de entrada para soportar triggers nativos de WooCommerce, Shopify y MercadoLibre, '
            'con un nodo de normalización que unifica el formato de cada plataforma antes de ingresar al pipeline '
            'de stock.',
            'extiende el webhook de entrada para soportar triggers nativos de WooCommerce y Shopify, con un nodo de '
            'normalización que unifica el formato de cada plataforma antes de ingresar al pipeline de stock.')
k.reescribir(
    'Integrar Tiendanube en la variante de producción del Flujo 1:',
    'Integrar Tiendanube y MercadoShops en la variante de producción del Flujo 1: los workflows de producción '
    'contemplan WooCommerce y Shopify, y no las otras dos plataformas que la Sección 1.1 menciona entre las que '
    'usan las PyMEs argentinas.',
    etiqueta='Integrar Tiendanube y MercadoShops en la variante de producción del Flujo 1:')

# ------------------------------------------------------------------ B-07
k.reemplazo('El MTTR mide, por lo tanto, el tiempo hasta que la notificación fue efectivamente despachada por el '
            'sistema.',
            'En la rama sin stock las escriben sus nodos equivalentes: processed_at, el nodo Marcar Sin Stock, y '
            'notified_at, el nodo Registrar Notificación Sin Stock (Tabla 4.5, nodos 12 y 14). El MTTR mide, por lo '
            'tanto, el tiempo hasta que la notificación fue efectivamente despachada por el sistema. El MTTD '
            'difiere entre ramas y conviene declararlo: en la corrida de carga fue de 0,010 s en las órdenes '
            'confirmadas y de 0,006 s en las que no tenían stock, porque la rama confirmada incluye además el '
            'descuento del stock y la evaluación del umbral de reposición.')

# ------------------------------------------------------------------ B-09
k.reemplazo('El evaluador con dos corridas válidas repitió su propio juicio en 30 de las 45 respuestas (κ = 0,318).',
            'El evaluador con dos corridas válidas repitió su propio juicio en 30 de las 45 respuestas (κ = 0,318). '
            'Cabe una salvedad sobre la corrida válida del otro evaluador: es su tercera lectura de las mismas 45 '
            'respuestas, después de dos corridas invalidadas por tiempo el mismo día, de modo que la exposición '
            'previa al material puede incidir en el acuerdo que se informa.')

# ------------------------------------------------------------------ X-01
k.reemplazo('y la correlación negativa entre el orden de ejecución y el tiempo empleado (Sección 5.1.4) indica que '
            'un operador no entrenado tardaría más.',
            'y la correlación negativa entre el orden de ejecución y el tiempo empleado (Sección 5.1.4) indica que '
            'un operador no entrenado tardaría más. En sentido contrario opera el sesgo de expectativa que declara '
            'la Sección 3.6.2: el operador pertenecía al equipo que formuló H1 y conocía el sentido de la '
            'comparación, de modo que pudo trabajar más lento de lo que trabajaría fuera de la medición, lo que '
            'agrandaría el numerador y con él el factor.')

# ------------------------------------------------------------------ B-08 y X-02, en el Anexo L
modelo = k.par('Pruebas funcionales.')
k.insertar_despues(
    k.par('Construcción de las consultas.'), modelo,
    'Corridas descartadas y defectos del instrumental. Dos corridas de las pruebas del Flujo 2 se descartaron antes '
    'de la que se informa. La del 17 de septiembre a las 03:41 UTC usó un identificador de usuario sin dominio de '
    'correo: las cinco ejecuciones terminaron en error en el nodo de envío, el emisor recibió HTTP 200 y no quedó '
    'ninguna interacción registrada, aunque sí los dos tickets de las pruebas de reclamo, que quedaron sin '
    'respuesta. Las dos corridas de la prueba del apóstrofo del mismo día informaban mal el resultado de su '
    'control, porque el guion leía un código de salida que no distingue una sentencia fallida, y dejaron dos '
    'interacciones y dos tickets. Los tres casos están declarados en el README de experiments/PF con los '
    'identificadores de las filas que dejaron. El guion de ejecución del corpus tiene además dos defectos '
    'registrados como D-11: su conciliación no filtra por fecha, de modo que con dos corridas en la base informa '
    'un total que suma ambas, y no genera el manifiesto de la corrida en la consola en que se ejecutó; la '
    'conciliación de la corrida informada se rehízo con consultas propias, y los manifiestos del diseño factorial, '
    'que sí se generaron, están en experiments/E8.',
    etiqueta='Corridas descartadas y defectos del instrumental.')

# ------------------------------------------------------------------ ajustes de redacción de esta pasada
k.reemplazo('armaban sus sentencias insertando los valores recibidos dentro del texto de la consulta, sin '
            'parámetros. Eso tiene dos consecuencias.',
            'armaban sus sentencias por interpolación: insertaban los valores recibidos dentro del texto de la '
            'consulta, sin parámetros. Eso tiene dos consecuencias.')
k.reemplazo('(x) las consultas del artefacto medido se construían interpolando los valores recibidos en el texto de '
            'la sentencia',
            '(x) las consultas del artefacto medido se construían por interpolación de los valores recibidos en el '
            'texto de la sentencia')
k.reemplazo('Contado ese caso, la proporción sería de 3 sobre 18 —el 16,7 %, con un intervalo de Wilson de 5,8 % a '
            '39,2 %—,',
            'Contado ese caso, la proporción sería de 3 de 18 —el 16,7 %, con un intervalo de Wilson de 5,8 % a '
            '39,2 %—,')

k.guardar()
