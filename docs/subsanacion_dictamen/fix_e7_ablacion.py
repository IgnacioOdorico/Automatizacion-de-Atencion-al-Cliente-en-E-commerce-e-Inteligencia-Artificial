# -*- coding: utf-8 -*-
"""Incorpora al documento el hallazgo del prompt versionado y la ablacion E7.

QUE PASO
El accuracy del 92,7 % se midio el 2026-08-12 con el workflow "Flujo 2 —
Chatbot Omnicanal IA" (14 nodos), cuyo prompt de sistema tenia 6338 caracteres e
incluia la base de conocimiento inyectada, siete ejemplos etiquetados y reglas
de clasificacion por categoria. El prompt de 1032 caracteres que el Anexo H
transcribia aparecio el 2026-08-27, quince dias DESPUES de la medicion, junto
con el workflow de 19 nodos. La auditoria original de §4.4.3 fue honesta pero se
hizo sobre el artefacto equivocado.

QUE SE HIZO
Se ejecuto la ablacion (E7): el MISMO corpus de 150 mensajes contra las MISMAS
etiquetas de referencia, con el prompt reducido. Resultado 86,0 % contra 92,7 %.
Diseño apareado -> McNemar, p exacto = 0,0309.

Este guion corrige las afirmaciones falsas y publica la ablacion.
"""
import sys
import os
import copy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'docs/subsanacion_dictamen')
from docxkit import *
from docx import Document
from docx.oxml.ns import qn

if any(f.startswith('~$') for f in os.listdir('docs')):
    sys.exit('ERROR: Word tiene abierto un documento en docs/. Cerralo primero.')

RUTA = 'docs/TESIS_FINAL_UTN_v6.docx'
d = Document(RUTA)


def idx(pref):
    for i, p in enumerate(d.paragraphs):
        if p.text.strip().startswith(pref):
            return i
    raise KeyError(pref)


def par(pref):
    return d.paragraphs[idx(pref)]


def reescribir(pref, texto):
    p = par(pref)
    assert 'blip' not in p._element.xml, 'lleva imagen'
    p.runs[0].text = texto
    for r in p.runs[1:]:
        r.text = ''
    return p


print('=' * 78)
print(' 1. Renumeracion: la Tabla 5.10 deja lugar a la de la ablacion')
print('=' * 78)
n = replace_everywhere(d, 'Tabla 5.10', 'Tabla 5.11')
print('  Tabla 5.10 -> Tabla 5.11 : %d referencias' % n)

print()
print('=' * 78)
print(' 2. Seccion 2.2.2 — el regimen de prompting realmente empleado')
print('=' * 78)
reescribir('Corresponde precisar el régimen de prompting empleado',
    'Corresponde precisar el régimen de prompting empleado, porque la distinción tiene '
    'consecuencias sobre la interpretación de los resultados. Brown et al. (2020) diferencian '
    'tres regímenes según la cantidad de ejemplos etiquetados que se incluyen en el prompt: '
    'zero-shot, donde el modelo recibe únicamente la instrucción y la definición de las clases; '
    'one-shot, con un ejemplo; y few-shot, con varios ejemplos de entrada y salida. Liu et al. '
    '(2023) sistematizan el conjunto de estas técnicas. Este trabajo mide el clasificador en dos '
    'configuraciones de prompt, y conviene nombrarlas desde aquí porque el Capítulo 5 las compara. '
    'La configuración principal opera en régimen few-shot con recuperación de contexto: el prompt '
    'de sistema incluye siete ejemplos etiquetados de entrada y salida, reglas de decisión por '
    'categoría, y un bloque en el que se inyecta la base de conocimiento de la tienda recuperada '
    'de la base de datos en tiempo de ejecución. La configuración de ablación opera en régimen '
    'zero-shot: el mismo modelo, el mismo corpus y las mismas etiquetas de referencia, con un '
    'prompt que se limita a enumerar las cuatro categorías y a fijar el formato de salida. Ambos '
    'se transcriben en el Anexo H y la comparación entre ellos se reporta en la Sección 5.2.4.')
print('  §2.2.2 reescrita: dos configuraciones declaradas')

reescribir('Estos antecedentes son los que dan sentido al régimen',
    'Estos antecedentes son los que dan sentido a la comparación entre regímenes que este trabajo '
    'ejecuta (Secciones 2.2.2 y 5.2.4) y permiten interpretar sus resultados: ninguno de los dos '
    'valores obtenidos es un dato aislado, sino puntos dentro de un rango que la literatura ya '
    'documenta como alcanzable sin ajuste fino. Corresponde señalar, sin embargo, una diferencia '
    'de alcance que impide la comparación directa de cifras: los trabajos citados evalúan sobre '
    'corpus públicos normalizados —del tipo de CLINC150, Banking77 o SNIPS—, con decenas o '
    'centenas de intenciones, mientras que este trabajo opera sobre cuatro categorías de un '
    'dominio deliberadamente acotado. Un accuracy más alto sobre menos clases no constituye un '
    'mejor resultado, y este trabajo no lo presenta como tal.')
print('  §2.5.2 actualizada')

print()
print('=' * 78)
print(' 3. Seccion 4.4.3 — la configuracion que realmente corrio')
print('=' * 78)
p443 = reescribir('Se eligió GPT-4o-mini por su balance entre costo y capacidad',
    'Se eligió GPT-4o-mini por su balance entre costo y capacidad: para la clasificación de '
    'intenciones en un dominio acotado y la generación de respuestas de soporte no se requiere la '
    'potencia completa de GPT-4o. El prompt de sistema con el que se obtuvo el accuracy del '
    '92,7 % que reporta el Capítulo 5 tiene 6338 caracteres y consta de cinco bloques: identidad '
    'y tono del asistente; definición de la tarea y formato de salida; reglas de decisión por '
    'categoría; un bloque rotulado «base de conocimiento» en el que se inyecta el contenido de la '
    'tabla faq_responses recuperado en tiempo de ejecución, con la instrucción de usar '
    'exclusivamente esa información para responder consultas frecuentes; y siete ejemplos '
    'etiquetados de entrada y salida. Opera por lo tanto en régimen few-shot y con recuperación '
    'de contexto, no en régimen zero-shot. La cadena que provee ese contexto son los nodos Buscar '
    'FAQ en PostgreSQL y Preparar Contexto FAQ, que sí inciden en la salida del sistema en la '
    'configuración medida.')
insert_paragraph_after(p443,
    'Corresponde declarar cómo se llegó a esta precisión, porque una versión anterior de este '
    'documento afirmaba lo contrario y el error es instructivo. Al auditar el workflow para '
    'documentar el prompt se tomó el archivo vigente en el repositorio, que corresponde al '
    'workflow de diecinueve nodos incorporado el 27 de agosto junto con el canal de Telegram, y '
    'cuyo prompt de 1032 caracteres no inyecta la base de conocimiento ni contiene ejemplos. De '
    'ahí se concluyó que el clasificador operaba en régimen zero-shot. La corrida del corpus, sin '
    'embargo, es del 12 de agosto, quince días anterior, y se ejecutó sobre el workflow de '
    'catorce nodos cuyo prompt sí tenía ambas cosas. La auditoría fue correcta en su método y se '
    'aplicó al artefacto equivocado: se auditó la versión vigente del workflow y no la que había '
    'producido la medición. El historial de versiones del repositorio permite fechar ambas '
    'configuraciones y es lo que permitió detectar la discrepancia. Se consigna aquí porque la '
    'regla que de ello se sigue vale más que el caso: una afirmación sobre cómo se obtuvo una '
    'medición debe verificarse contra la versión del artefacto que corrió en la fecha de esa '
    'medición, no contra la versión actual.',
    estilo='Body Text')
print('  §4.4.3 reescrita, con la declaracion del error de auditoria')

print()
print('=' * 78)
print(' 4. Anexo H — se publican los dos prompts')
print('=' * 78)
n = replace_everywhere(d, 'Anexo H: Prompt de sistema del clasificador de intenciones',
                          'Anexo H: Prompts de sistema del clasificador de intenciones')
print('  titulo del anexo: %d' % n)
n = replace_everywhere(d,
    'Se transcribe a continuación el texto íntegro del prompt de sistema que recibe el modelo '
    'GPT-4o-mini en el nodo de inferencia del Flujo 2, tal como está configurado en el workflow '
    'versionado en el repositorio. Es el prompt con el que se obtuvo el accuracy del 92,7 % '
    'reportado en la Sección 5.2.3.',
    'Se transcriben los dos prompts de sistema que este trabajo midió. El primero, de 1032 '
    'caracteres, es el de la condición de ablación: enumera las categorías y fija el formato de '
    'salida, sin ejemplos ni base de conocimiento. Es el prompt del workflow vigente y el que '
    'produjo el 86,0 % de la Sección 5.2.4. El segundo, de 6338 caracteres, es el de la '
    'configuración principal: el que corrió el 12 de agosto y produjo el 92,7 % de la Sección '
    '5.2.3. Por extensión se lo transcribe abreviado en sus bloques repetitivos, con la '
    'indicación expresa de qué se omite; su texto íntegro está en el workflow versionado en el '
    'repositorio, cuya ruta y commit se consignan al pie.')
print('  nota introductoria del Anexo H: %d' % n)

reescribir('Obsérvese que el prompt no contiene ejemplos etiquetados',
    'El prompt transcripto arriba es el de la CONDICIÓN DE ABLACIÓN (1032 caracteres): no '
    'contiene ejemplos etiquetados ni recibe el contenido de la base de conocimiento. Es el que '
    'produjo el 86,0 % de exactitud de la Sección 5.2.4. A continuación se resume el prompt de la '
    'CONFIGURACIÓN PRINCIPAL (6338 caracteres), que es el que produjo el 92,7 % de la Sección '
    '5.2.3 y el que corrió sobre el corpus el 12 de agosto de 2026.')

p_res = par('El prompt transcripto arriba es el de la CONDICIÓN DE ABLACIÓN')
bloque_h2 = [
    ('Los tres primeros bloques —identidad, tarea y formato de salida— son idénticos a los del '
     'prompt de ablación transcripto arriba. Los dos que siguen son los que lo distinguen, y son '
     'los que la Sección 5.2.4 mide.', 'Body Text'),
    ('## REGLAS DE CLASIFICACIÓN\n'
     '### FAQ\n'
     'Preguntas sobre: métodos de pago, envíos, tiempos de entrega, devoluciones, garantía,\n'
     'facturación, soporte técnico, horarios de atención, políticas de la tienda.\n'
     '### ESTADO_PEDIDO\n'
     'El cliente pregunta por el estado de un pedido, envío o compra.\n'
     '- Si menciona un número con formato ORD-XXXX-NNN o similar -> extraelo EXACTO en "order_id"\n'
     '- NUNCA inventes un número de pedido que el cliente no haya dicho\n'
     '### RECLAMO\n'
     'Quejas, insatisfacción, problemas con productos, demoras excesivas, cobros incorrectos.\n'
     '- Marcá "urgente": true SOLO si menciona acción legal, defensa del consumidor o tono muy\n'
     '  agresivo\n'
     '### GENERAL\n'
     'Saludos, agradecimientos, despedidas, o consultas que no encajan en las otras categorías.\n'
     '\n'
     '## BASE DE CONOCIMIENTO FAQ\n'
     'Usá EXCLUSIVAMENTE esta información para responder FAQs. Si la pregunta no está cubierta\n'
     'acá, decí que vas a consultar con el equipo:\n'
     '\n'
     '{{ $json.faq_context }}\n'
     '\n'
     '   [ la expresión anterior se sustituye en tiempo de ejecución por las 23 entradas de la\n'
     '     tabla faq_responses, en el formato "P: <pregunta>" / "R: <respuesta>", tal como las\n'
     '     arma el nodo Preparar Contexto FAQ. Su contenido es el del Anexo D. ]\n'
     '\n'
     '## EJEMPLOS\n'
     'Mensaje: "hola che, quiero saber cómo va mi pedido ORD-TEST-003" | Cliente: Carlos\n'
     '-> {"intent": "ESTADO_PEDIDO", "order_id": "ORD-TEST-003", "urgente": false,\n'
     '    "respuesta": "¡Hola Carlos! Ya te busco la info de tu pedido, dame un segundo."}\n'
     '\n'
     'Mensaje: "me llegó roto el producto, una vergüenza" | Cliente: Pedro\n'
     '-> {"intent": "RECLAMO", "order_id": null, "urgente": false,\n'
     '    "respuesta": "Pedro, lamento muchísimo que hayas recibido el producto en esas\n'
     '     condiciones... ¿me pasás el número de tu pedido?"}\n'
     '\n'
     'Mensaje: "si no me solucionan esto voy a defensa del consumidor" | Cliente: María\n'
     '-> {"intent": "RECLAMO", "order_id": null, "urgente": true, "respuesta": "María, entiendo\n'
     '     perfectamente tu frustración..."}\n'
     '\n'
     '   [ se omiten cuatro de los siete ejemplos, de idéntica estructura: dos de FAQ con varias\n'
     '     preguntas en un mismo mensaje, uno de ESTADO_PEDIDO sin número de pedido y uno en\n'
     '     inglés que verifica la regla de responder en el idioma del cliente. ]', 'Source Code'),
    ('El texto íntegro de este prompt se encuentra en el nodo IA - Motor Decision del archivo '
     'workflows/Flujo 2 — Chatbot Omnicanal IA.json, en el commit f297c9e del repositorio, que es '
     'el export del workflow vigente durante la corrida del corpus. El prompt de ablación '
     'corresponde al mismo nodo del archivo workflows/Flujo 2 — Chatbot WhatsApp + Telegram.json '
     'en la versión actual. Ambos son verificables sin ejecutar el sistema.', 'Body Text'),
]
ancla = p_res
for texto, estilo in bloque_h2:
    ancla = insert_paragraph_after(ancla, texto, estilo=estilo)
print('  prompt de la configuracion principal incorporado al Anexo H')

d.save(RUTA)
print()
print('guardado (parte 1 de 2).')
