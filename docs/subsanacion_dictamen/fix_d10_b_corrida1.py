# -*- coding: utf-8 -*-
"""A-02 de la auditoría del 17/09: la primera corrida del corpus y el defecto D-7.

El 12 de agosto el corpus se ejecutó dos veces. La primera corrida recibió 150
respuestas HTTP 200 y escribió 115 filas: se perdieron en silencio las 35 que el
modelo enrutó a ESTADO_PEDIDO, porque el nodo que busca el pedido no emitía ningún
ítem cuando el número citado no existía. El documento reportaba la segunda corrida
sin declarar la primera. Se declara en la §5.2.3, en las §§5.5 (f) y (h), en la §6.3,
en la §6.4 y en el Anexo L, con su exactitud, sus pérdidas y la variación de TMR.
Se agrega además la conciliación de la corrida reportada (M-03).

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ §5.2.3
ancla = k.par('Accuracy global: 92,7%')
p1 = k.insertar_despues(
    ancla, ancla,
    'Dos corridas, y por qué se informa la segunda. El corpus se ejecutó dos veces ese día. La primera, de las '
    '11:09, recibió 150 respuestas HTTP 200 y dejó 115 filas en la tabla de interacciones: se perdieron sin aviso '
    'las 35 que el modelo había enrutado a ESTADO_PEDIDO. El nodo que busca el pedido no emitía ningún ítem cuando '
    'el número citado no existía en la tabla de órdenes, y en un orquestador de flujo de datos un nodo que no emite '
    'detiene todo el subgrafo que sigue: esos clientes no recibieron respuesta, no se escribió su registro y la '
    'ejecución terminó marcada como exitosa. La respuesta de resguardo que el flujo ya tenía escrita para el pedido '
    'inexistente era inalcanzable por construcción, lo que muestra que en esta arquitectura la programación '
    'defensiva dentro del nodo no alcanza: el resguardo tiene que garantizar que el paso anterior emita siempre al '
    'menos un ítem. La consulta se reescribió para que parta de una fila sintética y traiga el pedido por '
    'combinación externa, de modo que devuelve siempre exactamente una fila, y la corrida definitiva, de las 20:45, '
    'se ejecutó sobre el sistema corregido y escribió las 150. La corrida omitida no era menos favorable: acertó '
    '140 de 150 (93,3 %) frente a 139 (92,7 %) de la definitiva, y ambas asignan la misma etiqueta a 145 de los 150 '
    'mensajes. Se informa la segunda porque es la única medida sobre un sistema que respondió a los 150 mensajes; '
    'el defecto se registra en el Anexo L y se retoma en las Secciones 5.5 (f) y (h), 6.3 y 6.4, y la comparación '
    'completa entre ambas corridas se versiona en experiments/E2/resultados/corrida1_vs_corrida2.txt.',
    etiqueta='Dos corridas, y por qué se informa la segunda.')
k.insertar_despues(
    p1, ancla,
    'Conciliación de la corrida informada. Las 150 respuestas se registraron con una etiqueta del vocabulario '
    'admitido y ninguna es el mensaje de disculpa que el flujo entrega cuando no consigue interpretar la salida del '
    'modelo (Sección 4.4.1): no hubo errores de parseo ni etiquetas fuera de vocabulario, de modo que los 150 '
    'mensajes del denominador corresponden a clasificaciones efectivas. El control no es una formalidad: un fallo '
    'de parseo se registra como GENERAL y podría contarse como acierto, y una etiqueta inexistente impide escribir '
    'la fila y saldría del denominador. En los dos casos la exactitud quedaría sobrestimada.',
    etiqueta='Conciliación de la corrida informada.')

# ------------------------------------------------------------------ §5.5 (f) y (h)
k.reemplazo('El valor reportado debe leerse en consecuencia como el desempeño en una ventana favorable y no como el '
            'esperable a lo largo del día.',
            'El valor reportado debe leerse en consecuencia como el desempeño en una ventana favorable y no como el '
            'esperable a lo largo del día. Las dos corridas del corpus de ese mismo día, separadas por nueve horas, '
            'lo muestran con una comparación directa: el tiempo medio de respuesta fue de 2,42 s a las 11:09 y de '
            '1,47 s a las 20:45, un 39 % más bajo, con la salvedad de que la media de la primera se calcula sobre '
            'las 115 interacciones que llegó a registrar (Sección 5.2.3). La diferencia entre dos corridas del '
            'mismo sistema en un mismo día es del orden de la que separa a los dos canales de la Tabla 5.6.')
k.reemplazo('El mismo patrón aparece en el Flujo 1: las órdenes perdidas bajo concurrencia y las rechazadas por un '
            'producto inexistente o un número de orden duplicado reciben HTTP 200 sin cuerpo (Secciones 5.1.1 y '
            '5.1.3).',
            'La forma más severa de este patrón se observó en la primera corrida del corpus: cuando el número de '
            'pedido citado no existía, el nodo que lo busca no emitía ningún ítem y el subgrafo siguiente no se '
            'ejecutaba, de modo que el 23 % de los mensajes quedó sin respuesta y sin registro con la ejecución '
            'marcada como exitosa (Sección 5.2.3). Se corrigió antes de la corrida que se informa. El mismo patrón '
            'aparece en el Flujo 1: las órdenes perdidas bajo concurrencia y las rechazadas por un producto '
            'inexistente o un número de orden duplicado reciben HTTP 200 sin cuerpo (Secciones 5.1.1 y 5.1.3).')

# ------------------------------------------------------------------ §6.3 y §6.4
k.reemplazo('la pérdida de órdenes bajo concurrencia (Sección 5.1.3) y la de registros ante una etiqueta inválida '
            '(Sección 5.2.4) ocurrieron sin que el motor de flujos las advirtiera, y detectarlas exigió '
            'instrumentación propia.',
            'la pérdida de órdenes bajo concurrencia (Sección 5.1.3), la de registros ante una etiqueta inválida '
            '(Sección 5.2.4) y la del 23 % de los mensajes de la primera corrida del corpus, cuando un nodo no '
            'emitió ningún ítem y el subgrafo siguiente no llegó a ejecutarse (Sección 5.2.3), ocurrieron sin que '
            'el motor de flujos las advirtiera —una con la ejecución en error y las otras dos con la ejecución en '
            'estado exitoso— y detectarlas exigió instrumentación propia.')
k.reemplazo('y (ix) ninguno de los dos flujos advierte sus propias fallas.',
            '(ix) ninguno de los dos flujos advierte sus propias fallas, como mostró la primera corrida del corpus, '
            'que perdió el 23 % de los mensajes con la ejecución en estado exitoso (Sección 5.2.3).')

# ------------------------------------------------------------------ Anexo L
modelo = k.par('Pruebas funcionales.')
k.insertar_despues(
    k.par('Trazabilidad del artefacto medido.'), modelo,
    'Primera corrida del corpus. El corpus se ejecutó dos veces el 12 de agosto de 2026. La primera corrida, de las '
    '11:09, recibió 150 respuestas HTTP 200 y escribió 115 interacciones: las 35 que el modelo enrutó a '
    'ESTADO_PEDIDO se perdieron sin aviso, porque el nodo que busca el pedido no emitía ningún ítem cuando el '
    'número citado no existía y el subgrafo siguiente no se ejecutaba. El registro de trabajo del equipo identifica '
    'el defecto como D-7. La consulta se reescribió y la corrida definitiva, de las 20:45, se ejecutó cuatro '
    'minutos después de publicar esa versión del flujo y escribió las 150 filas. Versiones anteriores de este '
    'documento informaban la segunda corrida sin mencionar la primera; la Sección 5.2.3 la declara, con su '
    'exactitud de 140 sobre 150 —mayor que la de la corrida definitiva— y la coincidencia de 145 de 150 etiquetas '
    'entre ambas, y las Secciones 5.5 (f) y (h), 6.3 y 6.4 incorporan el defecto y la variación de tiempo de '
    'respuesta que la comparación permite medir. La comparación se versiona en '
    'experiments/E2/resultados/corrida1_vs_corrida2.txt.',
    etiqueta='Primera corrida del corpus.')

k.guardar()
