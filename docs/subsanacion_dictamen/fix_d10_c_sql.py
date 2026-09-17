# -*- coding: utf-8 -*-
"""A-03 de la auditoría del 17/09: las consultas se construían por interpolación.

Los nodos de base de datos de ambos flujos insertaban los valores recibidos dentro
del texto de la sentencia. El equipo lo tenía registrado como defecto D-9, de
severidad alta, y el documento no lo mencionaba. Se declara en la §5.5, en la §6.4
y en el Anexo L, y la §7.1 recomienda la parametrización, que además ya se aplicó a
los cuatro flujos publicados (experiments/PF/parametrizar_consultas.py).

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ §5.5 (j)
ultimo = k.par('(i) Variabilidad y versión del modelo:')
k.insertar_despues(
    ultimo, ultimo,
    '(j) Construcción de las consultas y superficie de inyección: los nodos de base de datos de ambos flujos '
    'armaban sus sentencias insertando los valores recibidos dentro del texto de la consulta, sin parámetros. Eso '
    'tiene dos consecuencias. La primera es de robustez: un valor legítimo que contenga un apóstrofo —un apellido '
    'O’Brien en el pedido, una contracción en un reclamo escrito en inglés— rompe la sentencia, la ejecución '
    'termina ahí y el caso se suma a las pérdidas silenciosas del punto (h). La segunda es de seguridad: un valor '
    'preparado para cerrar la comilla altera la sentencia, y llega al sistema por dos vías sin control previo, el '
    'cuerpo del webhook de órdenes, que no exige autenticación, y el mensaje del cliente, del que el modelo extrae '
    'el número de pedido. Ninguna de las dos se manifestó en las corridas medidas, porque ni el corpus ni las '
    'órdenes de prueba contienen apóstrofos, pero el defecto pertenece al artefacto medido y estaba registrado como '
    'tal en el repositorio del trabajo. Las diez consultas de los cuatro flujos se parametrizaron después de cerrar '
    'las mediciones, de modo que el artefacto publicado difiere del medido en ese punto y solo en ese (Anexo L); la '
    'prueba PF-06 deja constancia del comportamiento con un apóstrofo antes y después del cambio, y la '
    'recomendación correspondiente está en la Sección 7.1.',
    etiqueta='(j) Construcción de las consultas y superficie de inyección:')

# ------------------------------------------------------------------ §6.4
k.reemplazo('(ix) ninguno de los dos flujos advierte sus propias fallas, como mostró la primera corrida del corpus, '
            'que perdió el 23 % de los mensajes con la ejecución en estado exitoso (Sección 5.2.3).',
            '(ix) ninguno de los dos flujos advierte sus propias fallas, como mostró la primera corrida del corpus, '
            'que perdió el 23 % de los mensajes con la ejecución en estado exitoso (Sección 5.2.3); y (x) las '
            'consultas del artefacto medido se construían interpolando los valores recibidos en el texto de la '
            'sentencia, con el riesgo de rotura y de inyección que analiza la Sección 5.5 (j).')

# ------------------------------------------------------------------ §7.1
ancla = k.par('Implementar autenticación en los webhooks')
k.insertar_despues(
    ancla, k.par('Validar la etiqueta del modelo antes de registrar la interacción:'),
    'Parametrizar las consultas de los nodos de base de datos: las sentencias de ambos flujos insertaban los '
    'valores recibidos dentro de su propio texto (Sección 5.5 (j)). El nodo de PostgreSQL de n8n admite parámetros '
    'de consulta, que envían el valor separado de la sentencia y eliminan a la vez la vía de inyección y la rotura '
    'ante un apóstrofo. El cambio ya se aplicó a los cuatro flujos publicados; la recomendación vale para cualquier '
    'nodo que se agregue, y con más razón si el webhook de entrada no exige autenticación.',
    etiqueta='Parametrizar las consultas de los nodos de base de datos:')

# ------------------------------------------------------------------ Anexo L
modelo = k.par('Pruebas funcionales.')
k.insertar_despues(
    k.par('Primera corrida del corpus.'), modelo,
    'Construcción de las consultas. Los nodos de base de datos de ambos flujos armaban sus sentencias insertando '
    'los valores recibidos dentro del texto de la consulta. El registro de trabajo del equipo lo consigna como '
    'defecto D-9, de severidad alta, y no se lo corrigió durante las mediciones para no mover dos variables a la '
    'vez. Las diez consultas de los cuatro flujos se parametrizaron el 17 de septiembre de 2026, con las '
    'mediciones ya cerradas: el artefacto publicado difiere del medido en ese punto y solo en ese, porque la '
    'parametrización no cambia lo que cada consulta lee ni escribe. La prueba PF-06 deja constancia de las dos '
    'situaciones: la sentencia anterior, con un apellido que lleva apóstrofo, la rechaza PostgreSQL por un error '
    'de sintaxis; con la sentencia parametrizada el mismo valor llega como dato, y un reclamo en inglés con dos '
    'contracciones se clasifica, genera su ticket con el texto íntegro y recibe respuesta. El mismo cambio cerró lo '
    'que quedaba del defecto D-8 —la variante de producción del Flujo 2 conservaba la consulta anterior a la '
    'corrección de D-7, de modo que quien la importara reproducía el sistema con la pérdida silenciosa— y corrigió '
    'el nombre de un nodo de la variante de producción del Flujo 1 que una exportación había dejado mal '
    'codificado. El guion, la prueba y su evidencia están en experiments/PF.',
    etiqueta='Construcción de las consultas.')

k.guardar()
